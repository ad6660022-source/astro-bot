from aiogram import Router, F
from aiogram.types import CallbackQuery
from datetime import datetime, timezone

import database as db
from keyboards.inline import zodiac_kb, main_menu_kb, horoscope_confirm_kb, ZODIAC_SIGNS
from services.ai_service import generate_horoscope

router = Router()


@router.callback_query(F.data == "horoscope_today")
async def horoscope_today(call: CallbackQuery):
    user = await db.get_user(call.from_user.id)
    zodiac = user.get("zodiac_sign") if user else None

    if zodiac and zodiac in ZODIAC_SIGNS:
        await call.message.edit_text(
            "🔮 <b>Гороскоп на сегодня</b>",
            parse_mode="HTML",
            reply_markup=horoscope_confirm_kb(zodiac)
        )
    else:
        await call.message.edit_text(
            "🔮 <b>Гороскоп на сегодня</b>\n\nВыбери свой знак зодиака:",
            parse_mode="HTML",
            reply_markup=zodiac_kb("horoscope_show")
        )


@router.callback_query(F.data == "horoscope_change")
async def horoscope_change(call: CallbackQuery):
    await call.message.edit_text(
        "🔮 Выбери знак зодиака:",
        reply_markup=zodiac_kb("horoscope_show")
    )


@router.callback_query(F.data.startswith("horoscope_show_"))
async def horoscope_for_sign(call: CallbackQuery):
    sign = call.data.removeprefix("horoscope_show_")
    if sign not in ZODIAC_SIGNS:
        return
    name, emoji = ZODIAC_SIGNS[sign]
    today = datetime.now(timezone.utc).date().isoformat()

    await db.set_zodiac(call.from_user.id, sign)

    cached = await db.get_horoscope(today, sign)
    if cached:
        await call.message.edit_text(
            f"{emoji} <b>Гороскоп {name} на {today}</b>\n\n{cached}",
            parse_mode="HTML",
            reply_markup=main_menu_kb()
        )
        return

    await call.message.edit_text("⏳ Составляю гороскоп...", reply_markup=None)

    try:
        text, usage = await generate_horoscope(name, today)
        await db.save_horoscope(today, sign, text)
        await db.add_token_usage(usage["input_tokens"], usage["output_tokens"], is_free=True)
    except Exception:
        await call.message.edit_text(
            "⚠️ Ошибка при составлении гороскопа. Попробуй позже.",
            reply_markup=main_menu_kb()
        )
        return

    await call.message.edit_text(
        f"{emoji} <b>Гороскоп {name} на {today}</b>\n\n{text}",
        parse_mode="HTML",
        reply_markup=main_menu_kb()
    )
