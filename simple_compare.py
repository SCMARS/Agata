#!/usr/bin/env python3
"""
Простое сравнение обычного и тихого режимов
"""

import os
import subprocess
import time

def count_log_lines(output):
    """Подсчитываем количество строк логов"""
    lines = output.split('\n')
    # Считаем строки, которые выглядят как логи (с эмодзи или специальными символами)
    log_indicators = ['🧠', '🎭', '📝', '🤖', '✅', '❌', '🔍', '🔄', '🚀', '📊']
    log_lines = [line for line in lines if any(indicator in line for indicator in log_indicators)]
    return len(log_lines), len(lines)

def test_mode(env_var):
    """Тестируем режим и возвращаем статистику"""
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

        # Делаем запрос и получаем вывод
        result = subprocess.run([
            'curl', '-s', '-X', 'POST', 'http://localhost:8000/api/chat',
            '-H', 'Content-Type: application/json',
            '-d', '{"user_id": "test", "messages": [{"role": "user", "content": "Привет"}], "metaTime": "2024-01-15T14:30:00Z"}'
        ], capture_output=True, text=True, cwd=os.path.dirname(os.path.abspath(__file__)))

        # Останавливаем сервер
        server_process.terminate()
        server_process.wait(timeout=3)

        return count_log_lines(result.stdout)

    except Exception as e:
        return 0, 0

def main():
    print("🎭 ПРОСТОЕ СРАВНЕНИЕ РЕЖИМОВ")
    print("=" * 50)

    # Обычный режим
    normal_logs, normal_total = test_mode(None)
    print(f"📝 ОБЫЧНЫЙ РЕЖИМ:")
    print(f"   Лог-строк: {normal_logs}")
    print(f"   Всего строк: {normal_total}")

    # Тихий режим
    quiet_logs, quiet_total = test_mode('true')
    print(f"\n🤫 ТИХИЙ РЕЖИМ:")
    print(f"   Лог-строк: {quiet_logs}")
    print(f"   Всего строк: {quiet_total}")

    # Разница
    print(f"\n📊 РАЗНИЦА:")
    print(f"   Логов меньше на: {normal_logs - quiet_logs} строк")
    print(f"   Всего строк меньше на: {normal_total - quiet_total} строк")

    if normal_logs > quiet_logs:
        print("✅ Тихий режим работает!")
    else:
        print("⚠️ Разница не обнаружена")

if __name__ == "__main__":
    main()
