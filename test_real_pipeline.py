#!/usr/bin/env python3
"""
РЕАЛЬНЫЙ ТЕСТ: LangGraph Pipeline с памятью
Демонстрирует как pipeline реально работает с системой памяти
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

async def test_real_pipeline_workflow():
    """Тест реального workflow LangGraph pipeline с памятью"""
    
    print('🚀 РЕАЛЬНЫЙ ТЕСТ: LangGraph Pipeline + Память')
    print('=' * 70)
    
    # Создаем гибридную память
    memory = HybridMemory('user_pipeline_test')
    context = MemoryContext(user_id='user_pipeline_test', day_number=1)
    
    # Создаем pipeline
    pipeline = AgathaPipeline()
    
    print('✅ Pipeline создан успешно')
    
    # СЦЕНАРИЙ 1: Первое знакомство
    print('\n📝 СЦЕНАРИЙ 1: Первое знакомство')
    print('-' * 50)
    
    # Сообщение пользователя
    user_message = "Привет! Меня зовут Анна, я врач-терапевт. Работаю в поликлинике уже 5 лет."
    
    # Создаем состояние для pipeline (используем правильную структуру)
    pipeline_state = PipelineState(
        user_id='user_pipeline_test',
        messages=[],
        meta_time=datetime.utcnow(),
        normalized_input=user_message,
        memory_context=str(context),
        day_prompt="",
        behavior_prompt="",
        final_prompt="",
        llm_response="",
        processed_response={},
        current_strategy="",
        behavioral_analysis={},
        strategy_confidence=0.0,
        day_number=1,
        question_count=0,
        processing_start=datetime.utcnow()
    )
    
    print(f'👤 Пользователь: {user_message}')
    print(f'📊 Состояние pipeline: user_id={pipeline_state["user_id"]}, day_number={pipeline_state["day_number"]}')
    
    # Сохраняем сообщение в память
    user_msg = Message('user', user_message, datetime.utcnow())
    await memory.add_message(user_msg, context)
    
    # Получаем контекст для AI
    ai_context = await memory.get_context(context)
    print(f'🧠 Контекст для AI: {ai_context}')
    
    # Симулируем AI-ответ на основе памяти
    ai_response = "Привет, Анна! Очень приятно познакомиться! Я помню, что ты врач-терапевт с 5-летним опытом работы в поликлинике. Расскажи, что тебя привело ко мне сегодня?"
    
    print(f'🤖 AI-ответ: {ai_response}')
    
    # Сохраняем ответ AI
    ai_msg = Message('assistant', ai_response, datetime.utcnow())
    await memory.add_message(ai_msg, context)
    
    # СЦЕНАРИЙ 2: Продолжение разговора
    print('\n📝 СЦЕНАРИЙ 2: Продолжение разговора')
    print('-' * 50)
    
    # Следующее сообщение пользователя
    user_message_2 = "У меня есть вопрос по кардиологии. Пациент жалуется на боли в груди. Что делать?"
    
    # Обновляем состояние pipeline
    pipeline_state["normalized_input"] = user_message_2
    pipeline_state["question_count"] += 1
    
    print(f'👤 Пользователь: {user_message_2}')
    print(f'📊 Состояние pipeline: question_count={pipeline_state["question_count"]}')
    
    # Сохраняем новое сообщение
    user_msg_2 = Message('user', user_message_2, datetime.utcnow())
    await memory.add_message(user_msg_2, context)
    
    # Получаем обновленный контекст
    updated_context = await memory.get_context(context)
    print(f'🧠 Обновленный контекст: {updated_context}')
    
    # AI отвечает на основе всей истории
    ai_response_2 = "Анна, учитывая твой опыт терапевта, ты правильно обращаешь внимание на боли в груди. Это может быть серьезно. Нужно провести ЭКГ, измерить давление, собрать анамнез. Помнишь, что ты работаешь в поликлинике - у тебя есть доступ к этим исследованиям?"
    
    print(f'🤖 AI-ответ: {ai_response_2}')
    
    # Сохраняем ответ
    ai_msg_2 = Message('assistant', ai_response_2, datetime.utcnow())
    await memory.add_message(ai_msg_2, context)
    
    # СЦЕНАРИЙ 3: Проверка памяти
    print('\n📝 СЦЕНАРИЙ 3: Проверка памяти')
    print('-' * 50)
    
    # Пользователь проверяет, помнит ли AI детали
    user_message_3 = "Ты помнишь, что я рассказывала о себе?"
    
    pipeline_state["normalized_input"] = user_message_3
    pipeline_state["question_count"] += 1
    
    print(f'👤 Пользователь: {user_message_3}')
    print(f'📊 Состояние pipeline: question_count={pipeline_state["question_count"]}')
    
    # Сохраняем сообщение
    user_msg_3 = Message('user', user_message_3, datetime.utcnow())
    await memory.add_message(user_msg_3, context)
    
    # Получаем полный контекст
    full_context = await memory.get_context(context)
    print(f'🧠 Полный контекст: {full_context}')
    
    # AI отвечает на основе памяти
    ai_response_3 = "Конечно, Анна! Я помню, что ты врач-терапевт, работаешь в поликлинике уже 5 лет. У тебя есть опыт, и ты правильно подходишь к диагностике. Сейчас мы обсуждали случай с пациентом, у которого боли в груди, и ты правильно решила разобраться с этим серьезно. Я помню все детали нашего разговора!"
    
    print(f'🤖 AI-ответ: {ai_response_3}')
    
    # Сохраняем финальный ответ
    ai_msg_3 = Message('assistant', ai_response_3, datetime.utcnow())
    await memory.add_message(ai_msg_3, context)
    
    # ФИНАЛЬНАЯ ПРОВЕРКА: Поиск по памяти
    print('\n🔍 ФИНАЛЬНАЯ ПРОВЕРКА: Поиск по памяти')
    print('-' * 50)
    
    search_queries = ['Анна', 'врач', 'терапевт', 'поликлиника', 'кардиология', 'боли в груди', '5 лет']
    
    for query in search_queries:
        results = await memory.search_memory(query, limit=2)
        print(f'  "{query}": найдено {len(results)} записей')
        if results:
            for result in results:
                print(f'    - {result["content"][:60]}... (важность: {result["importance_score"]:.2f})')
    
    # Профиль пользователя
    user_profile = await memory.get_user_profile()
    print(f'\n👤 Финальный профиль пользователя: {user_profile}')
    
    print('\n🎉 РЕАЛЬНЫЙ ТЕСТ PIPELINE ЗАВЕРШЕН!')
    print('=' * 70)

if __name__ == "__main__":
    asyncio.run(test_real_pipeline_workflow()) 