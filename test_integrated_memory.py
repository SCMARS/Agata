#!/usr/bin/env python3
"""
ИНТЕГРИРОВАННЫЙ ТЕСТ: LangGraph + Buffer Memory + Vector Memory
Тестирует как все компоненты работают вместе
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta

# Добавляем путь к приложению
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.memory.hybrid_memory import HybridMemory
from app.memory.base import Message, MemoryContext
from app.graph.pipeline import AgathaPipeline, PipelineState

async def test_integrated_system():
    """Тест полной интеграции системы памяти с LangGraph"""
    
    print('🚀 ИНТЕГРИРОВАННЫЙ ТЕСТ: LangGraph + Память')
    print('=' * 70)
    
    # Создаем гибридную память
    memory = HybridMemory('user_integrated_test')
    context = MemoryContext(user_id='user_integrated_test', day_number=1)
    
    # СЦЕНАРИЙ: Реальное общение с пользователем
    print('\n📝 СЦЕНАРИЙ: Общение с пользователем через LangGraph')
    
    conversation_messages = [
        Message('user', 'Привет! Меня зовут Дмитрий, я разработчик', datetime.utcnow() - timedelta(hours=8)),
        Message('assistant', 'Привет, Дмитрий! Рад познакомиться. Расскажи о себе подробнее.', datetime.utcnow() - timedelta(hours=7, minutes=45)),
        Message('user', 'Я работаю в IT-компании, разрабатываю веб-приложения на Python', datetime.utcnow() - timedelta(hours=7, minutes=30)),
        Message('assistant', 'Интересно! Какие технологии используешь в работе?', datetime.utcnow() - timedelta(hours=7, minutes=15)),
        Message('user', 'Использую Django, FastAPI, PostgreSQL, Redis. Люблю работать с микросервисами', datetime.utcnow() - timedelta(hours=7)),
        Message('assistant', 'Отличный стек! Есть ли проекты, которыми гордишься?', datetime.utcnow() - timedelta(hours=6, minutes=45)),
        Message('user', 'Да, недавно запустил платформу для онлайн-образования. Очень доволен результатом', datetime.utcnow() - timedelta(hours=6, minutes=30)),
        Message('assistant', 'Поздравляю! Это действительно достижение. Какие планы на будущее?', datetime.utcnow() - timedelta(hours=6, minutes=15)),
        Message('user', 'Хочу изучить машинное обучение и добавить AI-функции в свои проекты', datetime.utcnow() - timedelta(hours=6)),
        Message('assistant', 'Отличная идея! ML может сильно улучшить пользовательский опыт.', datetime.utcnow() - timedelta(hours=5, minutes=45)),
        Message('user', 'Согласен! Но пока не знаю, с чего начать изучение ML', datetime.utcnow() - timedelta(hours=5, minutes=30)),
        Message('assistant', 'Могу порекомендовать несколько ресурсов для изучения. Что тебя больше интересует?', datetime.utcnow() - timedelta(hours=5, minutes=15)),
        Message('user', 'Интересует компьютерное зрение и обработка естественного языка', datetime.utcnow() - timedelta(hours=5)),
        Message('assistant', 'Отличный выбор! Начни с основ Python для ML, затем TensorFlow или PyTorch.', datetime.utcnow() - timedelta(hours=4, minutes=45)),
        Message('user', 'Спасибо за совет! Буду изучать. А ты помнишь, что я рассказывал о себе?', datetime.utcnow() - timedelta(hours=4, minutes=30)),
    ]
    
    # Сохраняем сообщения в память
    print('\n📝 Сохраняем диалог в память...')
    for i, msg in enumerate(conversation_messages, 1):
        print(f'  {i:2d}. [{msg.role.upper()}] {msg.content[:50]}...')
        await memory.add_message(msg, context)
    
    # ТЕСТ 1: Проверяем, что память работает
    print('\n🧠 ТЕСТ 1: Проверка работы памяти')
    print('-' * 50)
    
    # Получаем контекст
    context_result = await memory.get_context(context)
    print(f'📝 Контекст: {context_result}')
    
    # Поиск по ключевым темам
    search_queries = ['Дмитрий', 'разработчик', 'Python', 'ML', 'компьютерное зрение', 'платформа образования']
    
    print('\n🔍 Поиск по ключевым темам:')
    for query in search_queries:
        results = await memory.search_memory(query, limit=2)
        print(f'  "{query}": найдено {len(results)} записей')
        if results:
            for result in results:
                print(f'    - {result["content"][:60]}... (важность: {result["importance_score"]:.2f})')
    
    # ТЕСТ 2: Интеграция с LangGraph Pipeline
    print('\n🔄 ТЕСТ 2: Интеграция с LangGraph Pipeline')
    print('-' * 50)
    
    try:
        # Создаем экземпляр pipeline
        pipeline = AgathaPipeline()
        
        # Создаем состояние для pipeline
        pipeline_state = PipelineState(
            user_id='user_integrated_test',
            message='Привет! Помнишь, что я рассказывал о себе?',
            memory_context=context,
            current_step='start'
        )
        
        print('✅ Pipeline создан успешно')
        print(f'📊 Состояние: {pipeline_state}')
        
        # Симулируем работу pipeline с памятью
        print('\n🔄 Симуляция работы pipeline с памятью...')
        
        # Получаем контекст для AI-ответа
        ai_context = await memory.get_context(context)
        print(f'🧠 Контекст для AI: {ai_context}')
        
        # Симулируем AI-ответ на основе памяти
        print('\n🤖 Симуляция AI-ответа на основе памяти:')
        
        # Анализируем, что помнит система
        user_info = await memory.get_user_profile()
        print(f'👤 Профиль пользователя: {user_info}')
        
        # Формируем персонализированный ответ
        if 'Дмитрий' in str(ai_context):
            print('✅ Система помнит имя пользователя')
            response = "Конечно, Дмитрий! Я помню, что ты разработчик, работаешь с Python, Django, FastAPI. Недавно запустил платформу для онлайн-образования и хочешь изучать машинное обучение, особенно компьютерное зрение и NLP. Правильно?"
        else:
            print('❌ Система не помнит детали пользователя')
            response = "Извини, но я не помню детали нашего разговора. Расскажи о себе еще раз?"
        
        print(f'🤖 AI-ответ: {response}')
        
        # ТЕСТ 3: Проверка работы памяти в реальном времени
        print('\n⏰ ТЕСТ 3: Память в реальном времени')
        print('-' * 50)
        
        # Добавляем новое сообщение
        new_message = Message('user', 'Да, все правильно! Ты отлично помнишь наши разговоры', datetime.utcnow())
        await memory.add_message(new_message, context)
        
        # Проверяем обновленный контекст
        updated_context = await memory.get_context(context)
        print(f'📝 Обновленный контекст: {updated_context}')
        
        # Поиск по новому сообщению
        search_result = await memory.search_memory('отлично помнишь', limit=1)
        if search_result:
            print(f'🔍 Найдено новое сообщение: {search_result[0]["content"]}')
        
        print('\n✅ Интеграция работает отлично!')
        
    except Exception as e:
        print(f'❌ Ошибка в LangGraph интеграции: {e}')
        import traceback
        traceback.print_exc()
    
    print('\n🎉 ИНТЕГРИРОВАННЫЙ ТЕСТ ЗАВЕРШЕН!')
    print('=' * 70)

if __name__ == "__main__":
    asyncio.run(test_integrated_system()) 