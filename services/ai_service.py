import anthropic
from config import ANTHROPIC_API_KEY, ANTHROPIC_MODEL

client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)


async def generate_horoscope(zodiac_name: str, date_str: str) -> tuple[str, dict]:
    prompt = (
        f"Ты профессиональный астролог с 20-летним опытом. "
        f"Напиши детальный гороскоп для знака зодиака {zodiac_name} на {date_str}.\n\n"
        f"Стиль: мистический, вдохновляющий, конкретный и практичный.\n"
        f"Охвати: любовь и отношения, карьеру и финансы, здоровье, общий энергетический прогноз.\n"
        f"Объём: 200-250 слов. Пиши по-русски. Не используй HTML-теги."
    )
    response = await client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=700,
        messages=[{"role": "user", "content": prompt}]
    )
    text = response.content[0].text
    usage = {"input_tokens": response.usage.input_tokens, "output_tokens": response.usage.output_tokens}
    return text, usage


async def generate_daily_tarot(zodiac_name: str, birth_date: str, date_str: str) -> tuple[str, dict]:
    prompt = (
        f"Ты опытный таролог-астролог. "
        f"Сделай персональный расклад Таро на {date_str} для человека:\n"
        f"- Знак зодиака: {zodiac_name}\n"
        f"- Дата рождения: {birth_date}\n\n"
        f"Выбери 3 карты Таро из Старших Арканов:\n"
        f"1. Энергия дня — карта, описывающая общую атмосферу\n"
        f"2. Совет — что важно сделать или учесть\n"
        f"3. Итог — к чему приведёт день\n\n"
        f"Учитывай астрологические особенности {zodiac_name} и числовую вибрацию даты рождения. "
        f"Дай конкретные рекомендации на сегодня.\n"
        f"Объём: 200-250 слов. Пиши по-русски. Не используй HTML-теги."
    )
    response = await client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=700,
        messages=[{"role": "user", "content": prompt}]
    )
    text = response.content[0].text
    usage = {"input_tokens": response.usage.input_tokens, "output_tokens": response.usage.output_tokens}
    return text, usage


async def generate_private_tarot(situation: str, user_messages: list[str]) -> tuple[str, dict]:
    style_hint = ""
    if user_messages:
        examples = "\n".join(f"- «{m}»" for m in user_messages)
        style_hint = (
            f"\n\nАдаптируй тон и стиль ответа под манеру общения этого человека. "
            f"Примеры его сообщений:\n{examples}\n"
            f"Если человек пишет неформально — отвечай живо и тепло. "
            f"Если формально — сохраняй серьёзный тон."
        )

    prompt = (
        f"Ты опытный таролог с глубоким интуитивным даром. "
        f"Сделай глубокий расклад Таро «Прошлое — Настоящее — Будущее» на ситуацию:\n\n"
        f"«{situation}»\n\n"
        f"Выбери три карты Таро из Старших Арканов. Для каждой:\n"
        f"- Назови карту и её позицию\n"
        f"- Объясни значение применительно к описанной ситуации\n\n"
        f"Завершив карты, дай общий вывод и конкретный практический совет. "
        f"Будь честен — если карты показывают сложности, скажи об этом мягко но прямо.\n"
        f"Объём: 280-330 слов. Пиши по-русски.{style_hint}"
    )
    response = await client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=950,
        messages=[{"role": "user", "content": prompt}]
    )
    text = response.content[0].text
    usage = {"input_tokens": response.usage.input_tokens, "output_tokens": response.usage.output_tokens}
    return text, usage
