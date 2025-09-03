#!/usr/bin/env python3

import requests
import time

def final_vector_diagnosis():
    """Финальная диагностика всей цепочки векторной памяти"""
    
    print("🔍 ФИНАЛЬНАЯ ДИАГНОСТИКА ВЕКТОРНОЙ ПАМЯТИ")
    print("=" * 60)
    
    user_id = "1132821710"
    
    # Шаг 1: Очистка
    print("🧹 Шаг 1: Полная очистка")
    try:
        response = requests.post(f"http://localhost:8000/api/memory/{user_id}/clear", timeout=10)
        print(f"   Очистка: {response.status_code}")
    except Exception as e:
        print(f"   Ошибка: {e}")
    
    # Шаг 2: Добавляем ОДИН конкретный факт
    print("\n📝 Шаг 2: Добавление ОДНОГО конкретного факта")
    
    test_fact = "Меня зовут Глеб Уховский, я Senior Python Developer в компании TechCorp, увлекаюсь пауэрлифтингом"
    
    try:
        memory_data = {
            'role': 'user',
            'content': test_fact,
            'metadata': {
                'source': 'final_diagnosis',
                'user_id': user_id,
                'timestamp': '2025-09-03T21:10:00Z',
                'importance': 'high',
                'category': 'personal_info'
            },
            'conversation_id': f'final_diagnosis_{user_id}',
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
            print(f"   ❌ Ошибка: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
    
    # Шаг 3: Ждем
    print(f"\n⏳ Шаг 3: Ждем индексации (5 секунд)")
    time.sleep(5)
    
    # Шаг 4: Прямой поиск в векторной БД
    print(f"\n🔍 Шаг 4: Прямой поиск в векторной БД")
    try:
        search_data = {
            'query': 'Глеб Уховский Senior Python Developer TechCorp пауэрлифтинг',
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
            print(f"   ✅ Векторная БД нашла: {found_count} результатов")
            
            if found_count > 0:
                results = result.get('results', [])
                for i, item in enumerate(results):
                    content = item.get('content', '')
                    score = item.get('relevance_score', 0)
                    print(f"      {i+1}. {content} (score: {score:.3f})")
                    
                    # Проверяем наличие ключевых слов
                    if "уховский" in content.lower() and "senior" in content.lower():
                        print(f"         ✅ СОДЕРЖИТ: полное имя и должность")
                    elif "уховский" in content.lower():
                        print(f"         ⚠️ СОДЕРЖИТ: только полное имя")
                    elif "senior" in content.lower():
                        print(f"         ⚠️ СОДЕРЖИТ: только должность")
                    else:
                        print(f"         ❌ НЕ СОДЕРЖИТ: ни полное имя, ни должность")
        else:
            print(f"   ❌ Ошибка поиска: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
    
    # Шаг 5: Тест через ИИ с ПРЯМЫМ вопросом
    print(f"\n🤖 Шаг 5: Тест через ИИ с ПРЯМЫМ вопросом")
    try:
        chat_data = {
            'user_id': user_id,
            'messages': [{'role': 'user', 'content': 'Назови мое полное имя и точную должность'}],
            'metaTime': "2025-09-03T21:15:00Z"
        }
        
        print("   ❓ ВОПРОС: 'Назови мое полное имя и точную должность'")
        
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
                print(f"\n   🤖 ОТВЕТ ИИ:")
                print(f"   {ai_response}")
                
                # ТОЧНАЯ проверка
                has_full_name = "уховский" in ai_response.lower()
                has_senior_title = "senior" in ai_response.lower()
                has_company = "techcorp" in ai_response.lower()
                has_sport = "пауэрлифтинг" in ai_response.lower()
                
                print(f"\n   📊 ДЕТАЛЬНЫЙ АНАЛИЗ:")
                print(f"   {'✅' if has_full_name else '❌'} Полное имя (Уховский): {has_full_name}")
                print(f"   {'✅' if has_senior_title else '❌'} Должность (Senior): {has_senior_title}")
                print(f"   {'✅' if has_company else '❌'} Компания (TechCorp): {has_company}")
                print(f"   {'✅' if has_sport else '❌'} Хобби (пауэрлифтинг): {has_sport}")
                
                success_count = sum([has_full_name, has_senior_title, has_company, has_sport])
                
                if success_count >= 3:
                    print(f"   🎉 УСПЕХ: ИИ использует векторную память ({success_count}/4)")
                elif success_count >= 1:
                    print(f"   ⚠️ ЧАСТИЧНЫЙ УСПЕХ: ({success_count}/4)")
                else:
                    print(f"   ❌ ПРОВАЛ: ИИ НЕ использует векторную память (0/4)")
                    
            else:
                print("   ❌ Нет ответа от ИИ")
        else:
            print(f"   ❌ Ошибка API: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
    
    # Шаг 6: Проверяем, что передается в MemoryAdapter
    print(f"\n🔧 Шаг 6: Диагностика MemoryAdapter")
    print("   Смотрим логи сервера для диагностики...")
    
    print(f"\n" + "=" * 60)
    
    if success_count >= 3:
        print("🎉 ВЕКТОРНАЯ ПАМЯТЬ РАБОТАЕТ ПОЛНОСТЬЮ!")
        print("✅ ИИ корректно использует данные из долгосрочной памяти")
    elif success_count >= 1:
        print("⚠️ ВЕКТОРНАЯ ПАМЯТЬ РАБОТАЕТ ЧАСТИЧНО")
        print("🔧 Некоторые данные теряются в процессе передачи")
    else:
        print("❌ КРИТИЧЕСКАЯ ПРОБЛЕМА С ВЕКТОРНОЙ ПАМЯТЬЮ")
        print("🔧 ИИ полностью игнорирует долгосрочную память")
        print("🔧 Проблема может быть в:")
        print("   - MemoryAdapter не находит данные")
        print("   - Данные не передаются в промпт")
        print("   - Системный промпт игнорирует память")

if __name__ == "__main__":
    final_vector_diagnosis()
