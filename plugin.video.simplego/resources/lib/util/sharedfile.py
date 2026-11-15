"""A JSON file that every client of the profile reads and writes (the service and each plugin call)."""

import os

from resources.lib.util import atomicfile


class SharedJson:
    """A dict kept in a JSON file: read again only when the file changed, changed under a lock every writer holds.

    :param path: the file
    :param lock: lock() gives the context in which a change is made (read, edited, written) against every other client
    """

    def __init__(self, path, lock):
        self._path = path
        self._lock = lock
        self._content = None
        self._version = None

    def read(self):
        """Return the content ({} if none); not to be changed in place (see change)."""
        version = _read_version(self._path)
        if self._content is None or version != self._version:
            self._content, self._version = _read(self._path), version
        return self._content

    def change(self, edit):
        """Change the content as edit(content) does, on what the file has now: other clients' changes stay."""
        with self._lock():
            content = _read(self._path)
            edit(content)
            atomicfile.write_json(self._path, content)
            self._content, self._version = content, _read_version(self._path)


def _read(path):
    return atomicfile.read_json(path, {}) or {}


def _read_version(path):
    """Return what tells a file's versions apart (written whole as a new file: its inode changes); None if missing."""
    try:
        st = os.stat(path)
    except OSError:
        return None
    return st.st_ino, st.st_mtime_ns, st.st_size
