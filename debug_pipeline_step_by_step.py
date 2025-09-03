#!/usr/bin/env python3

import os
import sys
import asyncio
import traceback
from datetime import datetime

# Добавляем путь к проекту
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

async def test_pipeline_step_by_step():
    """Тестируем пайплайн пошагово для выявления проблемы"""
    
    print("🔍 ПОШАГОВАЯ ДИАГНОСТИКА PIPELINE")
    print("=" * 50)
    
    try:
        print("📦 Импортируем pipeline...")
        from app.graph.pipeline import AgathaPipeline
        print("✅ Pipeline импортирован")
        
        print("\n🏗️ Создаем pipeline...")
        pipeline = AgathaPipeline()
        print("✅ Pipeline создан")
        print(f"   Граф: {type(pipeline.graph)}")
        
        print("\n📝 Подготавливаем тестовые данные...")
        user_id = "debug_user"
        messages = [{"role": "user", "content": "привет"}]
        meta_time = "2025-09-02T14:07:00Z"
        
        print(f"   User ID: {user_id}")
        print(f"   Messages: {messages}")
        print(f"   Meta time: {meta_time}")
        
        print("\n🚀 Запускаем process_chat...")
        
        try:
            result = await pipeline.process_chat(user_id, messages, meta_time)
            print("✅ Pipeline выполнен успешно!")
            print(f"📄 Результат: {result}")
            
        except Exception as e:
            print(f"❌ Ошибка в process_chat: {e}")
            print(f"   Тип ошибки: {type(e)}")
            traceback.print_exc()
            
            # Попробуем выполнить граф напрямую
            print("\n🔧 Попробуем выполнить граф напрямую...")
            
            try:
                # Создаем начальное состояние как в process_chat
                state = {
                    "user_id": user_id,
                    "messages": messages,
                    "meta_time": datetime.fromisoformat(meta_time.replace('Z', '+00:00')),
                    "normalized_input": "",
                    "memory_context": "",
                    "day_prompt": "",
                    "stage_prompt": "",
                    "behavior_prompt": "",
                    "final_prompt": "",
                    "llm_response": "",
                    "processed_response": {},
                    "current_strategy": "caring",
                    "behavioral_analysis": {},
                    "strategy_confidence": 0.0,
                    "day_number": 1,
                    "stage_number": 1,
                    "question_count": 0,
                    "processing_start": datetime.utcnow()
                }
                
                print(f"📊 Начальное состояние: {state}")
                
                # Выполняем граф
                result = await pipeline.graph.ainvoke(state)
                print("✅ Граф выполнен напрямую!")
                print(f"📄 Результат: {result}")
                
            except Exception as e2:
                print(f"❌ Ошибка в прямом вызове графа: {e2}")
                print(f"   Тип ошибки: {type(e2)}")
                traceback.print_exc()
                
                # Попробуем выполнить узлы по одному
                print("\n🔧 Попробуем выполнить узлы по одному...")
                
                try:
                    # Узел 1: ingest_input
                    print("   🚀 Узел 1: ingest_input")
                    state = await pipeline._ingest_input(state)
                    print(f"      ✅ normalized_input: {state['normalized_input']}")
                    
                    # Узел 2: short_memory
                    print("   🧠 Узел 2: short_memory")
                    state = await pipeline._short_memory(state)
                    print(f"      ✅ memory_context: {len(state.get('memory_context', ''))} символов")
                    
                    # Узел 3: day_policy
                    print("   📅 Узел 3: day_policy")
                    state = await pipeline._day_policy(state)
                    print(f"      ✅ day_prompt: {len(state.get('day_prompt', ''))} символов")
                    
                    # Узел 4: behavior_policy
                    print("   🎭 Узел 4: behavior_policy")
                    state = await pipeline._behavior_policy(state)
                    print(f"      ✅ behavior_prompt: {len(state.get('behavior_prompt', ''))} символов")
                    
                    # Узел 5: compose_prompt
                    print("   ✍️ Узел 5: compose_prompt")
                    state = await pipeline._compose_prompt(state)
                    print(f"      ✅ final_prompt: {len(state.get('final_prompt', ''))} символов")
                    
                    # Узел 6: llm_call
                    print("   🤖 Узел 6: llm_call")
                    state = await pipeline._llm_call(state)
                    print(f"      ✅ llm_response: {len(state.get('llm_response', ''))} символов")
                    
                    # Узел 7: postprocess
                    print("   🔧 Узел 7: postprocess")
                    state = await pipeline._postprocess(state)
                    print(f"      ✅ processed_response: {state.get('processed_response', {})}")
                    
                    # Узел 8: persist
                    print("   💾 Узел 8: persist")
                    state = await pipeline._persist(state)
                    print(f"      ✅ Финальное состояние сохранено")
                    
                    print("\n🎉 Все узлы выполнены успешно!")
                    
                except Exception as e3:
                    print(f"❌ Ошибка в узле: {e3}")
                    print(f"   Тип ошибки: {type(e3)}")
                    traceback.print_exc()
    
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        print(f"   Тип ошибки: {type(e)}")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_pipeline_step_by_step())
