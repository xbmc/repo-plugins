#
#      Copyright (C) 2014 Tommy Winther, TermeHansen
#
#  https://github.com/xbmc-danish-addons/plugin.video.drnu
#
#  This Program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2, or (at your option)
#  any later version.
#
#  This Program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this Program; see the file LICENSE.txt.  If not, write to
#  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
#  http://www.gnu.org/copyleft/gpl.html
#
"""Scheduling and running of the background re-cache job.

The job is the same recache_items() crawl the addon's settings button
triggers via '?re-cache=1', but run from the addon's service: it fires
daily at the time configured in 'recache.time' (persisted across restarts
in a small state file), and only while Kodi is idle if the idle gate is
enabled. Deliberately free of Kodi imports: the progress dialog, idle
check and Api construction are injected, which keeps the logic unit-
testable without the Kodi stub modules.
"""
from contextlib import suppress
from datetime import datetime, time, timedelta
from pathlib import Path
from typing import Any, Callable, Optional

STATE_FILE = 'recache.state'
DEFAULT_MAX_SECONDS = 30 * 60


def parse_time_setting(value: str) -> Optional[time]:
    """Parse a Kodi time setting ('HH:MM') into a datetime.time.

    Tolerates 'H:MM' and 'HH:MM:SS'; returns None for anything invalid.
    """
    try:
        parts = [int(p) for p in value.strip().split(':')]
        hour, minute = parts[0], parts[1]
    except (ValueError, IndexError):
        return None
    if not 0 <= hour <= 23 or not 0 <= minute <= 59:
        return None
    return time(hour, minute)


def due_slot(last: Optional[datetime], now: datetime, at: time) -> Optional[datetime]:
    """The most recent daily slot at time 'at' in (last, now], or None.

    A slot at exactly 'last' is not re-reported. With last=None only the
    slot at 'now' itself matches (used right after seeding).
    """
    candidate = datetime.combine(now.date(), at)
    if candidate > now:
        candidate = datetime.combine(now.date() - timedelta(days=1), at)
    if candidate <= now and (last is None or candidate > last):
        return candidate
    return None


class RecacheState:
    """Persists the last daily slot the service acted on."""

    def __init__(self, cache_path: Path) -> None:
        self.path = cache_path / STATE_FILE
        self.last_slot: Optional[datetime] = None

    def load(self) -> Optional[datetime]:
        if self.path.exists():
            try:
                self.last_slot = datetime.fromisoformat(self.path.read_text().strip())
            except ValueError:
                self.last_slot = None
        return self.last_slot

    def save(self, slot: datetime) -> None:
        self.path.write_text(slot.isoformat())
        self.last_slot = slot


def recache_due(state: RecacheState, at: time, now: datetime) -> Optional[datetime]:
    """The daily slot to act on in this pass, or None.

    A missing state file means the service has never run: seed it with
    'now' so a fresh install does not fire immediately. A slot missed
    while Kodi was down is caught up on the first pass.
    """
    if not state.path.exists():
        state.save(now)
        return None
    last = state.load()
    if last is None:
        state.save(now)
        return None
    return due_slot(last, now, at)


class IdleAbortProgress:
    """Adapts an xbmcgui.DialogProgressBG to the iscanceled() protocol.

    The background dialog has no cancel button; 'canceled' instead means
    the user became active again, so recache_items() aborts between pages
    and the slot is left unsaved for the next idle pass.

    The dialog is optional: when it is None (the service could not create
    one) progress updates are dropped and only the abort signal remains.

    The deadline is a wall-clock cap: when passed, the crawl reports
    canceled once it is exceeded, so a wedged crawl (network stall, skin
    issue) cannot hold the dialog open forever.

    The shutdown check is consulted independently of the idle gate: the
    crawl must also stop between requests when Kodi is exiting, even when
    the user disabled the idle gate and nothing is playing.

    updates counts the progress callbacks and abort_reason records why
    the crawl stopped, for the service log.
    """

    def __init__(self, dialog: Any, idle_check: Optional[Callable[[], bool]] = None,
                 deadline: Optional[datetime] = None,
                 shutdown_check: Optional[Callable[[], bool]] = None) -> None:
        self.dialog = dialog
        self.idle_check = idle_check or (lambda: True)
        self.deadline = deadline
        self.shutdown_check = shutdown_check or (lambda: False)
        self.was_aborted = False
        self.abort_reason = ''
        self.updates = 0

    def update(self, percent: int, msg: str) -> None:
        self.updates += 1
        if self.dialog is not None:
            self.dialog.update(int(percent), message=msg)

    def iscanceled(self) -> bool:
        if self.was_aborted:
            return True
        if self.deadline is not None and datetime.now() >= self.deadline:
            self.was_aborted = True
            self.abort_reason = f'deadline exceeded after {self.updates} progress updates'
            return True
        if self.shutdown_check():
            self.was_aborted = True
            self.abort_reason = 'Kodi is shutting down'
            return True
        if self.idle_check():
            return False
        self.was_aborted = True
        self.abort_reason = 'user became active'
        return True


def _log(log_func: Optional[Callable[[str], None]], msg: str) -> None:
    if log_func:
        log_func(msg)


def _close_dialog(dialog: Any) -> None:
    """Dismiss the background progress dialog, tolerating a missing one.

    DialogProgressBG.close() only marks Kodi's handle finished; Kodi removes
    the handle and closes the window on a later GUI frame. A handle that is
    never closed stays in Kodi's list, so close it on every exit path, and
    swallow a close failure rather than masking the crawl result with it.
    """
    if dialog is None:
        return
    with suppress(Exception):
        dialog.close()


def recache_pass(get_setting: Callable[[str], str], api_factory: Callable[[], Any],
                 cache_path: Path, now: datetime, idle_check: Callable[[], bool],
                 dialog_factory: Callable[[], Any],
                 progress_factory: Optional[Callable[[Any, Callable[[], bool]], Any]] = None,
                 log_func: Optional[Callable[[str], None]] = None,
                 shutdown_check: Optional[Callable[[], bool]] = None) -> bool:
    """One service pass: run the recache crawl if the cron slot is due.

    shutdown_check is consulted by the crawl between requests so an exit
    request stops it even when the idle gate is disabled; it defaults to
    never shutting down, which only matters for direct callers.

    Returns True when the crawl ran to completion (slot is marked done),
    False when it was skipped, blocked by the idle gate, or aborted.
    """
    if get_setting('recache.enabled') != 'true' or get_setting('recache.service') != 'true':
        return False
    at = parse_time_setting(get_setting('recache.time'))
    if at is None:
        _log(log_func, f'drnu service: invalid recache.time setting '
                       f'{get_setting("recache.time")!r}, skipping re-cache')
        return False
    state = RecacheState(cache_path)
    slot = recache_due(state, at, now)
    if slot is None:
        return False
    gate_enabled = get_setting('recache.service.idle') != 'false'
    if gate_enabled and not idle_check():
        _log(log_func, f'drnu service: re-cache due for {slot} but idle gate blocked it')
        return False

    if progress_factory is None:
        progress_factory = IdleAbortProgress
    # with the gate disabled the crawl runs to completion like the manual
    # variant; the abort signal only makes sense while the gate is active
    dialog: Any = None
    shutdown = shutdown_check or (lambda: False)

    try:
        # the factory returns a created dialog (or None when Kodi has no GUI)
        dialog = dialog_factory()
        # deadline on the real wall clock: IdleAbortProgress compares it
        # against datetime.now(), not the injected scheduling 'now'
        progress = progress_factory(dialog, idle_check if gate_enabled else None,
                                    datetime.now() + timedelta(seconds=DEFAULT_MAX_SECONDS))
        # the shutdown check must apply even when the idle gate is disabled,
        # so set it on the progress object instead of extending the factory
        # call signature (the tests inject a three-argument factory)
        progress.shutdown_check = shutdown
        _log(log_func, 'drnu service: starting re-cache job')

        api = api_factory()
        api.recache_items(progress=progress, clear_expired=True)
        if progress.was_aborted:
            _log(log_func, f'drnu service: re-cache did not finish: {progress.abort_reason}')
            return False
        state.save(slot)
        return True
    finally:
        _close_dialog(dialog)
