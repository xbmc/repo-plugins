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
      html = self.getRequest(NPRBASE % ('/sections/music-videos/'))
      m = re.compile('<div class="subtopics">(.+?)</ul>',re.DOTALL).search(html)
      cats = re.compile('<a href="(.+?)">(.+?)<',re.DOTALL).findall(html,m.start(1),m.end(1))
      for url, name in cats:
          ilist = self.addMenuItem(name,'GC', ilist, NPRBASE % (url), self.addonIcon, self.addonFanart, {}, isFolder=True)
      return(ilist)

  def getAddonCats(self,url,ilist):
      addonLanguage  = self.addon.getLocalizedString
      html = self.getRequest(uqp(url))
      nexturl = url
      blobs = re.compile('<article class(.+?)</article>',re.DOTALL).findall(html)
      for nextlink,blob in enumerate(blobs,2):
          if ('article-video' in blob) or ('type-video' in blob):
              a = re.compile('<a href="(.+?)".+?src="(.+?)".+?title="(.+?)".+?<time datetime="(.+?)".+?</time>(.+?)</p',re.DOTALL).search(blob)
              if a is not None:
                  (url, thumb, name, dt, plot) = a.groups()
              else:
                  (url, thumb, name) = re.compile('<a href="(.+?)".+?src="(.+?)".+?alt="(.+?)"',re.DOTALL).search(blob).groups()
                  plot = name
                  dt = ''
              name = h.unescape(name)
              plot = h.unescape(plot.strip().decode('utf-8'))
              infoList ={}
              infoList['Title'] = name
              if dt is not None:
                  infoList['date']  = dt
              infoList['Plot']  = plot
              year = dt.split('-',1)[0]
              if year is not None and year.isdigit():
                  infoList['Year'] = int()
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
      a = re.compile("data-jwplayer='(.+?)'>", re.DOTALL).search(html)
      if a is not None:
           a = json.loads(a.group(1))
           finalurl = a['sources'][1]['file']
      else:
           videoid = re.compile('<div class="video-wrap">.+?src="https://www\.youtube\.com/embed/(.+?)\?',re.DOTALL).search(html)
           if videoid is not None:
               finalurl = 'plugin://plugin.video.youtube/?path=/root/video&action=play_video&videoid=%s' % (videoid.group(1))
           else:
               dialog = xbmcgui.Dialog()
               dialog.ok(addonLanguage(30002), '',addonLanguage(30003)) #tell them no video found
               return
      xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, xbmcgui.ListItem(path = finalurl))
