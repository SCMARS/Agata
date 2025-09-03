#!/usr/bin/env python3

import requests
import time

def debug_vector_indexing():
    """Диагностика индексации в векторную БД"""
    
    print("🔍 ДИАГНОСТИКА ВЕКТОРНОЙ ИНДЕКСАЦИИ")
    print("=" * 50)
    
    user_id = "1132821710"
    
    # Шаг 1: Очистка
    print("🧹 Шаг 1: Очистка памяти")
    try:
        response = requests.post(f"http://localhost:8000/api/memory/{user_id}/clear", timeout=10)
        print(f"   Очистка: {response.status_code}")
    except Exception as e:
        print(f"   Ошибка: {e}")
    
    # Шаг 2: Добавляем ОДИН важный факт
    print("\n📝 Шаг 2: Добавление ОДНОГО важного факта")
    
    test_fact = "Меня зовут Глеб Уховский, я Senior Python Developer, увлекаюсь пауэрлифтингом и играю в шахматы"
    
    try:
        memory_data = {
            'role': 'user',
            'content': test_fact,
            'metadata': {
                'source': 'debug_test',
                'user_id': user_id,
                'timestamp': '2025-09-03T20:00:00Z',
                'importance': 'high',
                'category': 'personal_info'
            },
            'conversation_id': f'debug_test_{user_id}',
            'day_number': 1
        }
        
        response = requests.post(
            f"http://localhost:8000/api/memory/{user_id}/add",
            json=memory_data,
            timeout=15
        )
        
        if response.status_code == 200:
            print(f"   ✅ Факт добавлен: {test_fact}")
        else:
            print(f"   ❌ Ошибка добавления: {response.status_code}")
            print(f"   Ответ: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
    
    # Шаг 3: Ждем индексации
    print(f"\n⏳ Шаг 3: Ждем индексации (10 секунд)")
    time.sleep(10)
    
    # Шаг 4: Проверяем разные типы поиска
    print(f"\n🔍 Шаг 4: Тестируем разные запросы поиска")
    
    search_queries = [
        "Уховский",
        "Senior Python Developer", 
        "пауэрлифтинг",
        "шахматы",
        "Глеб Уховский Senior",
        "Python Developer пауэрлифтинг",
        "личная информация пользователь"
    ]
    
    for i, query in enumerate(search_queries):
        try:
            search_data = {
                'query': query,
                'max_results': 5,
                'levels': ['long_term']
            }
            
            response = requests.post(
                f"http://localhost:8000/api/memory/{user_id}/search",
                json=search_data,
                timeout=15
            )
            
            if response.status_code == 200:
                result = response.json()
                found_count = result.get('total_found', 0)
                
                if found_count > 0:
                    results = result.get('results', [])
                    best_result = results[0]
                    content = best_result.get('content', '')
                    score = best_result.get('relevance_score', 0)
                    print(f"   ✅ '{query}' → {found_count} результатов, лучший: {content[:60]}... (score: {score:.3f})")
                else:
                    print(f"   ❌ '{query}' → НЕ НАЙДЕНО")
            else:
                print(f"   ❌ '{query}' → Ошибка: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ '{query}' → Ошибка: {e}")
    
    # Шаг 5: Проверяем через ИИ
    print(f"\n🤖 Шаг 5: Тест через ИИ")
    try:
        chat_data = {
            'user_id': user_id,
            'messages': [{'role': 'user', 'content': 'Как меня зовут и кем я работаю?'}],
            'metaTime': "2025-09-03T20:30:00Z"
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
                print(f"   🤖 ОТВЕТ: {ai_response}")
                
                # Проверяем, нашел ли ИИ информацию
                found_keywords = []
                if "уховский" in ai_response.lower():
                    found_keywords.append("фамилия")
                if "senior" in ai_response.lower():
                    found_keywords.append("должность")
                if "python" in ai_response.lower():
                    found_keywords.append("технология")
                if "пауэрлифтинг" in ai_response.lower():
                    found_keywords.append("спорт")
                if "шахмат" in ai_response.lower():
                    found_keywords.append("хобби")
                
                if found_keywords:
                    print(f"   ✅ ИИ нашел: {', '.join(found_keywords)}")
                else:
                    print(f"   ❌ ИИ НЕ нашел информацию из векторной БД")
            else:
                print("   ❌ Нет ответа от ИИ")
        else:
            print(f"   ❌ Ошибка API: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
    
    print(f"\n" + "=" * 50)
    print("ДИАГНОСТИКА ЗАВЕРШЕНА")
    
    if found_keywords and len(found_keywords) >= 3:
        print("✅ Векторная индексация работает")
    else:
        print("❌ ПРОБЛЕМА: Векторная индексация НЕ работает")
        print("🔧 Возможные причины:")
        print("   - Данные не сохраняются в векторную БД")
        print("   - Поиск работает неправильно") 
        print("   - MemoryAdapter не передает данные в промпт")

if __name__ == "__main__":
    debug_vector_indexing()
