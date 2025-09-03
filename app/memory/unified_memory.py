"""
Унифицированная система памяти - решение архитектурных проблем
Объединяет краткосрочную и долгосрочную память в единую логичную систему
"""

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from .intelligent_vector_memory import IntelligentVectorMemory

logger = logging.getLogger(__name__)

class UnifiedMemoryManager:
    """
    Унифицированный менеджер памяти
    
    ЛОГИКА:
    - Сообщения 1-10: хранятся в short_term_window
    - Сообщения 11+: старые переносятся в vector_db, новые в window
    - Поиск: сначала window, потом vector_db
    """
    
    def __init__(self, user_id: str, window_size: int = 10):
        self.user_id = user_id
        self.window_size = window_size
        self.short_term_window = []  # Последние N сообщений
        self.message_count = 0
        
        # Инициализируем векторную БД
        try:
            self.vector_db = IntelligentVectorMemory(user_id)
            self.vector_available = True
            logger.info(f"🧠 [UNIFIED-{user_id}] Инициализирована векторная БД")
        except Exception as e:
            logger.error(f"❌ [UNIFIED-{user_id}] Ошибка инициализации векторной БД: {e}")
            self.vector_db = None
            self.vector_available = False
    
    def add_message(self, role: str, content: str, metadata: Dict[str, Any] = None) -> Dict[str, bool]:
        """
        Добавляет сообщение в унифицированную систему памяти
        
        Args:
            role: 'user' или 'assistant'
            content: текст сообщения
            metadata: дополнительные данные
            
        Returns:
            Результаты сохранения
        """
        self.message_count += 1
        
        # Создаем объект сообщения
        message = {
            'role': role,
            'content': content,
            'metadata': metadata or {},
            'timestamp': datetime.utcnow().isoformat(),
            'message_id': self.message_count
        }
        
        logger.info(f"📝 [UNIFIED-{self.user_id}] Добавляем сообщение #{self.message_count}: {content[:50]}...")
        
        results = {'short_term': False, 'long_term': False}
        
        # Добавляем в окно краткосрочной памяти
        self.short_term_window.append(message)
        results['short_term'] = True
        
        # Если окно переполнено - переносим старое сообщение в векторную БД
        if len(self.short_term_window) > self.window_size:
            oldest_message = self.short_term_window.pop(0)
            
            if self.vector_available:
                try:
                    # Переносим в векторную БД
                    self.vector_db.add_document(
                        content=oldest_message['content'],
                        metadata={
                            **oldest_message['metadata'],
                            'role': oldest_message['role'],
                            'timestamp': oldest_message['timestamp'],
                            'transferred_from_short_term': True
                        }
                    )
                    results['long_term'] = True
                    logger.info(f"🗄️ [UNIFIED-{self.user_id}] Перенесли сообщение #{oldest_message['message_id']} в векторную БД")
                except Exception as e:
                    logger.error(f"❌ [UNIFIED-{self.user_id}] Ошибка переноса в векторную БД: {e}")
            else:
                logger.warning(f"⚠️ [UNIFIED-{self.user_id}] Векторная БД недоступна, сообщение потеряно")
        
        logger.info(f"✅ [UNIFIED-{self.user_id}] Сообщение добавлено. Окно: {len(self.short_term_window)}, Всего: {self.message_count}")
        return results
    
    def get_context_for_prompt(self, query: str = "") -> Dict[str, str]:
        """
        Получает контекст для промпта с умным выбором источника
        
        Args:
            query: текущий запрос пользователя
            
        Returns:
            Словарь с контекстом для промпта
        """
        logger.info(f"🔍 [UNIFIED-{self.user_id}] Получаем контекст. Сообщений: {self.message_count}, В окне: {len(self.short_term_window)}")
        
        context = {
            "short_memory_summary": "—",
            "long_memory_facts": "—", 
            "semantic_context": "—"
        }
        
        # 1. Краткосрочная память (всегда доступна)
        if self.short_term_window:
            recent_messages = []
            for msg in self.short_term_window[-5:]:  # Последние 5 сообщений
                role_label = "👤" if msg['role'] == 'user' else "🤖"
                recent_messages.append(f"{role_label} {msg['content']}")
            
            context["short_memory_summary"] = "Недавние сообщения:\n" + "\n".join(recent_messages)
            logger.info(f"✅ [UNIFIED-{self.user_id}] Краткосрочная память: {len(recent_messages)} сообщений")
        
        # 2. Долгосрочная память - ВСЕГДА пытаемся искать в векторной БД если есть запрос
        if self.vector_available and query:
            try:
                # Ищем релевантные факты в векторной БД
                search_results = self.vector_db.search_similar(query, similarity_threshold=0.0, max_results=8)
                
                if search_results:
                    facts = []
                    for result in search_results:
                        content = result.get('content', '') or result.get('document', '')
                        if content and len(content) > 10:
                            # Фильтруем только пользовательские сообщения с фактами
                            if not content.startswith(("Добрый", "Привет", "Как дела")):
                                facts.append(f"• {content}")
                    
                    if facts:
                        context["long_memory_facts"] = "Важные факты из истории общения:\n" + "\n".join(facts[:5])
                        context["semantic_context"] = "Контекст поиска:\n" + "\n".join(facts[:3])
                        logger.info(f"✅ [UNIFIED-{self.user_id}] Долгосрочная память: {len(facts)} фактов")
                    else:
                        logger.info(f"⚠️ [UNIFIED-{self.user_id}] Векторная БД не содержит релевантных фактов")
                else:
                    logger.info(f"⚠️ [UNIFIED-{self.user_id}] Поиск в векторной БД не дал результатов")
                    
            except Exception as e:
                logger.error(f"❌ [UNIFIED-{self.user_id}] Ошибка поиска в векторной БД: {e}")
        
        # 3. ДОПОЛНИТЕЛЬНО: Если в краткосрочной памяти есть факты, добавляем их тоже
        if len(context["long_memory_facts"]) <= 5 and self.short_term_window:  # Если долгосрочных фактов мало
            user_messages = [msg for msg in self.short_term_window if msg['role'] == 'user']
            if user_messages:
                recent_facts = []
                for msg in user_messages:
                    content = msg['content']
                    # Ищем сообщения с фактами (имя, возраст, работа, хобби)
                    if any(keyword in content.lower() for keyword in ['зовут', 'лет', 'работаю', 'хобби', 'увлекаюсь', 'senior', 'python']):
                        if not content.startswith("Промежуточное"):
                            recent_facts.append(f"• {content}")
                
                if recent_facts:
                    if context["long_memory_facts"] == "—":
                        context["long_memory_facts"] = "Факты из недавних сообщений:\n" + "\n".join(recent_facts)
                    else:
                        context["long_memory_facts"] += "\n\nИз недавних сообщений:\n" + "\n".join(recent_facts)
                    logger.info(f"✅ [UNIFIED-{self.user_id}] Добавлены факты из краткосрочной памяти: {len(recent_facts)}")
        
        # 4. Логируем что возвращаем
        logger.info(f"📊 [UNIFIED-{self.user_id}] ВОЗВРАЩАЕМ:")
        logger.info(f"   Short: {len(context['short_memory_summary'])} символов")
        logger.info(f"   Facts: {len(context['long_memory_facts'])} символов") 
        logger.info(f"   Semantic: {len(context['semantic_context'])} символов")
        
        return context
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Получает статистику памяти для отладки"""
        return {
            "user_id": self.user_id,
            "total_messages": self.message_count,
            "short_term_count": len(self.short_term_window),
            "window_size": self.window_size,
            "vector_available": self.vector_available,
            "should_use_vector": self.message_count > self.window_size,
            "messages_in_vector": max(0, self.message_count - self.window_size)
        }
    
    def clear_memory(self) -> bool:
        """Очищает всю память"""
        try:
            self.short_term_window.clear()
            self.message_count = 0
            
            if self.vector_available:
                # Здесь можно добавить очистку векторной БД если нужно
                pass
            
            logger.info(f"🧹 [UNIFIED-{self.user_id}] Память очищена")
            return True
        except Exception as e:
            logger.error(f"❌ [UNIFIED-{self.user_id}] Ошибка очистки памяти: {e}")
            return False
