#!/usr/bin/env python3
"""
Демонстрация обычного и тихого режимов работы Agatha
"""

import os
import subprocess
import time

def run_with_mode(mode_name, env_vars):
    """Запускаем тест с определенными переменными окружения"""
    print(f"\n{'='*60}")
    print(f"🚀 РЕЖИМ: {mode_name}")
    print('='*60)

    # Устанавливаем переменные окружения
    env = os.environ.copy()
    env.update(env_vars)

    try:
        # Запускаем сервер в фоне
        server_process = subprocess.Popen([
            'python', 'run_server.py'
        ], env=env, cwd=os.path.dirname(os.path.abspath(__file__)),
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        # Ждем запуска сервера
        time.sleep(8)

        # Запускаем тестовый запрос
        test_process = subprocess.run([
            'python', 'test_response.py'
        ], env=env, cwd=os.path.dirname(os.path.abspath(__file__)),
        capture_output=True, text=True, timeout=30)

        print("📝 ВЫВОД СЕРВЕРА:")
        print("-" * 40)
        # Показываем только ключевые строки
        lines = test_process.stdout.split('\n')
        important_lines = [line for line in lines if any(keyword in line.upper() for keyword in [
            'AGATHA', 'ЧАСТЬ', 'ВОПРОС', 'ОШИБКА', 'ERROR', 'START', 'COMPLETED'
        ])]

        if important_lines:
            for line in important_lines[:10]:  # Показываем только первые 10 важных строк
                print(line)
        else:
            print("(Нет важных сообщений - тихий режим)")

        # Останавливаем сервер
        server_process.terminate()
        server_process.wait(timeout=5)

    except subprocess.TimeoutExpired:
        print("⏰ Таймаут выполнения")
    except Exception as e:
        print(f"❌ Ошибка: {e}")

def main():
    print("🎭 ДЕМОНСТРАЦИЯ РЕЖИМОВ AGATHA AI")
    print("Показываем разницу между обычным и тихим режимами")

    # Обычный режим (с логами)
    run_with_mode(
        "ОБЫЧНЫЙ РЕЖИМ (с подробными логами)",
        {'AGATHA_QUIET': 'false'}
    )

    # Тихий режим
    run_with_mode(
        "ТИХИЙ РЕЖИМ (только результат)",
        {'AGATHA_QUIET': 'true'}
    )

    print(f"\n{'='*60}")
    print("📊 СРАВНЕНИЕ:")
    print("• Обычный режим: Полная отладочная информация")
    print("• Тихий режим: Только результат, без шума")
    print()
    print("🎯 ДЛЯ ПРОДАКШЕНА:")
    print("export AGATHA_QUIET=true")
    print("python run_server.py")

if __name__ == "__main__":
    main()
