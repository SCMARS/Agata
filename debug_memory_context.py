#!/usr/bin/env python3

import requests
import json

def debug_memory_context():
    """Отладка контекста памяти"""
    
    print("🔍 ОТЛАДКА КОНТЕКСТА ПАМЯТИ")
    print("=" * 50)
    
    user_id = "1132821710"
    
    # Добавляем тестовые данные
    print("📝 Добавляем тестовые данные...")
    
    test_data = [
        "Я программист Python",
        "Люблю машинное обучение", 
        "Занимаюсь спортом"
    ]
    
    for data in test_data:
        try:
            memory_data = {
                'role': 'user',
                'content': data,
                'metadata': {
                    'source': 'debug_context',
                    'user_id': user_id,
                    'timestamp': '2025-09-02T14:07:00Z'
                },
                'conversation_id': f'debug_{user_id}',
                'day_number': 1
            }
            
            response = requests.post(
                f"http://localhost:8000/api/memory/{user_id}/add",
                json=memory_data,
                timeout=10
            )
            
            if response.status_code == 200:
                print(f"   ✅ {data}")
            else:
                print(f"   ❌ {data}: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ {data}: {e}")
    
    print("\n🤖 Тестируем chat API с детальным логированием...")
    
    try:
        chat_data = {
            'user_id': user_id,
            'messages': [{'role': 'user', 'content': 'Что ты знаешь обо мне?'}],
            'metaTime': "2025-09-02T14:07:00Z"
        }
        
        response = requests.post(
            "http://localhost:8000/api/chat",
            json=chat_data,
            timeout=30
        )
        
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"📄 Полный ответ API:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
            parts = result.get('parts', [])
            if parts:
                ai_response = ' '.join(parts)
                print(f"\n🤖 Ответ ИИ:")
                print(f"   {ai_response}")
                
                # Анализируем ответ
                keywords = ["программист", "Python", "машинное", "обучение", "спорт"]
                found_keywords = [kw for kw in keywords if kw.lower() in ai_response.lower()]
                
                if found_keywords:
                    print(f"\n✅ Найденные ключевые слова: {', '.join(found_keywords)}")
                else:
                    print(f"\n❌ Ключевые слова не найдены")
                    
                if "не знаю" in ai_response.lower() or "нет информации" in ai_response.lower():
                    print("❌ ИИ говорит, что не знает информацию")
                else:
                    print("✅ ИИ не говорит о недостатке информации")
        else:
            print(f"❌ Ошибка: {response.text}")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    
    print(f"\n" + "=" * 50)
    print("Проверьте логи сервера для подробностей о memory_context!")

if __name__ == "__main__":
    debug_memory_context()
