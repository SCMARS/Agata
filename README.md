# 🤖 Agatha AI Companion

**Продвинутый AI-компаньон с поведенческой адаптацией и долгосрочной памятью**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2.50-green.svg)](https://github.com/langchain-ai/langgraph)
[![OpenAI GPT-4](https://img.shields.io/badge/OpenAI-GPT--4-orange.svg)](https://openai.com/)
[![Flask](https://img.shields.io/badge/Flask-3.0+-red.svg)](https://flask.palletsprojects.com/)

## 📋 Обзор

Agatha — это продвинутый AI-компаньон, построенный на базе **LangGraph** и **LangChain**, который обеспечивает персонализированные, контекстно-зависимые разговоры с развитой поведенческой адаптацией. Система включает интеллектуальное управление памятью, эмоциональный анализ и многоуровневую архитектуру памяти для построения долгосрочных отношений.

### 🎯 Ключевые особенности

- **🧠 4-уровневая система памяти**: Short-Term, Episodic, Long-Term, Summary с семантическим поиском
- **🎭 Поведенческая адаптация**: Динамическая настройка персональности на основе эмоций и паттернов разговора
- **📅 Дневные сценарии**: 30+ сценариев разговора, которые развивают динамику отношений со временем
- **⚡ LangGraph Pipeline**: 8-узловый конвейер обработки для сложного потока разговора
- **🔍 Умное управление сообщениями**: Автоматическое разделение сообщений, управление частотой вопросов
- **⏰ Контекст времени**: Контекстные ответы на основе времени дня и истории разговора
- **🚀 Готов к продакшену**: Flask + Gunicorn с проверками здоровья и OpenAPI документацией
- **🎛️ Без хардкода**: Полностью конфигурируемая система через YAML файлы и базу данных

## 🏗️ Архитектура

### Схема системы памяти

```mermaid
graph TD
    A[Пользователь] --> B[LangGraph Pipeline]
    B --> C[Нормализация ввода]
    C --> D[Короткая память]
    D --> E[Дневная политика]
    E --> F[Поведенческий анализ]
    F --> G[Композиция промпта]
    G --> H[LLM вызов]
    H --> I[Обработка ответа]
    I --> J[Сохранение в память]
    J --> K[Финальный ответ]
    
    subgraph "4-уровневая память"
        L[Short-Term<br/>Буфер 15 сообщений]
        M[Episodic<br/>Эпизоды диалогов]
        N[Long-Term<br/>Векторная БД]
        O[Summary<br/>Резюме]
    end
    
    D --> L
    J --> L
    J --> M
    J --> N
    J --> O
```

### Компоненты системы

- **EnhancedBufferMemory**: Умная короткая память с определением эмоций и важности
- **IntelligentVectorMemory**: Векторная память с ChromaDB для семантического поиска
- **MemoryLevelsManager**: Координатор всех уровней памяти
- **ProductionConfigManager**: Динамический менеджер конфигурации без хардкода
- **PromptComposer**: Композитор промптов с поддержкой курсора диалога

## 🚀 Быстрый старт

### Системные требования

- **Python**: 3.11 или выше
- **OpenAI API Key**: для GPT-4 и text-embedding-ada-002
- **PostgreSQL**: 13+ (опционально, для продакшена)
- **Redis**: 6+ (опционально, для Celery)

### 1. Клонирование и настройка

```bash
# Клонируем репозиторий
git clone https://github.com/your-username/agatha-ai.git
cd agatha-ai

# Создаем виртуальное окружение
python -m venv venv
source venv/bin/activate  # Linux/macOS
# или
venv\Scripts\activate     # Windows

# Устанавливаем зависимости
pip install -r requirements.txt
```

### 2. Настройка переменных окружения

Создайте файл `.env` в корне проекта:

```bash
# OpenAI Configuration
OPENAI_API_KEY=sk-your-openai-api-key-here

# Flask Configuration
FLASK_ENV=development
FLASK_DEBUG=true
FLASK_PORT=5000

# Database Configuration (опционально)
DATABASE_URL=postgresql://user:password@localhost:5432/agatha
REDIS_URL=redis://localhost:6379/0

# Memory Configuration
MEMORY_TYPE=intelligent  # или 'simple' для fallback
VECTOR_DB_PATH=./data/chroma_db

# Telegram Bot (опционально)
TELEGRAM_BOT_TOKEN=your-telegram-bot-token
```

### 3. Инициализация базы данных (опционально)

Для продакшена с PostgreSQL:

```bash
# Запуск PostgreSQL
./start_local_db.sh

# Или вручную через Docker
docker run --name agatha-postgres -e POSTGRES_PASSWORD=password -p 5432:5432 -d postgres:13

# Выполнение миграций
python -c "
from app.database.migrations import run_migrations
run_migrations()
"
```

### 4. Запуск проекта
python run_full_system.py
#### Режим разработки

```bash
# Простой запуск Flask сервера
python run_server.py

# Или с автоперезагрузкой
FLASK_DEBUG=true python run_server.py
```

#### Продакшн режим

```bash
# С Gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 run_server:app

# С Celery для фоновых задач
celery -A app.workers.celery_app worker --loglevel=info &
```

#### Telegram Bot

```bash
# Запуск Telegram бота
python run_telegram_bot.py
```

### 5. Проверка работы

```bash
# Проверка здоровья API
curl http://localhost:5000/healthz

# Тестовый запрос к API
curl -X POST http://localhost:5000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Привет, меня зовут Александр!",
    "user_id": "test_user"
  }'
```

Ожидаемый ответ:
```json
{
  "response": "Привет, Александр! Рада познакомиться! 😊",
  "conversation_state": "active",
  "emotions_detected": ["happy"],
  "memory_stats": {
    "buffer_size": 2,
    "cursor_position": 1
  }
}
```

## 📊 API Документация

### Endpoints

#### `POST /chat` - Основной чат

```json
{
  "message": "Текст сообщения",
  "user_id": "идентификатор_пользователя",
  "metadata": {
    "day_number": 1,
    "time_context": "morning"
  }
}
```

**Ответ:**
```json
{
  "response": "Ответ AI",
  "conversation_state": "active",
  "emotions_detected": ["happy", "grateful"],
  "topics_detected": ["работа", "хобби"],
  "memory_stats": {
    "buffer_size": 5,
    "cursor_position": 4,
    "importance_score": 0.8
  },
  "behavior_tag": "care"
}
```

#### `GET /memory/{user_id}` - Состояние памяти

```json
{
  "levels": {
    "short_term": {
      "status": "active",
      "buffer_size": 5,
      "cursor_position": 4
    },
    "long_term": {
      "status": "active", 
      "total_documents": 127,
      "avg_importance": 0.7
    },
    "episodic": {
      "total_episodes": 3,
      "recent_episodes": 1
    },
    "summary": {
      "total_summaries": 8
    }
  }
}
```

#### `GET /healthz` - Проверка здоровья

```json
{
  "status": "healthy",
  "components": {
    "memory_system": "ok",
    "llm_connection": "ok",
    "database": "ok"
  }
}
```

## 🧪 Тестирование

### Базовые тесты

```bash
# Тест системы памяти
python -c "
from app.memory import EnhancedBufferMemory, create_short_memory
from app.memory.base import Message, MemoryContext
from datetime import datetime

# Тест короткой памяти
memory = create_short_memory('test_user', max_messages=5)
memory.add_message('user', 'Привет! Меня зовут Тест 😊')
print(f'Эмоции: {memory.get_emotions_detected()}')
print(f'Курсор: {memory.get_current_cursor_position()}')
print('✅ Тест пройден!')
"

# Тест конфигурации
python -c "
from app.config.production_config_manager import get_config
config = get_config('enhanced_memory_config')
print(f'Эмоции в конфиге: {list(config.get(\"emotion_markers\", {}).keys())}')
print('✅ Конфигурация загружена!')
"
```

### Интеграционные тесты

```bash
# Полный тест пайплайна
python quick_test.py
```

## ⚙️ Конфигурация

### Структура конфигурации

```
app/config/
├── enhanced_memory_config.yml    # Конфигурация памяти и эмоций
├── prompt_composer_config.yml    # Настройки композитора промптов  
├── system_defaults.yml           # Системные настройки по умолчанию
└── prompts/                      # Промпты для разных дней
    ├── base_prompt.txt
    ├── day_1.txt
    ├── day_7.txt
    └── day_30.txt
```

### Основные настройки

#### `enhanced_memory_config.yml`
```yaml
# Маркеры эмоций (без хардкода!)
emotion_markers:
  happy: ["спасибо", "отлично", "😊", "круто"]
  sad: ["грустно", "печально", "😢"]
  
# Расчет важности сообщений
importance_calculation:
  role_weights:
    user: 0.7
    assistant: 0.5
  importance_markers:
    critical:
      markers: ["важно", "срочно", "критично"]
      weight: 0.3

# Ключевые слова для тем
topic_keywords:
  работа: ["работ", "профессия", "карьер"]
  семья: ["семья", "родители", "дети"]
```

#### `system_defaults.yml`
```yaml
system:
  limits:
    max_message_length: 4096
    buffer_size: 15
  thresholds:
    memory:
      importance_threshold: 0.6
      similarity_threshold: 0.7
```

## 🔌 Расширения

### Добавление новых эмоций

1. Отредактируйте `app/config/enhanced_memory_config.yml`:
```yaml
emotion_markers:
  excited: ["ура", "супер", "восторг", "🎉"]
```

2. Добавьте в `app/memory/enhanced_buffer_memory.py`:
```python
class EmotionTag(Enum):
    EXCITED = "excited"  # Новая эмоция
```

### Добавление новых тем

```yaml
topic_keywords:
  спорт: ["спорт", "тренировка", "фитнес", "бег"]
  музыка: ["музыка", "песня", "концерт", "группа"]
```

### Кастомные поведенческие стратегии

Создайте новый промпт в `app/config/prompts/`:
```txt
# custom_behavior.txt
Ты дружелюбный и энергичный AI-помощник...
```

## 🐳 Docker

```dockerfile
# Dockerfile уже готов в проекте
docker build -t agatha-ai .
docker run -p 5000:5000 -e OPENAI_API_KEY=your-key agatha-ai
```

## 📱 Telegram Bot

### Настройка

1. Создайте бота через [@BotFather](https://t.me/botfather)
2. Добавьте токен в `.env`:
```bash
TELEGRAM_BOT_TOKEN=123456789:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
```
3. Запустите бота:
```bash
python run_telegram_bot.py
```

### Команды бота

- `/start` - Начать разговор
- `/memory` - Показать состояние памяти
- `/reset` - Очистить память
- `/stats` - Статистика диалога

## 🛠️ Разработка

### Структура проекта

```
agatha-ai/
├── app/
│   ├── api/              # Flask API endpoints
│   ├── bots/             # Telegram bot
│   ├── config/           # Конфигурационные файлы
│   ├── database/         # Миграции БД
│   ├── graph/            # LangGraph pipeline
│   ├── memory/           # Система памяти
│   ├── utils/            # Утилиты
│   └── workers/          # Celery задачи
├── tests/                # Тесты
├── data/                 # Данные (ChromaDB, логи)
├── requirements.txt      # Зависимости
└── run_server.py         # Точка входа
```

### Добавление новых узлов в LangGraph

```python
# app/graph/pipeline.py
def new_processing_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Новый узел обработки"""
    # Ваша логика здесь
    return state

# Добавление в граф
workflow.add_node("new_node", new_processing_node)
workflow.add_edge("previous_node", "new_node")
```

## 🔍 Мониторинг и логирование

### Логи

```bash
# Просмотр логов
tail -f logs/agatha.log

# Логи по уровням
grep "ERROR" logs/agatha.log
grep "INFO" logs/agatha.log
```

### Метрики памяти

```python
from app.memory import create_memory_levels_manager

manager = create_memory_levels_manager('user_id')
overview = manager.get_memory_overview()
print(overview)
```

## ❗ Известные проблемы

1. **SQLAlchemy конфликт**: Используйте Python 3.11, избегайте 3.13
2. **OpenAI API лимиты**: Настройте rate limiting в продакшене
3. **ChromaDB пространство**: Периодически очищайте старые векторы

## 🤝 Участие в разработке

1. Форкните проект
2. Создайте feature branch (`git checkout -b feature/amazing-feature`)
3. Коммитьте изменения (`git commit -m 'Add amazing feature'`)
4. Пушьте в branch (`git push origin feature/amazing-feature`)
5. Создайте Pull Request

## 📄 Лицензия

Проект распространяется под лицензией MIT. См. файл `LICENSE` для подробностей.

## 🙏 Благодарности

- [LangChain](https://github.com/langchain-ai/langchain) за мощную LLM инфраструктуру
- [LangGraph](https://github.com/langchain-ai/langgraph) за граф-ориентированные рабочие процессы
- [ChromaDB](https://github.com/chroma-core/chroma) за векторную базу данных
- [OpenAI](https://openai.com/) за GPT-4 и embeddings

---

**💡 Совет**: Начните с простого сценария, добавьте несколько сообщений и изучите, как система запоминает контекст и адаптирует поведение. Agatha становится умнее с каждым разговором!