# -*- coding: utf-8 -*-
# KodiAddon Travel Channel
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
   html = self.getRequest('http://www.travelchannel.com/shows/whats-new-on-travel-channel/articles/full-episodes')
   m = re.compile('<article(.+?)</article',re.DOTALL).search(html)
   a = re.compile('<div class="fullEpisode.+?<a href="(.+?)".+?title">(.+?)<.+?src="(.+?)".+?</div', re.DOTALL).findall(html,m.start(1),m.end(1))
   a[(len(a)-1)] = ('/video/p/1?wcmmode=disabled',addonLanguage(30021),self.addonIcon)
   for url,name,thumb in a:
       html  = self.getRequest('http://www.travelchannel.com%s' % url)
       c     = re.compile("data\-videoplaylist\-data='(.+?)'>", re.DOTALL).findall(html)
       if len(c) == 0: continue
       else: vidcnt = len(c)
       name=name.strip()
       b = json.loads(c[0])
       img = 'http://www.travelchannel.com%s' % b['thumbnailUrl']
       plot = name
       fanart = thumb
       infoList = {}
       infoList['TVShowTitle'] = name
       infoList['Title']       = name
       infoList['Studio']      = 'Travel Channel'
       infoList['Genre']       = ''
       try:    infoList['Episode'] = int(vidcnt)
       except: infoList['Episode'] = 0
       infoList['Plot'] = h.unescape(plot)
       ilist = self.addMenuItem(name,'GE', ilist, url, thumb, self.addonFanart, infoList, isFolder=True)
   return(ilist)


  def getAddonEpisodes(self,url,ilist):
   addonLanguage  = self.addon.getLocalizedString
   geurl = uqp(url)
   html  = self.getRequest('http://www.travelchannel.com%s' % uqp(url))
   c     = re.compile("data\-videoplaylist\-data='(.+?)'>", re.DOTALL).findall(html)
   for a in c:
      b = json.loads(a)
      url     = b['releaseUrl']
      html = self.getRequest(url)
      name    = h.unescape(b['title'])
      thumb   = 'http://www.travelchannel.com%s' % b['thumbnailUrl']
      fanart   = 'http://www.travelchannel.com%s' % b['thumbnailUrl']

      infoList = {}
      infoList['Duration']    = b['length']
      infoList['Title']       = name
      infoList['Studio']      = b['publisherId']
      months = {'Jan':'01','Feb':'02','Mar':'03','Apr':'04','May':'05','Jun':'06','Jul':'07','Aug':'08','Sep':'09','Oct':'10','Nov':'11','Dec':'12'}
      try:
         dstr = (re.compile('"premierDate" value="(.+?)"',re.DOTALL).search(html).group(1)).split(' ')
         dt   = '%s-%s-%s' % (dstr[5],months[dstr[1]],dstr[2])
         infoList['Date']        = dt
         infoList['Aired']       = infoList['Date']
      except: pass
      try:    infoList['MPAA'] = re.compile('ratings="(.+?)"',re.DOTALL).search(html).group(1).split(':',1)[1]
      except: infoList['MPAA'] = None
      try:    infoList['Episode'] = int(re.compile('"episodeNumber" value=".(.+?)H"',re.DOTALL).search(html).group(1).replace('Z',''), 16)
      except: infoList['Episode'] = None
      try:    infoList['Season']  = int(re.compile('"episodeNumber" value="(.+?)H"',re.DOTALL).search(html).group(1).replace('Z',''),16)/256
      except: infoList['Season']  = 1
      infoList['Plot']        = h.unescape(b["description"])
      ilist = self.addMenuItem(name,'GV', ilist, url, thumb, fanart, infoList, isFolder=False)

   if len(ilist) != 0:
      if 'wcmmode=disabled' in geurl:
        name = '[COLOR red]%s[/COLOR]' % addonLanguage(30012)
        url = '/video/p/%s?wcmmode=disabled' % str(int(geurl[9])+1)
        ilist = self.addMenuItem(name,'GE', ilist, url, self.addonIcon, self.addonFanart, {}, isFolder=True)
   return(ilist)


  def getAddonVideo(self,url):
   html   = self.getRequest(uqp(url))
   try:    
           subs = re.compile('<textstream src="(.+?)"',re.DOTALL).findall(html)
           suburl =''
           for st in subs:
             if '.srt' in st:
                suburl = st
                break
   except: pass
   try:
     url   = re.compile('<video src="(.+?)"',re.DOTALL).search(html).group(1)
   except:
     url, msg   = re.compile('<ref src="(.+?)".+?abstract="(.+?)"',re.DOTALL).search(html).groups()
     xbmc.executebuiltin('XBMC.Notification("%s", "%s", %s)' % ( self.addonName, msg , 5000) )
   liz = xbmcgui.ListItem(path=url)
   if suburl != "" : liz.setSubtitles([suburl])
   xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)
