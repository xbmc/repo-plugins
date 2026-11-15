"""A lock across Kodi's add-on processes: a Home window property marked with when its holder took it."""

import os
import threading
import time

# Seconds a new holder waits to see its mark stay: two that found the lock free at once both set
# theirs, and only the last one's stays.
SETTLE = 0.2


class HomeLock:
    """One holder at a time of a Home window property; a mark older than `stale` is a crashed holder's.

    :param home: Kodi's Home window (see kodiutil.home), whose properties every process shares
    :param name: the property
    :param stale: seconds after which a mark no longer holds the lock
    """

    def __init__(self, home, name, stale):
        self._home = home
        self._name = name
        self._stale = stale
        self._mark = None

    def held(self):
        """Return whether a holder's mark is set and not stale."""
        mark = self._home.getProperty(self._name)
        return bool(mark) and time.time() - float(mark.split()[0]) < self._stale

    def take(self):
        """Set this holder's mark, whoever held the lock."""
        # The process and thread too: two holders taking it in the same instant still tell their marks apart.
        self._mark = "%f %d-%d" % (time.time(), os.getpid(), threading.get_ident())
        self._home.setProperty(self._name, self._mark)

    def try_take(self):
        """Take the lock if it is free; return whether this holder has it (see SETTLE)."""
        if self.held():
            return False
        self.take()
        time.sleep(SETTLE)
        return self.is_mine()

    def is_mine(self):
        """Return whether the mark set is this holder's (two taking it at once: the last one's stays)."""
        return self._mark is not None and self._home.getProperty(self._name) == self._mark

    def release(self):
        """Clear the mark, if it is still this holder's."""
        if self.is_mine():
            self._home.clearProperty(self._name)
