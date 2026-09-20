# -*- coding: utf-8 -*-
"""Background service that refreshes linear-stream Now Playing metadata."""
from __future__ import annotations

import xbmc
import xbmcgui

from resources.lib.client import AudioAddictClient, AudioAddictError
from resources.lib.helpers import image_url
from resources.lib.state import load_state, update_state_if_current

def update_linear_metadata(client, player, state):
    channel = state.get("channel_key")
    if not channel or state.get("mode") != "linear":
        return

    current = client.current_track(
        channel, known_track_id=state.get("track_id")
    )

    latest_state = load_state()

    if (
        latest_state.get("mode") != "linear"
        or latest_state.get("channel_key") != channel
        or latest_state.get("stream_url") != state.get("stream_url")
    ):
        return

    try:
        if player.getPlayingFile() != state.get("stream_url"):
            return
    except Exception:
        return

    state = latest_state

    if not isinstance(current, dict) or not current.get("id"):
        return

    if current.get("id") == state.get("track_id"):
        return

    title = (
        current.get("display_title")
        or current.get("title")
        or channel
    )
    artist = current.get("display_artist") or "RadioTunes"
    album = f"RadioTunes — {state.get('channel_name') or channel}"

    # Work on Kodi's actual current ListItem. This gives artwork updates
    # the best chance of propagating not only to Estuary but also to
    # JSON-RPC clients such as the web interface and Kore.
    try:
        item = player.getPlayingItem()
    except Exception as exc:
        xbmc.log(
            f"[plugin.audio.radiotunes] unable to get playing item: {exc!r}",
            xbmc.LOGDEBUG,
        )
        item = xbmcgui.ListItem()
        try:
            item.setPath(player.getPlayingFile())
        except Exception as path_exc:
            xbmc.log(
                f"[plugin.audio.radiotunes] unable to set playing path: {path_exc!r}",
                xbmc.LOGDEBUG,
            )

    tag = item.getMusicInfoTag()
    tag.setTitle(str(title))
    tag.setArtist(str(artist))
    tag.setAlbum(str(album))

    thumb = image_url(
        current.get("asset_url")
        or (
            (current.get("images") or {}).get("default")
            if isinstance(current.get("images"), dict)
            else ""
        )
    )

    art = {}
    if thumb or state.get("channel_art"):
        art["thumb"] = thumb or state.get("channel_art")
        art["icon"] = thumb or state.get("channel_art")
    if state.get("channel_fanart") or state.get("channel_art"):
        art["fanart"] = (
            state.get("channel_fanart")
            or state.get("channel_art")
        )

    if art:
        item.setArt(art)

    try:
        if player.getPlayingFile() != state.get("stream_url"):
            return
    except Exception:
        return

    # updateInfoTag pushes the modified playing item back to Kodi's
    # Now Playing state after mutating title/artist/artwork above.
    player.updateInfoTag(item)

    updated = update_state_if_current(
        state.get("stream_url"),
        channel,
        {
            "track_id": current.get("id"),
            "title": title,
            "artist": artist,
            "track_art": thumb or "",
        },
    )

    if not updated:
        return

    xbmc.log(
        "[plugin.audio.radiotunes] Now Playing updated: "
        f"track_id={current.get('id')}, art={'yes' if thumb else 'no'}",
        xbmc.LOGDEBUG,
    )


def main():
    monitor = xbmc.Monitor()
    player = xbmc.Player()
    client = None

    while not monitor.abortRequested():
        if monitor.waitForAbort(10):
            break

        try:
            state = load_state()

            if state.get("mode") != "linear":
                continue
            if not player.isPlayingAudio():
                continue
            expected_stream = state.get("stream_url")

            if not expected_stream:
                continue

            try:
                playing_file = player.getPlayingFile()
            except Exception as exc:
                xbmc.log(
                    f"[plugin.audio.radiotunes] unable to read playing file: {exc!r}",
                    xbmc.LOGDEBUG,
                )
                continue

            if playing_file != expected_stream:
                continue

            if client is None:
                client = AudioAddictClient()

            update_linear_metadata(client, player, state)

        except AudioAddictError as exc:
            xbmc.log(
                f"[plugin.audio.radiotunes] metadata service API error: {exc}",
                xbmc.LOGDEBUG,
            )
        except Exception as exc:
            xbmc.log(
                f"[plugin.audio.radiotunes] metadata service error: {exc!r}",
                xbmc.LOGDEBUG,
            )


if __name__ == "__main__":
    main()
