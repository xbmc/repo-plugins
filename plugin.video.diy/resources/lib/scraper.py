# -*- coding: utf-8 -*-
# DIY Network Kodi Video Addon
#
from t1mlib import t1mAddon
import json
import re
import os
import datetime
import urllib
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
     html = self.getRequest('https://www.diynetwork.com/shows/full-episodes')
     html = re.compile('<section class="o-Capsule o-EditorialPromo(.+?)<div class="container-aside">', re.DOTALL).search(html).group(1)
     a = re.compile('m-MediaBlock--PLAYLIST">.+?href="(.+?)".+?data-src="(.+?)".+?HeadlineText.+?>(.+?)<.+?AssetInfo">(.+?)<', re.IGNORECASE | re.DOTALL).findall(html)
     fanart = self.addonFanart
     for i, (url, thumb, name, vidcnt) in list(enumerate(a[1:], start=1)):
       infoList = {}
       name=name.strip()
       vidcnt = vidcnt.strip()
       epinum = vidcnt.split(' ',1)[0]
       if epinum.isdigit():
           if int(epinum) == 0:
               continue
           infoList['Episode'] = int(epinum)
       else:
           continue

       html = self.getRequest(url.rsplit('/',1)[0])
       plot = re.compile('"og:description" content="(.+?)"',re.DOTALL).search(html)
       if plot is not None:
          plot = plot.group(1)
       else:
          plot = name
       infoList['TVShowTitle'] = name
       infoList['Title'] = name
       infoList['Studio'] = 'DIY'
       infoList['Genre'] = ''
       epinum = vidcnt.split(' ',1)[0]
       if epinum.isdigit():
          infoList['Episode'] = int(epinum)
       else: 
          infoList['Episode'] = 0
       infoList['Plot'] = h.unescape(plot)
       infoList['mediatype'] = 'tvshow'
       ilist = self.addMenuItem(name,'GE', ilist, url, thumb, fanart, infoList, isFolder=True)
     return(ilist)


  def getAddonEpisodes(self,url,ilist):
        url = uqp(url)
        if not url.startswith('http'):
            url = 'https:'+url
        showName = xbmc.getInfoLabel('ListItem.Title')
        html = self.getRequest(url)
        html = re.compile('<div id="video-player".+?type="text/x-config">(.+?)</script>',re.DOTALL).search(html)
        if html != None:
              a = json.loads(html.group(1))
        else:
#              xbmc.executebuiltin('XBMC.Notification("%s", "%s", %s)' % ( self.addonName, addonLanguage(30011) , 5000) )
              return(ilist)
        vids = a['channels'][0]['videos']

        for i,b in list(enumerate(vids, start=1)):
           url = b['releaseUrl']
           name = h.unescape(b['title'])
           fanart = 'http://www.hgtv.com%s' % b['thumbnailUrl']
           thumb = 'http://www.hgtv.com%s' % b['thumbnailUrl']

           infoList = {}
           infoList['Duration'] = b['length']
           infoList['Title'] = name
           infoList['Studio'] = b['publisherId']
           html = self.getRequest(url)
           mpaa = re.compile('ratings="(.+?)"',re.DOTALL).search(html)
           if mpaa is not None:
              infoList['MPAA'] = mpaa.group(1).split(':',1)[1]
           epinum = re.compile('"episodeNumber" value=".(.+?)H"',re.DOTALL).search(html)
           if epinum is not None:
              infoList['Episode'] = int(epinum.group(1).replace('M',''), 16)
           seanum  = re.compile('"episodeNumber" value="(.+?)H"',re.DOTALL).search(html)
           if seanum is not None:
              infoList['Season'] = int(seanum.group(1).replace('M','').replace('S',''),16)/256
           infoList['Plot'] = h.unescape(b["description"])
           infoList['TVShowTitle'] = showName
           infoList['mediatype'] = 'episode'
           ilist = self.addMenuItem(name,'GV', ilist, url, thumb, fanart, infoList, isFolder=False)
        return(ilist)



  def getAddonVideo(self,url):
   html = self.getRequest(uqp(url))
   suburl = ''
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
   if suburl != "" :
      liz.setSubtitles([suburl])
   xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)


