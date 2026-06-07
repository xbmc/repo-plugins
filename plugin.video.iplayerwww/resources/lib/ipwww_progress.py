
import time
import requests
import xbmc

from resources.lib import ipwww_common


class PlayState:
    UNDEFINED = 0xFF00
    PLAYING = 0xFF01
    PAUSED = 0xFF02
    STOPPED = 0xFF03


class FileProgress(xbmc.Player):
    """Monitor the play state and progress of a single file."""
    POLL_PERIOD = 1
    EVT_URL = 'https://user.ibl.api.bbc.co.uk/ibl/v1/user/plays'

    def __init__(self, episode_id, stream_id):
        super(FileProgress, self).__init__()
        self._episode_id = episode_id
        self._stream_id = stream_id
        self._playtime = 0
        self.sys_monitor = xbmc.Monitor()
        self._cur_file = None
        self._status = PlayState.UNDEFINED
        self._event_errors = 0

    @property
    def playtime(self):
        """Return the last known playtime in milliseconds"""
        return int(self._playtime * 1000)

    def onPlayBackResumed(self) -> None:
        # Can also be called when the player is just paying normally, just before switching to a new file.
        if self._status is PlayState.PAUSED:
            self._status = PlayState.PLAYING
            self.post_event('started')

    def onPlayBackPaused(self) -> None:
        if self._status is PlayState.PLAYING:
            self._status = PlayState.PAUSED
            self.post_event('paused')

    def onAVStarted(self) -> None:
        if self._status is not PlayState.UNDEFINED:
            return

        # noinspection PyBroadException
        try:
            self._cur_file = self.getPlayingFile()
            self._playtime = self.getTime()
            self._status = PlayState.PLAYING
            self.post_event('started')
        except Exception as err:
            xbmc.log("[iPlayer WWW.FileProgress] Unexpected error in onAvStarted() while monitoring {}: {!r}".format(
                self._episode_id, err))
            self._playtime = 0
            self._status = PlayState.STOPPED
            return

    def onAVChange(self) -> None:
        if self._cur_file and self._cur_file != self.getPlayingFile():
            self.onPlayBackStopped()

    def onPlayBackStopped(self) -> None:
        cur_state = self._status
        if cur_state is PlayState.STOPPED:
            return
        self._status = PlayState.STOPPED
        if cur_state is PlayState.PLAYING:
            # iplayer doesn't have an event type like 'stopped'
            self.post_event('paused')

    def onPlayBackEnded(self) -> None:
        self.onPlayBackStopped()

    def onPlayBackError(self) -> None:
        self.onPlayBackStopped()

    def wait_until_playing(self, timeout) -> bool:
        """Wait and return `True` when the player has started playing.
        Return `False` when `timeout` expires, or when play has been aborted before
        the actual playing started.

        """
        end_t = time.monotonic() + timeout
        while self._status is PlayState.UNDEFINED:
            if time.monotonic() >= end_t:
                return False
            if self.sys_monitor.waitForAbort(0.2):
                return False
        return not self._status is PlayState.STOPPED

    def monitor_progress(self) -> None:
        """Post heartbeat events at regular intervals while the file is playing.

        """
        if self._status is PlayState.UNDEFINED:
            return
        report_period = 30
        report_t = time.monotonic() + report_period
        while not (self.sys_monitor.waitForAbort(self.POLL_PERIOD) or self._status is PlayState.STOPPED):
            try:
                self._playtime = self.getTime()
            except RuntimeError:  # Player just stopped playing
                self.onPlayBackStopped()
                break
            if time.monotonic() > report_t and self._status is PlayState.PLAYING:
                report_t += report_period
                self.post_event('heartbeat')

    def post_event(self, action):
        data = {
            "action": action,
            "id": self._episode_id,
            "offset": int(self._playtime),
            "version_id": self._stream_id
        }
        try:
            resp = requests.post(self.EVT_URL, json=data,
                                 headers=ipwww_common.headers,
                                 cookies=ipwww_common.cookie_jar)
            resp.raise_for_status()
            self._event_errors = 0
        except requests.exceptions.HTTPError as err:
            self._handle_http_error(err, action)
        except requests.exceptions.RequestException as err:
            self._handle_event_error(err)

    def _handle_event_error(self, error):
        self._event_errors += 1
        if self._event_errors > 3:
            # No point in going on if events continue to have errors.
            self._status = PlayState.STOPPED
            xbmc.log(f"[iPlayer WWW.FileProgress] Multiple consecutive event errors - monitoring aborted. Last error: {repr(error)}.")
            return True

    def _handle_http_error(self, http_error, action):
        if http_error.response.status_code == 401:
            self._event_errors += 1
            # Only try to refresh tokens once and only if the user has already signed in.
            if self._event_errors > 1:
                self._status = PlayState.STOPPED
                xbmc.log("[iPlayer WWW.FileProgress] Second consecutive authentication error - monitoring aborted.")
                return
            # Try to refresh tokens
            if ipwww_common.StatusBBCiD():
                self.post_event(action)
            else:
                xbmc.log("[iPlayer WWW.FileProgress] Not signed in with BBCiD, monitoring aborted.")
                self._status = PlayState.STOPPED
        else:
            self._handle_event_error(http_error)


def monitor_progress(episode_id, stream_id):
    try:
        if episode_id and stream_id:
            play_monitor = FileProgress(episode_id, stream_id)

            if play_monitor.wait_until_playing(15) is False:
                return
            play_monitor.monitor_progress()
    except Exception as e:
        xbmc.log(f"[iPlayer WWW.monitor_progress] Play progress monitoring aborted due to unhandled exception: {repr(e)}")
