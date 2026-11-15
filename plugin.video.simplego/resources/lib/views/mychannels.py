"""My channels: the channels' manager (favourites, the own order, deactivation); nothing plays here.

The favourite and order actions run from the Live channels' menus too.
"""

import xbmcgui
import xbmcplugin

from resources.lib import kodiutil
from resources.lib import provider
from resources.lib.data import channellist
from resources.lib.views import listing
from resources.lib.views import rows

_s = kodiutil.string


class MyChannelsViews:
    """My channels (see views.routes).

    :param call: the plugin call (see views.call.Call)
    """

    def __init__(self, call):
        self._call = call

    def do_mychannels(self):
        """List every channel to manage, in the default order of channellist.grouped; no guide is read."""
        view = listing.list_view(self._call, channellist.MANAGE)
        subscribed = None if view["subscribed"] is None else set(view["subscribed"])
        favourites = set(view["favourites"] or ())
        off = set(view["deactivated"])
        for position, c in enumerate(view["channels"]):
            state = {
                "id": c["id"],
                "number": c["number"],
                "fav": int(c["id"] in favourites),
                "sub": int(subscribed is None or c["id"] in subscribed),
                "off": int(channellist.is_deactivated(c["id"], off)),
                "ordered": int(view["ordered"]),
            }
            li = self._managed_item(c, state, position)
            li.addContextMenuItems(
                [(label, "RunPlugin(%s)" % self._call.url(**params)) for label, params in self._manage_menu(state)]
            )
            # A click opens the same menu (see do_channel_menu), with what it needs in its address.
            xbmcplugin.addDirectoryItem(self._call.handle, self._call.url(action="channel_menu", **state), li, isFolder=False)
        self._call.laps("items")
        rows.add_channel_sorts(self._call.handle)
        xbmcplugin.endOfDirectory(self._call.handle)

    def do_channel_menu(self):
        """Offer a channel's management (a click on its row in My channels), and do what is chosen."""
        self._call.decline_play()
        menu = self._manage_menu({k: self._call.params[k] for k in ("id", "number", "fav", "sub", "off", "ordered")})
        choice = xbmcgui.Dialog().contextmenu([label for label, _ in menu])
        if choice < 0:
            return
        self._call.redirect({k: str(v) for k, v in menu[choice][1].items()})
        getattr(self, "do_" + self._call.action)()

    def do_deactivate(self):
        """Deactivate a subscribed channel in the lists, or activate it again (My channels' menu)."""
        on = self._call.params.get("on") == "1"
        channellist.set_deactivated(self._call.params["id"], on)
        xbmcgui.Dialog().notification(kodiutil.name(), _s(30233 if on else 30234))
        listing.list_changed()

    def do_move(self):
        """Move a channel in the account's own order: pick the channel it goes before."""
        channels = sorted(self._call.client.channel_list(scope="all"), key=provider.channels.sort_key)
        order = self._call.client.channel_order() or [c["id"] for c in channels]
        names = {c["id"]: "%s. %s" % (c["number"], c["name"]) for c in channels}
        # Channels the order does not have yet (new ones) go at its end, as the lists show them.
        order = [i for i in order if i in names] + [c["id"] for c in channels if c["id"] not in order]
        moving = self._call.params["id"]
        others = [i for i in order if i != moving]
        labels = [names[i] for i in others] + [_s(30178)]
        choice = xbmcgui.Dialog().select(_s(30179) % names.get(moving, "?"), labels)
        if choice < 0:
            return
        others.insert(choice, moving)
        self._call.client.set_channel_order(others)
        listing.list_changed()

    def do_reset_order(self):
        """Go back to the provider's channel numbering (the web's "Csatornasorrend visszaállítása")."""
        if xbmcgui.Dialog().yesno(_s(30177), _s(30180)):
            self._call.client.set_channel_order([])
            listing.list_changed()

    def do_favourite(self):
        """Put a channel onto the account's favourites or off them (the channel list's context menu)."""
        on = self._call.params.get("on") == "1"
        self._call.client.set_favourite_channel(self._call.params["number"], on)
        xbmcgui.Dialog().notification(kodiutil.name(), _s(30183 if on else 30184))
        listing.list_changed()

    @staticmethod
    def _manage_menu(state):
        """Return a channel's management as [(label, the action's parameters)]; the state's values as given or as text."""
        flag = {k: str(state[k]) == "1" for k in ("fav", "sub", "off", "ordered")}
        menu = [
            (_s(30176), {"action": "move", "id": state["id"]}),
            (
                rows.favourite_channel_item(not flag["fav"]),
                {"action": "favourite", "number": state["number"], "on": int(not flag["fav"])},
            ),
        ]
        if flag["sub"]:  # only a subscribed channel plays, so only one is worth deactivating
            deactivate = {"action": "deactivate", "id": state["id"], "on": int(not flag["off"])}
            menu.append((_s(30231 if flag["off"] else 30230), deactivate))
        if flag["ordered"]:
            menu.append((_s(30177), {"action": "reset_order"}))
        return menu

    @staticmethod
    def _managed_item(c, state, position):
        """Return a channel's row: its name and beside it what holds of it ("Deactivated | Favourite | Not subscribed").

        Greyed out if deactivated or not subscribed; nothing beside a plain subscribed one.
        """
        statuses = [(state["off"], _s(30236)), (state["fav"], _s(30237)), (not state["sub"], rows.not_available())]
        name = rows.greyed(c["name"]) if state["off"] or not state["sub"] else c["name"]
        li = xbmcgui.ListItem(rows.with_note(name, " | ".join(text for on, text in statuses if on)))
        # The row draws the icon (no thumb: the row would draw that), the strongest state's: deactivated,
        # favourite, not subscribed, else a plain channel's. Estuary's side panel draws the poster first: the logo there.
        icons = [
            (state["off"], "DefaultAddonNone.png"),
            (state["fav"], "DefaultFavourites.png"),
            (not state["sub"], "DefaultAddonTvInfo.png"),
        ]
        icon = next((name for on, name in icons if on), "DefaultTVShows.png")
        rows.set_art(li, {"poster": rows.panel_logo(c["logo"]), "icon": icon})
        # The sort keys only, no title: a titled row is "playable" to Kodi, which offers its own Play.
        rows.set_channel_sort_keys(li.getVideoInfoTag(), c, position)
        rows.hide_kodi_favourites(li)
        li.setProperty("IsPlayable", "false")
        return li
