#!/usr/bin/env python3
"""
Скрипт для отладки системы памяти
Тестирует сохранение и поиск фактов с LangSmith трейсингом
"""

import os
import sys
import json
import requests
import time
from datetime import datetime

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Настройки
API_BASE_URL = "http://localhost:8000"
TEST_USER_ID = "memory_debug_user"

def test_memory_operations():
    """Тестирует операции с памятью"""
    print("🧪 ТЕСТ СИСТЕМЫ ПАМЯТИ")
    print("=" * 50)
    
    # 1. Очищаем память
    print("\n1️⃣ Очищаем память...")
    try:
        response = requests.post(f"{API_BASE_URL}/api/memory/{TEST_USER_ID}/clear", timeout=10)
        if response.status_code == 200:
            print("✅ Память очищена")
        else:
            print(f"❌ Ошибка очистки: {response.status_code}")
    except Exception as e:
        print(f"❌ Ошибка очистки: {e}")
    
    # 2. Добавляем факт об имени
    print("\n2️⃣ Добавляем факт об имени...")
    name_message = {
        'role': 'user',
        'content': 'Меня зовут Глеб',
        'metadata': {
            'source': 'test',
            'user_id': TEST_USER_ID,
            'timestamp': datetime.now().isoformat(),
            'test': True
        },
        'conversation_id': f'test_{int(datetime.now().timestamp())}',
        'day_number': 1
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/memory/{TEST_USER_ID}/add",
            json=name_message,
            timeout=10
        )
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Факт добавлен: {json.dumps(result.get('result', {}), indent=2, ensure_ascii=False)}")
        else:
            print(f"❌ Ошибка добавления: {response.status_code}")
            print(f"Ответ: {response.text}")
    except Exception as e:
        print(f"❌ Ошибка добавления: {e}")
    
    # 3. Добавляем несколько обычных сообщений
    print("\n3️⃣ Добавляем обычные сообщения...")
    regular_messages = [
        "Привет, как дела?",
        "Что нового?", 
        "Расскажи что-нибудь интересное",
        "Какая сегодня погода?",
        "Что ты думаешь о программировании?",
        "Как твои дела?"
    ]
    
    for i, msg in enumerate(regular_messages, 1):
        print(f"  Добавляем сообщение {i}: {msg}")
        message_data = {
            'role': 'user',
            'content': msg,
            'metadata': {
                'source': 'test',
                'user_id': TEST_USER_ID,
                'timestamp': datetime.now().isoformat(),
                'test': True
            },
            'conversation_id': f'test_{int(datetime.now().timestamp())}',
            'day_number': 1
        }
        
        try:
            response = requests.post(
                f"{API_BASE_URL}/api/memory/{TEST_USER_ID}/add",
                json=message_data,
                timeout=10
            )
            if response.status_code == 200:
                print(f"  ✅ Сообщение {i} добавлено")
            else:
                print(f"  ❌ Ошибка {i}: {response.status_code}")
        except Exception as e:
            print(f"  ❌ Ошибка {i}: {e}")
        
        time.sleep(0.5)  # Пауза между запросами
    
    # 4. Тестируем поиск имени
    print("\n4️⃣ Тестируем поиск имени...")
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/memory/{TEST_USER_ID}/search",
            json={"query": "как меня зовут", "limit": 10},
            timeout=10
        )
        if response.status_code == 200:
            results = response.json()
            print(f"✅ Результаты поиска имени:")
            for result in results.get('results', []):
                print(f"  📝 {result.get('content', '')}")
                print(f"     Релевантность: {result.get('score', 'N/A')}")
        else:
            print(f"❌ Ошибка поиска: {response.status_code}")
    except Exception as e:
        print(f"❌ Ошибка поиска: {e}")
    
    # 5. Тестируем chat API с вопросом об имени
    print("\n5️⃣ Тестируем chat API с вопросом об имени...")
    try:
        chat_data = {
            'user_id': TEST_USER_ID,
            'messages': [{'role': 'user', 'content': 'Как меня зовут?'}],
            'metaTime': datetime.now().isoformat()
        }
        
        response = requests.post(
            f"{API_BASE_URL}/api/chat",
            json=chat_data,
            timeout=30
        )
        
        if response.status_code == 200:
            chat_result = response.json()
            parts = chat_result.get('parts', [])
            if parts:
                ai_response = ' '.join(parts)
                print(f"✅ Ответ AI: {ai_response}")
            else:
                print("❌ Пустой ответ от AI")
                print(f"Полный ответ: {json.dumps(chat_result, indent=2, ensure_ascii=False)}")
        else:
            print(f"❌ Ошибка chat API: {response.status_code}")
            print(f"Ответ: {response.text}")
    except Exception as e:
        print(f"❌ Ошибка chat API: {e}")
    
    # 6. Получаем обзор памяти
    print("\n6️⃣ Получаем обзор памяти...")
    try:
        response = requests.get(f"{API_BASE_URL}/api/memory/{TEST_USER_ID}/overview", timeout=10)
        if response.status_code == 200:
            overview = response.json()
            print(f"✅ Обзор памяти:")
            print(json.dumps(overview, indent=2, ensure_ascii=False))
        else:
            print(f"❌ Ошибка получения обзора: {response.status_code}")
    except Exception as e:
        print(f"❌ Ошибка получения обзора: {e}")

if __name__ == "__main__":
    test_memory_operations()
