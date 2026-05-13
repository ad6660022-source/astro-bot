from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

ZODIAC_SIGNS: dict[str, tuple[str, str]] = {
    "aries":       ("Овен",      "♈"),
    "taurus":      ("Телец",     "♉"),
    "gemini":      ("Близнецы",  "♊"),
    "cancer":      ("Рак",       "♋"),
    "leo":         ("Лев",       "♌"),
    "virgo":       ("Дева",      "♍"),
    "libra":       ("Весы",      "♎"),
    "scorpio":     ("Скорпион",  "♏"),
    "sagittarius": ("Стрелец",   "♐"),
    "capricorn":   ("Козерог",   "♑"),
    "aquarius":    ("Водолей",   "♒"),
    "pisces":      ("Рыбы",      "♓"),
}


def zodiac_kb(callback_prefix: str) -> InlineKeyboardMarkup:
    signs = list(ZODIAC_SIGNS.items())
    rows = []
    for i in range(0, len(signs), 3):
        row = []
        for key, (name, emoji) in signs[i:i+3]:
            row.append(InlineKeyboardButton(
                text=f"{emoji} {name}",
                callback_data=f"{callback_prefix}_{key}"
            ))
        rows.append(row)
    rows.append([InlineKeyboardButton(text="◀️ Меню", callback_data="back_main")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def main_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔮 Гороскоп сегодня", callback_data="horoscope_today")],
        [InlineKeyboardButton(text="📅 Таро на день", callback_data="daily_tarot_start")],
        [InlineKeyboardButton(text="🎴 Приватный расклад", callback_data="private_reading_start")],
        [InlineKeyboardButton(text="👤 Мой профиль", callback_data="profile")],
        [InlineKeyboardButton(text="🆘 Поддержка", callback_data="support")],
    ])


def back_to_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ В меню", callback_data="back_main")]
    ])


def horoscope_confirm_kb(sign: str) -> InlineKeyboardMarkup:
    name, emoji = ZODIAC_SIGNS[sign]
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"✨ Гороскоп для {emoji} {name}", callback_data=f"horoscope_show_{sign}")],
        [InlineKeyboardButton(text="🔄 Другой знак", callback_data="horoscope_change")],
        [InlineKeyboardButton(text="◀️ Меню", callback_data="back_main")],
    ])


def subscribe_daily_tarot_kb(price: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"⭐ Подписка {price} звёзд / месяц", callback_data="pay_tarot_sub")],
        [InlineKeyboardButton(text="🎁 Приватный расклад — первый бесплатно!", callback_data="private_reading_start")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_main")],
    ])


def private_reading_free_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎁 Использовать бесплатный расклад", callback_data="use_free_tarot")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_main")],
    ])


def pay_private_reading_kb(price: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"💳 Оплатить {price} ⭐", callback_data="pay_private_reading")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_main")],
    ])


def cancel_kb(callback: str = "cancel_fsm") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data=callback)]
    ])


def admin_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Открытые тикеты", callback_data="admin_open_tickets")],
        [InlineKeyboardButton(text="✅ Закрытые тикеты", callback_data="admin_closed_tickets")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats"),
         InlineKeyboardButton(text="💰 Баланс API", callback_data="admin_balance")],
        [InlineKeyboardButton(text="📤 Рассылка", callback_data="admin_broadcast")],
    ])


def admin_tickets_kb(tickets: list, closed: bool = False) -> InlineKeyboardMarkup:
    buttons = []
    for t in tickets:
        name = f"@{t['username']}" if t['username'] else t['full_name'] or "Пользователь"
        preview = t['message'][:25] + ("…" if len(t['message']) > 25 else "")
        buttons.append([InlineKeyboardButton(
            text=f"#{t['id']} {name} — {preview}",
            callback_data=f"admin_ticket_{t['id']}"
        )])
    buttons.append([InlineKeyboardButton(text="◀️ Меню", callback_data="admin_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def admin_ticket_kb(ticket_id: int, answered: bool = False) -> InlineKeyboardMarkup:
    buttons = []
    if not answered:
        buttons.append([
            InlineKeyboardButton(text="✉️ Ответить", callback_data=f"admin_reply_{ticket_id}"),
            InlineKeyboardButton(text="✅ Закрыть", callback_data=f"admin_close_{ticket_id}"),
        ])
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="admin_open_tickets")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def admin_new_ticket_kb(ticket_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📨 Открыть обращение", callback_data=f"admin_ticket_{ticket_id}")]
    ])
