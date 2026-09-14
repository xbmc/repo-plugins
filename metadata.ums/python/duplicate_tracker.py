from __future__ import annotations

import json
import os
from typing import Any, Optional

try:
    import xbmcvfs
    _HAS_XBMCVFS = True
except ImportError:
    _HAS_XBMCVFS = False

_TRACKER_FILENAME = "duplicate_tracker.json"


class DuplicateTracker:

    def __init__(self, addon_id: str, logger: Any) -> None:
        self._addon_id = addon_id
        self._logger = logger
        self._tracker_path = self._get_tracker_path()
        self._logger.info(
            f"DuplicateTracker.__init__: addon_id='{addon_id}', "
            f"path='{self._tracker_path}'"
        )

    def check_and_update(self, kp_id: int, file_path: str) -> Optional[str]:
        """Check for duplicate kp_id. Returns existing path if duplicate, None otherwise."""
        try:
            data = self._load()
            kp_id_str = str(kp_id)
            existing = data.get(kp_id_str)

            if existing is None:
                data[kp_id_str] = file_path
                self._save(data)
                self._logger.info(
                    f"DuplicateTracker.check_and_update: new entry "
                    f"kp_id={kp_id}, path='{file_path}'"
                )
                return None

            if existing == file_path:
                self._logger.debug(
                    f"DuplicateTracker.check_and_update: same path "
                    f"for kp_id={kp_id}, not a duplicate"
                )
                return None

            # Duplicate detected
            self._logger.warning(
                f"DuplicateTracker.check_and_update: DUPLICATE "
                f"kp_id={kp_id}: new='{file_path}', existing='{existing}'"
            )
            data[kp_id_str] = file_path
            self._save(data)
            return existing

        except Exception as e:
            self._logger.warning(
                f"DuplicateTracker.check_and_update: error: {e}"
            )
            return None

    def clear(self) -> None:
        """Delete the tracker file."""
        try:
            self._delete_file()
            self._logger.info("DuplicateTracker.clear: tracker file deleted")
        except Exception as e:
            self._logger.warning(
                f"DuplicateTracker.clear: failed: {e}"
            )

    def _get_tracker_path(self) -> str:
        if _HAS_XBMCVFS:
            addon_data = xbmcvfs.translatePath(
                f"special://profile/addon_data/{self._addon_id}/"
            )
        else:
            addon_data = os.path.join(
                os.path.expanduser("~"), ".kodi", "userdata",
                "addon_data", self._addon_id,
            )
        return os.path.join(addon_data, _TRACKER_FILENAME)

    def _load(self) -> dict[str, str]:
        content = self._read_file()
        if content is None:
            return {}
        try:
            data = json.loads(content)
            if not isinstance(data, dict):
                raise ValueError(f"expected dict, got {type(data).__name__}")
            # Migration: remove entries corrupted by pathSettings bug (BUG-005)
            bad_keys = [k for k, v in data.items() if isinstance(v, str) and v.startswith("{")]
            if bad_keys:
                for k in bad_keys:
                    del data[k]
                self._save(data)
                self._logger.info(
                    f"DuplicateTracker._load: cleaned {len(bad_keys)} corrupted entries"
                )
            self._logger.debug(
                f"DuplicateTracker._load: loaded {len(data)} entries"
            )
            return data
        except (json.JSONDecodeError, ValueError) as e:
            self._logger.warning(
                f"DuplicateTracker._load: corrupted file, deleting: {e}"
            )
            self._delete_file()
            return {}

    def _save(self, data: dict[str, str]) -> None:
        try:
            self._ensure_dir()
            content = json.dumps(data, ensure_ascii=False)
            self._write_file(content)
            self._logger.debug(
                f"DuplicateTracker._save: saved {len(data)} entries"
            )
        except Exception as e:
            self._logger.warning(
                f"DuplicateTracker._save: failed: {e}"
            )

    def _ensure_dir(self) -> None:
        dir_path = os.path.dirname(self._tracker_path)
        if _HAS_XBMCVFS:
            if not xbmcvfs.exists(dir_path):
                xbmcvfs.mkdirs(dir_path)
        else:
            os.makedirs(dir_path, exist_ok=True)

    def _read_file(self) -> Optional[str]:
        if _HAS_XBMCVFS:
            if not xbmcvfs.exists(self._tracker_path):
                return None
            f = xbmcvfs.File(self._tracker_path)
            try:
                content = f.read()
                return content if content else None
            finally:
                f.close()
        else:
            if not os.path.exists(self._tracker_path):
                return None
            with open(self._tracker_path, "r", encoding="utf-8") as fh:
                return fh.read()

    def _write_file(self, content: str) -> None:
        if _HAS_XBMCVFS:
            f = xbmcvfs.File(self._tracker_path, "w")
            try:
                f.write(content)
            finally:
                f.close()
        else:
            with open(self._tracker_path, "w", encoding="utf-8") as fh:
                fh.write(content)

    def _delete_file(self) -> None:
        if _HAS_XBMCVFS:
            if xbmcvfs.exists(self._tracker_path):
                xbmcvfs.delete(self._tracker_path)
        else:
            if os.path.exists(self._tracker_path):
                os.remove(self._tracker_path)
