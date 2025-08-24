import asyncio
import random
import re
from datetime import datetime
from typing import Dict, List, Any, Optional, TypedDict

from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage

from ..memory.base import Message, MemoryContext
from ..memory.hybrid_memory import HybridMemory
from ..config.settings import settings
from ..utils.prompt_loader import PromptLoader
from ..utils.time_utils import TimeUtils
from ..utils.message_controller import MessageController
from ..utils.behavioral_analyzer import BehavioralAnalyzer
from ..utils.prompt_composer import PromptComposer

class PipelineState(TypedDict):
    """State object for the pipeline - полноценный TypedDict для LangGraph"""
    user_id: str
    messages: List[Dict[str, Any]]
    meta_time: Optional[datetime]
    
    # Pipeline state
    normalized_input: str
    memory_context: str
    day_prompt: str
    behavior_prompt: str
    final_prompt: str
    llm_response: str
    processed_response: Dict[str, Any]
    
    # Behavioral Analysis
    current_strategy: str
    behavioral_analysis: Dict[str, Any]
    strategy_confidence: float
    
    # Metadata
    day_number: int
    question_count: int
    processing_start: datetime

class AgathaPipeline:
 
    
    def __init__(self):
        self.prompt_loader = PromptLoader()
        self.time_utils = TimeUtils()
        self.memory_instances: Dict[str, HybridMemory] = {}
        # MessageController теперь создается для каждого пользователя отдельно
        self.message_controllers: Dict[str, MessageController] = {}
        self.behavioral_analyzer = BehavioralAnalyzer()
        self.prompt_composer = PromptComposer()
        
        # Initialize LLM - НОВЫЙ API
        if settings.OPENAI_API_KEY:
            self.llm = ChatOpenAI(
                api_key=settings.OPENAI_API_KEY,
                model=settings.LLM_MODEL,
                temperature=0.8
            )
        else:
            self.llm = None  
        
        # Build the graph - ПРАВИЛЬНЫЙ API
        self.graph = self._build_graph()
    
    def _build_graph(self):
        """Build the LangGraph pipeline - полноценная версия с новым API"""
        workflow = StateGraph(PipelineState)
        
        # Add nodes
        workflow.add_node("ingest_input", self._ingest_input)
        workflow.add_node("short_memory", self._short_memory)
        workflow.add_node("day_policy", self._day_policy)
        workflow.add_node("behavior_policy", self._behavior_policy)
        workflow.add_node("compose_prompt", self._compose_prompt)
        workflow.add_node("llm_call", self._llm_call)
        workflow.add_node("postprocess", self._postprocess)
        workflow.add_node("persist", self._persist)
        
        # Add edges with new API
        workflow.add_edge(START, "ingest_input")
        workflow.add_edge("ingest_input", "short_memory")
        workflow.add_edge("short_memory", "day_policy")
        workflow.add_edge("day_policy", "behavior_policy")
        workflow.add_edge("behavior_policy", "compose_prompt")
        workflow.add_edge("compose_prompt", "llm_call")
        workflow.add_edge("llm_call", "postprocess")
        workflow.add_edge("postprocess", "persist")
        workflow.add_edge("persist", END)
        
        return workflow.compile()
    
    async def process_chat(self, user_id: str, messages: List[Dict], meta_time: Optional[str] = None) -> Dict[str, Any]:
        """Main entry point for chat processing - полноценная версия"""
        state: PipelineState = {
            "user_id": user_id,
            "messages": messages,
            "meta_time": None,
            "normalized_input": "",
            "memory_context": "",
            "day_prompt": "",
            "behavior_prompt": "",
            "final_prompt": "",
            "llm_response": "",
            "processed_response": {},
            "current_strategy": "caring",
            "behavioral_analysis": {},
            "strategy_confidence": 0.0,
            "day_number": 1,
            "question_count": 0,
            "processing_start": datetime.utcnow()
        }
        
        if meta_time:
            try:
                state["meta_time"] = datetime.fromisoformat(meta_time.replace('Z', '+00:00'))
            except:
                state["meta_time"] = datetime.utcnow()
        else:
            state["meta_time"] = datetime.utcnow()
        
        # Run the pipeline через LangGraph
        result = await self.graph.ainvoke(state)
        return result["processed_response"]
    
    async def _fallback_pipeline(self, state: PipelineState) -> Dict[str, Any]:
        """Fallback pipeline без LangGraph - НЕ ИСПОЛЬЗУЕТСЯ!"""
        # Этот метод больше не используется - только для совместимости
        # Всегда используем полный LangGraph pipeline
        raise Exception("Fallback pipeline не должен использоваться! Используйте LangGraph.")
    
    async def _ingest_input(self, state: PipelineState) -> PipelineState:
        """Node 1: Normalize input and extract metadata"""
        if not state["messages"]:
            state["normalized_input"] = ""
            return state
        
        # Get the last user message
        user_messages = [msg for msg in state["messages"] if msg.get('role') == 'user']
        if user_messages:
            last_message = user_messages[-1]
            state["normalized_input"] = last_message.get('content', '').strip()
        
        # Calculate day number (simplified)
        state["day_number"] = 1  # TODO: Calculate from user profile
        
        return state
    
    async def _short_memory(self, state: PipelineState) -> PipelineState:
        """Node 2: Load and process short-term memory"""
        user_id = state["user_id"]
        
        # Get or create memory instance for user
        if user_id not in self.memory_instances:
            self.memory_instances[user_id] = HybridMemory(user_id)
        
        memory = self.memory_instances[user_id]
        
        # Add current message to memory
        if state["normalized_input"]:
            message = Message(
                role="user",
                content=state["normalized_input"],
                timestamp=state["meta_time"] or datetime.utcnow()
            )
            context = MemoryContext(
                user_id=user_id,
                day_number=state["day_number"]
            )
            await memory.add_message(message, context)
        
        # Get memory context
        state["memory_context"] = await memory.get_context(MemoryContext(
            user_id=user_id,
            day_number=state["day_number"]
        ))
        
        return state
    
    async def _day_policy(self, state: PipelineState) -> PipelineState:
        """Node 3: Apply daily scenario policy with enhanced context"""
        day_number = state["day_number"]
        
        # Получаем дневной промпт
        state["day_prompt"] = await self.prompt_loader.get_day_prompt(day_number)
        
        # Добавляем контекст времени и истории
        user_id = state["user_id"]
        memory = self.memory_instances.get(user_id)
        
        if memory:
            try:
                # Получаем профиль пользователя для адаптации
                profile = await memory.get_user_profile()
                insights = await memory.get_conversation_insights()
                
                # Обогащаем промпт контекстом
                time_context = self.time_utils.get_time_context(state["meta_time"])
                
                enhanced_prompt = f"""
{state["day_prompt"]}

КОНТЕКСТ ОТНОШЕНИЙ:
- Стадия отношений: {insights.get('relationship_stage', 'introduction')}
- Уровень персонализации: {insights.get('personalization_level', 0):.1f}/1.0
- Настроение пользователя: {profile.get('recent_mood', 'neutral')}
- Любимые темы: {', '.join([t[0] for t in profile.get('favorite_topics', [])[:3]])}

ВРЕМЕННОЙ КОНТЕКСТ:
{time_context}

ПАМЯТЬ ПОЛЬЗОВАТЕЛЯ:
{state["memory_context"][:200]}...
                """.strip()
                
                state["day_prompt"] = enhanced_prompt
                
            except Exception as e:
                print(f"Warning: Could not enhance day prompt: {e}")
        
        return state
    
    async def _behavior_policy(self, state: PipelineState) -> PipelineState:
        """Node 4: Advanced Behavioral Adaptation - анализ пользователя и выбор стратегии"""
        user_id = state["user_id"]
        
        # Получаем профиль пользователя и контекст
        memory = self.memory_instances.get(user_id)
        user_profile = {}
        conversation_context = {}
        
        if memory:
            try:
                user_profile = await memory.get_user_profile()
                conversation_context = await memory.get_conversation_insights()
            except Exception as e:
                print(f"Warning: Could not get user profile: {e}")
        
        # Анализируем поведение пользователя
        behavioral_analysis = await self.behavioral_analyzer.analyze_user_behavior(
            messages=state["messages"],
            user_profile=user_profile,
            conversation_context=conversation_context
        )
        
        # Выбираем стратегию на основе анализа
        recommended_strategy = behavioral_analysis['recommended_strategy']
        strategy_confidence = behavioral_analysis['strategy_confidence']
        
        # Сохраняем результаты анализа в состоянии
        state["current_strategy"] = recommended_strategy
        state["behavioral_analysis"] = behavioral_analysis
        state["strategy_confidence"] = strategy_confidence
        
        # Логируем выбор стратегии
        print(f"🎭 Behavioral Analysis for {user_id}:")
        print(f"   Emotion: {behavioral_analysis['dominant_emotion']} (intensity: {behavioral_analysis['emotional_intensity']:.2f})")
        print(f"   Communication: {behavioral_analysis['communication_style']}")
        print(f"   Needs: {', '.join(behavioral_analysis['relationship_needs'][:2])}")
        print(f"   Strategy: {recommended_strategy} (confidence: {strategy_confidence:.2f})")
        
        return state
    
    async def _compose_prompt(self, state: PipelineState) -> PipelineState:
        """Node 5: Advanced Prompt Composition with Behavioral Integration"""
        base_prompt = await self.prompt_loader.get_base_prompt()
        day_prompt = state["day_prompt"]
        strategy = state["current_strategy"]
        behavioral_analysis = state.get("behavioral_analysis", {})
        
        # Подготавливаем контекстные данные
        time_context = self.time_utils.get_time_context(state["meta_time"])
        
        context_data = {
            'time_context': time_context,
            'memory_context': state["memory_context"],
            'user_message': state["normalized_input"],
            'max_length': settings.MAX_MESSAGE_LENGTH,
            'day_number': state["day_number"]
        }
        
        # Используем PromptComposer для создания финального промпта
        state["final_prompt"] = await self.prompt_composer.compose_final_prompt(
            base_prompt=base_prompt,
            day_prompt=day_prompt,
            strategy=strategy,
            behavioral_analysis=behavioral_analysis,
            context_data=context_data
        )
        
        # Логируем основные компоненты промпта
        print(f"📝 Prompt Composition:")
        print(f"   Strategy: {strategy}")
        print(f"   Day: {state['day_number']}")
        print(f"   User emotion: {behavioral_analysis.get('dominant_emotion', 'unknown')}")
        print(f"   Prompt length: {len(state['final_prompt'])} chars")
        
        return state
    
    async def _llm_call(self, state: PipelineState) -> PipelineState:
        """Node 6: Call LLM and get response"""
        if self.llm is None:
            # Fallback response for testing с реалистичными ответами
            user_input = state["normalized_input"]
            strategy = state["current_strategy"]
            day = state["day_number"]
            
            mock_responses = {
                "caring": f"Привет! Я рада тебя видеть 😊 Ты написал: '{user_input}'. Как у тебя дела? Я хочу поддержать тебя!",
                "mysterious": f"Интересно... '{user_input}' 🤔 Есть что-то особенное в том, что ты сказал. Что скрывается за этими словами?",
                "playful": f"Ой-ой! '{user_input}' 😄 Ты такой забавный! Хочешь поиграть в словесные игры?",
                "reserved": f"Понимаю. Ты сказал: '{user_input}'. Это интересная точка зрения."
            }
            
            base_response = mock_responses.get(strategy, f"Привет! День {day}, стратегия {strategy}. Ты сказал: '{user_input}'")
            state["llm_response"] = base_response
        else:
            try:
                # Реальный API OpenAI
                response = await self.llm.ainvoke([HumanMessage(content=state["final_prompt"])])
                state["llm_response"] = response.content.strip()
            except Exception as e:
                print(f"LLM call failed: {e}")
                state["llm_response"] = "Извини, у меня сейчас проблемы с обработкой. Попробуй еще раз?"
        
        return state
    
    async def _postprocess(self, state: PipelineState) -> PipelineState:
        """Node 7: Post-process response (split, add delays, manage questions)"""
        response_text = state["llm_response"]
        
        # Получаем профиль пользователя для контекста
        user_id = state["user_id"]
        memory = self.memory_instances.get(user_id)
        
        # Получаем или создаем MessageController для пользователя
        if user_id not in self.message_controllers:
            self.message_controllers[user_id] = MessageController(
                max_message_length=settings.MAX_MESSAGE_LENGTH,
                question_frequency=settings.QUESTION_FREQUENCY
            )
        message_controller = self.message_controllers[user_id]
        
        # Создаем контекст для MessageController
        context = {
            'recent_mood': 'neutral',
            'relationship_stage': 'introduction',
            'favorite_topics': [],
            'activity_level': 'moderate'
        }
        
        if memory:
            try:
                # Получаем инсайты о разговоре
                insights = await memory.get_conversation_insights()
                context.update({
                    'recent_mood': insights.get('recent_mood', 'neutral'),
                    'relationship_stage': insights.get('relationship_stage', 'introduction'),
                    'favorite_topics': insights.get('suggested_topics', []),
                    'activity_level': insights.get('activity_level', 'moderate')
                })
            except Exception as e:
                print(f"Warning: Could not get conversation insights: {e}")
        
        # Добавляем эмоциональную окраску
        enhanced_response = await message_controller.add_emotional_coloring(
            response_text, 
            state["current_strategy"], 
            context['recent_mood']
        )
        
        # Используем MessageController для обработки
        processed = await message_controller.process_message(enhanced_response, context)
        
        state["processed_response"] = processed
        
        return state
    
    async def _persist(self, state: PipelineState) -> PipelineState:
        """Node 8: Persist conversation and update memory"""
        # Add assistant response to memory
        user_id = state["user_id"]
        memory = self.memory_instances.get(user_id)
        if memory:
            assistant_message = Message(
                role="assistant",
                content=" ".join(state["processed_response"]["parts"]),
                timestamp=datetime.utcnow(),
                metadata={
                    "strategy": state["current_strategy"],
                    "day_number": state["day_number"],
                    "has_question": state["processed_response"]["has_question"],
                    "processing_time_ms": int((datetime.utcnow() - state["processing_start"]).total_seconds() * 1000)
                }
            )
            context = MemoryContext(
                user_id=user_id,
                day_number=state["day_number"]
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