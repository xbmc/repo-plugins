#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from future import standard_library
standard_library.install_aliases()
from builtins import str
from builtins import object
import html
import os
import sys
import urllib.parse
import xml.etree.ElementTree as ElementTree
from datetime import datetime, timedelta, timezone

import requests
import xbmcgui
import xbmcplugin

from resources.lib.gamekings_const import (CATEGORY_ACTIVITY_DAYS, CATEGORY_SITEMAP_URL, CATEGORY_API_URL,
                                           EXCLUDED_CATEGORY_SLUGS, IMAGES_PATH, LANGUAGE, SETTINGS, log)

class Main(object):
    def __init__(self):
        self.plugin_url = sys.argv[0]
        self.plugin_handle = int(sys.argv[1])
        self.show_categories()

    def show_categories(self):
        categories = self._get_categories()
        if not categories:
            xbmcplugin.endOfDirectory(self.plugin_handle, succeeded=False)
            return

        listing = []
        for category in categories:
            label = category["name"]
            list_item = xbmcgui.ListItem(label=label)
            list_item.setArt({
                "thumb": "DefaultFolder.png",
                "icon": "DefaultFolder.png",
                "fanart": os.path.join(IMAGES_PATH, "fanart-blur.jpg"),
            })
            list_item.setProperty("IsPlayable", "false")
            parameters = {
                "action": "list",
                "plugin_category": label,
                "url": category["url"] + "page/001/",
                "next_page_possible": "True",
            }
            url = self.plugin_url + "?" + urllib.parse.urlencode(parameters)
            listing.append((url, list_item, True))

        xbmcplugin.addDirectoryItems(self.plugin_handle, listing, len(listing))
        xbmcplugin.addSortMethod(
            handle=self.plugin_handle,
            sortMethod=xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE,
        )
        xbmcplugin.endOfDirectory(self.plugin_handle)

    def _get_categories(self):
        try:
            return self._fetch_categories()
        except Exception as error:
            log("Error getting categories metadata", error)
            self._show_error()
            return None

    def _fetch_categories(self):
        sitemap_response = requests.get(CATEGORY_SITEMAP_URL, timeout=20)
        sitemap_response.raise_for_status()
        active_links = self._parse_active_category_links(sitemap_response.text)

        # GameKings currently fits within the WordPress API's 100-item limit.
        category_response = requests.get(
            CATEGORY_API_URL,
            params={"per_page": 100, "_fields": "name,slug,count,link"},
            timeout=20,
        )
        category_response.raise_for_status()

        # log("category_response.json()", category_response.json())

        categories = []
        for category in category_response.json():
            slug = category.get("slug", "")
            url = self._category_url(category.get("link", ""))
            # Exclude inactive category
            if self._normalize_url(url) not in active_links:
                continue
            # Exclude predetermined category
            if slug in EXCLUDED_CATEGORY_SLUGS:
                continue
            # Exclude category with no items
            if int(category.get("count", 0)) <= 0:
                continue

            categories.append({
                "name": html.unescape(category.get("name", slug)),
                "url": url,
            })

        categories.sort(key=lambda category: category["name"].casefold())
        if not categories:
            raise ValueError("No active video categories found")
        return categories

    # Select category links with a recent modification date-time
    def _parse_active_category_links(self, sitemap_xml):
        cutoff = datetime.now(timezone.utc) - timedelta(days=CATEGORY_ACTIVITY_DAYS)
        active_links = set()
        root = ElementTree.fromstring(sitemap_xml)

        for url_element in root:
            values = {}
            for child in url_element:
                values[child.tag.rsplit("}", 1)[-1]] = child.text or ""

            location = values.get("loc", "")
            lastmod = values.get("lastmod", "")
            if not location or not lastmod:
                continue

            try:
                modified = datetime.fromisoformat(lastmod.replace("Z", "+00:00"))
            except (TypeError, ValueError):
                continue
            if modified.tzinfo is None:
                modified = modified.replace(tzinfo=timezone.utc)
            if modified >= cutoff:
                active_link = self._normalize_url(self._category_url(location))

                # log("active_link", active_link)

                active_links.add(active_link)

        return active_links

    def _show_error(self):
        xbmcgui.Dialog().notification(
            SETTINGS.getAddonInfo("name"),
            LANGUAGE(30507) % LANGUAGE(30007),
            xbmcgui.NOTIFICATION_ERROR,
            5000,
        )

    @staticmethod
    def _category_url(url):
        return url.rstrip("/") + "/"

    @staticmethod
    def _normalize_url(url):
        return url.rstrip("/").lower()
