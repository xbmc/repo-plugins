# Copyright (C) 2018 melmorabity

# This program is free software; you can redistribute it and/or modify it under the terms of the GNU
# General Public License as published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without
# even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.

# You should have received a copy of the GNU General Public License along with this program; if not,
# write to the Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.


import os

import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin

from .francetv_api import FranceTVAPI, FranceTVAPIException

try:
    from urllib import urlencode
    from urlparse import parse_qsl
except ImportError:
    from urllib.parse import parse_qsl, urlencode


class FranceTVAddonNoVideoException(Exception):
    pass


class FranceTVAddon(object):
    _ADDON_ID = 'plugin.video.francetv'

    def __init__(self, addon_base_url, addon_handle, addon_params=None):
        self._addon = xbmcaddon.Addon(id=self._ADDON_ID)

        addon_dir = xbmc.translatePath(self._addon.getAddonInfo('path'))
        resources_dir = os.path.join(addon_dir, 'resources')
        media_dir = os.path.join(resources_dir, 'media')
        fanart = os.path.join(resources_dir, 'fanart.jpg')
        self._fallback_art = {'fanart': fanart}
        self._channel_art = {
            'france-2': {'icon': os.path.join(media_dir, 'france-2.png'), 'fanart': fanart},
            'france-3': {'icon': os.path.join(media_dir, 'france-3.png'), 'fanart': fanart},
            'france-4': {'icon': os.path.join(media_dir, 'france-4.png'), 'fanart': fanart},
            'france-5': {'icon': os.path.join(media_dir, 'france-5.png'), 'fanart': fanart},
            'france-o': {'icon': os.path.join(media_dir, 'france-o.png'), 'fanart': fanart},
            'franceinfo': {'icon': os.path.join(media_dir, 'franceinfo.png'), 'fanart': fanart},
            'slash': {'icon': os.path.join(media_dir, 'slash.png'), 'fanart': fanart}
        }

        self._max_videos_per_page = (int(self._addon.getSetting('max_videos_per_page')) + 1) * 10
        self._enable_subtitles = self._addon.getSetting('enable_subtitles') == 'true'

        self._api = FranceTVAPI()

        self._addon_base_url = addon_base_url
        self._addon_handle = int(addon_handle)
        self._addon_params = self._params_to_dict(addon_params)

    @staticmethod
    def _params_to_dict(params):
        result = {}
        if params:
            # Parameter string starts with a '?'
            result = dict(parse_qsl(params[1:]))

        return result

    def _build_url(self, **query):
        # Remove None values from the query string
        return '{}?{}'.format(
            self._addon_base_url, urlencode(dict((k, v) for k, v in list(query.items()) if v))
        )

    def _add_menu_item(self, item_list, label, url, info=None, art=None, is_folder=True,
                       channel=None):
        item = xbmcgui.ListItem(label)
        item.setInfo('video', info)
        item.setArt(art or self._channel_art.get(channel) or self._fallback_art)
        if not is_folder:
            item.setProperty('isPlayable', 'true')

        item_list.append((url, item, is_folder))

    def _set_directory_sort_methods(self):
        xbmcplugin.addSortMethod(self._addon_handle, xbmcplugin.SORT_METHOD_UNSORTED)
        xbmcplugin.addSortMethod(self._addon_handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)

    def _set_video_sort_methods(self):
        xbmcplugin.addSortMethod(self._addon_handle, xbmcplugin.SORT_METHOD_UNSORTED)
        xbmcplugin.addSortMethod(self._addon_handle, xbmcplugin.SORT_METHOD_DATEADDED)
        xbmcplugin.addSortMethod(self._addon_handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)

    def _show_main_menu(self):
        items = []

        self._add_menu_item(items, self._addon.getLocalizedString(30001),
                            self._build_url(mode='channels'))
        self._add_menu_item(items, self._addon.getLocalizedString(30002),
                            self._build_url(mode='categories'))
        self._add_menu_item(items, self._addon.getLocalizedString(30003),
                            self._build_url(mode='lives'))

        xbmcplugin.addDirectoryItems(self._addon_handle, items=items)

    def _show_channels(self):
        items = []

        for metadata, info, art in self._api.get_channels():
            channel = metadata.get('id')
            self._add_menu_item(items, info.get('title'),
                                self._build_url(mode='categories', channel=channel),
                                info=info, art=art, channel=channel)

        xbmcplugin.addDirectoryItems(self._addon_handle, items=items)
        self._set_directory_sort_methods()

    def _show_categories(self, channel=None):
        items = []

        if channel:
            self._add_menu_item(items, self._addon.getLocalizedString(30005),
                                self._build_url(mode='tv_shows', channel=channel), channel=channel)
            self._add_menu_item(items, self._addon.getLocalizedString(30006),
                                self._build_url(mode='videos', channel=channel), channel=channel)

        for metadata, info, art in self._api.get_categories(channel=channel):
            category = metadata.get('id')
            if channel:
                url = self._build_url(mode='tv_shows', category=category, channel=channel)
            else:
                url = self._build_url(mode='subcategories', category=category)
            self._add_menu_item(items, info.get('title'), url, info=info, art=art, channel=channel)

        xbmcplugin.addDirectoryItems(self._addon_handle, items=items)
        self._set_directory_sort_methods()

    def _show_lives(self):
        xbmcplugin.setContent(self._addon_handle, content='videos')

        items = []

        for metadata, info, art in self._api.get_lives():
            video = metadata.get('video_id')
            channel = metadata.get('channel_id')
            self._add_menu_item(items, info.get('title'), self._build_url(mode='play', video=video),
                                info=info, art=art, is_folder=False, channel=channel)

        xbmcplugin.addDirectoryItems(self._addon_handle, items=items)

    def _show_subcategories(self, category):
        items = []

        self._add_menu_item(items, self._addon.getLocalizedString(30005),
                            self._build_url(mode='tv_shows', category=category))
        self._add_menu_item(items, self._addon.getLocalizedString(30006),
                            self._build_url(mode='videos', category=category))

        for metadata, info, art in self._api.get_subcategories(category):
            subcategory = metadata.get('id')
            self._add_menu_item(items, info.get('title'),
                                self._build_url(mode='tv_shows', category=subcategory), info=info,
                                art=art)

        xbmcplugin.addDirectoryItems(self._addon_handle, items=items)
        self._set_directory_sort_methods()

    def _show_tv_shows(self, channel=None, category=None):
        items = []

        self._add_menu_item(items, self._addon.getLocalizedString(30006),
                            self._build_url(mode='videos', channel=channel, category=category),
                            channel=channel)

        for metadata, info, art in self._api.get_tv_shows(channel=channel, category=category):
            tv_show = metadata.get('id')
            if not channel:
                channel = metadata.get('channel_id')

            self._add_menu_item(
                items, info.get('title'),
                self._build_url(mode='videos', channel=channel, category=category, tv_show=tv_show),
                info=info, art=art, channel=channel
            )

        xbmcplugin.addDirectoryItems(self._addon_handle, items=items)
        self._set_directory_sort_methods()

    def _show_videos(self, channel=None, category=None, tv_show=None, page=0):
        xbmcplugin.setContent(self._addon_handle, content='videos')

        items = []

        data = self._api.get_videos(channel=channel, category=category, tv_show=tv_show,
                                    size=self._max_videos_per_page, page=page)
        for metadata, info, art in data.get('videos', []):
            video = metadata.get('video_id')
            if not channel:
                channel = metadata.get('channel_id')

            self._add_menu_item(items, info.get('title'), self._build_url(mode='play', video=video),
                                info=info, art=art, is_folder=False, channel=channel)

        if data.get('next') or False:
            next_page = int(page) + 1

            self._add_menu_item(
                items,
                '{} ({})'.format(self._addon.getLocalizedString(30004), next_page + 1),
                self._build_url(mode='videos', channel=channel, category=category, tv_show=tv_show,
                                page=next_page)
            )

        xbmcplugin.addDirectoryItems(self._addon_handle, items=items)
        self._set_video_sort_methods()

    def _play(self, video):
        data = self._api.get_video_stream(video, subtitles=self._enable_subtitles)
        video_url = data.get('video')
        if not video_url:
            raise FranceTVAddonNoVideoException()

        item = xbmcgui.ListItem(path=video_url)
        if self._enable_subtitles:
            item.setSubtitles(data.get('subtitles', []))
        xbmcplugin.setResolvedUrl(self._addon_handle, True, item)

    def run(self):
        mode = self._addon_params.get('mode')
        succeeded = True
        try:
            if mode == 'channels':
                self._show_channels()
            elif mode == 'categories':
                self._show_categories(channel=self._addon_params.get('channel'))
            elif mode == 'lives':
                self._show_lives()
            elif mode == 'subcategories':
                self._show_subcategories(self._addon_params.get('category'))
            elif mode == 'tv_shows':
                self._show_tv_shows(channel=self._addon_params.get('channel'),
                                    category=self._addon_params.get('category'))
            elif mode == 'videos':
                self._show_videos(channel=self._addon_params.get('channel'),
                                  category=self._addon_params.get('category'),
                                  tv_show=self._addon_params.get('tv_show'),
                                  page=self._addon_params.get('page', 0))
            elif mode == 'play':
                self._play(self._addon_params.get('video'))
            else:
                self._show_main_menu()
        except FranceTVAPIException:
            xbmcgui.Dialog().ok(self._addon.getLocalizedString(30200),
                                self._addon.getLocalizedString(30201))
            succeeded = False
        except FranceTVAddonNoVideoException:
            xbmcgui.Dialog().ok(self._addon.getLocalizedString(30202),
                                self._addon.getLocalizedString(30203))
            succeeded = False
        finally:
            xbmcplugin.endOfDirectory(self._addon_handle, succeeded=succeeded)
