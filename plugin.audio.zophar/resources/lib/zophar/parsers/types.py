from __future__ import annotations

import dataclasses as dc
import datetime as dt
from enum import Enum
from typing import List, Mapping, Optional, Tuple


class ParseError(Exception):
    """Parsing error exception"""


class PageType(Enum):
    """Enum of supported page classes"""

    GameListPage = "gamelistpage"
    """List of games entries"""
    GamePage = "gamepage"
    """Game info page with soundtrack"""
    InfoPage = "infopage"
    """Simple page with links"""


class AudioFormat(Enum):
    """Enum with used audio formats"""

    MP3 = "mp3"
    """MPEG Layer-3 lossy format"""
    FLAC = "flac"
    """FLAC lossless format"""

    @property
    def mime(self) -> str:
        """MIME media type"""

        if self is AudioFormat.MP3:
            return "audio/mpeg"

        return f"audio/{self.value}"


@dc.dataclass
class Browsable:
    """Browsable entity. Have `path` property."""

    name: str
    """Name"""
    path: str
    """Encoded relative request path to webserver"""


@dc.dataclass
class GameEntry(Browsable):
    """Game list entry"""

    cover: Optional[str]
    """URL to cover image"""
    year: Optional[str]
    """Year of production"""
    console: Optional[str]
    """Game platform"""
    developer: Optional[str]
    """Developer"""


@dc.dataclass
class AudioTrack:
    """Audiotrack. Part of media playlist."""

    title: str
    """Title"""
    length: dt.timedelta
    """Duration"""
    mp3url: str
    """URL to MP3 stream"""

    def url(self, format: AudioFormat) -> str:
        """Returns URL to audio in specified format"""

        if format is AudioFormat.MP3:
            return self.mp3url

        return self.mp3url[:-3] + format.value


@dc.dataclass
class GamePage:
    """Represents page of game description"""

    name: str
    """Name"""
    console: str
    """Console"""
    cover: Optional[str]
    """URL to cover image"""
    release_date: Optional[str]
    """Release date"""
    developer: Optional[str]
    """Developer"""
    publisher: Optional[str]
    """Publisher"""
    originals: Optional[str]
    """Original platform (emulator) files"""
    archives: Mapping[AudioFormat, str]
    """Media archives by audioformat"""
    tracks: Tuple[AudioTrack, ...]
    """Playlist of MP3 audio"""

    def has_format(self, format: AudioFormat) -> bool:
        return format in self.archives


@dc.dataclass
class GameListPage:
    """Represents one page of gamelist"""

    entries: List[GameEntry]
    """Game entries list"""
    title: str
    """Title"""
    description: str
    """Found statistics or any description"""
    page: int
    """Current page number"""
    total_pages: int
    """Total pages in this list"""

    def __bool__(self) -> bool:
        return bool(self.entries)


@dc.dataclass
class InfoPage:
    """Represents simple list of links"""

    entries: List[Browsable]
    description: str
