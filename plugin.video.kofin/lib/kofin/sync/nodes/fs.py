"""The one place the node generator deletes anything.

Every file and folder kofin generates under Kodi's library and playlist
trees carries the ``kofin`` prefix, and every deletion here is gated on it:
hand-made node files and the user's own playlists share those directories
and are never ours to remove. The two prefix-less files kofin owns -- a
parent folder's ``index.xml`` and the managed playlist folder's icon -- go
only when the caller names them (``also``), on a full teardown. A folder is
only ever removed once it is empty, so a foreign entry keeps it alive.

Plain ``os`` throughout: the paths are ``special://profile`` translated to
a local directory on every platform Kodi runs on, and nothing here ever
names a VFS protocol. That is also what lets the generators run in a test
without a Kodi filesystem fake.
"""

import os
from collections.abc import Iterable

from kofin.core.log import Logger

LOG = Logger(__name__)

# The gate. Spelled once; every managed name is built from it.
PREFIX = "kofin"


def is_managed(name: str) -> bool:
    return name.startswith(PREFIX)


def listdir(root: str) -> tuple[list[str], list[str]]:
    """``(dirs, files)`` of a directory that may not exist, sorted."""
    dirs: list[str] = []
    files: list[str] = []
    if not os.path.isdir(root):
        return dirs, files
    for entry in sorted(os.listdir(root)):
        if os.path.isdir(os.path.join(root, entry)):
            dirs.append(entry)
        else:
            files.append(entry)
    return dirs, files


def delete_file(path: str, label: str = "node") -> None:
    try:
        os.remove(path)
    except FileNotFoundError:
        return
    LOG.debug("DELETE %s %s", label, path)


def entry(root: str, name: str) -> str:
    """The path of ``name`` in ``root``, refused (ValueError) unless it
    resolves to an entry of ``root`` itself, links followed. A generated
    name carries a library's id, and a library's node folder is emptied of
    whatever the pass did not write."""
    path = os.path.join(root, name)
    if os.path.dirname(os.path.realpath(path)) != os.path.realpath(root):
        raise ValueError("%r is not an entry of %s" % (name, root))
    return path


def remove_empty(root: str) -> bool:
    """Remove a directory when nothing is left in it."""
    if not os.path.isdir(root):
        return False
    dirs, files = listdir(root)
    if dirs or files:
        return False
    os.rmdir(root)
    return True


def remove_folder(folder: str, label: str = "node") -> None:
    """A generated folder and the files in it.

    Managed folders only -- the caller has checked the prefix. A hand-made
    subfolder inside keeps the folder itself alive.
    """
    _, files = listdir(folder)
    for name in files:
        delete_file(os.path.join(folder, name), label)
    remove_empty(folder)


def remove_managed_entries(
    root: str,
    keep: Iterable[str] = (),
    also: Iterable[str] = (),
    label: str = "node",
) -> list[str]:
    """Every managed entry under ``root`` not named in ``keep``, plus the
    prefix-less files named in ``also``. Returns what was removed."""
    kept = set(keep)
    extra = set(also)
    removed: list[str] = []
    dirs, files = listdir(root)
    for name in dirs:
        if is_managed(name) and name not in kept:
            remove_folder(os.path.join(root, name), label)
            removed.append(name)
    for name in files:
        if (is_managed(name) and name not in kept) or name in extra:
            delete_file(os.path.join(root, name), label)
            removed.append(name)
    return removed
