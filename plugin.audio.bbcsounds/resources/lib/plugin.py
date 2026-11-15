# ------------------------------------------------------------------------------
#  Copyright (c) 2026 Dimitri Kroon.
#  This file is part of plugin.audio.bbcsounds.
#  SPDX-License-Identifier: GPL-3.0-or-later
#  See LICENSE.txt or https://www.gnu.org/licenses/gpl-3.0.txt
# ------------------------------------------------------------------------------

from __future__ import annotations
import os
from urllib.parse import parse_qsl

import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import xbmcvfs

from resources.lib import route
from resources.lib.log import log

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from resources.lib.typedef import ListItemTuple
    from collections.abc import Callable


class Plugin:
    def __init__(self, args: list[str]):
        if len(args) != 4:
            raise RuntimeError('Invalid commandline arguments; this addon must be run conform the plugin protocol.')
        full_path = args[0]
        self.protocol, sep, path = full_path.partition('://')
        self.addon_id, sep, self._path = path.partition('/')
        self._handle = int(args[1])
        self._querystring = args[2][1:]
        self._addon = xbmcaddon.Addon(self.addon_id)
        self._kodi_version = None
        self._user_dir = xbmcvfs.translatePath(self._addon.getAddonInfo('profile'))
        os.makedirs(self._user_dir, exist_ok=True)
        self._settings = None
        self._delayed_calls = []
        self.is_resuming = args[3] == 'resume:true'
        self.cache_to_disc = True

    @property
    def settings(self) -> xbmcaddon.Settings:
        """A wrapper to this plugin's settings."""
        s = self._settings
        if s is None:
            self._settings = s = self.addon.getSettings()
        return s

    @property
    def addon(self) -> xbmcaddon.Addon:
        """An instance of this plugin's xbmcaddon.Addon."""
        return self._addon

    @property
    def user_dir(self) -> str:
        """Full path to the folder containing this plugin’s user data."""
        return self._user_dir

    @property
    def kodi_version(self):
        if self._kodi_version is None:
            from resources.lib.kodi_utils import kodi_version
            self._kodi_version = kodi_version()
        return self._kodi_version

    def run(self):
        """Run the addon.

        Execute the callback function for the current route and pass the possible result
        to Kodi, depending on the type of callback.

        """
        callb, callb_type, params = route.route(self._path, self._querystring)

        xbmcplugin.setContent(self._handle, 'episodes')

        if callb_type == route.CONTENT:
            slug = params.get('slug')
            if slug:
                xbmcplugin.setPluginCategory(self._handle, slug)

            xbmcplugin.addSortMethod(self._handle, xbmcplugin.SORT_METHOD_UNSORTED)
            xbmcplugin.addSortMethod(self._handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
            success = False
            items = callb(self, **params)
            validate = self._validate_item
            if items:
                valid_items = [validate(item) for item in items if item]
                xbmcplugin.addDirectoryItems(self._handle, valid_items, totalItems=len(valid_items))
                success = True
            xbmcplugin.endOfDirectory(self._handle, succeeded=success, cacheToDisc=self.cache_to_disc)

        elif callb_type == route.RESOLVER:
            li = callb(self, **params)
            if li:
                xbmcplugin.setResolvedUrl(self._handle, True, li)
            else:
                # Prevent the next item from playing when setting "Play next song automatically" is enabled
                # in Kodi's player settings.
                xbmc.PlayList(xbmc.PLAYLIST_MUSIC).clear()
                xbmcplugin.setResolvedUrl(self._handle, False, xbmcgui.ListItem())

        elif callb_type == route.SCRIPT:
            callb(self, **params)

        else:
            # We should never get here.
            raise RuntimeError(f'Invalid callback type: "{callb_type}".')

        self.execute_delayed()

    @staticmethod
    def _validate_item(content_item: ListItemTuple) -> ListItemTuple:
        li = content_item[1]
        info = li.getVideoInfoTag()
        # Ensure a title is set to support wall views.
        if not info.getTitle():
            info.setTitle(li.getLabel())
        return content_item

    def translate(self, str_id: int) -> str:
        return self._addon.getLocalizedString(str_id)

    t_ = translate

    def set_sort_methods(self, sort_methods: set | None = None):
        handle = self._handle
        xbmcplugin.addSortMethod(handle, xbmcplugin.SORT_METHOD_UNSORTED)
        xbmcplugin.addSortMethod(handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
        if sort_methods:
            for method in sort_methods:
                xbmcplugin.addSortMethod(handle, method)

    def next_page(self) -> ListItemTuple | None:
        """Create a (path, ListItem, isFolder) tuple for the next page of the current listing."""
        kwargs = dict(parse_qsl(self._querystring))
        cur_page = kwargs.get('page', 1)
        if not cur_page:
            return None
        kwargs['page'] = str(int(cur_page) + 1)
        li = xbmcgui.ListItem('Next Page')
        info = li.getVideoInfoTag()
        info.setTitle('[B]Next Page[/B]')
        li.setProperty('SpecialSort', 'bottom')
        return route.build_callback(self._path, **kwargs), li, True

    def register_delayed(self, func: Callable, *args, **kwargs):
        """Register a function to be called after all ListItems have been passed to Kodi"""
        self._delayed_calls.append((func, args, kwargs))

    def execute_delayed(self):
        for func, args, kwargs in self._delayed_calls:
            log('Executing delayed call: %s %s %s', func.__name__, args, kwargs)
            func(*args, **kwargs)
        self._delayed_calls = []
