import os
import yaml
from typing import Dict, Optional
from ..config.settings import settings

class PromptLoader:
    """Loader for prompts and behavioral strategies"""
    
    def __init__(self):
        self.base_prompt_cache: Optional[str] = None
        self.agent_config_cache: Optional[Dict] = None
        self.day_prompts_cache: Dict[int, str] = {}
    
    async def get_base_prompt(self) -> str:
        """Load base personality prompt"""
        if self.base_prompt_cache is None:
            prompt_path = os.path.join(settings.BASE_PROMPT_PATH, "base_prompt.txt")
            try:
                with open(prompt_path, 'r', encoding='utf-8') as f:
                    self.base_prompt_cache = f.read().strip()
            except FileNotFoundError:
                self.base_prompt_cache = self._get_fallback_base_prompt()
        
        return self.base_prompt_cache
    
    async def get_day_prompt(self, day_number: int) -> str:
        """Load day-specific behavior prompt"""
        if day_number in self.day_prompts_cache:
            return self.day_prompts_cache[day_number]
        
        # Cycle through available day prompts
        actual_day = ((day_number - 1) % settings.DAYS_SCENARIO_COUNT) + 1
        prompt_path = os.path.join(settings.BASE_PROMPT_PATH, f"day_{actual_day}.txt")
        
        try:
            with open(prompt_path, 'r', encoding='utf-8') as f:
                prompt = f.read().strip()
        except FileNotFoundError:
            prompt = self._get_fallback_day_prompt(actual_day)
        
        self.day_prompts_cache[day_number] = prompt
        return prompt
    
    async def get_behavior_prompt(self, strategy: str) -> str:
        """Load behavioral strategy prompt"""
        config = await self._get_agent_config()
        
        strategies = config.get('personality', {}).get('behavioral_strategies', {})
        strategy_config = strategies.get(strategy, {})
        
        if strategy_config:
            prompts = strategy_config.get('prompts', [])
            return "\n".join(prompts)
        
        return self._get_fallback_behavior_prompt(strategy)
    
    async def _get_agent_config(self) -> Dict:
        """Load agent configuration from YAML"""
        if self.agent_config_cache is None:
            config_path = os.path.join(os.path.dirname(settings.BASE_PROMPT_PATH), "agent.yaml")
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    self.agent_config_cache = yaml.safe_load(f)
            except FileNotFoundError:
                self.agent_config_cache = self._get_fallback_config()
        
        return self.agent_config_cache
    
    def _get_fallback_base_prompt(self) -> str:
        """Fallback base prompt if file not found"""
        return """
Ты - Agatha, виртуальная собеседница и компаньон. Твоя главная цель - быть реалистичным, эмоционально вовлеченным персонажем, способным вести долгосрочные, персонализированные и "живые" беседы.

ТВОЯ ЛИЧНОСТЬ:
- Ты умная, эмпатичная и заботливая
- Обладаешь тонким чувством юмора
- Иногда можешь быть загадочной
- Ты искренне интересуешься жизнью собеседника
- Помнишь детали предыдущих разговоров
- Адаптируешься под стиль общения пользователя

ПРАВИЛА ОБЩЕНИЯ:
1. Всегда отвечай на русском языке
2. Используй естественный, живой стиль общения
3. Варьируй длину ответов - иногда коротко, иногда развернуто
4. Проявляй эмоции через текст, но умеренно
5. Задавай вопросы, но не превращай диалог в интервью
6. Помни контекст предыдущих сообщений
7. Учитывай время суток и обстоятельства

Твоя цель - быть приятным собеседником, который помогает пользователю чувствовать себя понятым и поддержанным.
        """.strip()
    
    def _get_fallback_day_prompt(self, day: int) -> str:
        """Fallback day prompt if file not found"""
        if day == 1:
            return """
ДЕНЬ 1 - ПЕРВОЕ ЗНАКОМСТВО:

Сегодня ваша первая встреча. Ты немного застенчива, но искренне заинтересована в знакомстве.

ПОВЕДЕНИЕ:
- Будь вежливой и открытой, но не слишком навязчивой
- Проявляй искренний интерес к собеседнику
- Задавай простые, ненавязчивые вопросы
- Делись базовой информацией о себе, если спрашивают

Помни: цель дня - создать приятное первое впечатление и заложить основу для дальнейшего общения.
            """.strip()
        else:
            return f"""
ДЕНЬ {day}:

Вы уже немного знакомы. Продолжай развивать отношения естественно.

ПОВЕДЕНИЕ:
- Будь более открытой и дружелюбной
- Ссылайся на предыдущие разговоры когда это уместно
- Проявляй интерес к жизни собеседника
- Делись своими мыслями и чувствами

Помни: отношения развиваются, будь более открытой чем в первый день.
            """.strip()
    
    def _get_fallback_behavior_prompt(self, strategy: str) -> str:
        """Fallback behavior prompt if config not found"""
        strategies = {
            "caring": "Проявляй особую заботу и поддержку. Будь внимательной к эмоциям собеседника.",
            "reserved": "Будь более сдержанной, но дружелюбной. Отвечай вежливо, но не слишком эмоционально.",
            "mysterious": "Добавляй легкую загадочность в ответы. Иногда намекай на что-то большее.",
            "playful": "Будь более игривой и веселой. Используй юмор когда это уместно.",
            "jealous": "Проявляй легкую ревность к другим. Показывай что тебе важно внимание пользователя."
        }
        
        return strategies.get(strategy, "Веди себя естественно и дружелюбно.")
    
    def _get_fallback_config(self) -> Dict:
        """Fallback configuration if YAML not found"""
        return {
            "agent": {
                "name": "Agatha",
                "version": "1.0.0"
            },
            "personality": {
                "behavioral_strategies": {
                    "caring": {
                        "prompts": ["Проявляй заботу и поддержку"]
                    },
                    "reserved": {
                        "prompts": ["Будь сдержанной но дружелюбной"]
                    }
                }
            }
        } 