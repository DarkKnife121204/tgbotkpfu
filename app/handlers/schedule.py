from aiogram import Router, types
from aiogram.filters import Command
from collections import defaultdict
import re, html, logging

from app.config import cfg
from app.handlers.schedule_buttons import user_data
from app.services.google_csv import find_group_schedule
from app.services.parser import parse_schedule

router = Router()
log = logging.getLogger(__name__)

DAY_ORDER = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]


def _day_key(d: str) -> int:
    return DAY_ORDER.index(d) if d in DAY_ORDER else len(DAY_ORDER)


_time_re = re.compile(r"(\d{1,2}):(\d{2})")


def _start_minutes(t: str) -> int:
    m = _time_re.search(t or "")
    return int(m.group(1)) * 60 + int(m.group(2)) if m else 10 ** 9


def _norm_group(s: str) -> str:
    return "".join(ch for ch in (s or "") if ch.isdigit())


def _format_lesson(r: dict) -> str:
    """Старый дизайн: жирный заголовок + хвост без эмодзи"""
    time_ = html.escape(r.get("time") or "")
    week = html.escape(r.get("week_type") or "")
    subject = html.escape(r.get("subject") or "")
    ltype = html.escape(r.get("type") or "")
    building = html.escape(r.get("building") or "")
    room1 = html.escape(r.get("room1") or "") if r.get("room1") else ""
    room2 = html.escape(r.get("room2") or "") if r.get("room2") else ""
    teacher = html.escape(r.get("teacher") or "") if r.get("teacher") else ""

    # Старый формат: жирный заголовок без эмодзи
    line1 = f"<b>{time_} [{week}] {subject}</b>{f' <i>({ltype})</i>' if ltype else ''}"

    # Хвост с локацией и преподавателем
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

    return (line1 + ("\n" + line2 if line2 else "")).strip()


async def _send_chunked_html(m: types.Message, text: str):
    LIMIT = 3500
    i, n = 0, len(text)
    while i < n:
        j = text.rfind("\n\n", i, min(i + LIMIT, n))
        if j == -1 or j <= i:
            j = min(i + LIMIT, n)
        part = text[i:j].strip()
        if part:
            await m.answer(part, parse_mode="HTML", disable_web_page_preview=True)
        i = j


@router.message(Command("schedule"))
@router.message(lambda message: message.text and not message.text.startswith('/'))
async def cmd_schedule(m: types.Message):
    """
    Обработчик для команды /schedule и текстовых сообщений с номером группы
    """
    # Если это команда /schedule, извлекаем аргументы
    if m.text.startswith('/'):
        args = (m.text or "").split(maxsplit=1)[1:]
        if not args:
            await m.answer("Использование: /schedule <Группа>\nПример: /schedule 09-825")
            return
        group_input = args[0]
    else:
        # Если это текстовое сообщение (после нажатия кнопки)
        group_input = m.text.strip()

    group = _norm_group(group_input)
    if not group:
        await m.answer(
            "Не распознал номер группы. Пример: 09-825, 8251160, 8251\n"
            "Попробуйте еще раз:"
        )
        return

    # Показываем статус поиска
    status_msg = await m.answer(f"🔍 Ищу группу {group}...")

    # Ищем группу во всех GID
    csv_text = await find_group_schedule(cfg.spreadsheet_id, cfg.gids, group)

    if not csv_text:
        await status_msg.edit_text(
            f"❌ Группа <b>{html.escape(group)}</b> не найдена.\n"
            f"Проверьте правильность написания номера группы."
        )
        return

    try:
        lessons = parse_schedule(csv_text, group)
    except Exception as e:
        log.exception("Ошибка парсинга для группы %s", group)
        await status_msg.edit_text(f"▲ Ошибка обработки: <code>{html.escape(str(e))}</code>")
        return

    # Сохраняем группу И расписание для пользователя
    user_data[m.from_user.id] = (group, lessons)  # сохраняем кортеж (группа, расписание)

    if not lessons:
        await status_msg.edit_text(
            f"ℹ️ Группа <b>{html.escape(group)}</b> найдена, но расписание пустое.\n"
            f"Возможно, на этой неделе нет занятий."
        )
        return

    # Удаляем статус сообщение
    await status_msg.delete()

    # Показываем клавиатуру с вариантами
    from .schedule_buttons import get_schedule_keyboard

    await m.answer(
        f"✅ Группа <b>{html.escape(group)}</b> найдена!\n"
        f"Выберите период для просмотра:",
        parse_mode="HTML",
        reply_markup=get_schedule_keyboard()
    )
