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
  #~ liz.setProperty("IsPlayable","true")
  xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=liz, isFolder=False)

def scan(params):
  module = params['module']

  URL = 'http://feeds.nos.nl/vodcast_jeugdjournaal'
  items = SoupStrainer('item')
  for tag in BeautifulStoneSoup(urllib2.urlopen(URL).read(), parseOnlyThese=items):
    title = tag.title.contents[0]
    url = tag.guid.contents[0]
    addLink(title, url, '')
  xbmcplugin.endOfDirectory(int(sys.argv[1]))

def run(params): # This is the entrypoint
  scan(params) # Correct url is directly in rss feed, so no switch needed
