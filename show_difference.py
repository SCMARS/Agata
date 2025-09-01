#!/usr/bin/env python3
"""
Показать разницу между обычным и тихим режимами
"""

import os
import subprocess
import time

def run_test(env_var, mode_name):
    """Запускаем тест и показываем результат"""
    print(f"\n🎯 {mode_name}")
    print("=" * 50)

    env = os.environ.copy()
    if env_var:
        env['AGATHA_QUIET'] = 'true'

    try:
        # Запускаем сервер
        server_process = subprocess.Popen([
            'python', 'run_server.py'
        ], env=env, cwd=os.path.dirname(os.path.abspath(__file__)),
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        time.sleep(5)

        # Делаем запрос
        result = subprocess.run([
            'curl', '-s', '-X', 'POST', 'http://localhost:8000/api/chat',
            '-H', 'Content-Type: application/json',
            '-d', '{"user_id": "demo", "messages": [{"role": "user", "content": "Привет"}], "metaTime": "2024-01-15T14:30:00Z"}'
        ], capture_output=True, text=True, cwd=os.path.dirname(os.path.abspath(__file__)))

        # Останавливаем сервер
        server_process.terminate()
        server_process.wait(timeout=3)

        # Анализируем вывод (stdout + stderr)
        all_output = result.stdout + result.stderr
        lines = all_output.split('\n')

        # Считаем логи (строки с эмодзи или ключевыми словами)
        log_indicators = ['🧠', '🎭', '📝', '🤖', '✅', '❌', '🔍', '🚀', 'Pipeline', 'START', 'COMPLETED', 'Behavioral', 'VectorMemory']
        log_lines = [line for line in lines if any(indicator in line for indicator in log_indicators)]

        # Показываем первые 8 строк логов (если есть)
        if log_lines:
            print("📋 ЛОГИ (первые 8 строк):")
            for i, line in enumerate(log_lines[:8], 1):
                # Обрезаем слишком длинные строки
                short_line = line[:80] + "..." if len(line) > 80 else line
                print(f"  {i}. {short_line}")
            if len(log_lines) > 8:
                print(f"  ... и ещё {len(log_lines) - 8} строк")
        else:
            print("📋 ЛОГИ: Отсутствуют")

        print(f"📊 СТАТИСТИКА:")
        print(f"  Всего строк вывода: {len(lines)}")
        print(f"  Строк с логами: {len(log_lines)}")

        # Проверяем JSON ответ
        json_found = any('"delays_ms"' in line and '"has_question"' in line for line in lines)
        print(f"  JSON ответ: {'✅ Найден' if json_found else '❌ Отсутствует'}")

    except Exception as e:
        print(f"❌ Ошибка: {e}")

def main():
    print("🎭 ДЕМОНСТРАЦИЯ РЕЖИМОВ AGATHA AI")
    print("Показываем разницу между обычным и тихим режимами")
    print("В обычном режиме - много отладочных логов")
    print("В тихом режиме - только результат")

    # Обычный режим
    run_test(None, "ОБЫЧНЫЙ РЕЖИМ (полные логи)")

    # Тихий режим
    run_test('true', "ТИХИЙ РЕЖИМ (только результат)")

    print(f"\n{'='*50}")
    print("🎯 ВЫВОД:")
    print("• Тихий режим убирает все отладочные логи")
    print("• Оставляет только HTTP ответ с JSON")
    print("• Идеально для продакшена")
    print()
    print("🚀 ДЛЯ ПРОДАКШЕНА:")
    print("  export AGATHA_QUIET=true")
    print("  python run_server.py")

if __name__ == "__main__":
    main()
