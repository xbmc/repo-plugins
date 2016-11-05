# -*- coding: utf-8 -*-
# NPR Music Kodi Video Addon
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
NPRBASE = 'http://www.npr.org%s'


class myAddon(t1mAddon):

  def getAddonMenu(self,url,ilist):
   addonLanguage  = self.addon.getLocalizedString
   urlbase   = NPRBASE % ('/sections/music-videos/')
   html = self.getRequest(urlbase)
   name = addonLanguage(30000)
   urlbase = NPRBASE % ('/series/15667984/favorite-sessions')
   ilist = self.addMenuItem(name,'GC', ilist, urlbase, self.addonIcon, self.addonFanart, {}, isFolder=True)
   m = re.compile('<div class="subtopics">(.+?)</ul>',re.DOTALL).search(html)
   cats = re.compile('<a href="(.+?)">(.+?)<',re.DOTALL).findall(html,m.start(1),m.end(1))
   for url, name in cats:
     url = NPRBASE % (url)
     ilist = self.addMenuItem(name,'GC', ilist, url, self.addonIcon, self.addonFanart, {}, isFolder=True)
   return(ilist)



  def getAddonCats(self,url,ilist):
             addonLanguage  = self.addon.getLocalizedString
             html = self.getRequest(uqp(url))
             nexturl = url
             blobs = re.compile('<article class(.+?)</article>',re.DOTALL).findall(html)
             curlink  = 0
             nextlink = 1
             for blob in blobs:
               nextlink = nextlink+1
               if ('article-video' in blob) or ('type-video' in blob):
                 try:
                    (url, thumb, name, dt, plot) = re.compile('<a href="(.+?)".+?src="(.+?)".+?title="(.+?)".+?<time datetime="(.+?)".+?</time>(.+?)</p',re.DOTALL).search(blob).groups()
                 except:
                    (url, thumb, name) = re.compile('<a href="(.+?)".+?src="(.+?)".+?alt="(.+?)"',re.DOTALL).search(blob).groups()
                    plot = name
                    dt   = ''
                 name = h.unescape(name)
                 plot = h.unescape(plot.strip().decode('utf-8'))
                 infoList ={}
                 infoList['Title'] = name
                 infoList['date']  = dt
                 infoList['Plot']  = plot
                 try: infoList['Year'] = int(dt.split('-',1)[0])
                 except: pass
                 fanart = thumb
                 ilist = self.addMenuItem(name,'GV', ilist, url, thumb, fanart, infoList, isFolder=False)

             curlink=0
             nextstr = '/archive?start='
             if (nextstr in nexturl):
                (nexturl,curlink) = nexturl.split(nextstr,1)
                curlink = int(curlink)
             nextlink = str(nextlink+curlink+1)
             url = nexturl+nextstr+nextlink
             name = '[COLOR red]%s[/COLOR]' % (addonLanguage(30001))
             home = self.addon.getAddonInfo('path').decode(UTF8)
             iconNext = xbmc.translatePath(os.path.join(home, 'next.png'))
             ilist = self.addMenuItem(name,'GC', ilist, url, iconNext, self.addonFanart, {}, isFolder=True)
             return(ilist)


  def getAddonVideo(self,url):
            addonLanguage  = self.addon.getLocalizedString
            html = self.getRequest(url)
            try:
                 a = re.compile("data-jwplayer='(.+?)'>", re.DOTALL).search(html).group(1)
                 a = json.loads(a)
                 finalurl = a['sources'][1]['file']
            except:
                try:
                    videoid = re.compile('<div class="video-wrap">.+?src="http://www\.youtube\.com/embed/(.+?)\?',re.DOTALL).search(html).group(1)
                    finalurl = 'plugin://plugin.video.youtube/?path=/root/video&action=play_video&videoid=%s' % (videoid)
                except:
                    dialog = xbmcgui.Dialog()
                    dialog.ok(addonLanguage(30002), '',addonLanguage(30003)) #tell them no video found
                    return
            xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, xbmcgui.ListItem(path = finalurl))

