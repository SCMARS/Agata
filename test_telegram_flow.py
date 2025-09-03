#!/usr/bin/env python3

import requests
import time
import json
import os
import sys

# Добавляем путь к проекту
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

API_BASE_URL = "http://localhost:8000"

def test_chat_response():
    """Тестируем полный цикл: сообщение -> память -> ответ от нейросети"""
    
    print("🧪 ТЕСТ ПОЛНОГО ЦИКЛА TELEGRAM БОТА")
    print("=" * 50)
    
    user_id = "test_telegram_user"
    
    # Очищаем память перед тестом
    print("🧹 Очищаем память...")
    try:
        response = requests.post(f"{API_BASE_URL}/api/memory/{user_id}/clear", timeout=10)
        if response.status_code == 200:
            print("✅ Память очищена")
        else:
            print(f"⚠️ Проблема с очисткой: {response.status_code}")
    except Exception as e:
        print(f"❌ Ошибка очистки: {e}")
    
    # Тест 1: Добавляем информацию о пользователе
    print("\n📝 Тест 1: Добавление информации о пользователе")
    
    test_message = "Привет! Меня зовут Глеб и я разработчик."
    
    try:
        # Добавляем в память
        memory_data = {
            'role': 'user',
            'content': test_message,
            'metadata': {
                'source': 'telegram_test',
                'user_id': user_id,
                'timestamp': '2025-09-02T14:07:00Z'
            },
            'conversation_id': f'test_{user_id}',
            'day_number': 1
        }
        
        print(f"💬 Сообщение: {test_message}")
        
        response = requests.post(
            f"{API_BASE_URL}/api/memory/{user_id}/add",
            json=memory_data,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            memory_result = result.get('result', {})
            print(f"✅ Память: Short-term: {'✅' if memory_result.get('short_term') else '❌'}, Long-term: {'✅' if memory_result.get('long_term') else '❌'}")
        else:
            print(f"❌ Ошибка добавления в память: {response.status_code}")
            return
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return
    
    # Тест 2: Получаем ответ от нейросети
    print("\n🤖 Тест 2: Получение ответа от нейросети")
    
    try:
        chat_data = {
            'user_id': user_id,
            'messages': [{'role': 'user', 'content': test_message}],
            'metaTime': "2025-09-02T14:07:00Z"
        }
        
        print("🔄 Отправляем запрос к /api/chat...")
        
        chat_response = requests.post(
            f"{API_BASE_URL}/api/chat",
            json=chat_data,
            timeout=30
        )
        
        if chat_response.status_code == 200:
            chat_result = chat_response.json()
            parts = chat_result.get('parts', [])
            
            if parts:
                ai_response = ' '.join(parts)
                print(f"✅ Ответ получен!")
                print(f"🤖 Ответ нейросети: {ai_response[:200]}...")
                
                # Проверяем, что ответ не пустой и осмысленный
                if len(ai_response.strip()) > 10:
                    print("✅ Ответ содержательный")
                else:
                    print("⚠️ Ответ слишком короткий")
                    
            else:
                print("❌ Нет частей в ответе")
                print(f"📄 Полный ответ: {json.dumps(chat_result, indent=2, ensure_ascii=False)}")
        else:
            print(f"❌ Ошибка chat API: {chat_response.status_code}")
            print(f"📄 Ответ: {chat_response.text}")
            
    except Exception as e:
        print(f"❌ Ошибка chat: {e}")
        return
    
    # Тест 3: Проверяем память через несколько сообщений
    print("\n🔄 Тест 3: Проверка памяти после нескольких сообщений")
    
    # Добавляем несколько промежуточных сообщений
    intermediate_messages = [
        "Сегодня хорошая погода",
        "Я изучаю Python",
        "Мне нравится программирование",
        "Работаю над интересным проектом",
        "Использую LangChain и векторные базы данных"
    ]
    
    for i, msg in enumerate(intermediate_messages):
        try:
            memory_data = {
                'role': 'user',
                'content': msg,
                'metadata': {
                    'source': 'telegram_test',
                    'user_id': user_id,
                    'timestamp': '2025-09-02T14:07:00Z'
                },
                'conversation_id': f'test_{user_id}',
                'day_number': 1
            }
            
            response = requests.post(
                f"{API_BASE_URL}/api/memory/{user_id}/add",
                json=memory_data,
                timeout=10
            )
            
            if response.status_code == 200:
                print(f"✅ Сообщение {i+1}: {msg[:30]}...")
            else:
                print(f"❌ Ошибка сообщения {i+1}: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Ошибка сообщения {i+1}: {e}")
    
    # Тест 4: Проверяем, помнит ли система имя
    print("\n🔍 Тест 4: Проверка долгосрочной памяти")
    
    try:
        question = "Как меня зовут?"
        
        chat_data = {
            'user_id': user_id,
            'messages': [{'role': 'user', 'content': question}],
            'metaTime': "2025-09-02T14:07:00Z"
        }
        
        print(f"❓ Вопрос: {question}")
        
        chat_response = requests.post(
            f"{API_BASE_URL}/api/chat",
            json=chat_data,
            timeout=30
        )
        
        if chat_response.status_code == 200:
            chat_result = chat_response.json()
            parts = chat_result.get('parts', [])
            
            if parts:
                ai_response = ' '.join(parts)
                print(f"🤖 Ответ: {ai_response}")
                
                # Проверяем, упоминается ли имя "Глеб"
                if "Глеб" in ai_response or "глеб" in ai_response.lower():
                    print("✅ УСПЕХ: Система помнит имя пользователя!")
                else:
                    print("❌ ПРОБЛЕМА: Система не помнит имя пользователя")
                    
                    # Дополнительная диагностика - поиск в памяти
                    print("\n🔍 Диагностика: Поиск в памяти...")
                    search_data = {
                        'query': 'Глеб имя зовут',
                        'max_results': 5,
                        'levels': ['short_term', 'long_term']
                    }
                    
                    search_response = requests.post(
                        f"{API_BASE_URL}/api/memory/{user_id}/search",
                        json=search_data,
                        timeout=10
                    )
                    
                    if search_response.status_code == 200:
                        search_result = search_response.json()
                        found_count = search_result.get('total_found', 0)
                        print(f"🔍 Найдено результатов в памяти: {found_count}")
                        
                        if found_count > 0:
                            results = search_result.get('results', [])
                            for i, item in enumerate(results[:3]):
                                content = item.get('content', '')
                                print(f"   {i+1}. {content[:100]}...")
                    else:
                        print(f"❌ Ошибка поиска: {search_response.status_code}")
            else:
                print("❌ Нет ответа от нейросети")
        else:
            print(f"❌ Ошибка: {chat_response.status_code}")
            
    except Exception as e:
        print(f"❌ Ошибка финального теста: {e}")
    
    print("\n" + "=" * 50)
    print("🏁 ТЕСТ ЗАВЕРШЕН")

if __name__ == "__main__":
    test_chat_response()
