#!/usr/bin/env python3

import requests
import time

def final_memory_fix():
    """Финальное исправление памяти"""
    
    print("🔧 ФИНАЛЬНОЕ ИСПРАВЛЕНИЕ ПАМЯТИ")
    print("=" * 50)
    
    user_id = "1132821710"
    
    # Шаг 1: Очистка
    print("🧹 Шаг 1: Полная очистка памяти")
    try:
        response = requests.post(f"http://localhost:8000/api/memory/{user_id}/clear", timeout=10)
        print(f"   Очистка: {response.status_code}")
    except Exception as e:
        print(f"   Ошибка: {e}")
    
    # Шаг 2: Добавляем ОЧЕНЬ конкретную информацию
    print("\n📝 Шаг 2: Добавление КОНКРЕТНОЙ информации")
    
    specific_info = [
        "Глеб любит программировать на Python",
        "Глеб увлекается машинным обучением и ИИ", 
        "Глеб занимается спортом в спортзале",
        "Глеб читает книги по технологиям",
        "Глеб работает разработчиком"
    ]
    
    for info in specific_info:
        try:
            memory_data = {
                'role': 'user',
                'content': info,
                'metadata': {
                    'source': 'final_fix',
                    'user_id': user_id,
                    'timestamp': '2025-09-02T14:07:00Z',
                    'importance': 'high',
                    'category': 'personal_info'
                },
                'conversation_id': f'final_fix_{user_id}',
                'day_number': 1
            }
            
            response = requests.post(
                f"http://localhost:8000/api/memory/{user_id}/add",
                json=memory_data,
                timeout=15
            )
            
            if response.status_code == 200:
                print(f"   ✅ {info}")
            else:
                print(f"   ❌ {info}: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ {info}: {e}")
    
    # Шаг 3: Ждем индексации
    print("\n⏳ Шаг 3: Ждем индексации (5 секунд)")
    time.sleep(5)
    
    # Шаг 4: Проверяем поиск
    print("\n🔍 Шаг 4: Проверка поиска в памяти")
    try:
        search_data = {
            'query': 'что любит Глеб программирование спорт',
            'max_results': 10,
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
            print(f"   ✅ Найдено: {found_count} результатов")
            
            if found_count > 0:
                results = result.get('results', [])
                for i, item in enumerate(results[:5]):
                    content = item.get('content', '')
                    score = item.get('relevance_score', 0)
                    print(f"      {i+1}. {content} (score: {score:.2f})")
        else:
            print(f"   ❌ Ошибка поиска: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
    
    # Шаг 5: Тестируем с ПРЯМЫМ вопросом
    print("\n🤖 Шаг 5: Тест с прямым вопросом")
    try:
        chat_data = {
            'user_id': user_id,
            'messages': [{'role': 'user', 'content': 'Что ты знаешь о моих увлечениях? Чем я люблю заниматься?'}],
            'metaTime': "2025-09-02T14:07:00Z"
        }
        
        print("   ❓ Вопрос: 'Что ты знаешь о моих увлечениях? Чем я люблю заниматься?'")
        
        response = requests.post(
            "http://localhost:8000/api/chat",
            json=chat_data,
            timeout=45
        )
        
        if response.status_code == 200:
            result = response.json()
            parts = result.get('parts', [])
            
            if parts:
                ai_response = ' '.join(parts)
                print(f"\n   🤖 ПОЛНЫЙ ОТВЕТ:")
                print(f"   {ai_response}")
                
                # Детальная проверка
                keywords_found = []
                keywords_check = {
                    "программир": "программирование",
                    "python": "Python", 
                    "машинн": "машинное обучение",
                    "ИИ": "ИИ",
                    "спорт": "спорт",
                    "технолог": "технологии",
                    "разработ": "разработка"
                }
                
                for key, name in keywords_check.items():
                    if key.lower() in ai_response.lower():
                        keywords_found.append(name)
                
                print(f"\n   📊 АНАЛИЗ:")
                if keywords_found:
                    print(f"   ✅ НАЙДЕННЫЕ УВЛЕЧЕНИЯ: {', '.join(keywords_found)}")
                else:
                    print(f"   ❌ НЕ НАЙДЕНО УВЛЕЧЕНИЙ")
                    
                if "не знаю" in ai_response.lower() or "нет информации" in ai_response.lower():
                    print(f"   ❌ ИИ ВСЕ ЕЩЕ ГОВОРИТ 'НЕ ЗНАЮ'")
                else:
                    print(f"   ✅ ИИ НЕ ГОВОРИТ 'НЕ ЗНАЮ'")
                    
                if len(keywords_found) >= 3:
                    print(f"   🎉 УСПЕХ! ИИ ИСПОЛЬЗУЕТ СОХРАНЕННУЮ ИНФОРМАЦИЮ")
                else:
                    print(f"   ❌ ПРОБЛЕМА: ИИ НЕ ИСПОЛЬЗУЕТ ПАМЯТЬ ПОЛНОСТЬЮ")
            else:
                print("   ❌ Нет ответа от ИИ")
        else:
            print(f"   ❌ Ошибка API: {response.status_code}")
            print(f"   Ответ: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
    
    print("\n" + "=" * 50)
    if keywords_found and len(keywords_found) >= 3:
        print("🎉 ПАМЯТЬ РАБОТАЕТ ПРАВИЛЬНО!")
        print("✅ Telegram бот теперь использует сохраненную информацию")
    else:
        print("❌ ПАМЯТЬ ВСЕ ЕЩЕ НЕ РАБОТАЕТ")
        print("🔧 Нужны дополнительные исправления")

if __name__ == "__main__":
    final_memory_fix()
