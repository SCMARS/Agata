#!/usr/bin/env python3
"""
Тестовый скрипт для красивого отображения ответов Agatha AI
"""

import json
import requests
from datetime import datetime

def format_agatha_response(response_data):
    """Форматирует ответ Agatha для удобного чтения"""
    print("\n🎭 AGATHA AI RESPONSE")
    print("=" * 60)

    # Показываем части с задержками
    parts = response_data.get('parts', [])
    delays = response_data.get('delays_ms', [])

    for i, (part, delay) in enumerate(zip(parts, delays), 1):
        print(f"📝 ЧАСТЬ {i} (задержка: {delay}мс):")
        print(f"   {part}")
        print()

    # Информация о вопросе
    has_question = response_data.get('has_question', False)
    print(f"❓ ВОПРОС: {'ДА' if has_question else 'НЕТ'}")
    print(f"📊 ВСЕГО ЧАСТЕЙ: {len(parts)}")
    print(f"⏱️  ОБЩАЯ ЗАДЕРЖКА: {sum(delays)}мс")

    return response_data

def test_chat_endpoint():
    """Тестирует чат endpoint и показывает красивый ответ"""
    url = "http://localhost:8000/api/chat"

    payload = {
        "user_id": "test_user",
        "messages": [{"role": "user", "content": "Привет! Расскажи о себе"}],
        "metaTime": datetime.now().isoformat()
    }

    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()

        data = response.json()
        format_agatha_response(data)

    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка запроса: {e}")
    except json.JSONDecodeError as e:
        print(f"❌ Ошибка парсинга JSON: {e}")

if __name__ == "__main__":
    print("🧪 ТЕСТИРОВАНИЕ AGATHA AI")
    print("Убедитесь, что сервер запущен на http://localhost:8000")
    print("\nЗапуск теста...")

    test_chat_endpoint()
