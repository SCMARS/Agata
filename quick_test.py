#!/usr/bin/env python3
"""
Быстрое сравнение обычного и тихого режимов
"""

import os
import subprocess
import time

def test_mode(mode_name, quiet_flag):
    print(f"\n{'='*50}")
    print(f"🧪 {mode_name}")
    print('='*50)

    # Устанавливаем переменную окружения
    env = os.environ.copy()
    if quiet_flag:
        env['AGATHA_QUIET'] = 'true'

    try:
        # Запускаем сервер в фоне
        server_process = subprocess.Popen([
            'python', 'run_server.py'
        ], env=env, cwd='/Users/glebuhovskij/Desktop/Agata',
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        # Ждем запуска
        time.sleep(6)

        # Делаем тестовый запрос
        result = subprocess.run([
            'curl', '-s', '-X', 'POST', 'http://localhost:8000/api/chat',
            '-H', 'Content-Type: application/json',
            '-d', '{"user_id": "test", "messages": [{"role": "user", "content": "Привет"}], "metaTime": "2024-01-15T14:30:00Z"}'
        ], capture_output=True, text=True, cwd='/Users/glebuhovskij/Desktop/Agata')

        # Останавливаем сервер
        server_process.terminate()
        server_process.wait(timeout=3)

        # Анализируем вывод
        lines = result.stdout.strip().split('\n')
        log_lines = [line for line in lines if any(keyword in line.upper() for keyword in [
            'VECTOR', 'BEHAVIORAL', 'PROMPT', 'LLM', 'PIPELINE', 'START', 'COMPLETED', 'MEMORY', 'EMBEDDING'
        ])]

        if log_lines:
            print(f"📝 ЛОГИ ({len(log_lines)} строк):")
            for line in log_lines[:5]:  # Показываем первые 5
                print(f"  {line}")
            if len(log_lines) > 5:
                print(f"  ... и ещё {len(log_lines) - 5} строк")
        else:
            print("📝 ЛОГИ: Нет отладочных сообщений")

        # Проверяем, есть ли JSON ответ
        json_lines = [line for line in lines if '"delays_ms"' in line or '"has_question"' in line]
        if json_lines:
            print("✅ JSON ответ: Присутствует")
        else:
            print("❌ JSON ответ: Отсутствует")

    except Exception as e:
        print(f"❌ Ошибка: {e}")

def main():
    print("🎭 СРАВНЕНИЕ РЕЖИМОВ AGATHA AI")

    # Обычный режим
    test_mode("ОБЫЧНЫЙ РЕЖИМ", quiet_flag=False)

    # Тихий режим
    test_mode("ТИХИЙ РЕЖИМ", quiet_flag=True)

    print(f"\n{'='*50}")
    print("📊 РЕЗУЛЬТАТ:")
    print("• Обычный режим: Полные логи для разработки")
    print("• Тихий режим: Только результат, без шума")
    print("\n🎯 Для продакшена используйте:")
    print("  export AGATHA_QUIET=true")

if __name__ == "__main__":
    main()
