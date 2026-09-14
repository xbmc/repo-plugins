from __future__ import annotations

import json
import os
import re
from datetime import datetime, timedelta
from typing import Any, Optional

try:
    import xbmcvfs
    _HAS_XBMCVFS = True
except ImportError:
    _HAS_XBMCVFS = False

_SANITIZE_RE = re.compile(r'[^a-zA-Z0-9_]')


class FileCache:

    def __init__(self, addon_id: str, logger: Any, ttl_days: int = 7) -> None:
        self._addon_id = addon_id
        self._logger = logger
        self._ttl_days = ttl_days

        if _HAS_XBMCVFS:
            self._cache_dir = xbmcvfs.translatePath(
                f"special://profile/addon_data/{addon_id}/cache/"
            )
        else:
            self._cache_dir = os.path.join(
                os.path.expanduser("~"), ".kodi", "userdata",
                "addon_data", addon_id, "cache",
            )

        self._logger.info(
            f"FileCache.__init__: addon_id='{addon_id}', "
            f"ttl_days={ttl_days}, cache_dir='{self._cache_dir}'"
        )

    def get(self, key: str) -> Optional[dict]:
        try:
            safe_key = self._sanitize_key(key)
            file_path = self._key_to_path(safe_key)

            content = self._read_file(file_path)
            if content is None:
                self._logger.debug(
                    f"FileCache.get: MISS key='{key}' (file not found)"
                )
                return None

            try:
                envelope = json.loads(content)
            except (json.JSONDecodeError, ValueError):
                self._logger.warning(
                    f"FileCache.get: corrupted JSON for key='{key}', deleting"
                )
                self._delete_file(file_path)
                return None

            cached_at_str = envelope.get("cached_at", "")

            if self._is_expired(cached_at_str):
                self._logger.info(
                    f"FileCache.get: MISS key='{key}' "
                    f"(TTL expired, cached_at='{cached_at_str}')"
                )
                return None

            file_size = len(content.encode("utf-8"))
            self._logger.info(
                f"FileCache.get: HIT key='{key}', "
                f"cached_at='{cached_at_str}', size={file_size}b"
            )
            return envelope.get("data")

        except Exception as e:
            self._logger.warning(
                f"FileCache.get: unexpected error for key='{key}': {e}"
            )
            return None

    def get_stale(self, key: str) -> Optional[dict]:
        """Return cached data even if TTL expired. Returns None only on true miss."""
        try:
            safe_key = self._sanitize_key(key)
            file_path = self._key_to_path(safe_key)

            content = self._read_file(file_path)
            if content is None:
                self._logger.debug(
                    f"FileCache.get_stale: MISS key='{key}' (file not found)"
                )
                return None

            try:
                envelope = json.loads(content)
            except (json.JSONDecodeError, ValueError):
                self._logger.warning(
                    f"FileCache.get_stale: corrupted JSON for key='{key}', deleting"
                )
                self._delete_file(file_path)
                return None

            cached_at_str = envelope.get("cached_at", "")
            data = envelope.get("data")

            if data is None:
                self._logger.debug(
                    f"FileCache.get_stale: MISS key='{key}' (data is None)"
                )
                return None

            self._logger.info(
                f"FileCache.get_stale: HIT key='{key}', "
                f"cached_at='{cached_at_str}', stale=True"
            )
            return data

        except Exception as e:
            self._logger.warning(
                f"FileCache.get_stale: unexpected error for key='{key}': {e}"
            )
            return None

    def put(self, key: str, data: Any) -> None:
        try:
            self._ensure_dir()
            safe_key = self._sanitize_key(key)
            file_path = self._key_to_path(safe_key)

            envelope = {
                "cached_at": datetime.now().isoformat(timespec="seconds"),
                "ttl_days": self._ttl_days,
                "data": data,
            }

            content = json.dumps(envelope, ensure_ascii=False)
            self._write_file(file_path, content)

            self._logger.info(
                f"FileCache.put: saved key='{key}', size={len(content)}b"
            )

        except Exception as e:
            self._logger.warning(
                f"FileCache.put: failed to save key='{key}': {e}"
            )

    def delete(self, key: str) -> None:
        try:
            safe_key = self._sanitize_key(key)
            file_path = self._key_to_path(safe_key)
            self._delete_file(file_path)
            self._logger.debug(
                f"FileCache.delete: removed key='{key}'"
            )
        except Exception as e:
            self._logger.warning(
                f"FileCache.delete: failed to remove key='{key}': {e}"
            )

    def clear(self) -> None:
        try:
            files = self._list_files()
            count = 0
            for filename in files:
                if filename.endswith(".json"):
                    file_path = os.path.join(self._cache_dir, filename)
                    self._delete_file(file_path)
                    count += 1

            self._logger.info(
                f"FileCache.clear: removed {count} cache files"
            )

        except Exception as e:
            self._logger.warning(
                f"FileCache.clear: failed: {e}"
            )

    def _sanitize_key(self, key: str) -> str:
        return _SANITIZE_RE.sub('_', key)

    def _key_to_path(self, safe_key: str) -> str:
        return os.path.join(self._cache_dir, f"{safe_key}.json")

    def _is_expired(self, cached_at_str: str) -> bool:
        try:
            cached_at = datetime.fromisoformat(cached_at_str)
            return datetime.now() - cached_at > timedelta(days=self._ttl_days)
        except (ValueError, TypeError):
            return True

    def _ensure_dir(self) -> None:
        if _HAS_XBMCVFS:
            if not xbmcvfs.exists(self._cache_dir):
                xbmcvfs.mkdirs(self._cache_dir)
                self._logger.debug(
                    f"FileCache._ensure_dir: created '{self._cache_dir}'"
                )
        else:
            if not os.path.exists(self._cache_dir):
                os.makedirs(self._cache_dir, exist_ok=True)
                self._logger.debug(
                    f"FileCache._ensure_dir: created '{self._cache_dir}'"
                )

    def _read_file(self, file_path: str) -> Optional[str]:
        if _HAS_XBMCVFS:
            if not xbmcvfs.exists(file_path):
                return None
            f = xbmcvfs.File(file_path)
            try:
                content = f.read()
                return content if content else None
            finally:
                f.close()
        else:
            if not os.path.exists(file_path):
                return None
            with open(file_path, "r", encoding="utf-8") as fh:
                return fh.read()

    def _write_file(self, file_path: str, content: str) -> None:
        if _HAS_XBMCVFS:
            f = xbmcvfs.File(file_path, "w")
            try:
                f.write(content)
            finally:
                f.close()
        else:
            with open(file_path, "w", encoding="utf-8") as fh:
                fh.write(content)

    def _delete_file(self, file_path: str) -> None:
        if _HAS_XBMCVFS:
            if xbmcvfs.exists(file_path):
                xbmcvfs.delete(file_path)
        else:
            if os.path.exists(file_path):
                os.remove(file_path)

    def _list_files(self) -> list:
        if _HAS_XBMCVFS:
            dirs, files = xbmcvfs.listdir(self._cache_dir)
            return files
        else:
            if not os.path.exists(self._cache_dir):
                return []
            return os.listdir(self._cache_dir)
