#!/usr/bin/env python3
"""
Тест системы памяти - проверяем запоминание и воспроизведение информации
"""
import sys
import os
import asyncio
from datetime import datetime

# Добавляем путь к проекту
sys.path.append('/Users/glebuhovskij/Agata')

from app.graph.pipeline import AgathaPipeline

class MemoryTester:
    def __init__(self):
        self.pipeline = AgathaPipeline()
        self.user_id = "test_user_memory"
        self.conversation_history = []
    
    async def send_message(self, message: str) -> str:
        """Отправить сообщение и получить ответ"""
        print(f"\n👤 Пользователь: {message}")
        
        # Добавляем сообщение пользователя в историю
        user_message = {
            "role": "user",
            "content": message,
            "timestamp": datetime.utcnow().isoformat()
        }
        self.conversation_history.append(user_message)
        
        try:
            # Отправляем в пайплайн
            response = await self.pipeline.process_chat(
                user_id=self.user_id,
                messages=self.conversation_history,
                meta_time=datetime.utcnow().isoformat()
            )
            
            # Извлекаем текст ответа
            if isinstance(response, dict):
                if "parts" in response:
                    response_text = " ".join(response["parts"])
                elif "text" in response:
                    response_text = response["text"]
                elif "content" in response:
                    response_text = response["content"]
                else:
                    response_text = str(response)
            else:
                response_text = str(response)
            
            print(f"🤖 Агата: {response_text}")
            
            # Добавляем ответ ассистента в историю
            assistant_message = {
                "role": "assistant", 
                "content": response_text,
                "timestamp": datetime.utcnow().isoformat()
            }
            self.conversation_history.append(assistant_message)
            
            return response_text
            
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            return f"Ошибка: {e}"
    
    async def test_memory_sequence(self):
        """Тестируем последовательность запоминания и воспроизведения"""
        print("🧠 ТЕСТ СИСТЕМЫ ПАМЯТИ")
        print("=" * 50)
        
        # Этап 1: Знакомство и сбор информации
        print("\n📝 ЭТАП 1: Сбор информации")
        await self.send_message("Привет! Меня зовут Андрей")
        await asyncio.sleep(1)
        
        await self.send_message("Мне 28 лет")
        await asyncio.sleep(1)
        
        await self.send_message("Я программист")
        await asyncio.sleep(1)
        
        await self.send_message("Моя любимая еда - пицца")
        await asyncio.sleep(1)
        
        # Этап 2: Отвлекающие вопросы (3-4 вопроса)
        print("\n🎲 ЭТАП 2: Отвлекающие вопросы")
        await self.send_message("Какая сегодня погода?")
        await asyncio.sleep(1)
        
        await self.send_message("Расскажи мне шутку")
        await asyncio.sleep(1)
        
        await self.send_message("Что ты думаешь о программировании?")
        await asyncio.sleep(1)
        
        await self.send_message("Какие у тебя планы на будущее?")
        await asyncio.sleep(1)
        
        # Этап 3: Проверка памяти
        print("\n🔍 ЭТАП 3: Проверка памяти")
        memory_questions = [
            "Как меня зовут?",
            "Сколько мне лет?", 
            "Кем я работаю?",
            "Какая моя любимая еда?"
        ]
        
        for question in memory_questions:
            print(f"\n🧠 Тестируем память: {question}")
            response = await self.send_message(question)
            await asyncio.sleep(1)
            
            # Анализируем ответ
            self.analyze_memory_response(question, response)
        
        # Этап 4: Дополнительная информация
        print("\n📝 ЭТАП 4: Добавляем новую информацию")
        await self.send_message("Кстати, я живу в Москве")
        await asyncio.sleep(1)
        
        await self.send_message("У меня есть кот по имени Барсик")
        await asyncio.sleep(1)
        
        # Еще отвлекающие вопросы
        await self.send_message("Что такое искусственный интеллект?")
        await asyncio.sleep(1)
        
        await self.send_message("Посоветуй фильм")
        await asyncio.sleep(1)
        
        await self.send_message("Как дела с погодой?")
        await asyncio.sleep(1)
        
        # Этап 5: Финальная проверка памяти
        print("\n🎯 ЭТАП 5: Финальная проверка памяти")
        final_questions = [
            "Напомни мне, как меня зовут?",
            "Где я живу?",
            "Как зовут моего кота?",
            "Что я люблю есть?",
            "Кем я работаю?"
        ]
        
        for question in final_questions:
            print(f"\n🎯 Финальный тест: {question}")
            response = await self.send_message(question)
            await asyncio.sleep(1)
            
            self.analyze_memory_response(question, response)
    
    def analyze_memory_response(self, question: str, response: str):
        """Анализируем ответ на предмет правильного воспроизведения информации"""
        response_lower = response.lower()
        
        if "как" in question.lower() and "зовут" in question.lower():
            if "андрей" in response_lower:
                print("✅ Имя запомнено правильно!")
            else:
                print("❌ Имя не найдено в ответе")
        
        elif "сколько" in question.lower() and "лет" in question.lower():
            if "28" in response_lower:
                print("✅ Возраст запомнен правильно!")
            else:
                print("❌ Возраст не найден в ответе")
        
        elif "работа" in question.lower() or "кем" in question.lower():
            if "программист" in response_lower:
                print("✅ Профессия запомнена правильно!")
            else:
                print("❌ Профессия не найдена в ответе")
        
        elif "еда" in question.lower() or "люблю есть" in question.lower():
            if "пицца" in response_lower:
                print("✅ Любимая еда запомнена правильно!")
            else:
                print("❌ Любимая еда не найдена в ответе")
        
        elif "живу" in question.lower() or "где" in question.lower():
            if "москва" in response_lower or "москве" in response_lower:
                print("✅ Город запомнен правильно!")
            else:
                print("❌ Город не найден в ответе")
        
        elif "кот" in question.lower():
            if "барсик" in response_lower:
                print("✅ Имя кота запомнено правильно!")
            else:
                print("❌ Имя кота не найдено в ответе")
    
    async def debug_memory_state(self):
        """Отладка состояния памяти"""
        print("\n🔧 ОТЛАДКА СОСТОЯНИЯ ПАМЯТИ")
        print("=" * 50)
        
        try:
            memory = self.pipeline._get_memory(self.user_id)
            print(f"Тип памяти: {type(memory)}")
            
            # Проверяем HybridMemory
            if hasattr(memory, 'short_memory'):
                short_memory = memory.short_memory
                print(f"Короткая память: {type(short_memory)}")
                if hasattr(short_memory, 'messages'):
                    print(f"Сообщений в короткой памяти: {len(short_memory.messages)}")
                    for i, msg in enumerate(short_memory.messages[-3:]):
                        print(f"  {i}: {msg.role}: {msg.content[:50]}...")
            
            if hasattr(memory, 'long_memory'):
                long_memory = memory.long_memory
                print(f"Долгая память: {type(long_memory)}")
                
                # Пытаемся получить профиль
                if hasattr(long_memory, 'get_user_profile'):
                    profile = long_memory.get_user_profile()
                    print(f"Профиль пользователя: {profile}")
            
            # Тестируем MemoryAdapter
            from app.memory.memory_adapter import MemoryAdapter
            adapter = MemoryAdapter(memory)
            memory_data = adapter.get_for_prompt(self.user_id, "тест")
            print(f"Данные от MemoryAdapter:")
            for key, value in memory_data.items():
                print(f"  {key}: {value[:100] if len(str(value)) > 100 else value}")
                
        except Exception as e:
            print(f"❌ Ошибка отладки: {e}")
            import traceback
            print(traceback.format_exc())

async def main():
    """Главная функция теста"""
    tester = MemoryTester()
    
    try:
        # Запускаем основной тест
        await tester.test_memory_sequence()
        
        # Отладка состояния памяти
        await tester.debug_memory_state()
        
        print("\n🎉 ТЕСТ ЗАВЕРШЕН!")
        
    except Exception as e:
        print(f"❌ Критическая ошибка теста: {e}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(main())
