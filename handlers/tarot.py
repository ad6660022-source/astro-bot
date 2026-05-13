from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from datetime import datetime, timezone

import database as db
from config import TAROT_SUB_STARS, PRIVATE_READING_STARS
from keyboards.inline import (
    main_menu_kb, subscribe_daily_tarot_kb, pay_private_reading_kb,
    private_reading_free_kb, cancel_kb, ZODIAC_SIGNS
)
from services.ai_service import generate_daily_tarot, generate_private_tarot

router = Router()


class TarotState(StatesGroup):
    waiting_for_birth_date = State()
    waiting_for_private_situation = State()
    waiting_for_private_situation_paid = State()


def get_level(readings: int) -> str:
    if readings == 0:
        return "🌱 Новичок"
    elif readings <= 3:
        return "⭐ Начинающий астролог"
    elif readings <= 10:
        return "🌙 Искатель знаний"
    elif readings <= 25:
        return "🔮 Практикующий таролог"
    elif readings <= 50:
        return "🌟 Опытный таролог"
    elif readings <= 100:
        return "🪄 Мастер Таро"
    else:
        return "👑 Великий Оракул"


def get_next_level_info(readings: int) -> str:
    thresholds = [(3, "Начинающий астролог"), (10, "Искатель знаний"),
                  (25, "Практикующий таролог"), (50, "Опытный таролог"),
                  (100, "Мастер Таро")]
    for threshold, name in thresholds:
        if readings < threshold:
            return f"{threshold - readings} раскладов до уровня «{name}»"
    return "Максимальный уровень достигнут ✨"


# ── Таро на день (подписка) ───────────────────────────────────

@router.callback_query(F.data == "daily_tarot_start")
async def daily_tarot_start(call: CallbackQuery, state: FSMContext):
    user = await db.get_user(call.from_user.id)
    subscribed = _is_subscribed(user)

    if not subscribed:
        await call.message.edit_text(
            "📅 <b>Таро на день</b>\n\n"
            "Каждый день — персональный расклад из 3 карт на основе твоего знака "
            "и даты рождения. Генерируется один раз, остаётся неизменным.\n\n"
            f"⭐ Подписка: <b>{TAROT_SUB_STARS} звёзд / месяц</b>",
            parse_mode="HTML",
            reply_markup=subscribe_daily_tarot_kb(TAROT_SUB_STARS)
        )
        return

    birth_date = user.get("birth_date") if user else None
    if not birth_date:
        await state.set_state(TarotState.waiting_for_birth_date)
        await call.message.edit_text(
            "📅 <b>Таро на день</b>\n\n"
            "Для персонального расклада нужна дата рождения.\n\n"
            "✏️ Введи в формате <b>ДД.ММ.ГГГГ</b>\n"
            "Например: <code>15.03.1995</code>",
            parse_mode="HTML",
            reply_markup=cancel_kb("cancel_fsm")
        )
        return

    await _show_daily_tarot(call, user, birth_date)


@router.message(TarotState.waiting_for_birth_date)
async def set_birth_date(message: Message, state: FSMContext):
    text = (message.text or "").strip()
    try:
        datetime.strptime(text, "%d.%m.%Y")
    except ValueError:
        await message.answer(
            "⚠️ Неверный формат.\n\n"
            "Введи дату как <code>ДД.ММ.ГГГГ</code>, например: <code>15.03.1995</code>",
            parse_mode="HTML",
            reply_markup=cancel_kb("cancel_fsm")
        )
        return

    await state.clear()
    await db.set_birth_date(message.from_user.id, text)
    user = await db.get_user(message.from_user.id)
    await _show_daily_tarot_message(message, user, text)


async def _show_daily_tarot(call: CallbackQuery, user: dict, birth_date: str):
    today = datetime.now(timezone.utc).date().isoformat()
    cached = await db.get_daily_tarot(call.from_user.id, today)

    zodiac = user.get("zodiac_sign", "")
    zodiac_name = ZODIAC_SIGNS[zodiac][0] if zodiac in ZODIAC_SIGNS else "неизвестный знак"
    zodiac_emoji = ZODIAC_SIGNS[zodiac][1] if zodiac in ZODIAC_SIGNS else "🔮"

    if cached:
        await call.message.edit_text(
            f"📅 <b>Таро на день</b>  {zodiac_emoji} {zodiac_name}\n\n{cached}",
            parse_mode="HTML",
            reply_markup=main_menu_kb()
        )
        return

    await call.message.edit_text("🔮 Раскладываю карты на сегодня...", reply_markup=None)
    await _generate_and_show_daily(call.message, call.from_user.id, zodiac_name, zodiac_emoji, birth_date, today)


async def _show_daily_tarot_message(message: Message, user: dict, birth_date: str):
    today = datetime.now(timezone.utc).date().isoformat()
    zodiac = user.get("zodiac_sign", "") if user else ""
    zodiac_name = ZODIAC_SIGNS[zodiac][0] if zodiac in ZODIAC_SIGNS else "неизвестный знак"
    zodiac_emoji = ZODIAC_SIGNS[zodiac][1] if zodiac in ZODIAC_SIGNS else "🔮"

    thinking = await message.answer("🔮 Раскладываю карты на сегодня...")
    await _generate_and_show_daily(thinking, message.from_user.id, zodiac_name, zodiac_emoji, birth_date, today)


async def _generate_and_show_daily(msg, user_id: int, zodiac_name: str, zodiac_emoji: str, birth_date: str, today: str):
    try:
        text, usage = await generate_daily_tarot(zodiac_name, birth_date, today)
        await db.save_daily_tarot(user_id, today, text)
        await db.add_token_usage(usage["input_tokens"], usage["output_tokens"], is_free=False)
        await db.increment_readings(user_id)
    except Exception:
        await msg.edit_text("⚠️ Ошибка. Попробуй позже.", reply_markup=main_menu_kb())
        return

    await msg.edit_text(
        f"📅 <b>Таро на день</b>  {zodiac_emoji} {zodiac_name}\n\n{text}",
        parse_mode="HTML",
        reply_markup=main_menu_kb()
    )


# ── Приватный расклад ─────────────────────────────────────────

@router.callback_query(F.data == "private_reading_start")
async def private_reading_start(call: CallbackQuery):
    today = datetime.now(timezone.utc).date().isoformat()
    free_used = await db.get_free_tarot_used(call.from_user.id, today)

    if not free_used:
        await call.message.edit_text(
            "🎴 <b>Приватный расклад</b>\n\n"
            "🎁 Сегодня у тебя есть <b>бесплатный расклад</b>!\n\n"
            "Получишь глубокий анализ своей ситуации:\n"
            "🌑 Прошлое  •  🌕 Настоящее  •  🌟 Будущее  •  💫 Совет",
            parse_mode="HTML",
            reply_markup=private_reading_free_kb()
        )
    else:
        await call.message.edit_text(
            "🎴 <b>Приватный расклад</b>\n\n"
            "Глубокий анализ твоей ситуации:\n"
            "🌑 Прошлое  •  🌕 Настоящее  •  🌟 Будущее  •  💫 Совет\n\n"
            "🆓 Бесплатный расклад сегодня уже использован\n"
            f"💳 Стоимость: <b>{PRIVATE_READING_STARS} звёзд</b>",
            parse_mode="HTML",
            reply_markup=pay_private_reading_kb(PRIVATE_READING_STARS)
        )


@router.callback_query(F.data == "use_free_tarot")
async def use_free_tarot(call: CallbackQuery, state: FSMContext):
    await state.set_state(TarotState.waiting_for_private_situation)
    await call.message.edit_text(
        "🎴 <b>Приватный расклад</b>  🎁 бесплатный\n\n"
        "Расскажи свою ситуацию или задай вопрос.\n"
        "Чем подробнее — тем точнее расклад:",
        parse_mode="HTML",
        reply_markup=cancel_kb("cancel_fsm")
    )


@router.message(TarotState.waiting_for_private_situation)
async def private_situation_free(message: Message, state: FSMContext):
    await state.clear()
    situation = message.text or ""
    today = datetime.now(timezone.utc).date().isoformat()

    await db.mark_free_tarot_used(message.from_user.id, today)
    await db.add_user_message(message.from_user.id, situation)
    user_messages = await db.get_user_messages(message.from_user.id, 5)

    thinking = await message.answer("🔮 Читаю карты...")

    try:
        text, usage = await generate_private_tarot(situation, user_messages)
        await db.add_token_usage(usage["input_tokens"], usage["output_tokens"], is_free=True)
        await db.increment_readings(message.from_user.id)
    except Exception:
        await thinking.edit_text("⚠️ Ошибка. Попробуй ещё раз.", reply_markup=main_menu_kb())
        return

    await thinking.edit_text(
        f"🎴 <b>Приватный расклад</b>\n\n{text}",
        parse_mode="HTML",
        reply_markup=main_menu_kb()
    )


@router.message(TarotState.waiting_for_private_situation_paid)
async def private_situation_paid(message: Message, state: FSMContext):
    await state.clear()
    situation = message.text or ""

    await db.add_user_message(message.from_user.id, situation)
    user_messages = await db.get_user_messages(message.from_user.id, 5)

    thinking = await message.answer("🔮 Читаю карты...")

    try:
        text, usage = await generate_private_tarot(situation, user_messages)
        await db.add_token_usage(usage["input_tokens"], usage["output_tokens"], is_free=False)
        await db.increment_readings(message.from_user.id)
    except Exception:
        await thinking.edit_text("⚠️ Ошибка. Попробуй ещё раз.", reply_markup=main_menu_kb())
        return

    await thinking.edit_text(
        f"🎴 <b>Приватный расклад</b>\n\n{text}",
        parse_mode="HTML",
        reply_markup=main_menu_kb()
    )


# ── Отмена FSM ────────────────────────────────────────────────

@router.callback_query(F.data == "cancel_fsm")
async def cancel_fsm(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text(
        "Главное меню — выбери действие:",
        reply_markup=main_menu_kb()
    )


# ── Вспомогательная функция ───────────────────────────────────

def _is_subscribed(user: dict | None) -> bool:
    if not user:
        return False
    sub_end = user.get("sub_end")
    if not sub_end:
        return False
    sub_dt = datetime.fromisoformat(sub_end)
    if sub_dt.tzinfo is None:
        sub_dt = sub_dt.replace(tzinfo=timezone.utc)
    return sub_dt > datetime.now(timezone.utc)
