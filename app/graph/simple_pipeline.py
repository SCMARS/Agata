import asyncio
import random
import re
from datetime import datetime
from typing import Dict, List, Any, Optional

from ..memory.base import Message, MemoryContext
from ..memory.buffer_memory import BufferMemory
from ..config.settings import settings
from ..utils.prompt_loader import PromptLoader
from ..utils.time_utils import TimeUtils

class SimplePipelineState:
    """Упрощенное состояние pipeline для локального тестирования"""
    def __init__(self):
        self.user_id: str = ""
        self.messages: List[Dict[str, Any]] = []
        self.meta_time: Optional[datetime] = None
        
        # Pipeline state
        self.normalized_input: str = ""
        self.memory_context: str = ""
        self.day_prompt: str = ""
        self.behavior_prompt: str = ""
        self.final_prompt: str = ""
        self.llm_response: str = ""
        self.processed_response: Dict[str, Any] = {}
        
        # Metadata
        self.day_number: int = 1
        self.current_strategy: str = "caring"
        self.question_count: int = 0
        self.processing_start: datetime = datetime.utcnow()

class SimpleAgathaPipeline:
    """Упрощенная версия pipeline для локального тестирования без LangGraph"""
    
    def __init__(self):
        self.prompt_loader = PromptLoader()
        self.time_utils = TimeUtils()
        self.memory_instances: Dict[str, BufferMemory] = {}
        
        # Mock LLM для тестирования
        self.llm = None
    
    async def process_chat(self, user_id: str, messages: List[Dict], meta_time: Optional[str] = None) -> Dict[str, Any]:
        """Main entry point for chat processing - УПРОЩЕННАЯ ВЕРСИЯ"""
        state = SimplePipelineState()
        state.user_id = user_id
        state.messages = messages
        
        if meta_time:
            try:
                state.meta_time = datetime.fromisoformat(meta_time.replace('Z', '+00:00'))
            except:
                state.meta_time = datetime.utcnow()
        else:
            state.meta_time = datetime.utcnow()
        
        # Выполняем pipeline последовательно
        state = await self._ingest_input(state)
        state = await self._short_memory(state)
        state = await self._day_policy(state)
        state = await self._behavior_policy(state)
        state = await self._compose_prompt(state)
        state = await self._llm_call(state)
        state = await self._postprocess(state)
        state = await self._persist(state)
        
        return state.processed_response
    
    async def _ingest_input(self, state: SimplePipelineState) -> SimplePipelineState:
        """Node 1: Normalize input and extract metadata"""
        if not state.messages:
            state.normalized_input = ""
            return state
        
        # Get the last user message
        user_messages = [msg for msg in state.messages if msg.get('role') == 'user']
        if user_messages:
            last_message = user_messages[-1]
            state.normalized_input = last_message.get('content', '').strip()
        
        state.day_number = 1  # Simplified
        return state
    
    async def _short_memory(self, state: SimplePipelineState) -> SimplePipelineState:
        """Node 2: Load and process short-term memory"""
        user_id = state.user_id
        
        # Get or create memory instance for user
        if user_id not in self.memory_instances:
            self.memory_instances[user_id] = BufferMemory(user_id)
        
        memory = self.memory_instances[user_id]
        
        # Add current message to memory
        if state.normalized_input:
            message = Message(
                role="user",
                content=state.normalized_input,
                timestamp=state.meta_time or datetime.utcnow()
            )
            context = MemoryContext(
                user_id=user_id,
                day_number=state.day_number
            )
            await memory.add_message(message, context)
        
        # Get memory context
        state.memory_context = await memory.get_context(MemoryContext(
            user_id=user_id,
            day_number=state.day_number
        ))
        
        return state
    
    async def _day_policy(self, state: SimplePipelineState) -> SimplePipelineState:
        """Node 3: Apply daily scenario policy"""
        state.day_prompt = await self.prompt_loader.get_day_prompt(state.day_number)
        return state
    
    async def _behavior_policy(self, state: SimplePipelineState) -> SimplePipelineState:
        """Node 4: Apply behavioral strategy"""
        strategies = ["caring", "reserved", "mysterious", "playful"]
        state.current_strategy = random.choice(strategies)
        
        state.behavior_prompt = await self.prompt_loader.get_behavior_prompt(state.current_strategy)
        return state
    
    async def _compose_prompt(self, state: SimplePipelineState) -> SimplePipelineState:
        """Node 5: Compose final prompt"""
        base_prompt = await self.prompt_loader.get_base_prompt()
        
        # Time context
        time_context = self.time_utils.get_time_context(state.meta_time or datetime.utcnow())
        
        # Compose final prompt
        prompt_parts = [
            base_prompt,
            f"\n--- ДЕНЬ {state.day_number} ---",
            state.day_prompt,
            f"\n--- ПОВЕДЕНЧЕСКАЯ СТРАТЕГИЯ: {state.current_strategy.upper()} ---",
            state.behavior_prompt,
            f"\n--- ВРЕМЯ ---",
            time_context,
            f"\n--- КОНТЕКСТ ПАМЯТИ ---",
            state.memory_context,
            f"\n--- ТЕКУЩЕЕ СООБЩЕНИЕ ПОЛЬЗОВАТЕЛЯ ---",
            state.normalized_input,
            f"\n--- ИНСТРУКЦИИ ПО ОТВЕТУ ---",
            f"Максимальная длина ответа: {settings.MAX_MESSAGE_LENGTH} символов.",
            "Разбей ответ на 1-3 логические части если он длинный.",
            "Отвечай естественно и как Agatha."
        ]
        
        state.final_prompt = "\n".join(prompt_parts)
        return state
    
    async def _llm_call(self, state: SimplePipelineState) -> SimplePipelineState:
        """Node 6: Mock LLM call для тестирования"""
        # Mock response для локального тестирования
        user_input = state.normalized_input
        strategy = state.current_strategy
        day = state.day_number
        
        mock_responses = {
            "caring": f"Привет! Я рада тебя видеть 😊 Ты написал: '{user_input}'. Как у тебя дела? Я хочу поддержать тебя!",
            "mysterious": f"Интересно... '{user_input}' 🤔 Есть что-то особенное в том, что ты сказал. Что скрывается за этими словами?",
            "playful": f"Ой-ой! '{user_input}' 😄 Ты такой забавный! Хочешь поиграть в словесные игры?",
            "reserved": f"Понимаю. Ты сказал: '{user_input}'. Это интересная точка зрения."
        }
        
        base_response = mock_responses.get(strategy, f"Привет! День {day}, стратегия {strategy}. Ты сказал: '{user_input}'")
        
        state.llm_response = base_response
        return state
    
    async def _postprocess(self, state: SimplePipelineState) -> SimplePipelineState:
        """Node 7: Post-process response"""
        response_text = state.llm_response
        
        # Check if response contains a question
        has_question = bool(re.search(r'\?', response_text))
        
        # Split response into parts (simplified)
        parts = self._split_response(response_text)
        
        # Calculate delays between parts
        delays_ms = self._calculate_delays(parts)
        
        state.processed_response = {
            "parts": parts,
            "has_question": has_question,
            "delays_ms": delays_ms
        }
        
        return state
    
    async def _persist(self, state: SimplePipelineState) -> SimplePipelineState:
        """Node 8: Persist conversation"""
        # Add assistant response to memory
        user_id = state.user_id
        memory = self.memory_instances.get(user_id)
        if memory:
            assistant_message = Message(
                role="assistant",
                content=" ".join(state.processed_response["parts"]),
                timestamp=datetime.utcnow(),
                metadata={
                    "strategy": state.current_strategy,
                    "day_number": state.day_number,
                    "has_question": state.processed_response["has_question"]
                }
            )
            context = MemoryContext(
                user_id=user_id,
                day_number=state.day_number
            )
            await memory.add_message(assistant_message, context)
        
        print(f"✅ Persisted conversation for user {user_id}")
        return state
    
    def _split_response(self, text: str) -> List[str]:
        """Split response into 1-3 logical parts"""
        if len(text) <= settings.MAX_MESSAGE_LENGTH:
            return [text]
        
        # Try to split by sentences
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if len(sentences) <= 3:
            return sentences
        
        # Group sentences into 2-3 parts
        if len(sentences) <= 6:
            mid = len(sentences) // 2
            return [
                ". ".join(sentences[:mid]) + ".",
                ". ".join(sentences[mid:]) + "."
            ]
        else:
            third = len(sentences) // 3
            return [
                ". ".join(sentences[:third]) + ".",
                ". ".join(sentences[third:2*third]) + ".",
                ". ".join(sentences[2*third:]) + "."
            ]
    
    def _calculate_delays(self, parts: List[str]) -> List[int]:
        """Calculate typing delays between parts"""
        delays = [0]  # First part has no delay
        
        for i in range(1, len(parts)):
            # Simulate typing delay based on length
            chars = len(parts[i-1])
            typing_time = chars * 1000 // 50  # 50 chars per second
            delay = min(max(typing_time, 500), 3000)  # Between 0.5-3 seconds
            delays.append(delay)
        
        return delays 