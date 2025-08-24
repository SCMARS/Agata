"""
Vector Memory Adapter with semantic search for long-term memory
"""
import json
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from .base import MemoryAdapter, Message, MemoryContext

class VectorMemory(MemoryAdapter):
    """
    Векторная память для долгосрочного хранения с семантическим поиском
    """
    
    def __init__(self, user_id: str, max_memories: int = 1000):
        self.user_id = user_id
        self.max_memories = max_memories
        self.memories: List[Dict[str, Any]] = []
        self.embeddings_cache = {}
        
    async def add_message(self, message: Message, context: MemoryContext) -> None:
        """Добавить сообщение в долгосрочную память"""
        # Создаем память только для важных сообщений
        is_important = await self._is_important_message(message, context)
        print(f"🧠 VectorMemory: Сообщение '{message.content[:50]}...' важное: {is_important}")
        
        if is_important:
            importance_score = await self._calculate_importance(message, context)
            memory_entry = {
                'id': f"{self.user_id}_{datetime.utcnow().isoformat()}",
                'content': message.content,
                'role': message.role,
                'timestamp': message.timestamp.isoformat(),
                'day_number': context.day_number,
                'importance_score': importance_score,
                'topics': await self._extract_topics(message.content),
                'emotions': await self._detect_emotions(message.content),
                'metadata': {
                    'user_id': self.user_id,
                    'message_length': len(message.content),
                    'has_question': '?' in message.content,
                    'day_context': context.day_number
                }
            }
            
            # Добавляем в память
            self.memories.append(memory_entry)
            print(f"🧠 VectorMemory: Добавлено в память (важность: {importance_score:.2f}). Всего воспоминаний: {len(self.memories)}")
            
            # Ограничиваем размер памяти
            if len(self.memories) > self.max_memories:
                # Удаляем наименее важные воспоминания
                self.memories.sort(key=lambda x: x['importance_score'], reverse=True)
                self.memories = self.memories[:self.max_memories]
        else:
            print(f"🧠 VectorMemory: Сообщение не важное, не сохраняем")
    
    async def get_context(self, context: MemoryContext, query: str = "") -> str:
        """Получить контекст из долгосрочной памяти"""
        print(f"🧠 VectorMemory: Запрос контекста. Всего воспоминаний: {len(self.memories)}")
        
        if not self.memories:
            print(f"🧠 VectorMemory: Нет воспоминаний, возвращаем базовый ответ")
            return "Это наше первое общение."
        
        # Поиск релевантных воспоминаний
        relevant_memories = await self._search_memories(query, context, limit=5)
        
        # Если нет релевантных по запросу, берем самые важные
        if not relevant_memories and self.memories:
            relevant_memories = sorted(self.memories, key=lambda x: x['importance_score'], reverse=True)[:3]
            print(f"🧠 VectorMemory: Нет релевантных, взяли {len(relevant_memories)} самых важных")
        
        if not relevant_memories:
            return "У нас уже было несколько разговоров."
        
        # Формируем умный контекст
        context_parts = []
        
        # Простое формирование контекста (временно упрощено)
        context_parts.append(f"Мы общаемся уже {len(self.memories)} сообщений.")
        
        # Добавляем важные воспоминания
        for memory in relevant_memories[:3]:
            if memory['importance_score'] > 0.5:
                content_preview = memory['content'][:80] + "..." if len(memory['content']) > 80 else memory['content']
                context_parts.append(f"Помню: {content_preview}")
        
        print(f"🧠 Сформированный контекст: {' | '.join(context_parts)}")
        
        return " | ".join(context_parts)
    
    async def _extract_user_profile(self, memories: List[Dict]) -> str:
        """Извлечь профиль пользователя из воспоминаний"""
        try:
            profile_parts = []
            
            for memory in memories:
                content = memory.get('content', '').lower()
                
                # Имя
                if 'меня зовут' in content or 'мое имя' in content:
                    # Простое извлечение имени
                    words = memory.get('content', '').split()
                    for i, word in enumerate(words):
                        if word.lower() in ['зовут', 'имя'] and i + 1 < len(words):
                            name = words[i + 1].strip('.,!?').title()
                            if name and len(name) > 1:
                                profile_parts.append(f"имя {name}")
                                break
            
            # Возраст
            if 'мне ' in content and 'лет' in content:
                words = content.split()
                for i, word in enumerate(words):
                    if word == 'мне' and i + 1 < len(words):
                        next_word = words[i + 1]
                        if next_word.isdigit():
                            profile_parts.append(f"{next_word} лет")
                            break
            
            # Профессия
            if 'работаю' in content or 'профессия' in content:
                if 'учителем' in content: profile_parts.append("учитель")
                elif 'врачом' in content: profile_parts.append("врач")
                elif 'программистом' in content: profile_parts.append("программист")
                elif 'дизайнером' in content: profile_parts.append("дизайнер")
                elif 'инженером' in content: profile_parts.append("инженер")
            
            # Питомцы
            if 'кот' in content or 'собака' in content:
                words = memory['content'].split()
                for i, word in enumerate(words):
                    if word.lower() in ['кот', 'собака'] and 'имени' in content:
                        # Ищем имя питомца
                        for j in range(max(0, i-5), min(len(words), i+5)):
                            if words[j].lower() in ['имени', 'зовут']:
                                if j + 1 < len(words):
                                    pet_name = words[j + 1].strip('.,!?').title()
                                    pet_type = "кот" if "кот" in content else "собака"
                                    profile_parts.append(f"{pet_type} {pet_name}")
                                    break
        
            return ", ".join(list(set(profile_parts))[:3])  # Убираем дубли, берем первые 3
        except Exception as e:
            print(f"🧠 Ошибка извлечения профиля: {e}")
            return ""
    
    async def _extract_conversation_themes(self, memories: List[Dict]) -> str:
        """Извлечь темы разговоров"""
        try:
            themes = set()
            
            for memory in memories:
                topics = memory.get('topics', [])
                themes.update(topics[:2])  # Берем первые 2 темы из каждого воспоминания
            
            return ", ".join(list(themes)[:3])
        except Exception as e:
            print(f"🧠 Ошибка извлечения тем: {e}")
            return ""
    
    async def _extract_emotional_context(self, memories: List[Dict]) -> str:
        """Извлечь эмоциональный контекст"""
        try:
            emotions = []
            
            for memory in memories:
                memory_emotions = memory.get('emotions', [])
                emotions.extend(memory_emotions)
            
            if emotions:
                # Находим доминирующую эмоцию
                emotion_counts = {}
                for emotion in emotions:
                    emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
                
                dominant_emotion = max(emotion_counts, key=emotion_counts.get)
                return dominant_emotion
            
            return ""
        except Exception as e:
            print(f"🧠 Ошибка извлечения эмоций: {e}")
            return ""
    
    async def _is_important_message(self, message: Message, context: MemoryContext) -> bool:
        """Определить важность сообщения для долгосрочной памяти"""
        content = message.content.lower()
        
        # 1. ПЕРСОНАЛЬНАЯ ИНФОРМАЦИЯ (высокий приоритет)
        personal_markers = [
            'меня зовут', 'мое имя', 'я работаю', 'моя профессия', 'я учусь',
            'мне ', 'лет', 'живу в', 'из ', 'родом', 'родился', 'родилась',
            'семья', 'родители', 'мама', 'папа', 'брат', 'сестра', 'дети',
            'женат', 'замужем', 'холост', 'не замужем', 'развод',
            'жена', 'муж', 'сын', 'дочь', 'ребенок', 'дочка', 'сынок'
        ]
        
        # 2. ИНТЕРЕСЫ И ХОББИ
        interests_markers = [
            'мне нравится', 'я люблю', 'увлекаюсь', 'хобби', 'интересуюсь',
            'занимаюсь', 'играю в', 'читаю', 'смотрю', 'слушаю',
            'коллекционирую', 'путешествую', 'готовлю'
        ]
        
        # 3. ЭМОЦИИ И ПЕРЕЖИВАНИЯ
        emotional_markers = [
            'переживаю', 'волнуюсь', 'боюсь', 'радуюсь', 'грущу',
            'злюсь', 'расстраиваюсь', 'счастлив', 'несчастлив',
            'проблема', 'беспокоит', 'тревожит', 'мечтаю'
        ]
        
        # 4. ПЛАНЫ И ЦЕЛИ
        goals_markers = [
            'планирую', 'хочу', 'собираюсь', 'мечтаю', 'цель',
            'надеюсь', 'стремлюсь', 'пытаюсь', 'учусь', 'изучаю'
        ]
        
        # 5. ОТНОШЕНИЯ И СОЦИАЛЬНЫЕ СВЯЗИ
        social_markers = [
            'друзья', 'подруга', 'друг', 'коллеги', 'знакомые',
            'отношения', 'встречаюсь', 'расстались', 'познакомился',
            'общаюсь', 'дружу', 'ссорюсь'
        ]
        
        # 6. ВАЖНЫЕ СОБЫТИЯ
        events_markers = [
            'случилось', 'произошло', 'событие', 'новость',
            'вчера', 'сегодня', 'недавно', 'давно', 'помню',
            'забыл', 'напомни', 'расскажу', 'история'
        ]
        
        # 7. ВОПРОСЫ О ПАМЯТИ
        memory_markers = [
            'помнишь', 'помни', 'запомни', 'забыл', 'напомни',
            'рассказывал', 'говорил', 'упоминал'
        ]
        
        # Проверяем все категории
        categories = [
            personal_markers, interests_markers, emotional_markers,
            goals_markers, social_markers, events_markers, memory_markers
        ]
        
        importance_score = 0
        for category in categories:
            if any(marker in content for marker in category):
                importance_score += 1
        
        # Дополнительные факторы
        is_detailed = len(message.content) > 80  # Детальные сообщения
        has_questions = '?' in message.content  # Вопросы пользователя
        is_first_person = any(word in content for word in ['я ', 'мне ', 'мой ', 'моя ', 'мои '])
        
        # Контекстуальная важность
        is_response_to_question = any(word in content for word in ['да', 'нет', 'конечно', 'возможно'])
        
        # Финальная оценка
        final_score = importance_score
        if is_detailed: final_score += 0.5
        if has_questions: final_score += 0.3
        if is_first_person: final_score += 0.4
        if is_response_to_question: final_score += 0.2
        
        print(f"🧠 Анализ важности: '{content[:30]}...' = {final_score:.1f} баллов")
        
        return final_score >= 0.8  # Понижен порог важности
    
    async def _calculate_importance(self, message: Message, context: MemoryContext) -> float:
        """Рассчитать важность сообщения (0.0 - 1.0)"""
        score = 0.0
        content = message.content.lower()
        
        # Персональная информация (+0.4)
        personal_markers = ['меня зовут', 'мое имя', 'я работаю', 'живу в']
        if any(marker in content for marker in personal_markers):
            score += 0.4
        
        # Эмоциональное содержание (+0.3)
        emotional_markers = ['люблю', 'ненавижу', 'боюсь', 'мечтаю', 'расстраивает', 'радует']
        if any(marker in content for marker in emotional_markers):
            score += 0.3
        
        # Длина сообщения (+0.2)
        if len(message.content) > 100:
            score += 0.2
        
        # Первые дни общения важнее (+0.2)
        if context.day_number <= 3:
            score += 0.2
        
        # Вопросы (+0.1)
        if '?' in message.content:
            score += 0.1
        
        return min(score, 1.0)
    
    async def _extract_topics(self, content: str) -> List[str]:
        """Извлечь темы из сообщения"""
        content_lower = content.lower()
        topics = []
        
        topic_keywords = {
            'работа': ['работа', 'работаю', 'профессия', 'карьера', 'коллеги', 'начальник'],
            'семья': ['семья', 'родители', 'мама', 'папа', 'брат', 'сестра', 'дети'],
            'отношения': ['отношения', 'любовь', 'парень', 'девушка', 'свидание', 'друзья'],
            'хобби': ['хобби', 'увлечение', 'спорт', 'музыка', 'фильмы', 'игры', 'чтение'],
            'здоровье': ['здоровье', 'болею', 'врач', 'лечение', 'самочувствие'],
            'планы': ['планы', 'мечты', 'цели', 'хочу', 'планирую', 'надеюсь'],
            'проблемы': ['проблема', 'беспокоит', 'стресс', 'переживаю', 'трудности']
        }
        
        for topic, keywords in topic_keywords.items():
            if any(keyword in content_lower for keyword in keywords):
                topics.append(topic)
        
        return topics
    
    async def _detect_emotions(self, content: str) -> List[str]:
        """Определить эмоции в сообщении"""
        content_lower = content.lower()
        emotions = []
        
        emotion_keywords = {
            'радость': ['радость', 'счастье', 'весело', 'отлично', 'прекрасно', ':)', '😊', '😄'],
            'грусть': ['грусть', 'печаль', 'расстроен', 'плохо', 'ужасно', ':(', '😢', '😭'],
            'злость': ['злость', 'сердит', 'раздражает', 'бесит', 'ненавижу', '😠', '😡'],
            'страх': ['страх', 'боюсь', 'переживаю', 'волнуюсь', 'тревожно', '😰', '😱'],
            'удивление': ['удивление', 'удивлен', 'невероятно', 'вау', 'ого', '😮', '😲'],
            'усталость': ['устал', 'утомлен', 'измучен', 'нет сил', 'вымотан']
        }
        
        for emotion, keywords in emotion_keywords.items():
            if any(keyword in content_lower for keyword in keywords):
                emotions.append(emotion)
        
        return emotions if emotions else ['нейтральное']
    
    async def _search_memories(self, query: str, context: MemoryContext, limit: int = 5) -> List[Dict[str, Any]]:
        """Поиск релевантных воспоминаний"""
        if not query:
            # Если запроса нет, возвращаем последние важные
            recent_memories = [m for m in self.memories if m['importance_score'] > 0.5]
            return sorted(recent_memories, key=lambda x: x['timestamp'], reverse=True)[:limit]
        
        # Простой поиск по ключевым словам (в будущем заменить на векторный)
        query_words = query.lower().split()
        scored_memories = []
        
        for memory in self.memories:
            score = 0
            content_lower = memory['content'].lower()
            
            # Поиск по содержанию
            for word in query_words:
                if word in content_lower:
                    score += 1
            
            # Поиск по темам
            for topic in memory.get('topics', []):
                if any(word in topic for word in query_words):
                    score += 2
            
            # Бонус за важность
            score += memory['importance_score']
            
            if score > 0:
                memory_with_score = memory.copy()
                memory_with_score['search_score'] = score
                scored_memories.append(memory_with_score)
        
        # Сортируем по релевантности
        scored_memories.sort(key=lambda x: x['search_score'], reverse=True)
        return scored_memories[:limit]
    
    async def get_user_profile(self) -> Dict[str, Any]:
        """Получить профиль пользователя на основе памяти"""
        if not self.memories:
            return {}
        
        profile = {
            'user_id': self.user_id,
            'total_messages': len(self.memories),
            'communication_days': len(set(m['day_number'] for m in self.memories)),
            'favorite_topics': [],
            'emotional_profile': {},
            'personal_info': {},
            'preferences': {}
        }
        
        # Анализ тем
        all_topics = []
        for memory in self.memories:
            all_topics.extend(memory.get('topics', []))
        
        if all_topics:
            topic_counts = {}
            for topic in all_topics:
                topic_counts[topic] = topic_counts.get(topic, 0) + 1
            
            profile['favorite_topics'] = sorted(topic_counts.items(), 
                                              key=lambda x: x[1], reverse=True)[:3]
        
        # Эмоциональный профиль
        all_emotions = []
        for memory in self.memories:
            all_emotions.extend(memory.get('emotions', []))
        
        if all_emotions:
            emotion_counts = {}
            for emotion in all_emotions:
                emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
            
            profile['emotional_profile'] = emotion_counts
        
        # Извлечение персональной информации
        personal_memories = [m for m in self.memories if 'меня зовут' in m['content'].lower() 
                           or 'я работаю' in m['content'].lower()]
        
        if personal_memories:
            profile['personal_info'] = {
                'has_name': any('меня зовут' in m['content'].lower() for m in personal_memories),
                'has_profession': any('я работаю' in m['content'].lower() for m in personal_memories),
                'details_shared': len(personal_memories)
            }
        
        return profile
    
    async def search_memory(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Поиск в памяти по запросу"""
        context = MemoryContext(user_id=self.user_id)
        return await self._search_memories(query, context, limit)
    
    async def summarize_conversation(self, messages: List[Message]) -> str:
        """Суммаризация разговора"""
        if not messages:
            return "Разговор пуст."
        
        # Простая суммаризация - берем ключевые моменты
        user_messages = [msg for msg in messages if msg.role == 'user']
        
        if len(user_messages) <= 3:
            return f"Краткий разговор из {len(user_messages)} сообщений."
        
        # Анализируем темы и эмоции
        all_content = ' '.join([msg.content for msg in user_messages])
        topics = await self._extract_topics(all_content)
        emotions = await self._detect_emotions(all_content)
        
        summary_parts = [f"Разговор из {len(user_messages)} сообщений"]
        
        if topics:
            summary_parts.append(f"Основные темы: {', '.join(topics[:3])}")
        
        if emotions and emotions[0] != 'нейтральное':
            summary_parts.append(f"Эмоциональный тон: {emotions[0]}")
        
        return ". ".join(summary_parts) + "."
    
    async def clear_memory(self) -> None:
        """Очистить память пользователя"""
        self.memories.clear()
        self.embeddings_cache.clear() 