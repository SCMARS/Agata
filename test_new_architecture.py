#!/usr/bin/env python3

import requests
import time

def test_new_architecture():
    """Тест новой унифицированной архитектуры памяти"""
    
    print("🚀 ТЕСТ НОВОЙ АРХИТЕКТУРЫ ПАМЯТИ")
    print("=" * 60)
    
    user_id = "1132821710"
    
    # Шаг 1: Очистка
    print("🧹 Шаг 1: Полная очистка памяти")
    try:
        response = requests.post(f"http://localhost:8000/api/memory/{user_id}/clear", timeout=10)
        print(f"   Очистка: {response.status_code}")
    except Exception as e:
        print(f"   Ошибка: {e}")
    
    # Шаг 2: Добавляем факты постепенно (тестируем переход short → vector)
    print("\n📝 Шаг 2: Добавление фактов с тестированием переходов")
    
    facts = [
        # Сообщения 1-5: Должны быть в краткосрочной памяти
        "Меня зовут Глеб Уховский",
        "Мне 28 лет, родился в Москве", 
        "Работаю Senior Python Developer",
        "Увлекаюсь машинным обучением",
        "Хожу в спортзал каждый день",
        
        # Сообщения 6-10: Все еще в краткосрочной памяти
        "Играю в шахматы, рейтинг 1800",
        "Изучаю японский язык",
        "Планирую поездку в Токио",
        "Читаю книги по нейронным сетям",
        "Работаю с PyTorch и TensorFlow",
        
        # Сообщения 11-15: Должны вытеснить первые 5 в векторную БД
        "Занимаюсь пауэрлифтингом",
        "Люблю слушать джаз",
        "Готовлю итальянскую кухню",
        "Изучаю архитектуру микросервисов",
        "Мечтаю о собственном стартапе"
    ]
    
    for i, fact in enumerate(facts):
        try:
            chat_data = {
                'user_id': user_id,
                'messages': [{'role': 'user', 'content': fact}],
                'metaTime': f"2025-09-03T20:{i:02d}:00Z"
            }
            
            response = requests.post(
                "http://localhost:8000/api/chat",
                json=chat_data,
                timeout=30
            )
            
            if response.status_code == 200:
                print(f"   ✅ Сообщение {i+1:2d}: {fact}")
                
                # Тестируем переход после 10 сообщений
                if i == 9:
                    print(f"   🔄 ПЕРЕХОД: Следующее сообщение должно вытеснить первые в векторную БД")
                elif i == 10:
                    print(f"   🗄️ ВЫТЕСНЕНИЕ: Первое сообщение должно быть в векторной БД")
            else:
                print(f"   ❌ Сообщение {i+1}: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Сообщение {i+1}: {e}")
    
    print(f"   📊 Добавлено {len(facts)} сообщений")
    print(f"   💡 Ожидаемое состояние:")
    print(f"      - В краткосрочной памяти: сообщения 6-15 (10 шт)")
    print(f"      - В векторной БД: сообщения 1-5 (5 шт)")
    
    # Шаг 3: Ждем индексации
    print(f"\n⏳ Шаг 3: Ждем индексации векторной БД (10 секунд)")
    time.sleep(10)
    
    # Шаг 4: Тестируем поиск СТАРЫХ данных (должны быть в векторной БД)
    print(f"\n🔍 Шаг 4: Тест поиска СТАРЫХ данных (векторная БД)")
    
    old_data_tests = [
        ("Как меня зовут полностью?", ["Глеб Уховский"]),
        ("Сколько мне лет?", ["28 лет", "москва", "родился"]),
        ("Какая у меня должность?", ["Senior Python Developer"])
    ]
    
    for question, expected_keywords in old_data_tests:
        try:
            chat_data = {
                'user_id': user_id,
                'messages': [{'role': 'user', 'content': question}],
                'metaTime': "2025-09-03T21:00:00Z"
            }
            
            response = requests.post(
                "http://localhost:8000/api/chat",
                json=chat_data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                parts = result.get('parts', [])
                ai_response = ' '.join(parts) if parts else ""
                
                found_keywords = []
                for keyword in expected_keywords:
                    if keyword.lower() in ai_response.lower():
                        found_keywords.append(keyword)
                
                print(f"   ❓ {question}")
                print(f"   🤖 {ai_response[:100]}...")
                
                if found_keywords:
                    print(f"   ✅ НАЙДЕНО из векторной БД: {', '.join(found_keywords)}")
                else:
                    print(f"   ❌ НЕ НАЙДЕНО из векторной БД: {', '.join(expected_keywords)}")
                    
            else:
                print(f"   ❌ Ошибка: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Ошибка: {e}")
    
    # Шаг 5: Тестируем поиск НОВЫХ данных (должны быть в краткосрочной памяти)
    print(f"\n🔍 Шаг 5: Тест поиска НОВЫХ данных (краткосрочная память)")
    
    new_data_tests = [
        ("Что я планирую с бизнесом?", ["стартап", "мечтаю"]),
        ("Какую кухню я готовлю?", ["итальянскую"]),
        ("Какую музыку слушаю?", ["джаз"])
    ]
    
    for question, expected_keywords in new_data_tests:
        try:
            chat_data = {
                'user_id': user_id,
                'messages': [{'role': 'user', 'content': question}],
                'metaTime': "2025-09-03T21:05:00Z"
            }
            
            response = requests.post(
                "http://localhost:8000/api/chat",
                json=chat_data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                parts = result.get('parts', [])
                ai_response = ' '.join(parts) if parts else ""
                
                found_keywords = []
                for keyword in expected_keywords:
                    if keyword.lower() in ai_response.lower():
                        found_keywords.append(keyword)
                
                print(f"   ❓ {question}")
                print(f"   🤖 {ai_response[:100]}...")
                
                if found_keywords:
                    print(f"   ✅ НАЙДЕНО из краткосрочной памяти: {', '.join(found_keywords)}")
                else:
                    print(f"   ❌ НЕ НАЙДЕНО из краткосрочной памяти: {', '.join(expected_keywords)}")
                    
            else:
                print(f"   ❌ Ошибка: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Ошибка: {e}")
    
    # Шаг 6: Финальный комбинированный тест
    print(f"\n🎯 Шаг 6: ФИНАЛЬНЫЙ ТЕСТ - комбинированный запрос")
    
    try:
        chat_data = {
            'user_id': user_id,
            'messages': [{'role': 'user', 'content': 'Расскажи все что знаешь обо мне: имя, возраст, работа, увлечения, планы'}],
            'metaTime': "2025-09-03T21:10:00Z"
        }
        
        response = requests.post(
            "http://localhost:8000/api/chat",
            json=chat_data,
            timeout=45
        )
        
        if response.status_code == 200:
            result = response.json()
            parts = result.get('parts', [])
            ai_response = ' '.join(parts) if parts else ""
            
            print(f"   🤖 ПОЛНЫЙ ОТВЕТ:")
            print(f"   {ai_response}")
            
            # Анализ использования обеих систем памяти
            old_data_found = 0
            new_data_found = 0
            
            # Старые данные (должны быть из векторной БД)
            old_checks = ["уховский", "28", "senior", "python"]
            for check in old_checks:
                if check.lower() in ai_response.lower():
                    old_data_found += 1
            
            # Новые данные (должны быть из краткосрочной памяти)
            new_checks = ["стартап", "джаз", "итальянск", "пауэрлифтинг"]
            for check in new_checks:
                if check.lower() in ai_response.lower():
                    new_data_found += 1
            
            print(f"\n   📊 АНАЛИЗ НОВОЙ АРХИТЕКТУРЫ:")
            print(f"   📚 Векторная БД (старые данные): {old_data_found}/4")
            print(f"   💭 Краткосрочная память (новые данные): {new_data_found}/4")
            print(f"   🔄 Общее использование памяти: {old_data_found + new_data_found}/8")
            
            if old_data_found >= 3 and new_data_found >= 2:
                print(f"   🎉 УСПЕХ! Новая архитектура работает")
                print(f"   ✅ Система использует ОБЕ системы памяти корректно")
            elif old_data_found >= 2 or new_data_found >= 2:
                print(f"   ⚠️ ЧАСТИЧНЫЙ УСПЕХ")
                print(f"   🔧 Одна из систем памяти работает не полностью")
            else:
                print(f"   ❌ ПРОВАЛ: Новая архитектура НЕ работает")
                print(f"   🔧 Обе системы памяти не функционируют")
                
        else:
            print(f"   ❌ Ошибка финального теста: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Ошибка финального теста: {e}")
    
    print(f"\n" + "=" * 60)
    
    total_success = old_data_found + new_data_found
    if total_success >= 6:
        print("🎉 НОВАЯ АРХИТЕКТУРА РАБОТАЕТ ОТЛИЧНО!")
        print("✅ UnifiedMemoryManager корректно управляет переходами")
        print("✅ Краткосрочная и долгосрочная память работают совместно")
    elif total_success >= 4:
        print("⚠️ НОВАЯ АРХИТЕКТУРА РАБОТАЕТ ЧАСТИЧНО")
        print("🔧 Нужны небольшие доработки")
    else:
        print("❌ НОВАЯ АРХИТЕКТУРА НЕ РАБОТАЕТ")
        print("🔧 Требуются серьезные исправления")

if __name__ == "__main__":
    test_new_architecture()
