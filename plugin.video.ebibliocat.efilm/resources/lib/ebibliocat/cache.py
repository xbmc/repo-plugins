"""Versioned public-data caches, independent of sign-in state."""

import contextlib
import time
from pathlib import Path

from resources.lib.ebibliocat.errors import Cancelled, EfilmError
from resources.lib.ebibliocat.storage import file_lock, read_json, write_json

SCHEMA = 1


class Cache:
    def __init__(self, profile, language):
        self.directory = Path(profile) / "cache"
        self.language = language
        self.used_stale = False

    def get(self, name, loader, valid, ttl=600, force=False, cancelled=None):
        path = self.directory / (name + "-" + self.language + ".json")
        self.used_stale = False
        with file_lock(self.directory, name, timeout=120, cancelled=cancelled):
            old = read_json(path)
            usable = isinstance(old, dict) and old.get("schema") == SCHEMA and valid(old.get("data"))
            timestamp = old.get("updated") if usable else None
            fresh = isinstance(timestamp, (int, float)) and 0 <= time.time() - timestamp < ttl
            if usable and fresh and not force:
                return old["data"]
            if cancelled and cancelled():
                raise Cancelled()
            try:
                data = loader()
                if not valid(data):
                    raise EfilmError("invalid_response")
                if cancelled and cancelled():
                    raise Cancelled()
                write_json(path, {"schema": SCHEMA, "updated": time.time(), "data": data})
                return data
            except EfilmError as error:
                if usable and (
                    error.message == "network_error"
                    or error.status == 429
                    or (error.status and error.status >= 500)
                ):
                    self.used_stale = True
                    return old["data"]
                raise

    def clear(self):
        # Preserve lock files; they may be held by another invocation.
        for path in self.directory.glob("*.json"):
            with file_lock(self.directory, path.stem.rsplit("-", 1)[0], timeout=120):
                with contextlib.suppress(FileNotFoundError):
                    path.unlink()
