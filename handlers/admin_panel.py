from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery
from datetime import datetime, timezone

import database as db
from config import ADMIN_IDS
from keyboards.inline import admin_menu_kb, admin_tickets_kb, admin_ticket_kb

router = Router()

PRICE_INPUT_PER_M = 0.80
PRICE_OUTPUT_PER_M = 4.00
USD_TO_RUB = 90


class AdminStates(StatesGroup):
    waiting_for_reply = State()
    waiting_for_broadcast = State()


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


@router.message(Command("admin"))
async def cmd_admin(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.clear()
    await message.answer("🛠 <b>Админ-панель AstroBot</b>", parse_mode="HTML", reply_markup=admin_menu_kb())


@router.callback_query(F.data == "admin_menu")
async def admin_menu_cb(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return
    await state.clear()
    await call.message.edit_text("🛠 <b>Админ-панель AstroBot</b>", parse_mode="HTML", reply_markup=admin_menu_kb())


@router.callback_query(F.data == "admin_open_tickets")
async def admin_open_tickets(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    tickets = await db.get_open_tickets(20)
    if not tickets:
        await call.message.edit_text("✅ Открытых обращений нет.", reply_markup=admin_menu_kb())
        return
    await call.message.edit_text(
        f"📋 <b>Открытые обращения: {len(tickets)}</b>\n\nВыбери для просмотра:",
        parse_mode="HTML",
        reply_markup=admin_tickets_kb(tickets)
    )


@router.callback_query(F.data == "admin_closed_tickets")
async def admin_closed_tickets(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    tickets = await db.get_closed_tickets(20)
    if not tickets:
        await call.message.edit_text("Закрытых обращений пока нет.", reply_markup=admin_menu_kb())
        return
    await call.message.edit_text(
        f"✅ <b>Закрытые обращения: {len(tickets)}</b>",
        parse_mode="HTML",
        reply_markup=admin_tickets_kb(tickets, closed=True)
    )


@router.callback_query(F.data.startswith("admin_ticket_"))
async def admin_view_ticket(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    ticket_id = int(call.data.split("_")[-1])
    ticket = await db.get_ticket(ticket_id)
    if not ticket:
        await call.answer("Тикет не найден", show_alert=True)
        return

    name = ticket['full_name'] or "Пользователь"
    username_str = f"@{ticket['username']}" if ticket['username'] else "нет username"
    status = "✅ Закрыт" if ticket['answered'] else "🔴 Открыт"
    created = ticket['created_at'][:16].replace("T", " ")

    await call.message.edit_text(
        f"📨 <b>Обращение #{ticket_id}</b>  {status}\n\n"
        f"👤 {name} ({username_str})\n"
        f"🆔 <code>{ticket['user_id']}</code>\n"
        f"🕐 {created}\n\n"
        f"💬 <b>Сообщение:</b>\n{ticket['message']}",
        parse_mode="HTML",
        reply_markup=admin_ticket_kb(ticket_id, answered=bool(ticket['answered']))
    )


@router.callback_query(F.data.startswith("admin_reply_"))
async def admin_reply_start(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return
    ticket_id = int(call.data.split("_")[-1])
    ticket = await db.get_ticket(ticket_id)
    if not ticket:
        await call.answer("Тикет не найден", show_alert=True)
        return

    await state.set_state(AdminStates.waiting_for_reply)
    await state.update_data(ticket_id=ticket_id, user_id=ticket["user_id"])
    await call.message.edit_text(
        f"✉️ <b>Ответ на обращение #{ticket_id}</b>\n\n"
        f"Напиши текст ответа пользователю:",
        parse_mode="HTML"
    )


@router.message(AdminStates.waiting_for_reply)
async def admin_reply_send(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    ticket_id = data["ticket_id"]
    user_id = data["user_id"]
    await state.clear()

    try:
        await bot.send_message(
            user_id,
            f"📩 <b>Ответ от поддержки по обращению #{ticket_id}:</b>\n\n{message.text}",
            parse_mode="HTML"
        )
        await db.mark_ticket_answered(ticket_id)
        await message.answer(
            f"✅ Ответ отправлен по обращению #{ticket_id}.",
            reply_markup=admin_menu_kb()
        )
    except Exception:
        await message.answer(
            "❌ Не удалось отправить — пользователь заблокировал бота.",
            reply_markup=admin_menu_kb()
        )


@router.callback_query(F.data.startswith("admin_close_"))
async def admin_close_ticket(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    ticket_id = int(call.data.split("_")[-1])
    await db.mark_ticket_answered(ticket_id)
    await call.answer(f"Обращение #{ticket_id} закрыто")
    tickets = await db.get_open_tickets(20)
    await call.message.edit_text(
        f"📋 <b>Открытые обращения: {len(tickets)}</b>\n\nВыбери для просмотра:" if tickets else "✅ Открытых обращений нет.",
        parse_mode="HTML",
        reply_markup=admin_tickets_kb(tickets) if tickets else admin_menu_kb()
    )


@router.callback_query(F.data == "admin_stats")
async def admin_stats(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    stats = await db.get_stats()
    open_tickets = await db.get_open_tickets(100)
    await call.message.edit_text(
        f"📊 <b>Статистика AstroBot</b>\n\n"
        f"👥 Всего пользователей: <b>{stats['total']}</b>\n"
        f"💳 Активных подписок: <b>{stats['active_subs']}</b>\n"
        f"💰 Доход в месяц: ~<b>{stats['active_subs'] * 175} руб</b>\n"
        f"🔮 Гороскопов сгенерировано: <b>{stats['horoscopes']}</b>\n"
        f"📅 Раскладов «на день»: <b>{stats.get('daily_tarots', 0)}</b>\n"
        f"🆘 Открытых тикетов: <b>{len(open_tickets)}</b>",
        parse_mode="HTML",
        reply_markup=admin_menu_kb()
    )


@router.callback_query(F.data == "admin_balance")
async def admin_balance(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    this_month = datetime.now(timezone.utc).strftime("%Y-%m")
    usage = await db.get_token_usage(this_month)

    inp = usage["input_tokens"]
    out = usage["output_tokens"]
    reqs = usage["requests"]
    f_inp = usage["free_input"]
    f_out = usage["free_output"]
    f_reqs = usage["free_requests"]
    p_reqs = reqs - f_reqs

    def cost_rub(i, o):
        return ((i / 1_000_000 * PRICE_INPUT_PER_M) + (o / 1_000_000 * PRICE_OUTPUT_PER_M)) * USD_TO_RUB

    total_cost = cost_rub(inp, out)
    free_cost = cost_rub(f_inp, f_out)
    paid_cost = total_cost - free_cost
    avg = (total_cost / reqs) if reqs > 0 else 0

    await call.message.edit_text(
        f"💰 <b>Расход API — {this_month}</b>\n\n"
        f"📊 Всего запросов: <b>{reqs:,}</b>\n"
        f"├ 🔮 Гороскопы (бесплатно): <b>{f_reqs:,}</b> (~<b>{free_cost:.0f} руб</b>)\n"
        f"└ 🃏 Таро (платные): <b>{p_reqs:,}</b> (~<b>{paid_cost:.0f} руб</b>)\n\n"
        f"🔤 Токенов входящих: <b>{inp:,}</b>\n"
        f"🔤 Токенов исходящих: <b>{out:,}</b>\n\n"
        f"💵 Итого: <b>{total_cost:.0f} руб</b>\n"
        f"📈 Среднее за запрос: <b>{avg:.2f} руб</b>",
        parse_mode="HTML",
        reply_markup=admin_menu_kb()
    )


@router.callback_query(F.data == "admin_broadcast")
async def admin_broadcast_start(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return
    await state.set_state(AdminStates.waiting_for_broadcast)
    await call.message.edit_text(
        "📤 <b>Рассылка</b>\n\n"
        "Напиши текст сообщения для всех пользователей.\n"
        "Поддерживается HTML-форматирование (<b>жирный</b>, <i>курсив</i>).",
        parse_mode="HTML"
    )


@router.message(AdminStates.waiting_for_broadcast)
async def admin_broadcast_send(message: Message, state: FSMContext, bot: Bot):
    await state.clear()
    text = message.text or ""
    user_ids = await db.get_all_user_ids()

    status = await message.answer(f"📤 Отправляю {len(user_ids)} пользователям...")
    sent, failed = 0, 0

    for uid in user_ids:
        if uid in ADMIN_IDS:
            continue
        try:
            await bot.send_message(uid, text, parse_mode="HTML")
            sent += 1
        except Exception:
            failed += 1

    await status.edit_text(
        f"✅ <b>Рассылка завершена</b>\n\n"
        f"📨 Отправлено: <b>{sent}</b>\n"
        f"❌ Не доставлено: <b>{failed}</b>",
        parse_mode="HTML"
    )
