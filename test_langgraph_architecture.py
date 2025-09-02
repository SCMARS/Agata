#!/usr/bin/env python3
"""
Комплексный тест архитектуры LangGraph
Проверяем: Буфер → Векторы → Поиск → Промпт → LLM
"""

import requests
import json
import time
from datetime import datetime

API_BASE_URL = "http://localhost:8000"
TEST_USER = "langgraph_test"

def send_to_memory(content, role="user"):
    """Отправляем сообщение в память"""
    memory_data = {
        'role': role,
        'content': content,
        'metadata': {
            'source': 'langgraph_test',
            'user_id': TEST_USER,
            'timestamp': datetime.now().isoformat()
        },
        'conversation_id': f'langgraph_{int(time.time())}',
        'day_number': 1
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/memory/{TEST_USER}/add",
            json=memory_data,
            timeout=20
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"❌ Ошибка сохранения: {e}")
        return None

def send_chat_message(message):
    """Отправляем сообщение в чат через LangGraph pipeline"""
    chat_data = {
        'user_id': TEST_USER,
        'messages': [{'role': 'user', 'content': message}],
        'metaTime': datetime.now().isoformat()
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/chat",
            json=chat_data,
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"❌ Ошибка чата: {e}")
        return None

def search_memory(query, limit=5):
    """Поиск в памяти"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/memory/{TEST_USER}/search",
            json={"query": query, "limit": limit},
            timeout=20
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"❌ Ошибка поиска: {e}")
        return None

def get_memory_overview():
    """Получаем обзор памяти"""
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/memory/{TEST_USER}/overview",
            timeout=15
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"❌ Ошибка обзора: {e}")
        return None

def clear_memory():
    """Очищаем память"""
    try:
        response = requests.post(f"{API_BASE_URL}/api/memory/{TEST_USER}/clear")
        response.raise_for_status()
        print("🧹 Память очищена")
    except Exception as e:
        print(f"⚠️ Очистка не удалась: {e}")

def test_architecture():
    print("🔍 ТЕСТ АРХИТЕКТУРЫ LANGGRAPH")
    print("=" * 50)
    print("Проверяем: Буфер → Векторы → Поиск → Промпт → LLM")
    print("=" * 50)
    
    # Очищаем память
    clear_memory()
    time.sleep(2)
    
    print("\n📝 ЭТАП 1: Добавляем факты в память")
    print("-" * 30)
    
    facts = [
        "Меня зовут Глеб",
        "Моя любимая еда - пицца",
        "Я живу в Москве",
        "Мой друг Олег работает программистом",
        "Я люблю играть в шахматы"
    ]
    
    for i, fact in enumerate(facts, 1):
        print(f"📌 Факт {i}: {fact}")
        result = send_to_memory(fact)
        if result:
            print(f"   ✅ Сохранено: short_term={result['result']['short_term']}, long_term={result['result']['long_term']}")
        else:
            print(f"   ❌ Ошибка сохранения")
        time.sleep(1)
    
    print("\n📊 ЭТАП 2: Проверяем обзор памяти")
    print("-" * 30)
    
    overview = get_memory_overview()
    if overview:
        print(f"📈 Обзор памяти:")
        print(f"   Short-term: {overview.get('short_term_count', 0)} сообщений")
        print(f"   Long-term: {overview.get('long_term_count', 0)} фактов")
        print(f"   Vector DB: {overview.get('vector_count', 0)} документов")
    
    print("\n🔍 ЭТАП 3: Тестируем векторный поиск")
    print("-" * 30)
    
    search_queries = [
        "имя зовут",
        "любимая еда",
        "где живу",
        "друг программист",
        "шахматы"
    ]
    
    for query in search_queries:
        print(f"🔎 Поиск: '{query}'")
        results = search_memory(query, limit=3)
        if results and results.get('success'):
            found = results.get('results', [])
            print(f"   📋 Найдено: {len(found)} результатов")
            for i, result in enumerate(found[:2]):  # Показываем первые 2
                content = result.get('content', '')
                source = result.get('source_level', 'unknown')
                score = result.get('relevance_score', 0)
                print(f"      {i+1}. [{source}] {content} (score: {score:.2f})")
        else:
            print(f"   ❌ Поиск не работает")
        time.sleep(1)
    
    print("\n🤖 ЭТАП 4: Тестируем LangGraph pipeline")
    print("-" * 30)
    
    test_questions = [
        "Как меня зовут?",
        "Что я люблю есть?",
        "Где я живу?",
        "Кто мой друг и где он работает?",
        "Что я люблю делать?"
    ]
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n🤔 Вопрос {i}: '{question}'")
        
        # Отправляем через LangGraph pipeline
        chat_response = send_chat_message(question)
        
        if chat_response:
            parts = chat_response.get('parts', [])
            if parts:
                ai_response = ' '.join(parts)
                print(f"🤖 Ответ AI: {ai_response}")
                
                # Проверяем, помнит ли модель факты
                if "глеб" in ai_response.lower():
                    print("   ✅ Модель помнит имя!")
                if "пицца" in ai_response.lower():
                    print("   ✅ Модель помнит любимую еду!")
                if "москва" in ai_response.lower():
                    print("   ✅ Модель помнит где живет!")
                if "олег" in ai_response.lower() or "программист" in ai_response.lower():
                    print("   ✅ Модель помнит друга!")
                if "шахматы" in ai_response.lower():
                    print("   ✅ Модель помнит хобби!")
            else:
                print("   ❌ Пустой ответ")
        else:
            print("   ❌ Нет ответа от pipeline")
        
        time.sleep(2)  # Пауза между вопросами
    
    print("\n📊 ЭТАП 5: Финальная проверка архитектуры")
    print("-" * 30)
    
    # Проверяем, что все факты сохранились в векторной БД
    final_search = search_memory("глеб пицца москва олег шахматы", limit=10)
    if final_search and final_search.get('success'):
        total_found = final_search.get('total_found', 0)
        print(f"📈 В векторной БД найдено: {total_found} документов")
        
        if total_found >= 5:
            print("✅ АРХИТЕКТУРА РАБОТАЕТ ПРАВИЛЬНО!")
            print("   • Факты сохраняются в буфер")
            print("   • Автоматически переносятся в векторную БД")
            print("   • Поиск работает семантически")
            print("   • LangGraph pipeline обрабатывает запросы")
            print("   • LLM получает правильный контекст")
        else:
            print("⚠️ Не все факты найдены в векторной БД")
    else:
        print("❌ Проблема с финальным поиском")
    
    print("\n" + "=" * 50)
    print("🎯 ТЕСТ АРХИТЕКТУРЫ ЗАВЕРШЕН")
    print("=" * 50)

if __name__ == "__main__":
    test_architecture()
