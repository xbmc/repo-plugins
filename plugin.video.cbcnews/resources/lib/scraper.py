# -*- coding: utf-8 -*-
# KodiAddon (CBC News)
#
from t1mlib import t1mAddon
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
uqp = urllib.unquote_plus
UTF8 = 'utf-8'

class myAddon(t1mAddon):


 def getAddonMenu(self,url,ilist):
   html  = self.getRequest('http://www.cbc.ca/player/news')
   html = re.compile('<section class="section-cats full">(.+?)</section', re.DOTALL).search(html).group(1)
   shows = re.compile('a href="(.+?)">(.+?)<', re.DOTALL).findall(html)
   shows.append(('/player/news/TV%20Shows/The%20National/Latest%20Broadcast', 'The National / Latest Broadcast'))
   for url, name in shows:
      infoList = {}
      infoList['mediatype'] = 'tvshow'
      infoList['Title'] = name
      infoList['TVShowTitle'] = name
      ilist = self.addMenuItem(name, 'GS', ilist, url, self.addonIcon, self.addonFanart, infoList, isFolder=True)
   return(ilist)

 def getAddonShows(self,url,ilist):
   html  = self.getRequest('http://www.cbc.ca%s' % url)
   html1 = re.compile('<section class="category-subs full">(.+?)</section', re.DOTALL).search(html)
   if not html1 is None:
       html = html1.group(1)
       shows = re.compile('a href="(.+?)">(.+?)<', re.DOTALL).findall(html)
   else:
       html1 = re.compile('<section class="category-content full">(.+?)</section', re.DOTALL).search(html)
       if not html1 is None:
           ilist = self.getAddonEpisodes(url, ilist)
           return(ilist)
       else:
           html = re.compile('<section class="section-cats full">(.+?)</section', re.DOTALL).search(html).group(1)
           shows = re.compile('a href="(.+?)">(.+?)<', re.DOTALL).findall(html)
   for url, name in shows:
      infoList = {}
      infoList['mediatype'] = 'tvshow'
      infoList['Title'] = name
      infoList['TVShowTitle'] = name
      ilist = self.addMenuItem(name, 'GE', ilist, url, self.addonIcon, self.addonFanart, infoList, isFolder=True)
   return(ilist)



 def getAddonEpisodes(self,url,ilist):
   self.defaultVidStream['width']  = 960
   self.defaultVidStream['height'] = 540

   geurl = url.replace('%3A',':',1)
   html  = self.getRequest('http://www.cbc.ca%s' % geurl)
   html  = re.compile('<section class="category-content full">(.+?)</section', re.DOTALL).search(html).group(1)
   epis  = re.compile('<a href="(.+?)" aria-label="(.+?)".+?src="(.+?)"(.+?)</a', re.DOTALL).findall(html)
   for (url,name,img, meta) in epis:
     name = name.decode('utf-8','replace')
     infoList={}
     if 'title">' in meta:
         name = re.compile('title">(.+?)<', re.DOTALL).search(meta).group(1)
         if 'date">' in meta:
             name = re.compile('date">(.+?)<', re.DOTALL).search(meta).group(1) + ' - ' +name

     if 'description">' in meta:
         plot = re.compile('description">(.+?)<', re.DOTALL).search(meta).group(1)
     else:
         plot = name

     infoList['TVShowTitle'] = xbmc.getInfoLabel('ListItem.TVShowTitle')
     infoList['Title'] = name
     try:
        infoList['Plot'] = h.unescape(plot.decode('utf-8'))
     except:
        infoList['Plot'] = h.unescape(plot)
     infoList['mediatype'] = 'episode'
     fanart = img
     ilist = self.addMenuItem(name,'GV', ilist, url, img, fanart, infoList, isFolder=False)
   return(ilist)


 def getAddonVideo(self,lurl):
      vid = uqp(lurl)
      vid = vid.rsplit('/',1)[1]
      html = self.getRequest('http://tpfeed.cbc.ca/f/ExhSPC/vms_5akSXx4Ng_Zn?q=*&byGuid=%s' % vid)
      a = json.loads(html)
      a = a['entries'][0]['content']
      u = ''
      vwid = 0
      for b in a:
         if b['width'] >= vwid:
            u = b['url']
            vwid = b['width']

      u = u.split('/meta.smil',1)[0]
      u = u + '?mbr=true&manifest=m3u&feed=Player%20Selector%20-%20Prod'
      html = self.getRequest(u)
      u = re.compile('src="(.+?)"', re.DOTALL).search(html)
      if u is None:
           return
      u = u.group(1)
      liz = xbmcgui.ListItem(path=u)
      suburl = re.compile('<textstream src="(.+?)".+?/>', re.DOTALL).findall(html)
      for sub in suburl:
          if '.srt' in sub:
              liz.setSubtitles([sub])
              break
      infoList={}
      infoList['mediatype'] = xbmc.getInfoLabel('ListItem.DBTYPE')
      infoList['Title'] = xbmc.getInfoLabel('ListItem.Title')
      infoList['TVShowTitle'] = xbmc.getInfoLabel('ListItem.TVShowTitle')
      infoList['Year'] = xbmc.getInfoLabel('ListItem.Year')
      infoList['Premiered'] = xbmc.getInfoLabel('Premiered')
      infoList['Plot'] = xbmc.getInfoLabel('ListItem.Plot')
      infoList['Studio'] = xbmc.getInfoLabel('ListItem.Studio')
      infoList['Genre'] = xbmc.getInfoLabel('ListItem.Genre')
      infoList['Duration'] = xbmc.getInfoLabel('ListItem.Duration')
      infoList['MPAA'] = xbmc.getInfoLabel('ListItem.Mpaa')
      infoList['Aired'] = xbmc.getInfoLabel('ListItem.Aired')
      infoList['Season'] = xbmc.getInfoLabel('ListItem.Season')
      infoList['Episode'] = xbmc.getInfoLabel('ListItem.Episode')
      liz.setInfo('video', infoList)
      xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)
