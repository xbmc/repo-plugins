#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#     Copyright (C) 2012 Tristan Fischer (sphere@dersphere.de)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#

import os
from xbmcswift2 import Plugin

plugin = Plugin()

PLAYBACK_ADDON_DICT = {
    0: {
        'addon': 'Youtube',
        'channel_url': 'plugin://plugin.video.youtube/channel/%s/?page=1',
        'video_url': 'plugin://plugin.video.youtube/play/?video_id=%s'
    },
    1: {
        'addon': 'Tubed',
        'channel_url': 'plugin://plugin.video.tubed/?channel_id=%s&mode=channel',
        'video_url': 'plugin://plugin.video.tubed/?mode=play&video_id=%s'
    }
}


STRINGS = {
    'page': 30001,
    'streams': 30100,
    'videos': 30101,
    'vodcasts': 30103,
    'search': 30200,
    'title': 30201
}

STATIC_STREAMS = (
    {
        'title': 'Nasa TV HD',
        'logo': 'public.jpg',
        'fanart': plugin.fanart,
        'stream_url': (PLAYBACK_ADDON_DICT[plugin.get_setting('playbackaddon', int)]['video_url'] % '21X5lGlDOfg'),
    }, {
        'title': 'ISS Live Stream',
        'logo': 'iss.jpg',
        'fanart': plugin.fanart,
        'stream_url': (PLAYBACK_ADDON_DICT[plugin.get_setting('playbackaddon', int)]['video_url'] % 'EEIk7gwjgIM'),
    }, {
        'title': 'Media Channel HD',
        'logo': 'media.jpg',
        'fanart': plugin.fanart,
        'stream_url': (PLAYBACK_ADDON_DICT[plugin.get_setting('playbackaddon', int)]['video_url'] % 'nA9UZF-SZoQ'),
    },{
        'title': 'ISS HD Earth Viewing',
        'logo': 'isshd.jpg',
        'fanart': plugin.fanart,
        'stream_url': (PLAYBACK_ADDON_DICT[plugin.get_setting('playbackaddon', int)]['video_url'] % '2E7l9rZ0cQY'),
    },{
        'title': 'ISS HD Earth From Space',
        'logo': 'isshd.jpg',
        'fanart': plugin.fanart,
        'stream_url': (PLAYBACK_ADDON_DICT[plugin.get_setting('playbackaddon', int)]['video_url'] % 'EEIk7gwjgIM'),
    }
)

YOUTUBE_CHANNELS = (
    {
        'name': 'NASA Main',
        'logo': 'nasa.jpg',
        'channel_id': 'UCLA_DiR1FfKNvjuUpBHmylQ',
        'user': 'NASAtelevision',
    }, {
        'name': 'NASA Goddard',
        'logo': 'goddard.jpg',
        'channel_id': 'UCAY-SMFNfynqz1bdoaV8BeQ',
        'user': 'NASAexplorer',
    }, {
        'name': 'NASA Jet Propulsion Laboratory',
        'logo': 'jpl.jpg',
        'channel_id': 'UCryGec9PdUCLjpJW2mgCuLw',
        'user': 'JPLnews',
    }, {
        'name': 'NASA Kennedy Space Center',
        'logo': 'nasa.jpg',
        'channel_id': 'UCjJtr2fFcUp6yljzJOzpHUg',
        'user': 'NASAKennedy',
    }, {
        'name': 'Hubble Space Telescope',
        'logo': 'hubble.jpg',
        'channel_id': 'UCqvjEkH_41m4DYaoNQwk4Bw',
        'user': 'HubbleSiteChannel',
    },
)

@plugin.route('/')
def show_root_menu():
    items = [
        {'label': _('streams'), 'icon': plugin.icon, 'fanart': plugin.fanart,
         'path': plugin.url_for('show_streams')},
        {'label': _('videos'), 'icon': plugin.icon, 'fanart': plugin.fanart,
         'path': plugin.url_for('show_channels')},
    ]
    return plugin.finish(items)


@plugin.route('/streams/')
def show_streams():
    items = [{
        'label': stream['title'],
        'thumbnail': get_logo(stream['logo']),
        'fanart': stream['fanart'],
        'path': stream['stream_url'],
        'is_playable': True,
        'info': { 'genre': 'Educational', 'title': stream['title'] }
    } for stream in STATIC_STREAMS]
    return plugin.finish(items)


@plugin.route('/channels/')
def show_channels():
    items = [{
        'label': channel['name'],
        'thumbnail': get_logo(channel['logo']),
        'fanart': plugin.fanart,
        'path': PLAYBACK_ADDON_DICT[plugin.get_setting('playbackaddon', int)]['channel_url'] % channel['channel_id'],
    } for channel in YOUTUBE_CHANNELS]
    return plugin.finish(items)


def get_logo(logo):
    addon_id = plugin._addon.getAddonInfo('id')
    return os.path.join(plugin.addon_folder, "resources", "media", logo)


def _(string_id):
    if string_id in STRINGS:
        return plugin.get_string(STRINGS[string_id])
    else:
        plugin.log.warning('String is missing: %s' % string_id)
        return string_id


def log(text):
    plugin.log.info(text)


def run():
    plugin.run()
