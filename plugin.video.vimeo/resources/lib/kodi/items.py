import json
import urllib.parse
import xbmcgui

from resources.lib.api import Api
from resources.lib.kodi.utils import format_bold
from resources.lib.models.user import User
from resources.routes import *


class Items:
    def __init__(self, addon, addon_base, settings, search_history, vfs):
        self.addon = addon
        self.addon_base = addon_base
        self.settings = settings
        self.search_history = search_history
        self.vfs = vfs

    def root(self):
        items = []

        # Search
        list_item = xbmcgui.ListItem(label=self.addon.getLocalizedString(30101))
        url = self.addon_base + PATH_SEARCH
        items.append((url, list_item, True))

        # Charts
        list_item = xbmcgui.ListItem(label=self.addon.getLocalizedString(30102))
        url = self.addon_base + PATH_FEATURED
        items.append((url, list_item, True))

        # Trending
        list_item = xbmcgui.ListItem(label=self.addon.getLocalizedString(30103))
        url = self.addon_base + PATH_TRENDING
        items.append((url, list_item, True))

        # Categories
        list_item = xbmcgui.ListItem(label=self.addon.getLocalizedString(30104))
        url = self.addon_base + PATH_CATEGORIES
        items.append((url, list_item, True))

        # Log in/out
        user = self._get_authenticated_user()

        if isinstance(user, dict):
            user_model = User(id=user["resource_key"], label=self.addon.getLocalizedString(30105))
            user_model.data = user
            items.append(user_model.to_list_item(self.addon, self.addon_base))

            list_item = xbmcgui.ListItem(label=self.addon.getLocalizedString(30110))
            url = self.addon_base + PATH_AUTH_LOGOUT
            items.append((url, list_item, False))
        else:
            list_item = xbmcgui.ListItem(label=self.addon.getLocalizedString(30109))
            url = self.addon_base + PATH_AUTH_LOGIN
            items.append((url, list_item, False))

        # Settings
        list_item = xbmcgui.ListItem(label=self.addon.getLocalizedString(30108))
        url = self.addon_base + "/?action=settings"
        items.append((url, list_item, False))

        return items

    def search(self):
        items = []

        # New search
        list_item = xbmcgui.ListItem(label=format_bold(self.addon.getLocalizedString(30201)))
        url = self.addon_base + PATH_SEARCH + "?action=new"
        items.append((url, list_item, True))

        # Search history
        history = self.search_history.get()
        for k in sorted(list(history), reverse=True):
            query = history[k].get("query")
            list_item = xbmcgui.ListItem(label=query)
            list_item.addContextMenuItems(self._search_context_menu(query))
            url = self.addon_base + PATH_SEARCH + "?" + urllib.parse.urlencode({
                "query": history[k].get("query")
            })
            items.append((url, list_item, True))

        return items

    def search_sub(self, query):
        items = []

        # People
        list_item = xbmcgui.ListItem(label=format_bold(self.addon.getLocalizedString(30211)))
        url = self.addon_base + PATH_SEARCH + "?" + urllib.parse.urlencode({
            "action": "people",
            "query": query
        })
        items.append((url, list_item, True))

        # Channels
        list_item = xbmcgui.ListItem(label=format_bold(self.addon.getLocalizedString(30212)))
        url = self.addon_base + PATH_SEARCH + "?" + urllib.parse.urlencode({
            "action": "channels",
            "query": query
        })
        items.append((url, list_item, True))

        # Groups
        list_item = xbmcgui.ListItem(label=format_bold(self.addon.getLocalizedString(30213)))
        url = self.addon_base + PATH_SEARCH + "?" + urllib.parse.urlencode({
            "action": "groups",
            "query": query
        })
        items.append((url, list_item, True))

        return items

    def profile_sub(self, user):
        items = []
        authenticated_user = self._get_authenticated_user()

        # Followers
        if user["metadata"]["connections"]["followers"]["total"] > 0:
            list_item = xbmcgui.ListItem(label=format_bold(self.addon.getLocalizedString(30701)))
            url = self.addon_base + PATH_ROOT + "?" + urllib.parse.urlencode({
                "action": "call",
                "call": user["metadata"]["connections"]["followers"]["uri"]
            })
            items.append((url, list_item, True))

        # Following
        if user["metadata"]["connections"]["following"]["total"] > 0:
            list_item = xbmcgui.ListItem(label=format_bold(self.addon.getLocalizedString(30702)))
            url = self.addon_base + PATH_ROOT + "?" + urllib.parse.urlencode({
                "action": "call",
                "call": user["metadata"]["connections"]["following"]["uri"]
            })
            items.append((url, list_item, True))

        # Likes
        if user["metadata"]["connections"]["likes"]["total"] > 0:
            list_item = xbmcgui.ListItem(label=format_bold(self.addon.getLocalizedString(30703)))
            url = self.addon_base + PATH_ROOT + "?" + urllib.parse.urlencode({
                "action": "call",
                "call": user["metadata"]["connections"]["likes"]["uri"]
            })
            items.append((url, list_item, True))

        # Albums
        if user["metadata"]["connections"]["albums"]["total"] > 0:
            list_item = xbmcgui.ListItem(label=format_bold(self.addon.getLocalizedString(30704)))
            url = self.addon_base + PATH_ROOT + "?" + urllib.parse.urlencode({
                "action": "call",
                "call": user["metadata"]["connections"]["albums"]["uri"]
            })
            items.append((url, list_item, True))

        # Channels
        if user["metadata"]["connections"]["channels"]["total"] > 0:
            list_item = xbmcgui.ListItem(label=format_bold(self.addon.getLocalizedString(30212)))
            url = self.addon_base + PATH_ROOT + "?" + urllib.parse.urlencode({
                "action": "call",
                "call": user["metadata"]["connections"]["channels"]["uri"]
            })
            items.append((url, list_item, True))

        # Groups
        if user["metadata"]["connections"]["groups"]["total"] > 0:
            list_item = xbmcgui.ListItem(label=format_bold(self.addon.getLocalizedString(30213)))
            url = self.addon_base + PATH_ROOT + "?" + urllib.parse.urlencode({
                "action": "call",
                "call": user["metadata"]["connections"]["groups"]["uri"]
            })
            items.append((url, list_item, True))

        # Watchlist
        if isinstance(authenticated_user, dict) and user["uri"] == authenticated_user["uri"] and \
           authenticated_user["metadata"]["connections"]["watchlater"]["total"] > 0:
            list_item = xbmcgui.ListItem(label=format_bold(self.addon.getLocalizedString(30705)))
            url = self.addon_base + PATH_ROOT + "?" + urllib.parse.urlencode({
                "action": "call",
                "call": authenticated_user["metadata"]["connections"]["watchlater"]["uri"]
            })
            items.append((url, list_item, True))

        return items

    def featured(self):
        """
        Channel IDs were retrieved with the following request:
        curl https://api.vimeo.com/users/39723100/channels -H "Authorization: bearer <token>"
        """
        items = []

        # Staff Pics
        list_item = xbmcgui.ListItem(label=self.addon.getLocalizedString(30301))
        url = self.addon_base + PATH_FEATURED + "?" + urllib.parse.urlencode({
            "action": "channel",
            "id": "927"
        })
        items.append((url, list_item, True))

        # Premieres
        list_item = xbmcgui.ListItem(label=self.addon.getLocalizedString(30302))
        url = self.addon_base + PATH_FEATURED + "?" + urllib.parse.urlencode({
            "action": "channel",
            "id": "1143843"
        })
        items.append((url, list_item, True))

        # Best of the Month
        list_item = xbmcgui.ListItem(label=self.addon.getLocalizedString(30303))
        url = self.addon_base + PATH_FEATURED + "?" + urllib.parse.urlencode({
            "action": "channel",
            "id": "1143844"
        })
        items.append((url, list_item, True))

        # Best of the Year
        list_item = xbmcgui.ListItem(label=self.addon.getLocalizedString(30304))
        url = self.addon_base + PATH_FEATURED + "?" + urllib.parse.urlencode({
            "action": "channel",
            "id": "1172058"
        })
        items.append((url, list_item, True))

        # A Decade of Staff Picks
        list_item = xbmcgui.ListItem(label=self.addon.getLocalizedString(30305))
        url = self.addon_base + PATH_FEATURED + "?" + urllib.parse.urlencode({
            "action": "channel",
            "id": "1354461"
        })
        items.append((url, list_item, True))

        # Vimeo Curation channels
        list_item = xbmcgui.ListItem(label=self.addon.getLocalizedString(30306))
        url = self.addon_base + "/?" + urllib.parse.urlencode({
            "action": "call",
            "call": "/users/39723100/channels"
        })
        items.append((url, list_item, True))

        return items

    def from_collection(self, collection):
        items = []

        for item in collection.items:
            items.append(item.to_list_item(self.addon, self.addon_base))

        if collection.next_href:
            next_item = xbmcgui.ListItem(label=self.addon.getLocalizedString(30901))
            url = self.addon_base + "/?" + urllib.parse.urlencode({
                "action": "call",
                "call": collection.next_href
            })
            items.append((url, next_item, True))

        return items

    def _search_context_menu(self, query):
        return [
            (
                self.addon.getLocalizedString(30601),
                "RunPlugin({}/{}?{})".format(
                    self.addon_base, PATH_SEARCH, urllib.parse.urlencode({
                        "action": "remove",
                        "query": query
                    })
                )
            ),
            (
                self.addon.getLocalizedString(30602),
                "RunPlugin({}/{}?{})".format(
                    self.addon_base, PATH_SEARCH, urllib.parse.urlencode({"action": "clear"})
                )
             ),
        ]

    def _get_authenticated_user(self):
        token = self.settings.get("api.accesstoken")
        user = self.vfs.read(Api.api_user_cache_key)

        return json.loads(user) if user and token else False
