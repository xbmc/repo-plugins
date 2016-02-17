# -*- coding: utf-8 -*-
# Popcornflix Kodi Video Addon
#
from t1mlib import t1mAddon
import json
import re
import os
import datetime
import urllib
import urllib2
import xbmc
import xbmcplugin
import xbmcgui
import HTMLParser
import sys

h = HTMLParser.HTMLParser()
qp  = urllib.quote_plus
uqp = urllib.unquote_plus
UTF8     = 'utf-8'


class myAddon(t1mAddon):

  def getAddonMenu(self,url,ilist):

    html = self.getRequest('http://www.popcornflix.com')
    m  = re.compile('>Home<(.+?)</ul',re.DOTALL).search(html)
    cats = re.compile('<a href="(.+?)">(.+?)</a>',re.DOTALL).findall(html, m.start(1),m.end(1))
    cats = cats[0:2]
    m = re.compile('Genres(.+?)<div class=',re.DOTALL).search(html)
    c2 = re.compile('<a href="(.+?)">(.+?)</a>',re.DOTALL).findall(html, m.start(1),m.end(1))
    cats.extend(c2)
    for url,name in cats:
       name = '[COLOR blue]'+name+'[/COLOR]'
       ilist = self.addMenuItem(name,'GM', ilist, url, self.addonIcon, self.addonFanart, {} , isFolder=True)
    return(ilist)


  def getAddonEpisodes(self,url,ilist):
    html  = self.getRequest('http://www.popcornflix.com%s' % (url))
    m = re.compile('<div class="b-videos panes floated">(.+?)</ul',re.DOTALL).search(html)
    if m != None:
       shows=re.compile('<figure>.+?href="(.+?)".+?src="(.+?)".+?title">(.+?)<(.+?)genre">(.+?)<.+?desc">(.+?)<.+?</li>',re.DOTALL).findall(html,m.start(1),m.end(1)) 
    else:
       shows=re.compile('<figure>.+?href="(.+?)".+?src="(.+?)".+?title">(.+?)<(.+?)genre">(.+?)<.+?desc">(.+?)<.+?</li>',re.DOTALL).findall(html)
    for url,thumb,name,blob,genre,plot in shows:
         infoList = {} 
         actors, rating, duration = re.compile('actors">(.+?)<.+?rating">(.+?)<.+?duration">(.+?)<',re.DOTALL).search(blob).groups()
         plot = plot.strip()
         infoList['Plot']  = plot.strip()
         infoList['Genre'] = genre
         infoList['Title'] = name
         if   rating == 'R'  : rating = 'Rated R'
         elif rating == 'PG-13' : rating = 'Rated PG-13'
         elif rating == 'PG' : rating = 'Rated PG'
         elif rating == 'G'  : rating = 'Rated G'
         infoList['MPAA']  = rating
         try: infoList['duration'] = int(duration)*60
         except: pass
         infoList['cast'] = actors.split(',')
         url = url.rsplit('/',1)[1]
         ilist = self.addMenuItem(name,'GV', ilist, url, thumb, self.addonFanart, infoList, isFolder=False)
    return(ilist)



  def getAddonMovies(self,url,ilist):
    self.defaultVidStream['width']  = 960
    self.defaultVidStream['height'] = 540
    html  = self.getRequest('http://www.popcornflix.com%s' % (url))
    m = re.compile('<div class="b-videos panes floated">(.+?)</ul',re.DOTALL).search(html)
    if m != None:
       shows=re.compile('<figure>.+?href="(.+?)".+?src="(.+?)".+?title">(.+?)<(.+?)genre">(.+?)<.+?desc">(.+?)<.+?</li>',re.DOTALL).findall(html,m.start(1),m.end(1)) 
    else:
       shows=re.compile('<figure>.+?href="(.+?)".+?src="(.+?)".+?title">(.+?)<(.+?)genre">(.+?)<.+?desc">(.+?)<.+?</li>',re.DOTALL).findall(html)
    for url,thumb,name,blob,genre,plot in shows:
      if (not url.startswith('/series')) and (not url.startswith('/tv-shows')):
         infoList = {} 
         actors, rating, duration = re.compile('actors">(.+?)<.+?rating">(.+?)<.+?duration">(.+?)<',re.DOTALL).search(blob).groups()
         plot = plot.strip()
         infoList['Plot']  = plot.strip()
         infoList['Genre'] = genre
         infoList['Title'] = name
         if   rating == 'R'  : rating = 'Rated R'
         elif rating == 'PG-13' : rating = 'Rated PG-13'
         elif rating == 'PG' : rating = 'Rated PG'
         elif rating == 'G'  : rating = 'Rated G'
         infoList['MPAA']  = rating
         try: infoList['duration'] = int(duration)*60
         except: pass
         infoList['cast'] = actors.split(',')
         url = url.rsplit('/',1)[1]
         ilist = self.addMenuItem(name,'GV', ilist, url, thumb, self.addonFanart, infoList, isFolder=False)
      else:
         name = '[COLOR blue]'+name+'[/COLOR]'
         ilist = self.addMenuItem(name,'GE', ilist, url, thumb, self.addonFanart, {} , isFolder=True)
    return(ilist)




  def getAddonVideo(self,url):
      html = self.getRequest('http://popcornflixv2.device.screenmedia.net/api/videos/%s' % (url))
      a = json.loads(html)
      u = a['movies'][0]['urls']['Web v2 Player']
      liz = xbmcgui.ListItem(path = u)
      xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)

