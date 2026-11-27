"""What SyncPlay needs from the REST client.

``SyncPlayManager`` calls ``core.api.Api``'s verbs by name through getattr
(``_api``/``_api_raw``), so this Protocol is their static caller: the
manager's constructor and ``get_api`` are typed against it, ``Api`` is
checked against it where the service hands the client over
(``service/main.py``), and a renamed verb fails mypy.
"""

from typing import Any, Optional, Protocol, TypedDict

JsonDict = dict[str, Any]


class Claim(TypedDict, total=False):
    """The claimed play state the engine reads.

    What ``player.current_item()`` answers: kofin's service player claims
    every play resolved through the plugin, and the engine reads identity
    and transport off that claim, and ``Live``, which the play route
    (``plugin/play.py``) stamps on a channel and ``utils.claim_is_live``
    reads.
    ``Provider`` is absent on kofin's own claims and defaults to
    ``"jellyfin"`` — the key the provider registry dispatches on
    (``syncplay/providers.py``).
    """

    Id: str
    Provider: str
    Name: str
    RunTimeTicks: int
    PlayMethod: str
    PlaySessionId: str
    Live: bool


class SyncPlayApi(Protocol):
    """The SyncPlay and session verbs, plus the two socket helpers the
    time-sync transport needs. Signatures mirror ``core.api.Api``."""

    def get_utc_time(self) -> JsonDict: ...

    def item(self, item_id: str) -> JsonDict: ...

    def websocket_url(self, path: str) -> str: ...

    def authorization(self) -> str: ...

    def syncplay_list(self) -> list[JsonDict]: ...

    def syncplay_new(
        self, group_name: str, protocol_version: Optional[int] = None
    ) -> None: ...

    def syncplay_join(
        self, group_id: str, protocol_version: Optional[int] = None
    ) -> None: ...

    def syncplay_leave(self) -> None: ...

    def syncplay_hello(
        self, protocol_version: int, capabilities: Optional[list[str]] = None
    ) -> JsonDict: ...

    def syncplay_snapshot(self) -> None: ...

    def syncplay_ready(
        self, when: str, position_ticks: int, is_playing: bool, playlist_item_id: str
    ) -> None: ...

    def syncplay_buffering(
        self, when: str, position_ticks: int, is_playing: bool, playlist_item_id: str
    ) -> None: ...

    def syncplay_ping(self, ping_ms: int) -> None: ...

    def syncplay_unpause(self) -> None: ...

    def syncplay_pause(self) -> None: ...

    def syncplay_stop(self) -> None: ...

    def syncplay_seek(self, position_ticks: int) -> None: ...

    def syncplay_set_new_queue(
        self,
        item_ids: list[str],
        playing_item_position: int = 0,
        start_position_ticks: int = 0,
    ) -> None: ...

    def syncplay_set_new_queue_ex(
        self,
        entries: list[JsonDict],
        playing_item_position: int = 0,
        start_position_ticks: int = 0,
    ) -> None: ...

    def syncplay_next_item(self, playlist_item_id: str) -> None: ...

    def syncplay_set_ignore_wait(self, ignore_wait: bool) -> None: ...
