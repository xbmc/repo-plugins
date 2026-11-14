"""Playing in the plugin itself: the way when the background service cannot (see quickplay)."""

import time
from urllib.parse import urlencode

import xbmc
import xbmcplugin

from resources.lib import kodiutil
from resources.lib import provider
from resources.lib.data import guidedata
from resources.lib.login import loginstate
from resources.lib.login import phonelogin

_log = kodiutil.log


def resolve(call, params):
    """Hand Kodi the stream these play parameters name: its own "Play" (context menu, info page) waits for one.

    As any play address: through the service, else here; the call becomes the play's (see Call.redirect).
    """
    from resources.lib.service import quickplay

    if not quickplay.run([call.base, str(call.handle), "?" + urlencode(params)], call.started):
        call.redirect(params)
        PlayViews(call).do_play()


class PlayViews:
    """The plugin's own playback (see views.routes).

    :param call: the plugin call (see views.call.Call)
    """

    def __init__(self, call):
        self._call = call

    def do_play(self):
        """Play a channel (live, from a programme's beginning, or back) when the service cannot (see quickplay)."""
        from resources.lib import resolveditem
        from resources.lib.stream import playitem
        from resources.lib.stream import streamsession

        call, client, params = self._call, self._call.client, self._call.params
        started = time.time()
        # Before the login too: off Android the licence would be refused anyway.
        if kodiutil.untrusted_widevine():
            raise provider.LicenceRefusedError()
        # InputStream Adaptive ready before the stream session opens: a session waiting on InputStream
        # Helper's questions is closed before the player asks for it. Skipping it where it has nothing
        # to check saves its import on every switch.
        if not kodiutil.isa_ready():
            import inputstreamhelper

            # The provider's streams are DASH (see playback.play_live).
            if not inputstreamhelper.Helper("mpd", drm="com.widevine.alpha").check_inputstream():
                return call.end(False)
        # Not logged in: the phone login first, then the channel starts.
        if not client.is_logged_in():
            token = phonelogin.wait_for_token(client)
            if not token:
                return call.end(False)
            client.login_with_refresh_token(token)
            loginstate.login_changed(client)
        try:
            stream, proxy = streamsession.start_stream(client, self._channel(), guidedata.from_param(params.get("programme")))
        except provider.errors.CatchupExpiredError as e:
            from resources.lib.data import watchoffer

            e.offer = watchoffer.offer_for_play(client, params["id"], params.get("programme"))  # see plugin.tell
            raise
        session = streamsession.Session(client, stream, proxy)
        rolled = time.time()
        li = resolveditem.list_item(playitem.spec(stream, proxy.manifest, proxy.url, kodiutil.kodi_major()))
        xbmcplugin.setResolvedUrl(call.handle, True, li)
        from resources.lib.service import quickplay

        kodiutil.home().setProperty(quickplay.PLAYING, quickplay.playing_mark(params))
        _log(
            "play: start-up %.2fs, stream session %.2fs, resolved after %.2fs in total"
            % (started - call.started, rolled - started, time.time() - call.started),
            xbmc.LOGDEBUG,
        )
        # Sessions left open by earlier playbacks (a channel switch, a crash)
        # are closed now, off the start's critical path.
        try:
            client.close_stale_sessions(keep=session.id)
        except provider.ApiError as e:
            _log("closing stale sessions failed: %s" % e, xbmc.LOGWARNING)
        _keep_alive(session)
        return None

    def _channel(self):
        """Return the channel the call plays: from its address, else from the channel list."""
        params = self._call.params
        # "stream" in IPTV Simple's catch-up URL (see iptvfiles._catchup).
        media = params.get("media") or params.get("stream")
        if media:
            # Listing and playlist URLs carry all client.play_live needs: no channel list fetch.
            return {"id": params["id"], "media_id": media}
        channel = next((c for c in self._call.client.channel_list() if c["id"] == params["id"]), None)
        if not channel:
            raise provider.ApiError("Unknown channel %s" % params["id"])
        return channel


def _keep_alive(session):
    """Keep the session while our stream plays (this process outlives setResolvedUrl); close it when it stops.

    A channel switch is a new invocation, so this exits once something else plays.
    """
    monitor = xbmc.Monitor()
    player = xbmc.Player()
    playing_file = None
    try:
        # Within the try: the player may stop between asking and reading what it plays.
        for _ in range(60):
            if monitor.waitForAbort(0.5):
                break
            if player.isPlaying():  # radio too
                playing_file = player.getPlayingFile()
                break
        if playing_file:
            session.start()
            session.seek_to_start(player)  # where it was left off (see playservice.PlayService.on_started)
            while not monitor.waitForAbort(1):
                try:
                    if not player.isPlaying() or player.getPlayingFile() != playing_file:
                        break
                except RuntimeError:
                    break
                session.tick(player)
    finally:
        session.close()
