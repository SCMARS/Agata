#!/usr/bin/env python3
"""
🚀 ПОЛНЫЙ ЗАПУСК СИСТЕМЫ AGATHA
===============================
Запускает все компоненты системы:
- API сервер с памятью
- Telegram bot
- Мониторинг системы
"""

import os
import sys
import time
import signal
import subprocess
import requests
from pathlib import Path

# Добавляем корневую директорию в PATH
PROJECT_ROOT = Path(__file__).parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT))

class AgathaLauncher:
    def __init__(self):
        self.processes = []
        self.project_root = PROJECT_ROOT
        self.config_loaded = False
        
    def load_environment(self):
        """Загружает переменные окружения из config.env"""
        config_file = self.project_root / "config.env"
        if not config_file.exists():
            print("❌ Файл config.env не найден!")
            return False
            
        print("📁 Загружаем переменные окружения...")
        with open(config_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key] = value
        
        # Проверяем обязательные переменные
        required_vars = ['OPENAI_API_KEY', 'TELEGRAM_BOT_TOKEN']
        missing_vars = []
        for var in required_vars:
            if not os.environ.get(var):
                missing_vars.append(var)
        
        if missing_vars:
            print(f"❌ Отсутствуют обязательные переменные: {', '.join(missing_vars)}")
            return False
            
        print("✅ Переменные окружения загружены")
        self.config_loaded = True
        return True
    
    def activate_venv(self):
        """Активирует виртуальное окружение"""
        venv_path = self.project_root / "venv"
        if venv_path.exists():
            if sys.platform == "win32":
                activate_script = venv_path / "Scripts" / "activate.bat"
                python_exe = venv_path / "Scripts" / "python.exe"
            else:
                activate_script = venv_path / "bin" / "activate"
                python_exe = venv_path / "bin" / "python"
            
            if python_exe.exists():
                print("🐍 Используем виртуальное окружение")
                return str(python_exe)
        
        print("⚠️ Виртуальное окружение не найдено, используем системный Python")
        return sys.executable
    
    def check_dependencies(self):
        """Проверяет установленные зависимости"""
        try:
            import flask, openai, chromadb, langchain, telegram
            print("✅ Все зависимости установлены")
            return True
        except ImportError as e:
            print(f"❌ Отсутствуют зависимости: {e}")
            print("💡 Установите зависимости: pip install -r requirements.txt")
            return False
    
    def start_api_server(self, python_exe):
        """Запускает API сервер"""
        print("🚀 Запускаем API сервер...")
        
        env = os.environ.copy()
        env['PYTHONPATH'] = str(self.project_root)
        
        process = subprocess.Popen(
            [python_exe, "run_server.py"],
            cwd=str(self.project_root),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            bufsize=1
        )
        
        print(f"   PID: {process.pid}")
        print(f"   Команда: {python_exe} run_server.py")
        
        self.processes.append(('API Server', process))
        
        # Ждем запуска API
        print("⏳ Ждем запуска API сервера...")
        for i in range(30):
            try:
                response = requests.get("http://localhost:8000/healthz", timeout=1)
                if response.status_code == 200:
                    print("✅ API сервер запущен!")
                    return True
            except:
                time.sleep(1)
        
        print("❌ API сервер не запустился")
        return False
    
    def start_telegram_bot(self, python_exe):
        """Запускает Telegram bot"""
        print("🤖 Запускаем Telegram bot...")
        
        env = os.environ.copy()
        env['PYTHONPATH'] = str(self.project_root)
        
        process = subprocess.Popen(
            [python_exe, "telegram_bot.py"],
            cwd=str(self.project_root),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            bufsize=1
        )
        
        print(f"   PID: {process.pid}")
        print(f"   Команда: {python_exe} telegram_bot.py")
        
        self.processes.append(('Telegram Bot', process))
        
        # Ждем запуска бота
        print("⏳ Ждем запуска Telegram bot...")
        time.sleep(3)
        
        if process.poll() is None:
            print("✅ Telegram bot запущен!")
            return True
        else:
            print("❌ Telegram bot не запустился")
            return False
    
    def test_system(self):
        """Тестирует работу системы"""
        print("🧪 Тестируем систему...")
        
        # Тест API
        try:
            print("   Проверяем /api/info...")
            response = requests.get("http://localhost:8000/api/info", timeout=5)
            if response.status_code == 200:
                data = response.json()
                print("✅ API работает")
                print(f"   Endpoints: {len(data.get('endpoints', {}))}")
                print(f"   Версия: {data.get('version')}")
            else:
                print(f"⚠️ API отвечает с кодом {response.status_code}")
                print(f"   Ответ: {response.text[:200]}")
        except Exception as e:
            print(f"❌ API недоступен: {e}")
            # Проверим процессы
            for name, process in self.processes:
                if 'API' in name:
                    if process.poll() is not None:
                        print(f"   💥 Процесс {name} уже завершился с кодом {process.returncode}")
                    else:
                        print(f"   ✅ Процесс {name} еще работает (PID: {process.pid})")
            return False
        
        # Тест памяти
        try:
            test_data = {
                "content": "Тестовое сообщение для проверки памяти",
                "role": "user",
                "conversation_id": "system_test",
                "day_number": 1
            }
            response = requests.post(
                "http://localhost:8000/api/memory/system_test/add",
                json=test_data,
                timeout=5
            )
            if response.status_code == 200:
                print("✅ Система памяти работает")
            else:
                print("⚠️ Проблемы с памятью")
        except Exception as e:
            print(f"⚠️ Память недоступна: {e}")
        
        # Тест чата
        try:
            chat_data = {
                "user_id": "system_test",
                "messages": [{"role": "user", "content": "Привет, это тест системы"}],
                "metaTime": "2025-09-01T18:30:00Z"
            }
            response = requests.post(
                "http://localhost:8000/api/chat",
                json=chat_data,
                timeout=10
            )
            if response.status_code == 200:
                print("✅ Нейросеть отвечает")
            else:
                print("⚠️ Проблемы с нейросетью")
        except Exception as e:
            print(f"⚠️ Нейросеть недоступна: {e}")
        
        return True
    
    def print_status(self):
        """Выводит статус системы"""
        print("\n" + "="*50)
        print("🎉 СИСТЕМА AGATHA ЗАПУЩЕНА!")
        print("="*50)
        
        telegram_token = os.environ.get('TELEGRAM_BOT_TOKEN', '')
        bot_username = telegram_token.split(':')[0] if telegram_token else 'unknown'
        
        print(f"🌐 API сервер: http://localhost:8000")
        print(f"🤖 Telegram bot: https://t.me/{bot_username}")
        print(f"📋 API Info: http://localhost:8000/api/info")
        print(f"💚 Health: http://localhost:8000/healthz")
        
        print("\n📋 Доступные endpoints:")
        print("   • POST /api/chat - чат с Agatha")
        print("   • POST /api/memory/<user_id>/add - добавить в память")
        print("   • POST /api/memory/<user_id>/search - поиск в памяти")
        print("   • GET  /api/memory/<user_id>/overview - обзор памяти")
        print("   • POST /api/memory/<user_id>/clear - очистить память")
        
        print("\n🚀 Активные процессы:")
        for name, process in self.processes:
            status = "✅ Работает" if process.poll() is None else "❌ Остановлен"
            print(f"   • {name}: {status}")
        
        print("\n💡 Используйте Telegram bot для общения с Agatha!")
        print("🛑 Нажмите Ctrl+C для остановки всей системы")
    
    def monitor_processes(self):
        """Мониторит процессы и выводит логи"""
        try:
            print("🔍 Начинаем мониторинг процессов...")
            while True:
                time.sleep(2)
                
                # Проверяем состояние процессов
                for name, process in self.processes:
                    if process.poll() is not None:
                        print(f"💥 ПРОЦЕСС {name} ЗАВЕРШИЛСЯ!")
                        print(f"   Код выхода: {process.returncode}")
                        
                        # Читаем последние логи
                        try:
                            stdout, stderr = process.communicate(timeout=1)
                            if stdout:
                                print(f"   📝 Последние логи stdout:")
                                print(f"   {stdout[-500:]}")  # Последние 500 символов
                            if stderr:
                                print(f"   ❌ Ошибки stderr:")
                                print(f"   {stderr[-500:]}")
                        except:
                            print("   (Не удалось получить логи)")
                        
                        return False
                
                # Проверяем что API отвечает
                try:
                    response = requests.get("http://localhost:8000/healthz", timeout=2)
                    if response.status_code != 200:
                        print(f"⚠️ API отвечает с кодом {response.status_code}")
                except Exception as e:
                    print(f"💥 API НЕ ОТВЕЧАЕТ: {e}")
                    return False
                        
        except KeyboardInterrupt:
            print("\n🛑 Получен сигнал остановки...")
            return True
    
    def cleanup(self):
        """Останавливает все процессы"""
        print("🧹 Останавливаем все процессы...")
        
        for name, process in self.processes:
            if process.poll() is None:
                print(f"   Останавливаем {name}...")
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    print(f"   Принудительно завершаем {name}...")
                    process.kill()
        
        print("✅ Все процессы остановлены")
    
    def run(self):
        """Основной метод запуска"""
        print("🚀 ЗАПУСК СИСТЕМЫ AGATHA")
        print("=" * 40)
        
        # Загружаем окружение
        if not self.load_environment():
            return False
        
        # Получаем Python executable
        python_exe = self.activate_venv()
        
        # Проверяем зависимости
        if not self.check_dependencies():
            return False
        
        try:
            # Запускаем компоненты
            if not self.start_api_server(python_exe):
                return False
            
            if not self.start_telegram_bot(python_exe):
                return False
            
            # Тестируем систему
            self.test_system()
            
            # Выводим статус
            self.print_status()
            
            # Мониторим процессы
            self.monitor_processes()
            
        except Exception as e:
            print(f"❌ Ошибка запуска: {e}")
            return False
        
        finally:
            self.cleanup()
        
        return True

def main():
    """Главная функция"""
    launcher = AgathaLauncher()
    
    # Обработка сигналов
    def signal_handler(signum, frame):
        print("\n🛑 Получен сигнал завершения...")
        launcher.cleanup()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Запускаем систему
    success = launcher.run()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
