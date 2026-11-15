"""What the user is told when nothing plays, by the provider error's kind (the fast play path's and the plugin's).

Kodi's modules only: the fast play path (quickplay) imports it.
"""

from urllib.parse import urlencode

import xbmc
import xbmcaddon
import xbmcgui

# Error kinds told no more: the PIN dialog has said why, or the user cancelled a question.
SILENT = ("parental", "cancelled")
# The message string id of each error kind with one of its own.
ERRORS = {
    "auth": 30010,
    "geo": 30011,
    "subscription": 30139,
    "restart": 30141,
    "archive": 30142,
    "expired": 30259,
    "licence": 30012,
}


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
