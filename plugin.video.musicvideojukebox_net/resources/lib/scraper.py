#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#     Copyright (C) 2013 Tristan Fischer
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

from urllib2 import urlopen, Request, HTTPError, URLError
from BeautifulSoup import BeautifulSoup

MAIN_URL = 'http://www.musicvideojukebox.net/'


class NetworkError(Exception):
    pass


def get_videos():
    req = Request(MAIN_URL + 'media.xml')
    try:
        response = urlopen(req).read()
    except HTTPError, error:
        raise NetworkError(error)
    except URLError, error:
        raise NetworkError(error)
    items = [{
        'interpret': item.infotitle.text[11:-12],
        'title': item.infodesc.text[10:-11],
        'video_url': MAIN_URL + item.url.get('value'),
        'thumb': MAIN_URL + item.startimage.get('value')
    } for item in BeautifulSoup(response).findAll('item')]
    return items
