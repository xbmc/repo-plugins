"""The provider seam: how the engine starts content and maps local plays.

The engine coordinates the *global* Kodi player; what a queue item id means —
how to start it at a position, and how a Kodi library id maps back to one — is
the owning provider's business. Jellyfin-through-kofin is always registered;
template and delegated providers register over the public bus
(``SyncPlayManager.on_provider_register``).

Kept in the ``ports.py`` discipline: the engine types against the Protocol,
the registry is the only dispatch, and the Jellyfin implementation is the one
place the engine's start path may reach kofin's plugin URL builder and sync
database.
"""

from typing import Optional, Protocol, TypedDict
from urllib.parse import quote

from kofin.core.log import Logger
from kofin.core.urls import PARAM_UNATTENDED, plugin_url
from kofin.syncplay.ports import JsonDict, SyncPlayApi

LOG = Logger(__name__)

JELLYFIN = "jellyfin"

# Jellyfin item types whose length is not fixed, so no runtime is claimed for
# them: channels and programmes, and ``Recording`` — a recording still being
# written is already longer than the length it was probed at.
LIVE_TYPES = frozenset(
    {"TvChannel", "LiveTvChannel", "Program", "LiveTvProgram", "Recording"}
)


class _PlayTargetRequired(TypedDict):
    url: str
    audio: bool


class PlayTarget(_PlayTargetRequired, total=False):
    """What the playback controller needs to start a queue item: the URL to
    hand Kodi, and which playlist it belongs on.

    ``runtime_ticks`` is the item's length where its provider can vouch for
    one, so the engine can decline a start aimed at or past the end. A
    provider that cannot — live content, a template or delegated provider —
    leaves it out, and nothing is checked."""

    runtime_ticks: int


class Provider(Protocol):
    """What the engine needs from a content provider."""

    def play_target(self, key: str, start_ticks: int) -> PlayTarget: ...

    def resolve_kodi_id(self, kodi_id: int, media: str) -> Optional[str]: ...


class JellyfinProvider:
    """Jellyfin-through-kofin: the reference provider.

    ``api`` mirrors the manager's Optional client: a manager built without
    one answers every start with a failed lookup.
    """

    def __init__(self, api: Optional[SyncPlayApi]):
        self.api = api

    def play_target(self, key: str, start_ticks: int) -> PlayTarget:
        # Direct on the client, not via the manager's _api wrapper: a 403
        # here is a library permission problem, not lost group membership.
        if self.api is None:
            raise LookupError("no API client")

        item = self.api.item(key)

        if not item:
            raise LookupError("item lookup failed")

        # A group start is nobody's at this Kodi: the play route asks nothing.
        params = {"mode": "play", "id": str(key), PARAM_UNATTENDED: "1"}

        # Always sent, and never negative: omitted, the play route falls back
        # to the member's own resume point; and the estimate can extrapolate
        # below zero across a clock offset.
        params["startticks"] = str(max(0, int(start_ticks or 0)))

        target: PlayTarget = {
            "url": plugin_url(params),
            "audio": item.get("Type") == "Audio",
        }
        runtime_ticks = self._runtime_ticks(item)

        if runtime_ticks:
            target["runtime_ticks"] = runtime_ticks

        return target

    @staticmethod
    def _runtime_ticks(item: JsonDict) -> int:
        """The longest this item can run, or 0 when that is not known.

        The longest of its versions, not the item's own figure: that one
        describes the primary version, and a member may be on a longer cut.
        """
        if item.get("Type") in LIVE_TYPES:
            return 0

        sources = item.get("MediaSources") or []

        return max(
            [int(item.get("RunTimeTicks") or 0)]
            + [int(source.get("RunTimeTicks") or 0) for source in sources]
        )

    def resolve_kodi_id(self, kodi_id: int, media: str) -> Optional[str]:
        # A native row is ours when Kodi's row and the catalogue agree on its
        # unique id and resolver URL. A lookup that fails raises: the caller
        # leaves that play to its claim rather than calling it foreign.
        from kofin.sync.backends.api.identity import mapped_item

        item_id = mapped_item(kodi_id, media)
        return str(item_id) if item_id else None


class TemplateProvider:
    """A provider registered over the public bus: start-only.

    The template names ``{key}`` and optionally ``{position_s}`` (whole
    seconds). Substitution is by token replace, never str.format — the
    template is foreign text and must not be able to name anything else.
    ``resolve_kodi_id`` answers None: a foreign provider has no claim on
    the Kodi library; its plays are identified by the claims it publishes.
    """

    def __init__(self, template: str, audio: bool = False):
        self.template = template
        self.audio = audio

    def play_target(self, key: str, start_ticks: int) -> PlayTarget:
        seconds = max(0, int(start_ticks or 0)) // 10000000
        url = self.template.replace("{key}", quote(key, safe="")).replace(
            "{position_s}", str(seconds)
        )
        return {"url": url, "audio": self.audio}

    def resolve_kodi_id(self, kodi_id: int, media: str) -> Optional[str]:
        return None


class DelegatedProvider:
    """A provider whose starts the engine cannot make (the provider
    contract's delegated start): its content is tuned, not fetched, so
    there is no URL to build — the engine broadcasts SyncSession.Start
    and the provider's own service executes it."""

    delegated = True

    def __init__(self, audio: bool = False):
        self.audio = audio

    def play_target(self, key: str, start_ticks: int) -> PlayTarget:
        raise LookupError("delegated provider has no play target")

    def resolve_kodi_id(self, kodi_id: int, media: str) -> Optional[str]:
        return None


class ProviderRegistry:
    """The engine's one dispatch from a content key to its provider."""

    def __init__(self) -> None:
        self._providers: dict[str, Provider] = {}

    def register(self, name: str, provider: Provider) -> None:
        self._providers[name] = provider

    def get(self, name: str = JELLYFIN) -> Provider:
        return self._providers[name]

    def is_delegated(self, name: str) -> bool:
        """Whether the named provider takes delegated starts. False for an
        unregistered name, which the ordinary start path (play_target)
        tries as a Jellyfin item."""
        provider = self._providers.get(name)
        return bool(getattr(provider, "delegated", False))

    def play_target(
        self, key: str, start_ticks: int, provider: str = JELLYFIN
    ) -> PlayTarget:
        named = self._providers.get(provider)
        if named is None:
            # A provider this member lacks. Its key may still be an item the
            # server has: pvr.kofin names a live channel by its Jellyfin id,
            # so a member without pvr.kofin plays the channel through kofin.
            # Any other key fails the Jellyfin lookup, and with it the load.
            LOG.debug(
                "[ syncplay/play ] no provider %s here; key %s as a Jellyfin item",
                provider,
                key,
            )
            named = self._providers[JELLYFIN]
        return named.play_target(key, start_ticks)

    def resolve_kodi_id(self, kodi_id: int, media: str) -> Optional[str]:
        # The default provider owns the Kodi library.
        return self.get(JELLYFIN).resolve_kodi_id(kodi_id, media)


def jellyfin_registry(api: Optional[SyncPlayApi]) -> ProviderRegistry:
    """The registry every kofin service starts with."""
    registry = ProviderRegistry()
    registry.register(JELLYFIN, JellyfinProvider(api))
    return registry
