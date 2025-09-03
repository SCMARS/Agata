#!/usr/bin/env python3

import requests
import json
import time

def test_chat_api():
    """Тестируем chat API с детальным логированием"""
    
    print("🔍 ДИАГНОСТИКА CHAT API")
    print("=" * 40)
    
    user_id = "1132821710"
    message = "привет"
    
    # Сначала очистим память
    print("🧹 Очищаем память...")
    try:
        clear_response = requests.post(f"http://localhost:8000/api/memory/{user_id}/clear", timeout=5)
        print(f"   Очистка памяти: {clear_response.status_code}")
    except Exception as e:
        print(f"   Ошибка очистки: {e}")
    
    # Добавим сообщение в память
    print("\n📝 Добавляем сообщение в память...")
    try:
        memory_data = {
            'role': 'user',
            'content': message,
            'metadata': {
                'source': 'debug_test',
                'user_id': user_id,
                'timestamp': '2025-09-02T14:07:00Z'
            },
            'conversation_id': f'debug_{user_id}',
            'day_number': 1
        }
        
        memory_response = requests.post(
            f"http://localhost:8000/api/memory/{user_id}/add",
            json=memory_data,
            timeout=10
        )
        print(f"   Добавление в память: {memory_response.status_code}")
        if memory_response.status_code == 200:
            result = memory_response.json()
            print(f"   Результат: {result}")
        else:
            print(f"   Ошибка: {memory_response.text}")
    except Exception as e:
        print(f"   Ошибка памяти: {e}")
    
    # Теперь тестируем chat API
    print(f"\n🤖 Тестируем chat API...")
    print(f"   User ID: {user_id}")
    print(f"   Сообщение: {message}")
    
    chat_data = {
        'user_id': user_id,
        'messages': [{'role': 'user', 'content': message}],
        'metaTime': "2025-09-02T14:07:00Z"
    }
    
    print(f"   Данные запроса: {json.dumps(chat_data, ensure_ascii=False)}")
    
    try:
        print("\n⏱️ Отправляем запрос...")
        start_time = time.time()
        
        chat_response = requests.post(
            "http://localhost:8000/api/chat",
            json=chat_data,
            timeout=60,  # Большой таймаут для диагностики
            stream=False
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"📊 Результат:")
        print(f"   Status Code: {chat_response.status_code}")
        print(f"   Время ответа: {duration:.2f} секунд")
        print(f"   Headers: {dict(chat_response.headers)}")
        
        if chat_response.status_code == 200:
            try:
                result = chat_response.json()
                print(f"✅ Успешный ответ:")
                print(f"   Тип ответа: {type(result)}")
                print(f"   Ключи: {list(result.keys()) if isinstance(result, dict) else 'не словарь'}")
                
                if isinstance(result, dict):
                    parts = result.get('parts', [])
                    print(f"   Parts: {len(parts) if parts else 0}")
                    if parts:
                        print(f"   Первая часть: {parts[0][:100]}...")
                    else:
                        print(f"   Полный ответ: {json.dumps(result, ensure_ascii=False, indent=2)}")
                else:
                    print(f"   Ответ: {result}")
                    
            except json.JSONDecodeError as e:
                print(f"❌ Ошибка парсинга JSON: {e}")
                print(f"   Raw ответ: {chat_response.text[:500]}...")
        else:
            print(f"❌ Ошибка API:")
            print(f"   Код: {chat_response.status_code}")
            print(f"   Ответ: {chat_response.text[:500]}...")
            
    except requests.exceptions.Timeout:
        print(f"⏰ Таймаут запроса (больше 60 секунд)")
    except requests.exceptions.ConnectionError as e:
        print(f"🔌 Ошибка подключения: {e}")
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_chat_api()
