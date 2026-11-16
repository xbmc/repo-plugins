"""Jellyfin's lyric payload as timed lines for the skin overlay.

Jellyfin returns lyrics as a list of lines, each optionally carrying a start
time in .NET ticks (100 ns units)::

    {"Metadata": {}, "Lyrics": [{"Text": "Tonight", "Start": 5800000}]}

``Metadata.IsSynced`` looks like the field to branch on but is never set by
Jellyfin core — every response for a locally stored lyric carries an empty
``Metadata``. Whether a lyric is timed is decided by the presence of ``Start``
on the first line, which is what jellyfin-web does too.
"""

from typing import Any, Optional

JsonDict = dict[str, Any]

# One rendered line: its start time in seconds, or None when the payload
# carries no timings at all (or this particular line was left unstamped).
LyricLine = tuple[Optional[float], str]

TICKS_PER_SECOND = 10_000_000


def is_synced(payload: Optional[JsonDict]) -> bool:
    """Whether the payload carries line timings.

    Decided on the first line alone: Jellyfin sorts timed lyrics by start time,
    so a timed set always stamps line zero. A lyric file that failed LRC
    parsing falls back to the plain-text parser server-side and arrives with no
    stamps at all, which lands here as False.
    """
    lines = (payload or {}).get("Lyrics") or []
    return bool(lines) and lines[0].get("Start") is not None


def to_lines(payload: Optional[JsonDict]) -> list[LyricLine]:
    """The payload as ``(start_seconds, text)`` pairs for the skin overlay.

    A line without a stamp inside an otherwise timed payload keeps ``None``
    rather than a guessed time.
    """
    lines: list[JsonDict] = (payload or {}).get("Lyrics") or []
    if not lines:
        return []

    timed = is_synced(payload)
    out: list[LyricLine] = []
    for line in lines:
        text = line.get("Text") or ""
        start = line.get("Start")
        if timed and start is not None:
            out.append((max(0.0, int(start) / TICKS_PER_SECOND), text))
        else:
            out.append((None, text))
    return out
