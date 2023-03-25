# -*- coding: utf-8 -*-
#
# Copyright (C) 2010-2016 Thomas Amland
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

import os
import re
import xbmc
import xbmcvfs    # ^zZz^  https://github.com/xbmc/xbmc/pull/19301
import requests
from io import StringIO


def get_subtitles(video_id):
    mediaelement_json = requests.get("https://psapi.nrk.no/playback/manifest/%s" % (video_id)).json()

    if not mediaelement_json["playable"]['subtitles']:
        return None
    ttml_sub_url = mediaelement_json["playable"]['subtitles'][0]['webVtt']
    subs = requests.get(ttml_sub_url).text
    if not subs:
        return None

    content = _vtt_to_srt(subs)
    filename = os.path.join(xbmcvfs.translatePath("special://temp"), 'nor.srt')  # ^zZz^  https://github.com/xbmc/xbmc/pull/19301
    # filename = os.path.join(xbmc.translatePath("special://temp"), 'nor.srt')  # ^zZz^  https://github.com/xbmc/xbmc/pull/19301
    with open(filename, 'w' ,encoding='utf8') as f:
        f.write(content)
    return filename


def _vtt_to_srt(content):
    return content

def _str_to_time(txt):
    p = txt.split(':')
    try:
        ms = float(p[2])
    except ValueError:
        ms = 0
    return int(p[0]) * 3600 + int(p[1]) * 60 + ms


def _time_to_str(time):
    return '%02d:%02d:%02d,%03d' % (time / 3600, (time % 3600) / 60, time % 60, (time % 1) * 1000)
