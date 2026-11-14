"""Playing a catch-up programme across its key changes, one part per key (see keychanges).

Each proxy declares one part's keys (see licproxy); before a change, or on a jump, the
stream restarts through the next part's proxy. InputStream Adaptive licenses one key pair
per stream, and on Android Kodi cannot open a second video decoder within one (a period
per key stopped the picture: "InstanceGuard locked").

A live channel's key change is noticed at the live edge (see manifest.ManifestRewriter._watch_live_keys) while
the player is behind it: the stream restarts when the player gets there, from the live edge
again, its new proxy declaring the new key.
"""

import threading
import time

import xbmc

from resources.lib import kodiutil
from resources.lib.stream import dash

# The next part's manifest and keys are read this many seconds ahead.
PREPARE_AHEAD = 20
# The restart is timed RESTART_BEFORE ahead of the change (InputStream Adaptive decodes a
# little ahead, so no old-key frame shows), by a timer once within TIME_WITHIN.
RESTART_BEFORE = 0.5
TIME_WITHIN = 3
# Seconds after a start while Kodi still seeks to its start offset.
SETTLE = 5
# Live: how far behind the live edge the player is taken to be when Kodi does not say (the live delay
# ISA is given, see playitem), the most it can be (the manifest's 15 minutes, and some), and how
# long after it reaches the change the restart comes (a moment late beats the old key's last
# segment playing on the new stream).
LIVE_LAG = dash.LIVE_DELAY
LIVE_LAG_MAX = 16 * 60
LIVE_RESTART_AFTER = 1


class KeyFollower:
    """Which part's proxy a stream plays through, and the switch to the next one.

    restart(part, seconds), set by the player, restarts through part's proxy (seconds None: live, from
    its edge); unset, nothing is followed.

    :param proxy: the proxy the stream starts with (a licproxy.LicenceProxy)
    :param make_proxy: make_proxy(part) returns a proxy of the same stream declaring that part's keys
    :param known: {key: proxy.found_changes} kept across streams, so a replay (a switch is one)
        needs no search
    :param key: this programme's key in `known`
    """

    def __init__(self, proxy, make_proxy, known=None, key=None):
        self.proxy = proxy
        self.restart = None
        self.switching = 0  # when the switch to another part's proxy began
        self._make_proxy = make_proxy
        self._known, self._key = known, key
        self._next = None  # the next part's proxy, made ready ahead
        self._old = None  # while switching, the one before
        self._timer = None  # the restart timed for the coming change
        self._started_at = 0
        self._restarted = 0

    def started(self):
        """Note that playback (re)started now: the position settles for SETTLE seconds."""
        self._started_at = time.time()

    def follow(self, position, player, now=None):
        """Act once a second while it plays: prepare the next part, time its start, or follow a jump."""
        now = now or time.time()
        if getattr(self.proxy, "live_changes", None):
            return self._follow_live(player, now)
        changes = self.proxy.change_times
        if not changes or self.switching:
            return
        if self._key and self.proxy.found_changes and self._known is not None:
            self._known.setdefault(self._key, self.proxy.found_changes)
        if now - self._started_at < SETTLE or self._restarted or not self.restart:
            return
        part = self.proxy.part_of(position)
        ahead = changes[self.proxy.part] if self.proxy.part < len(changes) else None
        if ahead is not None and ahead - position <= PREPARE_AHEAD and self._next is None:
            self._next = self.part_proxy(self.proxy.part + 1)
        if part != self.proxy.part:
            self._restart_now(part, position)  # a jump into another key's part
        elif ahead is not None and ahead - position <= TIME_WITHIN and self._timer is None:
            self._time_restart(player, part + 1, ahead, ahead - position)

    def _follow_live(self, player, now):
        """Time the restart for when the player reaches the first live key change noticed."""
        if self.switching or self._restarted or not self.restart or self._timer is not None:
            return
        self._time_live_restart(player, self._live_left(player, now))

    def _live_left(self, player, now):
        """Return the seconds until the restart for the first live key change noticed is due."""
        noticed, before_edge = self.proxy.live_changes[0][:2]
        lag = self._live_lag(player)
        # The change is further behind the edge by the time passed since it was noticed.
        left = lag - (before_edge + now - noticed) + LIVE_RESTART_AFTER
        kodiutil.log("live key change: the player %.0f s behind the edge, restart in %.1f s" % (lag, left), xbmc.LOGDEBUG)
        return left

    def _time_live_restart(self, player, left):
        self._timer = threading.Timer(max(0, left), self._at_live_change, (player,))
        self._timer.daemon = True
        self._timer.start()

    @staticmethod
    def _live_lag(player):
        """Return how far (seconds) the player is behind the live edge: its time to the stream's end, else LIVE_LAG."""
        try:
            lag = player.getTotalTime() - player.getTime()
        except RuntimeError:
            return LIVE_LAG
        return lag if 0 < lag < LIVE_LAG_MAX else LIVE_LAG

    def _at_live_change(self, player):
        self._timer = None
        if self._restarted or self.switching:
            return
        left = self._live_left(player, time.time())
        if left > 1:  # paused or rewound meanwhile: not there yet
            return self._time_live_restart(player, left)
        self._restarted = time.time()
        kodiutil.log("restarting the live stream for its new key")
        self.restart(self.proxy.part, None)

    def _time_restart(self, player, part, ahead, left):
        """Restart RESTART_BEFORE seconds before the change at `ahead`, `left` seconds away."""
        self._timer = threading.Timer(max(0, left - RESTART_BEFORE), self._at_change, (player, part, ahead))
        self._timer.daemon = True
        self._timer.start()

    def _at_change(self, player, part, ahead):
        self._timer = None
        if self._restarted or self.switching:
            return
        try:
            left = ahead - player.getTime()
        except RuntimeError:
            return
        if left > RESTART_BEFORE + 0.3:
            self._time_restart(player, part, ahead, left)  # paused or held up: not yet
        elif left > -1:
            # InputStream Adaptive resumes at the first segment after the position asked
            # for, so ask a moment before the change to land on its first segment.
            self._restart_now(part, ahead - 0.3)
        # (Past it already: a jump, which follow handles.)

    def _restart_now(self, part, target):
        self._restarted = time.time()
        kodiutil.log("restarting at %.1f s with the keys of part %d" % (target, part))
        self.restart(part, target)

    def part_proxy(self, part):
        """Return a proxy of this stream declaring another part's keys, reading them already."""
        if self._next is not None and self._next.part == part:
            return self._next
        proxy = self._make_proxy(part)
        proxy.prefetch()
        return proxy

    def switch(self, proxy):
        """Note that Kodi is about to play the same stream through another part's proxy."""
        self._cancel_timer()
        self._old, self.proxy, self._next = self.proxy, proxy, None
        self.switching = time.time()

    def switched(self):
        """Note that the new proxy plays: the old one goes."""
        if self._old is not None:
            self._old.stop()
            self._old = None
        self.switching = 0
        self._restarted = 0
        self.started()

    def hold(self):
        """Call off a restart timed for this stream: another one is on its way."""
        self._cancel_timer()

    def close(self, keep=None):
        """Cancel the timed restart and stop every proxy of this stream but `keep`."""
        self._cancel_timer()
        for proxy in (self.proxy, self._old, self._next):
            if proxy is not None and proxy is not keep:
                proxy.stop()

    def _cancel_timer(self):
        if self._timer is not None:
            self._timer.cancel()
            self._timer = None
