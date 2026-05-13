import anthropic
from config import ANTHROPIC_API_KEY, ANTHROPIC_MODEL

client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)


async def generate_horoscope(zodiac_name: str, date_str: str) -> tuple[str, dict]:
    prompt = (
        f"Ты профессиональный астролог с 20-летним опытом. "
        f"Напиши гороскоп для знака {zodiac_name} на {date_str}.\n\n"
        f"Используй HTML-форматирование для Telegram (только тег <b>жирный</b>).\n"
        f"Строго следуй этой структуре:\n\n"
        f"💕 <b>Любовь и отношения</b>\n[2-3 предложения]\n\n"
        f"💼 <b>Карьера и финансы</b>\n[2-3 предложения]\n\n"
        f"🌿 <b>Здоровье</b>\n[2-3 предложения]\n\n"
        f"⚡ <b>Энергия дня</b>\n[1-2 предложения с главным советом]\n\n"
        f"Стиль: мистический, вдохновляющий, конкретный. Пиши по-русски."
    )
    response = await client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=800,
        messages=[{"role": "user", "content": prompt}]
    )
    text = response.content[0].text
    usage = {"input_tokens": response.usage.input_tokens, "output_tokens": response.usage.output_tokens}
    return text, usage


async def generate_daily_tarot(zodiac_name: str, birth_date: str, date_str: str) -> tuple[str, dict]:
    prompt = (
        f"Ты опытный таролог-астролог. Сделай персональный расклад Таро на {date_str}.\n"
        f"Знак зодиака: {zodiac_name}. Дата рождения: {birth_date}.\n\n"
        f"Используй HTML-форматирование (только тег <b>жирный</b>).\n"
        f"Строго следуй этой структуре:\n\n"
        f"🌅 <b>Энергия дня</b> — [Название карты]\n[2-3 предложения о карте применительно к этому человеку]\n\n"
        f"💡 <b>Совет</b> — [Название карты]\n[2-3 предложения что важно сделать или учесть]\n\n"
        f"🎯 <b>Итог дня</b> — [Название карты]\n[2-3 предложения к чему приведёт день]\n\n"
        f"✨ <b>Послание дня</b>\n[1-2 предложения — главная мысль]\n\n"
        f"Учитывай астрологические особенности {zodiac_name}. Пиши по-русски."
    )
    response = await client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=800,
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
            f"\n\nАдаптируй тон под стиль этого человека. Примеры его сообщений:\n{examples}\n"
            f"Неформально — отвечай тепло и живо. Формально — серьёзно."
        )

    prompt = (
        f"Ты опытный таролог. Сделай расклад Таро на ситуацию: «{situation}»\n\n"
        f"Используй HTML-форматирование (только тег <b>жирный</b>).\n"
        f"Строго следуй этой структуре:\n\n"
        f"🌑 <b>Прошлое</b> — [Название карты]\n[2-3 предложения как прошлое влияет на ситуацию]\n\n"
        f"🌕 <b>Настоящее</b> — [Название карты]\n[2-3 предложения что происходит сейчас]\n\n"
        f"🌟 <b>Будущее</b> — [Название карты]\n[2-3 предложения к чему это ведёт]\n\n"
        f"💫 <b>Совет карт</b>\n[2-3 предложения — конкретный практический совет]\n\n"
        f"Будь честен: если карты показывают трудности — скажи мягко, но прямо. "
        f"Пиши по-русски.{style_hint}"
    )
    response = await client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=950,
        messages=[{"role": "user", "content": prompt}]
    )
    text = response.content[0].text
    usage = {"input_tokens": response.usage.input_tokens, "output_tokens": response.usage.output_tokens}
    return text, usage
