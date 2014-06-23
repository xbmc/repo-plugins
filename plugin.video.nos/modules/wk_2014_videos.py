#/*
# *      Copyright (C) 2014 Erwin Junge
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

try:
  import xbmcplugin
  import xbmcgui
except:
  pass
import urllib2
import urllib
import re
import sys
import json

video_anchor_re = re.compile(r'<a class="link-block".*?</a>', re.S)
video_id_re = re.compile(r'href="/wk2014/video/([0-9]+?)-.*?"', re.S)
thumb_re = re.compile(r'<img.*?src="(.*?)"', re.S)
title_re = re.compile(r'<h3.*>(.*?)</h3>', re.S)
HOSTNAME = 'http://nos.nl'
ROOT = '/wk2014/video'
URL = HOSTNAME + ROOT

def addLink(title, url, thumb):
  liz=xbmcgui.ListItem(title, thumbnailImage=thumb)
  liz.setProperty("IsPlayable", "true")
  xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=liz, isFolder=False)

def video_list():
  html = urllib2.urlopen(URL).read()
  video_anchors = video_anchor_re.findall(html)
  for anchor in video_anchors:
    # Apply regex
    video_id = video_id_re.search(anchor).group(1)
    thumb = thumb_re.search(anchor).group(1)
    title = title_re.search(anchor).group(1)
    # Compute playlist
    playlist_link = 'http://nos.nl/playlist/video/mp4-web03/' + video_id + '.json'
    yield title, thumb, playlist_link

def play_playlist(playlist_link):
  playlist = json.loads(urllib2.urlopen(urllib.unquote(playlist_link)).read())
  videofile = playlist['videofile']
  listitem = xbmcgui.ListItem(path=videofile)
  xbmcplugin.setResolvedUrl(handle=int(sys.argv[1]), succeeded=True, listitem=listitem)

def scan(params):
  for title, thumb, playlist_link in video_list():
    addLink(title, sys.argv[0] + '?module=wk_2014_videos&playlist_link=' + playlist_link, thumb)
  xbmcplugin.endOfDirectory(int(sys.argv[1]))

def run(params): # This is the entrypoint
  print sys.argv
  if 'playlist_link' in params:
    play_playlist(params['playlist_link'])
  else:
    scan(params)

if __name__ == '__main__':
  video_list()
