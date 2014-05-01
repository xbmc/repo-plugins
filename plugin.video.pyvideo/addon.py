# -*- coding: utf-8 -*-
# Copyright 2012 Jörn Schumacher
# Copyright 2014 Benjamin Bertrand
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

from xbmcswift2 import xbmc
import resources.lib.pyvideo as pyvideo
from config import plugin


strings = {'Categories': plugin.get_string(30001),
           'Latest videos': plugin.get_string(30002),
           'Search': plugin.get_string(30003),
           }


@plugin.route('/')
def index():
    items = [
            {'label': strings['Categories'],
             'path': plugin.url_for('show_categories')},
            {'label': strings['Latest videos'],
             'path': plugin.url_for('show_latest')},
            {'label': strings['Search'],
             'path': plugin.url_for('search')},
            ]
    return items


@plugin.route('/categories')
def show_categories():
    categories = pyvideo.get_categories()
    items = [{'label': category['title'],
              'path': plugin.url_for('show_category', url=category['url']),
              } for category in categories]
    return items


@plugin.route('/category/<url>')
def show_category(url):
    videos = pyvideo.get_category_videos(url)
    return list_videos(videos)


@plugin.route('/latest')
def show_latest():
    videos = pyvideo.get_latest()
    return list_videos(videos)


@plugin.route('/search')
def search():
    # Pagination doesn't seem to work for search results
    # Display only the first page of search results
    keyboard = xbmc.Keyboard('', 'Search')
    keyboard.doModal()
    if keyboard.isConfirmed() and keyboard.getText():
        text = keyboard.getText().replace(" ", "+")
        videos = pyvideo.search(text)
        return list_videos(videos)


def list_videos(videos):
    items = [
        {'label': item['title'],
         'path': plugin.url_for('play_video', video_id=item['id']),
         'thumbnail': item.get('thumbnail'),
         'is_playable': True,
         } for item in videos]
    return items


@plugin.route('/play/<video_id>')
def play_video(video_id):
    url = pyvideo.get_video_url(video_id)
    return plugin.set_resolved_url(url)


if __name__ == '__main__':
    plugin.run()
