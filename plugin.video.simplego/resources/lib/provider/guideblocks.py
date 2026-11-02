"""The guide's 3-hour blocks kept on disk: where, how long they stay good, reading and writing them."""

import calendar
import collections
import contextlib
import gzip
import hashlib
import json
import os
import threading
import time

from resources.lib.util import atomicfile

# An ended block never changes; a later one is refetched after BLOCK_FRESH (the CDN serves them
# up to 15 minutes old).
BLOCK_FRESH = 15 * 60
# Blocks beyond NEAR rarely change; refreshing them was most of an export (~100 of ~130 blocks).
NEAR = 2 * 86400
FAR_BLOCK_FRESH = 12 * 3600
# In the kept block's file name: blocks of an older layout are ignored.
BLOCK_VERSION = 5
# How many days back the provider's archive goes.
ARCHIVE_DAYS = 7
# Parsed blocks kept in memory (see read_channels): live lookups reread the same block, and
# parsing it was most of a channel start (0.4-0.5 s on a TV stick).
READ_KEPT = 2
_read = collections.OrderedDict()
_read_lock = threading.Lock()


def block_path(cache_dir, date, offset):
    """Return where the block of `date` (UTC) from hour `offset` is kept in cache_dir."""
    return os.path.join(cache_dir, "%s-%02d.v%d.json.gz" % (date, offset, BLOCK_VERSION))


def drop_blocks(cache_dir, kept):
    """Remove the kept blocks out of the range last asked for (days gone by)."""
    for name in os.listdir(cache_dir) if cache_dir else ():
        if name not in kept:
            with contextlib.suppress(OSError):
                os.remove(os.path.join(cache_dir, name))


class GuideBlock:
    """One 3-hour guide block; a kept one is read only when its programmes are asked for.

    The export detects changes by digest without reading a week's programmes (see tv.iptvfiles.export).
    """

    def __init__(self, path=None, stations=None, programmes=None, channels=None):
        self._path = path
        self._stations = stations
        self._channels = channels
        self.programmes = sum(map(len, channels.values())) if programmes is None else programmes

    def channels(self):
        """Return its programmes by station ({} if its file is gone meanwhile)."""
        if self._channels is not None:
            return self._channels
        return read_channels(self._path, self._stations) or {}

    def digest(self):
        """Return a digest of what it holds: of its file, if kept."""
        if self._channels is not None:
            content = json.dumps(self._channels, sort_keys=True, ensure_ascii=False).encode("utf-8")
        else:
            try:
                with open(self._path, "rb") as f:
                    content = f.read()
            except OSError:
                content = b""
        return hashlib.sha1(content).hexdigest()


def block_header(path, stations, date, offset, any_stations=False, fresh=None):
    """Return a kept block's header ({"stations", "programmes"}) if still good for these stations; else None.

    :param any_stations: accept whatever stations it was kept for (the caller checks)
    :param fresh: how long a block not over yet stays good (default: by distance, see NEAR)
    """
    try:
        fetched = os.path.getmtime(path)
    except (OSError, TypeError):
        return None
    start = calendar.timegm(time.strptime(date, "%Y-%m-%d")) + offset * 3600
    fresh = fresh or (FAR_BLOCK_FRESH if start - time.time() > NEAR else BLOCK_FRESH)
    if fetched < start + 3 * 3600 and time.time() - fetched > fresh:
        return None
    try:
        with gzip.open(path, "rt", encoding="utf-8") as f:
            header = json.loads(f.readline())
    except (OSError, EOFError, ValueError):
        return None
    if not any_stations and header["stations"] is not None and (stations is None or not stations <= set(header["stations"])):
        return None  # kept for fewer channels than wanted now
    return header


def read_channels(path, stations):
    """Return a kept block's programmes of these stations (all if None); None if unreadable.

    The result is shared with later readers (see READ_KEPT): do not mutate it.
    """
    try:
        info = os.stat(path)
    except (OSError, TypeError):
        return None
    key = (path, info.st_mtime_ns, info.st_size)  # a block fetched again is another file
    with _read_lock:
        channels = _read.get(key)
    if channels is None:
        try:
            with gzip.open(path, "rt", encoding="utf-8") as f:
                f.readline()  # the header
                channels = json.loads(f.read())
        except (OSError, EOFError, ValueError):
            return None
        with _read_lock:
            _read[key] = channels
            while len(_read) > READ_KEPT:
                _read.popitem(last=False)
    return {s: progs for s, progs in channels.items() if stations is None or s in stations}


def cached_block(path, stations, date, offset, any_stations=False, fresh=None):
    """Return a kept block's programmes if still good for these stations; else None."""
    if block_header(path, stations, date, offset, any_stations, fresh) is None:
        return None
    return read_channels(path, stations)


def drop_old_blocks(cache_dir):
    """Remove kept blocks older than the archive."""
    oldest = time.strftime("%Y-%m-%d", time.gmtime(time.time() - (ARCHIVE_DAYS + 1) * 86400))
    for name in os.listdir(cache_dir):
        if name[:10] < oldest:
            with contextlib.suppress(OSError):
                os.remove(os.path.join(cache_dir, name))


def store_block(path, stations, channels):
    """Keep a block at `path`: a header line (its stations, how many programmes), then the programmes."""
    # Header line first so block_header need not parse the programmes.
    header = {"stations": None if stations is None else sorted(stations), "programmes": sum(map(len, channels.values()))}
    with contextlib.suppress(OSError):  # fetched again next time
        # dumps+write: json.dump() into a file is much slower.
        atomicfile.write(path, json.dumps(header) + "\n" + json.dumps(channels))
