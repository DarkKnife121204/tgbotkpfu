from aiogram import Router, types
from aiogram.filters import Command
import logging

logger = logging.getLogger(__name__)
router = Router()

@router.message(Command("start"))
async def cmd_start(m: types.Message):
    logger.info("Пользователь %s вызвал /start", m.from_user.id)
    await m.answer(
        "Привет! Я бот расписания КФУ.\n"
        "Команды:\n"
        "• /schedule <группа> — показать расписание группы"
    )
