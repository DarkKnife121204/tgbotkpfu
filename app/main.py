import asyncio
import logging
from logging.handlers import RotatingFileHandler

from app.services.config import cfg
from app.handlers import start, schedule, schedule_buttons
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode


def setup_logging():
    # Создаем папку logs если нет
    import os
    os.makedirs("logs", exist_ok=True)

    handlers = [
        RotatingFileHandler(cfg.log_file, maxBytes=5_000_000, backupCount=5, encoding="utf-8"),
        logging.StreamHandler()
    ]
    logging.basicConfig(
        level=getattr(logging, cfg.log_level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        handlers=handlers
    )
    return logging.getLogger(__name__)


logger = setup_logging()


async def main() -> None:
    logger.info("Запуск бота...")

    bot = Bot(
        token=cfg.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    dp.include_router(start.router)
    dp.include_router(schedule_buttons.router)
    dp.include_router(schedule.router)

    try:
        await dp.start_polling(bot)
    except asyncio.CancelledError:
        logger.warning("Polling остановлен (CancelledError)")
    finally:
        await bot.session.close()
        logger.info("Бот завершил работу.")
