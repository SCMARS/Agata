#!/usr/bin/env python3
"""
Быстрый тест новой архитектуры памяти
"""

import requests
import json
import time

API_URL = "http://localhost:8000/api/chat"
USER_ID = "1132821710"

def send_message(content: str) -> dict:
    """Отправляет сообщение и возвращает ответ"""
    payload = {
        "user_id": USER_ID,
        "messages": [{"role": "user", "content": content}],
        "metaTime": "2025-09-03T21:45:00Z"
    }
    
    try:
        response = requests.post(API_URL, json=payload, timeout=30)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ [{content[:30]}...] → {result['parts'][0][:80]}...")
            return result
        else:
            print(f"❌ [{content[:30]}...] → HTTP {response.status_code}: {response.text[:100]}")
            return {"error": f"HTTP {response.status_code}"}
    except Exception as e:
        print(f"❌ [{content[:30]}...] → Ошибка: {e}")
        return {"error": str(e)}

def main():
    print("🚀 БЫСТРЫЙ ТЕСТ НОВОЙ АРХИТЕКТУРЫ ПАМЯТИ")
    print("=" * 60)
    
    # Тест 1: Добавляем базовую информацию
    print("\n📝 Шаг 1: Добавляем базовые факты")
    send_message("Меня зовут Глеб Уховский, мне 28 лет")
    time.sleep(2)
    
    send_message("Я работаю Senior Python разработчиком")
    time.sleep(2)
    
    send_message("Мои хобби: программирование, спорт, путешествия")
    time.sleep(2)
    
    # Тест 2: Добавляем промежуточные сообщения
    print("\n🔄 Шаг 2: Добавляем промежуточные сообщения")
    for i in range(8):
        send_message(f"Промежуточное сообщение {i+1}")
        time.sleep(1)
    
    # Тест 3: Проверяем память
    print("\n🔍 Шаг 3: Проверяем память")
    time.sleep(3)  # Даем время на индексацию
    
    result1 = send_message("Как меня зовут?")
    result2 = send_message("Сколько мне лет?")
    result3 = send_message("Кем я работаю?")
    result4 = send_message("Какие у меня хобби?")
    
    # Анализ результатов
    print("\n📊 АНАЛИЗ РЕЗУЛЬТАТОВ:")
    
    # Проверяем упоминание имени
    if result1 and "parts" in result1:
        response_text = " ".join(result1["parts"]).lower()
        if "глеб" in response_text:
            print("✅ ИИ помнит имя")
        else:
            print("❌ ИИ НЕ помнит имя")
    
    # Проверяем упоминание возраста
    if result2 and "parts" in result2:
        response_text = " ".join(result2["parts"])
        if "28" in response_text:
            print("✅ ИИ помнит возраст")
        else:
            print("❌ ИИ НЕ помнит возраст")
    
    # Проверяем упоминание работы
    if result3 and "parts" in result3:
        response_text = " ".join(result3["parts"]).lower()
        if "python" in response_text or "разработчик" in response_text or "senior" in response_text:
            print("✅ ИИ помнит работу")
        else:
            print("❌ ИИ НЕ помнит работу")
    
    # Проверяем упоминание хобби
    if result4 and "parts" in result4:
        response_text = " ".join(result4["parts"]).lower()
        if any(hobby in response_text for hobby in ["программирование", "спорт", "путешеств"]):
            print("✅ ИИ помнит хобби")
        else:
            print("❌ ИИ НЕ помнит хобби")
    
    print("\n🎯 ТЕСТ ЗАВЕРШЕН")

if __name__ == "__main__":
    main()