#/*
# *      Copyright (C) 2012 Erwin Junge
# *
# *
# *  This Program is free software; you can redistribute it and/or modify
# *  it under the terms of the GNU General Public License as published by
# *  the Free Software Foundation; either version 2, or (at your option)
# *  any later version.
# *
# *  This Program is distributed in the hope that it will be useful,
# *  but WITHOUT ANY WARRANTY; without even the implied warranty of
# *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# *  GNU General Public License for more details.
# *
# *  You should have received a copy of the GNU General Public License
# *  along with this program; see the file COPYING.  If not, write to
# *  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
# *  http://www.gnu.org/copyleft/gpl.html
# *
# */

import xbmcplugin
import xbmcgui
import urllib2
import re
import sys
import json
from StringIO import StringIO
import gzip

nos_url = 'http://content.nos.nl/apps/feeds/journaal-app/page/1'
playlist_format = 'http://content.nos.nl/apps/broadcast/{}/format/mp4-web03'
headers = (
    ('X-NOS-App', 'LGE/hammerhead;Android/4.4.3;nl.nos.app/3.1'),
    ('X-NOS-Salt', '1417002425'),
    ('X-NOS-Key', 'a9e3c0bdfc9b4d8eedddfa6df1d01ed2'),
    ('Accept-Encoding', 'gzip'),
    ('Host', 'content.nos.nl'),
    ('User-Agent', 'Apache-HttpClient/UNAVAILABLE (java 1.4)'),
    ('Connection', 'close'),
)

def addLink(title, url, thumb):
  liz=xbmcgui.ListItem(title, thumbnailImage=thumb)
  xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=liz, isFolder=False)

def scan(params):
  request = urllib2.Request(nos_url)
  for header in headers:
    request.add_header(*header)
  response = urllib2.urlopen(request)
  if response.info().get('Content-Encoding') == 'gzip':
    buf = StringIO( response.read())
    f = gzip.GzipFile(fileobj=buf)
    data = f.read()
    stuff = json.loads(data)
    for item in sorted(stuff['broadcasts'], key=lambda item: item['pub_date'], reverse=True):
      playlist_url = playlist_format.format(item['id'])
      playlist_request = urllib2.Request(playlist_url)
      for header in headers:
        playlist_request.add_header(*header)
      playlist_response = urllib2.urlopen(playlist_request)
      if playlist_response.info().get('Content-Encoding') == 'gzip':
        playlist_buf = StringIO(playlist_response.read())
        playlist_f = gzip.GzipFile(fileobj=playlist_buf)
        playlist_data = playlist_f.read()
        playlist_stuff = json.loads(playlist_data)
        title = playlist_stuff['title']
        video_url = playlist_stuff['url']
        img = None
        addLink(title, video_url, img)
  xbmcplugin.endOfDirectory(int(sys.argv[1]))

def run(params): # This is the entrypoint
  scan(params)
