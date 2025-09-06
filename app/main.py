import asyncio
import logging

from aiogram import Bot, Dispatcher

from app.config import cfg
from app.handlers import start, schedule, schedule_buttons


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)

logger = logging.getLogger(__name__)

bot = Bot(cfg.bot_token)
dp = Dispatcher()

dp.include_router(start.router)
dp.include_router(schedule_buttons.router)
dp.include_router(schedule.router)


async def main() -> None:
    logger.info("Запускаем бота...")
    try:
        await dp.start_polling(bot)
    except asyncio.CancelledError:
        logger.info("Polling остановлен (CancelledError)")
    finally:
        logger.info("Бот завершил работу.")
