#!/usr/bin/env python3
"""
Тест OpenAI API
"""
import os
import asyncio
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

async def test_openai():
    """Тестируем OpenAI API"""
    print("🧪 Тестирование OpenAI API")
    print("=" * 40)
    
    # Проверяем переменную окружения
    api_key = os.getenv('OPENAI_API_KEY')
    print(f"🔑 API Key: {api_key[:20] if api_key else 'None'}...")
    
    if not api_key:
        print("❌ Нет API ключа!")
        return
    
    try:
        # Создаем LLM
        llm = ChatOpenAI(
            api_key=api_key,
            model="gpt-4",
            temperature=0.8
        )
        print("✅ LLM создан успешно")
        
        # Тестируем вызов
        prompt = "Привет! Расскажи мне кратко о том, что такое искусственный интеллект. Ответ должен быть минимум 200 символов."
        print(f"📝 Отправляем промпт: {prompt}")
        
        response = await llm.ainvoke([HumanMessage(content=prompt)])
        print(f"✅ Получен ответ длиной {len(response.content)} символов")
        print(f"📝 Ответ: {response.content[:200]}...")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(test_openai()) 