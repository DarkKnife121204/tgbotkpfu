import logging
from datetime import datetime, timedelta, date
from typing import Dict, List, Tuple

from aiogram import Router, types
from aiogram.utils.keyboard import ReplyKeyboardBuilder

router = Router()
logger = logging.getLogger(__name__)

user_data: Dict[int, Tuple[str, List[dict]]] = {}


def get_schedule_keyboard() -> types.ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.add(types.KeyboardButton(text="📅 Сегодня"))
    builder.add(types.KeyboardButton(text="📅 Завтра"))
    builder.add(types.KeyboardButton(text="📋 Вся неделя"))
    builder.add(types.KeyboardButton(text="🔍 Другая группа"))
    builder.adjust(3, 1)
    return builder.as_markup(resize_keyboard=True)


def get_week_menu_keyboard() -> types.ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.add(types.KeyboardButton(text="🔎 Текущая неделя"))
    builder.add(types.KeyboardButton(text="➡️ Следующая неделя"))
    builder.add(types.KeyboardButton(text="📚 Вся без фильтров"))
    builder.add(types.KeyboardButton(text="⬅️ Назад"))
    builder.adjust(3, 1)
    return builder.as_markup(resize_keyboard=True)


def get_day_name(day_offset: int = 0) -> str:
    days = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
    today = datetime.now() + timedelta(days=day_offset)
    return days[today.weekday()]


def filter_lessons_by_day(lessons: List[dict], day_name: str) -> List[dict]:
    return [lesson for lesson in lessons if lesson.get("day") == day_name]


def _time_to_minutes(time_str: str) -> int:
    hours, minutes = map(int, time_str.split(":"))
    return hours * 60 + minutes


def get_current_week_type(start_date: date = date(2025, 9, 1)) -> str:
    today = date.today()
    weeks_passed = ((today - start_date).days // 7)
    return "в" if weeks_passed % 2 == 0 else "н"


def filter_by_week(lessons: List[dict]) -> List[dict]:
    week_type = get_current_week_type()
    return [
        lesson for lesson in lessons
        if not lesson.get("week_type") or lesson.get("week_type").lower() == week_type
    ]


def format_day_schedule(lessons: List[dict], day_name: str, group: str) -> str:
    if not lessons:
        return f"<b>{day_name}</b>\n\nЗанятий нет\n"

    lessons.sort(key=lambda x: _time_to_minutes(x.get("time", "")))

    result = [f"<b>{day_name}</b>\n"]
    for lesson in lessons:
        time_ = lesson.get("time", "")
        week = lesson.get("week_type", "")
        subject = lesson.get("subject", "")
        ltype = lesson.get("type", "")
        building = lesson.get("building", "")
        room1 = lesson.get("room1", "")
        room2 = lesson.get("room2", "")
        teacher = lesson.get("teacher", "")

        line1 = f"⏰ <b>{time_} [{week}] {subject}</b>{f' <i>({ltype})</i>' if ltype else ''}"

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

        result.append(line1)
        if line2:
            result.append(line2)
        result.append("")

    return "\n".join(result).strip()


@router.message(lambda m: m.text in [
    "📅 Сегодня", "📅 Завтра", "📋 Вся неделя", "🔍 Другая группа",
    "🔎 Текущая неделя", "➡️ Следующая неделя", "📚 Вся без фильтров", "⬅️ Назад"
])
async def handle_schedule_buttons(message: types.Message) -> None:
    user_id = message.from_user.id

    if message.text == "🔍 Другая группа":
        await message.answer(
            "Введите номер группы:\nПример: 09-825, 8251160, 8251",
            reply_markup=types.ReplyKeyboardRemove(),
        )
        return

    if message.text == "⬅️ Назад":
        await message.answer("Выберите действие:", reply_markup=get_schedule_keyboard())
        return

    if user_id not in user_data:
        await message.answer(
            "❌ Расписание не найдено. Сначала найдите группу:",
            reply_markup=types.ReplyKeyboardRemove(),
        )
        return

    group, lessons = user_data[user_id]

    if message.text == "📅 Сегодня":
        day_name = get_day_name(0)
        day_lessons = filter_lessons_by_day(lessons, day_name)
        day_lessons = filter_by_week(day_lessons)
        await message.answer(
            format_day_schedule(day_lessons, day_name, group),
            parse_mode="HTML", disable_web_page_preview=True
        )

    elif message.text == "📅 Завтра":
        day_name = get_day_name(1)
        day_lessons = filter_lessons_by_day(lessons, day_name)
        day_lessons = filter_by_week(day_lessons)
        await message.answer(
            format_day_schedule(day_lessons, day_name, group),
            parse_mode="HTML", disable_web_page_preview=True
        )

    elif message.text == "📋 Вся неделя":
        await message.answer("Выберите фильтр:", reply_markup=get_week_menu_keyboard())

    elif message.text == "🔎 Текущая неделя":
        await message.answer(
            f"📆 <b>Расписание на текущую неделю</b>\nГруппа: <b>{group}</b>",
            parse_mode="HTML", reply_markup=get_week_menu_keyboard()
        )
        days_order = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота"]
        for day in days_order:
            day_lessons = filter_lessons_by_day(lessons, day)
            day_lessons = filter_by_week(day_lessons)
            day_text = format_day_schedule(day_lessons, day, group)
            await message.answer(day_text, parse_mode="HTML", disable_web_page_preview=True)

    elif message.text == "➡️ Следующая неделя":
        await message.answer(
            f"📆 <b>Расписание на следующую неделю</b>\nГруппа: <b>{group}</b>",
            parse_mode="HTML", reply_markup=get_week_menu_keyboard()
        )
        days_order = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота"]
        next_type = "н" if get_current_week_type() == "в" else "в"
        for day in days_order:
            day_lessons = filter_lessons_by_day(lessons, day)
            day_lessons = [l for l in day_lessons
                           if not l.get("week_type") or l.get("week_type").lower() == next_type]
            day_text = format_day_schedule(day_lessons, day, group)
            await message.answer(day_text, parse_mode="HTML", disable_web_page_preview=True)

    elif message.text == "📚 Вся без фильтров":
        await message.answer(
            f"📆 <b>Расписание на неделю (без фильтра)</b>\nГруппа: <b>{group}</b>",
            parse_mode="HTML", reply_markup=get_week_menu_keyboard()
        )
        days_order = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота"]
        for day in days_order:
            day_lessons = filter_lessons_by_day(lessons, day)
            day_text = format_day_schedule(day_lessons, day, group)
            await message.answer(day_text, parse_mode="HTML", disable_web_page_preview=True)
