

from app.config.settings import settings

__version__ = "1.0.0"
__author__ = "Agatha AI Team"
__description__ = "AI Companion with LangGraph and Behavioral Adaptation"

from app.graph.pipeline import AgathaPipeline
from app.memory.hybrid_memory import HybridMemory
from app.utils.behavioral_analyzer import BehavioralAnalyzer
from app.utils.prompt_composer import PromptComposer
from app.utils.message_controller import MessageController

__all__ = [
    'AgathaPipeline',
    'HybridMemory', 
    'BehavioralAnalyzer',
    'PromptComposer',
    'MessageController',
    'settings'
] 