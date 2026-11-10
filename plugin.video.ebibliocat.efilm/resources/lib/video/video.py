from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class Video:
    title: str
    iconImage: str
    thumbnailImage: str
    information: Dict[str, Any]
    url: str
    durada: int = 0
