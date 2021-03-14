# coding: utf-8
#
# Copyright © 2020 melmorabity
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 51
# Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.

from __future__ import unicode_literals
import logging
import os
import re

try:
    from typing import Dict
    from typing import Optional
    from typing import Text
except ImportError:
    pass

try:
    from urllib.parse import parse_qsl
    from urllib.parse import quote
except ImportError:
    from urlparse import parse_qsl
    from urllib import quote

from inputstreamhelper import Helper  # pylint: disable=import-error
import xbmc  # pylint: disable=import-error
from xbmcaddon import Addon  # pylint: disable=import-error
from xbmcgui import Dialog  # pylint: disable=import-error
from xbmcgui import ListItem  # pylint: disable=import-error
import xbmcplugin  # pylint: disable=import-error

from resources.lib.api import FranceTV
from resources.lib.api import ParsedItem
import resources.lib.kodilogging
from resources.lib.utils import update_url_params
from resources.lib.video import FranceTVVideo
from resources.lib.video import FranceTVVideoException


resources.lib.kodilogging.config()

_LOGGER = logging.getLogger(__name__)

_KODI_VERSION = int(xbmc.getInfoLabel("System.BuildVersion").split(".")[0])


# pylint: disable=too-few-public-methods
class FranceTVAddon:
    _ADDON_ID = "plugin.video.francetv"
    _ADDON = Addon()
    _ADDON_DIR = xbmc.translatePath(_ADDON.getAddonInfo("path"))
    _ADDON_MEDIA_DIR = os.path.join(_ADDON_DIR, "resources", "media")
    _ADDON_FANART = Addon().getAddonInfo("fanart")
    _USER_AGENT = (
        "Mozilla/5.0 (X11; Fedora; Linux x86_64; rv:85.0) Gecko/20100101 "
        "Firefox/85.0"
    )

    def __init__(self, base_url, handle, params):
        # type: (Text, int, Text) -> None

        self._base_url = base_url
        self._handle = handle
        self._params = self._params_to_dict(params)

        self._api = FranceTV()

    @staticmethod
    def _params_to_dict(params):
        # type: (Optional[Text]) -> Dict[Text, Text]

        # Parameter string starts with a '?'
        return dict(parse_qsl(params[1:])) if params else {}

    def _localize(self, label):
        # type: (Text) -> Text

        return re.sub(
            r"\$LOCALIZE\[(\d+)\]",
            lambda m: self._ADDON.getLocalizedString(int(m.group(1))),
            label,
        )

    def _add_listitem(self, parsed_item):
        # type: (ParsedItem) -> None

        is_folder = parsed_item.url.get("mode") != "watch"

        _LOGGER.debug("Add ListItem %s", parsed_item)
        listitem = ListItem(
            label=self._localize(parsed_item.label), offscreen=True
        )
        listitem.setInfo("video", parsed_item.info)

        # Set fallback fanart
        parsed_item.art.setdefault("fanart", self._ADDON_FANART)
        listitem.setArt(parsed_item.art)

        for key, value in list(parsed_item.properties.items()):
            listitem.setProperty(key, value)

        xbmcplugin.addDirectoryItem(
            self._handle,
            update_url_params(self._base_url, **parsed_item.url),
            listitem,
            isFolder=is_folder,
        )

    def _mode_collection(self, path):
        # type: (Text) -> None

        xbmcplugin.setContent(self._handle, "videos")
        xbmcplugin.addSortMethod(
            self._handle, xbmcplugin.SORT_METHOD_UNSORTED, label2Mask="%Z"
        )

        level = None  # type: Optional[int]
        if self._params.get("level"):
            try:
                level = int(self._params["level"])
            except ValueError:
                pass

        for item in self._api.get_collection(path, level):
            self._add_listitem(item)

    def _mode_watch(self):
        # type: () -> None

        video_id = self._params["id"]

        is_helper = Helper("mpd")
        use_dash = bool(is_helper.check_inputstream())
        video_url = FranceTVVideo().get_video_url(video_id, use_dash)

        # Workaround for
        # https://github.com/melmorabity/plugin.video.francetv/issues/2
        headers = "User-Agent={}".format(self._USER_AGENT)

        listitem = ListItem(
            path="{}|{}".format(video_url, headers),
            offscreen=True,
        )

        # Use DASH if possible for better subtitle management
        if use_dash and ".mpd" in video_url:
            listitem.setMimeType("application/dash+xml")
            listitem.setProperty("inputstream.adaptive.manifest_type", "mpd")
            if _KODI_VERSION >= 19:
                listitem.setProperty(
                    "inputstream", is_helper.inputstream_addon
                )
            else:
                listitem.setProperty(
                    "inputstreamaddon", is_helper.inputstream_addon
                )
            listitem.setProperty(
                "inputstream.adaptive.stream_headers", headers
            )
        xbmcplugin.setResolvedUrl(self._handle, True, listitem)

    def _mode_search(self):
        # type: () -> None

        search = Dialog().input(self._ADDON.getLocalizedString(30005))

        self._mode_collection(
            "apps/search?term={}&filters=with-lives,with-collections".format(
                quote(search, safe="")
            )
        )

    def _mode_default(self):
        # type: () -> None

        self._add_listitem(
            ParsedItem(
                self._ADDON.getLocalizedString(30001),
                {"mode": "collection", "path": "apps/page/_"},
                {},
                {"icon": os.path.join(self._ADDON_MEDIA_DIR, "home.png")},
                {},
            )
        )
        self._add_listitem(
            ParsedItem(
                self._ADDON.getLocalizedString(30002),
                {"mode": "collection", "path": "generic/directs"},
                {},
                {"icon": os.path.join(self._ADDON_MEDIA_DIR, "live-tv.png")},
                {},
            )
        )
        self._add_listitem(
            ParsedItem(
                self._ADDON.getLocalizedString(30003),
                {"mode": "collection", "path": "generic/channels"},
                {},
                {"icon": os.path.join(self._ADDON_MEDIA_DIR, "channels.png")},
                {},
            )
        )
        self._add_listitem(
            ParsedItem(
                self._ADDON.getLocalizedString(30004),
                {"mode": "collection", "path": "generic/categories"},
                {},
                {
                    "icon": os.path.join(
                        self._ADDON_MEDIA_DIR, "categories.png"
                    )
                },
                {},
            )
        )
        self._add_listitem(
            ParsedItem(
                self._ADDON.getLocalizedString(30005),
                {"mode": "search"},
                {},
                {"icon": os.path.join(self._ADDON_MEDIA_DIR, "search.png")},
                {},
            )
        )

    def run(self):
        # type: () -> None

        mode = self._params.get("mode")
        _LOGGER.debug("Addon params = %s", self._params)
        succeeded = True

        try:
            if mode == "collection" and self._params.get("path"):
                self._mode_collection(self._params["path"])
            elif mode == "watch" and self._params.get("id"):
                self._mode_watch()
            elif mode == "search":
                self._mode_search()
            else:
                self._mode_default()
        except FranceTVVideoException as ex:
            _LOGGER.error(ex)
            Dialog().ok(self._ADDON.getLocalizedString(30201), ex.args[1])
            succeeded = False
        finally:
            xbmcplugin.endOfDirectory(self._handle, succeeded=succeeded)
