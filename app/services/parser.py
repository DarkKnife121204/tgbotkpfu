import logging
from io import StringIO
from typing import List, Dict
import pandas as pd


def parse_schedule(csv_text: str, group_code: str) -> List[Dict]:
    df = pd.read_csv(StringIO(csv_text), header=[0, 1])

    col_day = df.columns[0]
    col_time = df.columns[1]
    col_week = df.columns[2]

    days = df[col_day].ffill()
    times = df[col_time].astype(str).str.strip().replace("nan", "")
    weeks = df[col_week].astype(str).str.strip().replace("nan", "")

    start_idx = None
    for i, col in enumerate(df.columns):
        if group_code in str(col[0]):
            start_idx = i
            break

    if start_idx is None:
        logging.warning("Группа %s не найдена", group_code)
        return []

    col_subj = df.columns[start_idx]
    col_build = df.columns[start_idx + 1]
    col_room1 = df.columns[start_idx + 2]
    col_room2 = df.columns[start_idx + 3]
    col_type = df.columns[start_idx + 4]
    col_teacher = df.columns[start_idx + 7]

    subj = df[col_subj].astype(str).str.strip().replace("nan", "")
    build = df[col_build].astype(str).str.strip().replace("nan", "")
    room1 = df[col_room1].astype(str).str.strip().replace("nan", "")
    room2 = df[col_room2].astype(str).str.strip().replace("nan", "")
    type_ = df[col_type].astype(str).str.strip().replace("nan", "")
    teach = df[col_teacher].astype(str).str.strip().replace("nan", "")

    out = []
    for d, t, w, s, b, r1, r2, ty, te in zip(days, times, weeks, subj, build, room1, room2, type_, teach):
        if s != "" and t != "":
            out.append({
                "group": group_code,
                "day": d,
                "time": t,
                "week_type": w,
                "subject": s,
                "building": b,
                "room1": r1,
                "room2": r2,
                "type": ty,
                "teacher": te,
            })

    return out
