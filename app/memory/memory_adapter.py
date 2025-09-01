"""
Memory Adapter - адаптер для подготовки данных памяти для промпта
"""
from typing import Dict, Optional, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class MemoryAdapter:
    """Адаптер для подготовки данных памяти для промпта"""
    
    def __init__(self, memory_manager):
        self.memory_manager = memory_manager
    
    def get_for_prompt(self, user_id: str, query: str) -> Dict[str, str]:
        """
        Получает все данные памяти для промпта
        
        Args:
            user_id: ID пользователя
            query: текущий запрос пользователя
            
        Returns:
            Словарь с данными для промпта
        """
        try:
            logger.info(f"🚀 [ADAPTER] СТАРТ get_for_prompt для {user_id}, запрос: {query[:50]}...")
            print(f"🚀 [ADAPTER] СТАРТ get_for_prompt для {user_id}, запрос: {query[:50]}...")
            
            # Получаем короткую сводку
            short_summary = self._get_short_memory_summary(user_id)
            
            # Получаем долгосрочные факты
            long_facts = self._get_long_memory_facts(user_id)
            
            # Получаем семантический контекст
            semantic_context = self._get_semantic_context(user_id, query)
            
            result = {
                "short_memory_summary": short_summary or "—",
                "long_memory_facts": long_facts or "—", 
                "semantic_context": semantic_context or "—",
            }
            
            logger.info(f"✅ [ADAPTER] РЕЗУЛЬТАТ get_for_prompt: short={len(result['short_memory_summary'])}, facts={len(result['long_memory_facts'])}, semantic={len(result['semantic_context'])}")
            print(f"✅ [ADAPTER] РЕЗУЛЬТАТ get_for_prompt: short={len(result['short_memory_summary'])}, facts={len(result['long_memory_facts'])}, semantic={len(result['semantic_context'])}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ [ADAPTER] Ошибка получения данных памяти для промпта: {e}")
            print(f"❌ [ADAPTER] Ошибка получения данных памяти для промпта: {e}")
            import traceback
            logger.error(f"❌ [ADAPTER] Traceback: {traceback.format_exc()}")
            print(f"❌ [ADAPTER] Traceback: {traceback.format_exc()}")
            return {
                "short_memory_summary": "—",
                "long_memory_facts": "—",
                "semantic_context": "—",
            }
    
    def _get_short_memory_summary(self, user_id: str) -> Optional[str]:
        """Получает короткую сводку последних сообщений"""
        try:
            logger.info(f"🔍 [ADAPTER] Получаем короткую сводку для {user_id}")
            
            # ИСПРАВЛЕНИЕ: Проверяем разные типы memory_manager
            
            # Вариант 1: MemoryLevelsManager
            if hasattr(self.memory_manager, 'short_term') and self.memory_manager.short_term:
                short_term = self.memory_manager.short_term
                logger.info(f"🔍 [ADAPTER] short_term найден: {type(short_term)}")
                
                # Метод 1: get_context_string (основной для ShortMemory)
                if hasattr(short_term, 'get_context_string'):
                    try:
                        context_string = short_term.get_context_string()
                        if context_string and context_string != "Нет сообщений в памяти":
                            logger.info(f"✅ [ADAPTER] get_context_string вернул {len(context_string)} символов")
                            return context_string
                    except Exception as e:
                        logger.warning(f"⚠️ [ADAPTER] get_context_string failed: {e}")
                
                # Метод 2: get_context (возвращает список сообщений)
                if hasattr(short_term, 'get_context'):
                    try:
                        messages = short_term.get_context()
                        if messages:
                            logger.info(f"✅ [ADAPTER] get_context вернул {len(messages)} сообщений")
                            
                            # Форматируем в читаемый вид
                            summary_parts = []
                            for msg in messages[-10:]:  # Последние 10
                                if isinstance(msg, dict):
                                    role = msg.get('role', 'unknown')
                                    content = msg.get('content', '')[:100]  # Обрезаем длинные сообщения
                                else:
                                    # Если это объект сообщения
                                    role = getattr(msg, 'role', 'unknown')
                                    content = getattr(msg, 'content', str(msg))[:100]
                                
                                if content:
                                    summary_parts.append(f"[{role.upper()}]: {content}")
                            
                            if summary_parts:
                                result = "\n".join(summary_parts)
                                logger.info(f"✅ [ADAPTER] Сформирована сводка из get_context: {len(result)} символов")
                                return result
                    except Exception as e:
                        logger.warning(f"⚠️ [ADAPTER] get_context failed: {e}")
            
            # Вариант 2: HybridMemory с short_memory
            if hasattr(self.memory_manager, 'short_memory') and self.memory_manager.short_memory:
                try:
                    buffer = self.memory_manager.short_memory
                    logger.info(f"🔍 [ADAPTER] HybridMemory.short_memory найден: {type(buffer)}")
                    
                    if hasattr(buffer, 'messages') and buffer.messages:
                        recent_messages = buffer.messages[-10:]
                        logger.info(f"✅ [ADAPTER] short_memory.messages: {len(recent_messages)} сообщений")
                        
                        # Форматируем в читаемый вид
                        summary_parts = []
                        for msg in recent_messages:
                            if isinstance(msg, dict):
                                role = msg.get('role', 'unknown')
                                content = msg.get('content', '')[:100]
                            else:
                                role = getattr(msg, 'role', 'unknown')
                                content = getattr(msg, 'content', str(msg))[:100]
                            
                            if content:
                                summary_parts.append(f"[{role.upper()}]: {content}")
                        
                        if summary_parts:
                            result = "\n".join(summary_parts)
                            logger.info(f"✅ [ADAPTER] Сформирована сводка из HybridMemory: {len(result)} символов")
                            return result
                except Exception as e:
                    logger.warning(f"⚠️ [ADAPTER] HybridMemory short_memory failed: {e}")
            
            # Вариант 3: Простой MemoryAdapter с messages
            if hasattr(self.memory_manager, 'messages') and self.memory_manager.messages:
                try:
                    recent_messages = self.memory_manager.messages[-10:]
                    logger.info(f"✅ [ADAPTER] direct messages: {len(recent_messages)} сообщений")
                    
                    # Форматируем в читаемый вид
                    summary_parts = []
                    for msg in recent_messages:
                        if isinstance(msg, dict):
                            role = msg.get('role', 'unknown')
                            content = msg.get('content', '')[:100]
                        else:
                            role = getattr(msg, 'role', 'unknown')
                            content = getattr(msg, 'content', str(msg))[:100]
                        
                        if content:
                            summary_parts.append(f"[{role.upper()}]: {content}")
                    
                    if summary_parts:
                        result = "\n".join(summary_parts)
                        logger.info(f"✅ [ADAPTER] Сформирована сводка из direct messages: {len(result)} символов")
                        return result
                except Exception as e:
                    logger.warning(f"⚠️ [ADAPTER] direct messages failed: {e}")
            
            logger.warning(f"❌ [ADAPTER] Не удалось получить короткую сводку для {user_id}")
            logger.info(f"❌ [ADAPTER] Доступные атрибуты memory_manager: {dir(self.memory_manager)}")
            return None
            
        except Exception as e:
            logger.warning(f"❌ [ADAPTER] Ошибка получения короткой сводки: {e}")
            return None
    
    def _get_long_memory_facts(self, user_id: str) -> Optional[str]:
        """Получает долгосрочные факты о пользователе"""
        try:
            logger.info(f"🔍 [ADAPTER] Получаем долгосрочные факты для {user_id}")
            
            # ИСПРАВЛЕНИЕ: Проверяем разные типы memory_manager
            
            # Вариант 1: MemoryLevelsManager с long_term
            if hasattr(self.memory_manager, 'long_term') and self.memory_manager.long_term:
                logger.info(f"🔍 [ADAPTER] long_term найден: {type(self.memory_manager.long_term)}")
                
                try:
                    # Ищем факты о пользователе (более конкретные запросы)
                    user_facts = self.memory_manager.long_term.search_memories(
                        query=f"пользователь имя зовут возраст работа семья предпочтения цели",
                        limit=5
                    )
                    
                    logger.info(f"🔍 [ADAPTER] Поиск фактов вернул {len(user_facts) if user_facts else 0} результатов")
                    
                    if user_facts:
                        facts_parts = []
                        for fact in user_facts:
                            content = fact.get('content', '')
                            logger.info(f"🔍 [ADAPTER] Обрабатываем факт: {content[:50]}...")
                            
                            # Фильтруем факты, содержащие личную информацию
                            if content and len(content) > 10:
                                # Приоритет фактам с именами и личной информацией
                                important_keywords = ['зовут', 'имя', 'меня', 'лет', 'возраст', 'работа', 'программист', 'андрей', 'глеб', 'пицца', 'еда', 'москве', 'москва', 'живу']
                                if any(word in content.lower() for word in important_keywords):
                                    facts_parts.insert(0, f"• {content}")  # В начало списка
                                    logger.info(f"✅ [ADAPTER] Важный факт добавлен в начало: {content[:30]}...")
                                else:
                                    facts_parts.append(f"• {content}")
                                    logger.info(f"✅ [ADAPTER] Обычный факт добавлен: {content[:30]}...")
                        
                        if facts_parts:
                            result = "\n".join(facts_parts[:5])  # Максимум 5 фактов
                            logger.info(f"✅ [ADAPTER] Сформированы долгосрочные факты: {len(facts_parts)} фактов, {len(result)} символов")
                            return result
                        else:
                            logger.warning(f"⚠️ [ADAPTER] Факты найдены, но все отфильтрованы")
                    else:
                        logger.warning(f"⚠️ [ADAPTER] Долгосрочные факты не найдены")
                except Exception as e:
                    logger.warning(f"⚠️ [ADAPTER] long_term.search_memories failed: {e}")
            
            # Вариант 2: HybridMemory с long_memory
            if hasattr(self.memory_manager, 'long_memory') and self.memory_manager.long_memory:
                try:
                    long_memory = self.memory_manager.long_memory
                    logger.info(f"🔍 [ADAPTER] HybridMemory.long_memory найден: {type(long_memory)}")
                    
                    # Пытаемся получить профиль пользователя
                    if hasattr(long_memory, 'get_user_profile'):
                        profile = long_memory.get_user_profile()
                        if profile:
                            logger.info(f"✅ [ADAPTER] Получен профиль пользователя: {profile}")
                            
                            facts_parts = []
                            if profile.get('name'):
                                facts_parts.append(f"• Имя: {profile['name']}")
                            if profile.get('age'):
                                facts_parts.append(f"• Возраст: {profile['age']} лет")
                            if profile.get('interests'):
                                facts_parts.append(f"• Интересы: {', '.join(profile['interests'])}")
                            if profile.get('favorite_topics'):
                                facts_parts.append(f"• Любимые темы: {', '.join([t[0] if isinstance(t, tuple) else str(t) for t in profile['favorite_topics'][:3]])}")
                            
                            if facts_parts:
                                result = "\n".join(facts_parts)
                                logger.info(f"✅ [ADAPTER] Сформированы факты из профиля HybridMemory: {len(result)} символов")
                                return result
                    
                    # Альтернативно: поиск в памяти
                    if hasattr(long_memory, 'search_memory'):
                        search_results = long_memory.search_memory("имя зовут возраст", limit=5)
                        if search_results:
                            facts_parts = []
                            for result in search_results:
                                content = result.get('content', '')
                                if content and len(content) > 10:
                                    facts_parts.append(f"• {content}")
                            
                            if facts_parts:
                                result = "\n".join(facts_parts[:5])
                                logger.info(f"✅ [ADAPTER] Сформированы факты из поиска HybridMemory: {len(result)} символов")
                                return result
                except Exception as e:
                    logger.warning(f"⚠️ [ADAPTER] HybridMemory long_memory failed: {e}")
            
            # Вариант 3: Попытка получить данные напрямую
            if hasattr(self.memory_manager, 'get_user_profile'):
                try:
                    profile = self.memory_manager.get_user_profile()
                    if profile:
                        facts_parts = []
                        if profile.get('name'):
                            facts_parts.append(f"• Имя: {profile['name']}")
                        if profile.get('age'):
                            facts_parts.append(f"• Возраст: {profile['age']} лет")
                        if profile.get('interests'):
                            facts_parts.append(f"• Интересы: {', '.join(profile['interests'])}")
                        
                        if facts_parts:
                            result = "\n".join(facts_parts)
                            logger.info(f"✅ [ADAPTER] Сформированы факты из direct profile: {len(result)} символов")
                            return result
                except Exception as e:
                    logger.warning(f"⚠️ [ADAPTER] direct get_user_profile failed: {e}")
            
            logger.warning(f"❌ [ADAPTER] Не удалось получить долгосрочные факты для {user_id}")
            logger.info(f"❌ [ADAPTER] Доступные атрибуты memory_manager: {[attr for attr in dir(self.memory_manager) if not attr.startswith('_')]}")
            return None
            
        except Exception as e:
            logger.warning(f"❌ [ADAPTER] Ошибка получения долгосрочных фактов: {e}")
            return None
    
    def _get_semantic_context(self, user_id: str, query: str) -> Optional[str]:
        """Получает семантический контекст по запросу"""
        try:
            logger.info(f"🔍 [ADAPTER] Получаем семантический контекст для {user_id}, запрос: {query[:50]}...")
            
            # ИСПРАВЛЕНИЕ: Проверяем разные типы memory_manager
            
            # Вариант 1: MemoryLevelsManager с long_term
            if hasattr(self.memory_manager, 'long_term') and self.memory_manager.long_term:
                logger.info(f"🔍 [ADAPTER] long_term найден для семантического поиска")
                
                try:
                    # Ищем релевантные документы по запросу
                    relevant_docs = self.memory_manager.long_term.search_memories(
                        query=query,
                        limit=3
                    )
                    
                    logger.info(f"🔍 [ADAPTER] Семантический поиск вернул {len(relevant_docs) if relevant_docs else 0} документов")
                    
                    if relevant_docs:
                        context_parts = []
                        for doc in relevant_docs:
                            content = doc.get('content', '')
                            logger.info(f"🔍 [ADAPTER] Обрабатываем документ: {content[:50]}...")
                            
                            if content and len(content) > 20:  # Фильтруем слишком короткие
                                context_parts.append(f"📝 {content}")
                                logger.info(f"✅ [ADAPTER] Документ добавлен в семантический контекст")
                            else:
                                logger.info(f"⚠️ [ADAPTER] Документ отфильтрован (слишком короткий): {len(content)} символов")
                        
                        if context_parts:
                            result = "\n".join(context_parts)
                            logger.info(f"✅ [ADAPTER] Сформирован семантический контекст: {len(context_parts)} документов, {len(result)} символов")
                            return result
                        else:
                            logger.warning(f"⚠️ [ADAPTER] Документы найдены, но все отфильтрованы")
                    else:
                        logger.warning(f"⚠️ [ADAPTER] Релевантные документы не найдены")
                except Exception as e:
                    logger.warning(f"⚠️ [ADAPTER] long_term.search_memories failed: {e}")
            
            # Вариант 2: HybridMemory с long_memory
            if hasattr(self.memory_manager, 'long_memory') and self.memory_manager.long_memory:
                try:
                    long_memory = self.memory_manager.long_memory
                    logger.info(f"🔍 [ADAPTER] HybridMemory.long_memory найден для семантического поиска")
                    
                    if hasattr(long_memory, 'search_memory'):
                        search_results = long_memory.search_memory(query, limit=3)
                        if search_results:
                            context_parts = []
                            for result in search_results:
                                content = result.get('content', '')
                                if content and len(content) > 20:
                                    context_parts.append(f"📝 {content}")
                            
                            if context_parts:
                                result = "\n".join(context_parts)
                                logger.info(f"✅ [ADAPTER] Сформирован семантический контекст из HybridMemory: {len(result)} символов")
                                return result
                except Exception as e:
                    logger.warning(f"⚠️ [ADAPTER] HybridMemory semantic search failed: {e}")
            
            # Вариант 3: Простой поиск по всем доступным методам
            search_methods = ['search_memory', 'search_memories', 'get_relevant_context']
            for method_name in search_methods:
                if hasattr(self.memory_manager, method_name):
                    try:
                        method = getattr(self.memory_manager, method_name)
                        if callable(method):
                            logger.info(f"🔍 [ADAPTER] Пытаемся использовать метод {method_name}")
                            
                            # Разные сигнатуры методов
                            if method_name == 'get_relevant_context':
                                results = method(query)
                            else:
                                results = method(query, limit=3)
                            
                            if results:
                                context_parts = []
                                for item in results:
                                    if isinstance(item, dict):
                                        content = item.get('content', '')
                                    elif isinstance(item, str):
                                        content = item
                                    else:
                                        content = str(item)
                                    
                                    if content and len(content) > 20:
                                        context_parts.append(f"📝 {content}")
                                
                                if context_parts:
                                    result = "\n".join(context_parts)
                                    logger.info(f"✅ [ADAPTER] Сформирован семантический контекст через {method_name}: {len(result)} символов")
                                    return result
                    except Exception as e:
                        logger.warning(f"⚠️ [ADAPTER] {method_name} failed: {e}")
            
            logger.warning(f"❌ [ADAPTER] Не удалось получить семантический контекст для {user_id}")
            logger.info(f"❌ [ADAPTER] Доступные методы memory_manager: {[method for method in dir(self.memory_manager) if 'search' in method.lower() or 'context' in method.lower()]}")
            return None
            
        except Exception as e:
            logger.warning(f"❌ [ADAPTER] Ошибка получения семантического контекста: {e}")
            return None
    
    def get_question_counter(self, user_id: str) -> int:
        """Получает счетчик вопросов для контроля частоты"""
        try:
            # Можно хранить в Redis или БД, пока используем простой счетчик
            # В реальной реализации здесь должна быть персистентность
            # Реализуем персистентный счетчик через memory_manager
            if hasattr(self.memory_manager, 'get_user_stats'):
                stats = self.memory_manager.get_user_stats()
                return stats.get('question_count', 0)
            return 0
        except Exception as e:
            logger.warning(f"Ошибка получения счетчика вопросов: {e}")
            return 0
    
    def can_ask_question(self, user_id: str) -> bool:
        """Проверяет, можно ли задать вопрос"""
        counter = self.get_question_counter(user_id)
        return (counter % 3 == 2)  # Вопрос каждый 3-й раз
