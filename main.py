import asyncio
import logging
import os
import sys
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

import database as db
from handlers import router

TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')

async def main():
    if not TOKEN:
        print("ERROR: TELEGRAM_BOT_TOKEN environment variable not set")
        print("Please set your Telegram bot token in the Secrets tab")
        return
    
    # Настройка логов
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    
    # Инициализация БД
    await db.init_db()
    
    bot = Bot(token=TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    
    dp.include_router(router)

    await bot.delete_webhook(drop_pending_updates=True)
    print("Бот успешно запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен")


