"""Playback starts inside the background service, for fast channel switches.

A plugin call is a fresh interpreter, and loading the add-on and opening a session
takes seconds on a TV stick (about half of a switch). The already-loaded service opens
the session and proxy; the plugin (quickplay, standard library only) asks it over
localhost. The service then keeps the sessions alive and closes them when playback moves on.
"""

import json
import secrets
import threading
import time

import xbmc

from resources.lib import clientfactory
from resources.lib import kodiutil
from resources.lib import resolveditem
from resources.lib.data import channellist
from resources.lib.data import guidedata
from resources.lib.data import menucounts
from resources.lib.net import localserver
from resources.lib.service import quickplay
from resources.lib.stream import playitem
from resources.lib.stream import streamsession
from resources.lib.util import laps

# Home window property with "port token"; only Kodi's own processes can read it.
PROPERTY = quickplay.PROPERTY
# The live channel list (see views.channels), redrawn when the channel it marks stops playing.
CHANNEL_LIST = "plugin://%s/?action=channels" % kodiutil.ADDON_ID
LIST_ON_SCREEN = "Window.IsVisible(videos) + String.StartsWith(Container.FolderPath,%s)" % CHANNEL_LIST
# A started session that never reaches playback (an error in Kodi) is closed after this.
START_TIMEOUT = 90
# The least time between two restarts at key changes (see _restart).
RESTART_GAP = 15
# Going to sleep, Kodi stops playing a moment before or after it says so: a live channel
# stopped this recently counts as playing. On waking, it plays again after Kodi's own resume jobs.
SLEEP_STOP = 30
WAKE_DELAY = 5


class _Player(xbmc.Player):
    def __init__(self, service):
        super().__init__()
        self._service = service

    def onAVStarted(self):
        self._service.on_started()

    def onPlayBackStopped(self):
        self._service.on_stopped()

    def onPlayBackEnded(self):
        self._service.on_stopped()

    def onPlayBackError(self):
        self._service.on_stopped()


class PlayService:
    """Open streams for the plugin over localhost, and keep their sessions until playback moves on.

    :param shared_client: shared_client() returns the client the service's streams and lists share
        (see clientfactory.shared_client)
    """

    def __init__(self, shared_client=clientfactory.shared_client):
        self._shared_client = shared_client
        self._lock = threading.Lock()
        # One stream opens at a time: zapping fast must not renew the login twice at once.
        self._play_lock = threading.Lock()
        self._sessions = []  # streamsession.Session, newest last
        self._sleeping = None  # the last stopped stream's proxy (see _sleep)
        self._stopping = False
        self._live = None  # (channel, when it stopped or None while it plays): the last live channel
        self._resume_live = None  # the live channel to play again on waking up
        self._restarted = 0
        self._token = secrets.token_hex(16)
        self._server = self._player = None  # see start
        # Whether the video was on the full screen, as last seen while it played (see tick, _unmark_playing).
        self._full_screen = True

    def start(self):
        """Serve the plugin and follow Kodi's player; tell the plugin where (a Home window property); return the service."""
        self._server = localserver.start(self.respond)
        self._player = _Player(self)
        kodiutil.home().setProperty(PROPERTY, "%d %s" % (localserver.port(self._server), self._token))
        return self

    def respond(self, request):
        """Answer the plugin's request (see quickplay.ask): /play, /list or /menu, with the token; JSON."""
        q = request.query
        if request.method != "GET" or request.path not in ("/play", "/list", "/menu") or q.get("token") != self._token:
            status, answer = 403, {"error": "forbidden"}
        elif request.path == "/list":
            status, answer = 200, self.list_view(q.get("scope") or None)
        elif request.path == "/menu":
            status, answer = 200, self.menu_counts()
        else:
            status, answer = 200, self.play(q.get("id", ""), q.get("media", ""), q.get("programme"))
        return localserver.Response(status, json.dumps(answer).encode(), "application/json")

    def play(self, channel_id, media_id, programme=None):
        """Open a stream and return its ListItem spec.

        :param programme: a programme from its beginning (the plugin URL's, see guidedata.from_param)
        :return: the ListItem spec (see playitem.spec), or {"error": kind, "message": ...}
        """
        started = time.time()
        steps = laps.Laps()
        try:
            with self._play_lock:
                steps("waiting")  # for a channel switch still opening
                client = self._shared_client()
                channel = {"id": channel_id, "media_id": media_id}
                stream, proxy = streamsession.start_stream(client, channel, guidedata.from_param(programme), steps)
            # Read the stream's keys while Kodi is still setting up the player.
            proxy.prefetch()
        except Exception as e:  # noqa: BLE001 - the HTTP answer says what failed, whatever it was
            if getattr(e, "kind", None) is None:  # not the provider's: unexpected
                kodiutil.log("play failed: %s" % e, xbmc.LOGERROR)
            answer = _error(e)
            if answer["error"] == "expired":  # what is left: onto the favourites, or off Continue watching
                from resources.lib.data import watchoffer

                answer["offer"] = watchoffer.offer_for_play(self._shared_client(), channel_id, programme)
            return answer
        session = streamsession.Session(client, stream, proxy)
        session.keys.restart = lambda part, seconds: self._restart(session, part, seconds)
        session.reopen = lambda: self._reopen(channel_id, media_id, programme)
        with self._lock:
            for playing in self._sessions:
                playing.keys.hold()
            self._sessions.append(session)
        steps("session")
        kodiutil.log("play (service): stream session ready in %.2fs (%s)" % (time.time() - started, steps), xbmc.LOGDEBUG)
        return playitem.spec(stream, proxy.manifest, proxy.url, kodiutil.kodi_major())

    def list_view(self, scope):
        """Return what a channel list shows (see channellist.view), or {"error": kind, "message"}.

        Served from here so the plugin loads neither the client nor the guide (most of a list's time on a TV stick).
        """
        try:
            return channellist.view(self._current_client(), scope)
        except Exception as e:  # noqa: BLE001 - the plugin makes the list itself then, and says what failed
            return _error(e)

    def menu_counts(self):
        """Return what the main menu says beside its rows (see menucounts.counts), or {"error": kind, "message"}."""
        try:
            return menucounts.counts(self._current_client())
        except Exception as e:  # noqa: BLE001 - the plugin makes them itself then
            return _error(e)

    def _current_client(self):
        """Return the shared client with what the plugin changed taken up (a favourite, the order)."""
        client = self._shared_client()
        client.reload()
        return client

    # ------------------------------------------------------------ lifecycle

    def _restart(self, session, part, seconds):
        """Play a programme watched back on through another key's part's proxy, from `seconds`.

        A live channel (seconds None) plays again from its edge, through a proxy declaring its new key.

        Hands Kodi the ready item: a plugin URL would show a busy dialog while the stopping
        player may still show one, and two at once make Kodi exit ("two concurrent busydialogs").
        """
        if time.time() - self._restarted < RESTART_GAP:
            return
        self._restarted = time.time()

        def play():
            proxy = session.keys.part_proxy(part)
            session.keys.switch(proxy)
            item = playitem.spec(session.stream, proxy.manifest, proxy.url, kodiutil.kodi_major())
            li = resolveditem.list_item(item)
            if seconds is not None:  # None: live, from its edge
                li.setProperty("StartOffset", "%.1f" % seconds)
            self._player.play(item["path"], li)

        threading.Thread(target=play, daemon=True).start()

    def on_started(self):
        """Handle a playback start: it is our newest stream if that one has not started yet."""
        playing = self._playing_file()
        unmark = False
        with self._lock:
            switching = next((s for s in self._sessions if s.keys.switching), None)
            if switching:
                # Our own restart at a key change: the same session plays on.
                switching.keys.switched()
                return
            # Played through the sleeping proxy (reopened, see _sleep): it stays, others go.
            if self._sleeping is not None and not playing.startswith(self._sleeping.manifest):
                self._sleeping.stop()
                self._sleeping = None
            newest = self._sessions[-1] if self._sessions else None
            if newest and not newest.started:
                newest.start()
                old, self._sessions = self._sessions[:-1], [newest]
                live = newest.stream["programme"] is None
                self._live = (newest.stream["channel"], None) if live else None
            else:
                # Something else is playing now (another add-on, a file).
                old, self._sessions, newest = self._sessions, [], None
                self._live = None
                unmark = True
        if unmark:
            _unmark_playing(self._full_screen)
        self._close(old)
        if newest:
            # Kodi takes no start offset from an IPTV Simple or resolved plugin item, so seek instead.
            newest.seek_to_start(self._player)

    def on_stopped(self):
        """Handle a playback stop: close the sessions that were playing; the last one's proxy sleeps."""
        # Streams not started yet belong to a playback on its way (a switch stops the old one first);
        # a session switching to another key's part plays on.
        unmark = False
        with self._lock:
            if self._stopping:
                return  # stop() closes them all
            old = [s for s in self._sessions if s.started and not s.keys.switching]
            self._sessions = [s for s in self._sessions if s not in old]
            if old and self._live and self._live[1] is None:
                self._live = (self._live[0], time.time())
            # Nothing on its way (a switch has its next stream here already): no channel plays.
            unmark = bool(old) and not self._sessions
        if unmark:
            _unmark_playing(self._full_screen)
        if old:
            # Kodi may play the same item again by its address (see _sleep).
            self._sleep(old[-1])
        self._close(old[:-1])

    def busy(self):
        """Return whether a stream of ours is open (for the service's round times, see background.RoundTimes)."""
        return bool(self._sessions)

    def tick(self):
        """Keep the playing sessions; give up on ones that never started. Called every second."""
        now = time.time()
        with self._lock:
            expired = [
                s
                for s in self._sessions
                if (not s.started and now - s.created > START_TIMEOUT)
                or (s.keys.switching and now - s.keys.switching > START_TIMEOUT)
            ]
            self._sessions = [s for s in self._sessions if s not in expired]
            playing = [s for s in self._sessions if s.started]
            # A stream on its way (a channel switch): what the player says is not the playing ones' any more.
            incoming = any(not s.started for s in self._sessions)
        for s in playing:
            s.tick(self._player, now, own=not incoming)
        if playing:
            # Looked at while it plays: at the stop Kodi is already leaving the full screen.
            self._full_screen = xbmc.getCondVisibility("VideoPlayer.IsFullscreen")
        self._close(expired)

    def on_power(self, method):
        """Handle System.OnSleep / System.OnWake (the TV off and on).

        On waking Kodi resumes what was watched back but never a live channel, so that is restarted here.
        """
        if method == "System.OnSleep":
            with self._lock:
                live = self._live
            recent = live and (live[1] is None or time.time() - live[1] < SLEEP_STOP)
            self._resume_live = live[0] if recent else None
        elif method == "System.OnWake" and self._resume_live:
            channel, self._resume_live = self._resume_live, None
            timer = threading.Timer(WAKE_DELAY, self._play_live_again, (channel,))
            timer.daemon = True
            timer.start()

    def _play_live_again(self, channel):
        """Play a live channel again (see on_power), unless something plays already."""
        if self._player.isPlaying():
            return
        item = self.play(channel["id"], channel["media_id"])
        if "path" not in item:
            kodiutil.log("playing the live channel again failed: %s" % item.get("message"), xbmc.LOGWARNING)
            return
        kodiutil.log("live channel %s plays again after waking up" % channel["id"])
        # The service hands Kodi the ready item, as at a key change (see _restart).
        self._player.play(item["path"], resolveditem.list_item(item))

    def _sleep(self, session):
        """Close a stream whose item Kodi may still play again: its proxy stays, to reopen it then.

        Back from the background (another HDMI input) Kodi replays the item by its old address,
        however much later; with that address closed it failed and Kodi crashed.
        """
        if self._sleeping is not None:
            self._sleeping.stop()
        self._sleeping = session.proxy

        def close():
            session.close(keep_proxy=True)
            session.proxy.sleep(session.reopen)

        threading.Thread(target=close, daemon=True).start()

    def _reopen(self, channel_id, media_id, programme):
        """Open the stream again for a sleeping proxy; return its proxy's base address, or None.

        No "where to start" question: Kodi resumes at its own point, and a question held
        its request up until it gave up.
        """
        if programme:
            programme = guidedata.resumed(programme)
        spec = self.play(channel_id, media_id, programme)
        return spec["path"].rsplit("/", 1)[0] if "path" in spec else None

    def _playing_file(self):
        """Return what Kodi plays (a resolved item's own URL); "" if nothing."""
        try:
            return self._player.getPlayingFile() if self._player.isPlaying() else ""
        except RuntimeError:
            return ""

    def _close(self, sessions):
        if sessions:
            # Off the caller's thread: the player callbacks must return quickly.
            threading.Thread(target=_close_all, args=(sessions,), daemon=True).start()

    def stop(self):
        """Close what is left at Kodi's exit or the add-on's update, waiting a little for it.

        A stream still playing is stopped too, or Kodi keeps asking its closed proxy, the picture frozen.
        """
        kodiutil.home().clearProperty(PROPERTY)
        localserver.stop(self._server)
        with self._lock:
            self._stopping = True
            proxies = [s.proxy for s in self._sessions] + [p for p in (self._sleeping,) if p is not None]
        playing = self._playing_file()
        if any(playing.startswith(p.manifest.rsplit("/", 1)[0] + "/") for p in proxies):
            # Posted, not Player().stop(): on an update Kodi stops this service from its main
            # thread and waits, and Player().stop() waits for the main thread: a deadlock.
            xbmc.executebuiltin("PlayerControl(Stop)")
        with self._lock:
            old, self._sessions = self._sessions, []
            if self._sleeping is not None:
                self._sleeping.stop()
                self._sleeping = None
        closing = threading.Thread(target=_close_all, args=(old,), daemon=True)
        closing.start()
        closing.join(3)


def _unmark_playing(full_screen):
    """Drop the mark when no channel of ours plays now, and redraw a channel list on screen that shows it.

    :param full_screen: whether the video was on the full screen: back from it, Kodi loads the list again
        itself, and a refresh then ran a second listing alongside its own (seen 2026-11-02: each channel
        twice, then the subscribed ones missing). Only a list shown beside a playing video is redrawn here.
    """
    home = kodiutil.home()
    if not home.getProperty(quickplay.PLAYING):
        return
    home.clearProperty(quickplay.PLAYING)
    # The list draws the mark when it is made: one left open shows it until made again.
    if not full_screen and xbmc.getCondVisibility(LIST_ON_SCREEN):
        xbmc.executebuiltin("Container.Refresh")


def _close_all(sessions):
    for s in sessions:
        s.close()


def _error(e):
    """Return a failure as the plugin's answer: its kind, for quickplay's message (see provider.ApiError), and text."""
    return {"error": getattr(e, "kind", None) or "api", "message": str(e)}
