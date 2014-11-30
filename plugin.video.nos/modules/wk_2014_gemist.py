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
from urlparse import urlparse, parse_qs

match_re = re.compile(r'<li class="match-row.*?</li>', re.S)
match_left_team_re = re.compile(r'<span class="team">.*?<span class="show-large-up".*?>(.*?)</span>', re.S)
match_right_team_re = re.compile(r'<span class="opponent team.*?">.*?<span class="show-large-up".*?>(.*?)</span>', re.S)
match_link_re = re.compile(r'<a href="(.*?)"', re.S)
match_date_re = re.compile(r'<span class="date">(.*?)</span>', re.S)
match_time_re = re.compile(r'<span class="time">(.*?)</span>', re.S)
json_re = re.compile(r'DATA = ({.*?})(?:[^}]|\n)*?</script>', re.S)
vod_re = re.compile(r'<ul.*?data-js="playlist-vod">.*?</ul>', re.S)
id_re = re.compile(r'.*?id=([^&"]*?).*?', re.S)
HOSTNAME = 'http://nos.nl'
ROOT = '/wk2014/gemist'
URL = HOSTNAME + ROOT

playlist_location_map = {
  'v': HOSTNAME + '/playlist/video/mp4-web03/{video_id}.json',
  'b2': HOSTNAME + '/playlist/uitzending/mp4-web03/{video_id}.json',
}

def addDir(name, url):
  liz=xbmcgui.ListItem(name)
  xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=liz,isFolder=True)

def addLink(title, url, thumb):
  liz=xbmcgui.ListItem(title, thumbnailImage=thumb)
  liz.setProperty("IsPlayable", "true")
  xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=liz, isFolder=False)

def match_list():
  html = urllib2.urlopen(URL).read()
  match_objects = match_re.findall(html)
  for match_object in match_objects:
    left_team = match_left_team_re.search(match_object).group(1)
    right_team = match_right_team_re.search(match_object).group(1)
    link = HOSTNAME + match_link_re.search(match_object).group(1)
    date = match_date_re.search(match_object).group(1)
    time = match_time_re.search(match_object).group(1)
    yield left_team, right_team, date, time, link

def video_list(url):
  html = urllib2.urlopen(url).read()
  json_data = json_re.search(html).group(1)
  data = json.loads(json_data)
  broadcasts = data['broadcast']
  videos = data['video']
  for broadcast in broadcasts + videos:
    title = broadcast['title']
    video_type, video_id = parse_qs(urlparse(broadcast['url']).query)[u'id'][0].split(':')
    playlist_link = playlist_location_map[video_type].format(video_id=video_id)
    thumb = broadcast['posterframe']
    yield title, playlist_link, thumb

def play_playlist(playlist_link):
  playlist = json.loads(urllib2.urlopen(urllib.unquote(playlist_link)).read())
  videofile = playlist['videofile']
  listitem = xbmcgui.ListItem(path=videofile)
  xbmcplugin.setResolvedUrl(handle=int(sys.argv[1]), succeeded=True, listitem=listitem)

def scan(params):
  for left_team, right_team, date, time, link in match_list():
    title = date + ', ' + time + ' ' + left_team + ' - ' + right_team
    addDir(title, sys.argv[0] + '?module=wk_2014_gemist&match_link=' + link)
  xbmcplugin.endOfDirectory(int(sys.argv[1]))

def scan_match(params):
  url = urllib.unquote(params['match_link'])
  for title, playlist_link, thumb in video_list(url):
    addLink(title, sys.argv[0] + '?module=wk_2014_gemist&playlist_link=' + playlist_link, thumb)
  xbmcplugin.endOfDirectory(int(sys.argv[1]))

def run(params): # This is the entrypoint
  if 'playlist_link' in params:
    play_playlist(params['playlist_link'])
  elif 'match_link' in params:
    scan_match(params)
  else:
    scan(params)

if __name__ == '__main__':
  match_list()
