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
   a = re.compile('m-MediaBlock">.+?href="(.+?)".+?data-src="(.+?)".+?HeadlineText">(.+?)<.+?AssetInfo">(.+?)<', re.DOTALL).findall(html)

   meta = self.getAddonMeta()
   try:    i = len(meta['shows'])
   except: meta['shows']={}
   pDialog = xbmcgui.DialogProgress()
   pDialog.create(self.addonName, addonLanguage(30101))
   pDialog.update(0)
   dirty = False
   numShows = len(a)
   for i, (url, thumb, name, vidcnt) in list(enumerate(a, start=1)):
      try:
        (name, url, thumb, fanart, infoList) = meta['shows'][url]
      except:
       dirty = True
       name=name.strip()
       vidcnt = vidcnt.strip()
       infoList = {}
       try:    infoList['Episode'] = int(vidcnt.split(' ',1)[0])
       except: infoList['Episode'] = 0
       if infoList['Episode'] == 0: continue
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
       meta['shows'][url] = (name, url, thumb, fanart, infoList)
      ilist = self.addMenuItem(name,'GE', ilist, url, thumb, fanart, infoList, isFolder=True)
      pDialog.update(int((100*i)/numShows))
   pDialog.close()
   if dirty == True: self.updateAddonMeta(meta)
   return(ilist)


  def getAddonEpisodes(self,url,ilist):
        addonLanguage  = self.addon.getLocalizedString
        self.defaultVidStream['width']  = 1280
        self.defaultVidStream['height'] = 720
        url = uqp(url)
        showName = xbmc.getInfoLabel('ListItem.Title')
        meta  = self.getAddonMeta()
        sname = url
        if meta.get(sname) == None:
              meta[sname]={}
        html  = self.getRequest(url)
        html    = re.compile('<div id="video-player".+?type="text/x-config">(.+?)</script>',re.DOTALL).search(html)
        if html != None:
              a = json.loads(html.group(1))
        else:
              xbmc.executebuiltin('XBMC.Notification("%s", "%s", %s)' % ( self.addonName, addonLanguage(30011) , 5000) )
              return(ilist)
        vids = a['channels'][0]['videos']
        pDialog = xbmcgui.DialogProgress()
        pDialog.create(self.addonName, addonLanguage(30101))
        pDialog.update(0)
        numShows = len(vids)
        dirty = False
        for i,b in list(enumerate(vids, start=1)):
         url     = b['releaseUrl']
         if meta[sname].get(url) != None:
           (name, url, thumb, fanart, infoList) = meta[sname][url]
         else:
           dirty = True
           name    = h.unescape(b['title'])
           fanart  = 'http://www.hgtv.com%s' % b['thumbnailUrl']
           thumb   = 'http://www.hgtv.com%s' % b['thumbnailUrl']

           infoList = {}
           infoList['Duration']    = b['length']
           infoList['Title']       = name
           infoList['Studio']      = b['publisherId']
           try:  html = self.getRequest(url)
           except: continue
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
           infoList['TVShowTitle'] = showName
           infoList['mediatype'] = 'episode'
           meta[sname][url] = (name, url, thumb, fanart, infoList)
         ilist = self.addMenuItem(name,'GV', ilist, url, thumb, fanart, infoList, isFolder=False)
         pDialog.update(int((100*i)/numShows))
        pDialog.close()
        if dirty == True: self.updateAddonMeta(meta)
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

