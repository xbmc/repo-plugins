"""At most two builds of one listing at a time, decided before anything is
imported.

A skin asks for its home widgets again at every visit to Home, and Kodi
starts the next request whether or not the last has answered. Each is an
invoker thread and an interpreter of its own (Kodi keeps one parked invoker
for the whole of Python, and a skin's own plugin calls take it), so nothing
is shared between them and each pays for every import again. When listings
are slow, the same URL is being built many times over, each build slower
for the others, until Kodi cannot create another thread.

So ``default.py`` comes here first. A request that is turned away has
imported this module and Kodi's own built-ins, and none of the rest of
kofin.

The slots are window properties, the one thing separate interpreters share
(``core/state.py`` names them; importing it is what this module exists to
avoid). A slot holds ``<deadline>|<nonce>``, the deadline on the monotonic
clock the whole process shares. Slots, not a counter: a count two requests
update at once drifts and stays wrong, and one stuck high would turn every
listing away for good, where a slot whose request died is free again at its
deadline.
"""

from __future__ import annotations

import _thread
import time

import xbmc
import xbmcgui
import xbmcplugin

PROP = "kofin.listing.flight"
# How many builds of one URL run side by side. Two, so that coming back to
# Home while the first is still answering is still served.
FLIGHTS = 2
# Longer than a listing takes on a loaded device. A build that outlives it
# leaves its slot open to one more, so the bound on a URL is then two builds
# started per SECONDS, not two in all; a longer lease would instead refuse a
# URL for that long after two requests died holding it.
SECONDS = 180.0
# The listing routes a skin puts on its home screen. Not ``play`` or
# ``check_exists``, which answer for one item and must always answer; not
# ``search`` or ``lyrics``, which a viewer asked for by hand.
BOUNDED_MODES = frozenset({"", "browse", "continuewatching", "nextepisodes", "extras"})
# Every path the scanner provider answers lies under this, and
# none of them is ever turned away: a native listing refused is a directory
# Kodi takes for empty.
NATIVE_MARK = "/native/"
_HOME_WINDOW = 10000


def bounded(argv: list[str]) -> str:
    """The URL a request is counted under, or '' when it is never counted:
    no directory fetch, a native path, a cleaner's check, a route outside
    ``BOUNDED_MODES``. Read with string operations alone; the router's own
    parse comes after its imports."""
    if len(argv) < 2 or NATIVE_MARK in argv[0]:
        return ""
    try:
        if int(argv[1]) < 0:
            return ""
    except ValueError:
        return ""
    query = (argv[2] if len(argv) > 2 else "").lstrip("?").rstrip("/")
    mode = ""
    if "%" in query or "+" in query:
        # An escape somewhere in it: read as the router will, at the price
        # of the one import, so that an escaped name or value cannot make
        # the two disagree about which route this is.
        from urllib.parse import parse_qsl

        params = dict(parse_qsl(query))
        if params.get("kodi_action"):
            return ""
        mode = params.get("mode", "")
    else:
        for part in query.split("&"):
            name, _, value = part.partition("=")
            if name == "kodi_action" and value:
                return ""
            if name == "mode":
                mode = value
    if mode not in BOUNDED_MODES:
        return ""
    return argv[0] + "?" + query


def _live(held: str, now: float) -> bool:
    try:
        return bool(held) and float(held.split("|", 1)[0]) > now
    except ValueError:
        return False


def claim(url: str) -> str | None:
    """A slot to build one listing of ``url`` in, or None when ``FLIGHTS``
    builds of it are running. The token goes to ``leave``.

    Two requests racing for one free slot can both win it; the bound is
    then one over for the length of a listing, the price of needing no lock
    that two interpreters could not share anyway. And a window that does
    not keep what it is given bounds nothing: the listing is built, with
    the empty token, since refusing every listing would be the worse
    failure."""
    window = xbmcgui.Window(_HOME_WINDOW)
    now = time.monotonic()
    for slot in range(FLIGHTS):
        key = "%s.%d.%s" % (PROP, slot, url)
        if _live(window.getProperty(key), now):
            continue
        mine = "%.3f|%d.%d" % (now + SECONDS, _thread.get_ident(), time.monotonic_ns())
        window.setProperty(key, mine)
        seen = window.getProperty(key)
        if seen == mine:
            return key + "\n" + mine
        if not _live(seen, now):
            return ""
    return None


def enter(argv: list[str]) -> str | None:
    """None when the request has been turned away and its directory ended;
    otherwise the token ``leave`` takes, empty when nothing is held."""
    url = bounded(argv)
    if not url:
        return ""
    token = claim(url)
    if token is None:
        xbmc.log(
            "[kofin] kofin.plugin.gate: %s is being built %d times over already;"
            " this request is turned away" % (url, FLIGHTS),
            xbmc.LOGDEBUG,
        )
        xbmcplugin.endOfDirectory(int(argv[1]), succeeded=False, cacheToDisc=False)
    return token


def leave(token: str | None) -> None:
    """Give a slot back, if it is still this request's: one that outlived
    its deadline may already be another's."""
    if not token:
        return
    key, _, mine = token.partition("\n")
    window = xbmcgui.Window(_HOME_WINDOW)
    if window.getProperty(key) == mine:
        window.clearProperty(key)
