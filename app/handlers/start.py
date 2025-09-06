from aiogram import Router, types
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder

router = Router()


@router.message(Command("start"))
async def cmd_start(message: types.Message):
    builder = ReplyKeyboardBuilder()
    builder.add(types.KeyboardButton(text="📅 Расписание"))
    builder.adjust(1)

    await message.answer(
        "👋 Добро пожаловать в бот расписания КФУ!\n"
        "Нажмите кнопку ниже чтобы посмотреть расписание",
        reply_markup=builder.as_markup(resize_keyboard=True)
    )


@router.message(lambda message: message.text == "📅 Расписание")
async def handle_schedule_button(message: types.Message):
    await message.answer(
        "Введите номер группы:\n"
        "Пример: 09-825, 8251160, 8251",
        reply_markup=types.ReplyKeyboardRemove()
    )