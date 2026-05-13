import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN
import database as db
from handlers import admin_panel, start, horoscope, tarot, payment, support

logging.basicConfig(level=logging.INFO)


async def main():
    await db.init_db()
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(admin_panel.router)
    dp.include_router(start.router)
    dp.include_router(horoscope.router)
    dp.include_router(tarot.router)
    dp.include_router(payment.router)
    dp.include_router(support.router)

    print("AstroBot started!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
