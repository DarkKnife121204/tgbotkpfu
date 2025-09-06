import os
from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class Config:
    bot_token: str = os.getenv("BOT_TOKEN", "")
    spreadsheet_id: str = os.getenv("SPREADSHEET_ID", "")
    gids: List[int] = field(
        default_factory=lambda: list(map(int, os.getenv("GIDS", "0,1,2,3,4,5").split(",")))
    )


cfg = Config()
