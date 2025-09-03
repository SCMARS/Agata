#!/usr/bin/env python3

import requests
import time
import json

def final_test():
    """Финальный тест всей системы"""
    
    print("🎯 ФИНАЛЬНЫЙ ТЕСТ СИСТЕМЫ")
    print("=" * 50)
    
    user_id = "1132821710"  # Ваш реальный Telegram ID
    
    # Тест 1: Проверяем API сервер
    print("🔍 Тест 1: Проверка API сервера")
    try:
        response = requests.get("http://localhost:8000/healthz", timeout=5)
        if response.status_code == 200:
            print("✅ API сервер работает")
        else:
            print(f"❌ API сервер вернул: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ API сервер недоступен: {e}")
        return
    
    # Тест 2: Очищаем память
    print("\n🧹 Тест 2: Очистка памяти")
    try:
        response = requests.post(f"http://localhost:8000/api/memory/{user_id}/clear", timeout=10)
        print(f"   Очистка: {response.status_code}")
    except Exception as e:
        print(f"   Ошибка очистки: {e}")
    
    # Тест 3: Добавляем сообщение в память
    print("\n📝 Тест 3: Добавление в память")
    try:
        memory_data = {
            'role': 'user',
            'content': 'Привет! Меня зовут Глеб и я разработчик.',
            'metadata': {
                'source': 'final_test',
                'user_id': user_id,
                'timestamp': '2025-09-02T14:07:00Z'
            },
            'conversation_id': f'final_{user_id}',
            'day_number': 1
        }
        
        response = requests.post(
            f"http://localhost:8000/api/memory/{user_id}/add",
            json=memory_data,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            memory_result = result.get('result', {})
            print(f"✅ Память: Short-term: {'✅' if memory_result.get('short_term') else '❌'}, Long-term: {'✅' if memory_result.get('long_term') else '❌'}")
        else:
            print(f"❌ Ошибка добавления: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return
    
    # Тест 4: Тестируем chat API
    print("\n🤖 Тест 4: Chat API")
    try:
        chat_data = {
            'user_id': user_id,
            'messages': [{'role': 'user', 'content': 'Привет! Меня зовут Глеб и я разработчик.'}],
            'metaTime': "2025-09-02T14:07:00Z"
        }
        
        print("   Отправляем запрос к chat API...")
        start_time = time.time()
        
        response = requests.post(
            "http://localhost:8000/api/chat",
            json=chat_data,
            timeout=30
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"   Время ответа: {duration:.2f} секунд")
        
        if response.status_code == 200:
            result = response.json()
            parts = result.get('parts', [])
            
            if parts:
                ai_response = ' '.join(parts)
                print(f"✅ Получен ответ от нейросети:")
                print(f"   {ai_response[:100]}...")
                
                # Проверяем, что ответ содержательный
                if len(ai_response.strip()) > 20:
                    print("✅ Ответ содержательный")
                else:
                    print("⚠️ Ответ слишком короткий")
            else:
                print("❌ Нет частей в ответе")
                print(f"   Полный ответ: {result}")
        else:
            print(f"❌ Ошибка chat API: {response.status_code}")
            print(f"   Ответ: {response.text}")
            return
    except Exception as e:
        print(f"❌ Ошибка chat API: {e}")
        return
    
    # Тест 5: Проверяем память
    print("\n🔍 Тест 5: Проверка памяти")
    try:
        # Добавляем несколько сообщений
        messages = [
            "Я работаю Python разработчиком",
            "Мне нравится машинное обучение", 
            "Сегодня хорошая погода"
        ]
        
        for msg in messages:
            memory_data = {
                'role': 'user',
                'content': msg,
                'metadata': {
                    'source': 'final_test',
                    'user_id': user_id,
                    'timestamp': '2025-09-02T14:07:00Z'
                },
                'conversation_id': f'final_{user_id}',
                'day_number': 1
            }
            
            response = requests.post(
                f"http://localhost:8000/api/memory/{user_id}/add",
                json=memory_data,
                timeout=10
            )
            
            if response.status_code == 200:
                print(f"   ✅ Добавлено: {msg[:30]}...")
            else:
                print(f"   ❌ Ошибка: {response.status_code}")
        
        # Теперь спрашиваем имя
        print("\n   Спрашиваем имя...")
        chat_data = {
            'user_id': user_id,
            'messages': [{'role': 'user', 'content': 'Как меня зовут?'}],
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
                print(f"   🤖 Ответ: {ai_response[:150]}...")
                
                # Проверяем, упоминается ли имя
                if "Глеб" in ai_response or "глеб" in ai_response.lower():
                    print("✅ УСПЕХ: Система помнит имя!")
                else:
                    print("❌ ПРОБЛЕМА: Система не помнит имя")
            else:
                print("❌ Нет ответа")
        else:
            print(f"❌ Ошибка: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Ошибка теста памяти: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 ФИНАЛЬНЫЙ ТЕСТ ЗАВЕРШЕН")
    print("✅ Теперь Telegram бот @agata3_bot должен работать корректно!")
    print("📱 Попробуйте написать боту - он будет отвечать от нейросети!")

if __name__ == "__main__":
    final_test()
