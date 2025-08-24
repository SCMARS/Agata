"""
Hybrid Memory Adapter - объединяет кратковременную и долгосрочную память
"""
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from .base import MemoryAdapter, Message, MemoryContext
from .buffer_memory import BufferMemory
from .vector_memory import VectorMemory

class HybridMemory(MemoryAdapter):
    """
    Гибридная память, объединяющая:
    - BufferMemory: для кратковременной памяти (последние 10-20 сообщений)
    - VectorMemory: для долгосрочной памяти с семантическим поиском
    """
    
    def __init__(self, user_id: str, short_memory_size: int = 15, long_memory_size: int = 1000):
        self.user_id = user_id
        self.short_memory = BufferMemory(user_id, max_messages=short_memory_size)
        self.long_memory = VectorMemory(user_id, max_memories=long_memory_size)
        
        # Счетчики для аналитики
        self.total_messages = 0
        self.conversation_start = datetime.utcnow()
        
    async def add_message(self, message: Message, context: MemoryContext) -> None:
        """Добавить сообщение в обе системы памяти"""
        self.total_messages += 1
        
        # Добавляем в кратковременную память (все сообщения)
        await self.short_memory.add_message(message, context)
        
        # Добавляем в долгосрочную память (только важные)
        await self.long_memory.add_message(message, context)
    
    async def get_context(self, context: MemoryContext, query: str = "") -> str:
        """Получить объединенный контекст из обеих систем памяти"""
        # Получаем контекст из кратковременной памяти
        short_context = await self.short_memory.get_context(context)
        
        # Получаем контекст из долгосрочной памяти
        long_context = await self.long_memory.get_context(context, query)
        
        # Создаем статистику общения
        days_communicating = (datetime.utcnow() - self.conversation_start).days + 1
        communication_stats = f"День общения: {context.day_number} | Всего сообщений: {self.total_messages}"
        
        # Объединяем контексты
        context_parts = [communication_stats]
        
        if long_context and long_context != "Это наше первое общение.":
            context_parts.append(f"Долгосрочная память: {long_context}")
        
        if short_context:
            context_parts.append(f"Недавние сообщения: {short_context}")
        
        return " | ".join(context_parts)
    
    async def get_user_profile(self) -> Dict[str, Any]:
        """Получить расширенный профиль пользователя"""
        # Получаем базовый профиль из долгосрочной памяти
        profile = await self.long_memory.get_user_profile()
        
        # Добавляем данные из кратковременной памяти
        recent_messages = self.short_memory.messages
        
        if recent_messages:
            # Анализ последних сообщений
            recent_content = [msg.content for msg in recent_messages[-5:] if msg.role == 'user']
            recent_text = ' '.join(recent_content).lower()
            
            # Настроение в последних сообщениях
            current_mood = await self._analyze_recent_mood(recent_text)
            
            # Активность общения
            activity_level = await self._calculate_activity_level()
            
            profile.update({
                'recent_mood': current_mood,
                'activity_level': activity_level,
                'last_message_time': recent_messages[-1].timestamp.isoformat() if recent_messages else None,
                'session_length': len(recent_messages),
                'days_since_start': (datetime.utcnow() - self.conversation_start).days + 1
            })
        
        return profile
    
    async def _analyze_recent_mood(self, recent_text: str) -> str:
        """Анализ настроения по последним сообщениям"""
        mood_indicators = {
            'positive': ['хорошо', 'отлично', 'прекрасно', 'радость', 'счастлив', 'весело', ':)', '😊'],
            'negative': ['плохо', 'ужасно', 'грустно', 'расстроен', 'проблема', ':(', '😢'],
            'neutral': ['нормально', 'обычно', 'так себе', 'не знаю'],
            'excited': ['супер', 'классно', 'потрясающе', 'ого', 'вау', '!!!!'],
            'tired': ['устал', 'утомлен', 'нет сил', 'сонный'],
            'stressed': ['стресс', 'переживаю', 'волнуюсь', 'беспокоюсь', 'нервничаю']
        }
        
        mood_scores = {}
        for mood, indicators in mood_indicators.items():
            score = sum(1 for indicator in indicators if indicator in recent_text)
            if score > 0:
                mood_scores[mood] = score
        
        if not mood_scores:
            return 'neutral'
        
        return max(mood_scores, key=mood_scores.get)
    
    async def _calculate_activity_level(self) -> str:
        """Вычислить уровень активности пользователя"""
        if self.total_messages < 5:
            return 'new'
        elif self.total_messages < 20:
            return 'moderate'
        elif self.total_messages < 50:
            return 'active'
        else:
            return 'very_active'
    
    async def get_conversation_insights(self) -> Dict[str, Any]:
        """Получить инсайты о развитии разговора"""
        profile = await self.get_user_profile()
        
        insights = {
            'relationship_stage': await self._determine_relationship_stage(),
            'communication_patterns': await self._analyze_communication_patterns(),
            'suggested_topics': await self._suggest_topics(),
            'emotional_journey': await self._track_emotional_journey(),
            'personalization_level': await self._calculate_personalization_level()
        }
        
        return insights
    
    async def _determine_relationship_stage(self) -> str:
        """Определить стадию отношений с пользователем"""
        profile = await self.long_memory.get_user_profile()
        
        if not profile:
            return 'introduction'
        
        personal_info = profile.get('personal_info', {})
        total_messages = profile.get('total_messages', 0)
        communication_days = profile.get('communication_days', 1)
        
        if total_messages < 5:
            return 'introduction'
        elif not personal_info.get('has_name', False) and total_messages < 10:
            return 'getting_acquainted'
        elif personal_info.get('has_name', False) and total_messages < 30:
            return 'building_trust'
        elif personal_info.get('has_profession', False) and communication_days > 3:
            return 'close_friend'
        else:
            return 'confidant'
    
    async def _analyze_communication_patterns(self) -> Dict[str, Any]:
        """Анализ паттернов общения"""
        recent_messages = self.short_memory.messages
        
        if len(recent_messages) < 3:
            return {'pattern': 'insufficient_data'}
        
        # Анализ длины сообщений
        user_messages = [msg for msg in recent_messages if msg.role == 'user']
        avg_length = sum(len(msg.content) for msg in user_messages) / len(user_messages) if user_messages else 0
        
        # Анализ использования вопросов
        questions_count = sum(1 for msg in user_messages if '?' in msg.content)
        question_ratio = questions_count / len(user_messages) if user_messages else 0
        
        # Анализ эмоциональности
        emotional_indicators = ['!', '😊', '😢', '😡', 'очень', 'сильно']
        emotional_messages = sum(1 for msg in user_messages 
                               if any(indicator in msg.content for indicator in emotional_indicators))
        emotional_ratio = emotional_messages / len(user_messages) if user_messages else 0
        
        return {
            'message_length': 'long' if avg_length > 100 else 'short' if avg_length < 30 else 'medium',
            'question_frequency': 'high' if question_ratio > 0.5 else 'low' if question_ratio < 0.2 else 'medium',
            'emotional_expression': 'high' if emotional_ratio > 0.6 else 'low' if emotional_ratio < 0.3 else 'medium',
            'communication_style': await self._determine_communication_style(avg_length, question_ratio, emotional_ratio)
        }
    
    async def _determine_communication_style(self, avg_length: float, question_ratio: float, emotional_ratio: float) -> str:
        """Определить стиль общения пользователя"""
        if avg_length > 100 and emotional_ratio > 0.5:
            return 'expressive_storyteller'
        elif question_ratio > 0.6:
            return 'curious_questioner'
        elif avg_length < 30 and question_ratio < 0.2:
            return 'laconic_responder'
        elif emotional_ratio > 0.7:
            return 'emotional_sharer'
        else:
            return 'balanced_conversationalist'
    
    async def _suggest_topics(self) -> List[str]:
        """Предложить темы для разговора на основе интересов пользователя"""
        profile = await self.long_memory.get_user_profile()
        
        if not profile or not profile.get('favorite_topics'):
            return ['хобби', 'планы', 'настроение']
        
        favorite_topics = [topic[0] for topic in profile['favorite_topics']]
        
        # Предлагаем смежные темы
        related_topics = {
            'работа': ['карьера', 'коллеги', 'проекты'],
            'семья': ['детство', 'традиции', 'праздники'],
            'отношения': ['дружба', 'любовь', 'общение'],
            'хобби': ['творчество', 'спорт', 'путешествия'],
            'здоровье': ['самочувствие', 'спорт', 'питание'],
            'планы': ['мечты', 'цели', 'будущее']
        }
        
        suggestions = []
        for topic in favorite_topics:
            suggestions.extend(related_topics.get(topic, []))
        
        return list(set(suggestions))[:5]
    
    async def _track_emotional_journey(self) -> List[Dict[str, Any]]:
        """Отследить эмоциональное путешествие пользователя"""
        long_term_memories = self.long_memory.memories
        
        if not long_term_memories:
            return []
        
        emotional_timeline = []
        for memory in sorted(long_term_memories, key=lambda x: x['timestamp']):
            emotions = memory.get('emotions', [])
            if emotions and emotions[0] != 'нейтральное':
                emotional_timeline.append({
                    'day': memory['day_number'],
                    'emotion': emotions[0],
                    'context': memory['content'][:50] + '...',
                    'importance': memory['importance_score']
                })
        
        return emotional_timeline[-10:]  # Последние 10 эмоциональных моментов
    
    async def _calculate_personalization_level(self) -> float:
        """Вычислить уровень персонализации (0.0 - 1.0)"""
        profile = await self.long_memory.get_user_profile()
        
        if not profile:
            return 0.0
        
        score = 0.0
        
        # Персональная информация
        personal_info = profile.get('personal_info', {})
        if personal_info.get('has_name'):
            score += 0.3
        if personal_info.get('has_profession'):
            score += 0.2
        
        # Количество общения
        total_messages = profile.get('total_messages', 0)
        if total_messages > 10:
            score += 0.2
        if total_messages > 50:
            score += 0.1
        
        # Эмоциональная связь
        emotional_profile = profile.get('emotional_profile', {})
        if len(emotional_profile) > 3:
            score += 0.1
        
        # Любимые темы
        favorite_topics = profile.get('favorite_topics', [])
        if len(favorite_topics) > 2:
            score += 0.1
        
        return min(score, 1.0)
    
    async def search_memory(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Поиск в памяти - делегируем долгосрочной памяти"""
        return await self.long_memory.search_memory(query, limit)
    
    async def summarize_conversation(self, messages: List[Message]) -> str:
        """Суммаризация разговора - делегируем долгосрочной памяти"""
        return await self.long_memory.summarize_conversation(messages)
    
    async def clear_memory(self) -> None:
        """Очистить всю память пользователя"""
        await self.short_memory.clear_memory()
        await self.long_memory.clear_memory()
        self.total_messages = 0
        self.conversation_start = datetime.utcnow() 