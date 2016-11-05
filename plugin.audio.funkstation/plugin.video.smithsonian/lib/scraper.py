# -*- coding: utf-8 -*-
# Smithsonian Channel Kodi Video Addon
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
   xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
   addonLanguage  = self.addon.getLocalizedString
   self.defaultVidStream['width']  = 1920
   self.defaultVidStream['height'] = 1080

   html = self.getRequest('http://www.smithsonianchannel.com/full-episodes')
   a = re.compile('data-premium=".+?href="(.+?)".+?srcset="(.+?)".+?"timecode">(.+?)<.+?</li>',re.DOTALL).findall(html)
   meta = self.getAddonMeta()
   try:    i = len(meta)
   except: meta={}
   pDialog = xbmcgui.DialogProgress()
   pDialog.create(self.addonName, addonLanguage(30101))
   pDialog.update(0)
   dirty = False
   numShows = len(a)
   for i, (url, thumb, dur) in list(enumerate(a, start=1)):
      try:
        (iconimg,fanart, infoList)  = meta[url]
      except:
       dirty = True
       html = self.getRequest('http://www.smithsonianchannel.com%s' % url)
       m = re.compile('property="og:title" content="(.+?)"',re.DOTALL).search(html)
       title = m.group(1)
       m = re.compile('property="og:image" content="(.+?)"',re.DOTALL).search(html, m.end(1))
       iconimg = m.group(1)
       m = re.compile('"og:site_name" content="(.+?)"', re.DOTALL).search(html, m.end(1))
       studio = m.group(1)
       m = re.compile('"twitter:image" content="(.+?)"',re.DOTALL).search(html, m.end(1))
       fanart = m.group(1)
       plot = re.compile('<div class="accordion-content-mobile">.+?"description">(.+?)</p',re.DOTALL).search(html,m.end(1)).group(1)
       infoList = {}
       length = 0
       dur = dur.replace('|','').split(':')
       for d in dur: length = length*60 + int(d.strip())

       infoList['Duration']    = length
       infoList['MPAA']        = 'tv-pg'
       infoList['Title']       = h.unescape(title)
       infoList['Studio']      = studio
       infoList['Genre']       = 'Documentary'
       infoList['Plot']        = h.unescape(plot)
       meta[url] = (iconimg, fanart, infoList)
      name  = infoList['Title']
      ilist = self.addMenuItem(name,'GV', ilist, url, iconimg, fanart, infoList, isFolder=False)
      pDialog.update(int((100*i)/numShows))
   pDialog.close()
   if dirty == True: self.updateAddonMeta(meta)
   return(ilist)

  def getAddonVideo(self,url):
   html = self.getRequest('http://www.smithsonianchannel.com%s' % uqp(url))
   (suburl, vidID) = re.compile('data-vttfile="(.+?)".+?data-bcid="(.+?)"', re.DOTALL).search(html).groups()
   url = 'http://c.brightcove.com/services/mobile/streaming/index/master.m3u8?videoId=%s&pubId=1466806621001' % (vidID)
   liz = xbmcgui.ListItem(path = url)
   if suburl != "" : liz.setSubtitles(['http://www.smithsonianchannel.com%s'% suburl])
   xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)

