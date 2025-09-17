import logging
from aiogram import Router, types
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder

router = Router()
logger = logging.getLogger(__name__)


@router.message(Command("start"))
async def cmd_start(message: types.Message) -> None:
    keyboard = (
        ReplyKeyboardBuilder()
        .add(types.KeyboardButton(text="📅 Расписание"))
        .as_markup(resize_keyboard=True)
    )

    await message.answer(
        "👋 Добро пожаловать в бот расписания КФУ!\n"
        "Нажмите кнопку ниже, чтобы посмотреть расписание.",
        reply_markup=keyboard,
    )


@router.message(lambda message: message.text == "📅 Расписание")
async def handle_schedule_button(message: types.Message) -> None:
    logger.info("Пользователь %s запросил расписание", message.from_user.id)
    await message.answer(
        "Введите номер группы:\nПример: 09-825, 8251160, 8251",
        reply_markup=types.ReplyKeyboardRemove(),
    )
