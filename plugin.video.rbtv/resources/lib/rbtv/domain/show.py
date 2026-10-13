from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class Show:
    id: int
    title: str
    thumbnail_url: str | None = None
    description: str = ""
    genre: str = ""
    last_episode_date: date | None = None
    episode_count: int | None = None

    @property
    def last_year(self) -> int | None:
        return self.last_episode_date.year if self.last_episode_date else None
