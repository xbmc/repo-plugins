#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#     Copyright (C) 2015 Jester
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

plugin = Plugin()

@plugin.route('/')
def show_tmos_list():
    items = [

  {'label': 'TMOS Episodes',
   'thumbnail': 'special://home/addons/plugin.video.tmos/icon.png',
   'path': 'plugin://plugin.video.youtube/channel/UCtO6jOECGV2FQHj4RGOXyDA/?page=1',
  },

  {'label': 'TMOS Live Ustream (Mon. through Fri. 09:00am EST)',
   'thumbnail': 'special://home/addons/plugin.video.tmos/icon.png',
   'path': 'http://iphone-streaming.ustream.tv/uhls/4443605/streams/live/iphone/playlist.m3u8',
   'is_playable': True,
  },
]
    return plugin.finish(items)

def log(text):
    plugin.log.info(text)

if __name__ == '__main__':
    plugin.run()