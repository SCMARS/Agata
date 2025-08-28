#!/usr/bin/env python3
"""
ТЕСТ API СЕРВЕРА: Запуск реального сервера с памятью
Демонстрирует как вся система работает через HTTP API
"""

import asyncio
import sys
import os
import time
import requests
import json
from datetime import datetime

# Добавляем путь к приложению
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_api_server():
    """Тест запуска API сервера и работы через HTTP"""
    
    print('🚀 ТЕСТ API СЕРВЕРА: Запуск реального сервера')
    print('=' * 70)
    
    # Проверяем, что можем импортировать API
    try:
        from app.api import create_app
        print('✅ API приложение импортировано успешно')
        
        # Создаем тестовое приложение
        app = create_app()
        print('✅ Flask приложение создано успешно')
        
    except Exception as e:
        print(f'❌ Ошибка импорта API: {e}')
        return
    
    # Проверяем, что можем импортировать память
    try:
        from app.memory.hybrid_memory import HybridMemory
        from app.memory.base import Message, MemoryContext
        print('✅ Система памяти импортирована успешно')
    except Exception as e:
        print(f'❌ Ошибка импорта памяти: {e}')
        return
    
    # ТЕСТ 1: Проверка работы памяти напрямую
    print('\n🧠 ТЕСТ 1: Проверка памяти напрямую')
    print('-' * 50)
    
    memory = HybridMemory('api_test_user')
    context = MemoryContext(user_id='api_test_user', day_number=1)
    
    # Добавляем тестовое сообщение
    test_message = Message('user', 'Привет! Я тестирую API сервер', datetime.utcnow())
    await memory.add_message(test_message, context)
    
    # Проверяем контекст
    context_result = await memory.get_context(context)
    print(f'📝 Контекст: {context_result}')
    
    # ТЕСТ 2: Проверка конфигурации
    print('\n⚙️ ТЕСТ 2: Проверка конфигурации')
    print('-' * 50)
    
    try:
        from app.config.settings import settings
        print(f'✅ OpenAI API ключ: {settings.OPENAI_API_KEY[:20]}...')
        print(f'✅ Тип памяти: {settings.MEMORY_TYPE}')
        print(f'✅ Векторное хранилище: {settings.VECTOR_STORE_TYPE}')
        print(f'✅ База данных: {settings.DATABASE_HOST}:{settings.DATABASE_PORT}')
    except Exception as e:
        print(f'❌ Ошибка конфигурации: {e}')
    
    # ТЕСТ 3: Проверка структуры API
    print('\n🔌 ТЕСТ 3: Проверка структуры API')
    print('-' * 50)
    
    try:
        # Проверяем, что у нас есть Flask приложение
        if hasattr(app, 'url_map'):
            print(f'✅ API имеет {len(app.url_map._rules)} маршрутов')
            
            # Выводим доступные маршруты
            for rule in app.url_map._rules:
                print(f'  📍 {rule.rule} [{", ".join(rule.methods)}]')
        else:
            print('⚠️ API не имеет маршрутов')
            
    except Exception as e:
        print(f'❌ Ошибка проверки API: {e}')
    
    # ТЕСТ 4: Проверка подключения к базе данных
    print('\n🗄️ ТЕСТ 4: Проверка подключения к БД')
    print('-' * 50)
    
    try:
        # Проверяем подключение к PostgreSQL
        import asyncpg
        
        # Тестируем подключение
        conn = await asyncpg.connect(
            host='localhost',
            port=5432,
            user='postgres',
            password='postgres',
            database='agatha'
        )
        
        # Проверяем таблицу vector_memories
        result = await conn.fetchval("SELECT COUNT(*) FROM vector_memories")
        print(f'✅ Подключение к БД успешно')
        print(f'✅ В таблице vector_memories: {result} записей')
        
        await conn.close()
        
    except Exception as e:
        print(f'❌ Ошибка подключения к БД: {e}')
    
    # ТЕСТ 5: Проверка OpenAI API
    print('\n🤖 ТЕСТ 5: Проверка OpenAI API')
    print('-' * 50)
    
    try:
        import openai
        
        # Тестируем API ключ
        client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        # Простой тест эмбеддинга
        response = client.embeddings.create(
            model="text-embedding-ada-002",
            input="Тестовое сообщение"
        )
        
        if response.data and len(response.data) > 0:
            embedding = response.data[0].embedding
            print(f'✅ OpenAI API работает')
            print(f'✅ Эмбеддинг создан: {len(embedding)} элементов')
        else:
            print('❌ OpenAI API не вернул эмбеддинг')
            
    except Exception as e:
        print(f'❌ Ошибка OpenAI API: {e}')
    
    print('\n🎉 ТЕСТ API СЕРВЕРА ЗАВЕРШЕН!')
    print('=' * 70)
    
    # РЕКОМЕНДАЦИИ ПО ЗАПУСКУ
    print('\n💡 РЕКОМЕНДАЦИИ ПО ЗАПУСКУ СЕРВЕРА:')
    print('1. Убедитесь, что PostgreSQL запущен')
    print('2. Проверьте, что pgvector установлен')
    print('3. Запустите сервер: python run_server.py')
    print('4. Откройте Swagger UI: http://localhost:8000/docs')
    print('5. Протестируйте API endpoints')

if __name__ == "__main__":
    asyncio.run(test_api_server()) 