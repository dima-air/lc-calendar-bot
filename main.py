import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN
from database import init_db
from handlers import setup_routers


async def main():
    logging.basicConfig(level=logging.INFO)

    # Инициализация БД
    await init_db()

    # Создание бота
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    # Создание диспетчера
    dp = Dispatcher(storage=MemoryStorage())

    # Регистрация роутеров
    dp.include_router(setup_routers())

    print("✅ Бот запущен! Нажмите Ctrl+C для остановки.")

    # Запуск polling
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Бот остановлен.")