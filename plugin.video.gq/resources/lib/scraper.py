# -*- coding: utf-8 -*-
# GQ Magazine Kodi Video Addon
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
     dolist = [(30081, '/new.js?page=1'),(30082, '/popular.js?page=1')]
     for gstr, url in dolist:
       name = addonLanguage(gstr)
       ilist = self.addMenuItem(name,'GE', ilist, url, self.addonIcon, self.addonFanart, {} , isFolder=True)

     html = self.getRequest('http://video.gq.com/categories')
     a    = re.compile('class="cne-nav--drawer__item--categories".+?label="(.+?)".+?href="(.+?)".+?src="(.+?)"' , re.DOTALL).findall(html)
     for name, url, fanart in a:
       name = h.unescape(name.decode(UTF8))
       url  = h.unescape(url)
       url += '.js?page=1'
       vidcnt = 1
       infoList = {}
       infoList['TVShowTitle'] = name
       infoList['Title']       = name
       infoList['Studio']      = addonLanguage(30010)
       infoList['Genre']       = ''
       try:    infoList['Episode'] = int(vidcnt)
       except: infoList['Episode'] = 0
       infoList['Plot'] = name
       ilist = self.addMenuItem(name,'GE', ilist, url, self.addonIcon, fanart, infoList, isFolder=True)
     return(ilist)


  def getAddonEpisodes(self,url,ilist):
     addonLanguage  = self.addon.getLocalizedString
     self.defaultVidStream['width'] = 1920
     self.defaultVidStream['height'] = 1080
     url = 'http://video.gq.com%s' % url
     headers = self.defaultHeaders
     headers['X-Requested-With'] = 'XMLHttpRequest'
     html = self.getRequest(url,None, headers).replace('\\n','').replace('\\','')
     shows = re.compile('<div class="cne-thumb cne-episode-block ".+?src="(.+?)".+?href="(.+?)">(.+?)<.+?class="cne-rollover-description".+?p>(.+?)<',re.DOTALL).findall(html)
     for thumb,url,name,plot in shows:
        infoList = {}
        plot = plot.strip()
        name = name.strip()
#        fanart = thumb.replace(',h_321',',h_720').replace(',w_570',',w_1280').replace(',q_80',',q_100')
        infoList['Title'] = h.unescape(name.decode(UTF8))
        infoList['Studio'] = 'GQ'
        infoList['Plot'] = h.unescape(plot.decode(UTF8))
        ilist = self.addMenuItem(name,'GV', ilist, url, thumb, None, infoList, isFolder=False)
     url = re.compile("'ajaxurl'.+?'(.+?)'",re.DOTALL).search(html)
     if url:
         url = url.group(1)
         name ='[COLOR red]%s[/COLOR]' % (addonLanguage(30084))
         mode = 'GE'
         ilist = self.addMenuItem(name,'GE', ilist, url, self.addonIcon, self.addonFanart, infoList, isFolder=True)
     return(ilist)


  def getAddonVideo(self,url):
     url = uqp(url)
     html = self.getRequest('http://video.gq.com/%s' % uqp(url)).replace('\\n','').replace('\\','')
     url = re.compile('"contentURL".+?="(.+?)"', re.DOTALL).search(html).group(1)
     url = url.replace('low.mp4','high.mp4')
     liz = xbmcgui.ListItem(path = url)
     xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)
