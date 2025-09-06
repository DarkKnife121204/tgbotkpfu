from aiogram import Router, types
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Tuple

from app.config import cfg
from app.services.google_csv import find_group_schedule
from app.services.parser import parse_schedule

router = Router()
log = logging.getLogger(__name__)

# Храним последние найденные расписания и группы по пользователям
# Формат: {user_id: (group_name, lessons)}
user_data: Dict[int, Tuple[str, List[dict]]] = {}


def get_schedule_keyboard():
    """Клавиатура для выбора периода"""
    builder = ReplyKeyboardBuilder()
    builder.add(types.KeyboardButton(text="📅 Сегодня"))
    builder.add(types.KeyboardButton(text="📅 Завтра"))
    builder.add(types.KeyboardButton(text="📋 Вся неделя"))
    builder.add(types.KeyboardButton(text="🔍 Другая группа"))
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)


def get_day_name(day_offset: int = 0) -> str:
    """Получение названия дня недели"""
    days = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
    today = datetime.now() + timedelta(days=day_offset)
    return days[today.weekday()]


def filter_lessons_by_day(lessons: List[dict], day_name: str) -> List[dict]:
    """Фильтрация занятий по дню недели"""
    return [lesson for lesson in lessons if lesson.get("day") == day_name]


def format_day_schedule(lessons: List[dict], day_name: str, group: str) -> str:
    """Старый дизайн без эмодзи и лишних отступов"""
    if not lessons:
        return f"<b>{day_name}</b>\n\nЗанятий нет\n"

    lessons.sort(key=lambda x: x.get("time", ""))

    result = f"<b>{day_name}</b>\n\n"
    for lesson in lessons:
        time_ = lesson.get('time', '')
        week = lesson.get('week_type', '')
        subject = lesson.get('subject', '')
        ltype = lesson.get('type', '')
        building = lesson.get('building', '')
        room1 = lesson.get('room1', '')
        room2 = lesson.get('room2', '')
        teacher = lesson.get('teacher', '')

        # Старый формат без эмодзи
        line1 = f"<b>{time_} [{week}] {subject}</b>{f' <i>({ltype})</i>' if ltype else ''}"

        loc_parts = []
        if building:
            loc_parts.append(building)
        rooms = ", ".join([x for x in (room1, room2) if x])
        if rooms:
            loc_parts.append(f"ауд. {rooms}")

        tail_parts = []
        if loc_parts:
            tail_parts.append(", ".join(loc_parts))
        if teacher:
            tail_parts.append(teacher)

        line2 = " — ".join(tail_parts) if tail_parts else ""

        result += line1
        if line2:
            result += f"\n{line2}"
        result += "\n\n"

    return result


@router.message(lambda message: message.text in ["📅 Сегодня", "📅 Завтра", "📋 Вся неделя", "🔍 Новая группа"])
async def handle_schedule_buttons(message: types.Message):
    """Обработчик кнопок расписания"""
    user_id = message.from_user.id

    if message.text == "🔍 Новая группа":
        await message.answer(
            "Введите номер группы:\nПример: 09-825, 8251160, 8251",
            reply_markup=types.ReplyKeyboardRemove()
        )
        return

    if user_id not in user_data:
        await message.answer(
            "❌ Расписание не найдено. Сначала найдите группу:",
            reply_markup=types.ReplyKeyboardRemove()
        )
        return

    group, lessons = user_data[user_id]

    if message.text == "📅 Сегодня":
        day_name = get_day_name(0)
        day_lessons = filter_lessons_by_day(lessons, day_name)
        response = format_day_schedule(day_lessons, day_name, group)

    elif message.text == "📅 Завтра":
        day_name = get_day_name(1)
        day_lessons = filter_lessons_by_day(lessons, day_name)
        response = format_day_schedule(day_lessons, day_name, group)

    elif message.text == "📋 Вся неделя":
        response = f"<b>Расписание на неделю</b>\nГруппа: <b>{group}</b>\n\n"
        days_order = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]

        for day in days_order:
            day_lessons = filter_lessons_by_day(lessons, day)
            if day_lessons:
                response += format_day_schedule(day_lessons, day, group)

    await message.answer(response, parse_mode="HTML", disable_web_page_preview=True)