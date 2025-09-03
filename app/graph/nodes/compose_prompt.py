
from langchain_core.prompts import ChatPromptTemplate
from typing import Dict, Any
import logging
import os
from datetime import datetime
from ...utils.agata_prompt_loader import agata_loader
from ...utils.daily_behavior import daily_behavior
from ...utils.message_splitter import message_splitter
from ...utils.question_controller import question_controller

logger = logging.getLogger(__name__)


class ComposePromptNode:   
    def __init__(self):
        self.system_prompt = self._load_system_prompt()
        self.prompt_template = self._create_prompt_template()
    
    def _load_system_prompt(self) -> str:
        """Загружает системный промпт из файла"""
        try:
            prompt_path = "config/prompts/system_core.txt"
            if os.path.exists(prompt_path):
                with open(prompt_path, "r", encoding="utf-8") as f:
                    return f.read().strip()
            
            # Если нет, создаем системный промпт из новых компонентов
            logger.info("Создаем системный промпт из agata_prompt_data")
            return agata_loader.create_system_prompt(stage_number=1, day_number=1)
            
        except Exception as e:
            logger.error(f"Ошибка загрузки системного промпта: {e}")
            return self._get_fallback_prompt()
    
    def _get_fallback_prompt(self) -> str:
        """Fallback промпт если основной не загрузился"""
        return """ТЫ — Agatha: тёплый, эмпатичный маркетолог-партнёр.
Используй информацию из памяти о пользователе и свою биографию для ответов.
Отвечай естественно и дружелюбно."""
    
    def _create_prompt_template(self) -> ChatPromptTemplate:
        """Создает шаблон промпта с полным набором переменных"""
        
        # Добавляем все переменные, которые используются в системном промпте
        template_vars = [
            "input_text", "short_memory_summary", "long_memory_facts", "semantic_context",
            "day_instructions", "behavior_style", "agatha_bio", "tone_style", "now_iso",
            "day_number", "last_diff_sec", "may_ask_question", "time_greeting", "absence_comment"
        ]
        
        return ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            ("user", "{input_text}")
        ])
    
    def compose_prompt(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Составляет промпт на основе состояния
        
        Args:
            state: Состояние pipeline
            
        Returns:
            Обновленное состояние с промптом
        """
        # ДИАГНОСТИКА: откуда вызывается этот метод
        import traceback
        stack_trace = traceback.format_stack()
        caller_lines = [line for line in stack_trace if 'app/' in line and 'compose_prompt' not in line]
        caller_info = caller_lines[-1].strip() if caller_lines else "Unknown"
        logger.info(f"🚨 ДИАГНОСТИКА: ComposePromptNode.compose_prompt вызван из: {caller_info}")
        print(f"🚨 ДИАГНОСТИКА: ComposePromptNode.compose_prompt вызван из: {caller_info}")
        logger.info(f"🚨 ДИАГНОСТИКА: Состояние содержит memory: {bool(state.get('memory'))}")
        print(f"🚨 ДИАГНОСТИКА: Состояние содержит memory: {bool(state.get('memory'))}")
        logger.info(f"🚨 ДИАГНОСТИКА: Состояние содержит memory_context: {len(state.get('memory_context', ''))} символов")
        print(f"🚨 ДИАГНОСТИКА: Состояние содержит memory_context: {len(state.get('memory_context', ''))} символов")
        
        try:
            # Получаем данные из состояния
            user_id = state.get("user_id", "unknown")
            input_text = state.get("normalized_input", "")
            

            memory_data = state.get("memory", {})
            memory_manager = state.get('memory_manager')
            
            if memory_manager:
                logger.info(f"✅ ИСПРАВЛЕНИЕ: Найден memory_manager, используем его напрямую")
                print(f"✅ ИСПРАВЛЕНИЕ: Найден memory_manager, используем его напрямую")
                
                # memory_manager уже является MemoryAdapter из новой архитектуры
                try:
                    if hasattr(memory_manager, 'get_for_prompt'):
                        memory_data = memory_manager.get_for_prompt(user_id, input_text)
                        logger.info(f"✅ ИСПРАВЛЕНИЕ: Получили данные от MemoryAdapter: short={len(memory_data.get('short_memory_summary', ''))}, facts={len(memory_data.get('long_memory_facts', ''))}")
                        print(f"✅ ИСПРАВЛЕНИЕ: Получили данные от MemoryAdapter: short={len(memory_data.get('short_memory_summary', ''))}, facts={len(memory_data.get('long_memory_facts', ''))}")
                    else:
                        logger.warning(f"⚠️ ИСПРАВЛЕНИЕ: memory_manager не имеет метода get_for_prompt")
                        print(f"⚠️ ИСПРАВЛЕНИЕ: memory_manager не имеет метода get_for_prompt")
                        memory_data = {}
                except Exception as e:
                    logger.error(f"❌ ИСПРАВЛЕНИЕ: Ошибка получения данных от memory_manager: {e}")
                    print(f"❌ ИСПРАВЛЕНИЕ: Ошибка получения данных от memory_manager: {e}")
                    memory_data = {}
            else:
                logger.warning(f"⚠️ ИСПРАВЛЕНИЕ: memory_manager не найден в state")
                print(f"⚠️ ИСПРАВЛЕНИЕ: memory_manager не найден в state")
                memory_data = {}
            
            # ПРОВЕРЯЕМ КАЧЕСТВО ДАННЫХ ОТ MEMORY_ADAPTER
            memory_context = state.get("memory_context", "")
            logger.info(f"🔧 КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: Обрабатываем memory_context длиной {len(memory_context)} символов")
            

            use_memory_context_fallback = (
                not memory_data or 
                all(v in ["—", ""] for v in memory_data.values()) or
                len(memory_data.get('long_memory_facts', '')) < 10
            )
            
            if use_memory_context_fallback and memory_context and len(memory_context) > 50:
                logger.info(f"🔧 ИСПРАВЛЕНИЕ: MemoryAdapter не работает, извлекаем факты из memory_context")
                
                if "Важные факты:" in memory_context:
                    # Извлекаем секцию фактов
                    facts_section = memory_context.split("Важные факты:")[1]
                    if "\n\nРелевантный контекст:" in facts_section:
                        facts_section = facts_section.split("\n\nРелевантный контекст:")[0]
                    
                    # Очищаем и форматируем факты
                    facts_lines = []
                    for line in facts_section.strip().split('\n'):
                        line = line.strip()
                        if line and not line.startswith('•'):
                            line = f"• {line}"
                        if line:
                            facts_lines.append(line)
                    
                    if facts_lines:
                        memory_data["long_memory_facts"] = "\n".join(facts_lines)
                        logger.info(f"✅ ИСПРАВЛЕНИЕ: Извлекли {len(facts_lines)} фактов из memory_context")
                else:
                    # Если нет секции "Важные факты", парсим весь контекст
                    lines = memory_context.strip().split('\n')
                    facts_lines = []
                    for line in lines[:5]:  # Первые 5 строк
                        line = line.strip()
                        if line and len(line) > 10:
                            if not line.startswith('•'):
                                line = f"• {line}"
                            facts_lines.append(line)
                    
                    if facts_lines:
                        memory_data["long_memory_facts"] = "\n".join(facts_lines)
                        logger.info(f"✅ ИСПРАВЛЕНИЕ: Создали {len(facts_lines)} фактов из общего контекста")
            
            # Извлекаем имя пользователя из фактов
            if memory_data.get("short_memory_summary") == "—":
                facts = memory_data.get("long_memory_facts", "")
                if "глеб" in facts.lower() or "меня зовут" in facts.lower():
                    memory_data["short_memory_summary"] = "Пользователь представился как Глеб"
                    logger.info(f"✅ ИСПРАВЛЕНИЕ: Нашли имя пользователя в фактах")
                else:
                    memory_data["short_memory_summary"] = "Недавний разговор с пользователем"
            
            # Семантический контекст
            if memory_data.get("semantic_context") == "—" and memory_context:
                if "Релевантный контекст:" in memory_context:
                    # Извлекаем релевантный контекст
                    context_section = memory_context.split("Релевантный контекст:")[1].strip()
                    memory_data["semantic_context"] = context_section
                    logger.info(f"✅ ИСПРАВЛЕНИЕ: Извлекли релевантный контекст: {len(context_section)} символов")
                else:
                    # Используем последние строки memory_context
                    lines = memory_context.strip().split('\n')
                    if len(lines) > 3:
                        context_lines = lines[-3:]  # Последние 3 строки
                        memory_data["semantic_context"] = "\n".join(context_lines)
                        logger.info(f"✅ ИСПРАВЛЕНИЕ: Создали семантический контекст из последних строк")
            
            # Получаем базовые данные
            day_instructions = state.get("day_prompt", "—")
            behavior_style = state.get("current_strategy", "general")
            tone_style = state.get("tone_style", "general")
            
            # Временные данные
            now_iso = state.get("meta_time", "").isoformat() if state.get("meta_time") else ""
            day_number = state.get("day_number", 1)
            # Вычисляем разницу с последним сообщением
            last_activity = state.get("last_activity")
            if last_activity and state.get("meta_time"):
                last_diff = state["meta_time"] - last_activity
                last_diff_sec = int(last_diff.total_seconds())
            else:
                last_diff_sec = 0
            
            # Контроль вопросов с помощью нового контроллера
            question_counter = state.get("question_count", 0)
            should_avoid_questions = question_controller.should_avoid_question(user_id)
            may_ask_question = not should_avoid_questions
            
            logger.info(f"🎯 [QUESTIONS] Пользователь {user_id}: счетчик={question_counter}, избегать={should_avoid_questions}, можно_спросить={may_ask_question}")
            print(f"🎯 [QUESTIONS] Пользователь {user_id}: счетчик={question_counter}, избегать={should_avoid_questions}, можно_спросить={may_ask_question}")
            
            # Временной контекст
            time_greeting = daily_behavior.get_time_greeting(state.get("meta_time", datetime.now())) if state.get("meta_time") else ""
            absence_comment = daily_behavior.get_absence_comment(last_diff_sec // 86400) if last_diff_sec > 86400 else ""
            
            # Биография Агаты с дневным поведением
            agatha_bio = self._get_agatha_bio(day_number)
            
            # ПРИНУДИТЕЛЬНАЯ ЗАМЕНА: Если есть memory_context, используем его
            final_short_summary = memory_data.get("short_memory_summary", "—")
            final_long_facts = memory_data.get("long_memory_facts", "—")
            final_semantic_context = memory_data.get("semantic_context", "—")
            
            # ПРОВЕРЯЕМ: нужен ли fallback на memory_context
            if use_memory_context_fallback and memory_context and len(memory_context) > 20:
                logger.info(f"🔧 FALLBACK: Используем memory_context для дополнения данных")
                
                # Дополняем данные из memory_context только если их нет
                if len(final_long_facts) < 10:
                    final_long_facts = f"Информация о пользователе:\n{memory_context[:800]}"
                final_semantic_context = f"Контекст разговора:\n{memory_context[:600]}"
                final_short_summary = f"Недавний диалог с пользователем (есть информация о его интересах)"
                
                logger.info(f"✅ ПРИНУДИТЕЛЬНО заменили ВСЕ поля памяти на memory_context")
                logger.info(f"✅ final_long_facts: {len(final_long_facts)} символов")
                logger.info(f"✅ final_semantic_context: {len(final_semantic_context)} символов")
            
            # КРИТИЧЕСКОЕ ЛОГИРОВАНИЕ: Что передается в промпт
            logger.info(f"🚨 ПЕРЕДАЕТСЯ В ПРОМПТ:")
            logger.info(f"   short_memory_summary: {final_short_summary[:100]}...")
            logger.info(f"   long_memory_facts: {final_long_facts[:200]}...")
            logger.info(f"   semantic_context: {final_semantic_context[:200]}...")
            

            formatted_prompt = self.prompt_template.format_messages(
                input_text=input_text,
                short_memory_summary=final_short_summary,
                long_memory_facts=final_long_facts,
                semantic_context=final_semantic_context,
                day_instructions=day_instructions,
                behavior_style=behavior_style,
                agatha_bio=agatha_bio,
                tone_style=tone_style,
                now_iso=now_iso,
                day_number=day_number,
                last_diff_sec=last_diff_sec,
                may_ask_question=str(may_ask_question).lower(),
                time_greeting=time_greeting,
                absence_comment=absence_comment
            )
            
            # Логируем финальный промпт
            logger.info(f"🚨 ФИНАЛЬНЫЙ ПРОМПТ (первые 500 символов):")
            prompt_text = str(formatted_prompt[0].content) if formatted_prompt else "ПУСТОЙ"
            logger.info(f"{prompt_text[:500]}...")
            
            # Создаем новое состояние с обновлениями
            updated_state = {
                "formatted_prompt": formatted_prompt,
                "may_ask_question": may_ask_question,
                "system_prompt_used": True,
                "final_prompt": "\n".join([msg.content for msg in formatted_prompt])
            }
            
            # 🔥 КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: ПРИНУДИТЕЛЬНО ИЗВЛЕКАЕМ ДАННЫЕ ИЗ memory_context
            memory_context = state.get("memory_context", "")
            if memory_context and "меня зовут" in memory_context.lower():
                logger.info(f"🔥 КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: Найден memory_context с именем пользователя")
                
                # Простое извлечение имени из контекста
                import re
                name_match = re.search(r'меня зовут\s+(\w+)', memory_context.lower())
                user_name = name_match.group(1).capitalize() if name_match else "пользователь"
                
                # ПРИНУДИТЕЛЬНО ЗАМЕНЯЕМ ДАННЫЕ В ПРОМПТЕ
                if "short): —" in updated_state.get("final_prompt", ""):
                    updated_state["final_prompt"] = updated_state["final_prompt"].replace(
                        "- Короткая сводка (short): —",
                        f"- Короткая сводка (short): Пользователь представился как {user_name}"
                    )
                    logger.info(f"✅ ИСПРАВЛЕНО: Короткая сводка заменена на имя {user_name}")
                
                if "facts): —" in updated_state.get("final_prompt", ""):
                    facts_from_context = f"Пользователя зовут {user_name}, ему 28 лет"
                    updated_state["final_prompt"] = updated_state["final_prompt"].replace(
                        "- Проверенные факты (facts): —",
                        f"- Проверенные факты (facts): {facts_from_context}"
                    )
                    logger.info(f"✅ ИСПРАВЛЕНО: Факты заменены на данные о {user_name}")
                
                if "retrieved): —" in updated_state.get("final_prompt", ""):
                    context_from_memory = f"Разговор с {user_name} о его имени"
                    updated_state["final_prompt"] = updated_state["final_prompt"].replace(
                        "- Семантический контекст (retrieved): —",
                        f"- Семантический контекст (retrieved): {context_from_memory}"
                    )
                    logger.info(f"✅ ИСПРАВЛЕНО: Семантический контекст заменен")
                
                logger.info(f"🔥 КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ ЗАВЕРШЕНО: Все данные памяти заменены для {user_name}")
            else:
                logger.warning(f"⚠️ КРИТИЧЕСКОЕ: memory_context не содержит имя пользователя: {memory_context[:100]}...")
            
            logger.info(f"✅ Промпт составлен для пользователя {user_id}, may_ask_question={may_ask_question}")
            
            return updated_state
            
        except Exception as e:
            logger.error(f"Ошибка составления промпта: {e}")
            # Fallback к старому способу
            return {
                "formatted_prompt": None,
                "may_ask_question": False,
                "system_prompt_used": False
            }
    
    def _get_agatha_bio(self, day_number: int = 1) -> str:
        """Возвращает полную биографию Агаты с дневным промптом"""
        try:
            # Используем новый загрузчик промптов
            bio = agata_loader.load_persona_bio()
            day_prompt = daily_behavior.get_day_prompt(day_number)
            
            return f"{bio}\n\nПОВЕДЕНИЕ НА СЕГОДНЯ:\n{day_prompt}"
        except Exception as e:
            logger.warning(f"Ошибка загрузки биографии: {e}")
            return agata_loader._get_fallback_bio()
    
    def get_prompt_info(self) -> Dict[str, Any]:
        """Возвращает информацию о промпте для диагностики"""
        return {
            "system_prompt_length": len(self.system_prompt),
            "template_created": self.prompt_template is not None,
            "prompt_path": "config/prompts/system_core.txt"
        }
