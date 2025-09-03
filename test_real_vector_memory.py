#!/usr/bin/env python3

import requests
import time

def test_real_vector_memory():
    """РЕАЛЬНЫЙ тест векторной памяти - добавляем 50+ сообщений"""
    
    print("🔍 РЕАЛЬНЫЙ ТЕСТ ВЕКТОРНОЙ БАЗЫ ДАННЫХ")
    print("=" * 60)
    
    user_id = "1132821710"
    
    # Шаг 1: Очистка
    print("🧹 Шаг 1: Полная очистка памяти")
    try:
        response = requests.post(f"http://localhost:8000/api/memory/{user_id}/clear", timeout=10)
        print(f"   Очистка: {response.status_code}")
    except Exception as e:
        print(f"   Ошибка: {e}")
    
    # Шаг 2: Добавляем важные факты в САМОМ НАЧАЛЕ
    print("\n📝 Шаг 2: Добавление важных фактов (САМОЕ НАЧАЛО)")
    
    important_facts = [
        "Меня зовут Глеб Уховский, мне 28 лет, родился в Москве",
        "Работаю Senior Python Developer в крупной IT компании", 
        "Специализируюсь на машинном обучении и Computer Vision",
        "Увлекаюсь глубоким обучением, работаю с PyTorch и TensorFlow",
        "Хожу в спортзал 4 раза в неделю, занимаюсь пауэрлифтингом",
        "Читаю книги по AI/ML, недавно изучал трансформеры",
        "Люблю играть в шахматы, мой рейтинг 1800 ELO",
        "Изучаю японский язык, планирую поездку в Токио"
    ]
    
    for i, fact in enumerate(important_facts):
        try:
            memory_data = {
                'role': 'user',
                'content': fact,
                'metadata': {
                    'source': 'vector_test_facts',
                    'user_id': user_id,
                    'timestamp': f'2025-09-01T10:{i:02d}:00Z',
                    'importance': 'high',
                    'category': 'personal_info'
                },
                'conversation_id': f'vector_test_{user_id}',
                'day_number': 1
            }
            
            response = requests.post(
                f"http://localhost:8000/api/memory/{user_id}/add",
                json=memory_data,
                timeout=15
            )
            
            if response.status_code == 200:
                print(f"   ✅ Факт {i+1}: {fact[:50]}...")
            else:
                print(f"   ❌ Факт {i+1}: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Факт {i+1}: {e}")
    
    # Шаг 3: Добавляем 50+ промежуточных сообщений
    print(f"\n🔄 Шаг 3: Добавление 50+ промежуточных сообщений")
    print("(Это должно ПОЛНОСТЬЮ вытеснить краткосрочную память)")
    
    filler_messages = [
        "Привет", "Как дела?", "Что делаешь?", "Какая погода?", "Как настроение?",
        "Что планируешь?", "Как прошел день?", "Что нового?", "Как здоровье?", "Планы на вечер?",
        "Смотрел фильмы?", "Что читаешь?", "Как работа?", "Что едим?", "Как выходные?",
        "Планы на отпуск?", "Что покупаешь?", "Как семья?", "Что слушаешь?", "Где гуляешь?",
        "Как учеба?", "Что готовишь?", "Как спорт?", "Что играешь?", "Как транспорт?",
        "Что смотришь?", "Как погода?", "Что пьешь?", "Как сон?", "Что покупать?",
        "Как дорога?", "Что делать?", "Как время?", "Что есть?", "Как дела дома?",
        "Что интересного?", "Как проекты?", "Что нового в мире?", "Как технологии?", "Что модно?",
        "Как друзья?", "Что в планах?", "Как бизнес?", "Что изучаешь?", "Как отдых?",
        "Что покупал?", "Как поездка?", "Что готовил?", "Как встреча?", "Что планируешь завтра?",
        "Как прошла неделя?", "Что будешь делать?", "Как настроение сегодня?", "Что интересного случилось?", "Как планы на месяц?"
    ]
    
    for i, message in enumerate(filler_messages):
        try:
            memory_data = {
                'role': 'user',
                'content': message,
                'metadata': {
                    'source': 'filler_overload',
                    'user_id': user_id,
                    'timestamp': f'2025-09-02T{10 + i//60}:{(i%60):02d}:00Z',
                    'importance': 'low',
                    'category': 'casual'
                },
                'conversation_id': f'filler_overload_{user_id}',
                'day_number': 1
            }
            
            response = requests.post(
                f"http://localhost:8000/api/memory/{user_id}/add",
                json=memory_data,
                timeout=15
            )
            
            if response.status_code == 200 and i % 10 == 0:
                print(f"   ✅ Добавлено {i+1} промежуточных сообщений...")
            elif response.status_code != 200:
                print(f"   ❌ Сообщение {i+1}: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Сообщение {i+1}: {e}")
    
    print(f"   ✅ Всего добавлено: {len(filler_messages)} промежуточных сообщений")
    print(f"   📊 Общее количество сообщений: {len(important_facts) + len(filler_messages)}")
    
    # Шаг 4: Ждем индексации
    print(f"\n⏳ Шаг 4: Ждем индексации векторной БД (15 секунд)")
    time.sleep(15)
    
    # Шаг 5: Проверяем прямой поиск в векторной БД
    print(f"\n🔍 Шаг 5: ПРЯМОЙ поиск в векторной БД")
    try:
        search_data = {
            'query': 'Глеб Уховский Senior Python Developer машинное обучение пауэрлифтинг шахматы японский',
            'max_results': 15,
            'levels': ['long_term']
        }
        
        response = requests.post(
            f"http://localhost:8000/api/memory/{user_id}/search",
            json=search_data,
            timeout=20
        )
        
        if response.status_code == 200:
            result = response.json()
            found_count = result.get('total_found', 0)
            print(f"   ✅ Найдено в векторной БД: {found_count} результатов")
            
            if found_count > 0:
                results = result.get('results', [])
                important_found = 0
                for i, item in enumerate(results[:10]):
                    content = item.get('content', '')
                    score = item.get('relevance_score', 0)
                    print(f"      {i+1}. {content[:80]}... (score: {score:.3f})")
                    
                    # Проверяем важные факты
                    if any(keyword in content.lower() for keyword in 
                          ["уховский", "senior", "python", "машинн", "пауэрлифтинг", "шахмат", "японск"]):
                        important_found += 1
                
                print(f"   📊 Важных фактов в векторной БД: {important_found}")
                
                if important_found >= 4:
                    print(f"   ✅ ВЕКТОРНАЯ БД содержит важные факты")
                else:
                    print(f"   ❌ ВЕКТОРНАЯ БД потеряла важные факты")
        else:
            print(f"   ❌ Ошибка поиска в векторной БД: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
    
    # Шаг 6: КРИТИЧЕСКИЙ ТЕСТ - вопрос через ИИ
    print(f"\n🤖 Шаг 6: КРИТИЧЕСКИЙ ТЕСТ - ИИ должен использовать ТОЛЬКО векторную БД")
    print("(Краткосрочная память должна быть полностью вытеснена)")
    
    try:
        chat_data = {
            'user_id': user_id,
            'messages': [{'role': 'user', 'content': 'Расскажи подробно: как меня зовут, кем работаю, чем увлекаюсь, какие у меня хобби?'}],
            'metaTime': "2025-09-03T18:00:00Z"
        }
        
        print("   ❓ ВОПРОС: 'Расскажи подробно: как меня зовут, кем работаю, чем увлекаюсь, какие у меня хобби?'")
        
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
                print(f"\n   🤖 ОТВЕТ ИИ (должен использовать ВЕКТОРНУЮ БД):")
                print(f"   {ai_response}")
                
                # ДЕТАЛЬНАЯ проверка векторной памяти
                vector_memory_checks = {
                    "полное_имя": ["уховский", "глеб уховский"],
                    "должность": ["senior", "senior python"],
                    "специализация": ["computer vision", "pytorch", "tensorflow"],
                    "спорт": ["пауэрлифтинг", "4 раза в неделю"],
                    "хобби": ["шахмат", "1800", "elo"],
                    "языки": ["японск", "токио"],
                    "книги": ["трансформер", "ai/ml"]
                }
                
                found_details = []
                for category, keywords in vector_memory_checks.items():
                    if any(keyword.lower() in ai_response.lower() for keyword in keywords):
                        found_details.append(category)
                
                print(f"\n   📊 АНАЛИЗ ВЕКТОРНОЙ ПАМЯТИ:")
                print(f"   ✅ НАЙДЕННЫЕ ДЕТАЛИ: {', '.join(found_details)}")
                print(f"   📈 ИСПОЛЬЗОВАНИЕ ВЕКТОРНОЙ БД: {len(found_details)}/{len(vector_memory_checks)} категорий")
                
                # Определяем источник памяти
                if len(found_details) >= 5:
                    print(f"   🎉 УСПЕХ! ИИ ИСПОЛЬЗУЕТ ВЕКТОРНУЮ БАЗУ ДАННЫХ")
                    print(f"   ✅ Детальная информация доступна через векторный поиск")
                    print(f"   ✅ Краткосрочная память вытеснена, работает долгосрочная")
                elif len(found_details) >= 2:
                    print(f"   ⚠️ ЧАСТИЧНЫЙ УСПЕХ: Векторная БД работает частично")
                    print(f"   🔧 Некоторые детали потеряны или не найдены")
                else:
                    print(f"   ❌ ПРОВАЛ: ИИ НЕ использует векторную базу данных")
                    print(f"   🔧 Система не находит информацию из долгосрочной памяти")
                    
                # Проверяем, не использует ли краткосрочную память
                recent_words = ["привет", "как дела", "что делаешь", "планируешь"]
                uses_recent = any(word in ai_response.lower() for word in recent_words)
                
                if uses_recent:
                    print(f"   ⚠️ ВНИМАНИЕ: ИИ упоминает недавние сообщения")
                    print(f"   🔧 Возможно, краткосрочная память еще активна")
                else:
                    print(f"   ✅ ИИ НЕ упоминает недавние промежуточные сообщения")
                    print(f"   ✅ Фокус только на важных фактах из векторной БД")
                    
            else:
                print("   ❌ Нет ответа от ИИ")
        else:
            print(f"   ❌ Ошибка API: {response.status_code}")
            print(f"   Ответ: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
    
    print(f"\n" + "=" * 60)
    
    if len(found_details) >= 5:
        print("🎉 ВЕКТОРНАЯ БАЗА ДАННЫХ РАБОТАЕТ ИДЕАЛЬНО!")
        print("✅ Система использует долгосрочную память через векторный поиск")
        print("✅ Краткосрочная память корректно вытеснена")
        print("✅ Детальная информация сохраняется и извлекается")
    elif len(found_details) >= 2:
        print("⚠️ ВЕКТОРНАЯ БД РАБОТАЕТ, НО НЕ ИДЕАЛЬНО")
        print("🔧 Некоторые детали теряются или не находятся")
        print("🔧 Нужна оптимизация поиска или индексации")
    else:
        print("❌ КРИТИЧЕСКАЯ ПРОБЛЕМА С ВЕКТОРНОЙ БАЗОЙ")
        print("🔧 Система НЕ использует долгосрочную память")
        print("🔧 Требуется серьезная диагностика архитектуры")

if __name__ == "__main__":
    test_real_vector_memory()
