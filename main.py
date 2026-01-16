import asyncio
import logging
import os
import sys
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv  # Импортируем функцию загрузки

# Импорты ваших модулей (предполагается, что эти файлы существуют в папке)
import database as db
from handlers import router

# Загружаем переменные из файла .env в окружение
load_dotenv()

# Теперь os.getenv будет искать переменную сначала в системе, потом в .env
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

async def main():
    if not TOKEN:
        print("ОШИБКА: Переменная TELEGRAM_BOT_TOKEN не найдена.")
        print("Пожалуйста, создайте файл .env и укажите там токен: TELEGRAM_BOT_TOKEN=ваш_токен")
        return
    
    # Настройка логов
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    
    # Инициализация БД
    try:
        await db.init_db()
    except Exception as e:
        logging.error(f"Ошибка при инициализации базы данных: {e}")
        # Можно добавить return, если БД критична для запуска
    
    bot = Bot(token=TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    
    dp.include_router(router)

    await bot.delete_webhook(drop_pending_updates=True)
    print("Бот успешно запущен и читает токен из .env!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен")
