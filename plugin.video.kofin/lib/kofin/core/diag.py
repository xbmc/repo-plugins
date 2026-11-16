"""Thread dumps for a library thread that will not stop.

The teardown's wait for the library thread is bounded
(``service.main.LIBRARY_JOIN_SECONDS``). When the wait goes long, write down
what every thread was doing, and say whether the one we are waiting on moved
between one look and the next: blocked and slow are indistinguishable from a
single dump and obvious from two.

Warnings rather than debug, since debug logging is usually off.
"""

import sys
import threading
import traceback
from types import FrameType
from typing import Optional

from kofin.core.log import Logger

LOG = Logger(__name__)

# Innermost frames kept per thread. Deep enough to cross a writer's call chain
# into whatever it is blocked on, short enough that a dozen threads still make
# one readable log entry.
FRAMES = 12


def _position(frame: FrameType) -> str:
    """One line naming where a thread is: the innermost frame."""
    filename = frame.f_code.co_filename.replace("\\", "/").rsplit("/", 1)[-1]
    return "%s:%d %s" % (filename, frame.f_lineno, frame.f_code.co_name)


def positions() -> dict[int, str]:
    """Innermost frame per thread id. Cheap enough to call on a poll tick."""
    return {ident: _position(frame) for ident, frame in sys._current_frames().items()}


def thread_dump(reason: str) -> dict[int, str]:
    """Log every live thread's stack; return the innermost frame of each.

    The return value is the input to :func:`describe_movement` — hold onto it
    and compare against a later dump.
    """
    frames = sys._current_frames()
    names = {thread.ident: thread.name for thread in threading.enumerate()}
    lines = ["thread dump (%s) — %d thread(s)" % (reason, len(frames))]

    for ident, frame in sorted(frames.items()):
        stack = traceback.format_stack(frame)  # outermost first
        shown = stack[-FRAMES:]
        omitted = len(stack) - len(shown)
        lines.append(
            "  --- %s (id %s)%s"
            % (
                names.get(ident, "?"),
                ident,
                " [%d outer frame(s) omitted]" % omitted if omitted else "",
            )
        )
        for entry in shown:
            lines.extend("    " + piece for piece in entry.rstrip().splitlines())

    # One entry rather than one per line: Kodi interleaves every thread's
    # logging, and a stack split across a hundred entries is unreadable.
    LOG.warning("\n".join(lines))
    return {ident: _position(frame) for ident, frame in frames.items()}


def describe_movement(
    ident: Optional[int], before: dict[int, str], after: dict[int, str]
) -> str:
    """Whether the thread got anywhere between two dumps, in words.

    "did not move" is the interesting answer: a thread parked on the same line
    for the whole deadline is blocked in a call that does not consult the stop
    flag, which is a different bug from one grinding through a long batch.
    """
    if ident is None:
        return "thread had no id to follow"
    was, now = before.get(ident), after.get(ident)
    if was is None or now is None:
        return "thread was not in both dumps"
    if was == now:
        return "did not move: still at %s" % now
    return "moved: %s -> %s" % (was, now)
