from resources.routes import *

import urllib.parse
import xbmcgui


class Items:
    def __init__(self, addon, addon_base):
        self.addon = addon
        self.addon_base = addon_base

    def root(self):
        items = []

        # Videos
        list_item = xbmcgui.ListItem(label=self.addon.getLocalizedString(30101))
        url = self.addon_base + PATH_VIDEOS
        items.append((url, list_item, True))

        # Standings
        list_item = xbmcgui.ListItem(label=self.addon.getLocalizedString(30102))
        url = self.addon_base + PATH_STANDINGS
        items.append((url, list_item, True))

        # Racing
        list_item = xbmcgui.ListItem(label=self.addon.getLocalizedString(30103))
        url = self.addon_base + PATH_RACING
        items.append((url, list_item, True))

        # Settings
        list_item = xbmcgui.ListItem(label=self.addon.getLocalizedString(30109))
        url = self.addon_base + "/?action=settings"
        items.append((url, list_item, False))

        return items

    def standings(self):
        items = []

        # Drivers
        list_item = xbmcgui.ListItem(label=self.addon.getLocalizedString(30120))
        url = self.addon_base + PATH_STANDINGS + "?" + urllib.parse.urlencode({
            "action": "drivers",
        })
        items.append((url, list_item, True))

        # Constructors
        list_item = xbmcgui.ListItem(label=self.addon.getLocalizedString(30121))
        url = self.addon_base + PATH_STANDINGS + "?" + urllib.parse.urlencode({
            "action": "constructors",
        })
        items.append((url, list_item, True))

        # Race results
        list_item = xbmcgui.ListItem(label=self.addon.getLocalizedString(30122))
        url = self.addon_base + PATH_STANDINGS + "?" + urllib.parse.urlencode({
            "action": "results",
        })
        items.append((url, list_item, True))

        return items

    def from_collection(self, collection):
        items = []

        for item in collection.items:
            items.append(item.to_list_item(self.addon_base))

        if collection.next_href:
            next_item = xbmcgui.ListItem(label=self.addon.getLocalizedString(30901))
            url = self.addon_base + "/?" + urllib.parse.urlencode({
                "action": "call",
                "call": collection.next_href,
            })
            items.append((url, next_item, True))

        return items
