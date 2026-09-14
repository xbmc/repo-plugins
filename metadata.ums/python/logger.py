from __future__ import annotations

import re
import xbmc
import xbmcaddon

_addon_id: str = ""


def _resolve_addon_id() -> str:
    global _addon_id
    if not _addon_id:
        try:
            _addon_id = xbmcaddon.Addon().getAddonInfo('id')
        except Exception:
            _addon_id = "metadata.unknown"
    return _addon_id

_SANITIZE_PATTERNS = [
    (re.compile(r'(X-API-KEY:\s*)\S+', re.IGNORECASE), r'\1***'),
    (re.compile(r'(api_key=)[^&\s]+', re.IGNORECASE), r'\1***'),
]


class Logger:

    def __init__(self, debug_enabled: bool = False):
        self._debug_enabled = debug_enabled
        self._addon_id = _resolve_addon_id()

    def _sanitize(self, message: str) -> str:
        for pattern, replacement in _SANITIZE_PATTERNS:
            message = pattern.sub(replacement, message)
        return message

    def _log(self, level: int, message: str) -> None:
        sanitized = self._sanitize(message)
        xbmc.log(f"[{self._addon_id}] {sanitized}", level)

    def debug(self, message: str) -> None:
        if self._debug_enabled:
            self._log(xbmc.LOGDEBUG, message)

    def info(self, message: str) -> None:
        self._log(xbmc.LOGINFO, message)

    def warning(self, message: str) -> None:
        self._log(xbmc.LOGWARNING, message)

    def error(self, message: str) -> None:
        self._log(xbmc.LOGERROR, message)

    def fatal(self, message: str) -> None:
        self._log(xbmc.LOGFATAL, message)
