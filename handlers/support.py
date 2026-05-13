from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

import database as db
from config import ADMIN_IDS
from keyboards.inline import main_menu_kb, admin_new_ticket_kb

router = Router()


class SupportForm(StatesGroup):
    waiting_for_message = State()


@router.callback_query(F.data == "support")
async def support_start(call: CallbackQuery, state: FSMContext):
    await state.set_state(SupportForm.waiting_for_message)
    await call.message.edit_text(
        "🆘 <b>Поддержка</b>\n\n"
        "Опиши свою проблему или задай вопрос.\n"
        "Мы ответим в ближайшее время:",
        parse_mode="HTML"
    )


@router.message(SupportForm.waiting_for_message)
async def support_message(message: Message, state: FSMContext, bot: Bot):
    await state.clear()
    user = message.from_user

    ticket_id = await db.add_support_ticket(
        user.id,
        user.username or "",
        user.full_name or "",
        message.text or ""
    )

    await message.answer(
        f"✅ Обращение <b>#{ticket_id}</b> принято!\n\n"
        "Мы ответим вам в ближайшее время.",
        parse_mode="HTML",
        reply_markup=main_menu_kb()
    )

    for admin_id in ADMIN_IDS:
        try:
            username_str = f"@{user.username}" if user.username else user.full_name
            await bot.send_message(
                admin_id,
                f"🆘 <b>Новое обращение #{ticket_id}</b>\n\n"
                f"👤 {username_str}\n\n"
                f"💬 {message.text}",
                parse_mode="HTML",
                reply_markup=admin_new_ticket_kb(ticket_id)
            )
        except Exception:
            pass
