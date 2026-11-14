"""Playing the live channel again that was on when Kodi went to sleep or into the background.

On waking Kodi resumes what was watched back but never a live channel, so that is played again here.
Back from another HDMI input, Kodi closes the live channel the TV paused on the way out, with no
sleep or wake notice: a live stop with no key pressed for a while counts as that return.
"""

import threading
import time

# Going to sleep, Kodi stops playing a moment before or after it says so: a live channel
# stopped this recently counts as playing. On waking, it plays again after Kodi's own resume jobs.
SLEEP_STOP = 30
WAKE_DELAY = 5
# A stop this long (seconds) after the last key or button: not the user's, so Kodi's on a return.
RETURN_IDLE = 5
# A channel played again on a return that stops on its own within this many seconds is not played
# again: a stream that keeps stopping is not restarted over and over.
SHORT_PLAY = 10


class WakeResume:
    """Follow which live channel plays, and play it again on waking up if it played when Kodi went to sleep.

    :param play_live: play_live(channel, why) opens a live channel's stream and plays it
    :param is_playing: is_playing() returns whether Kodi plays anything
    """

    def __init__(self, play_live, is_playing):
        self._play_live = play_live
        self._is_playing = is_playing
        # Set from Kodi's player callbacks, read from its monitor's.
        self._lock = threading.Lock()
        self._live = None  # (channel, when it stopped or None while it plays): the last live channel
        self._resume = None  # the live channel to play again on waking up
        self._started = 0  # when the live channel playing started
        self._replayed = None  # the id of the live channel playing because of a return

    def playing(self, channel):
        """Note what plays now: a live channel of ours, or None for anything else."""
        with self._lock:
            if channel and self._replayed != channel["id"]:
                self._replayed = None
            self._live = (channel, None) if channel else None
            self._started = time.time()

    def stopped(self, idle, next_on_its_way):
        """Note that what played stopped: a live channel playing until now stopped now.

        A live channel stopped with no key pressed for RETURN_IDLE seconds and nothing else on its way
        is played again (see the module's docstring).

        :param idle: seconds since the last key or button (Kodi's global idle time)
        :param next_on_its_way: whether another stream of ours is already starting (a switch, a renewal)
        """
        now = time.time()
        with self._lock:
            if not self._live or self._live[1] is not None:
                return
            channel = self._live[0]
            self._live = (channel, now)
            stopped_again = self._replayed == channel["id"] and now - self._started < SHORT_PLAY
            if next_on_its_way or idle < RETURN_IDLE or stopped_again:
                self._replayed = None
                return
            self._replayed = channel["id"]
        self._play_later(channel, "after a return")

    def on_power(self, method):
        """Handle System.OnSleep / System.OnWake (the TV off and on)."""
        if method == "System.OnSleep":
            with self._lock:
                live = self._live
            recent = live and (live[1] is None or time.time() - live[1] < SLEEP_STOP)
            self._resume = live[0] if recent else None
        elif method == "System.OnWake" and self._resume:
            channel, self._resume = self._resume, None
            self._play_later(channel, "after waking up")

    def _play_later(self, channel, why):
        """Play the live channel again after WAKE_DELAY, once Kodi's own resume jobs are done."""
        timer = threading.Timer(WAKE_DELAY, self._play_again, (channel, why))
        timer.daemon = True
        timer.start()

    def _play_again(self, channel, why):
        """Play the live channel again, unless something plays already."""
        if self._is_playing():
            return
        self._play_live(channel, why)
