from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from datetime import datetime, timezone

import database as db
from config import ADMIN_IDS
from keyboards.inline import main_menu_kb, zodiac_kb, admin_menu_kb, ZODIAC_SIGNS

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    user = message.from_user
    await db.create_user(user.id, user.username or "", user.full_name or "")

    if user.id in ADMIN_IDS:
        await message.answer(
            f"👋 Привет, <b>{user.first_name}</b>!\n\n"
            "🛠 Ты вошёл как <b>администратор</b>.",
            parse_mode="HTML",
            reply_markup=admin_menu_kb()
        )
        return

    db_user = await db.get_user(user.id)
    if db_user and db_user.get("zodiac_sign"):
        sign = db_user["zodiac_sign"]
        name, emoji = ZODIAC_SIGNS[sign]
        await message.answer(
            f"✨ Привет, <b>{user.first_name}</b>!\n\n"
            f"Твой знак: {emoji} <b>{name}</b>\n\n"
            f"Что хочешь узнать сегодня?",
            parse_mode="HTML",
            reply_markup=main_menu_kb()
        )
    else:
        await message.answer(
            f"✨ Привет, <b>{user.first_name}</b>!\n\n"
            "Я <b>AstroBot</b> — твой персональный астролог и таролог.\n\n"
            "🔮 <b>Бесплатно:</b> ежедневный гороскоп\n"
            "📅 <b>Подписка:</b> персональное Таро на день\n"
            "🎴 <b>Разово:</b> приватный расклад за 50 ⭐\n\n"
            "Для начала выбери свой знак зодиака:",
            parse_mode="HTML",
            reply_markup=zodiac_kb("set_zodiac")
        )


@router.callback_query(F.data.startswith("set_zodiac_"))
async def set_zodiac(call: CallbackQuery):
    sign = call.data.removeprefix("set_zodiac_")
    if sign not in ZODIAC_SIGNS:
        return
    name, emoji = ZODIAC_SIGNS[sign]
    await db.set_zodiac(call.from_user.id, sign)
    await call.message.edit_text(
        f"✨ Отлично! Твой знак — {emoji} <b>{name}</b>\n\n"
        "Теперь выбери что хочешь сделать:",
        parse_mode="HTML",
        reply_markup=main_menu_kb()
    )


@router.callback_query(F.data == "back_main")
async def back_main(call: CallbackQuery):
    await call.message.edit_text(
        "Главное меню — выбери действие:",
        reply_markup=main_menu_kb()
    )


@router.callback_query(F.data == "profile")
async def show_profile(call: CallbackQuery):
    from handlers.tarot import get_level, get_next_level_info
    user_data = await db.get_user(call.from_user.id)
    if not user_data:
        await call.answer("Профиль не найден", show_alert=True)
        return

    zodiac = user_data.get("zodiac_sign")
    zodiac_str = (
        f"{ZODIAC_SIGNS[zodiac][1]} {ZODIAC_SIGNS[zodiac][0]}"
        if zodiac and zodiac in ZODIAC_SIGNS else "не выбран"
    )

    birth_date = user_data.get("birth_date") or "не указана"

    sub_end = user_data.get("sub_end")
    if sub_end:
        sub_dt = datetime.fromisoformat(sub_end)
        if sub_dt.tzinfo is None:
            sub_dt = sub_dt.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        if sub_dt > now:
            days = (sub_dt - now).days
            sub_status = f"✅ Активна ещё <b>{days} дн.</b>"
        else:
            sub_status = "❌ Истекла"
    else:
        sub_status = "❌ Не оформлена"

    readings = user_data.get("readings_count") or 0
    level = get_level(readings)
    next_level = get_next_level_info(readings)

    await call.message.edit_text(
        f"👤 <b>Профиль</b>\n\n"
        f"✨ Уровень: <b>{level}</b>\n"
        f"🃏 Раскладов сделано: <b>{readings}</b>\n"
        f"📈 <i>{next_level}</i>\n\n"
        f"Знак зодиака: {zodiac_str}\n"
        f"Дата рождения: {birth_date}\n"
        f"Подписка «Таро на день»: {sub_status}",
        parse_mode="HTML",
        reply_markup=main_menu_kb()
    )
