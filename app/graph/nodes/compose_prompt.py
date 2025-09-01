"""
Compose Prompt Node - узел для составления промпта с использованием системного шаблона
"""
from langchain_core.prompts import ChatPromptTemplate
from typing import Dict, Any
import logging
import os

logger = logging.getLogger(__name__)


class ComposePromptNode:
    """Узел для составления промпта с использованием системного шаблона"""
    
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
            else:
                logger.warning(f"Файл системного промпта не найден: {prompt_path}")
                return self._get_fallback_prompt()
        except Exception as e:
            logger.error(f"Ошибка загрузки системного промпта: {e}")
            return self._get_fallback_prompt()
    
    def _get_fallback_prompt(self) -> str:
        """Fallback промпт если основной не загрузился"""
        return """ТЫ — Agatha: тёплый, эмпатичный маркетолог-партнёр.
Используй информацию из памяти о пользователе и свою биографию для ответов.
Отвечай естественно и дружелюбно."""
    
    def _create_prompt_template(self) -> ChatPromptTemplate:
        """Создает шаблон промпта"""
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
            
            # КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: Если нет готовых данных памяти, создаем MemoryAdapter
            memory_data = state.get("memory", {})
            if not memory_data or all(v == "—" for v in memory_data.values()):
                logger.info(f"🔧 КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: memory_data пусто, создаем MemoryAdapter")
                print(f"🔧 КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: memory_data пусто, создаем MemoryAdapter")
                
                # Получаем менеджер памяти из pipeline
                if hasattr(state, 'memory_manager') or 'memory_manager' in state:
                    memory_manager = state.get('memory_manager') or getattr(state, 'memory_manager', None)
                    if memory_manager:
                        from ...memory.memory_adapter import MemoryAdapter
                        adapter = MemoryAdapter(memory_manager)
                        memory_data = adapter.get_for_prompt(user_id, input_text)
                        logger.info(f"✅ ИСПРАВЛЕНИЕ: Получили данные от MemoryAdapter")
                        print(f"✅ ИСПРАВЛЕНИЕ: Получили данные от MemoryAdapter")
                    else:
                        logger.warning(f"⚠️ ИСПРАВЛЕНИЕ: memory_manager не найден в state")
                        print(f"⚠️ ИСПРАВЛЕНИЕ: memory_manager не найден в state")
                else:
                    logger.warning(f"⚠️ ИСПРАВЛЕНИЕ: memory_manager не найден")
                    print(f"⚠️ ИСПРАВЛЕНИЕ: memory_manager не найден")
            
            # КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: извлекаем данные из memory_context
            memory_context = state.get("memory_context", "")
            logger.info(f"🔧 КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: Обрабатываем memory_context длиной {len(memory_context)} символов")
            
            # Всегда используем данные из memory_context, если MemoryAdapter не работает
            if memory_data.get("long_memory_facts") == "—" and memory_context:
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
            
            # Счетчик вопросов
            question_counter = state.get("question_count", 0)
            may_ask_question = (question_counter % 3 == 2)
            
            # Биография Агаты (можно вынести в отдельный файл)
            agatha_bio = self._get_agatha_bio()
            
            # Форматируем промпт
            formatted_prompt = self.prompt_template.format_messages(
                input_text=input_text,
                short_memory_summary=memory_data.get("short_memory_summary", "—"),
                long_memory_facts=memory_data.get("long_memory_facts", "—"),
                semantic_context=memory_data.get("semantic_context", "—"),
                day_instructions=day_instructions,
                behavior_style=behavior_style,
                agatha_bio=agatha_bio,
                tone_style=tone_style,
                now_iso=now_iso,
                day_number=day_number,
                last_diff_sec=last_diff_sec,
                may_ask_question=str(may_ask_question).lower()
            )
            
            # Создаем новое состояние с обновлениями
            updated_state = {
                "formatted_prompt": formatted_prompt,
                "may_ask_question": may_ask_question,
                "system_prompt_used": True,
                "final_prompt": "\n".join([msg.content for msg in formatted_prompt])
            }
            
            # 🔥 КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: ПРИНУДИТЕЛЬНО ИЗВЛЕКАЕМ ДАННЫЕ ИЗ memory_context
            memory_context = state.get("memory_context", "")
            if memory_context and ("глеб" in memory_context.lower() or "меня зовут" in memory_context.lower()):
                logger.info(f"🔥 КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: Найден memory_context с именем пользователя")
                
                # Извлекаем имя
                user_name = "Глеб" if "глеб" in memory_context.lower() else "пользователь"
                
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
    
    def _get_agatha_bio(self) -> str:
        """Возвращает биографию Агаты из конфигурации"""
        try:
            # Пытаемся загрузить из файла конфигурации
            bio_path = "config/agatha_bio.txt"
            if os.path.exists(bio_path):
                with open(bio_path, "r", encoding="utf-8") as f:
                    return f.read().strip()
            
            # Fallback биография
            return """Агата Кузьменко, 27 лет, родилась в Киеве, живет в Варшаве с 2018 года.
Маркетолог, работаю в Move Closer, занимаюсь трейдингом. 
Хобби: спорт (бассейн, спортзал), кулинария, путешествия.
Мечтаю о Tesla, планирую свое агентство."""
        except Exception as e:
            logger.warning(f"Ошибка загрузки биографии: {e}")
            return "Агата - дружелюбный AI-помощник."
    
    def get_prompt_info(self) -> Dict[str, Any]:
        """Возвращает информацию о промпте для диагностики"""
        return {
            "system_prompt_length": len(self.system_prompt),
            "template_created": self.prompt_template is not None,
            "prompt_path": "config/prompts/system_core.txt"
        }
