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

from xbmcswift2 import Plugin, xbmc


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
        'stream_url': ('http://public.infozen.cshls.lldns.net/infozen/public/'
                       'public/public_1000.m3u8'),
    }, {
        'title': 'ISS Live Stream',
        'logo': 'iss.jpg',
        'stream_url': ('http://sjc-uhls-proxy.ustream.tv/watch/'
                       'playlist.m3u8?cid=9408562'),
    }, {
        'title': 'Educational Channel HD',
        'logo': 'edu.jpg',
        'stream_url': ('http://edu.infozen.cshls.lldns.net/infozen/edu/'
                       'edu/edu_1000.m3u8'),
    }, {
        'title': 'Media Channel HD',
        'logo': 'media.jpg',
        'stream_url': ('http://media.infozen.cshls.lldns.net/infozen/media/'
                       'media/media_1000.m3u8'),
    },
)

YOUTUBE_CHANNELS = (
    {
        'name': 'NASA Main',
        'logo': 'nasa.jpg',
        'user': 'NASAtelevision',
    }, {
        'name': 'NASA Goddard',
        'logo': 'goddard.jpg',
        'user': 'NASAexplorer',
    }, {
        'name': 'NASA Jet Propulsion Laboratory',
        'logo': 'jpl.jpg',
        'user': 'JPLnews',
    }, {
        'name': 'NASA Kennedy Space Center',
        'logo': 'nasa.jpg',
        'user': 'NASAKennedy',
    }, {
        'name': 'Hubble Space Telescope',
        'logo': 'hubble.jpg',
        'user': 'HubbleSiteChannel',
    },
)

YOUTUBE_URL = (
    'plugin://plugin.video.youtube/?'
    'path=/root&feed=uploads&channel=%s'
)

plugin = Plugin()


@plugin.route('/')
def show_root_menu():
    items = [
        {'label': _('streams'),
         'path': plugin.url_for('show_streams')},
        {'label': _('videos'),
         'path': plugin.url_for('show_channels')},
    ]
    return plugin.finish(items)


@plugin.route('/streams/')
def show_streams():
    items = [{
        'label': stream['title'],
        'thumbnail': get_logo(stream['logo']),
        'path': stream['stream_url'],
        'is_playable': True,
    } for stream in STATIC_STREAMS]
    return plugin.finish(items)


@plugin.route('/channels/')
def show_channels():
    items = [{
        'label': channel['name'],
        'thumbnail': get_logo(channel['logo']),
        'path': YOUTUBE_URL % channel['user'],
    } for channel in YOUTUBE_CHANNELS]
    return plugin.finish(items)

def get_logo(logo):
    addon_id = plugin._addon.getAddonInfo('id')
    return 'special://home/addons/%s/resources/media/%s' % (addon_id, logo)


def _(string_id):
    if string_id in STRINGS:
        return plugin.get_string(STRINGS[string_id])
    else:
        plugin.log.warning('String is missing: %s' % string_id)
        return string_id


def log(text):
    plugin.log.info(text)

if __name__ == '__main__':
    plugin.run()
