
import os
import json
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Set
from dataclasses import dataclass, field
from collections import defaultdict
import traceback

# Импорты с fallback
try:
    import telegram
    from telegram import Update, BotCommand
    from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False
    print("⚠️ python-telegram-bot not installed. Install with: pip install python-telegram-bot")

# Импорты для интеграции с системой
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

try:
    from config.production_config_manager import get_config
    from memory.enhanced_buffer_memory import EnhancedBufferMemory
    from memory.hybrid_memory import HybridMemory
    from utils.time_utils import get_current_time
except ImportError as e:
    print(f"⚠️ Memory system imports not available: {e}")


@dataclass
class BotConfig:
    """Конфигурация бота из настроек"""
    token: str
    timeout: int = 30
    connection_pool_size: int = 8
    allowed_users: Set[int] = field(default_factory=set)
    admin_users: Set[int] = field(default_factory=set)
    max_message_length: int = 4096
    rate_limit_messages_per_minute: int = 20
    rate_limit_commands_per_hour: int = 100
    commands: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    messages: Dict[str, str] = field(default_factory=dict)
    memory_integration: Dict[str, Any] = field(default_factory=dict)
    logging_config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UserSession:
    """Сессия пользователя для rate limiting"""
    user_id: int
    username: Optional[str]
    message_times: List[datetime] = field(default_factory=list)
    command_times: List[datetime] = field(default_factory=list)
    last_activity: datetime = field(default_factory=datetime.now)
    message_count: int = 0
    command_count: int = 0


class ProductionTelegramBot:
    """Production-ready Telegram Bot без хардкода"""
    
    def __init__(self, config_manager=None):
        if not TELEGRAM_AVAILABLE:
            raise RuntimeError("python-telegram-bot is required but not installed")
        
        self.config_manager = config_manager
        self.config: Optional[BotConfig] = None
        self.application: Optional[Application] = None
        self.memory_system: Optional[HybridMemory] = None
        
        # Сессии пользователей для rate limiting
        self.user_sessions: Dict[int, UserSession] = {}
        
        # Статистика
        self.stats = {
            'messages_processed': 0,
            'commands_executed': 0,
            'memory_operations': 0,
            'errors': 0,
            'started_at': datetime.now()
        }
        
        # Логгер
        self.logger = logging.getLogger(__name__)
        
        # Инициализация
        self._load_config()
        self._setup_logging()
        self._initialize_memory_system()
        self._setup_bot()
    
    def _load_config(self):
        """Загружает конфигурацию бота"""
        try:
            if self.config_manager:
                # Используем ProductionConfigManager
                bot_settings = self.config_manager.get_config('bot_settings', default={})
            else:
                # Fallback: загружаем напрямую из файла
                import yaml
                config_path = Path(__file__).parent.parent / 'config' / 'bot_settings.yml'
                if config_path.exists():
                    with open(config_path, 'r', encoding='utf-8') as f:
                        settings = yaml.safe_load(f)
                    bot_settings = settings.get('telegram_bot', {})
                else:
                    bot_settings = {}
            
            # Получаем токен из переменной окружения
            token_env_var = bot_settings.get('token_env_var', 'TELEGRAM_BOT_TOKEN')
            token = os.getenv(token_env_var)
            if not token:
                raise ValueError(f"Telegram bot token not found in environment variable: {token_env_var}")
            
            # Получаем админов из переменной окружения
            admin_users = set()
            admin_env_var = bot_settings.get('admin_users_env_var', 'BOT_ADMIN_USERS')
            admin_users_env = os.getenv(admin_env_var)
            if admin_users_env:
                try:
                    admin_list = json.loads(admin_users_env)
                    admin_users = set(int(uid) for uid in admin_list)
                except (json.JSONDecodeError, ValueError) as e:
                    self.logger.warning(f"Failed to parse admin users from {admin_env_var}: {e}")
            
            # Создаем конфигурацию
            self.config = BotConfig(
                token=token,
                timeout=bot_settings.get('timeout', 30),
                connection_pool_size=bot_settings.get('connection_pool_size', 8),
                allowed_users=set(bot_settings.get('allowed_users', [])),
                admin_users=admin_users,
                max_message_length=bot_settings.get('max_message_length', 4096),
                rate_limit_messages_per_minute=bot_settings.get('rate_limit', {}).get('messages_per_minute', 20),
                rate_limit_commands_per_hour=bot_settings.get('rate_limit', {}).get('commands_per_hour', 100),
                commands=bot_settings.get('commands', {}),
                messages=bot_settings.get('messages', {}),
                memory_integration=bot_settings.get('memory_integration', {}),
                logging_config=bot_settings.get('logging', {})
            )
            
            self.logger.info(f"Bot config loaded successfully. Admin users: {len(admin_users)}")
            
        except Exception as e:
            self.logger.error(f"Failed to load bot config: {e}")
            raise
    
    def _setup_logging(self):
        """Настраивает логирование"""
        if not self.config:
            return
        
        log_config = self.config.logging_config
        level = getattr(logging, log_config.get('level', 'INFO').upper(), logging.INFO)
        format_str = log_config.get('format', '[%(asctime)s] %(name)s [%(levelname)s] %(message)s')
        
        logging.basicConfig(level=level, format=format_str)
        self.logger.setLevel(level)
        
        # Настраиваем логгер telegram библиотеки
        telegram_logger = logging.getLogger('telegram')
        telegram_logger.setLevel(logging.WARNING)  # Меньше спама
    
    def _initialize_memory_system(self):
        """Инициализирует систему памяти"""
        try:
            self.memory_system = HybridMemory(user_id="default")
            self.logger.info("Memory system initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize memory system: {e}")
            self.memory_system = None
    
    def _setup_bot(self):
        """Настраивает Telegram бота"""
        if not self.config:
            raise RuntimeError("Bot config not loaded")
        
        # Создаем приложение
        self.application = Application.builder().token(self.config.token).build()
        
        # Регистрируем обработчики команд
        self._register_handlers()
        
        self.logger.info("Telegram bot setup completed")
    
    def _register_handlers(self):
        """Регистрирует обработчики команд"""
        if not self.application or not self.config:
            return
        
        # Обработчики команд
        commands_config = self.config.commands
        
        if commands_config.get('start', {}).get('enabled', True):
            self.application.add_handler(CommandHandler('start', self.cmd_start))
        
        if commands_config.get('help', {}).get('enabled', True):
            self.application.add_handler(CommandHandler('help', self.cmd_help))
        
        if commands_config.get('status', {}).get('enabled', True):
            self.application.add_handler(CommandHandler('status', self.cmd_status))
        
        if commands_config.get('config', {}).get('enabled', True):
            self.application.add_handler(CommandHandler('config', self.cmd_config))
        
        if commands_config.get('test_memory', {}).get('enabled', True):
            self.application.add_handler(CommandHandler('test_memory', self.cmd_test_memory))
        
        if commands_config.get('test_search', {}).get('enabled', True):
            self.application.add_handler(CommandHandler('test_search', self.cmd_test_search))
        
        if commands_config.get('metrics', {}).get('enabled', True):
            self.application.add_handler(CommandHandler('metrics', self.cmd_metrics))
        
        # Обработчик обычных сообщений
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
        # Обработчик ошибок
        self.application.add_error_handler(self.error_handler)
    
    def _get_user_session(self, user_id: int, username: Optional[str] = None) -> UserSession:
        """Получает или создает сессию пользователя"""
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = UserSession(user_id=user_id, username=username)
        
        session = self.user_sessions[user_id]
        session.last_activity = datetime.now()
        return session
    
    def _check_rate_limit(self, user_id: int, is_command: bool = False) -> bool:
        """Проверяет rate limit для пользователя"""
        session = self._get_user_session(user_id)
        now = datetime.now()
        
        if is_command:
            # Очищаем старые команды (старше часа)
            cutoff = now - timedelta(hours=1)
            session.command_times = [t for t in session.command_times if t > cutoff]
            
            if len(session.command_times) >= self.config.rate_limit_commands_per_hour:
                return False
            
            session.command_times.append(now)
            session.command_count += 1
        else:
            # Очищаем старые сообщения (старше минуты)
            cutoff = now - timedelta(minutes=1)
            session.message_times = [t for t in session.message_times if t > cutoff]
            
            if len(session.message_times) >= self.config.rate_limit_messages_per_minute:
                return False
            
            session.message_times.append(now)
            session.message_count += 1
        
        return True
    
    def _check_permissions(self, user_id: int, admin_required: bool = False) -> bool:
        """Проверяет разрешения пользователя"""
        # Проверяем список разрешенных пользователей
        if self.config.allowed_users and user_id not in self.config.allowed_users:
            return False
        
        # Проверяем админские права
        if admin_required and user_id not in self.config.admin_users:
            return False
        
        return True
    
    def _format_message(self, template_key: str, **kwargs) -> str:
        """Форматирует сообщение из шаблона"""
        template = self.config.messages.get(template_key, f"Message template '{template_key}' not found")
        try:
            return template.format(**kwargs)
        except KeyError as e:
            self.logger.warning(f"Missing template variable {e} in message {template_key}")
            return template
    
    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        user_id = update.effective_user.id
        
        if not self._check_rate_limit(user_id, is_command=True):
            return
        
        if not self._check_permissions(user_id):
            await update.message.reply_text(self._format_message('unauthorized'))
            return
        
        welcome_msg = self._format_message('welcome')
        await update.message.reply_text(welcome_msg)
        
        self.stats['commands_executed'] += 1
        self.logger.info(f"Start command executed by user {user_id}")
    
    async def cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /help"""
        user_id = update.effective_user.id
        
        if not self._check_rate_limit(user_id, is_command=True):
            return
        
        if not self._check_permissions(user_id):
            await update.message.reply_text(self._format_message('unauthorized'))
            return
        
        help_msg = self._format_message('help')
        await update.message.reply_text(help_msg)
        
        self.stats['commands_executed'] += 1
    
    async def cmd_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /status"""
        user_id = update.effective_user.id
        
        if not self._check_rate_limit(user_id, is_command=True):
            return
        
        if not self._check_permissions(user_id):
            await update.message.reply_text(self._format_message('unauthorized'))
            return
        
        try:
            # Проверяем статус системы памяти
            if self.memory_system:
                memory_status = "🟢 Активна"
                try:
                    # Пробуем простую операцию
                    test_user = f"{self.config.memory_integration.get('user_prefix', 'telegram_user_')}{user_id}"
                    context_result = self.memory_system.get_context(test_user, "тест статуса")
                    memory_details = f"Контекст получен: {len(context_result.get('combined_context', []))} элементов"
                except Exception as e:
                    memory_status = f"🟡 Частично работает (ошибка: {str(e)[:50]}...)"
                    memory_details = ""
            else:
                memory_status = "🔴 Недоступна"
                memory_details = ""
            
            # Статистика бота
            uptime = datetime.now() - self.stats['started_at']
            
            status_msg = f"""📊 Статус системы:

🧠 Память: {memory_status}
{memory_details}

🤖 Бот:
• Время работы: {uptime}
• Сообщений обработано: {self.stats['messages_processed']}
• Команд выполнено: {self.stats['commands_executed']}
• Операций памяти: {self.stats['memory_operations']}
• Ошибок: {self.stats['errors']}
• Активных сессий: {len(self.user_sessions)}

⚙️ Конфигурация:
• Rate limit: {self.config.rate_limit_messages_per_minute} сообщений/мин
• Админов: {len(self.config.admin_users)}
• Язык по умолчанию: {self.config.memory_integration.get('default_language', 'ru')}"""
            
            await update.message.reply_text(status_msg)
            
        except Exception as e:
            error_msg = self._format_message('error_generic', error=str(e))
            await update.message.reply_text(error_msg)
            self.logger.error(f"Status command error: {e}")
            self.stats['errors'] += 1
        
        self.stats['commands_executed'] += 1
    
    async def cmd_config(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /config (только для админов)"""
        user_id = update.effective_user.id
        
        if not self._check_rate_limit(user_id, is_command=True):
            return
        
        if not self._check_permissions(user_id, admin_required=True):
            await update.message.reply_text(self._format_message('unauthorized'))
            return
        
        try:
            # Получаем текущую конфигурацию (без секретов)
            config_info = f"""⚙️ Конфигурация бота:

🔧 Основные настройки:
• Timeout: {self.config.timeout}s
• Pool size: {self.config.connection_pool_size}
• Max message length: {self.config.max_message_length}

🚦 Rate Limits:
• Сообщения: {self.config.rate_limit_messages_per_minute}/мин
• Команды: {self.config.rate_limit_commands_per_hour}/час

👥 Пользователи:
• Разрешенные: {len(self.config.allowed_users) if self.config.allowed_users else 'все'}
• Админы: {len(self.config.admin_users)}

🧠 Интеграция памяти:
• Сохранение диалогов: {self.config.memory_integration.get('store_conversations', False)}
• Префикс пользователей: {self.config.memory_integration.get('user_prefix', 'telegram_user_')}
• Язык по умолчанию: {self.config.memory_integration.get('default_language', 'ru')}
• Бонус важности: {self.config.memory_integration.get('importance_boost', 0.0)}

📝 Команды: {len([k for k, v in self.config.commands.items() if v.get('enabled', True)])} активных"""
            
            await update.message.reply_text(config_info)
            
        except Exception as e:
            error_msg = self._format_message('error_generic', error=str(e))
            await update.message.reply_text(error_msg)
            self.logger.error(f"Config command error: {e}")
            self.stats['errors'] += 1
        
        self.stats['commands_executed'] += 1
    
    async def cmd_test_memory(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /test_memory"""
        user_id = update.effective_user.id
        
        if not self._check_rate_limit(user_id, is_command=True):
            return
        
        if not self._check_permissions(user_id):
            await update.message.reply_text(self._format_message('unauthorized'))
            return
        
        try:
            # Получаем текст для сохранения
            if context.args:
                text_to_save = ' '.join(context.args)
            else:
                await update.message.reply_text("💡 Использование: /test_memory <текст для сохранения>")
                return
            
            if not self.memory_system:
                await update.message.reply_text("❌ Система памяти недоступна")
                return
            
            # Сохраняем в память
            telegram_user_id = f"{self.config.memory_integration.get('user_prefix', 'telegram_user_')}{user_id}"
            
            result = self.memory_system.add_message(
                user_id=telegram_user_id,
                message=text_to_save,
                role="user",
                metadata={
                    'source': 'telegram_bot',
                    'command': 'test_memory',
                    'telegram_user_id': user_id,
                    'telegram_username': update.effective_user.username
                }
            )
            
            if result:
                success_msg = self._format_message('memory_saved')
                await update.message.reply_text(f"{success_msg}\n📝 Текст: {text_to_save}")
                self.stats['memory_operations'] += 1
            else:
                error_msg = self._format_message('memory_error', error="Неизвестная ошибка")
                await update.message.reply_text(error_msg)
                self.stats['errors'] += 1
                
        except Exception as e:
            error_msg = self._format_message('memory_error', error=str(e))
            await update.message.reply_text(error_msg)
            self.logger.error(f"Test memory command error: {e}")
            self.stats['errors'] += 1
        
        self.stats['commands_executed'] += 1
    
    async def cmd_test_search(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /test_search"""
        user_id = update.effective_user.id
        
        if not self._check_rate_limit(user_id, is_command=True):
            return
        
        if not self._check_permissions(user_id):
            await update.message.reply_text(self._format_message('unauthorized'))
            return
        
        try:
            # Получаем запрос для поиска
            if context.args:
                search_query = ' '.join(context.args)
            else:
                await update.message.reply_text("💡 Использование: /test_search <запрос для поиска>")
                return
            
            if not self.memory_system:
                await update.message.reply_text("❌ Система памяти недоступна")
                return
            
            # Выполняем поиск
            telegram_user_id = f"{self.config.memory_integration.get('user_prefix', 'telegram_user_')}{user_id}"
            
            search_result = self.memory_system.get_context(
                user_id=telegram_user_id,
                query=search_query
            )
            
            # Форматируем результаты
            if search_result and search_result.get('combined_context'):
                results = search_result['combined_context']
                
                response = f"🔍 Найдено {len(results)} результатов по запросу: {search_query}\n\n"
                
                for i, result in enumerate(results[:3], 1):  # Показываем только первые 3
                    content = result.get('content', 'Нет контента')[:100]
                    if len(result.get('content', '')) > 100:
                        content += '...'
                    
                    response += f"{i}. {content}\n"
                    if 'importance' in result:
                        response += f"   📊 Важность: {result['importance']:.2f}\n"
                    response += "\n"
                
                if len(results) > 3:
                    response += f"... и еще {len(results) - 3} результатов"
                
                await update.message.reply_text(response)
                self.stats['memory_operations'] += 1
                
            else:
                no_results_msg = self._format_message('search_no_results', query=search_query)
                await update.message.reply_text(no_results_msg)
                
        except Exception as e:
            error_msg = self._format_message('error_generic', error=str(e))
            await update.message.reply_text(error_msg)
            self.logger.error(f"Test search command error: {e}")
            self.stats['errors'] += 1
        
        self.stats['commands_executed'] += 1
    
    async def cmd_metrics(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /metrics (только для админов)"""
        user_id = update.effective_user.id
        
        if not self._check_rate_limit(user_id, is_command=True):
            return
        
        if not self._check_permissions(user_id, admin_required=True):
            await update.message.reply_text(self._format_message('unauthorized'))
            return
        
        try:
            # Собираем метрики
            uptime = datetime.now() - self.stats['started_at']
            
            # Статистика сессий
            active_sessions = len(self.user_sessions)
            total_user_messages = sum(s.message_count for s in self.user_sessions.values())
            total_user_commands = sum(s.command_count for s in self.user_sessions.values())
            
            # Метрики системы памяти
            memory_metrics = ""
            if self.memory_system:
                try:
                    # Если есть метод получения статистики
                    if hasattr(self.memory_system, 'get_stats'):
                        memory_stats = self.memory_system.get_stats()
                        memory_metrics = f"\n🧠 Метрики памяти:\n"
                        for key, value in memory_stats.items():
                            if isinstance(value, (int, float)):
                                memory_metrics += f"• {key}: {value}\n"
                except Exception as e:
                    memory_metrics = f"\n🧠 Память: ошибка получения метрик ({e})"
            
            metrics_msg = f"""📈 Метрики системы:

🕐 Время работы: {uptime}

📊 Статистика бота:
• Сообщений обработано: {self.stats['messages_processed']}
• Команд выполнено: {self.stats['commands_executed']}
• Операций памяти: {self.stats['memory_operations']}
• Ошибок: {self.stats['errors']}

👥 Пользователи:
• Активных сессий: {active_sessions}
• Всего сообщений от пользователей: {total_user_messages}
• Всего команд от пользователей: {total_user_commands}

⚡ Производительность:
• Сообщений/час: {(self.stats['messages_processed'] / max(uptime.total_seconds() / 3600, 1)):.1f}
• Команд/час: {(self.stats['commands_executed'] / max(uptime.total_seconds() / 3600, 1)):.1f}
• Успешность: {((self.stats['messages_processed'] + self.stats['commands_executed'] - self.stats['errors']) / max(self.stats['messages_processed'] + self.stats['commands_executed'], 1) * 100):.1f}%{memory_metrics}"""
            
            await update.message.reply_text(metrics_msg)
            
        except Exception as e:
            error_msg = self._format_message('error_generic', error=str(e))
            await update.message.reply_text(error_msg)
            self.logger.error(f"Metrics command error: {e}")
            self.stats['errors'] += 1
        
        self.stats['commands_executed'] += 1
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик обычных сообщений"""
        user_id = update.effective_user.id
        
        if not self._check_rate_limit(user_id):
            return
        
        if not self._check_permissions(user_id):
            await update.message.reply_text(self._format_message('unauthorized'))
            return
        
        try:
            message_text = update.message.text
            
            # Проверяем длину сообщения
            if len(message_text) > self.config.max_message_length:
                await update.message.reply_text(f"❌ Сообщение слишком длинное (макс. {self.config.max_message_length} символов)")
                return
            
            # Сохраняем в память если включено
            if self.config.memory_integration.get('store_conversations', True) and self.memory_system:
                telegram_user_id = f"{self.config.memory_integration.get('user_prefix', 'telegram_user_')}{user_id}"
                
                result = self.memory_system.add_message(
                    user_id=telegram_user_id,
                    message=message_text,
                    role="user",
                    metadata={
                        'source': 'telegram_bot',
                        'telegram_user_id': user_id,
                        'telegram_username': update.effective_user.username,
                        'chat_id': update.effective_chat.id,
                        'message_id': update.message.message_id
                    }
                )
                
                if result:
                    await update.message.reply_text("✅ Сохранено в память")
                    self.stats['memory_operations'] += 1
                else:
                    await update.message.reply_text("⚠️ Ошибка сохранения в память")
                    self.stats['errors'] += 1
            else:
                # Просто подтверждаем получение
                await update.message.reply_text("👍 Сообщение получено")
            
            self.stats['messages_processed'] += 1
            
            # Логируем если включено
            if self.config.logging_config.get('log_chat_messages', False):
                self.logger.info(f"Message from user {user_id}: {message_text[:50]}...")
            
        except Exception as e:
            error_msg = self._format_message('error_generic', error=str(e))
            await update.message.reply_text(error_msg)
            self.logger.error(f"Message handling error: {e}")
            self.stats['errors'] += 1
    
    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик ошибок"""
        self.logger.error(f"Exception while handling an update: {context.error}")
        
        # Увеличиваем счетчик ошибок
        self.stats['errors'] += 1
        
        # Если есть update и сообщение, отправляем пользователю уведомление
        if isinstance(update, Update) and update.effective_message:
            try:
                error_msg = self._format_message('error_generic', error="Внутренняя ошибка")
                await update.effective_message.reply_text(error_msg)
            except Exception:
                pass  # Если не можем отправить сообщение об ошибке, игнорируем
    
    async def setup_bot_commands(self):
        """Настраивает команды бота в Telegram"""
        if not self.application:
            return
        
        commands = []
        for cmd_name, cmd_config in self.config.commands.items():
            if cmd_config.get('enabled', True):
                description = cmd_config.get('description', f'Command {cmd_name}')
                commands.append(BotCommand(cmd_name, description))
        
        try:
            await self.application.bot.set_my_commands(commands)
            self.logger.info(f"Bot commands set: {[cmd.command for cmd in commands]}")
        except Exception as e:
            self.logger.error(f"Failed to set bot commands: {e}")
    
    async def start(self):
        """Запускает бота"""
        if not self.application:
            raise RuntimeError("Bot not configured")
        
        self.logger.info("Starting Telegram bot...")
        
        # Настраиваем команды
        await self.setup_bot_commands()
        
        # Запускаем polling
        await self.application.run_polling(drop_pending_updates=True)
    
    def run(self):
        """Синхронный запуск бота"""
        try:
            asyncio.run(self.start())
        except KeyboardInterrupt:
            self.logger.info("Bot stopped by user")
        except Exception as e:
            self.logger.error(f"Bot crashed: {e}")
            raise


def main():
    """Точка входа для запуска бота"""
    try:
        # Пытаемся использовать ProductionConfigManager
        try:
            from config.production_config_manager import config_manager
            bot = ProductionTelegramBot(config_manager=config_manager)
        except ImportError:
            # Fallback: без config manager
            print("⚠️ ProductionConfigManager not available, using fallback config loading")
            bot = ProductionTelegramBot()
        
        bot.run()
        
    except Exception as e:
        print(f"❌ Failed to start bot: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
