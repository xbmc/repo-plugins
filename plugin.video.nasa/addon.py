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

from xbmcswift2 import Plugin


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
        'stream_url': ('http://nasatv-lh.akamaihd.net/i/'
                       'NASA_101@319270/master.m3u8'),
    }, {
        'title': 'ISS Live Stream',
        'logo': 'iss.jpg',
        'stream_url': ('http://iphone-streaming.ustream.tv/ustreamVideo/'
                       '9408562/streams/live/playlist.m3u8'),
    }, {
        'title': 'Educational Channel HD',
        'logo': 'edu.jpg',
        'stream_url': ('http://nasatv-lh.akamaihd.net/i/'
                       'NASA_102@319272/master.m3u8'),
    }, {
        'title': 'Media Channel HD',
        'logo': 'media.jpg',
        'stream_url': ('http://nasatv-lh.akamaihd.net/i/'
                       'NASA_103@319271/master.m3u8'),
    },{
        'title': 'ISS HD Earth Viewing - ustream',
        'logo': 'isshd.jpg',
        'stream_url': ('http://iphone-streaming.ustream.tv/uhls/'
                       '17074538/streams/live/iphone/playlist.m3u8'),
    },{
        'title': 'ISS HD Earth Viewing - urthecast HD',
        'logo': 'isshd.jpg',
        'stream_url': ('http://d2ai41bknpka2u.cloudfront.net/live/'
                       'iss.stream_source/playlist.m3u8'),
    },
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

YOUTUBE_URL ='plugin://plugin.video.youtube/channel/%s/?page=1'

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
        'path': YOUTUBE_URL % channel['channel_id'],
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
