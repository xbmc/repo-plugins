"""The state file several clients share: its content, its parsing and its lock across threads and interpreters."""

import contextlib
import json
import os
import threading
import time

from resources.lib.util import atomicfile


def parse(text):
    """Return the parsed state; {} if empty or broken."""
    try:
        return json.loads(text) if text else {}
    except ValueError:
        return {}


class State(dict):
    """The client's state (session.json): login, device identity and kept answers, shared by its parts.

    Each part writes only its own keys and asks their owner to drop one; only a logout clears them all.
    One object for all the parts, changed in place: they hold it, and save() takes up other clients' writes.

    :param path: the state file
    :param debug: debug(message), where its timings go
    :param lock_wait: lock_wait(seconds) waits for the file's lock, True to give up (see state_lock)
    """

    def __init__(self, path, debug=None, lock_wait=None):
        super().__init__()
        self._path = path
        self._debug = debug or (lambda message: None)
        self._lock_wait = lock_wait
        began = time.time()
        text = self._read()
        self.update(parse(text))
        self._saved = parse(text)  # as on disk when last read or written
        self._debug("state: %d kB read and parsed twice in %d ms" % (len(text) // 1024, (time.time() - began) * 1000))

    def _read(self):
        try:
            with open(self._path) as f:
                return f.read()
        except OSError:
            return ""

    def on_disk(self):
        """Return the state as the file has it now (other clients' writes included), not taken up."""
        return parse(self._read())

    def lock(self):
        """Hold the state file for a change of several steps (see state_lock)."""
        return state_lock(self._path, self._lock_wait)

    def save(self):
        """Merge this client's changed keys into the file and take up everyone else's.

        Several clients share the file and Keycloak rotates the refresh token on every
        renewal, so writing back a whole older copy would undo another renewal and log out.
        """
        began = time.time()
        with self.lock():
            locked = time.time()
            text = self._read()
            current = parse(text)
            changed = False
            for key in set(self) | set(self._saved):
                if key not in self:
                    if key in current:
                        del current[key]
                        changed = True
                elif key not in self._saved or self[key] != self._saved[key]:
                    current[key] = self[key]
                    changed = True
            if changed:
                os.makedirs(os.path.dirname(self._path), exist_ok=True)
                # dumps+write is 4x faster than json.dump(); re-parsing beats copy.deepcopy.
                text = json.dumps(current)
                atomicfile.write(self._path, text)
            self.clear()
            self.update(current)
            self._saved = parse(text)
        self._debug(
            "state saved: %d kB, %s in %d ms (lock wait %d ms)"
            % (len(text) // 1024, "written" if changed else "unchanged", (time.time() - locked) * 1000, (locked - began) * 1000)
        )

    def change(self, edit):
        """Change the state as edit(state) does, on what the file has now (other clients' writes taken up), and save.

        Under the lock: a list several clients add to (the open sessions) must not lose another's entry.
        """
        with self.lock():
            self.save()
            edit(self)
            self.save()

    def keep_only(self, keys):
        """Drop every key but these, and save (a logout: the device's identity stays)."""
        for key in [k for k in self if k not in keys]:
            del self[key]
        self.save()


# Threads share this lock; other interpreters (Kodi runs the service and each plugin run in
# their own, on Android in one OS process) use a lock file beside the state file.
_STATE_LOCK = threading.RLock()
_FILE_LOCKS = {}  # lock file -> [depth, descriptor], held by this interpreter
# Past this the work goes on unlocked rather than hang Kodi (a stuck renewal may take its timeouts).
LOCK_WAIT = 45
# Seconds between tries for a lock file another interpreter holds.
LOCK_RETRY = 0.05

try:
    import fcntl
except ImportError:  # Windows
    fcntl = None
    try:
        import msvcrt
    except ImportError:
        msvcrt = None


@contextlib.contextmanager
def state_lock(state_file, wait=None):
    """Hold the state file for one read-change-write against every other client.

    Re-entrant within the interpreter: a renewal saves inside its own turn.

    :param wait: wait(seconds) waits for the lock's turn, True to give up (Kodi exiting); else a plain sleep
    """
    path = state_file + ".lock"
    with _STATE_LOCK:
        held = _FILE_LOCKS.setdefault(path, [0, None])
        if held[0] == 0:
            held[1] = _lock_file(path, wait)
        held[0] += 1
        try:
            yield
        finally:
            held[0] -= 1
            if held[0] == 0:
                _unlock_file(held[1])
                del _FILE_LOCKS[path]


def _lock_file(path, wait=None):
    """Take the lock file; return its descriptor, or None if it could not be had in LOCK_WAIT."""
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        fd = os.open(path, os.O_RDWR | os.O_CREAT, 0o600)
    except OSError:
        return None
    deadline = time.monotonic() + LOCK_WAIT
    while True:
        try:
            # flock, not lockf: lockf locks are per process, and the interpreters share
            # Kodi's process; flock locks are per open file.
            if fcntl:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            elif msvcrt:
                msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
            return fd
        except OSError:
            if time.monotonic() > deadline or _pause(LOCK_RETRY, wait):
                os.close(fd)
                return None


def _pause(seconds, wait):
    """Wait a moment for the lock; return True if the wait was cut short to give up."""
    if wait:
        return bool(wait(seconds))
    time.sleep(seconds)
    return False


def _unlock_file(fd):
    if fd is None:
        return
    with contextlib.suppress(OSError):
        if fcntl:
            fcntl.flock(fd, fcntl.LOCK_UN)
        elif msvcrt:
            os.lseek(fd, 0, os.SEEK_SET)
            msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
    os.close(fd)
