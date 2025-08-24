import asyncio
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
    
    async def add_message(self, message: Message, context: MemoryContext) -> None:
        """Add message to buffer"""
        self.messages.append(message)
        self.last_activity = datetime.utcnow()
        
        # Keep only recent messages
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]
    
    async def get_context(self, context: MemoryContext) -> str:
        """Get formatted context from recent messages"""
        if not self.messages:
            return "Это начало вашего разговора."
        
        # Format recent messages
        context_parts = []
        
        # Add time context
        time_gap = datetime.utcnow() - self.last_activity
        if time_gap > timedelta(hours=6):
            context_parts.append(f"Прошло {self._format_time_gap(time_gap)} с последнего сообщения.")
        
        # Add recent conversation
        context_parts.append("Недавний разговор:")
        for msg in self.messages[-5:]:  # Last 5 messages
            role = "Пользователь" if msg.role == "user" else "Ты"
            context_parts.append(f"{role}: {msg.content}")
        
        return "\n".join(context_parts)
    
    async def search_memory(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
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
    
    async def summarize_conversation(self, messages: List[Message]) -> str:
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
    
    async def clear_memory(self) -> None:
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