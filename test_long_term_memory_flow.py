#!/usr/bin/env python3

import requests
import time

def test_long_term_memory():
    """Тест долгосрочной памяти после 10+ сообщений"""
    
    print("🧠 ТЕСТ ДОЛГОСРОЧНОЙ ПАМЯТИ")
    print("=" * 50)
    
    user_id = "1132821710"
    
    # Шаг 1: Очистка памяти
    print("🧹 Шаг 1: Очистка памяти")
    try:
        response = requests.post(f"http://localhost:8000/api/memory/{user_id}/clear", timeout=10)
        print(f"   Очистка: {response.status_code}")
    except Exception as e:
        print(f"   Ошибка: {e}")
    
    # Шаг 2: Добавляем важные факты о пользователе
    print("\n📝 Шаг 2: Добавление важных фактов (первые сообщения)")
    
    important_facts = [
        "Меня зовут Глеб, мне 28 лет",
        "Я работаю Python разработчиком в IT компании", 
        "Увлекаюсь машинным обучением и нейронными сетями",
        "Хожу в спортзал 3 раза в неделю, занимаюсь силовыми тренировками",
        "Читаю книги по Data Science и технологиям"
    ]
    
    for i, fact in enumerate(important_facts):
        try:
            memory_data = {
                'role': 'user',
                'content': fact,
                'metadata': {
                    'source': 'long_term_test',
                    'user_id': user_id,
                    'timestamp': f'2025-09-02T14:0{i}:00Z',
                    'importance': 'high',
                    'category': 'personal_info'
                },
                'conversation_id': f'long_term_test_{user_id}',
                'day_number': 1
            }
            
            response = requests.post(
                f"http://localhost:8000/api/memory/{user_id}/add",
                json=memory_data,
                timeout=15
            )
            
            if response.status_code == 200:
                print(f"   ✅ Факт {i+1}: {fact}")
            else:
                print(f"   ❌ Факт {i+1}: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Факт {i+1}: {e}")
    
    # Шаг 3: Добавляем 10+ промежуточных сообщений
    print(f"\n🔄 Шаг 3: Добавление 12 промежуточных сообщений")
    
    filler_messages = [
        "Привет, как дела?",
        "Что делаешь сегодня?", 
        "Какая погода?",
        "Как прошел день?",
        "Что планируешь на выходные?",
        "Смотрел ли новые фильмы?",
        "Как настроение?",
        "Что нового в работе?",
        "Как здоровье?",
        "Планы на вечер?",
        "Что интересного читаешь?",
        "Как проходит неделя?"
    ]
    
    for i, message in enumerate(filler_messages):
        try:
            memory_data = {
                'role': 'user',
                'content': message,
                'metadata': {
                    'source': 'filler',
                    'user_id': user_id,
                    'timestamp': f'2025-09-02T15:{i:02d}:00Z',
                    'importance': 'low',
                    'category': 'casual'
                },
                'conversation_id': f'filler_{user_id}',
                'day_number': 1
            }
            
            response = requests.post(
                f"http://localhost:8000/api/memory/{user_id}/add",
                json=memory_data,
                timeout=15
            )
            
            if response.status_code == 200:
                print(f"   ✅ Сообщение {i+1}: {message}")
            else:
                print(f"   ❌ Сообщение {i+1}: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Сообщение {i+1}: {e}")
    
    # Шаг 4: Ждем индексации
    print(f"\n⏳ Шаг 4: Ждем индексации (10 секунд)")
    time.sleep(10)
    
    # Шаг 5: Проверяем поиск в векторной БД
    print(f"\n🔍 Шаг 5: Проверка поиска в векторной БД")
    try:
        search_data = {
            'query': 'Глеб работа программист Python машинное обучение',
            'max_results': 10,
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
            print(f"   ✅ Найдено: {found_count} результатов")
            
            if found_count > 0:
                results = result.get('results', [])
                important_found = 0
                for i, item in enumerate(results):
                    content = item.get('content', '')
                    score = item.get('relevance_score', 0)
                    print(f"      {i+1}. {content} (score: {score:.2f})")
                    
                    # Проверяем, нашли ли важные факты
                    if any(keyword in content.lower() for keyword in ["глеб", "python", "разработчик", "машинн", "спорт"]):
                        important_found += 1
                
                print(f"   📊 Важных фактов найдено: {important_found}/{len(important_facts)}")
        else:
            print(f"   ❌ Ошибка поиска: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
    
    # Шаг 6: ГЛАВНЫЙ ТЕСТ - спрашиваем о фактах через ИИ
    print(f"\n🤖 Шаг 6: ГЛАВНЫЙ ТЕСТ - вопрос через ИИ")
    try:
        chat_data = {
            'user_id': user_id,
            'messages': [{'role': 'user', 'content': 'Расскажи мне о себе: как меня зовут, сколько лет, кем работаю, чем увлекаюсь?'}],
            'metaTime': "2025-09-02T16:00:00Z"
        }
        
        print("   ❓ Вопрос: 'Расскажи мне о себе: как меня зовут, сколько лет, кем работаю, чем увлекаюсь?'")
        
        response = requests.post(
            "http://localhost:8000/api/chat",
            json=chat_data,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            parts = result.get('parts', [])
            
            if parts:
                ai_response = ' '.join(parts)
                print(f"\n   🤖 ОТВЕТ ИИ:")
                print(f"   {ai_response}")
                
                # Детальная проверка использования долгосрочной памяти
                memory_checks = {
                    "имя": ["глеб"],
                    "возраст": ["28"],
                    "работа": ["python", "разработчик", "программист"],
                    "увлечения": ["машинн", "нейронн", "спорт", "data science"],
                }
                
                found_categories = []
                for category, keywords in memory_checks.items():
                    if any(keyword.lower() in ai_response.lower() for keyword in keywords):
                        found_categories.append(category)
                
                print(f"\n   📊 АНАЛИЗ ДОЛГОСРОЧНОЙ ПАМЯТИ:")
                print(f"   ✅ НАЙДЕННЫЕ КАТЕГОРИИ: {', '.join(found_categories)}")
                print(f"   📈 ИСПОЛЬЗОВАНИЕ ПАМЯТИ: {len(found_categories)}/4 категорий")
                
                if len(found_categories) >= 3:
                    print(f"   🎉 УСПЕХ! ДОЛГОСРОЧНАЯ ПАМЯТЬ РАБОТАЕТ")
                    print(f"   ✅ ИИ помнит информацию даже после 12 промежуточных сообщений")
                elif len(found_categories) >= 1:
                    print(f"   ⚠️ ЧАСТИЧНЫЙ УСПЕХ: Память работает, но не полностью")
                else:
                    print(f"   ❌ ПРОВАЛ: Долгосрочная память НЕ работает")
                    print(f"   🔧 ИИ не использует факты, добавленные в начале")
            else:
                print("   ❌ Нет ответа от ИИ")
        else:
            print(f"   ❌ Ошибка API: {response.status_code}")
            print(f"   Ответ: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
    
    print(f"\n" + "=" * 50)
    if len(found_categories) >= 3:
        print("🎉 ДОЛГОСРОЧНАЯ ПАМЯТЬ РАБОТАЕТ ПРАВИЛЬНО!")
        print("✅ Система помнит важные факты даже после множества промежуточных сообщений")
    else:
        print("❌ ПРОБЛЕМА С ДОЛГОСРОЧНОЙ ПАМЯТЬЮ")
        print("🔧 Система не сохраняет/не использует важную информацию долгосрочно")

if __name__ == "__main__":
    test_long_term_memory()
