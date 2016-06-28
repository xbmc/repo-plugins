# -*- coding: utf-8 -*-
# KodiAddon (Syfy)
#
from t1mlib import t1mAddon
import json
import re
import urllib
import urllib2
import xbmcplugin
import xbmcgui
import xbmc
import datetime
import HTMLParser
import sys
import os

h = HTMLParser.HTMLParser()
uqp = urllib.unquote_plus
UTF8 = 'utf-8'


class myAddon(t1mAddon):

 def getAddonMenu(self,url,ilist):
     epiHTML = self.getRequest('http://www.syfy.com/episodes')
     posterHTML = self.getRequest('http://www.syfy.com/shows')
     posters = re.compile('<div class="grid-image-above">.+?<img  srcset="(.+?)".+?class="title">.+?>(.+?)<',re.DOTALL).findall(posterHTML)
     shows = re.compile('<div class="show id.+?<h3>(.+?)<.+?</div',re.DOTALL).findall(epiHTML)
     for name in shows:
         poster = None
         for pimg, pname in posters:
             if pname == name:
                 poster = pimg
                 break
         infoList = {}
         infoList['Title'] = name
         infoList['TVShowTitle'] = name
         infoList['mediatype'] = 'tvshow'
         infoList['Studio'] = 'Syfy'
         url = name
         contextMenu = [('Add To Library','XBMC.RunPlugin(%s?mode=DF&url=AL%s)' % (sys.argv[0], url))]
         ilist = self.addMenuItem(name,'GE', ilist, url, poster, self.addonFanart, infoList, isFolder=True, cm=contextMenu)
     return(ilist)



 def getAddonEpisodes(self,url,ilist, getFileData = False):
     sname = url
     self.defaultVidStream['width'] = 1920
     self.defaultVidStream['height']= 1080
     html = self.getRequest('http://www.syfy.com/episodes')
     m = re.compile('<div class="show id.+?<h3>'+sname+'</h3>(.+?)<div class="view-footer">',re.DOTALL).search(html)
     if m is None:
         return(ilist)
     fd = re.compile('href="(.+?)/videos').search(html,m.start(1),m.end(1)).group(1)
     epis = re.compile('href="'+fd+'(.+?)"',re.DOTALL).findall(html,m.start(1),m.end(1))
     for shurl in epis:
         url = 'http://www.syfy.com%s' % fd+shurl
         html = self.getRequest(url)
         purl = re.compile('data-src="(.+?)"',re.DOTALL).search(html).group(1)
         purl = 'http:'+purl.replace('&amp;','&')
         html = self.getRequest(purl)
         purl = re.compile('<link rel="alternate" href=".+?<link rel="alternate" href="(.+?)"',re.DOTALL).search(html).group(1)
         purl += '&format=Script&height=576&width=1024'
         html = self.getRequest(purl)
         a = json.loads(html)
         name = a['title']
         fanart = a['defaultThumbnailUrl']
         thumb = a['defaultThumbnailUrl']
         infoList = {}
         infoList['Date'] = datetime.datetime.fromtimestamp(a['pubDate']/1000).strftime('%Y-%m-%d')
         infoList['Aired'] = infoList['Date']
         infoList['Duration'] = str(int(a['duration']/1000))
         infoList['MPAA'] = a['ratings'][0]['rating']
         infoList['TVShowTitle'] = sname
         infoList['Title'] = a['title']
         infoList['Studio'] = a['provider']
         infoList['Genre'] = (a['nbcu$advertisingGenre']).replace('and','/')
         infoList['Episode'] = a.get('pl1$episodeNumber')
         infoList['Season'] = a.get('pl1$seasonNumber')
         infoList['Plot'] = a.get('description')
         if infoList['Plot'] in [None, '']:
             infoList['Plot'] = a.get('abstract')
         infoList['Plot'] = h.unescape(infoList['Plot'])
         url = a["captions"][0]["src"]
         url = url.split('/caption/',1)[1]
         url = url.split('.',1)[0]
         if getFileData == False:
             ilist = self.addMenuItem(name,'GV', ilist, url, thumb, fanart, infoList, isFolder=False)
         else:
             if not 'Spanish_Subtitles' in url:
                 ilist.append((infoList.get('Season',''), infoList.get('Episode',''), url))
     return(ilist)

 def doFunction(self, url):
     func = url[0:2]
     url  = url[2:]
     if func == 'AL':
         name  = xbmc.getInfoLabel('ListItem.Title')
         profile = self.addon.getAddonInfo('profile').decode(UTF8)
         moviesDir  = xbmc.translatePath(os.path.join(profile,'TV Shows'))
         movieDir  = xbmc.translatePath(os.path.join(moviesDir, name))
         if not os.path.isdir(movieDir):
             os.makedirs(movieDir)
         ilist = []
         ilist = self.getAddonEpisodes(url, ilist, getFileData = True)
         for season, episode, url in ilist:
             se = 'S%sE%s' % (str(season), str(episode))
             xurl = '%s?mode=GV&url=%s' % (sys.argv[0], url)
             strmFile = xbmc.translatePath(os.path.join(movieDir, se+'.strm'))
             with open(strmFile, 'w') as outfile:
                 outfile.write(xurl)         
     json_cmd = '{"jsonrpc":"2.0","method":"VideoLibrary.Scan", "params": {"directory":"%s/"},"id":1}' % movieDir.replace('\\','/')
     jsonRespond = xbmc.executeJSONRPC(json_cmd)


 def getAddonVideo(self,url):
     gvu1 = 'https://tvesyfy-vh.akamaihd.net/i/prod/video/%s_,25,40,18,12,7,4,2,00.mp4.csmil/master.m3u8?__b__=1000&hdnea=st=%s~exp=%s'
     td = (datetime.datetime.utcnow()- datetime.datetime(1970,1,1))
     unow = int((td.microseconds + (td.seconds + td.days * 24 * 3600) * 10**6) / 10**6)
     u = gvu1 % (url, str(unow), str(unow+60))
     liz = xbmcgui.ListItem(path = u)
     infoList ={}
     infoList['Title'] = xbmc.getInfoLabel('ListItem.Title')
     infoList['TVShowTitle'] = xbmc.getInfoLabel('ListItem.TVShowTitle')
     infoList['Year'] = xbmc.getInfoLabel('ListItem.Year')
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
