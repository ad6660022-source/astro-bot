from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, LabeledPrice, PreCheckoutQuery
from datetime import datetime, timezone, timedelta

import database as db
from config import TAROT_SUB_STARS, PRIVATE_READING_STARS
from keyboards.inline import main_menu_kb

router = Router()


@router.callback_query(F.data == "pay_tarot_sub")
async def pay_tarot_sub(call: CallbackQuery, bot: Bot):
    await bot.send_invoice(
        chat_id=call.from_user.id,
        title="AstroBot — Таро на день",
        description="Персональный расклад каждый день на 30 дней",
        payload="tarot_subscription",
        currency="XTR",
        prices=[LabeledPrice(label="Подписка", amount=TAROT_SUB_STARS)]
    )
    await call.answer()


@router.callback_query(F.data == "pay_private_reading")
async def pay_private_reading(call: CallbackQuery, bot: Bot):
    await bot.send_invoice(
        chat_id=call.from_user.id,
        title="AstroBot — Приватный расклад",
        description="Глубокий расклад Таро на твою ситуацию",
        payload="private_reading",
        currency="XTR",
        prices=[LabeledPrice(label="Расклад", amount=PRIVATE_READING_STARS)]
    )
    await call.answer()


@router.pre_checkout_query()
async def pre_checkout(query: PreCheckoutQuery):
    await query.answer(ok=True)


@router.message(F.successful_payment)
async def successful_payment(message: Message, state: FSMContext):
    payload = message.successful_payment.invoice_payload
    user_id = message.from_user.id

    if payload == "tarot_subscription":
        user = await db.get_user(user_id)
        now = datetime.now(timezone.utc)
        sub_end = user.get("sub_end") if user else None

        if sub_end:
            sub_dt = datetime.fromisoformat(sub_end)
            if sub_dt.tzinfo is None:
                sub_dt = sub_dt.replace(tzinfo=timezone.utc)
            new_end = (sub_dt if sub_dt > now else now) + timedelta(days=30)
        else:
            new_end = now + timedelta(days=30)

        await db.set_subscription(user_id, new_end)
        await message.answer(
            "🎉 <b>Подписка активирована!</b>\n\n"
            f"📅 Таро на день доступно до <b>{new_end.strftime('%d.%m.%Y')}</b>\n\n"
            "Нажми «Таро на день» чтобы получить расклад:",
            parse_mode="HTML",
            reply_markup=main_menu_kb()
        )

    elif payload == "private_reading":
        from handlers.tarot import TarotState
        await state.set_state(TarotState.waiting_for_private_situation)
        await message.answer(
            "✅ <b>Оплачено!</b>\n\n"
            "🎴 Опиши свою ситуацию или задай вопрос.\n"
            "Чем подробнее — тем точнее будет расклад:",
            parse_mode="HTML"
        )
