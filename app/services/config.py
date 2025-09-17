import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import List
from dotenv import load_dotenv

# Загружаем .env
load_dotenv()


def _parse_gids() -> List[int]:
    raw = os.getenv("GIDS", "0,1,2,3,4,5")
    return [int(x.strip()) for x in raw.split(",") if x.strip().isdigit()]


@dataclass(frozen=True)
class Config:
    bot_token: str = os.getenv("BOT_TOKEN", "")
    spreadsheet_id: str = os.getenv("SPREADSHEET_ID", "")
    gids: List[int] = field(default_factory=_parse_gids)

    # Логирование
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    log_file: str = os.getenv("LOG_FILE", "logs/bot.log")


cfg = Config()