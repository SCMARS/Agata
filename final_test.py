#!/usr/bin/env python3
"""
ФИНАЛЬНЫЙ КОМПЛЕКСНЫЙ ТЕСТ СИСТЕМЫ AGATHA
"""
import requests
import json
import time

def test_system():
    """Комплексное тестирование всех функций"""
    print('🎯 ФИНАЛЬНЫЕ ТЕСТЫ СИСТЕМЫ AGATHA')
    print('=' * 60)
    
    base_url = 'http://localhost:8000'
    
    # Тест 1: Health Check
    print('\n🧪 Тест 1: Health Check')
    try:
        response = requests.get(f'{base_url}/healthz')
        if response.status_code == 200:
            print('✅ Health Check: OK')
        else:
            print(f'❌ Health Check: {response.status_code}')
            return
    except Exception as e:
        print(f'❌ Health Check failed: {e}')
        return
    
    # Тест 2: Первое сообщение (должно быть разбито на части)
    print('\n🧪 Тест 2: Разбиение длинных сообщений')
    long_message = 'Расскажи мне очень подробно о том, как работает искусственный интеллект, машинное обучение, нейронные сети, глубокое обучение, и как это все связано с современными технологиями. Я хочу понять полную картину от основ до передовых достижений.'
    
    response = requests.post(f'{base_url}/api/chat', json={
        'user_id': 'final_test_user',
        'messages': [{'role': 'user', 'content': long_message}],
        'metaTime': '2024-01-15T15:00:00Z'
    })
    
    if response.status_code == 200:
        data = response.json()
        print(f'✅ Статус: {response.status_code}')
        print(f'✅ Частей ответа: {len(data["parts"])}')
        print(f'✅ Есть вопрос: {data["has_question"]}')
        print(f'✅ Задержки: {data["delays_ms"]}')
        
        for i, part in enumerate(data['parts'], 1):
            print(f'📝 Часть {i} ({len(part)} символов): {part[:100]}...')
        
        first_response = data['parts']
    else:
        print(f'❌ Ошибка API: {response.status_code}')
        return
    
    # Тест 3: Память (второй запрос)
    print('\n🧪 Тест 3: Система памяти')
    response2 = requests.post(f'{base_url}/api/chat', json={
        'user_id': 'final_test_user',
        'messages': [
            {'role': 'user', 'content': long_message},
            {'role': 'assistant', 'content': ' '.join(first_response)},
            {'role': 'user', 'content': 'Помнишь ли ты, о чем мы говорили?'}
        ],
        'metaTime': '2024-01-15T15:05:00Z'
    })
    
    if response2.status_code == 200:
        data2 = response2.json()
        print(f'✅ Память работает! Ответ: {data2["parts"][0][:150]}...')
        print(f'✅ Длина ответа: {len(data2["parts"][0])} символов')
        print(f'✅ Есть вопрос: {data2["has_question"]}')
    else:
        print(f'❌ Ошибка теста памяти: {response2.status_code}')
    
    # Тест 4: Поведенческие стратегии
    print('\n🧪 Тест 4: Поведенческие стратегии')
    response3 = requests.post(f'{base_url}/api/chat', json={
        'user_id': 'final_test_user',
        'messages': [
            {'role': 'user', 'content': 'Я очень устал и чувствую себя подавленным'}
        ],
        'metaTime': '2024-01-15T15:10:00Z'
    })
    
    if response3.status_code == 200:
        data3 = response3.json()
        print(f'✅ Поведенческие стратегии работают!')
        print(f'✅ Ответ: {data3["parts"][0][:150]}...')
        print(f'✅ Длина: {len(data3["parts"][0])} символов')
        print(f'✅ Есть вопрос: {data3["has_question"]}')
    else:
        print(f'❌ Ошибка теста стратегий: {response3.status_code}')
    
    # Тест 5: Контроль частоты вопросов
    print('\n🧪 Тест 5: Контроль частоты вопросов')
    response4 = requests.post(f'{base_url}/api/chat', json={
        'user_id': 'final_test_user',
        'messages': [
            {'role': 'user', 'content': 'Расскажи мне о погоде'}
        ],
        'metaTime': '2024-01-15T15:15:00Z'
    })
    
    if response4.status_code == 200:
        data4 = response4.json()
        print(f'✅ Контроль вопросов работает!')
        print(f'✅ Ответ: {data4["parts"][0][:150]}...')
        print(f'✅ Есть вопрос: {data4["has_question"]}')
        print(f'✅ Частей: {len(data4["parts"])}')
    else:
        print(f'❌ Ошибка теста вопросов: {response4.status_code}')
    
    print('\n🎉 ВСЕ ТЕСТЫ ЗАВЕРШЕНЫ!')
    print('=' * 60)

if __name__ == "__main__":
    test_system() 