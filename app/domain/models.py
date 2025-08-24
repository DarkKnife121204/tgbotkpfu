from dataclasses import dataclass
from typing import Optional

@dataclass
class Lesson:
    day: str
    time: str
    week_type: str
    subject: str
    building: Optional[str] = None
    room: Optional[str] = None
    type: Optional[str] = None
    teacher: Optional[str] = None
    group: Optional[str] = None    
