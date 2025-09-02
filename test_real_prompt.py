#!/usr/bin/env python3
"""
Тест РЕАЛЬНОГО промпта и ответов модели
Показывает что именно подставляется в промпт и что отвечает AI
"""

import requests
import json
import time
from datetime import datetime

API_BASE_URL = "http://localhost:8000"
TEST_USER = "prompt_test"

def clear_memory():
    """Очищает память"""
    try:
        requests.post(f"{API_BASE_URL}/api/memory/{TEST_USER}/clear", timeout=10)
        print("🧹 Память очищена")
    except:
        print("⚠️ Очистка не удалась")

def add_fact(content):
    """Добавляет факт в память"""
    memory_data = {
        'role': 'user',
        'content': content,
        'metadata': {'source': 'test', 'user_id': TEST_USER, 'timestamp': datetime.now().isoformat()},
        'conversation_id': f'test_{int(datetime.now().timestamp())}',
        'day_number': 1
    }
    
    try:
        response = requests.post(f"{API_BASE_URL}/api/memory/{TEST_USER}/add", json=memory_data, timeout=20)
        if response.status_code == 200:
            result = response.json().get('result', {})
            print(f"✅ Факт сохранен: short_term={result.get('short_term')}, long_term={result.get('long_term')}")
            return True
        else:
            print(f"❌ Ошибка сохранения: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

def test_chat_with_debug(question):
    """Тестирует чат с отладочной информацией"""
    print(f"\n🤔 ВОПРОС: '{question}'")
    print("-" * 50)
    
    try:
        chat_data = {
            'user_id': TEST_USER,
            'messages': [{'role': 'user', 'content': question}],
            'metaTime': datetime.now().isoformat()
        }
        
        response = requests.post(f"{API_BASE_URL}/api/chat", json=chat_data, timeout=45)
        
        if response.status_code == 200:
            chat_result = response.json()
            
            # Показываем ПОЛНЫЙ результат
            print("📋 ПОЛНЫЙ ОТВЕТ API:")
            print(json.dumps(chat_result, indent=2, ensure_ascii=False))
            
            parts = chat_result.get('parts', [])
            if parts:
                ai_response = ' '.join(parts)
                print(f"\n🤖 ОТВЕТ МОДЕЛИ: {ai_response}")
                return ai_response
            else:
                print("❌ Пустой ответ от модели")
                return ""
        else:
            print(f"❌ Ошибка chat API: {response.status_code}")
            print(f"Ответ: {response.text}")
            return ""
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return ""

def check_memory_search(query):
    """Проверяет прямой поиск в памяти"""
    print(f"\n🔍 ПРЯМОЙ ПОИСК В ПАМЯТИ: '{query}'")
    print("-" * 40)
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/memory/{TEST_USER}/search",
            json={"query": query, "limit": 5},
            timeout=15
        )
        if response.status_code == 200:
            results = response.json()
            found_results = results.get('results', [])
            print(f"📊 Найдено результатов: {len(found_results)}")
            
            for i, result in enumerate(found_results, 1):
                content = result.get('content', '')
                score = result.get('score', 'N/A')
                print(f"  {i}. {content} (релевантность: {score})")
            
            return found_results
        else:
            print(f"❌ Ошибка поиска: {response.status_code}")
            return []
    except Exception as e:
        print(f"❌ Ошибка поиска: {e}")
        return []

def main():
    """Основной тест"""
    print("🔍 ТЕСТ РЕАЛЬНОГО ПРОМПТА И ОТВЕТОВ")
    print("=" * 60)
    
    # Ждем запуска
    print("⏳ Ждем запуска системы...")
    time.sleep(10)
    
    # Очищаем память
    clear_memory()
    time.sleep(2)
    
    # Добавляем факты
    print("\n📝 ДОБАВЛЯЕМ ФАКТЫ...")
    add_fact("Меня зовут Глеб")
    time.sleep(3)
    add_fact("Я работаю программистом")
    time.sleep(3)
    add_fact("Люблю пиццу с грибами")
    time.sleep(3)
    
    # Добавляем обычные сообщения
    print("\n💬 ДОБАВЛЯЕМ ОБЫЧНЫЕ СООБЩЕНИЯ...")
    ordinary = ["Привет", "Как дела", "Хорошая погода", "Что нового", "Интересно"]
    for msg in ordinary:
        add_fact(msg)
        time.sleep(2)
    
    # Проверяем прямой поиск в памяти
    print("\n" + "=" * 60)
    print("🔍 ПРОВЕРЯЕМ ПРЯМОЙ ПОИСК В ВЕКТОРНОЙ БД")
    print("=" * 60)
    
    name_results = check_memory_search("как меня зовут")
    work_results = check_memory_search("где я работаю")
    food_results = check_memory_search("что я люблю есть")
    
    # Тестируем РЕАЛЬНЫЕ ответы модели
    print("\n" + "=" * 60)
    print("🤖 ТЕСТИРУЕМ РЕАЛЬНЫЕ ОТВЕТЫ МОДЕЛИ")
    print("=" * 60)
    
    # Вопрос 1: Имя
    response1 = test_chat_with_debug("Как меня зовут?")
    name_remembered = "глеб" in response1.lower()
    
    time.sleep(5)
    
    # Вопрос 2: Работа  
    response2 = test_chat_with_debug("Кем я работаю?")
    work_remembered = "программист" in response2.lower()
    
    time.sleep(5)
    
    # Вопрос 3: Еда
    response3 = test_chat_with_debug("Что я люблю есть?")
    food_remembered = "пицца" in response3.lower() or "гриб" in response3.lower()
    
    # ИТОГОВЫЙ АНАЛИЗ
    print("\n" + "=" * 60)
    print("📊 АНАЛИЗ РЕАЛЬНОЙ РАБОТЫ СИСТЕМЫ")
    print("=" * 60)
    
    print(f"🔍 ПОИСК В ВЕКТОРНОЙ БД:")
    print(f"  • Поиск имени: {len(name_results)} результатов")
    print(f"  • Поиск работы: {len(work_results)} результатов")
    print(f"  • Поиск еды: {len(food_results)} результатов")
    
    print(f"\n🤖 ОТВЕТЫ МОДЕЛИ:")
    print(f"  • Помнит имя 'Глеб': {'✅' if name_remembered else '❌'}")
    print(f"  • Помнит работу 'программист': {'✅' if work_remembered else '❌'}")
    print(f"  • Помнит еду 'пицца с грибами': {'✅' if food_remembered else '❌'}")
    
    total_success = sum([name_remembered, work_remembered, food_remembered])
    
    print(f"\n🎯 ОБЩИЙ РЕЗУЛЬТАТ: {total_success}/3 фактов помнит модель")
    
    if total_success == 3:
        print("🎉 ОТЛИЧНО! Архитектура работает правильно!")
        print("   ✅ Векторная БД сохраняет факты")
        print("   ✅ Поиск находит релевантную информацию") 
        print("   ✅ Модель получает правильный контекст в промпте")
    elif total_success >= 2:
        print("👍 ХОРОШО! Система работает, есть мелкие проблемы")
    else:
        print("❌ ПРОБЛЕМЫ! Архитектура работает неправильно")

if __name__ == "__main__":
    main()
