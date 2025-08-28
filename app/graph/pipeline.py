import os
from datetime import datetime
from typing import Dict, List, Any, Optional, TypedDict
from langgraph.graph import StateGraph
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

from ..memory.hybrid_memory import HybridMemory
from ..config.settings import settings
from ..utils.prompt_loader import PromptLoader
from ..utils.time_utils import TimeUtils
from ..utils.message_controller import MessageController
from ..utils.behavioral_analyzer import BehavioralAnalyzer
from ..utils.prompt_composer import PromptComposer

QUIET_MODE = os.getenv('AGATHA_QUIET', 'false').lower() == 'true'

def log_info(message: str):
    if not QUIET_MODE:
        print(message)

class PipelineState(TypedDict):
    user_id: str
    messages: List[Dict[str, Any]]
    meta_time: Optional[datetime]
    normalized_input: str
    memory_context: str
    day_prompt: str
    behavior_prompt: str
    final_prompt: str
    llm_response: str
    processed_response: Dict[str, Any]
    current_strategy: str
    behavioral_analysis: Dict[str, Any]
    strategy_confidence: float
    day_number: int
    question_count: int
    processing_start: datetime

class AgathaPipeline:
    def __init__(self):
        self.prompt_loader = PromptLoader()
        self.time_utils = TimeUtils()
        self.message_controllers = {}
        self.behavioral_analyzer = BehavioralAnalyzer()
        self.prompt_composer = PromptComposer()
        self.memories = {}

        api_key = os.getenv('OPENAI_API_KEY') or settings.OPENAI_API_KEY
        if not api_key:
            raise ValueError("OPENAI_API_KEY required")

        log_info(f"Using OpenAI API key: {api_key[:20]}...")
        self.llm = ChatOpenAI(
            api_key=api_key,
            model=settings.LLM_MODEL,
            temperature=0.8
        )

        self.graph = self._build_graph()

    def _get_memory(self, user_id: str):
        if user_id not in self.memories:
            from ..memory.hybrid_memory import HybridMemory
            self.memories[user_id] = HybridMemory(user_id)
        return self.memories[user_id]

    def _build_graph(self):
        workflow = StateGraph(PipelineState)
        workflow.add_node("ingest_input", self._ingest_input)
        workflow.add_node("short_memory", self._short_memory)
        workflow.add_node("day_policy", self._day_policy)
        workflow.add_node("behavior_policy", self._behavior_policy)
        workflow.add_node("compose_prompt", self._compose_prompt)
        workflow.add_node("llm_call", self._llm_call)
        workflow.add_node("postprocess", self._postprocess)
        workflow.add_node("persist", self._persist)
        
        # Add edges - правильный API для 0.2.50
        workflow.add_edge("ingest_input", "short_memory")
        workflow.add_edge("short_memory", "day_policy")
        workflow.add_edge("day_policy", "behavior_policy")
        workflow.add_edge("behavior_policy", "compose_prompt")
        workflow.add_edge("compose_prompt", "llm_call")
        workflow.add_edge("llm_call", "postprocess")
        workflow.add_edge("postprocess", "persist")

        workflow.set_entry_point("ingest_input")
        workflow.set_finish_point("persist")

        return workflow.compile()

    def _ensure_stage_data(self, state: PipelineState) -> None:
        """Убедиться, что stage данные сохранены в state"""
        if "stage_number" not in state:
            message_count = len(state.get("messages", []))
            stage_number = min(3, max(1, (message_count // 10) + 1))
            state["stage_number"] = stage_number
            state["stage_prompt"] = self.prompt_loader.get_stage_prompt(stage_number)
            log_info(f"Ensured stage {stage_number} data in state")

    async def process_chat(self, user_id: str, messages: List[Dict], meta_time: Optional[str] = None) -> Dict[str, Any]:
        log_info(f"Pipeline START for user {user_id}")

        state: PipelineState = {
            "user_id": user_id,
            "messages": messages,
            "meta_time": None,
            "normalized_input": "",
            "memory_context": "",
            "day_prompt": "",
            "stage_prompt": "",
            "behavior_prompt": "",
            "final_prompt": "",
            "llm_response": "",
            "processed_response": {},
            "current_strategy": "caring",
            "behavioral_analysis": {},
            "strategy_confidence": 0.0,
            "day_number": 1,
            "stage_number": 1,
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
        
        log_info(f"📝 Initial state: {state}")

        try:
            # Используем АСИНХРОННЫЙ ainvoke()
            result = await self.graph.ainvoke(state)
            log_info(f"✅ LangGraph Pipeline COMPLETED: {result}")
            return result["processed_response"]
        except Exception as e:
            log_info(f"❌ LangGraph Pipeline FAILED: {e}")
            raise e
    
    async def _ingest_input(self, state: PipelineState) -> PipelineState:
        """Node 1: Process input and normalize - АСИНХРОННЫЙ"""
        log_info("🚀 NODE: _ingest_input ✅ STARTED")
        if not state["messages"]:
            state["normalized_input"] = ""
            return state
        
        # Get last user message
        user_messages = [msg for msg in state["messages"] if msg.get('role') == 'user']
        if user_messages:
            last_message = user_messages[-1]
            state["normalized_input"] = last_message.get('content', '').strip()
        
        # Set day number and stage
        state["day_number"] = 1  # TODO: Calculate from user profile

        # Determine stage based on message count
        message_count = len(state.get("messages", []))
        stage_number = min(3, max(1, (message_count // 10) + 1))
        state["stage_number"] = stage_number
        stage_prompt = self.prompt_loader.get_stage_prompt(stage_number)
        state["stage_prompt"] = stage_prompt
        log_info(f"Set stage {stage_number} prompt: {len(stage_prompt)} chars")

        return state
    
    async def _short_memory(self, state: PipelineState) -> PipelineState:
        log_info("🧠 NODE: _short_memory ✅ STARTED")
        user_id = state["user_id"]

        # Убедимся, что этап сохранен
        if "stage_number" not in state:
            message_count = len(state.get("messages", []))
            stage_number = min(3, max(1, (message_count // 10) + 1))
            state["stage_number"] = stage_number
            state["stage_prompt"] = self.prompt_loader.get_stage_prompt(stage_number)

        memory = self._get_memory(user_id)

        if state["normalized_input"]:
            from ..memory.base import Message, MemoryContext
            message = Message(
                role="user",
                content=state["normalized_input"],
                timestamp=state["meta_time"] or datetime.utcnow()
            )
            context = MemoryContext(
                user_id=user_id,
                day_number=state["day_number"]
            )
            memory.add_message(message, context)

        state["memory_context"] = memory.get_context(MemoryContext(
            user_id=user_id,
            day_number=state["day_number"]
        ))

        return state
    
    async def _day_policy(self, state: PipelineState) -> PipelineState:
        """Node 3: Apply daily scenario policy - АСИНХРОННЫЙ"""
        day_number = state["day_number"]
        
        # Убедимся, что этап сохранен
        if "stage_number" not in state:
            message_count = len(state.get("messages", []))
            stage_number = min(3, max(1, (message_count // 10) + 1))
            state["stage_number"] = stage_number
            state["stage_prompt"] = self.prompt_loader.get_stage_prompt(stage_number)

        # Добавляем контекст времени и истории
        user_id = state["user_id"]
        memory = self._get_memory(user_id)

        try:
            # Получаем профиль пользователя для адаптации
            profile = memory.get_user_profile()
            insights = memory.get_conversation_insights()

            # Обогащаем промпт контекстом
            meta_time = state["meta_time"] or datetime.utcnow()
            if isinstance(meta_time, str):
                try:
                    meta_time = datetime.fromisoformat(meta_time.replace('Z', '+00:00'))
                except:
                    meta_time = datetime.utcnow()
            time_context = self.time_utils.get_time_context(meta_time)

            enhanced_prompt = f"""
{state["stage_prompt"]}

КОНТЕКСТ ОТНОШЕНИЙ:
- Стадия отношений: {insights.get('relationship_stage', 'introduction')}
- Уровень персонализации: {insights.get('personalization_level', 0):.1f}/1.0
- Настроение пользователя: {profile.get('recent_mood', 'neutral')}
- Любимые темы: {', '.join([t[0] for t in profile.get('favorite_topics', [])[:3]])}

ВРЕМЕННОЙ КОНТЕКСТ:
{time_context}

ПАМЯТЬ ПОЛЬЗОВАТЕЛЯ:
                {state["memory_context"]}
                """.strip()

            state["day_prompt"] = enhanced_prompt

        except Exception as e:
            log_info(f"Warning: Could not enhance day prompt: {e}")
        
        return state
    
    async def _behavior_policy(self, state: PipelineState) -> PipelineState:
        """Node 4: Behavioral Adaptation - АСИНХРОННЫЙ"""
        log_info("🎭 NODE: _behavior_policy ✅ STARTED")
        user_id = state["user_id"]
        
        # Получаем профиль пользователя и контекст
        memory = self._get_memory(user_id)
        user_profile = {}
        conversation_context = {}

        try:
            user_profile = memory.get_user_profile()
            conversation_context = memory.get_conversation_insights()
        except Exception as e:
            log_info(f"Warning: Could not get user profile: {e}")

        # Анализируем поведение пользователя
        log_info(f"🎭 Starting Behavioral Analysis for {user_id}...")
        try:
            behavioral_analysis = self.behavioral_analyzer.analyze_user_behavior(
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
            log_info(f"🎭 Behavioral Analysis for {user_id}: ✅ SUCCESS")
            log_info(f"   Emotion: {behavioral_analysis['dominant_emotion']} (intensity: {behavioral_analysis['emotional_intensity']:.2f})")
            log_info(f"   Communication: {behavioral_analysis['communication_style']}")
            log_info(f"   Needs: {', '.join(behavioral_analysis['relationship_needs'][:2])}")
            log_info(f"   Strategy: {recommended_strategy} (confidence: {strategy_confidence:.2f})")

        except Exception as e:
            log_info(f"🎭 Behavioral Analysis for {user_id}: ❌ ERROR - {e}")
            # Fallback к дефолтным значениям
            state["current_strategy"] = "caring"
            state["behavioral_analysis"] = {}
            state["strategy_confidence"] = 0.0
        
        return state
    
    async def _compose_prompt(self, state: PipelineState) -> PipelineState:
        """Node 5: Prompt Composition - АСИНХРОННЫЙ"""
        # Убедимся, что stage данные сохранены
        self._ensure_stage_data(state)

        # Получаем последний вопрос пользователя
        user_question = ""
        if state["messages"]:
            user_messages = [msg for msg in state["messages"] if msg.get('role') == 'user']
            if user_messages:
                user_question = user_messages[-1].get('content', '')

        # Создаем динамический промпт на основе вопроса
        if user_question:
            base_prompt = self.prompt_loader.create_dynamic_prompt(user_question)
        else:
            base_prompt = self.prompt_loader.get_base_prompt()

        stage_prompt = state["stage_prompt"]
        strategy = state["current_strategy"]
        behavioral_analysis = state.get("behavioral_analysis", {})
        
        # Подготавливаем контекстные данные
        meta_time = state["meta_time"] or datetime.utcnow()
        if isinstance(meta_time, str):
            try:
                meta_time = datetime.fromisoformat(meta_time.replace('Z', '+00:00'))
            except:
                meta_time = datetime.utcnow()
        time_context = self.time_utils.get_time_context(meta_time)

        context_data = {
            'time_context': time_context,
            'memory_context': state["memory_context"],
            'user_message': state["normalized_input"],
            'max_length': settings.MAX_MESSAGE_LENGTH,
            'day_number': state["day_number"]
        }
        
        # Используем PromptComposer для создания финального промпта
        log_info(f"Compose prompt - stage_prompt available: {'stage_prompt' in state}")
        if 'stage_prompt' in state:
            log_info(f"Stage prompt length: {len(state['stage_prompt'])}")

        state["final_prompt"] = self.prompt_composer.compose_final_prompt(
            base_prompt=base_prompt,
            stage_prompt=state.get("stage_prompt", "Stage prompt not found"),
            strategy=strategy,
            behavioral_analysis=behavioral_analysis,
            context_data=context_data
        )
        
        # Логируем основные компоненты промпта
        log_info(f"📝 Prompt Composition:")
        log_info(f"   Strategy: {strategy}")
        log_info(f"   Stage: {state['stage_number']}")
        log_info(f"   User emotion: {behavioral_analysis.get('dominant_emotion', 'unknown')}")
        log_info(f"   Prompt length: {len(state['final_prompt'])} chars")
        log_info(f"   Max length setting: {settings.MAX_MESSAGE_LENGTH}")
        log_info(f"   Final prompt preview: {state['final_prompt'][:300]}...")
        
        return state
    
    async def _llm_call(self, state: PipelineState) -> PipelineState:
        """Node 6: Call LLM and get response - АСИНХРОННЫЙ"""
        try:
            # Реальный API OpenAI
            log_info(f"🤖 Calling OpenAI API with prompt length: {len(state['final_prompt'])}")
            log_info(f"📝 Memory context in prompt: {state.get('memory_context', '')}")

            # Синхронный вызов LLM
            response = self.llm.invoke([HumanMessage(content=state["final_prompt"])])
            state["llm_response"] = response.content.strip()

            log_info(f"✅ OpenAI response length: {len(state['llm_response'])} chars")
            log_info(f"📝 Response preview: {state['llm_response'][:200]}...")

        except Exception as e:
            log_info(f"❌ LLM call failed: {e}")
            state["llm_response"] = "Извини, у меня сейчас проблемы с обработкой. Попробуй еще раз?"

        return state
    
    async def _postprocess(self, state: PipelineState) -> PipelineState:
        """Node 7: Post-process response - АСИНХРОННЫЙ"""
        response_text = state["llm_response"]
        
        # Получаем профиль пользователя для контекста
        user_id = state["user_id"]
        memory = self._get_memory(user_id)

        # Получаем или создаем MessageController для пользователя
        if user_id not in self.message_controllers:
            self.message_controllers[user_id] = MessageController()
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
                insights = memory.get_conversation_insights()
                context.update({
                    'recent_mood': insights.get('recent_mood', 'neutral'),
                    'relationship_stage': insights.get('relationship_stage', 'introduction'),
                    'favorite_topics': insights.get('suggested_topics', []),
                    'activity_level': insights.get('activity_level', 'moderate')
                })
            except Exception as e:
                print(f"Warning: Could not get conversation insights: {e}")
        
        # Добавляем эмоциональную окраску
        enhanced_response = message_controller.add_emotional_coloring(
            response_text,
            state["current_strategy"],
            context['recent_mood']
        )

        # Используем MessageController для обработки
        processed = message_controller.process_message(enhanced_response, context)
        
        state["processed_response"] = processed
        
        return state
    
    async def _persist(self, state: PipelineState) -> PipelineState:
        user_id = state["user_id"]
        memory = self._get_memory(user_id)

        from ..memory.base import Message, MemoryContext
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
        memory.add_message(assistant_message, context)
        
        log_info(f"✅ Persisted conversation for user {user_id}")
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