"""What the downloads are costing on disk.

Walked from the filesystem, not summed from the store:
``download.size_actual`` misses sidecars, ``.part`` files and rows the store
lost track of. The walk is stat-only.

The three category directories are counted separately, plus "other" for
everything else under the root, so the total agrees with ``du``.
"""

import os
from typing import NamedTuple

from kofin.core.log import Logger
from kofin.downloads import files

LOG = Logger(__name__)

# The three directories files.item_dirs writes into, in the order the report
# lists them.
CATEGORIES: tuple[str, ...] = (files.MOVIES_DIR, files.SHOWS_DIR, files.MUSIC_DIR)

# A ceiling on the walk, because this runs in the plugin process with a
# person waiting on it. Well past any real downloads folder (a 200k-entry
# tree is not one), and reaching it is reported rather than hidden: a total
# that silently stopped counting is worse than no total.
MAX_ENTRIES = 200000


class Bucket(NamedTuple):
    label_id: int  # a Kodi or kofin string id, resolved by the caller
    key: str
    size: int
    file_count: int


class Usage(NamedTuple):
    root: str
    buckets: list[Bucket]
    total: int
    free: int  # -1 when the filesystem would not say
    capped: bool

    @property
    def empty(self) -> bool:
        return self.total == 0 and not any(bucket.file_count for bucket in self.buckets)


# Kodi's own labels for the three categories — no kofin string needed, and
# they are already translated in every locale Kodi ships.
CATEGORY_LABELS: dict[str, int] = {
    files.MOVIES_DIR: 342,  # Movies
    files.SHOWS_DIR: 20343,  # TV shows
    files.MUSIC_DIR: 2,  # Music
}

# kofin's own, because "Other" alone in a list of Movies/TV shows/Music
# reads as another media type rather than as "not ours".
OTHER_LABEL = 30834


def scan(root: str) -> Usage:
    """Walk ``root`` and total it by category.

    A missing or unreadable root is an empty report, not an error: the
    folder legitimately does not exist until the first download lands, and
    the caller says so in words rather than showing three zeroes.
    """
    counter = _Counter()
    buckets: list[Bucket] = []
    for name in CATEGORIES:
        size, count = counter.walk(os.path.join(root, name))
        buckets.append(Bucket(CATEGORY_LABELS[name], name, size, count))

    other_size, other_count = _other(root, counter)
    if other_count:
        buckets.append(Bucket(OTHER_LABEL, "", other_size, other_count))

    return Usage(
        root=root,
        buckets=buckets,
        total=sum(bucket.size for bucket in buckets),
        free=files.free_bytes(root),
        capped=counter.capped,
    )


def _other(root: str, counter: "_Counter") -> tuple[int, int]:
    """Everything directly under the root that is not one of ours."""
    size = 0
    count = 0
    try:
        entries = list(os.scandir(root))
    except OSError:
        return (0, 0)
    for entry in entries:
        if entry.name in CATEGORIES:
            continue
        if entry.is_dir(follow_symlinks=False):
            found_size, found_count = counter.walk(entry.path)
        else:
            found_size, found_count = (_size_of(entry), 1)
        size += found_size
        count += found_count
    return (size, count)


class _Counter:
    """One walk's budget, shared across the category passes."""

    def __init__(self) -> None:
        self.seen = 0
        self.capped = False

    def walk(self, directory: str) -> tuple[int, int]:
        size = 0
        count = 0
        # Explicit stack rather than recursion: a downloads folder is
        # shallow, but a symlinked one need not be, and this cannot be the
        # thing that raises RecursionError in the plugin process.
        pending = [directory]
        while pending:
            current = pending.pop()
            try:
                entries = list(os.scandir(current))
            except OSError:
                continue
            for entry in entries:
                if self.seen >= MAX_ENTRIES:
                    self.capped = True
                    return (size, count)
                self.seen += 1
                # follow_symlinks=False throughout: a link into the media
                # library would count someone else's files as kofin's, and
                # a link loop would never end.
                if entry.is_dir(follow_symlinks=False):
                    pending.append(entry.path)
                    continue
                size += _size_of(entry)
                count += 1
        return (size, count)


def _size_of(entry: "os.DirEntry[str]") -> int:
    try:
        return int(entry.stat(follow_symlinks=False).st_size)
    except OSError:
        return 0
