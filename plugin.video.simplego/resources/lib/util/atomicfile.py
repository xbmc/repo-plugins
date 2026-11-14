"""Files written whole or not at all, by any of the add-on's processes and threads."""

import contextlib
import gzip
import os
import threading


def read_json(path, default=None):
    """Return a JSON file's content; `default` if it is missing or unreadable (a crash's leftover)."""
    import json  # here: most callers write text, not JSON

    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def write_json(path, value, **dumps):
    """Write a value as a JSON file, whole or not at all, its folder made if missing."""
    import json

    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    write(path, json.dumps(value, **dumps))


def write(path, text):
    """Write a file whole or not at all (gzipped for a .gz name)."""
    with writer(path) as add:
        add(text)


@contextlib.contextmanager
def writer(path):
    """Yield add(text) to build the file; it replaces `path` at the end, or is dropped on error.

    Gzipped for a .gz name.
    """
    # Per process and thread: concurrent exports must not share it (Windows refuses).
    tmp = "%s.%d-%d.tmp" % (path, os.getpid(), threading.get_ident())
    try:
        if path.endswith(".gz"):
            # Level 1: the files stay local, so speed beats size (week's guide: 2.5x faster, 25% bigger).
            with gzip.GzipFile(tmp, "wb", compresslevel=1, mtime=0) as f:
                yield lambda text: f.write(text.encode("utf-8"))
        else:
            with open(tmp, "w", encoding="utf-8") as f:
                yield f.write
        os.replace(tmp, path)
    except BaseException:
        with contextlib.suppress(OSError):
            os.remove(tmp)
        raise
