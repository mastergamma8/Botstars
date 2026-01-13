import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

import database as db
from handlers import router

# ⚠️ ВСТАВЬ СВОЙ ТОКЕН СЮДА
TOKEN = '7225900512:AAFKfTU5UcE5qTBh6iKmIwlMDFzXnKTGuIw'

async def main():
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


