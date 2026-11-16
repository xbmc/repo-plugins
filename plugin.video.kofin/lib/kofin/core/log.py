"""Logging through xbmc.log with unconditional masking of sensitive values.

Every kofin log line passes through :func:`mask`. Secrets are caught two ways:
regex patterns for the shapes credentials travel in (URLs, JSON bodies, auth
headers), and an exact-match registry fed by the code that handles the live
values. Debug detail lands at LOGDEBUG, so it is visible exactly when the user
enables Kodi's own debug logging — there is no addon log-level setting.

Allowed module-level state: the masking registry. It is append-only and
fail-safe in both directions (a stale entry only masks more), which is why it
is exempt from the no-module-globals rule that protects the restart path.
"""

import re
import traceback
from typing import Any

import xbmc

REDACTED = "***"

_PATTERNS: list[tuple["re.Pattern[str]", str]] = [
    (re.compile(r"(api_key=)[^&\"'\s]+", re.I), r"\g<1>" + REDACTED),
    (re.compile(r'(Token=")[^"]*(")'), r"\g<1>" + REDACTED + r"\g<2>"),
    (
        re.compile(r'("(?:AccessToken|Pw|Password|Secret)"\s*:\s*")[^"]*(")'),
        r"\g<1>" + REDACTED + r"\g<2>",
    ),
    # A URL's user name and password, up to the authority's last "@".
    (re.compile(r"(://)[^/?#\s\"']*@"), r"\g<1>" + REDACTED + "@"),
]

_secrets: dict[str, str] = {}


def register_secret(value: str, keep: int = 0) -> None:
    """Mask ``value`` in all future log lines.

    ``keep`` > 0 leaves that many leading characters for correlation (used for
    ids); 0 redacts outright (tokens, passwords).
    """
    if not value or len(value) <= keep:
        return
    _secrets[value] = value[:keep] + "…" if keep else REDACTED


def mask(text: str) -> str:
    # A snapshot: register_secret can add a key from any thread (a login,
    # a token change) while other threads log.
    for secret, replacement in list(_secrets.items()):
        if secret in text:
            text = text.replace(secret, replacement)
    for pattern, replacement in _PATTERNS:
        text = pattern.sub(replacement, text)
    return text


class Logger:
    def __init__(self, name: str) -> None:
        self._prefix = "[kofin] %s: " % name

    def debug(self, msg: object, *args: Any) -> None:
        self._write(xbmc.LOGDEBUG, msg, args)

    def warning(self, msg: object, *args: Any) -> None:
        self._write(xbmc.LOGWARNING, msg, args)

    def error(self, msg: object, *args: Any) -> None:
        self._write(xbmc.LOGERROR, msg, args)

    def exception(self, msg: object, *args: Any) -> None:
        self._write(xbmc.LOGERROR, msg, args, trailer=traceback.format_exc())

    def _write(
        self, level: int, msg: object, args: tuple[Any, ...], trailer: str = ""
    ) -> None:
        # Accept anything stringable (LOG.exception(error)).
        if not isinstance(msg, str):
            msg = str(msg)
        if args:
            try:
                msg = msg % args
            except TypeError:
                msg = "%s %r" % (msg, args)
        if trailer:
            msg = msg + "\n" + trailer
        xbmc.log(self._prefix + mask(msg), level)
