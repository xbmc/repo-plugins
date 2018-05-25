# -*- coding: utf-8 -*-
# TVO Kids Kodi Video Addon
#
from t1mlib import t1mAddon
import json
import re
import os
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
     ilist = self.addMenuItem('Ages 2 to 5', 'GS', ilist, 'preschool', self.addonIcon, self.addonFanart, {} , isFolder=True)
     ilist = self.addMenuItem('Ages 11 and under', 'GS', ilist, 'school-age', self.addonIcon, self.addonFanart, {} , isFolder=True)
     return(ilist)

  def getAddonShows(self,url,ilist):
     html = self.getRequest('https://tvokids.com/%s/videos' % url)
     shows = re.compile('<div class="tvokids-tile.+?href="(.+?)".+?"tile-title">(.+?)<.+?data-lazyload="(.+?)".+?</div', re.DOTALL).findall(html)
     for (url, name, thumb) in shows:
         name = name.strip()
         name = h.unescape(name).replace('&#039;',"'")
         fanart = thumb
         infoList = {}
         infoList['title'] = name
         infoList['TVShowTitle'] = name
         infoList['mediatype'] = 'tvshow'
         ilist = self.addMenuItem(name, 'GE', ilist, url, thumb, fanart, infoList, isFolder=True)
     return(ilist)

  def getAddonEpisodes(self,url,ilist):
     html = self.getRequest('https://tvokids.com%s' % url)
     html = re.compile('<footer class(.+?)</footer',re.DOTALL).search(html).group(1)
     a = re.compile('<a href="(.+?)".+?aria-label="(.+?)"', re.DOTALL).findall(html)
     for url, name in a:
         name = h.unescape(name).replace('&#039;',"'")
         html = self.getRequest('https://tvokids.com%s' % (url))
         url = re.compile('data-video-id="(.+?)"', re.DOTALL).search(html).group(1)
         vurl = 'https://secure.brightcove.com/services/viewer/htmlFederated?&width=859&height=482&flashID=BrightcoveExperience&bgcolor=%23FFFFFF&playerID=48543011001&playerKey=&isVid=true&isUI=true&dynamicStreaming=true&%40videoPlayer='+url+'&secureConnections=true&secureHTMLConnections=true'
         html = self.getRequest(vurl)
         m = re.compile('experienceJSON = (.+?)\};',re.DOTALL).search(html)
         a = json.loads(html[m.start(1):m.end(1)+1])
         a = a.get('data',{'x':None}).get('programmedContent',{'x':None}).get('videoPlayer',{'x':None}).get('mediaDTO',{'x':None})
         thumb = a.get('videoStillURL')
         fanart = thumb
         plot = a.get('longDescription')
         infoList = {}
         infoList['Title'] = name
         infoList['TVShowTitle'] = xbmc.getInfoLabel('ListItem.TVShowTitle')
         infoList['Studio'] = 'TVO Kids'
         infoList['Plot'] = h.unescape(plot)
         infoList['mediatype'] = 'episode'
         ilist = self.addMenuItem(name,'GV', ilist, url, thumb, fanart, infoList, isFolder=False)
     return(ilist)


  def getAddonVideo(self,url):
     url = 'https://secure.brightcove.com/services/viewer/htmlFederated?&width=859&height=482&flashID=BrightcoveExperience&bgcolor=%23FFFFFF&playerID=48543011001&playerKey=&isVid=true&isUI=true&dynamicStreaming=true&%40videoPlayer='+url+'&secureConnections=true&secureHTMLConnections=true'
     html = self.getRequest(url)
     m = re.compile('experienceJSON = (.+?)\};',re.DOTALL).search(html)
     a = json.loads(html[m.start(1):m.end(1)+1])
     a = a.get('data',{'x':None}).get('programmedContent',{'x':None}).get('videoPlayer',{'x':None}).get('mediaDTO',{'x':None})
     suburl = a.get('captions',[{'x':None}])
     if not suburl is None:
         suburl = suburl[0].get('URL')
     b = a.get('IOSRenditions',[])
     u = None
     rate = 0
     for c in b:
         if c['encodingRate'] > rate:
             rate = c['encodingRate']
             u = c['defaultURL']
     b = a.get('renditions',[])
     for c in b:
         if c['encodingRate'] > rate:
             rate = c['encodingRate']
             u = c['defaultURL']
     if rate == 0:
             u = a.get('FLVFullLengthURL')
     if u is None:
         return

     liz = xbmcgui.ListItem(path=u)
     infoList ={}
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
     if not suburl is None:
         subfile = self.procConvertSubtitles(suburl)
         liz.setSubtitles([subfile])
     xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)

