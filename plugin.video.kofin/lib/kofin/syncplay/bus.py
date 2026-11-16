"""The engine's end of the SyncSession bus (docs/syncplay-provider-contract.md):
what other add-ons tell SyncPlay, and the session mirror they read."""

import time
from typing import TYPE_CHECKING, Any, Optional

from kofin.core import contract, state
from kofin.core.log import Logger
from kofin.syncplay import utils
from kofin.syncplay.ports import Claim
from kofin.syncplay.providers import JELLYFIN, DelegatedProvider, TemplateProvider
from kofin.syncplay.utils import FOLLOWING

if TYPE_CHECKING:
    from kofin.syncplay.manager import SyncPlayManager

LOG = Logger(__name__)


class ProviderBus:
    """Registration, proposals and claims from the providers on the bus, and
    the session state published for them. Owns the foreign claim: what is
    playing when kofin's own pipeline did not resolve it."""

    def __init__(self, manager: "SyncPlayManager") -> None:
        self.manager = manager
        self.foreign_claim: Optional[Claim] = None
        self._foreign_claim_at = 0.0

    def on_foreign_claim(self, claim: Claim) -> None:
        """SyncProvider.Claim: what is playing when kofin's own pipeline
        did not resolve it. Called on the notification thread; applied on
        the dispatcher."""
        self.manager._post(self._take_claim, claim)

    def _take_claim(self, claim: Claim) -> None:
        manager = self.manager
        self.foreign_claim = claim
        self._foreign_claim_at = time.time()
        LOG.debug(
            "[ syncplay/claim ] foreign: %s via %s",
            claim.get("Id"),
            claim.get("Provider"),
        )

        if (
            manager.in_group()
            and not manager.ignore_wait
            and manager.phase in FOLLOWING
            and claim.get("Id")
            and claim.get("Id") != manager.current_item_id
        ):
            # A new foreign play while following the group: the claim is
            # the propose trigger, because the event chain cannot be — a
            # PVR zap fires no OnPlay, only an unpause echo whose programmatic
            # grace swallows the AVStarted forward.
            # A fresh start (phase idle) keeps the event-driven path, and
            # the adoption echo is inert here: its claim names the current
            # item.
            manager._post(manager.holds.forward)

    def drop_stale_claim(self) -> None:
        """A new local play is starting: a foreign claim older than
        STALE_CLAIM_SECS describes the *previous* playback (a seamless zap
        emits no stop to clear it). A fresh claim (a provider that claims at
        resolve time, before OnPlay) is kept."""
        if self.foreign_claim is None:
            return

        if time.time() - self._foreign_claim_at <= utils.STALE_CLAIM_SECS:
            return

        self.foreign_claim = None

    def on_provider_register(self, sender: str, payload: dict[str, Any]) -> None:
        """SyncProvider.Register: wrap the play template as a provider.

        Re-registration replaces — providers answer every service announce
        (SyncSession.State), so the registry rebuilds itself across service
        generations with no persistence anywhere.
        """
        play = contract.register_template(payload)

        if play is None:
            LOG.debug("Register from %s without a usable play template", sender)
            return

        name = payload["provider"]

        if name == JELLYFIN:
            LOG.warning("Register from %s tried to replace %r", sender, JELLYFIN)
            return

        providers = self.manager.providers
        if play.get("delegated"):
            providers.register(name, DelegatedProvider(play["audio"]))
        else:
            providers.register(
                name, TemplateProvider(play["url_template"], play["audio"])
            )
        LOG.debug(
            "[ syncplay/provider ] %r registered by %s%s",
            name,
            sender,
            " (delegated)" if play.get("delegated") else "",
        )

    def on_propose(self, payload: dict[str, Any]) -> None:
        """SyncSession.Propose: a provider asks for its item as the group
        queue — the programmatic form of the hold-and-propose flow."""
        self.manager._post(self._propose, payload)

    def _propose(self, payload: dict[str, Any]) -> None:
        if not self.manager.in_group():
            LOG.debug(
                "Propose from %r outside a group; ignored", payload.get("provider")
            )
            return

        position = utils.ticks_to_seconds(payload.get("position_ticks") or 0)
        provider = payload.get("provider") or JELLYFIN

        content = None
        if provider != JELLYFIN:
            name = payload.get("name")
            try:
                runtime = int(payload.get("runtime_ticks") or 0)
            except (TypeError, ValueError):
                runtime = 0
            content = {
                "Provider": provider,
                "Key": payload["key"],
                "Name": name[:256] if isinstance(name, str) else "",
                "RunTimeTicks": max(0, runtime),
            }

        self.manager.holds.propose(
            payload["key"], position=position, provider=provider, content=content
        )

    def publish_session_state(self, announce: bool = False) -> None:
        """The public session mirror on ``syncsession.state``.

        ``announce`` also pings SyncSession.State over the bus — group
        join/leave and service start, which is what tells providers to
        (re)register; every other publish is property-only so the bus
        stays quiet through ordinary phase traffic.
        """
        manager = self.manager
        names = []

        for member in manager.members or []:
            if isinstance(member, dict):
                names.append(member.get("UserName") or "?")
            else:
                names.append("%s" % member)

        current = None

        if manager.current_item_id:
            info = manager._local_file_info() or {}
            current = {
                "provider": info.get("Provider") or JELLYFIN,
                "key": manager.current_item_id,
            }

        state.publish_syncsession(
            {
                "v": contract.VERSION,
                "in_group": manager.in_group(),
                "group_name": (manager.group or {}).get("GroupName") or "",
                "members": names,
                "phase": str(manager.phase),
                "current": current,
            }
        )

        if announce:
            try:
                contract.publish_state()
            except Exception as error:  # never let the bus break the engine
                LOG.warning("SyncSession.State announce failed: %s", error)
