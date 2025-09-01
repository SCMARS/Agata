
import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

# LangChain imports
try:
    from langchain.memory import ConversationBufferWindowMemory, ConversationSummaryMemory
    from langchain_community.vectorstores import Chroma
    from langchain_openai import OpenAIEmbeddings, ChatOpenAI
    from langchain_core.documents import Document
    from langchain.schema import BaseMessage, HumanMessage, AIMessage
    LANGCHAIN_AVAILABLE = True
except ImportError as e:
    LANGCHAIN_AVAILABLE = False
    print(f"⚠️ LangChain импорт ошибка: {e}")

# Проект imports
try:
    from ..config.production_config_manager import get_config
    CONFIG_AVAILABLE = True
except ImportError:
    CONFIG_AVAILABLE = False
    print("⚠️ Config manager не доступен")


class WorkingMemorySystem:
    """
    Рабочая система памяти на LangChain
    - Short-term: ConversationBufferWindowMemory (последние N сообщений)
    - Long-term: Chroma векторная БД
    - Эмоции и темы: из YAML конфигурации
    """
    
    def __init__(self, user_id: str, config_file: str = "enhanced_memory_config"):
        self.user_id = user_id
        self.logger = logging.getLogger(f"{__name__}.{user_id}")
        
        # Загружаем конфигурацию из YAML
        self.config = self._load_config(config_file)
        
        # Инициализируем компоненты
        self.short_memory = None  # ConversationBufferWindowMemory
        self.long_memory = None   # Chroma VectorStore
        self.embeddings = None    # OpenAIEmbeddings
        self.llm = None          # ChatOpenAI для summarization
        
        if LANGCHAIN_AVAILABLE:
            self._initialize_memory_components()
        else:
            self.logger.error("LangChain не доступен!")
        
        self.logger.info(f"WorkingMemorySystem инициализирована для {user_id}")
    
    def _load_config(self, config_file: str) -> Dict[str, Any]:
        """Загружает конфигурацию из YAML без хардкода"""
        if CONFIG_AVAILABLE:
            try:
                return get_config(config_file, self.user_id, {})
            except Exception as e:
                self.logger.warning(f"Ошибка загрузки конфига: {e}")
        
        # Fallback конфигурация
        return {
            "short_memory": {
                "window_size": 10,  # последние 10 сообщений
                "memory_key": "chat_history"
            },
            "long_memory": {
                "persist_directory": "./data/vectordb",
                "collection_name": f"user_{self.user_id}"
            },
            "embeddings": {
                "model": "text-embedding-ada-002",
                "chunk_size": 1000
            },
            "llm": {
                "model": "gpt-4o-mini",
                "temperature": 0.3
            },
            "emotion_markers": {
                "happy": ["спасибо", "отлично", "😊"],
                "sad": ["грустно", "😢"],
                "confused": ["не понимаю", "🤔"]
            },
            "topic_keywords": {
                "работа": ["работ", "профессия"],
                "технологии": ["программ", "код", "компьютер"]
            },
            "importance_calculation": {
                "role_weights": {"user": 0.7, "assistant": 0.5},
                "length_weights": {"long_threshold": 200, "long_bonus": 0.1},
                "long_threshold": 0.6  # порог для добавления в long memory
            }
        }
    
    def _initialize_memory_components(self):
        """Инициализирует LangChain компоненты"""
        try:
            # 1. Short-term память (ConversationBufferWindowMemory)
            window_size = self.config.get("short_memory", {}).get("window_size", 10)
            memory_key = self.config.get("short_memory", {}).get("memory_key", "chat_history")
            
            self.short_memory = ConversationBufferWindowMemory(
                k=window_size,
                memory_key=memory_key,
                return_messages=True
            )
            self.logger.info(f"Short memory инициализирована (окно: {window_size})")
            
            # 2. Embeddings
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                embedding_model = self.config.get("embeddings", {}).get("model", "text-embedding-ada-002")
                self.embeddings = OpenAIEmbeddings(
                    model=embedding_model,
                    openai_api_key=api_key
                )
                self.logger.info(f"Embeddings инициализированы ({embedding_model})")
                
                # 3. Long-term память (Chroma)
                persist_dir = self.config.get("long_memory", {}).get("persist_directory", "./data/vectordb")
                collection_name = self.config.get("long_memory", {}).get("collection_name", f"user_{self.user_id}")
                
                # Создаем директорию если не существует
                Path(persist_dir).mkdir(parents=True, exist_ok=True)
                
                self.long_memory = Chroma(
                    persist_directory=persist_dir,
                    embedding_function=self.embeddings,
                    collection_name=collection_name
                )
                self.logger.info(f"Long memory инициализирована ({persist_dir}/{collection_name})")
                
                # 4. LLM для суммаризации
                llm_model = self.config.get("llm", {}).get("model", "gpt-4o-mini")
                temperature = self.config.get("llm", {}).get("temperature", 0.3)
                
                self.llm = ChatOpenAI(
                    model=llm_model,
                    temperature=temperature,
                    openai_api_key=api_key
                )
                self.logger.info(f"LLM инициализирован ({llm_model})")
            else:
                self.logger.warning("OPENAI_API_KEY не найден - векторная память отключена")
        
        except Exception as e:
            self.logger.error(f"Ошибка инициализации LangChain: {e}")
    
    def add_message(self, role: str, content: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Добавляет сообщение в систему памяти
        
        Args:
            role: 'user' или 'assistant'
            content: текст сообщения
            metadata: дополнительные данные
            
        Returns:
            Dict с результатами обработки
        """
        try:
            results = {
                "short_memory": False,
                "long_memory": False,
                "emotion": None,
                "topics": [],
                "importance": 0.0
            }
            
            # 1. Определяем эмоцию из конфига (БЕЗ ХАРДКОДА)
            emotion = self._detect_emotion(content)
            results["emotion"] = emotion
            
            # 2. Определяем темы из конфига (БЕЗ ХАРДКОДА)
            topics = self._detect_topics(content)
            results["topics"] = topics
            
            # 3. Рассчитываем важность из конфига (БЕЗ ХАРДКОДА)
            importance = self._calculate_importance(content, role)
            results["importance"] = importance
            
            # 4. Добавляем в short-term память
            if self.short_memory:
                if role == "user":
                    self.short_memory.chat_memory.add_user_message(content)
                else:
                    self.short_memory.chat_memory.add_ai_message(content)
                results["short_memory"] = True
                self.logger.debug(f"Сообщение добавлено в short memory")
            
            # 5. Добавляем в long-term память (если важное)
            # Используем fallback 0.65, если не задано в конфиге
            importance_config = self.config.get("importance_calculation", {})
            importance_threshold = importance_config.get("long_threshold", 0.75)
            
            self.logger.debug(f"Importance: {importance:.2f}, threshold: {importance_threshold}, will_save: {importance >= importance_threshold}")
            
            if self.long_memory and importance >= importance_threshold:
                document = Document(
                    page_content=content,
                    metadata={
                        "user_id": self.user_id,
                        "role": role,
                        "timestamp": datetime.now().isoformat(),
                        "emotion": emotion,
                        "topics": topics,
                        "importance": importance,
                        **(metadata or {})
                    }
                )
                
                doc_ids = self.long_memory.add_documents([document])
                results["long_memory"] = True
                self.logger.debug(f"Сообщение добавлено в long memory: {doc_ids}")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Ошибка добавления сообщения: {e}")
            return {"error": str(e)}
    
    def _detect_emotion(self, text: str) -> Optional[str]:
        """Определяет эмоцию из YAML конфигурации (БЕЗ ХАРДКОДА)"""
        try:
            emotion_markers = self.config.get("emotion_markers", {})
            text_lower = text.lower()
            
            for emotion, markers in emotion_markers.items():
                if any(marker in text_lower for marker in markers):
                    return emotion
            
            return None
        except Exception as e:
            self.logger.warning(f"Ошибка определения эмоции: {e}")
            return None
    
    def _detect_topics(self, text: str) -> List[str]:
        """Определяет темы из YAML конфигурации (БЕЗ ХАРДКОДА)"""
        try:
            topic_keywords = self.config.get("topic_keywords", {})
            text_lower = text.lower()
            topics = []
            
            for topic, keywords in topic_keywords.items():
                if any(keyword in text_lower for keyword in keywords):
                    topics.append(topic)
            
            return topics
        except Exception as e:
            self.logger.warning(f"Ошибка определения тем: {e}")
            return []
    
    def _calculate_importance(self, text: str, role: str) -> float:
        """Рассчитывает важность из YAML конфигурации (БЕЗ ХАРДКОДА)"""
        try:
            importance_config = self.config.get("importance_calculation", {})
            
            # Базовая важность по роли
            role_weights = importance_config.get("role_weights", {})
            base_importance = role_weights.get(role, 0.5)
            
            # Бонус за длину
            length_config = importance_config.get("length_weights", {})
            long_threshold = length_config.get("long_threshold", 200)
            long_bonus = length_config.get("long_bonus", 0.1)
            
            if len(text) > long_threshold:
                base_importance += long_bonus
            
            return min(1.0, max(0.0, base_importance))
            
        except Exception as e:
            self.logger.warning(f"Ошибка расчета важности: {e}")
            return 0.5
    
    def get_context(self, query: str = None, max_results: int = 5) -> Dict[str, Any]:
        """
        Получает контекст для LLM
        
        Args:
            query: поисковый запрос для long-term памяти
            max_results: максимум результатов из векторной БД
            
        Returns:
            Dict с контекстом из short и long памяти
        """
        try:
            context = {
                "short_memory": [],
                "long_memory": [],
                "total_messages": 0
            }
            
            # 1. Short-term память (последние сообщения)
            if self.short_memory:
                messages = self.short_memory.chat_memory.messages
                context["short_memory"] = [
                    {
                        "role": "user" if isinstance(msg, HumanMessage) else "assistant",
                        "content": msg.content
                    }
                    for msg in messages
                ]
                context["total_messages"] = len(messages)
            
            # 2. Long-term память (поиск по запросу)
            if self.long_memory and query:
                search_results = self.long_memory.similarity_search(
                    query=query,
                    k=max_results
                )
                
                context["long_memory"] = [
                    {
                        "content": doc.page_content,
                        "metadata": doc.metadata
                    }
                    for doc in search_results
                ]
            
            return context
            
        except Exception as e:
            self.logger.error(f"Ошибка получения контекста: {e}")
            return {"error": str(e)}
    
    def clear_memory(self):
        """Очищает всю память"""
        try:
            if self.short_memory:
                self.short_memory.clear()
                self.logger.info("Short memory очищена")
            
            if self.long_memory:
                # Удаляем коллекцию и создаем новую
                collection_name = self.config.get("long_memory", {}).get("collection_name", f"user_{self.user_id}")
                try:
                    self.long_memory._client.delete_collection(collection_name)
                    self.logger.info("Long memory очищена")
                except:
                    pass  # Коллекция может не существовать
            
        except Exception as e:
            self.logger.error(f"Ошибка очистки памяти: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Получает статистику памяти"""
        try:
            stats = {
                "user_id": self.user_id,
                "short_memory_available": self.short_memory is not None,
                "long_memory_available": self.long_memory is not None,
                "embeddings_available": self.embeddings is not None,
                "config_loaded": bool(self.config)
            }
            
            if self.short_memory:
                stats["short_memory_messages"] = len(self.short_memory.chat_memory.messages)
            
            if self.long_memory:
                try:
                    collection = self.long_memory._collection
                    stats["long_memory_documents"] = collection.count()
                except:
                    stats["long_memory_documents"] = "unknown"
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Ошибка получения статистики: {e}")
            return {"error": str(e)}


# Функция для создания рабочей памяти
def create_working_memory(user_id: str, config_file: str = "enhanced_memory_config") -> WorkingMemorySystem:
    """Создает экземпляр рабочей системы памяти."""
    return WorkingMemorySystem(user_id, config_file)
