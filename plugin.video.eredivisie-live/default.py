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
import sys
import urllib2
from BeautifulSoup import BeautifulSoup, SoupStrainer
import re

base_url = 'http://eredivisielive.nl'

def get_params():
  param={}
  paramstring=sys.argv[2]
  if len(paramstring)>=2:
    params=sys.argv[2]
    cleanedparams=params.replace('?','')
    if (params[len(params)-1]=='/'):
      params=params[0:len(params)-2]
    pairsofparams=cleanedparams.split('&')
    for i in range(len(pairsofparams)):
      splitparams={}
      splitparams=pairsofparams[i].split('=')
      if (len(splitparams))==2:
        param[splitparams[0]]=splitparams[1]
  return param

def addFilterDir(name, filterString):
  u=sys.argv[0]+"?filter="+filterString
  liz=xbmcgui.ListItem(name)
  xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)

def get_filter_list(filter_string):
  results = []
  filter_options = SoupStrainer('div', {'id': "filter-"+filter_string+"-options"})
  soup = BeautifulSoup(urllib2.urlopen(base_url+'/video').read(), parseOnlyThese=filter_options)
  for tag in soup.findAll("a"):
    if tag['href'] != '/video/overzicht/':
      results.append({"name": tag.find("span", {"class": "name"}).text, "location": base_url+tag['href']})
  return results

def addListingDir(item):
  u=sys.argv[0]+"?listing="+item['location']
  liz=xbmcgui.ListItem(item['name'])
  xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)

def get_videos(url):
  results = []
  videos = SoupStrainer('li', {'class': 'video-item'})
  soup = BeautifulSoup(urllib2.urlopen(url).read(), parseOnlyThese=videos)
  for link in soup.findAll('a'):
    if not link.find('span', {'class': 'video-payment-noprice-button'}):
      results.append({"name": link.find('span', {'class': 'title'}).text, "location": base_url+link['href']})
  return results
  
def get_bitrates(url):
  results = []
  bandwidth_re = re.compile(r'BANDWIDTH=([0-9]+)')
  playlist = SoupStrainer('input', {'id':"video-smil"})
  playlist_url = BeautifulSoup(urllib2.urlopen(url).read(), parseOnlyThese=playlist).input['value']
  playlist = urllib2.urlopen(playlist_url).readlines()
  bandwidth_found = False
  for line in playlist:
    bandwidth_temp = bandwidth_re.search(line)
    if bandwidth_temp:
      bandwidth_found = True
      bandwidth = '%i kbps'%(int(bandwidth_temp.group(1))/1000)
    elif bandwidth_found:      
      results.append({"name": bandwidth, "location": line.strip('\n')})
  return results

def addVideoItem(item):
  u=sys.argv[0]+"?item="+item['location']
  liz=xbmcgui.ListItem(item['name'])
  xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=True)

def addVideoLink(item):
  u=item['location']
  liz=xbmcgui.ListItem(item['name'], thumbnailImage=None)
  xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=False)
  
## Begin of main script
params=get_params() # First, get the parameters

if 'filter' in params: # Filter chosen, load items
  if params['filter']:
    items = get_filter_list(params['filter'])
    for item in items:
      addListingDir(item)
  else:
    items = get_videos(base_url+'/video')
    for item in items:
      addVideoItem(item)

elif 'listing' in params: # Listing mode
  items = get_videos(params['listing'])
  for item in items:
    addVideoItem(item)

elif 'item' in params: # Item selected, show bitrate options
  items = get_bitrates(params['item'])
  for item in items:
    addVideoLink(item)
    
else: # First entry, show main listing
  addFilterDir('List all videos', '')
  addFilterDir('Filter by competition', 'competition')
  addFilterDir('Filter by club', 'club')
  addFilterDir('Filter by category', 'category')

xbmcplugin.endOfDirectory(int(sys.argv[1]))
