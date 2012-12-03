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
import xbmcaddon
import sys
import urllib2
import urllib
import re

link_re = re.compile(r'<a.*?/a>', re.S)
href_re = re.compile(r'href="(.*?)"')
title_re = re.compile(r'title="(.*?)"')
name_re = re.compile(r'<span class="name">(.*?)</span>')
bandwidth_re = re.compile(r'BANDWIDTH=([0-9]+)')
playlist_re = re.compile(r'id="video-smil" value="(.*?)"')

base_url = 'http://eredivisielive.nl'

number_of_items = 100

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
  u=sys.argv[0]+"?module="+filterString
  liz=xbmcgui.ListItem(name)
  xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)

def get_filter_list(filter_string):
  results = []
  filter_re = re.compile(r'<div id="filter-'+filter_string+'-options".*?</div>', re.S)
  links = link_re.findall(filter_re.search(urllib2.urlopen(base_url+'/video').read()).group(0))
  for link in links:
    location = href_re.search(link).group(1)
    if location != '/video/overzicht/':
      results.append({"name": name_re.search(link).group(1), "location": base_url+location})
  return results

def addListingDir(item):
  u=sys.argv[0]+"?listing="+item['location']
  liz=xbmcgui.ListItem(item['name'])
  xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)

def get_videos(links):
  results = [{"name": title_re.search(string).group(1), "location": base_url+href_re.search(string).group(1)} for string in links if 'video-play-button' in string]
  return results

def get_bitrates(url):
  results = []
  playlist_url = playlist_re.search(urllib2.urlopen(urllib.unquote(url)).read()).group(1)
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
  liz=xbmcgui.ListItem(item['name'])
  xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=False)

def get_next_page(links):
  result = {"name": __language__(30004)}
  for string in links:
    if 'class="forward active"' in string:
      result['location'] = base_url+href_re.search(string).group(1)
      return result

def listVideoItems(url):
  next_page={'location': url}
  items=[]
  while next_page and len(items)<number_of_items:
    links = link_re.findall(urllib2.urlopen(urllib.unquote(next_page['location'])).read())
    items += get_videos(links)
    next_page = get_next_page(links)
  for item in items:
    addVideoItem(item)
  addListingDir(next_page)

## Begin of main script
__settings__ = xbmcaddon.Addon(id='plugin.video.eredivisie-live')
__language__ = __settings__.getLocalizedString
params=get_params() # First, get the parameters

if 'module' in params: # Filter chosen, load items
  if params['module'] == 'all':
    listVideoItems(base_url+'/video')
  else:
    items = get_filter_list(params['module'])
    for item in items:
      addListingDir(item)

elif 'listing' in params: # Listing mode
  listVideoItems(params['listing'])

elif 'item' in params: # Item selected, show bitrate options
  items = get_bitrates(params['item'])
  for item in items:
    addVideoLink(item)

else: # First entry, show main listing
  addFilterDir(__language__(30000), 'all')
  addFilterDir(__language__(30001), 'competition')
  addFilterDir(__language__(30002), 'club')
  addFilterDir(__language__(30003), 'category')

xbmcplugin.endOfDirectory(int(sys.argv[1]))
