# -*- coding: utf-8 -*-
#
# Copyright (C) 2012 Benjamin Bertrand
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301,
# USA.
# http://www.gnu.org/copyleft/gpl.html

import os
from config import plugin
from xbmcswift2 import SortMethod
import resources.lib.catalog as catalog

CHANNELS = ('all', 'M6', 'W9')
SHOW_BY = ('genre', 'clips')
MEDIA_PATH = os.path.join(plugin.addon.getAddonInfo('path'), 'resources', 'media')


@plugin.route('/')
def index():
    channels = CHANNELS[int(plugin.get_setting('channels'))]
    if channels == 'all':
        items = [{'label': 'M6Replay',
                  'path': plugin.url_for('show_channel', channel='M6'),
                  'thumbnail': os.path.join(MEDIA_PATH, 'm6.png')},
                {'label': 'W9Replay',
                 'path': plugin.url_for('show_channel', channel='W9'),
                 'thumbnail': os.path.join(MEDIA_PATH, 'w9.png')}]
        return items
    else:
        return show_channel(channels)


@plugin.route('/channel/<channel>')
def show_channel(channel):
    show_by = SHOW_BY[int(plugin.get_setting('show_by'))]
    if show_by == 'genre':
        return show_genres(channel)
    else:
        return show_clips(channel, 'all')


@plugin.route('/genres/<channel>')
def show_genres(channel):
    genres = catalog.get_genres(channel)
    items = [{'label': gnr['label'],
              'path': plugin.url_for('show_programs', channel=channel, genre=gnr['id'])
             } for gnr in genres]
    return plugin.finish(items, sort_methods=[SortMethod.LABEL])


@plugin.route('/programs/<channel>/<genre>')
def show_programs(channel, genre):
    programs = catalog.get_programs(channel, genre)
    items = [{'label': pgm['label'],
              'thumbnail': pgm['thumb'],
              'path': plugin.url_for('show_clips', channel=channel, program=pgm['id'])
             } for pgm in programs]
    return plugin.finish(items, sort_methods=[SortMethod.LABEL])


@plugin.route('/clips/<channel>/<program>')
def show_clips(channel, program):
    clips = catalog.get_clips(channel, program)
    items = [{'label': clp['label'],
              'is_playable': True,
              'thumbnail': clp['thumb'],
              'info': {'date': clp['date'],
                       'duration': clp['duration'],
                       'plot': clp['desc']},
              'path': plugin.url_for('play_clip', channel=channel, clip=clp['id'])
             } for clp in clips]
    if program == 'all':
        return plugin.finish(items, sort_methods=[SortMethod.LABEL, SortMethod.DATE, SortMethod.VIDEO_RUNTIME])
    else:
        return plugin.finish(items, sort_methods=[SortMethod.DATE])


@plugin.route('/play/<channel>/<clip>')
def play_clip(channel, clip):
    url = catalog.get_clip_url(channel, clip)
    plugin.set_resolved_url(url)


if __name__ == '__main__':
    plugin.run()
