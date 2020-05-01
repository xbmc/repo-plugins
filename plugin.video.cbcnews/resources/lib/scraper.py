# -*- coding: utf-8 -*-
# KodiAddon (CBC News)
#
from t1mlib import t1mAddon
import datetime
import json
import re
import urllib
import urllib2
import xbmcplugin
import xbmcgui
import HTMLParser
import sys
import xbmc

h = HTMLParser.HTMLParser()
UTF8 = 'utf-8'

class myAddon(t1mAddon):

 def getAddonMenu(self,url,ilist):
   html  = self.getRequest('http://www.cbc.ca/player')
   shows = re.compile('<h2 class="section-title"[^>]*><a[^>]* href="(.+?)">(.+?)</a>', re.DOTALL).findall(html)
   shows.append(('/player/news/TV%20Shows/MarketPlace', self.addon.getLocalizedString(30001)))
   shows.append(('/player/news/TV%20Shows/Power%20&%20Politics', self.addon.getLocalizedString(30003)))
   shows.append(('/player/news/TV%20Shows/The%20Fifth%20Estate', self.addon.getLocalizedString(30004)))
   shows.append(('/player/news/TV%20Shows/The%20National/Latest%20Broadcast', self.addon.getLocalizedString(30005)))
   shows.append(('/player/news/TV%20Shows/The%20Weekly', self.addon.getLocalizedString(30006)))
   for url, name in shows:
      infoList = {}
      infoList['mediatype'] = 'tvshow'
      infoList['Title'] = name
      infoList['TVShowTitle'] = name
      ilist = self.addMenuItem(name, 'GS', ilist, url, self.addonIcon, self.addonFanart, infoList, isFolder=True)
   return(ilist)

 def getAddonCats(self,url,ilist):
   html  = self.getRequest('http://www.cbc.ca')
   html  = re.compile('<!-- -->My Local Settings(.+?)href="/news">Top Stories', re.DOTALL).search(html).group(1)
   shows = re.compile('<li class="regionsListItem"><.+?data-path="(.+?)".+?value="(.+?)".+?</li>', re.DOTALL).findall(html)
   for url, name in shows:
       infoList = {}
       infoList['mediatype'] = 'tvshow'
       infoList['Title'] = name
       infoList['TVShowTitle'] = name
       lurl = "/player/"+url
       # Manual fixes for multi-word locations
       if lurl == '/player/news/canada/british-columbia':
          lurl = '/player/news/canada/bc'
       if lurl == '/player/news/canada/thunder-bay':
          lurl = '/player/news/canada/thunder%20bay'
       if lurl == '/player/news/canada/new-brunswick':
          lurl = '/player/news/canada/nb'
       if lurl == '/player/news/canada/prince-edward-island':
          lurl = '/player/news/canada/pei'
       if lurl == '/player/news/canada/nova-scotia':
          lurl = '/player/news/canada/ns'
       if lurl == '/player/news/canada/newfoundland-labrador':
          lurl = '/player/news/canada/nl'
       ilist = self.addMenuItem(name, 'GE', ilist, lurl, self.addonIcon, self.addonFanart, infoList, isFolder=True)
       if lurl == '/player/news/canada/toronto':
          ilist = self.addMenuItem('Ottawa', 'GE', ilist, '/player/news/canada/ottawa', self.addonIcon, self.addonFanart, infoList, isFolder=True)
   return(ilist)

 def getAddonShows(self,url,ilist):
   html  = self.getRequest('http://www.cbc.ca%s' % url)
   shows = re.compile('<h2 class="section-title"[^>]*><a[^>]* href="(.+?)">(.+?)</a>', re.DOTALL).findall(html)
   count = 0
   for lurl, name in shows:
       count+=1
   if (count <= 0) or (url.find('TV%20Shows') > 0):
       self.getAddonEpisodes(url, ilist)
   else:
       for lurl, name in shows:
           infoList = {}
           infoList['mediatype'] = 'tvshow'
           infoList['Title'] = name
           infoList['TVShowTitle'] = name
           if lurl == '/player/news/canada':
              ilist = self.addMenuItem(name, 'GC', ilist, lurl, self.addonIcon, self.addonFanart, infoList, isFolder=True)
           else:
              ilist = self.addMenuItem(name, 'GS', ilist, lurl, self.addonIcon, self.addonFanart, infoList, isFolder=True)
   return(ilist)

 def getAddonEpisodes(self,url,ilist):
   self.defaultVidStream['width']  = 1280
   self.defaultVidStream['height'] = 720
   cat = re.compile('/([^/]+?)$', re.DOTALL).search(url).group(1).replace('%20', ' ')
   html = self.getRequest('http://www.cbc.ca%s' % url)
   html = re.compile('window.__INITIAL_STATE__ = (.+?);</script>', re.DOTALL).search(html).group(1)
   a = json.loads(html)
   # Locate exact category name
   for b in a['video']['clipsByCategory']:
       if re.search(cat+"$", b, re.IGNORECASE):  # category must be at end of string
          idxcat = b
   for b in a['video']['clipsByCategory'][idxcat]['items']:
      name = b['title'].replace(u"\u2018", "'").replace(u"\u2019", "'").encode('ascii', 'xmlcharrefreplace')
      plot = b['description'].replace(u"\u2018", "'").replace(u"\u2019", "'").encode('ascii', 'xmlcharrefreplace')
      vurl = str(b['id'])  # mediaID
      thumb = b['thumbnail']
      fanart = thumb
      if b['captions']:
         captions = b['captions']['src']
      else:
         captions = 'N0NE'
      vurl = str(vurl)+'|'+str(captions)
      infoList = {}
      infoList['mediatype'] = 'tvshow'
      infoList['Title'] = name
      infoList['TVShowTitle'] = name
      infoList['Plot'] = plot
      infoList['Duration'] = b['duration']
      infoList['Aired'] = datetime.datetime.fromtimestamp(b['airDate']/1000).strftime('%Y-%m-%d')
      ilist = self.addMenuItem(name, 'GV', ilist, vurl, thumb, fanart, infoList, isFolder=False)
   return(ilist)

 def getAddonVideo(self,url):
      url = url.split('|',1)
      captions = url[1]
      url = url[0]
      u = 'https://link.theplatform.com/s/ExhSPC/media/guid/2655402169/' + url
      u = u + '/meta.smil'
      u = u + '?mbr=true&manifest=m3u&feed=Player%20Selector%20-%20Prod'
      html = self.getRequest(u)
      u = re.compile('RESOLUTION=1280x720.+?\n(http.+?)\?', re.DOTALL).search(html).group(1)
      if u is None:
           return
      liz = xbmcgui.ListItem(path = u.strip())
      if captions != 'N0NE':
          liz.setSubtitles([captions])
      xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)
