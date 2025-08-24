from aiogram import Router, types
from aiogram.filters import Command
from collections import defaultdict
import re, html, logging

from app.config import cfg
from app.services.google_csv import fetch_csv_text
from app.services.parser import parse_schedule

router = Router()
log = logging.getLogger(__name__)

DAY_ORDER = ["Понедельник","Вторник","Среда","Четверг","Пятница","Суббота","Воскресенье"]

def _day_key(d: str) -> int:
    return DAY_ORDER.index(d) if d in DAY_ORDER else len(DAY_ORDER)

_time_re = re.compile(r"(\d{1,2}):(\d{2})")
def _start_minutes(t: str) -> int:
    m = _time_re.search(t or "")
    return int(m.group(1))*60 + int(m.group(2)) if m else 10**9

def _norm_group(s: str) -> str:
    return "".join(ch for ch in (s or "") if ch.isdigit())

def _format_lesson(r: dict) -> str:
    """двухстрочный компактный формат: жирный заголовок + хвост."""
    time_ = html.escape(r.get("time") or "")
    week = html.escape(r.get("week_type") or "")
    subject = html.escape(r.get("subject") or "")
    ltype = html.escape(r.get("type") or "")
    building = html.escape(r.get("building") or "")
    room1 = html.escape(r.get("room1") or "") if r.get("room1") else ""
    room2 = html.escape(r.get("room2") or "") if r.get("room2") else ""
    teacher = html.escape(r.get("teacher") or "") if r.get("teacher") else ""

    line1 = f"⏰ <b>{time_} [{week}] {subject}</b>{f' <i>({ltype})</i>' if ltype else ''}"

    loc_parts = []
    if building: loc_parts.append(building)
    rooms = ", ".join([x for x in (room1, room2) if x])
    if rooms: loc_parts.append(f"ауд. {rooms}")
    tail = " — ".join([", ".join(loc_parts)] + ([teacher] if teacher else []))
    line2 = tail if tail.strip() else ""

    return (line1 + ("\n" + line2 if line2 else "")).strip()

async def _send_chunked_html(m: types.Message, text: str):
    """безопасно шлём HTML, режем по пустым строкам если > ~3500 знаков."""
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
async def cmd_schedule(m: types.Message):
    """
    /schedule <номер группы>
    отправляет 1) шапку, 2) по отдельному сообщению на каждый день.
    """
    args = (m.text or "").split(maxsplit=1)[1:]
    if not args:
        await m.answer("Использование: /schedule <группа>\nПример: /schedule 8251160")
        return

    group = _norm_group(args[0])
    if not group:
        await m.answer("Не распознал номер группы. Пример: /schedule 8251160")
        return

    csv_text = await fetch_csv_text(cfg.spreadsheet_id, cfg.gid)
    if not csv_text:
        await m.answer("Не удалось загрузить таблицу.")
        return

    try:
        lessons = parse_schedule(csv_text, group)
    except Exception as e:
        log.exception("parse_schedule failed for %s", group)
        await m.answer(f"⚠️ Ошибка парсинга: <code>{html.escape(str(e))}</code>", parse_mode="HTML")
        return

    if not lessons:
        await m.answer(f"Для группы <b>{html.escape(group)}</b> расписание не найдено.", parse_mode="HTML")
        return

    # группируем и сортируем
    grouped = defaultdict(list)
    for l in lessons:
        grouped[l["day"]].append(l)
    for day in grouped:
        grouped[day].sort(key=lambda r: _start_minutes(r.get("time") or ""))
    days_sorted = sorted(grouped.keys(), key=_day_key)

    # 1) шапка
    header = (
        f"📅 Расписание для группы <b>{html.escape(group)}</b>\n"
        f"<i>[н] — нечётная неделя, [в] — чётная</i>"
    )
    await m.answer(header, parse_mode="HTML", disable_web_page_preview=True)

    # 2) по дню — отдельное сообщение (+ разделитель в начале текста дня не нужен)
    for day in days_sorted:
        title = f"— <b>{html.escape(day)}</b> —"
        blocks = [_format_lesson(r) for r in grouped[day]]
        day_text = title + "\n\n" + "\n\n".join(blocks)
        await m.answer(day_text, parse_mode="HTML", disable_web_page_preview=True)
