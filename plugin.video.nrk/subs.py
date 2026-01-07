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
import xbmcvfs    # 4.8.0  https://github.com/xbmc/xbmc/pull/19301
import requests
from io import StringIO


def get_subtitles(video_id):
    mediaelement_json = requests.get("https://psapi.nrk.no/mediaelement/%s" % (video_id),
        headers={
            "Referer": "https://tv.nrk.no",
            "Accept": "application/vnd.nrk.psapi+json; version=9; ludo-client=true; psapi=snapshot"
        }).json()
    if not mediaelement_json['playable']['parts']:
        return None
    subtitles = mediaelement_json['playable']['parts'][0].get('subtitles', None)
    if not subtitles:
        return None
    subs = {}
    for sub in subtitles:
        subs[sub['type']] = sub['webVtt']
    if mediaelement_json['streamingMode'] != "onDemand":
        return subs
    for sub_type in subs.keys():
        vtt_sub_url = subs[sub_type]
        content = requests.get(vtt_sub_url).text
        if not content:
            continue
        filename = "nor.sdh.vtt" if sub_type == 'ttv' else "%s.vtt" % sub_type
        try:
            filename = os.path.join(xbmcvfs.translatePath("special://temp"), filename)  # 4.8.0 https://github.com/xbmc/xbmc/pull/19301
        except:
            filename = os.path.join(xbmc.translatePath("special://temp"), filename)  # deprecated already in Kodi v19
        with open(filename, 'w' ,encoding='utf8') as f:
            f.write(content)
        subs[sub_type] = filename
    return subs


