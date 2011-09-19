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
from BeautifulSoup import BeautifulSoup, SoupStrainer
import sys

def addLink(title, url, thumb):
  liz=xbmcgui.ListItem(title, thumbnailImage=thumb)
  liz.setProperty("IsPlayable","true")
  xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=liz, isFolder=False)

def stringfilter(s):
  return isinstance(s, basestring)

def scan(params):
  module = params['module']

  URL='http://tv.nos.nl'
  links = SoupStrainer('a')
  for tag in BeautifulSoup(urllib2.urlopen(URL).read(), parseOnlyThese=links):
    # Get url
    url_suffix = tag['href']
    url = URL+"/browser/"+url_suffix
    url = urllib.quote_plus(url)
    url = sys.argv[0]+"?module="+module+"&url="+url
    # Get thumbnail image
    thumb_suffix = tag.div.img['src']
    thumb = URL+"/browser/"+thumb_suffix
    # Get title
    title = tag.div.h3.contents[0]
    meta = ', '.join([substring.strip('\n ') for substring in filter(stringfilter, tag.div.p.contents)])
    title = title + ' - ' + meta
    addLink(title, url, thumb)
  xbmcplugin.endOfDirectory(int(sys.argv[1]))

def find_video(url):
  page=urllib2.urlopen(url).read()
  xml=re.search(r'http://content.nos.nl/.*?\.xml',page).group(0)
  xml=urllib2.urlopen(xml).read()
  video_link=re.search(r'http://.*?\.(flv|mp4)',xml).group(0)
  return video_link

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
