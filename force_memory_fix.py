#!/usr/bin/env python3

import requests
import json

def force_memory_fix():
    """Принудительное исправление - добавляем информацию прямо в сообщение"""
    
    print("🚨 ПРИНУДИТЕЛЬНОЕ ИСПРАВЛЕНИЕ ПАМЯТИ")
    print("=" * 50)
    
    user_id = "1132821710"
    
    # Создаем сообщение с встроенным контекстом
    context_message = """
Что ты знаешь о моих увлечениях?

КОНТЕКСТ ДЛЯ СПРАВКИ (используй эту информацию в ответе):
- Глеб любит программировать на Python
- Глеб увлекается машинным обучением и ИИ  
- Глеб занимается спортом в спортзале
- Глеб читает книги по технологиям
- Глеб работает разработчиком
"""
    
    print("📝 Отправляем сообщение с встроенным контекстом:")
    print(context_message.strip())
    
    try:
        chat_data = {
            'user_id': user_id,
            'messages': [{'role': 'user', 'content': context_message.strip()}],
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
                print(f"\n🤖 ОТВЕТ ИИ:")
                print(f"{ai_response}")
                
                # Проверяем, использует ли ИИ предоставленную информацию
                keywords = ["программир", "python", "машинн", "ИИ", "спорт", "технолог", "разработ"]
                found = [kw for kw in keywords if kw.lower() in ai_response.lower()]
                
                print(f"\n📊 АНАЛИЗ:")
                if found:
                    print(f"✅ ИСПОЛЬЗУЕТ ИНФОРМАЦИЮ: {', '.join(found)}")
                    if len(found) >= 3:
                        print(f"🎉 УСПЕХ! ИИ МОЖЕТ использовать предоставленную информацию")
                    else:
                        print(f"⚠️ Частичное использование")
                else:
                    print(f"❌ НЕ ИСПОЛЬЗУЕТ предоставленную информацию")
                    
                if "не знаю" in ai_response.lower() or "нет информации" in ai_response.lower():
                    print(f"❌ ВСЕ ЕЩЕ говорит 'не знаю'")
                else:
                    print(f"✅ НЕ говорит 'не знаю'")
            else:
                print("❌ Нет ответа")
        else:
            print(f"❌ Ошибка: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    
    print(f"\n" + "=" * 50)
    print("Если ИИ использует встроенную информацию, проблема в системе памяти.")
    print("Если не использует - проблема в самом ИИ или промпте.")

if __name__ == "__main__":
    force_memory_fix()
