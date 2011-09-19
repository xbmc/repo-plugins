#/*
# *      Copyright (C) 2011 Erwin Junge
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
import urllib
import urllib2
import re
from BeautifulSoup import BeautifulStoneSoup, SoupStrainer
import sys

def addLink(title, url, thumb):
  liz=xbmcgui.ListItem(title, thumbnailImage=thumb)
  liz.setProperty("IsPlayable","true")
  xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=liz, isFolder=False)

def scan(params):
  module = params['module']

  URL = 'http://feeds.nos.nl/nos-nieuwsin60seconden'
  items = SoupStrainer('item')
  for tag in BeautifulStoneSoup(urllib2.urlopen(URL).read(), parseOnlyThese=items):
    time = re.search(r'\(.*?\)', tag.title.contents[0]).group(0)
    title = tag.description.contents[0] + ' ' + time
    url = tag.link.contents[0]
    url = urllib.quote_plus(url)
    url = sys.argv[0]+"?module="+module+"&url="+url
    addLink(title, url, '')
  xbmcplugin.endOfDirectory(int(sys.argv[1]))

def find_video(url):
  page=urllib2.urlopen(url).read()
  xml=re.search(r'http://content.nos.nl/content/playlist/video/fragment/.*?\.(flv|mp4)',page).group(0)
  return xml

def play(url):
  url = urllib.unquote_plus(url)
  resolved_url = find_video(url)
  li=xbmcgui.ListItem(path = resolved_url)
  xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, li)

def run(params): # This is the entrypoint
  if 'url' in params: # url set, so play the url
    url = params['url']
    play(url)
  else: # no url set, scan for urls
    scan(params)
