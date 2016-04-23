# -*- coding: utf-8 -*-
# HGTV Kodi Video Addon
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
   addonLanguage  = self.addon.getLocalizedString
   url = 'http://www.hgtv.com/shows/full-episodes'
   html = self.getRequest(url)
   a = []
   html = re.compile('<div class="capsule editorialPromo parbase section">(.+?)<div class="textPromo capsule parbase section">', re.DOTALL).search(html).group(1)
   a = re.compile('<div class="m-MediaBlock o-Capsule__m-MediaBlock">.+?href="(.+?)".+?data-src="(.+?)".+?HeadlineText">(.+?)<.+?AssetInfo">(.+?)<', re.DOTALL).findall(html)
   for i, (url, thumb, name, vidcnt) in list(enumerate(a, start=1)):
       name=name.strip()
       vidcnt = vidcnt.strip()
       infoList = {}
       epinum = vidcnt.split(' ',1)[0]
       if epinum.isdigit(): infoList['Episode'] = int(epinum)
       else: continue
       html = self.getRequest(url.rsplit('/',1)[0])
       plot = re.compile('"og:description" content="(.+?)"',re.DOTALL).search(html)
       if plot != None:
           plot = plot.group(1)
       else:
           plot = name
       fanart = re.compile('property="og:image" content="(.+?)"',re.DOTALL).search(html)
       if fanart != None:
           fanart = fanart.group(1).replace('616.347.jpeg','1280.720.jpeg',1)
       else:
           fanart = thumb
       infoList['TVShowTitle'] = name
       infoList['Title']       = name
       infoList['Studio']      = 'HGTV'
       infoList['Plot'] = h.unescape(plot)
       infoList['mediatype'] = 'tvshow'
       ilist = self.addMenuItem(name,'GE', ilist, url, thumb, fanart, infoList, isFolder=True)
   return(ilist)


  def getAddonEpisodes(self,url,ilist):
        addonLanguage  = self.addon.getLocalizedString
        self.defaultVidStream['width']  = 1280
        self.defaultVidStream['height'] = 720
        url = uqp(url)
        showName = xbmc.getInfoLabel('ListItem.Title')
        html  = self.getRequest(url)
        html    = re.compile('<div id="video-player".+?type="text/x-config">(.+?)</script>',re.DOTALL).search(html)
        if html != None:
              a = json.loads(html.group(1))
        else:
              xbmc.executebuiltin('XBMC.Notification("%s", "%s", %s)' % ( self.addonName, addonLanguage(30011) , 5000) )
              return(ilist)
        vids = a['channels'][0]['videos']

        for i,b in list(enumerate(vids, start=1)):
           url     = b['releaseUrl']
           dirty = True
           name    = h.unescape(b['title'])
           fanart  = 'http://www.hgtv.com%s' % b['thumbnailUrl']
           thumb   = 'http://www.hgtv.com%s' % b['thumbnailUrl']

           infoList = {}
           infoList['Duration']    = b['length']
           infoList['Title']       = name
           infoList['Studio']      = b['publisherId']
           html = self.getRequest(url)
           mpaa = re.compile('ratings="(.+?)"',re.DOTALL).search(html)
           if mpaa is not None: infoList['MPAA'] = mpaa.group(1).split(':',1)[1]
           epinum = re.compile('"episodeNumber" value=".(.+?)H"',re.DOTALL).search(html)
           if epinum is not None: infoList['Episode'] = int(epinum.group(1).replace('Z',''), 16)
           seanum  = re.compile('"episodeNumber" value="(.+?)H"',re.DOTALL).search(html)
           if seanum is not None: infoList['Season']  = int(seanum.group(1).replace('Z',''),16)/256
           infoList['Plot']        = h.unescape(b["description"])
           infoList['TVShowTitle'] = showName
           infoList['mediatype'] = 'episode'
           ilist = self.addMenuItem(name,'GV', ilist, url, thumb, fanart, infoList, isFolder=False)
        return(ilist)



  def getAddonVideo(self,url):
   html   = self.getRequest(uqp(url))
   suburl =''
   subs = re.compile('<textstream src="(.+?)"',re.DOTALL).findall(html)
   for st in subs:
      if '.srt' in st:
         suburl = st
         break

   url   = re.compile('<video src="(.+?)"',re.DOTALL).search(html)
   if url != None:
     url = url.group(1)
   else:
     url, msg   = re.compile('<ref src="(.+?)".+?abstract="(.+?)"',re.DOTALL).search(html).groups()
     xbmc.executebuiltin('XBMC.Notification("%s", "%s", %s)' % ( self.addonName, msg , 5000) )
     return
   liz = xbmcgui.ListItem(path = url)
   if suburl != "" : liz.setSubtitles([suburl])
   xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)

