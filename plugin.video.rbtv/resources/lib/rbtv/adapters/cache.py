from __future__ import annotations

import contextlib
import json
import os
import tempfile
import time
from datetime import date
from pathlib import Path
from typing import Any, Callable

from rbtv.domain.episode import EpisodePage
from rbtv.domain.show import Show
from rbtv.ports.catalog import Catalog

CACHE_VERSION = 2


class JsonFileStore:
    def __init__(self, path: str | os.PathLike[str]) -> None:
        self._path = Path(path)

    def read(self) -> dict[str, Any] | None:
        try:
            with self._path.open(encoding="utf-8") as handle:
                payload = json.load(handle)
        except (OSError, ValueError):
            return None
        return payload if isinstance(payload, dict) else None

    def write(self, payload: dict[str, Any]) -> None:
        """Atomically replace the file. Raises OSError; callers decide if that matters."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        # A unique temp file per call: Kodi may run several plugin instances at once
        fd, tmp = tempfile.mkstemp(
            dir=self._path.parent, prefix=f".{self._path.name}.", suffix=".tmp"
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(payload, handle)
            os.replace(tmp, self._path)
        except BaseException:
            with contextlib.suppress(OSError):
                os.unlink(tmp)
            raise

    def clear(self) -> None:
        try:
            self._path.unlink()
        except OSError:
            pass


class CachedCatalog:
    def __init__(
        self,
        catalog: Catalog,
        store: JsonFileStore,
        ttl: float = 24 * 3600,
        clock: Callable[[], float] = time.time,
    ) -> None:
        self._catalog = catalog
        self._store = store
        self._ttl = ttl
        self._clock = clock

    def all_shows(self) -> list[Show]:
        cached = self._cached_shows()
        if cached is not None:
            return cached
        shows = self._catalog.all_shows()
        payload = {
            "version": CACHE_VERSION,
            "created": self._clock(),
            "shows": [_show_to_json(s) for s in shows],
        }
        try:
            self._store.write(payload)
        except OSError:
            pass  # the cache is best-effort; the next call simply fetches again
        return shows

    def episodes_of_show(self, show_id: int, offset: int = 0) -> EpisodePage:
        return self._catalog.episodes_of_show(show_id, offset)

    def invalidate(self) -> None:
        self._store.clear()

    def _cached_shows(self) -> list[Show] | None:
        payload = self._store.read()
        if not isinstance(payload, dict) or payload.get("version") != CACHE_VERSION:
            return None
        created = payload.get("created")
        if not isinstance(created, (int, float)) or self._clock() - created > self._ttl:
            return None
        try:
            return [_show_from_json(item) for item in payload["shows"]]
        except (KeyError, TypeError, ValueError):
            return None


def _show_to_json(show: Show) -> dict[str, Any]:
    return {
        "id": show.id,
        "title": show.title,
        "thumbnail_url": show.thumbnail_url,
        "description": show.description,
        "genre": show.genre,
        "last_episode_date": (
            show.last_episode_date.isoformat() if show.last_episode_date else None
        ),
        "episode_count": show.episode_count,
    }


def _show_from_json(item: dict[str, Any]) -> Show:
    raw_date = item["last_episode_date"]
    return Show(
        id=item["id"],
        title=item["title"],
        thumbnail_url=item["thumbnail_url"],
        description=item["description"],
        genre=item["genre"],
        last_episode_date=date.fromisoformat(raw_date) if raw_date else None,
        episode_count=item.get("episode_count"),
    )
