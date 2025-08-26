import os
from typing import Optional

class Settings:
    """Application settings configuration"""
    
    # Flask
    FLASK_ENV: str = os.getenv('FLASK_ENV', 'development')
    DEBUG: bool = os.getenv('DEBUG', 'False').lower() == 'true'
    HOST: str = os.getenv('HOST', '0.0.0.0')
    PORT: int = int(os.getenv('PORT', '5000'))
    
    # Database
    DATABASE_URL: str = os.getenv('DATABASE_URL', 'postgresql://agatha:agatha@postgres:5432/agatha')
    
    # Redis
    REDIS_URL: str = os.getenv('REDIS_URL', 'redis://redis:6379/0')
    
    # Celery
    CELERY_BROKER_URL: str = os.getenv('CELERY_BROKER_URL', 'redis://redis:6379/1')
    CELERY_RESULT_BACKEND: str = os.getenv('CELERY_RESULT_BACKEND', 'redis://redis:6379/2')
    
    # LLM Configuration
    OPENAI_API_KEY: Optional[str] = os.getenv('OPENAI_API_KEY')
    LLM_MODEL: str = os.getenv('LLM_MODEL', 'gpt-4')
    MAX_MESSAGE_LENGTH: int = int(os.getenv('MAX_MESSAGE_LENGTH', '500'))
    
    # LangSmith (optional)
    LANGSMITH_API_KEY: Optional[str] = os.getenv('LANGSMITH_API_KEY')
    LANGSMITH_PROJECT: str = os.getenv('LANGSMITH_PROJECT', 'agatha')
    
    # Agatha Configuration
    BASE_PROMPT_PATH: str = os.getenv('BASE_PROMPT_PATH', 'app/config/prompts')
    DAYS_SCENARIO_COUNT: int = int(os.getenv('DAYS_SCENARIO_COUNT', '30'))
    QUESTION_FREQUENCY: int = int(os.getenv('QUESTION_FREQUENCY', '3'))
    
    # Memory
    MEMORY_TYPE: str = os.getenv('MEMORY_TYPE', 'buffer')  # buffer, summary, vector
    VECTOR_STORE_TYPE: str = os.getenv('VECTOR_STORE_TYPE', 'faiss')  # faiss, chroma, pinecone

settings = Settings() 