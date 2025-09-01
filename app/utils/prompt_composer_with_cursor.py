"""
PromptComposer с поддержкой курсора
Реализует схему из ТЗ: build_prompt(base_prompt, daily_prompt, behavior_tag, short_memory, cursor_position)
"""
import os
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

class PromptComposerWithCursor:
    """
    Компоновщик промптов с поддержкой курсора диалога
    Полностью конфигурируемый, без хардкода
    """
    
    def __init__(self, config_manager=None):
        self.config_manager = config_manager
        self.logger = logging.getLogger(__name__)
        
        # Загружаем конфигурацию
        self.config = self._load_config()
        
        # Кеш для базовых промптов
        self._base_prompts_cache = {}
        self._daily_prompts_cache = {}
        
        self.logger.info("PromptComposerWithCursor initialized")
    
    def _load_config(self) -> Dict[str, Any]:
        """Загружает конфигурацию без хардкода"""
        try:
            if self.config_manager:
                from ..config.production_config_manager import get_config
                return get_config('prompt_composer', user_id=None, default={})
            else:
                # Fallback к переменным окружения
                return {
                    'base_prompts_dir': os.getenv('BASE_PROMPTS_DIR', './app/config/prompts'),
                    'daily_prompts_dir': os.getenv('DAILY_PROMPTS_DIR', './app/config/prompts'),
                    'cursor_marker': os.getenv('CURSOR_MARKER', '>> '),
                    'max_prompt_length': int(os.getenv('MAX_PROMPT_LENGTH', '8000')),
                    'behavior_templates': {
                        'care': 'Будь заботливой и внимательной.',
                        'playful': 'Будь игривой и веселой.',
                        'reserved': 'Будь сдержанной и формальной.',
                        'professional': 'Будь профессиональной и деловой.',
                        'friendly': 'Будь дружелюбной и открытой.',
                        'supportive': 'Будь поддерживающей и понимающей.'
                    }
                }
        except Exception as e:
            self.logger.error(f"Failed to load config: {e}")
            return {}
    
    def build_prompt(self, 
                    base_prompt_name: str,
                    daily_prompt_name: str,
                    behavior_tag: str,
                    short_memory: Dict[str, Any],
                    user_id: Optional[str] = None) -> str:
        """
        Строит финальный промпт по схеме из ТЗ
        
        Args:
            base_prompt_name: Имя файла базового промпта (без расширения)
            daily_prompt_name: Имя файла дневного промпта
            behavior_tag: Тег поведения (care, playful, reserved, etc.)
            short_memory: Контекст из short_memory в формате ТЗ
            user_id: ID пользователя для персонализации
            
        Returns:
            str: Готовый промпт для LLM
        """
        try:
            # 1. Собираем системный промпт
            base_prompt = self._load_base_prompt(base_prompt_name)
            daily_prompt = self._load_daily_prompt(daily_prompt_name)
            system_text = base_prompt + "\n\n" + daily_prompt
            
            # 2. Добавляем краткосрочную память (buffer + summary)
            memory_text = self._build_memory_section(short_memory)
            
            # 3. Добавляем поведение
            behavior_text = self._build_behavior_section(behavior_tag)
            
            # 4. Добавляем контекст пользователя
            user_context = self._build_user_context(user_id, short_memory)
            
            # 5. Финальный промпт
            prompt_parts = [
                system_text,
                behavior_text,
                user_context,
                memory_text,
                "[ASSISTANT]:"
            ]
            
            final_prompt = "\n\n".join(filter(None, prompt_parts))
            
            # Проверяем длину
            max_length = self.config.get('max_prompt_length', 8000)
            if len(final_prompt) > max_length:
                final_prompt = self._truncate_prompt(final_prompt, max_length)
                self.logger.warning(f"Prompt truncated to {max_length} characters")
            
            return final_prompt
            
        except Exception as e:
            self.logger.error(f"Failed to build prompt: {e}")
            return f"Ошибка генерации промпта: {e}"
    
    def _load_base_prompt(self, prompt_name: str) -> str:
        """Загружает базовый промпт из файла"""
        if prompt_name in self._base_prompts_cache:
            return self._base_prompts_cache[prompt_name]
        
        try:
            prompts_dir = Path(self.config.get('base_prompts_dir', './app/config/prompts'))
            prompt_file = prompts_dir / f"{prompt_name}.txt"
            
            if not prompt_file.exists():
                self.logger.warning(f"Base prompt file not found: {prompt_file}")
                return f"# Базовый промпт {prompt_name} не найден"
            
            with open(prompt_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            
            self._base_prompts_cache[prompt_name] = content
            return content
            
        except Exception as e:
            self.logger.error(f"Failed to load base prompt {prompt_name}: {e}")
            return f"# Ошибка загрузки базового промпта: {e}"
    
    def _load_daily_prompt(self, prompt_name: str) -> str:
        """Загружает дневной промпт из файла"""
        if prompt_name in self._daily_prompts_cache:
            return self._daily_prompts_cache[prompt_name]
        
        try:
            prompts_dir = Path(self.config.get('daily_prompts_dir', './app/config/prompts'))
            prompt_file = prompts_dir / f"{prompt_name}.txt"
            
            if not prompt_file.exists():
                self.logger.warning(f"Daily prompt file not found: {prompt_file}")
                return f"# Дневной промпт {prompt_name} не найден"
            
            with open(prompt_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            
            self._daily_prompts_cache[prompt_name] = content
            return content
            
        except Exception as e:
            self.logger.error(f"Failed to load daily prompt {prompt_name}: {e}")
            return f"# Ошибка загрузки дневного промпта: {e}"
    
    def _build_memory_section(self, short_memory: Dict[str, Any]) -> str:
        """Строит секцию памяти с поддержкой курсора"""
        try:
            memory_parts = []
            cursor_marker = self.config.get('cursor_marker', '>> ')
            
            # Добавляем summary memory
            summary_memory = short_memory.get('summary_memory', [])
            if summary_memory:
                memory_parts.append("[КРАТКОСРОЧНАЯ ПАМЯТЬ]")
                for summary in summary_memory:
                    summary_text = summary.get('summary_text', '')
                    topics = summary.get('topics', [])
                    emotions = summary.get('emotions', [])
                    
                    summary_line = f"SUMMARY: {summary_text}"
                    if topics:
                        summary_line += f" (темы: {', '.join(topics)})"
                    if emotions:
                        summary_line += f" [эмоции: {', '.join(emotions)}]"
                    
                    memory_parts.append(summary_line)
            
            # Добавляем текущий буфер с курсором
            buffer = short_memory.get('buffer', [])
            if buffer:
                memory_parts.append("\n[ТЕКУЩИЙ ДИАЛОГ]")
                
                config = short_memory.get('config', {})
                cursor_position = config.get('cursor_position', -1)
                
                for i, msg in enumerate(buffer):
                    role = msg.get('role', 'unknown').upper()
                    text = msg.get('text', '')
                    emotion_tag = msg.get('emotion_tag', '')
                    behavior_tag = msg.get('behavior_tag', '')
                    
                    # Добавляем курсор если это активная позиция
                    cursor_prefix = cursor_marker if i == cursor_position else ""
                    
                    # Формируем строку сообщения
                    msg_line = f"{cursor_prefix}[{role}] {text}"
                    
                    # Добавляем теги
                    tags = []
                    if emotion_tag:
                        tags.append(f"эмоция: {emotion_tag}")
                    if behavior_tag:
                        tags.append(f"поведение: {behavior_tag}")
                    
                    if tags:
                        msg_line += f" ({', '.join(tags)})"
                    
                    memory_parts.append(msg_line)
            
            return "\n".join(memory_parts) if memory_parts else ""
            
        except Exception as e:
            self.logger.error(f"Failed to build memory section: {e}")
            return f"# Ошибка создания секции памяти: {e}"
    
    def _build_behavior_section(self, behavior_tag: str) -> str:
        """Строит секцию поведения"""
        try:
            behavior_templates = self.config.get('behavior_templates', {})
            
            if behavior_tag in behavior_templates:
                behavior_instruction = behavior_templates[behavior_tag]
            else:
                # Fallback для неизвестных тегов
                behavior_instruction = f"Адаптируй поведение согласно тегу: {behavior_tag}"
            
            return f"[СТРАТЕГИЯ ПОВЕДЕНИЯ] {behavior_instruction}"
            
        except Exception as e:
            self.logger.error(f"Failed to build behavior section: {e}")
            return f"[СТРАТЕГИЯ ПОВЕДЕНИЯ] Ошибка: {e}"
    
    def _build_user_context(self, user_id: Optional[str], short_memory: Dict[str, Any]) -> str:
        """Строит контекст пользователя"""
        try:
            context_parts = []
            
            if user_id:
                context_parts.append(f"[ПОЛЬЗОВАТЕЛЬ] ID: {user_id}")
            
            # Добавляем статистику из памяти
            stats = short_memory.get('stats', {})
            if stats:
                total_messages = stats.get('total_messages', 0)
                buffer_size = stats.get('current_buffer_size', 0)
                summary_entries = stats.get('summary_entries', 0)
                
                context_parts.append(
                    f"[СТАТИСТИКА] Всего сообщений: {total_messages}, "
                    f"в буфере: {buffer_size}, резюме: {summary_entries}"
                )
            
            # Добавляем время
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            context_parts.append(f"[ВРЕМЯ] {current_time}")
            
            return "\n".join(context_parts) if context_parts else ""
            
        except Exception as e:
            self.logger.error(f"Failed to build user context: {e}")
            return f"[КОНТЕКСТ] Ошибка: {e}"
    
    def _truncate_prompt(self, prompt: str, max_length: int) -> str:
        """Обрезает промпт до максимальной длины"""
        if len(prompt) <= max_length:
            return prompt
        
        # Сохраняем важные части
        lines = prompt.split('\n')
        
        # Ищем секции
        system_end = -1
        memory_start = -1
        
        for i, line in enumerate(lines):
            if '[КРАТКОСРОЧНАЯ ПАМЯТЬ]' in line or '[ТЕКУЩИЙ ДИАЛОГ]' in line:
                memory_start = i
                break
            if '[СТРАТЕГИЯ ПОВЕДЕНИЯ]' in line:
                system_end = i
        
        # Обрезаем память если нужно
        if memory_start > 0:
            system_part = '\n'.join(lines[:system_end + 1])
            memory_part = '\n'.join(lines[memory_start:])
            
            available_length = max_length - len(system_part) - 100  # Резерв
            
            if len(memory_part) > available_length:
                # Обрезаем память, оставляя последние сообщения
                memory_lines = memory_part.split('\n')
                truncated_memory = []
                current_length = 0
                
                # Добавляем с конца
                for line in reversed(memory_lines):
                    if current_length + len(line) + 1 > available_length:
                        break
                    truncated_memory.insert(0, line)
                    current_length += len(line) + 1
                
                memory_part = '\n'.join(truncated_memory)
            
            return system_part + '\n\n' + memory_part
        
        # Простое обрезание
        return prompt[:max_length - 100] + "\n\n[АССИСТЕНТ ОБРЕЗАН]"
    
    def clear_cache(self):
        """Очищает кеш промптов"""
        self._base_prompts_cache.clear()
        self._daily_prompts_cache.clear()
        self.logger.info("Prompt cache cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """Получает статистику работы"""
        return {
            'base_prompts_cached': len(self._base_prompts_cache),
            'daily_prompts_cached': len(self._daily_prompts_cache),
            'config_loaded': bool(self.config),
            'available_behaviors': list(self.config.get('behavior_templates', {}).keys())
        }
