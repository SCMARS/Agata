#!/usr/bin/env python3
"""
Быстрый тест памяти - проверяем запоминание и воспроизведение
"""
import sys
import os
import asyncio
from datetime import datetime

# Добавляем путь к проекту
sys.path.append('/Users/glebuhovskij/Agata')

from app.graph.pipeline import AgathaPipeline

async def quick_test():
    """Быстрый тест памяти"""
    print("🚀 БЫСТРЫЙ ТЕСТ ПАМЯТИ")
    print("=" * 30)
    
    pipeline = AgathaPipeline()
    user_id = "quick_test_user"
    conversation = []
    
    async def ask_question(question: str) -> str:
        """Задать вопрос и получить ответ"""
        print(f"\n👤 Пользователь: {question}")
        
        conversation.append({
            "role": "user",
            "content": question,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        try:
            response = await pipeline.process_chat(
                user_id=user_id,
                messages=conversation,
                meta_time=datetime.utcnow().isoformat()
            )
            
            response_text = " ".join(response["parts"]) if isinstance(response, dict) and "parts" in response else str(response)
            print(f"🤖 Агата: {response_text}")
            
            conversation.append({
                "role": "assistant", 
                "content": response_text,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return response_text
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            return ""
    
    # Этап 1: Знакомство
    print("\n📝 ЭТАП 1: Знакомство")
    await ask_question("Привет! Меня зовут Андрей")
    await ask_question("Мне 28 лет")
    await ask_question("Я программист")
    await ask_question("Моя любимая еда - пицца")
    
    # Отвлекающие вопросы
    print("\n🎲 ОТВЛЕКАЮЩИЕ ВОПРОСЫ")
    await ask_question("Какая погода?")
    await ask_question("Расскажи шутку")
    await ask_question("Что думаешь о работе?")
    
    # Проверка памяти
    print("\n🧠 ПРОВЕРКА ПАМЯТИ")
    
    print("\n🔍 Тест 1: Имя")
    response = await ask_question("Как меня зовут?")
    if "андрей" in response.lower():
        print("✅ Имя запомнено!")
    else:
        print("❌ Имя не найдено в ответе")
    
    print("\n🔍 Тест 2: Возраст")
    response = await ask_question("Сколько мне лет?")
    if "28" in response:
        print("✅ Возраст запомнен!")
    else:
        print("❌ Возраст не найден в ответе")
    
    print("\n🔍 Тест 3: Профессия")
    response = await ask_question("Кем я работаю?")
    if "программист" in response.lower():
        print("✅ Профессия запомнена!")
    else:
        print("❌ Профессия не найдена в ответе")
    
    print("\n🔍 Тест 4: Еда")
    response = await ask_question("Какая моя любимая еда?")
    if "пицца" in response.lower():
        print("✅ Любимая еда запомнена!")
    else:
        print("❌ Любимая еда не найдена в ответе")
    
    print("\n🎉 ТЕСТ ЗАВЕРШЕН!")

if __name__ == "__main__":
    asyncio.run(quick_test())
