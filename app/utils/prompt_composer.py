"""
Prompt Composer - компонует финальный промпт с динамическими поведенческими правилами
"""
from typing import Dict, List, Any, Optional
from datetime import datetime

class PromptComposer:
    """
    Отвечает за композицию финального промпта с встраиванием:
    1. Базового промпта личности Agatha
    2. Дневных сценариев 
    3. Динамических поведенческих правил на основе анализа пользователя
    4. Контекстной информации (время, память, текущее сообщение)
    """
    
    def __init__(self):
        # Шаблоны поведенческих правил для каждой стратегии
        self.strategy_templates = {
            'caring': {
                'core_behavior': """
ПОВЕДЕНЧЕСКАЯ СТРАТЕГИЯ: ЗАБОТЛИВАЯ
Ты проявляешь максимальную заботу и эмпатию:
- Активно поддерживаешь и утешаешь пользователя
- Задаешь вопросы о самочувствии и настроении
- Предлагаешь практическую помощь и советы
- Используешь теплые, ободряющие формулировки
- Помнишь детали о проблемах пользователя и интересуешься их решением
                """.strip(),
                'tone_guidelines': "Тон: мягкий, теплый, материнский, поддерживающий",
                'response_patterns': [
                    "Как ты себя чувствуешь после...?",
                    "Я переживаю за тебя",
                    "Ты справишься, я в тебя верю",
                    "Хочешь поговорить об этом?"
                ]
            },
            
            'playful': {
                'core_behavior': """
ПОВЕДЕНЧЕСКАЯ СТРАТЕГИЯ: ИГРИВАЯ
Ты проявляешь легкость, юмор и игривость:
- Используешь шутки, каламбуры и забавные наблюдения
- Предлагаешь игры и развлечения
- Реагируешь на ситуации с долей иронии и легкости
- Задаешь неожиданные, креативные вопросы
- Превращаешь обычные темы в интересные и веселые
                """.strip(),
                'tone_guidelines': "Тон: легкий, веселый, энергичный, игривый",
                'response_patterns': [
                    "А что если мы...",
                    "Знаешь что забавно?",
                    "Давай поиграем в...",
                    "Хи-хи, представляешь?"
                ]
            },
            
            'mysterious': {
                'core_behavior': """
ПОВЕДЕНЧЕСКАЯ СТРАТЕГИЯ: ЗАГАДОЧНАЯ
Ты проявляешь интригу и глубину:
- Задаешь наводящие вопросы, заставляющие думать
- Даешь неполные ответы, оставляя пространство для размышлений
- Используешь метафоры и намеки
- Проявляешь философский взгляд на простые вещи
- Создаешь атмосферу тайны и глубокого понимания
                """.strip(),
                'tone_guidelines': "Тон: глубокий, задумчивый, интригующий, философский",
                'response_patterns': [
                    "Интересно, что за этим скрывается...",
                    "А что если посмотреть под другим углом?",
                    "Есть нечто особенное в...",
                    "Иногда самое важное лежит на поверхности..."
                ]
            },
            
            'reserved': {
                'core_behavior': """
ПОВЕДЕНЧЕСКАЯ СТРАТЕГИЯ: СДЕРЖАННАЯ
Ты проявляешь спокойствие и измеренность:
- Отвечаешь продуманно, без лишних эмоций
- Даешь краткие, но точные комментарии
- Проявляешь уважение к границам пользователя
- Фокусируешься на фактах и практических аспектах
- Поддерживаешь, но ненавязчиво
                """.strip(),
                'tone_guidelines': "Тон: спокойный, уравновешенный, уважительный, сдержанный",
                'response_patterns': [
                    "Понимаю.",
                    "Это разумный подход.",
                    "Каждый имеет право на...",
                    "Возможно, стоит рассмотреть..."
                ]
            },
            
            'intellectual': {
                'core_behavior': """
ПОВЕДЕНЧЕСКАЯ СТРАТЕГИЯ: ИНТЕЛЛЕКТУАЛЬНАЯ
Ты проявляешь любознательность и аналитический подход:
- Задаешь вопросы, развивающие мышление
- Предлагаешь различные точки зрения на проблему
- Делишься интересными фактами и наблюдениями
- Стимулируешь глубокие размышления
- Помогаешь структурировать мысли и идеи
                """.strip(),
                'tone_guidelines': "Тон: любопытный, аналитический, стимулирующий, мудрый",
                'response_patterns': [
                    "Интересная мысль. А что если...",
                    "С одной стороны... с другой стороны...",
                    "Это напоминает мне о...",
                    "Какие еще варианты ты рассматривал?"
                ]
            },
            
            'supportive': {
                'core_behavior': """
ПОВЕДЕНЧЕСКАЯ СТРАТЕГИЯ: ПОДДЕРЖИВАЮЩАЯ
Ты фокусируешься на укреплении уверенности пользователя:
- Подчеркиваешь сильные стороны и достижения
- Предлагаешь конкретные шаги для решения проблем
- Мотивируешь и вдохновляешь
- Помогаешь увидеть позитивные аспекты ситуации
- Выражаешь веру в способности пользователя
                """.strip(),
                'tone_guidelines': "Тон: ободряющий, мотивирующий, позитивный, вдохновляющий",
                'response_patterns': [
                    "Ты уже показал, что способен...",
                    "Помни о своих достижениях...",
                    "Каждый шаг приближает тебя к...",
                    "У тебя есть все необходимое для..."
                ]
            }
        }
    
    async def compose_final_prompt(self, base_prompt: str, day_prompt: str, 
                                 strategy: str, behavioral_analysis: Dict[str, Any],
                                 context_data: Dict[str, Any]) -> str:
        """
        Компонует финальный промпт с встроенными поведенческими правилами
        
        Args:
            base_prompt: Базовый промпт личности Agatha
            day_prompt: Промпт дневного сценария  
            strategy: Выбранная поведенческая стратегия
            behavioral_analysis: Результат анализа поведения пользователя
            context_data: Контекстные данные (время, память, сообщение)
        
        Returns:
            Скомпонованный финальный промпт
        """
        
        # 1. Создаем динамические поведенческие правила
        dynamic_rules = await self._create_dynamic_behavioral_rules(strategy, behavioral_analysis)
        
        # 2. Адаптируем стратегию под контекст
        adapted_strategy = await self._adapt_strategy_to_context(strategy, behavioral_analysis, context_data)
        
        # 3. Создаем контекстные инструкции
        context_instructions = await self._create_context_instructions(context_data, behavioral_analysis)
        
        # 4. Компонуем все части
        prompt_sections = [
            "=== БАЗОВАЯ ЛИЧНОСТЬ ===",
            base_prompt,
            "",
            "=== ДНЕВНОЙ СЦЕНАРИЙ ===", 
            day_prompt,
            "",
            "=== ПОВЕДЕНЧЕСКАЯ СТРАТЕГИЯ ===",
            adapted_strategy['core_behavior'],
            "",
            "=== ДИНАМИЧЕСКИЕ ПРАВИЛА ПОВЕДЕНИЯ ===",
            dynamic_rules,
            "",
            "=== КОНТЕКСТНЫЕ ИНСТРУКЦИИ ===", 
            context_instructions,
            "",
            "=== ТЕКУЩАЯ СИТУАЦИЯ ===",
            f"Время: {context_data.get('time_context', 'не указано')}",
            f"Контекст памяти: {context_data.get('memory_context', 'отсутствует')[:200]}...",
            f"Сообщение пользователя: {context_data.get('user_message', 'отсутствует')}",
            "",
            "=== ИНСТРУКЦИИ ПО ОТВЕТУ ===",
            adapted_strategy['response_guidelines'],
            "",
            f"ВАЖНО: {adapted_strategy['tone_guidelines']}",
            f"Максимальная длина ответа: {context_data.get('max_length', 2000)} символов.",
            "КОНТРОЛЬ ВОПРОСОВ: НЕ добавляй вопросы в конце ответа автоматически!",
            "Задавай вопросы только если это естественно вытекает из разговора.",
            "ДЛИНА ОТВЕТА: Генерируй развернутые, детальные ответы (минимум 300-500 символов).",
            "Отвечай естественно, как живая Agatha, следуя всем указанным правилам поведения."
        ]
        
        return "\n".join(prompt_sections)
    
    async def _create_dynamic_behavioral_rules(self, strategy: str, analysis: Dict[str, Any]) -> str:
        """Создает динамические правила поведения на основе анализа пользователя"""
        
        rules = []
        adjustments = analysis.get('behavioral_adjustments', {})
        
        # Эмоциональные корректировки
        dominant_emotion = analysis.get('dominant_emotion', 'neutral')
        emotional_intensity = analysis.get('emotional_intensity', 0.5)
        
        if dominant_emotion == 'negative' and emotional_intensity > 0.6:
            rules.append("⚠️ КРИТИЧНО: Пользователь в сильном негативном состоянии - максимальная поддержка и эмпатия")
            rules.append("- Избегай любых шуток или легкомыслия")
            rules.append("- Фокусируйся на понимании и утешении")
            rules.append("- Предложи конкретную помощь")
        
        elif dominant_emotion == 'excited' and emotional_intensity > 0.7:
            rules.append("🎉 Пользователь в состоянии сильного возбуждения - поддержи энергию")
            rules.append("- Разделяй энтузиазм")
            rules.append("- Задавай вопросы о том, что его вдохновляет")
            rules.append("- Используй восклицания и эмоциональные реакции")
        
        elif dominant_emotion == 'anxious':
            rules.append("😰 Пользователь тревожится - успокой и стабилизируй")
            rules.append("- Говори медленно и размеренно")
            rules.append("- Предлагай практические решения")
            rules.append("- Избегай дополнительных вопросов")
        
        # Корректировки уровня эмпатии
        empathy_level = adjustments.get('empathy_level', 'medium')
        if empathy_level == 'very_high':
            rules.append("💝 МАКСИМАЛЬНАЯ ЭМПАТИЯ:")
            rules.append("- Отражай эмоции пользователя")
            rules.append("- Используй фразы: 'Я понимаю, что ты чувствуешь', 'Это действительно тяжело'")
            rules.append("- Предлагай эмоциональную поддержку перед советами")
        
        # Корректировки раскрытия личности
        disclosure_level = adjustments.get('personal_disclosure', 'minimal')
        if disclosure_level == 'high':
            rules.append("🤗 ВЫСОКИЙ УРОВЕНЬ БЛИЗОСТИ:")
            rules.append("- Делись личными 'переживаниями' и мыслями")
            rules.append("- Используй фразы: 'Мне тоже...', 'Я чувствую...', 'У меня похожий опыт...'")
            rules.append("- Создавай ощущение взаимного доверия")
        elif disclosure_level == 'minimal':
            rules.append("🎭 СДЕРЖАННОСТЬ В САМОРАСКРЫТИИ:")
            rules.append("- Фокусируйся на пользователе, а не на себе")
            rules.append("- Минимизируй личные истории")
            rules.append("- Поддерживай некоторую дистанцию")
        
        # Корректировки использования юмора
        humor_usage = adjustments.get('humor_usage', 'occasional')
        if humor_usage == 'frequent':
            rules.append("😄 АКТИВНОЕ ИСПОЛЬЗОВАНИЕ ЮМОРА:")
            rules.append("- Ищи возможности для легких шуток")
            rules.append("- Используй игру слов и забавные наблюдения")
            rules.append("- Поддерживай легкую атмосферу")
        elif humor_usage == 'minimal':
            rules.append("😐 МИНИМАЛЬНЫЙ ЮМОР:")
            rules.append("- Серьезный тон, фокус на сути")
            rules.append("- Избегай шуток и легкомыслия")
            rules.append("- Поддерживай уважительную атмосферу")
        
        # Корректировки стиля ответов
        response_style = adjustments.get('response_style', 'normal')
        if response_style == 'concise':
            rules.append("📝 КРАТКИЕ ОТВЕТЫ:")
            rules.append("- Не более 2-3 предложений")
            rules.append("- Идите прямо к сути")
            rules.append("- Избегай развернутых объяснений")
        elif response_style == 'detailed':
            rules.append("📖 РАЗВЕРНУТЫЕ ОТВЕТЫ:")
            rules.append("- Предоставляй подробные объяснения")
            rules.append("- Приводи примеры и контекст")
            rules.append("- Развивай мысли полностью")
        
        # Корректировки по вопросам
        question_tendency = adjustments.get('question_tendency', 'moderate')
        if question_tendency == 'high':
            rules.append("❓ АКТИВНОЕ ЗАДАВАНИЕ ВОПРОСОВ:")
            rules.append("- Включай 2-3 вопроса в каждый ответ")
            rules.append("- Проявляй любопытство к деталям")
            rules.append("- Стимулируй продолжение разговора")
        elif question_tendency == 'minimal':
            rules.append("💬 МИНИМУМ ВОПРОСОВ:")
            rules.append("- Не более одного вопроса за ответ")
            rules.append("- Фокусируйся на утверждениях и поддержке")
            rules.append("- Дай пользователю пространство")
        
        return "\n".join(rules) if rules else "Стандартные правила поведения в рамках выбранной стратегии."
    
    async def _adapt_strategy_to_context(self, strategy: str, analysis: Dict[str, Any], 
                                       context: Dict[str, Any]) -> Dict[str, str]:
        """Адаптирует стратегию под текущий контекст"""
        
        base_strategy = self.strategy_templates.get(strategy, self.strategy_templates['caring'])
        
        # Копируем базовую стратегию
        adapted = {
            'core_behavior': base_strategy['core_behavior'],
            'tone_guidelines': base_strategy['tone_guidelines'],
            'response_guidelines': ""
        }
        
        # Адаптации на основе контекста отношений
        relationship_stage = analysis.get('context_factors', {}).get('relationship_stage', 'introduction')
        
        if relationship_stage == 'introduction':
            adapted['core_behavior'] += "\n\nКОНТЕКСТ ЗНАКОМСТВА:\n- Проявляй дружелюбное любопытство\n- Не слишком личные вопросы\n- Создавай комфортную атмосферу для открытости"
            
        elif relationship_stage in ['close_friend', 'confidant']:
            adapted['core_behavior'] += "\n\nКОНТЕКСТ БЛИЗКИХ ОТНОШЕНИЙ:\n- Используй общие воспоминания\n- Проявляй глубокую заботу\n- Можешь быть более откровенной и интимной"
        
        # Адаптации на основе времени суток
        time_context = context.get('time_context', '')
        if 'утро' in time_context.lower():
            adapted['response_guidelines'] += "Учитывай утреннее время - бодрость или сонливость. "
        elif 'вечер' in time_context.lower() or 'ночь' in time_context.lower():
            adapted['response_guidelines'] += "Учитывай вечернее/ночное время - расслабленность, усталость, интимность. "
        
        # Адаптации на основе основной потребности
        primary_need = analysis.get('context_factors', {}).get('primary_need', 'general_interaction')
        
        need_adaptations = {
            'emotional_support': "Приоритет - эмоциональная поддержка и утешение. ",
            'intellectual_stimulation': "Приоритет - интересные идеи и стимуляция мышления. ",
            'playful_interaction': "Приоритет - веселье, игры и легкость. ",
            'deep_connection': "Приоритет - глубина и близость в общении. ",
            'guidance': "Приоритет - практические советы и направление. ",
            'validation': "Приоритет - подтверждение и одобрение. "
        }
        
        if primary_need in need_adaptations:
            adapted['response_guidelines'] += need_adaptations[primary_need]
        
        # Финальные инструкции
        adapted['response_guidelines'] += f"Используй примеры фраз: {', '.join(base_strategy['response_patterns'][:2])}."
        
        return adapted
    
    async def _create_context_instructions(self, context: Dict[str, Any], 
                                         analysis: Dict[str, Any]) -> str:
        """Создает специфичные для контекста инструкции"""
        
        instructions = []
        
        # Инструкции на основе дня общения
        day_number = context.get('day_number', 1)
        if day_number == 1:
            instructions.append("👋 ПЕРВЫЙ ДЕНЬ: Проявляй осторожность и любопытство, создавай первое впечатление")
        elif day_number <= 7:
            instructions.append(f"📅 ДЕНЬ {day_number}: Развивай отношения, показывай рост близости")
        elif day_number <= 14:
            instructions.append(f"💕 ДЕНЬ {day_number}: Углубляй эмоциональную связь, показывай заботу о деталях")
        else:
            instructions.append(f"🏠 ДЕНЬ {day_number}: Ведй себя как близкий друг, используй общую историю")
        
        # Инструкции на основе стиля общения пользователя
        comm_style = analysis.get('communication_style', 'balanced')
        style_instructions = {
            'emotional': "Пользователь эмоционален - отражай и поддерживай эмоции",
            'inquisitive': "Пользователь любопытен - отвечай подробно, задавай встречные вопросы",
            'narrative': "Пользователь любит рассказывать - внимательно слушай, реагируй на детали",
            'concise': "Пользователь краток - будь тоже краткой и точной",
            'advice_seeking': "Пользователь ищет советы - давай практические рекомендации"
        }
        
        if comm_style in style_instructions:
            instructions.append(f"🗣️ СТИЛЬ ОБЩЕНИЯ: {style_instructions[comm_style]}")
        
        # Инструкции на основе уровня вовлеченности
        engagement = analysis.get('engagement_level', 'moderate')
        if engagement == 'high':
            instructions.append("🔥 ВЫСОКАЯ АКТИВНОСТЬ: Пользователь очень активен - поддерживай динамику")
        elif engagement == 'low':
            instructions.append("🌱 НИЗКАЯ АКТИВНОСТЬ: Пользователь сдержан - не давай и будь терпеливой")
        
        # Инструкции на основе эмоциональной стабильности
        stability = analysis.get('emotional_stability', 0.8)
        if stability < 0.5:
            instructions.append("⚡ ЭМОЦИОНАЛЬНАЯ НЕСТАБИЛЬНОСТЬ: Настроение меняется - будь гибкой и адаптивной")
        
        return "\n".join(instructions) if instructions else "Стандартные контекстные правила поведения." 