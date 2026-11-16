"""Remote control: Play / Playstate / GeneralCommand from the websocket,
plus the SyncPlay message routing.

Runs on the websocket thread; every handler is a quick JSON-RPC call or
builtin — the SyncPlay messages only enqueue onto the manager's dispatcher
thread, so ordering is preserved and this thread never blocks. Unknown
commands log and return — never raise.
"""

from __future__ import annotations

import threading
from typing import TYPE_CHECKING, Any

import xbmc

from kofin.core import kodirpc, toast
from kofin.core.log import Logger
from kofin.core.urls import PARAM_UNATTENDED, plugin_url

if TYPE_CHECKING:
    from kofin.syncplay.manager import SyncPlayManager

LOG = Logger(__name__)

JsonDict = dict[str, Any]

# GeneralCommand names that map straight to a Kodi input action.
INPUT_ACTIONS = {
    "MoveUp": "up",
    "MoveDown": "down",
    "MoveLeft": "left",
    "MoveRight": "right",
    "Select": "select",
    "Back": "back",
    "ToggleContextMenu": "contextmenu",
    "ToggleOsdMenu": "osd",
    "PageUp": "pageup",
    "PageDown": "pagedown",
    "NextLetter": "nextletter",
    "PreviousLetter": "prevletter",
    "TakeScreenshot": "screenshot",
    "ToggleFullscreen": "togglefullscreen",
}


def _as_int(value: Any, default: int = 0) -> int:
    """A server-supplied number, or ``default`` for anything that is not one."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _is_audio(item_id: str) -> bool:
    """Whether a Jellyfin id is a song in this Kodi library.

    Read from the catalogue rather than the server: the remote payload
    carries ids and nothing else, and this runs on the websocket thread
    where a round trip would hold the command up. An unknown or unreadable
    id answers False -- the video queue.
    """
    try:
        from kofin.sync.backends.api.identity import current_store

        entry = current_store().entry(item_id)
    except Exception:
        LOG.debug("remote: could not resolve the media type of %s", item_id)
        return False

    return entry is not None and entry.kind == "Audio"


class RemoteHandler:
    def __init__(self) -> None:
        # The SyncPlay manager (attached by the service while one is built);
        # all control-plane websocket traffic routes through this handler.
        self.syncplay: SyncPlayManager | None = None
        # The one thing a remote command may leave running: a PlayNow's
        # start-position seek waiting for the player to come up. Replaced
        # by the next PlayNow; the old one exits on its own bound.
        self._seek_thread: threading.Thread | None = None

    def handle(self, message_type: str, data: JsonDict) -> bool:
        """Dispatch a websocket message; returns True when handled."""
        if message_type == "Play":
            self._play(data)
        elif message_type == "Playstate":
            self._playstate(data)
        elif message_type == "GeneralCommand":
            self._general(data)
        elif message_type in ("SyncPlayCommand", "SyncPlayGroupUpdate"):
            manager = self.syncplay
            if manager is None:
                LOG.debug("%s with no SyncPlay manager; dropped", message_type)
            else:
                manager.on_notification(message_type, data)
        else:
            return False
        return True

    # -- Play ------------------------------------------------------------------

    def _play(self, data: JsonDict) -> None:
        item_ids = data.get("ItemIds") or []
        if isinstance(item_ids, str):
            item_ids = item_ids.split(",")
        start_index = max(_as_int(data.get("StartIndex")), 0)
        ordered: list[str] = list(item_ids[start_index:])
        if not ordered:
            return
        command = data.get("PlayCommand", "PlayNow")
        LOG.debug("remote %s of %d item(s)", command, len(ordered))

        # Remote Play carries no media kind; the catalogue picks the queue.
        playlist = xbmc.PlayList(
            xbmc.PLAYLIST_MUSIC if _is_audio(ordered[0]) else xbmc.PLAYLIST_VIDEO
        )
        urls = [
            plugin_url({"mode": "play", "id": item_id, PARAM_UNATTENDED: "1"})
            for item_id in ordered
        ]

        if command == "PlayNow":
            playlist.clear()
            for url in urls:
                playlist.add(url)
            xbmc.Player().play(playlist)
            position_ticks = _as_int(data.get("StartPositionTicks"))
            if position_ticks:
                self._start_seek(position_ticks / 10_000_000)
        elif command == "PlayNext":
            insert_at = playlist.getposition() + 1
            for offset, url in enumerate(urls):
                playlist.add(url, index=insert_at + offset)
        else:  # PlayLast
            for url in urls:
                playlist.add(url)

    def _start_seek(self, seconds: float) -> None:
        """Seek once the player is up — off this thread.

        The wait is up to 10 s of half-second polls, and this handler runs
        on the websocket thread, which must keep reading.
        """
        thread = threading.Thread(
            target=self._seek_when_playing,
            args=(seconds,),
            name="kofin-remote-seek",
            daemon=True,
        )
        self._seek_thread = thread
        thread.start()

    def _seek_when_playing(self, seconds: float) -> None:
        monitor = xbmc.Monitor()
        player = xbmc.Player()
        for _ in range(20):
            if monitor.waitForAbort(0.5):
                return
            if player.isPlaying():
                try:
                    player.seekTime(seconds)
                except RuntimeError:
                    pass
                return
        LOG.debug("remote start position dropped: nothing playing after 10 s")

    # -- Playstate ----------------------------------------------------------------

    def _playstate(self, data: JsonDict) -> None:
        command = data.get("Command", "")
        player = xbmc.Player()
        if command == "Stop":
            kodirpc.stop_player()  # not player.stop(); see kodirpc.stop_player
        elif command == "Pause":
            kodirpc.pause_player()
        elif command == "Unpause":
            kodirpc.resume_player()
        elif command == "PlayPause":
            player.pause()  # Kodi's pause() toggles
        elif command == "NextTrack":
            player.playnext()
        elif command == "PreviousTrack":
            player.playprevious()
        elif command == "Seek":
            ticks = _as_int(data.get("SeekPositionTicks"))
            try:
                player.seekTime(ticks / 10_000_000)
            except RuntimeError:
                LOG.debug("seek with nothing playing")
        else:
            LOG.debug("unhandled playstate command %s", command)

    # -- GeneralCommand -----------------------------------------------------------

    def _general(self, data: JsonDict) -> None:
        name = data.get("Name", "")
        arguments = data.get("Arguments") or {}

        if name in INPUT_ACTIONS:
            xbmc.executebuiltin("Action(%s)" % INPUT_ACTIONS[name])
        elif name == "GoHome":
            xbmc.executebuiltin("ActivateWindow(Home)")
        elif name == "GoToSettings":
            xbmc.executebuiltin("ActivateWindow(Settings)")
        elif name == "GoToSearch":
            xbmc.executebuiltin("ActivateWindow(Home)")
            xbmc.executebuiltin("SendClick(600)")
        elif name == "SetVolume":
            self._rpc(
                "Application.SetVolume",
                {"volume": _as_int(arguments.get("Volume"))},
            )
        elif name == "VolumeUp":
            self._rpc("Application.SetVolume", {"volume": "increment"})
        elif name == "VolumeDown":
            self._rpc("Application.SetVolume", {"volume": "decrement"})
        elif name in ("Mute", "Unmute", "ToggleMute"):
            mute = {"Mute": True, "Unmute": False, "ToggleMute": "toggle"}[name]
            self._rpc("Application.SetMute", {"mute": mute})
        elif name == "DisplayMessage":
            # The server's own message, relayed by kofin: its heading stands,
            # and the icon says which client put it on screen.
            toast.show(
                arguments.get("Text") or "",
                heading=arguments.get("Header") or "Jellyfin",
                time_ms=_as_int(arguments.get("TimeoutMs"), 5000),
            )
        elif name == "SendString":
            self._rpc(
                "Input.SendText",
                {"text": arguments.get("String") or "", "done": False},
            )
        else:
            LOG.debug("unhandled general command %s", name)

    def _rpc(self, method: str, params: JsonDict) -> None:
        kodirpc.call(method, params)
