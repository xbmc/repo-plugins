#/*
# *      Copyright (C) 2010 Arne Morten Kvarving
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

import urllib,urllib2,re,xbmcaddon,string,xbmc,xbmcgui,xbmcplugin
from BeautifulSoup import BeautifulSoup as BS

def INDEX():
  req = urllib2.Request('http://www.rbk.no/videos')
  response = urllib2.urlopen(req)
  link=response.read()
  response.close()
  links = string.split(link,'<div class="vodList"')[1].split('<div class="vodItems"')
  del links[0]
  for link in links:
    url = 'http://www.rbk.no'+link.split('<a href="')[1].split('"')[0]
    name = link.split('<a href="')[1].split('>')[1].split('<')[0].strip()
    date = link.split('<div class="vodItemDate">')[1].split('<')[0].strip()
    thumb = 'http://www.rbk.no'+link.split('<img src="')[1].split('"')[0]
    addLink(name,url,thumb,date)

def RESOLVE(url):
  req3 = urllib2.Request(url)
  response = urllib2.urlopen(req3)
  link = response.read()
  response.close()
  url = link.split('.html( "<source src=\'')[1].split("'")[0]
  name = link.split('<h2 class="videoTitle">')[1].split('<')[0]
  plot = link.split('<div class="description">')[1].split('<')[0]
  resolveLink(url,name,plot)

def get_params():
  param=[]
  paramstring=sys.argv[2]
  if len(paramstring)>=2:
    params=sys.argv[2]
    cleanedparams=params.replace('?','')
    if (params[len(params)-1]=='/'):
      params=params[0:len(params)-2]
    pairsofparams=cleanedparams.split('&')
    param={}
    for i in range(len(pairsofparams)):
      splitparams={}
      splitparams=pairsofparams[i].split('=')
      if (len(splitparams))==2:
        param[splitparams[0]]=splitparams[1]
                                
  return param

def addLink(name,url,iconimage,date):
  ok=True
  url2 = sys.argv[0]+"?url="+urllib.quote_plus(url)
  name=str(BS(name,convertEntities=BS.HTML_ENTITIES,fromEncoding='utf-8'))
  liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
  liz.setInfo( type="Video", infoLabels={ "Title": name } )
  liz.setInfo( type="Video", infoLabels={ "Date": date} )
  liz.setProperty("IsPlayable","true");
  ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url2,listitem=liz,isFolder=False)
  return ok

def resolveLink(url,name,plot):
  li=xbmcgui.ListItem(name,
  path = url)
  li.setInfo( type="Video", infoLabels={ "Title": name } )
  li.setInfo( type="Video", infoLabels={ "Plot": plot} )
  xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, li)
  return True

__settings__ = xbmcaddon.Addon(id='plugin.video.rbk.no')
__language__ = __settings__.getLocalizedString
params=get_params()
try:
  url = urllib.unquote_plus(params["url"])
except:
  url = "";
  pass

if len(url) > 0:
  RESOLVE(url)
else:
  INDEX()
  xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_DATE)
  xbmcplugin.endOfDirectory(int(sys.argv[1]))
