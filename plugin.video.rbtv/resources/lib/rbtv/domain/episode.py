from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum


class SourceKind(Enum):
    YOUTUBE = "youtube"
    TWITCH = "twitch"
    VIDEO_SERVICE = "video_service"
    UNKNOWN = "unknown"

    @classmethod
    def parse(cls, value: str | None) -> SourceKind:
        for kind in cls:
            if kind.value == value:
                return kind
        return cls.UNKNOWN


@dataclass(frozen=True)
class VideoSource:
    kind: SourceKind
    token: str


@dataclass(frozen=True)
class Episode:
    id: int
    title: str
    show_id: int
    duration: int
    available: bool
    thumbnail_url: str | None = None
    sources: tuple[VideoSource, ...] = ()
    published: date | None = None
    description: str = ""

    def source(self, kind: SourceKind) -> VideoSource | None:
        return next((s for s in self.sources if s.kind is kind), None)


@dataclass(frozen=True)
class EpisodePage:
    episodes: tuple[Episode, ...]
    offset: int
    total: int

    @property
    def has_more(self) -> bool:
        return self.offset + len(self.episodes) < self.total
