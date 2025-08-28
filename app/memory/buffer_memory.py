from typing import List, Dict, Any
from datetime import datetime, timedelta
import json

from .base import MemoryAdapter, Message, MemoryContext
from ..config.settings import settings

class BufferMemory(MemoryAdapter):
    """Simple buffer memory that keeps recent messages in memory"""
    
    def __init__(self, user_id: str, max_messages: int = 20):
        super().__init__(user_id)
        self.max_messages = max_messages
        self.messages: List[Message] = []
        self.last_activity: datetime = datetime.utcnow()
    
    def add_message(self, message: Message, context: MemoryContext) -> None:
        """Add message to buffer"""
        self.messages.append(message)
        self.last_activity = datetime.utcnow()
        
        # Keep only recent messages
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]
    
    def get_context(self, context: MemoryContext) -> str:
        """Get formatted context from recent messages with key information extraction"""
        if not self.messages:
            return "Это начало вашего разговора."
        
        # Format recent messages
        context_parts = []
        
        # Add time context
        time_gap = datetime.utcnow() - self.last_activity
        if time_gap > timedelta(hours=6):
            context_parts.append(f"Прошло {self._format_time_gap(time_gap)} с последнего сообщения.")
        
        # Extract key information from user messages
        key_info = self._extract_key_information()
        if key_info:
            context_parts.append(f"Ключевая информация: {key_info}")
            print(f"🧠 BufferMemory: Извлечена ключевая информация: {key_info}")
        else:
            print(f"🧠 BufferMemory: Ключевая информация не найдена")
        
        # Add recent conversation summary
        context_parts.append("Недавний разговор:")
        for msg in self.messages[-5:]:  # Last 5 messages
            role = "Пользователь" if msg.role == "user" else "Ты"
            context_parts.append(f"{role}: {msg.content}")
        
        return "\n".join(context_parts)
    
    def _extract_key_information(self) -> str:
        """Extract key information from user messages"""
        user_messages = [msg for msg in self.messages if msg.role == "user"]
        if not user_messages:
            return ""
        
        # Combine all user messages
        all_text = " ".join([msg.content for msg in user_messages])
        text_lower = all_text.lower()
        
        key_info = []
        
        # Extract name
        name_patterns = ["зовут", "меня зовут", "имя"]
        for pattern in name_patterns:
            if pattern in text_lower:
                # Find the word after the pattern
                words = all_text.split()
                for i, word in enumerate(words):
                    if pattern in word.lower() and i + 1 < len(words):
                        name = words[i + 1].replace(',', '').replace('.', '').replace('!', '')
                        if len(name) > 2:  # Avoid very short names
                            key_info.append(f"Имя: {name}")
                            break
        
        # Extract age
        age_patterns = ["мне", "лет", "года"]
        for pattern in age_patterns:
            if pattern in text_lower:
                words = all_text.split()
                for i, word in enumerate(words):
                    if pattern in word.lower() and i + 1 < len(words):
                        try:
                            age = int(words[i + 1])
                            if 1 <= age <= 120:  # Reasonable age range
                                key_info.append(f"Возраст: {age} лет")
                                break
                        except ValueError:
                            continue
        
        # Extract profession
        profession_keywords = ["работаю", "профессия", "дизайнер", "программист", "врач", "учитель", "инженер"]
        for keyword in profession_keywords:
            if keyword in text_lower:
                key_info.append(f"Профессия: {keyword}")
                break
        
        # Extract city
        city_keywords = ["москве", "киеве", "спб", "санкт-петербурге", "львове", "харькове", "одессе"]
        for keyword in city_keywords:
            if keyword in text_lower:
                key_info.append(f"Город: {keyword}")
                break
        
        # Extract hobbies
        hobby_keywords = ["люблю", "нравится", "увлекаюсь", "хобби", "рисовать", "читать", "путешествовать", "готовить"]
        hobbies = []
        
        # Look for hobby patterns
        for keyword in hobby_keywords:
            if keyword in text_lower:
                # Find words after hobby keywords
                words = all_text.split()
                for i, word in enumerate(words):
                    if keyword in word.lower():
                        # Look for next few words as potential hobbies
                        for j in range(1, 4):  # Check next 3 words
                            if i + j < len(words):
                                next_word = words[i + j].replace(',', '').replace('.', '').replace('!', '').replace('и', '')
                                if len(next_word) > 2 and next_word.lower() not in ['я', 'меня', 'мне', 'мое', 'моя', 'моего', 'моей']:
                                    hobbies.append(next_word)
        
        # Also look for specific hobby words
        specific_hobbies = ["рисовать", "читать", "путешествовать", "готовить", "спорт", "музыка", "фотография"]
        for hobby in specific_hobbies:
            if hobby in text_lower:
                hobbies.append(hobby)
        
        # Remove duplicates and limit
        unique_hobbies = list(set(hobbies))[:3]
        if unique_hobbies:
            key_info.append(f"Увлечения: {', '.join(unique_hobbies)}")
        
        return "; ".join(key_info) if key_info else ""
    
    def search_memory(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Simple text search in buffer (not semantic)"""
        results = []
        query_lower = query.lower()
        
        for msg in reversed(self.messages):
            if query_lower in msg.content.lower():
                results.append({
                    "content": msg.content,
                    "role": msg.role,
                    "timestamp": msg.timestamp,
                    "relevance": 1.0
                })
                if len(results) >= limit:
                    break
        
        return results
    
    def summarize_conversation(self, messages: List[Message]) -> str:
        """Simple summarization"""
        if not messages:
            return "Нет сообщений для обобщения."
        
        user_messages = [m for m in messages if m.role == "user"]
        assistant_messages = [m for m in messages if m.role == "assistant"]
        
        summary = f"Разговор из {len(messages)} сообщений. "
        summary += f"Пользователь написал {len(user_messages)} сообщений, "
        summary += f"ассистент ответил {len(assistant_messages)} раз."
        
        if user_messages:
            # Extract key topics (simple keyword approach)
            all_text = " ".join([m.content for m in user_messages])
            words = all_text.lower().split()
            # This is very simplified - in real implementation use proper NLP
            common_words = [w for w in words if len(w) > 4]
            if common_words:
                summary += f" Основные темы: {', '.join(common_words[:3])}."
        
        return summary
    
    def clear_memory(self) -> None:
        """Clear buffer memory"""
        self.messages.clear()
        self.last_activity = datetime.utcnow()
    
    def _format_time_gap(self, gap: timedelta) -> str:
        """Format time gap in Russian"""
        if gap.days > 0:
            return f"{gap.days} дн."
        elif gap.seconds > 3600:
            hours = gap.seconds // 3600
            return f"{hours} ч."
        else:
            minutes = gap.seconds // 60
            return f"{minutes} мин." 