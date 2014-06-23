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

link_re = re.compile(r'<a href="video.*?</a>', re.S)
video_re = re.compile(r'nos\.nl/embed/\?id=b2:([0-9]+)')
title_re = re.compile(r'<h3>(.*?)</h3>')
meta_re = re.compile(r'<p class="video-meta">(?:<span.*?</span>)?(.*?)</p>')
img_re = re.compile(r'<img src="(.*?)"')
playlist_format = 'http://nos.nl/playlist/uitzending/mp4-web03/{0:d}.json'

def addLink(title, url, thumb):
  liz=xbmcgui.ListItem(title, thumbnailImage=thumb)
  xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=liz, isFolder=False)

def scan(params):
  URL='http://tv.nos.nl'
  html=urllib2.urlopen(URL).read()
  for (a, video_url) in zip(link_re.findall(html), video_re.findall(html)):
    a = a.replace('\n', '')
    title = title_re.search(a).group(1).strip()
    meta = ', '.join([meta_part.strip() for meta_part in re.sub(r'\s+', ' ', meta_re.search(a).group(1)).split('<br />')])
    img = URL + '/browser/' + img_re.search(a).group(1).strip()
    title = title + ' - ' + meta
    playlist_url = playlist_format.format(int(video_url))
    playlist = json.loads(urllib2.urlopen(playlist_url).read())
    video_url = playlist['videofile']
    addLink(title, video_url, img)
  xbmcplugin.endOfDirectory(int(sys.argv[1]))

def run(params): # This is the entrypoint
  scan(params)