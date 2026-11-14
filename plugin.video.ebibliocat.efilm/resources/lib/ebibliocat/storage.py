"""Atomic JSON storage and cross-process locks for concurrent Kodi invocations."""

import contextlib
import json
import os
import tempfile
import threading
import time
from pathlib import Path

from resources.lib.ebibliocat.errors import Cancelled, EfilmError

_LOCKS = {}
_LOCKS_GUARD = threading.Lock()


def ensure_directory(path):
    Path(path).mkdir(mode=0o700, parents=True, exist_ok=True)
    if os.name != "nt":
        os.chmod(path, 0o700)


def read_json(path, default=None):
    try:
        with open(path, encoding="utf-8") as source:
            return json.load(source)
    except (FileNotFoundError, ValueError, UnicodeError):
        return default
    except OSError as error:
        raise EfilmError("storage_error") from error


def write_json(path, value):
    path = Path(path)
    temporary = None
    try:
        ensure_directory(path.parent)
        descriptor, temporary = tempfile.mkstemp(prefix="." + path.name + "-", dir=path.parent)
        with os.fdopen(descriptor, "w", encoding="utf-8") as target:
            json.dump(value, target, ensure_ascii=False)
            target.flush()
            os.fsync(target.fileno())
        os.replace(temporary, path)
        temporary = None
    except (OSError, ValueError, TypeError) as error:
        raise EfilmError("storage_error") from error
    finally:
        if temporary:
            with contextlib.suppress(FileNotFoundError):
                os.unlink(temporary)


@contextlib.contextmanager
def file_lock(directory, name, timeout=40, cancelled=None):
    """The lock file is persistent: unlinking it would break process exclusion."""
    path = str(Path(directory) / (name + ".lock"))
    with _LOCKS_GUARD:
        local = _LOCKS.setdefault(path, threading.Lock())
    deadline = time.monotonic() + timeout
    while not local.acquire(blocking=False):
        if cancelled and cancelled():
            raise Cancelled()
        if time.monotonic() >= deadline:
            raise EfilmError("busy")
        time.sleep(0.05)
    descriptor = None
    acquired = False
    try:
        ensure_directory(directory)
        descriptor = os.open(path, os.O_CREAT | os.O_RDWR, 0o600)
        if os.fstat(descriptor).st_size == 0:
            os.write(descriptor, b"\0")
        while not acquired:
            if cancelled and cancelled():
                raise Cancelled()
            try:
                if os.name == "nt":
                    import msvcrt

                    os.lseek(descriptor, 0, os.SEEK_SET)
                    msvcrt.locking(descriptor, msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl

                    fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
                acquired = True
            except (BlockingIOError, OSError):
                if time.monotonic() >= deadline:
                    raise EfilmError("busy") from None
                time.sleep(0.05)
        yield
    except OSError as error:
        raise EfilmError("storage_error") from error
    finally:
        if descriptor is not None:
            try:
                if acquired:
                    if os.name == "nt":
                        import msvcrt

                        os.lseek(descriptor, 0, os.SEEK_SET)
                        msvcrt.locking(descriptor, msvcrt.LK_UNLCK, 1)
                    else:
                        import fcntl

                        fcntl.flock(descriptor, fcntl.LOCK_UN)
            finally:
                os.close(descriptor)
        local.release()
