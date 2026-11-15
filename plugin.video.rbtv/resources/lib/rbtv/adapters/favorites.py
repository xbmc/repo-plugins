from __future__ import annotations

import os

from rbtv.adapters.cache import JsonFileStore


class FavoriteStore:
    def __init__(self, path: str | os.PathLike[str]) -> None:
        self._store = JsonFileStore(path)

    def ids(self) -> set[int]:
        payload = self._store.read()
        if not isinstance(payload, dict):
            return set()
        raw = payload.get("shows")
        if not isinstance(raw, list):
            return set()
        return {int(value) for value in raw if isinstance(value, int)}

    def add(self, show_id: int) -> None:
        self._write(self.ids() | {show_id})

    def remove(self, show_id: int) -> None:
        self._write(self.ids() - {show_id})

    def replace(self, ids: set[int]) -> None:
        """Store exactly these favourites in a single write."""
        self._write(set(ids))

    def _write(self, ids: set[int]) -> None:
        self._store.write({"shows": sorted(ids)})
