#!/usr/bin/env python3
"""
Простой тест - что попадает в промпт и что отвечает модель
"""

import requests
import json
import time
from datetime import datetime

API_BASE_URL = "http://localhost:8000"
TEST_USER = "simple_test"

def main():
    print("🔍 ПРОСТОЙ ТЕСТ - ЧТО В ПРОМПТЕ")
    print("=" * 40)
    
    # Ждем запуска
    print("⏳ Ждем 15 секунд...")
    time.sleep(15)
    
    # Добавляем ОДИН факт
    print("\n📝 Добавляем факт: 'Меня зовут Глеб'")
    memory_data = {
        'role': 'user',
        'content': 'Меня зовут Глеб',
        'metadata': {'source': 'test'},
        'conversation_id': 'test_123',
        'day_number': 1
    }
    
    try:
        response = requests.post(f"{API_BASE_URL}/api/memory/{TEST_USER}/add", json=memory_data, timeout=30)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Сохранено: {result}")
        else:
            print(f"❌ Ошибка: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return
    
    # Ждем сохранения
    print("⏳ Ждем сохранения в векторную БД...")
    time.sleep(10)
    
    # Проверяем поиск
    print("\n🔍 Проверяем поиск в памяти...")
    try:
        search_response = requests.post(
            f"{API_BASE_URL}/api/memory/{TEST_USER}/search",
            json={"query": "имя зовут", "limit": 3},
            timeout=20
        )
        if search_response.status_code == 200:
            search_results = search_response.json()
            print(f"📊 Результаты поиска:")
            print(json.dumps(search_results, indent=2, ensure_ascii=False))
        else:
            print(f"❌ Поиск не работает: {search_response.status_code}")
    except Exception as e:
        print(f"❌ Ошибка поиска: {e}")
    
    # Задаем простой вопрос
    print("\n🤔 Задаем вопрос: 'Как меня зовут?'")
    try:
        chat_data = {
            'user_id': TEST_USER,
            'messages': [{'role': 'user', 'content': 'Как меня зовут?'}],
            'metaTime': datetime.now().isoformat()
        }
        
        chat_response = requests.post(f"{API_BASE_URL}/api/chat", json=chat_data, timeout=30)
        
        if chat_response.status_code == 200:
            chat_result = chat_response.json()
            print(f"📋 ПОЛНЫЙ ОТВЕТ:")
            print(json.dumps(chat_result, indent=2, ensure_ascii=False))
            
            parts = chat_result.get('parts', [])
            if parts:
                ai_response = ' '.join(parts)
                print(f"\n🤖 ОТВЕТ МОДЕЛИ: {ai_response}")
                
                if "глеб" in ai_response.lower():
                    print("✅ МОДЕЛЬ ПОМНИТ ИМЯ!")
                else:
                    print("❌ МОДЕЛЬ НЕ ПОМНИТ ИМЯ!")
            else:
                print("❌ Пустой ответ")
        else:
            print(f"❌ Chat API ошибка: {chat_response.status_code}")
            print(f"Ответ: {chat_response.text}")
    except Exception as e:
        print(f"❌ Ошибка chat: {e}")

if __name__ == "__main__":
    main()
