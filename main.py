import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import Config, load_config
from database import Database
from handlers.admin import router as admin_router
from handlers.user import router as user_router
from middlewares.db import DbMiddleware


def setup_logging(log_file: str) -> None:
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Har doim console (stdout) ga chiqaradi — cloud platformalar uchun muhim
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    root_logger.handlers.clear()
    root_logger.addHandler(console_handler)

    # Agar LOG_FILE env o'rnatilgan bo'lsa, faylga ham yozadi
    if log_file:
        try:
            file_handler = logging.FileHandler(log_file, encoding="utf-8")
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
        except OSError as e:
            logging.getLogger(__name__).warning(
                "Log fayli ochilmadi (%s): %s — faqat consolega chiqariladi", log_file, e
            )


async def on_startup(db: Database) -> None:
    await db.init()
    logging.getLogger(__name__).info("Database initialized — path: %s", db.path)


async def run_bot(config: Config) -> None:
    setup_logging(config.log_file)
    db = Database(config.db_path)
    await on_startup(db)

    bot = Bot(
        token=config.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())
    dp.update.middleware(DbMiddleware(db))

    dp.include_router(admin_router)
    dp.include_router(user_router)

    logging.getLogger(__name__).info("Bot ishga tushdi (polling mode)")
    try:
        await dp.start_polling(bot, config=config)
    finally:
        await bot.session.close()
        logging.getLogger(__name__).info("Bot to'xtatildi")


def main() -> None:
    config = load_config()
    asyncio.run(run_bot(config))


if __name__ == "__main__":
    main()
