"""Fast play path: ask the background service to start the stream (see playservice).

Imports nothing but the standard library and Kodi's modules, so a channel
switch does not pay for loading the rest of the add-on.
"""

import json
import socket
import time
from urllib.parse import parse_qsl
from urllib.parse import urlencode

import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin

from resources.lib import resolveditem
from resources.lib.data import guidedata
from resources.lib.util import kodienv

PROPERTY = "%s.playservice" % kodienv.ADDON_ID
# Home window property: the live channel last handed to Kodi to play (views.channels.ChannelViews marks its row).
PLAYING = "%s.playing" % kodienv.ADDON_ID
CONNECT_TIMEOUT = 5
ANSWER_TIMEOUT = 600
# Error kinds told no more: the PIN dialog has said why, or the user cancelled a question.
SILENT = ("parental", "cancelled")
# Messages for the service's error kinds (shared with the full plugin).
ERRORS = {
    "auth": 30010,
    "geo": 30011,
    "subscription": 30139,
    "restart": 30141,
    "archive": 30142,
    "expired": 30259,
    "licence": 30012,
}


def playing_mark(params):
    """Return what PLAYING keeps for a play: a live channel's id; nothing for a programme (watched back or restarted)."""
    return "" if params.get("programme") else params.get("id", "")


def offer_instead(base, why, offer):
    """Say why nothing plays and offer what is left: the programme onto the favourites, or its row off Continue watching.

    :param base: the plugin's address (its actions do it, see views.programmes and views.continuing)
    :param why: the message (an airing no longer watched back)
    :param offer: {"id", "kind", "title", "next"} or {"mark"} (see watchoffer)
    """
    addon = xbmcaddon.Addon()
    if "mark" in offer:
        question = addon.getLocalizedString(30264)
        action = {"action": "continue_remove", "mark": offer["mark"]}
    else:
        question = addon.getLocalizedString(30260) % (offer["next"], offer["title"])
        action = {"action": "watch", "id": offer["id"], "kind": offer["kind"], "on": 1}
    # Kodi's own Yes/No: "Add to favourite programmes" did not fit the button.
    if xbmcgui.Dialog().yesno(addon.getAddonInfo("name"), "%s[CR][CR]%s" % (why, question)):
        xbmc.executebuiltin("RunPlugin(%s?%s)" % (base, urlencode(action)))


def _log(msg, level=xbmc.LOGDEBUG):
    """Log as kodiutil.log does, which the fast path does not load."""
    xbmc.log("[%s] %s" % (kodienv.ADDON_ID, msg), level)


def run(argv, started):
    """Play through the service; return False if it is not available (the caller falls back)."""
    begun = time.time()  # after Python's start and the imports: the log line below tells them apart
    params = dict(parse_qsl(argv[2].lstrip("?")))
    # "stream" in IPTV Simple's catch-up URL (see iptvfiles._catchup).
    params.setdefault("media", params.get("stream", ""))
    if not params.get("media") or not kodienv.isa_ready():
        return False
    query = {"id": params.get("id", ""), "media": params["media"]}
    if params.get("programme"):
        query["programme"] = guidedata.kodi_resume(params["programme"], argv)
    service = _connect()
    if service is None:
        return False
    try:
        asked = time.time()
        result = _get(service, "/play", query)
    except (OSError, ValueError) as e:  # no answer in time, or not one of the service's
        # The service has the request: playing directly too would open a second stream (and ask again).
        result = {"error": "api", "message": "play service: %s" % e}
    handle = int(argv[1])
    if result.get("error") == "auth":
        return False  # no (valid) login: the full plugin logs in by QR code, then plays
    if result.get("error") in SILENT:
        xbmcplugin.setResolvedUrl(handle, False, xbmcgui.ListItem())
        return True
    if "error" in result:
        addon = xbmcaddon.Addon()
        _log("play failed: %s" % result.get("message"), xbmc.LOGWARNING)
        if result.get("offer"):
            offer_instead(argv[0], addon.getLocalizedString(ERRORS[result["error"]]), result["offer"])
        elif result["error"] in ERRORS:
            xbmcgui.Dialog().ok(addon.getAddonInfo("name"), addon.getLocalizedString(ERRORS[result["error"]]))
        else:
            xbmcgui.Dialog().notification(
                addon.getAddonInfo("name"), (result.get("message") or "")[:120], xbmcgui.NOTIFICATION_ERROR
            )
        xbmcplugin.setResolvedUrl(handle, False, xbmcgui.ListItem())
        return True
    answered = time.time()
    xbmcplugin.setResolvedUrl(handle, True, resolveditem.list_item(result))
    xbmcgui.Window(10000).setProperty(PLAYING, playing_mark(params))
    now = time.time()
    _log(
        "play: resolved through the service after %.2fs"
        " (start %.2fs, before asking %.2fs, the service %.2fs, the item %.2fs)"
        % (now - started, begun - started, asked - begun, answered - asked, now - answered),
        xbmc.LOGDEBUG,
    )
    return True


def ask(path, timeout, **query):
    """Return the play service's JSON answer to a GET of `path` (see playservice); None if not had in time."""
    service = _connect()
    if service is None:
        return None
    try:
        return _get(service, path, query, timeout)
    except (OSError, ValueError):
        return None


def _connect():
    """Return (socket connected to the play service, its token); None if it does not run (or not yet)."""
    address = xbmcgui.Window(10000).getProperty(PROPERTY).split()
    if len(address) != 2:
        return None
    try:
        sock = socket.create_connection(("127.0.0.1", int(address[0])), timeout=CONNECT_TIMEOUT)
    except OSError as e:
        _log("play service unreachable (%s)" % e, xbmc.LOGWARNING)
        return None
    return sock, address[1]


def _get(service, path, query, timeout=ANSWER_TIMEOUT):
    """Send a bare HTTP/1.0 GET to the service and return its JSON answer.

    Not urllib.request: importing it (ssl, http.client, email) is a noticeable part of a switch on a TV stick.
    """
    sock, token = service
    path += "?" + urlencode(dict(query, token=token))
    with sock:
        # The service may wait on the user (the PIN, where to resume) before it answers a play.
        sock.settimeout(timeout)
        sock.sendall(("GET %s HTTP/1.0\r\nHost: 127.0.0.1\r\n\r\n" % path).encode())
        chunks = []
        while True:
            chunk = sock.recv(65536)
            if not chunk:
                break
            chunks.append(chunk)
    head, _, body = b"".join(chunks).partition(b"\r\n\r\n")
    status = head.split(b"\r\n", 1)[0]
    if b" 200 " not in status + b" ":
        raise OSError(status.decode("latin1"))
    return json.loads(body.decode("utf-8"))
