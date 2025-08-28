#!/usr/bin/env python3
"""
Тест новой векторной памяти с pgvector
"""
import asyncio
import requests
import json
from datetime import datetime

def test_vector_memory():
    """Тестируем новую векторную память"""
    print('🧠 ТЕСТ ВЕКТОРНОЙ ПАМЯТИ (pgvector)')
    print('=' * 60)
    
    base_url = 'http://localhost:8000'
    
    # Тест 1: Первое сообщение - знакомство
    print('\n🧪 Тест 1: Знакомство с пользователем')
    response1 = requests.post(f'{base_url}/api/chat', json={
        'user_id': 'vector_memory_test',
        'messages': [
            {'role': 'user', 'content': 'Привет! Меня зовут Виктор, мне 35 лет. Я работаю инженером в IT компании в Санкт-Петербурге. Люблю программировать, читать научную фантастику и играть в шахматы.'}
        ],
        'metaTime': '2024-01-15T18:00:00Z'
    })
    
    if response1.status_code == 200:
        data1 = response1.json()
        print(f'✅ Первое сообщение обработано')
        print(f'📝 Ответ: {data1["parts"][0][:150]}...')
        print(f'📊 Частей: {len(data1["parts"])}')
        first_response = data1['parts']
    else:
        print(f'❌ Ошибка первого сообщения: {response1.status_code}')
        return
    
    # Тест 2: Второе сообщение - проверка памяти
    print('\n🧪 Тест 2: Проверка памяти - помнит ли имя и профессию')
    response2 = requests.post(f'{base_url}/api/chat', json={
        'user_id': 'vector_memory_test',
        'messages': [
            {'role': 'user', 'content': 'Привет! Меня зовут Виктор, мне 35 лет. Я работаю инженером в IT компании в Санкт-Петербурге. Люблю программировать, читать научную фантастику и играть в шахматы.'},
            {'role': 'assistant', 'content': ' '.join(first_response)},
            {'role': 'user', 'content': 'Помнишь ли ты мое имя и где я работаю?'}
        ],
        'metaTime': '2024-01-15T18:05:00Z'
    })
    
    if response2.status_code == 200:
        data2 = response2.json()
        print(f'✅ Второе сообщение обработано')
        print(f'📝 Ответ: {data2["parts"][0][:200]}...')
        print(f'🔍 Использует ли память: {"Да" if ("Виктор" in data2["parts"][0] or "виктор" in data2["parts"][0].lower()) and ("инженер" in data2["parts"][0].lower() or "IT" in data2["parts"][0]) else "Нет"}')
        second_response = data2['parts']
    else:
        print(f'❌ Ошибка второго сообщения: {response2.status_code}')
        return
    
    # Тест 3: Третье сообщение - проверка увлечений
    print('\n🧪 Тест 3: Проверка памяти увлечений')
    response3 = requests.post(f'{base_url}/api/chat', json={
        'user_id': 'vector_memory_test',
        'messages': [
            {'role': 'user', 'content': 'Привет! Меня зовут Виктор, мне 35 лет. Я работаю инженером в IT компании в Санкт-Петербурге. Люблю программировать, читать научную фантастику и играть в шахматы.'},
            {'role': 'assistant', 'content': ' '.join(first_response)},
            {'role': 'user', 'content': 'Помнишь ли ты мое имя и где я работаю?'},
            {'role': 'assistant', 'content': ' '.join(second_response)},
            {'role': 'user', 'content': 'Какие у меня увлечения? Помнишь ли ты что я люблю делать?'}
        ],
        'metaTime': '2024-01-15T18:10:00Z'
    })
    
    if response3.status_code == 200:
        data3 = response3.json()
        print(f'✅ Третье сообщение обработано')
        print(f'📝 Ответ: {data3["parts"][0][:200]}...')
        print(f'🔍 Помнит увлечения: {"Да" if any(word in data3["parts"][0].lower() for word in ["программировать", "читать", "шахматы", "фантастик"]) else "Нет"}')
        third_response = data3['parts']
    else:
        print(f'❌ Ошибка третьего сообщения: {response3.status_code}')
        return
    
    # Тест 4: Четвертое сообщение - проверка деталей
    print('\n🧪 Тест 4: Проверка деталей - возраст и город')
    response4 = requests.post(f'{base_url}/api/chat', json={
        'user_id': 'vector_memory_test',
        'messages': [
            {'role': 'user', 'content': 'Привет! Меня зовут Виктор, мне 35 лет. Я работаю инженером в IT компании в Санкт-Петербурге. Люблю программировать, читать научную фантастику и играть в шахматы.'},
            {'role': 'assistant', 'content': ' '.join(first_response)},
            {'role': 'user', 'content': 'Помнишь ли ты мое имя и где я работаю?'},
            {'role': 'assistant', 'content': ' '.join(second_response)},
            {'role': 'user', 'content': 'Какие у меня увлечения? Помнишь ли ты что я люблю делать?'},
            {'role': 'assistant', 'content': ' '.join(third_response)},
            {'role': 'user', 'content': 'Сколько мне лет и в каком городе я живу?'}
        ],
        'metaTime': '2024-01-15T18:15:00Z'
    })
    
    if response4.status_code == 200:
        data4 = response4.json()
        print(f'✅ Четвертое сообщение обработано')
        print(f'📝 Ответ: {data4["parts"][0][:200]}...')
        print(f'🔍 Помнит возраст и город: {"Да" if ("35" in data4["parts"][0] or "тридцать пять" in data4["parts"][0].lower()) and ("петербург" in data4["parts"][0].lower() or "спб" in data4["parts"][0].lower()) else "Нет"}')
    else:
        print(f'❌ Ошибка четвертого сообщения: {response4.status_code}')
    
    # Тест 5: Пятое сообщение - проверка контекста
    print('\n🧪 Тест 5: Проверка общего контекста')
    response5 = requests.post(f'{base_url}/api/chat', json={
        'user_id': 'vector_memory_test',
        'messages': [
            {'role': 'user', 'content': 'Привет! Меня зовут Виктор, мне 35 лет. Я работаю инженером в IT компании в Санкт-Петербурге. Люблю программировать, читать научную фантастику и играть в шахматы.'},
            {'role': 'assistant', 'content': ' '.join(first_response)},
            {'role': 'user', 'content': 'Помнишь ли ты мое имя и где я работаю?'},
            {'role': 'assistant', 'content': ' '.join(second_response)},
            {'role': 'user', 'content': 'Какие у меня увлечения? Помнишь ли ты что я люблю делать?'},
            {'role': 'assistant', 'content': ' '.join(third_response)},
            {'role': 'user', 'content': 'Сколько мне лет и в каком городе я живу?'},
            {'role': 'assistant', 'content': ' '.join(data4["parts"])},
            {'role': 'user', 'content': 'Расскажи мне о себе - что ты знаешь обо мне?'}
        ],
        'metaTime': '2024-01-15T18:20:00Z'
    })
    
    if response5.status_code == 200:
        data5 = response5.json()
        print(f'✅ Пятое сообщение обработано')
        print(f'📝 Ответ: {data5["parts"][0][:300]}...')
        
        # Анализируем качество памяти
        response_text = data5["parts"][0].lower()
        memory_score = 0
        
        if "виктор" in response_text: memory_score += 1
        if "35" in response_text or "тридцать пять" in response_text: memory_score += 1
        if "инженер" in response_text: memory_score += 1
        if "петербург" in response_text or "спб" in response_text: memory_score += 1
        if any(word in response_text for word in ["программировать", "читать", "шахматы", "фантастик"]): memory_score += 1
        
        print(f'📊 Качество памяти: {memory_score}/5 ({memory_score*20}%)')
    else:
        print(f'❌ Ошибка пятого сообщения: {response5.status_code}')
    
    print('\n🎉 ТЕСТ ВЕКТОРНОЙ ПАМЯТИ ЗАВЕРШЕН!')
    print('=' * 60)

if __name__ == "__main__":
    test_vector_memory() 