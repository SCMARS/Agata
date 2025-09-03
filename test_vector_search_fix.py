#!/usr/bin/env python3

import requests
import time
import json

def test_vector_search_fix():
    """Тестируем исправления векторного поиска"""
    
    print("🔍 ТЕСТ ИСПРАВЛЕНИЙ ВЕКТОРНОГО ПОИСКА")
    print("=" * 50)
    
    user_id = "1132821710"
    
    # Шаг 1: Очищаем память
    print("🧹 Шаг 1: Очистка памяти")
    try:
        response = requests.post(f"http://localhost:8000/api/memory/{user_id}/clear", timeout=10)
        print(f"   Очистка: {response.status_code}")
    except Exception as e:
        print(f"   Ошибка очистки: {e}")
    
    # Шаг 2: Добавляем конкретную информацию о предпочтениях
    print("\n📝 Шаг 2: Добавление информации о предпочтениях")
    
    preferences = [
        "Я люблю программировать на Python",
        "Мне нравится машинное обучение",
        "Я увлекаюсь спортом и хожу в спортзал",
        "Люблю читать книги по технологиям",
        "Мне интересна разработка ИИ"
    ]
    
    for i, pref in enumerate(preferences):
        try:
            memory_data = {
                'role': 'user',
                'content': pref,
                'metadata': {
                    'source': 'vector_test',
                    'user_id': user_id,
                    'timestamp': '2025-09-02T14:07:00Z',
                    'preference': True
                },
                'conversation_id': f'vector_test_{user_id}',
                'day_number': 1
            }
            
            response = requests.post(
                f"http://localhost:8000/api/memory/{user_id}/add",
                json=memory_data,
                timeout=10
            )
            
            if response.status_code == 200:
                print(f"   ✅ Добавлено: {pref}")
            else:
                print(f"   ❌ Ошибка: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Ошибка: {e}")
    
    # Шаг 3: Ждем индексации
    print("\n⏳ Шаг 3: Ждем индексации (3 секунды)")
    time.sleep(3)
    
    # Шаг 4: Тестируем поиск в памяти напрямую
    print("\n🔍 Шаг 4: Прямой поиск в памяти")
    try:
        search_data = {
            'query': 'что я люблю программирование спорт',
            'max_results': 5,
            'levels': ['short_term', 'long_term']
        }
        
        response = requests.post(
            f"http://localhost:8000/api/memory/{user_id}/search",
            json=search_data,
            timeout=15
        )
        
        if response.status_code == 200:
            result = response.json()
            found_count = result.get('total_found', 0)
            print(f"   ✅ Найдено результатов: {found_count}")
            
            if found_count > 0:
                results = result.get('results', [])
                for i, item in enumerate(results[:3]):
                    content = item.get('content', '')
                    level = item.get('source_level', 'unknown')
                    score = item.get('relevance_score', 0)
                    print(f"      {i+1}. [{level}] {content} (score: {score:.2f})")
            else:
                print("   ⚠️ Результаты не найдены")
        else:
            print(f"   ❌ Ошибка поиска: {response.status_code}")
            print(f"   Ответ: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
    
    # Шаг 5: Тестируем через chat API
    print("\n🤖 Шаг 5: Тест через chat API")
    try:
        chat_data = {
            'user_id': user_id,
            'messages': [{'role': 'user', 'content': 'Что я люблю делать?'}],
            'metaTime': "2025-09-02T14:07:00Z"
        }
        
        print("   Отправляем вопрос: 'Что я люблю делать?'")
        
        response = requests.post(
            "http://localhost:8000/api/chat",
            json=chat_data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            parts = result.get('parts', [])
            
            if parts:
                ai_response = ' '.join(parts)
                print(f"   🤖 Ответ: {ai_response[:200]}...")
                
                # Проверяем, упоминаются ли предпочтения
                found_prefs = []
                for pref in ["программир", "машинн", "спорт", "книг", "ИИ", "Python"]:
                    if pref.lower() in ai_response.lower():
                        found_prefs.append(pref)
                
                if found_prefs:
                    print(f"   ✅ УСПЕХ! Найдены предпочтения: {', '.join(found_prefs)}")
                else:
                    print("   ❌ ПРОБЛЕМА: Предпочтения не найдены в ответе")
                    
                # Проверяем, не начинается ли с приветствия
                if ai_response.startswith("Добрый день"):
                    print("   ⚠️ ВНИМАНИЕ: Ответ начинается с приветствия (возможно, контекст не используется)")
                else:
                    print("   ✅ Ответ не начинается с стандартного приветствия")
            else:
                print("   ❌ Нет частей в ответе")
        else:
            print(f"   ❌ Ошибка chat API: {response.status_code}")
            print(f"   Ответ: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
    
    # Шаг 6: Тест с добавлением еще сообщений
    print("\n📝 Шаг 6: Добавляем промежуточные сообщения")
    
    filler_messages = [
        "Как дела?",
        "Что нового?", 
        "Хорошая погода сегодня",
        "Планы на выходные?",
        "Как работа?"
    ]
    
    for msg in filler_messages:
        try:
            memory_data = {
                'role': 'user',
                'content': msg,
                'metadata': {
                    'source': 'vector_test_filler',
                    'user_id': user_id,
                    'timestamp': '2025-09-02T14:07:00Z'
                },
                'conversation_id': f'vector_test_{user_id}',
                'day_number': 1
            }
            
            response = requests.post(
                f"http://localhost:8000/api/memory/{user_id}/add",
                json=memory_data,
                timeout=10
            )
            
            if response.status_code == 200:
                print(f"   ✅ Добавлено: {msg}")
            else:
                print(f"   ❌ Ошибка: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Ошибка: {e}")
    
    # Шаг 7: Повторный тест после промежуточных сообщений
    print("\n🔍 Шаг 7: Повторный тест поиска")
    try:
        chat_data = {
            'user_id': user_id,
            'messages': [{'role': 'user', 'content': 'Напомни, что я люблю делать?'}],
            'metaTime': "2025-09-02T14:07:00Z"
        }
        
        response = requests.post(
            "http://localhost:8000/api/chat",
            json=chat_data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            parts = result.get('parts', [])
            
            if parts:
                ai_response = ' '.join(parts)
                print(f"   🤖 Ответ: {ai_response[:200]}...")
                
                # Проверяем, упоминаются ли предпочтения
                found_prefs = []
                for pref in ["программир", "машинн", "спорт", "книг", "ИИ", "Python"]:
                    if pref.lower() in ai_response.lower():
                        found_prefs.append(pref)
                
                if found_prefs:
                    print(f"   ✅ ОТЛИЧНО! Долгосрочная память работает: {', '.join(found_prefs)}")
                else:
                    print("   ❌ ПРОБЛЕМА: Долгосрочная память не работает")
            else:
                print("   ❌ Нет ответа")
        else:
            print(f"   ❌ Ошибка: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 ТЕСТ ЗАВЕРШЕН")

if __name__ == "__main__":
    test_vector_search_fix()
