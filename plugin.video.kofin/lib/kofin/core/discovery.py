"""Jellyfin's UDP auto-discovery (port 7359), client side.

Kodi-free on purpose, like :mod:`kofin.core.auth`: the dialog around this
lives in :mod:`kofin.plugin.serverpicker` and this module only talks to the
network.

The protocol is one plaintext datagram broadcast to 255.255.255.255:7359.
Every Jellyfin whose ``AutoDiscovery`` is on — the default — replies
**unicast** to the sender's ephemeral port with a small JSON object naming
itself: ``Address``, ``Id``, ``Name``, ``EndpointAddress``.

``SCAN_SECONDS`` is a *retry* budget and not a patience one. Replies come in
milliseconds, so one not seen within a few tens of milliseconds was lost
rather than delayed. The half that gets lost is ours: an access point sends
a broadcast frame at the lowest basic rate, unacknowledged, while the
server's answer comes back unicast. So the window is spent re-broadcasting
once a second rather than listening harder.

Several classes of server never answer at any timeout, which is what the
caller's "nothing found" wording has to account for: ``AutoDiscovery`` turned
off, Docker bridge networking (a published UDP port does not receive
255.255.255.255 traffic), another subnet, and — easy to misread as a bug —
a second Jellyfin on a host where something already holds 7359, since only
one process per machine can bind it.
"""

import json
import socket
import time
from typing import Any, Callable, NamedTuple, Optional
from urllib.parse import urlsplit

from kofin.core import auth
from kofin.core.log import Logger

LOG = Logger(__name__)

DISCOVERY_PORT = 7359
DISCOVERY_MESSAGE = b"who is JellyfinServer?"
BROADCAST_ADDRESS = "255.255.255.255"

# Three probes, one a second, then done. See the module docstring for why the
# budget buys repeats rather than a longer wait.
SCAN_SECONDS = 3.0
PROBE_INTERVAL_SECONDS = 1.0
READ_TIMEOUT_SECONDS = 1.0

# The real payload is ~120 bytes. 1024 is what every other client reads and
# leaves room for a long friendly name.
RECV_BYTES = 1024


class Found(NamedTuple):
    """One server that answered the broadcast.

    ``address`` is what the server *published* for this caller — Jellyfin
    answers with ``GetSmartApiUrl(remote)``, so it carries a scheme and a
    port and may name an external host. ``source_host`` is where the
    datagram actually came from, and is the recovery when the published
    address does not resolve or route from here (see :func:`fallback_address`).
    """

    server_id: str
    name: str
    address: str
    source_host: str


SocketFactory = Callable[[], socket.socket]
Clock = Callable[[], float]


def _open_socket() -> socket.socket:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    return sock


def _probe(sock: socket.socket) -> None:
    try:
        sock.sendto(DISCOVERY_MESSAGE, (BROADCAST_ADDRESS, DISCOVERY_PORT))
    except OSError as error:
        # No route to the broadcast address: an interface that is down, a
        # sandbox with no network. The window continues rather than ending
        # here — a later probe may land once the interface is up, and a scan
        # that found nothing is the same answer to the caller either way.
        LOG.warning("discovery probe failed: %s", error)


def _parse(data: bytes, source_host: str) -> Optional[Found]:
    try:
        payload = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        # Something else is sitting on 7359, or the datagram was truncated.
        # Not fatal: the rest of the window still belongs to whatever else
        # answers.
        LOG.warning("discovery: undecodable datagram from %s", source_host)
        return None
    if not isinstance(payload, dict):
        return None
    published = str(payload.get("Address") or "")
    try:
        address = auth.normalize_address(published)
    except ValueError:
        # urlsplit refuses a port that is not a number in range, and an
        # unclosed IPv6 bracket.
        LOG.warning("discovery: unusable address %r from %s", published, source_host)
        return None
    if not address:
        return None
    return Found(
        server_id=str(payload.get("Id") or ""),
        name=str(payload.get("Name") or "") or source_host,
        address=address,
        source_host=source_host,
    )


def scan(
    on_found: Optional[Callable[[Found], None]] = None,
    *,
    sock_factory: SocketFactory = _open_socket,
    clock: Clock = time.monotonic,
) -> list[Found]:
    """Broadcast for ``SCAN_SECONDS`` and return every server that answered.

    ``on_found`` fires once per *new* server, as the datagram arrives, so a
    caller that wants to verify each hit over HTTP can start while the window
    is still open and pay no wall clock for it.

    ``sock_factory`` and ``clock`` are the test seams — the same shape as
    ``Api.from_credentials(http, ...)`` — so the unit suite never touches the
    network.
    """
    found: list[Found] = []
    seen: set[tuple[str, str]] = set()
    sock = sock_factory()
    try:
        started = clock()
        probes = 0
        while True:
            now = clock()
            remaining = SCAN_SECONDS - (now - started)
            if remaining <= 0:
                break
            if now >= started + probes * PROBE_INTERVAL_SECONDS:
                _probe(sock)
                probes += 1
            sock.settimeout(min(READ_TIMEOUT_SECONDS, remaining))
            try:
                data, addr = sock.recvfrom(RECV_BYTES)
            except socket.timeout:
                continue
            except OSError as error:
                LOG.warning("discovery read failed: %s", error)
                break
            entry = _parse(data, addr[0])
            if entry is None:
                continue
            # Keyed on the address as well as the id: two servers restored
            # from one data directory share an ``Id``.
            key = (entry.server_id, entry.address)
            if key in seen:
                continue
            seen.add(key)
            found.append(entry)
            if on_found is not None:
                on_found(entry)
    finally:
        sock.close()
    LOG.debug("discovery: %s server(s) answered in %.1fs", len(found), SCAN_SECONDS)
    return found


def fallback_address(found: Found) -> str:
    """``found.address`` re-hosted on the IP the datagram actually came from.

    A server answers with the URL it publishes, which is not always one this
    box can use: a reverse-proxied install may answer a LAN client with its
    external hostname. The datagram's source address is the one thing in the
    exchange known to be reachable, so it is what the second attempt uses.
    """
    parts = urlsplit(found.address)
    netloc = found.source_host
    if parts.port:
        netloc = "%s:%d" % (netloc, parts.port)
    rebuilt = "%s://%s" % (parts.scheme, netloc)
    if parts.path:
        rebuilt += parts.path.rstrip("/")
    return auth.normalize_address(rebuilt)


def may_probe(found: Found) -> bool:
    """Whether the published address may be probed as it stands.

    Anything on the network can answer the broadcast, and the probe is sent
    before the user has picked anything, so a published address chooses the
    host and path of a request this box makes: ``/cgi-bin/x`` on its own
    loopback or on a router. A path is followed only on the host the reply
    came from, where it reaches nothing that host could not reach itself.
    A published address with a path on any other host is not probed;
    :func:`fallback_address`, which is always on the source host, is.
    """
    parts = urlsplit(found.address)
    if not parts.path:
        return True
    return (parts.hostname or "").lower() == found.source_host.lower()


def label_for(
    name: str, address: str, info: Optional[dict[str, Any]] = None
) -> tuple[str, str]:
    """``(label, label2)`` for one row of the select dialog.

    Pure, and here rather than in the picker, because Kodistubs'
    ``ListItem.getLabel()`` answers ``''`` — row text is only testable while
    it is a value rather than a widget.
    """
    server_name = name
    version = ""
    if info:
        server_name = str(info.get("ServerName") or "") or name
        version = str(info.get("Version") or "")
    detail = "%s · %s" % (address, version) if version else address
    return (server_name, detail)
