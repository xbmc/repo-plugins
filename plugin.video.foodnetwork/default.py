# -*- coding: utf-8 -*-
# Food Network Kodi Video Addon
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

h = HTMLParser.HTMLParser()
qp  = urllib.quote_plus
uqp = urllib.unquote_plus
UTF8     = 'utf-8'


class myAddon(t1mAddon):

  def getAddonMenu(self,url,ilist):
     addonLanguage  = self.addon.getLocalizedString
     meta = self.getAddonMeta()
     try:    i = len(meta['shows'])
     except: meta['shows']={}
     html = self.getRequest('http://www.foodnetwork.com/videos/players/food-network-full-episodes.vc.html')
     m = re.compile('<section class="multichannel-component">(.+?)</section', re.DOTALL).search(html)
     a = re.compile('<a href="(.+?)".+?data-max="35">(.+?)<.+?</div', re.DOTALL).findall(html,m.start(1),m.end(1))
     pDialog = xbmcgui.DialogProgress()
     pDialog.create(self.addonName, addonLanguage(30101))
     pDialog.update(0)
     dirty = False
     numShows = len(a)
     fanart = self.addonFanart
     for i, (xurl,name) in list(enumerate(a, start=1)):
      name = name.decode(UTF8)
      try:
        (name, url, thumb, fanart, infoList) = meta['shows'][xurl]
      except:
       url = xurl
       infoList={}
       dirty = True
       url = 'http://www.foodnetwork.com%s' % url
       name=name.strip()
       html = self.getRequest(url)
       try:    html1  = re.compile('"channels":\[(.+?)\]\},', re.DOTALL).search(html).group(1)
       except: html1  = re.compile('"channels": \[(.+?)\]\},', re.DOTALL).search(html).group(1)
       html1  = '{"channels": ['+html1+']}'
       a = json.loads(html1)
       a = a['channels'][0]
       try: thumb = a['videos'][0]['thumbnailUrl16x9'].replace('126x71.jpg','480x360.jpg')
       except: thumb = icon
       meta['shows'][xurl] = (name, url, thumb, fanart, infoList)
      try: ilist = self.addMenuItem(name,'GE', ilist, url+'|'+name, thumb, fanart, infoList, isFolder=True)
      except: 
           ilist = self.addMenuItem(name,'GE', ilist, url+'|'+' ', thumb, fanart, infoList, isFolder=True)
      pDialog.update(int((100*i)/numShows))
     pDialog.close()
     if dirty == True: self.updateAddonMeta(meta)
     return(ilist)


  def getAddonEpisodes(self,url,ilist):
        addonLanguage  = self.addon.getLocalizedString
        self.defaultVidStream['width']  = 1280
        self.defaultVidStream['height'] = 720
        gcurl = uqp(url)
        gcurl, showName = gcurl.split('|',1)
        meta  = self.getAddonMeta()
        sname = gcurl
        try:  i = len(meta[sname])
        except:
              meta[sname]={}

        html  = self.getRequest(gcurl)
        try:    html  = re.compile('"channels":\[(.+?)\]\},', re.DOTALL).search(html).group(1)
        except: html  = re.compile('"channels": \[(.+?)\]\},', re.DOTALL).search(html).group(1)
        html  = '{"channels": ['+html+']}'
        a = json.loads(html)
        vids = a['channels'][0]['videos']

        pDialog = xbmcgui.DialogProgress()
        pDialog.create(self.addonName, addonLanguage(30101))
        pDialog.update(0)
        numShows = len(vids)
        dirty = False
        for i,b in list(enumerate(vids, start=1)):
         url     = b['releaseUrl']
         try:
           (name, url, thumb, fanart, infoList) = meta[sname][url]
         except:
           dirty = True
           name    = h.unescape(b['title'])
           thumb   = b['thumbnailUrl16x9'].replace('126x71.jpg','480x360.jpg')
           fanart  = thumb
           infoList = {}
           infoList['Duration']    = b['length']
           infoList['Title']       = h.unescape(b['title'])
           infoList['Studio']      = 'The Food Network'
           html = self.getRequest(url)
           months = {'Jan':'01','Feb':'02','Mar':'03','Apr':'04','May':'05','Jun':'06','Jul':'07','Aug':'08','Sep':'09','Oct':'10','Nov':'11','Dec':'12'}
           try:
              dstr = (re.compile('"premierDate" value="(.+?)"',re.DOTALL).search(html).group(1)).split(' ')
              dt   = '%s-%s-%s' % (dstr[5],months[dstr[1]],dstr[2])
              infoList['Date']        = dt
              infoList['Aired']       = infoList['Date']
           except: pass
           try:    infoList['MPAA'] = re.compile('ratings="(.+?)"',re.DOTALL).search(html).group(1).split(':',1)[1]
           except: pass
           try:    infoList['Episode'] = int(re.compile('"episodeNumber" value="..(.+?)H"',re.DOTALL).search(html).group(1), 16)
           except: infoList['Episode'] = None
           try:    infoList['Season']  = int(re.compile('"episodeNumber" value="(.+?)H"',re.DOTALL).search(html).group(1),16)/256
           except: infoList['Season']  = 1
           infoList['Plot']        = h.unescape(b["description"])
           infoList['TVShowTitle'] = showName
           meta[sname][url] = (name, url, thumb, fanart, infoList)
         try: ilist = self.addMenuItem(name,'GV', ilist, url, thumb, fanart, infoList, isFolder=False)
         except: continue
         pDialog.update(int((100*i)/numShows))
        pDialog.close()
        if dirty == True: self.updateAddonMeta(meta)
        return(ilist)


  def getAddonVideo(self,url):
   html   = self.getRequest(uqp(url))
   suburl =''
   try:    
           subs = re.compile('<textstream src="(.+?)"',re.DOTALL).findall(html)
           for st in subs:
             if '.srt' in st:
                suburl = st
                break
   except: pass

   url   = re.compile('<video src="(.+?)"',re.DOTALL).search(html).group(1)
   url = url.replace('_3.','_6.')
   req = urllib2.Request(url.encode(UTF8), None, self.defaultHeaders)
   try:
     response = urllib2.urlopen(req, timeout=20)
   except:
     url = url.replace('_6.','_5.')


   liz = xbmcgui.ListItem(path = url)
   if suburl != "" : liz.setSubtitles([suburl])
   xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)



# Start of Module

addonName = re.search('plugin\://plugin.video.(.+?)/',str(sys.argv[0])).group(1)
ma = myAddon(addonName)
ma.processAddonEvent()
del myAddon

