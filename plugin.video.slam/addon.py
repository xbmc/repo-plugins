#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#     Copyright (C) 2016 Jester
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
def show_slam_list():
    items = [

  {'label': 'SLAM! TV Stream',
   'thumbnail': 'special://home/addons/plugin.video.slam/icon.png',
   'path': 'http://hls2.slamfm.nl/content/slamtv/slamtv_1.m3u8',
   'is_playable': True,
  },
  
  {'label': 'SLAM! Webcam Live Stream',
   'thumbnail': 'special://home/addons/plugin.video.slam/icon.png',
   'path': 'http://hls2.slamfm.nl/content/slamwebcam/slamwebcam_1.m3u8',
   'is_playable': True,
  },
]
    return plugin.finish(items)

def log(text):
    plugin.log.info(text)

if __name__ == '__main__':
    plugin.run()