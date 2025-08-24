import os
from dataclasses import dataclass

@dataclass(frozen=True)
class Config:
    bot_token: str = os.getenv("BOT_TOKEN", "")
    spreadsheet_id: str = os.getenv("SPREADSHEET_ID", "")
    gid: int = int(os.getenv("GID", "0"))

cfg = Config()
