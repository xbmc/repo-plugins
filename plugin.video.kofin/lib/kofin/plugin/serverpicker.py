"""The LAN server picker (Account-tab settings button -> RunPlugin).

Broadcasts Jellyfin's UDP discovery probe (kofin.core.discovery), verifies
each answer over HTTP, and writes the chosen address into ``serverAddress``
so the Log in button below it has something to work with.

The settings button carries ``<close>true</close>``, so Kodi has committed
and closed the settings dialog before this route runs: a setting written
from here into a dialog that is still open is reverted when the user backs
out of it (``service/backdrop.py``). The route then reopens it — same
builtin as ``actions.open_settings`` — so the filled field is the
confirmation and Log in is the next press.

The verification is not a liveness check: what is in question is the
address the server published, which Jellyfin derives per caller and which
can name a host this box cannot resolve or route to. When it cannot be
reached, the datagram's own source address is tried, that being the one
endpoint in the exchange known to work.
"""

from concurrent.futures import Future, ThreadPoolExecutor
from typing import Any, NamedTuple, Optional, Union

import xbmc
import xbmcgui

from kofin.core import auth, discovery, settings, toast
from kofin.core.http import Http, JellyfinError, plugin_transport
from kofin.core.log import Logger
from kofin.core.settings import Credentials
from kofin.plugin.router import Request

LOG = Logger(__name__)

# One worker per address that can plausibly be answering at once. The probes
# overlap the scan window, so in the ordinary one-server case the
# verification has finished before the broadcast window even closes.
PROBE_WORKERS = 4

# How often the main thread pumps the progress dialog while the scan runs on
# its worker. Short enough that Cancel answers immediately and that a probe
# starts within a blink of its datagram arriving.
POLL_SECONDS = 0.1


class Candidate(NamedTuple):
    found: discovery.Found
    address: str
    info: Optional[dict[str, Any]]
    reachable: bool


def _text(string_id: int) -> str:
    return settings.localized(string_id)


def _addresses(found: discovery.Found) -> list[str]:
    """The addresses to try for one hit, best first. A published address
    left out by :func:`discovery.may_probe` is still offered, unverified,
    when its fallback does not answer either."""
    addresses = [found.address] if discovery.may_probe(found) else []
    fallback = discovery.fallback_address(found)
    if fallback and fallback not in addresses:
        addresses.append(fallback)
    return addresses


def _verify(transport: Http, found: discovery.Found) -> Candidate:
    for address in _addresses(found):
        try:
            info = auth.probe_public_info(transport, address)
        except (JellyfinError, ValueError) as error:
            # ValueError as well as the transport's own taxonomy: a body that
            # is not JSON means whatever answered is not the server, and one
            # bad address must not take the whole listing down with it.
            LOG.debug(
                "discovery: %s unreachable at %s (%s)", found.name, address, error
            )
            continue
        return Candidate(found=found, address=address, info=info, reachable=True)
    return Candidate(found=found, address=found.address, info=None, reachable=False)


def _scan_with_progress(transport: Http) -> Optional[list[Candidate]]:
    """Run the broadcast window, verifying hits as they land.

    None means the user cancelled. The scan runs on a worker so the main
    thread keeps the progress dialog honest — a Cancel button that cannot
    answer for three seconds is worse than none.
    """
    progress = xbmcgui.DialogProgress()
    progress.create(settings.addon_name(), _text(30827))
    monitor = xbmc.Monitor()
    arrivals: list[discovery.Found] = []
    probes: list[Future[Candidate]] = []
    cancelled = False

    try:
        with ThreadPoolExecutor(max_workers=PROBE_WORKERS + 1) as pool:
            scanning = pool.submit(discovery.scan, arrivals.append)
            elapsed = 0.0
            # Probes are submitted from this thread rather than from the
            # arrival callback: the pool is shut down when this block exits,
            # and a worker submitting into a closing pool raises.
            started_probes = 0
            while True:
                while started_probes < len(arrivals):
                    probes.append(
                        pool.submit(_verify, transport, arrivals[started_probes])
                    )
                    started_probes += 1
                if scanning.done():
                    break
                if progress.iscanceled():
                    cancelled = True
                    break
                elapsed += POLL_SECONDS
                progress.update(
                    min(99, int(elapsed * 100 / discovery.SCAN_SECONDS)), _text(30827)
                )
                if monitor.waitForAbort(POLL_SECONDS):
                    cancelled = True
                    break
            if cancelled:
                # Closed here rather than left to the finally, which runs only
                # once the pool has joined: the scan thread still has the rest
                # of the window to run, and a progress dialog that stays up
                # after Cancel reads as a hang. The normal path keeps the
                # dialog until the probes are in, which is the opposite case.
                progress.close()
    finally:
        progress.close()

    # The pool has been joined by here, so the scan is done however it ended.
    # Nothing reads its return value -- the arrivals list is the channel -- so
    # a raise inside it would otherwise be swallowed entirely, and the one
    # plausible cause is a socket this platform would not let us open.
    failure = scanning.exception()
    if failure is not None:
        LOG.error("discovery scan failed: %s", failure)

    if cancelled:
        LOG.debug("discovery: cancelled")
        return None
    return [probe.result() for probe in probes]


def find_servers(request: Request) -> None:
    """Find Jellyfin servers on the local network and fill in the address."""
    if Credentials.load().is_logged_in:
        # The button is hidden once signed in, but the route is reachable by
        # URL, and every other picker guards the same way.
        return

    transport = plugin_transport(settings.user_agent())
    try:
        candidates = _scan_with_progress(transport)
    finally:
        transport.close()

    if candidates is None:
        return
    if not candidates:
        toast.show(_text(30829), toast.WARNING, time_ms=6000)
        return

    # Reachable first: an entry that answered nothing is offered rather than
    # hidden, because the user may know the network better than the probe
    # does, but it should not be the obvious pick.
    candidates.sort(key=lambda entry: (not entry.reachable, entry.found.name.lower()))

    items: list[Union[str, xbmcgui.ListItem]] = []
    for candidate in candidates:
        label, detail = discovery.label_for(
            candidate.found.name, candidate.address, candidate.info
        )
        if not candidate.reachable:
            detail = "%s · %s" % (detail, _text(30830))
        items.append(xbmcgui.ListItem(label, detail))

    choice = xbmcgui.Dialog().select(_text(30828), items, useDetails=True)
    if choice < 0:
        return

    picked = candidates[choice]
    settings.set_str("serverAddress", picked.address)
    LOG.debug("discovery: server address set to %s", picked.address)
    if not picked.reachable:
        toast.show(_text(30831) % picked.found.name, toast.WARNING, time_ms=6000)
    xbmc.executebuiltin("Addon.OpenSettings(plugin.video.kofin)")
