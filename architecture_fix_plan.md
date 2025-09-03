# 🔧 ПЛАН ИСПРАВЛЕНИЯ АРХИТЕКТУРЫ ПАМЯТИ

## 🚨 ТЕКУЩИЕ ПРОБЛЕМЫ

### 1. Множественные конфликтующие системы
- `HybridMemory` (EnhancedBufferMemory + VectorMemory)
- `MemoryLevelsManager` (ShortMemory + IntelligentVectorMemory)
- `MemoryAdapter` пытается объединить все
- **РЕЗУЛЬТАТ:** Системы не знают друг о друге, дублируют функциональность

### 2. Неправильная логика переключения
- Краткосрочная память НЕ вытесняется после N сообщений
- Система НЕ переключается на векторную память
- **РЕЗУЛЬТАТ:** После 10 сообщений система теряет доступ к старым данным

### 3. MemoryAdapter не понимает состояние системы
- Не знает, сколько сообщений в краткосрочной памяти
- Не понимает, когда использовать долгосрочную память
- **РЕЗУЛЬТАТ:** Всегда возвращает данные из краткосрочной памяти

## ✅ РЕШЕНИЕ: УПРОЩЕННАЯ АРХИТЕКТУРА

### НОВАЯ АРХИТЕКТУРА:
```
UnifiedMemoryManager
├── ShortTermWindow (последние 10 сообщений)
├── VectorDatabase (все сообщения > 10)
└── SmartRetriever (выбирает источник данных)
```

### ЛОГИКА РАБОТЫ:
1. **Сообщения 1-10:** Используется ShortTermWindow
2. **Сообщения 11+:** 
   - Сообщения 1-10 переносятся в VectorDatabase
   - ShortTermWindow содержит только последние 10
   - SmartRetriever ищет в VectorDatabase для старых данных

### ПРЕИМУЩЕСТВА:
- ✅ Одна система памяти вместо 4-х
- ✅ Четкая логика переключения
- ✅ Автоматическое управление данными
- ✅ Простота отладки и поддержки

## 🛠️ ПЛАН РЕАЛИЗАЦИИ

### Шаг 1: Создать UnifiedMemoryManager
- Объединить логику всех систем памяти
- Реализовать четкое переключение short → vector
- Добавить автоматическое управление окном памяти

### Шаг 2: Упростить MemoryAdapter
- Убрать множественные источники данных
- Добавить логику "умного выбора" источника
- Реализовать кэширование для производительности

### Шаг 3: Тестирование
- Тест переключения после 10 сообщений
- Тест сохранения данных в векторной БД
- Тест корректного извлечения старых данных

## 📋 КОНКРЕТНЫЕ ИЗМЕНЕНИЯ

### 1. app/memory/unified_memory.py (НОВЫЙ)
```python
class UnifiedMemoryManager:
    def __init__(self, user_id: str, window_size: int = 10):
        self.user_id = user_id
        self.window_size = window_size
        self.short_term_messages = []  # Последние N сообщений
        self.vector_db = IntelligentVectorMemory(user_id)
        self.message_count = 0
    
    def add_message(self, message):
        self.message_count += 1
        
        # Добавляем в окно
        self.short_term_messages.append(message)
        
        # Если окно переполнено - переносим в векторную БД
        if len(self.short_term_messages) > self.window_size:
            oldest_message = self.short_term_messages.pop(0)
            self.vector_db.add_document(oldest_message)
    
    def get_context_for_prompt(self, query: str):
        # ЛОГИКА ВЫБОРА ИСТОЧНИКА:
        if self.message_count <= self.window_size:
            # Используем только краткосрочную память
            return self._format_short_term_context()
        else:
            # Комбинируем: краткосрочная + поиск в векторной БД
            short_context = self._format_short_term_context()
            vector_context = self.vector_db.search(query, max_results=5)
            return self._combine_contexts(short_context, vector_context)
```

### 2. app/memory/memory_adapter.py (УПРОЩЕНИЕ)
```python
class MemoryAdapter:
    def __init__(self, user_id: str):
        self.unified_memory = UnifiedMemoryManager(user_id)
    
    def get_for_prompt(self, user_id: str, query: str):
        # ПРОСТАЯ ЛОГИКА - один источник данных
        context = self.unified_memory.get_context_for_prompt(query)
        
        return {
            "short_memory_summary": context.get("recent", "—"),
            "long_memory_facts": context.get("facts", "—"),
            "semantic_context": context.get("search_results", "—")
        }
```

### 3. Удаление дублирующих систем
- Удалить HybridMemory (заменить на UnifiedMemoryManager)
- Упростить MemoryLevelsManager или объединить с UnifiedMemoryManager
- Оставить только один путь данных: UnifiedMemoryManager → MemoryAdapter → Prompt

## 🎯 ОЖИДАЕМЫЕ РЕЗУЛЬТАТЫ

После исправления:
- ✅ Система будет помнить информацию после 10+ сообщений
- ✅ Четкое переключение с краткосрочной на долгосрочную память
- ✅ ИИ будет использовать конкретные факты из векторной БД
- ✅ Простота отладки и поддержки системы

## 🚀 НАЧИНАЕМ С КРИТИЧЕСКОГО ИСПРАВЛЕНИЯ

Первым делом исправим MemoryAdapter, чтобы он правильно выбирал источник данных на основе количества сообщений.
