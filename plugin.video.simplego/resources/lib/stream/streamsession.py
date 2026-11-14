"""Starting a stream and keeping its session with the provider: used by the service and by the plugin."""

import contextlib
import functools
import threading
import time

import xbmc
import xbmcgui

from resources.lib import kodiutil
from resources.lib import parental
from resources.lib import provider
from resources.lib.data import guidedata
from resources.lib.data import infopages
from resources.lib.data import onair
from resources.lib.net import transport
from resources.lib.stream import keyfollower
from resources.lib.stream import licproxy
from resources.lib.util import isotime

# Seconds between position saves while watching back (the web player saves every 2 s).
BOOKMARK_EVERY = 30
# How long closing waits for the last round's beacon (see Session._send).
CLOSE_WAIT = 5
# How near the start or end (seconds) a saved position counts as none.
BOOKMARK_MARGIN = 60

# Home window property: a 3099 refusal seen in this Kodi run (see licence_refused).
LICENCE_REFUSED = "%s.licence_refused" % kodiutil.ADDON_ID

# (channel, start) -> key change segment indexes found by the proxy, reused when the next part starts.
_key_changes = {}


def start_stream(client, channel, programme=None, laps=None):
    """Open a stream session and the local proxy ISA talks to (see licproxy).

    :param programme: see provider.playback.Playback.play_live
    :param laps: laps(step) after each step (see resources.lib.util.laps), for the log
    :return: (stream, proxy): the session's details and its licproxy.LicenceProxy
    """
    laps = laps or (lambda step: None)
    refused = "3099" if kodiutil.untrusted_widevine() else kodiutil.home().getProperty(LICENCE_REFUSED)
    if refused:
        raise provider.LicenceRefusedError(refused)
    unlocked = parental.gate(client, channel, programme)
    laps("parental")
    ahead = _positions_ahead(client, programme)
    stream = client.play_live(channel, programme, laps)
    stream["channel"], stream["programme"] = channel, programme
    stream["logo"] = (client.channel_of(channel["id"]) or {}).get("logo")
    stream["details"] = programme_details(client, channel, programme)
    stream["bookmark"] = bookmark_info(client, channel, programme)
    if stream["bookmark"] and stream["details"]:
        # For the "Continue watching" list, which has no plots of its own.
        infopages.keep_plot(stream["bookmark"]["program_id"], stream["details"]["plot"], kodiutil.PROFILE)
    laps("guide")
    if programme:
        kept = (stream["bookmark"] or {}).get("id") or "nothing (live, or on air still)"
        kodiutil.log("position kept as: %s" % kept, xbmc.LOGDEBUG)
    resume = (programme or {}).get("resume")
    if ahead:
        ahead.join()
    try:
        if (programme or {}).get("continue"):  # picked to play on: there, without asking
            stream["start_offset"] = saved_position(client, stream["bookmark"])
        else:
            stream["start_offset"] = resume_offset(client, stream["bookmark"], resume)
    except provider.CancelledError:
        # Nothing plays: the stream session just opened must not count against the stream limit.
        with contextlib.suppress(provider.ApiError):
            client.beacon(stream["session"], complete=True)
        raise
    # Where it starts: there, or where Kodi resumes it (it seeks itself, see resume_offset).
    start_at = stream["start_offset"] or (saved_position(client, stream["bookmark"]) if resume else 0)
    laps("position")
    proxy = make_proxy(client, stream, start_at=start_at, unlocked=unlocked)
    laps("proxy")
    return stream, proxy


def _positions_ahead(client, programme):
    """Fetch the saved positions in parallel with opening the stream session (they took 0.6 s on a TV stick).

    :return: the thread to join before saved_position; None for live, a restart, or "from the start"
    """
    if not programme or programme["end"] > time.time() or programme.get("resume") is False or not client.authed:
        return None

    def fetch():
        with contextlib.suppress(provider.ApiError):  # saved_position asks again, and says so
            client.bookmarks()

    thread = threading.Thread(target=fetch, daemon=True)
    thread.start()
    return thread


def programme_details(client, channel, programme):
    """Return the guide's details of a programme watched back or restarted; None for live or no guide."""
    if programme is None:
        return None
    found = onair.on_air(client, client.station_of(channel["id"]), programme["start"])[0]
    return guidedata.details(found) if found else None


def make_proxy(client, stream, start_at=None, part=None, unlocked=None):
    """Make the local proxy ISA talks to for a stream's manifest and licence.

    :param part: which key's part of a programme watched back it declares
        (see manifest.ManifestRewriter._key_changes); else the one it starts in
    """
    channel, programme = stream["channel"], stream["programme"]
    station = client.station_of(channel["id"])
    http = transport.Session()
    http.verify = client.ca_bundle
    http.headers["User-Agent"] = provider.USER_AGENT

    def locked(p):
        return parental.locked_now(client, channel, p, unlocked)

    proxy = licproxy.LicenceProxy(
        http,
        stream["license_url"],
        # Asked again for each licence: the access token in them expires after about an hour.
        lambda: client.licence_headers(channel["id"]),
        kodiutil.log,
        debug=lambda msg: kodiutil.log(msg, xbmc.LOGDEBUG),
        on_refused=licence_refused,
        manifest_url=stream["manifest"],
        audio_langs=audio_languages(),
        from_start=bool(stream.get("from_start")),
        no_timeshift=onair.on_air_check(client, station, lambda p: "ts" in (p.get("content_flags") or [])),
        # A live channel only: a programme from its beginning is the one the lock was checked for.
        stop_when=None if programme else onair.on_air_check(client, station, locked),
        key_changes=_key_changes.get((channel["id"], (programme or {}).get("start"))),
        part=part,
        start_at=start_at,
        label=channel.get("name"),
    )
    return proxy.start()


def bookmark_info(client, channel, programme):
    """Return what the provider keeps a position of watching back under (as the web player sends it).

    :return: None for live TV and a restarted programme
    """
    if not programme or programme["end"] > time.time() or not client.authed:
        return None
    station = client.station_of(channel["id"])
    if not station:
        return None
    found = onair.on_air(client, station, programme["start"])[0] or {}
    end = isotime.iso(programme["end"])
    return {
        "id": guidedata.bookmark_id(station, programme["start"], end),
        "program_id": found.get("program_id", ""),
        "media_id": channel["media_id"],
        "start_time": programme["start"],
        "end_time": end,
        "station_id": station,
    }


def resume_offset(client, info, resume=None):
    """Return the seconds to start at: where it was left off, if the user picks it; else 0.

    :param resume: Kodi has already asked (True: continue, False: from the start); on
        "continue" Kodi seeks to its resume point itself, so no seek here either way
    """
    if resume is not None or not info:
        return 0
    seconds = saved_position(client, info)
    if not seconds:
        return 0
    choice = xbmcgui.Dialog().contextmenu([kodiutil.string(30186) % kodiutil.clock(seconds), kodiutil.string(30187)])
    if choice < 0:  # cancelled ("Back"): neither, so nothing plays
        raise provider.CancelledError("where to resume: cancelled")
    return seconds if choice == 0 else 0


def saved_position(client, info):
    """Return the seconds where watching back was left off (here or in the provider's apps).

    :return: 0 if none (or too near its start or end to count)
    """
    if not info:
        return 0
    try:
        saved = next((b for b in client.bookmarks() if b.get("id") == info["id"]), None)
    except provider.ApiError as e:
        kodiutil.log("bookmarks unavailable: %s" % e, xbmc.LOGWARNING)
        return 0
    seconds = float((saved or {}).get("time_seconds") or 0)
    runtime = float((saved or {}).get("runtime_seconds") or 0)
    if seconds < BOOKMARK_MARGIN or (runtime and seconds > runtime - BOOKMARK_MARGIN):
        return 0
    return seconds


def save_bookmark(client, info, seconds, runtime):
    """Save the position of a programme watched back to the account (best effort).

    Not within its first minute: a look from the start keeps where it was left off.
    """
    if not info or not runtime or seconds < BOOKMARK_MARGIN:
        return
    try:
        answer = client.set_bookmark(info, seconds, runtime)
    except provider.ApiError as e:
        kodiutil.log("saving the position failed: %s" % e, xbmc.LOGWARNING)
        return
    kodiutil.log("position saved: %s at %d of %d s, answer %s" % (info["id"], seconds, runtime, str(answer)[:200]), xbmc.LOGDEBUG)


class Session:
    """Keep a stream's session with the provider alive (beacons), save positions, close it at the end.

    Closing matters: the account's stream limit (2413) is small. Proxies and key parts are `keys`' job.
    """

    def __init__(self, client, stream, proxy):
        self.client = client
        self.stream = stream
        self.session = stream["session"]
        self.bookmark = stream.get("bookmark")
        self.start_offset = stream.get("start_offset") or 0
        self.created = time.time()
        self.started = False
        self.last_beacon = self.saved = self.created
        self.position = self.runtime = 0
        self._sending = None  # the thread sending the last round's beacon and position
        programme = stream.get("programme")
        self.keys = keyfollower.KeyFollower(
            proxy,
            lambda part: make_proxy(client, stream, part=part),
            known=_key_changes,
            key=(stream["channel"]["id"], programme["start"]) if programme else None,
        )

    @property
    def id(self):
        """Return the provider's ID of the session."""
        return self.session["session_id"]

    @property
    def proxy(self):
        """Return the proxy the stream plays through now (see KeyFollower)."""
        return self.keys.proxy

    def start(self):
        """Note that playback started: beacons and key changes are timed from now."""
        self.started = True
        self.last_beacon = time.time()
        self.keys.started()
        kodiutil.log("session %s started" % self.id)

    def tick(self, player, now=None, own=True):
        """Note the position while it plays, save it now and then, and send the beacon when due.

        :param own: whether the player's position is this stream's; False during a channel
            switch, whose position would read as a jump or be saved as this one's
        """
        now = now or time.time()
        due = []
        if own:
            self._follow(player, now)
            if self.bookmark and now - self.saved >= BOOKMARK_EVERY:
                self.saved = now
                due.append(functools.partial(save_bookmark, self.client, self.bookmark, self.position, self.runtime))
        if now - self.last_beacon >= self.session["interval"]:
            self.last_beacon = now
            due.append(self._beacon)
        if due:
            self._send(due)

    def _send(self, due):
        """Send what is due on a thread: the service's loop must not wait for the provider.

        While the last round's sending still runs (a slow provider, a token renewal), this
        round's is left out: the position comes again in BOOKMARK_EVERY, the beacon in its interval.
        """
        if self._sending and self._sending.is_alive():
            kodiutil.log("session %s: the last beacon is still being sent, this one is left out" % self.id, xbmc.LOGDEBUG)
            return

        def send():
            for work in due:
                work()

        self._sending = threading.Thread(target=send, daemon=True)
        self._sending.start()

    def _beacon(self):
        try:
            self.client.beacon(self.session)
        except provider.ApiError as e:
            kodiutil.log("beacon failed: %s" % e, xbmc.LOGWARNING)

    def _follow(self, player, now):
        if self.bookmark or self.proxy.change_times:
            try:
                if player.isPlaying():
                    self.position, self.runtime = player.getTime(), player.getTotalTime()
            except RuntimeError:
                pass
        self.keys.follow(self.position, player, now)

    def seek_to_start(self, player):
        """Seek to where playback should start (where it was left off); its part's keys are already declared."""
        if self.start_offset:
            player.seekTime(self.start_offset)

    def close(self, keep_proxy=False):
        """Stop the proxies, save the last position, release the session (best effort).

        :param keep_proxy: the proxy it plays through stays (see licproxy.LicenceProxy.sleep)
        """
        self.keys.close(keep=self.proxy if keep_proxy else None)
        if self._sending:
            # A beacon still on its way must not arrive after the closing one.
            self._sending.join(CLOSE_WAIT)
        if self.bookmark and self.position:
            save_bookmark(self.client, self.bookmark, self.position, self.runtime)
        try:
            self.client.beacon(self.session, complete=True)
        except provider.ApiError as e:
            kodiutil.log("closing session failed: %s" % e, xbmc.LOGWARNING)
        kodiutil.log("session %s closed" % self.id)


def licence_refused(code):
    """Tell the user the licence server refused the stream, and remember a 3099 until Kodi restarts."""
    # 3099 "browser framework is not trusted": Verified Media Path required, which Kodi's
    # desktop CDM cannot provide, so later channels fail fast without opening a session.
    if code == "3099":
        kodiutil.home().setProperty(LICENCE_REFUSED, code)
    xbmcgui.Dialog().ok(kodiutil.name(), licence_message(code))


def licence_message(code):
    """Return the message for a licence refused with this code."""
    return kodiutil.string(30012) if code == "3099" else kodiutil.string(30013) % code


def audio_languages():
    """Return the ISO 639-2 codes for Kodi's "Preferred audio language" setting, best first.

    One audio key pair per stream (see licproxy), so the choice is made before
    playback. The original soundtrack is labelled "mul"; an unlisted foreign
    language falls back to it. [] keeps the default, Hungarian.
    """
    value = kodiutil.kodi_setting("locale.audiolanguage")
    if not value or value == "mediadefault":
        return []
    if value == "original":
        return ["mul"]
    lang = xbmc.getLanguage(xbmc.ISO_639_2) if value == "default" else xbmc.convertLanguage(value, xbmc.ISO_639_2)
    return [] if lang in ("", "hun") else [lang, "mul"]
