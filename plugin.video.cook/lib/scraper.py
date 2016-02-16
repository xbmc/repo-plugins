# -*- coding: utf-8 -*-
# Cooking Channel Kodi Video Addon
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
     addonLanguage  = self.addon.getLocalizedString
     meta = self.getAddonMeta()
     try:    i = len(meta['shows'])
     except: meta['shows']={}
     html = self.getRequest('http://www.cookingchanneltv.com/videos/full-episodes-player.html')
     a = re.compile('<li id="/content/.+?href="(.+?)">(.+?)<.+?<span>\((.+?)\)<.+?</li>',re.DOTALL).findall(html)
     pDialog = xbmcgui.DialogProgress()
     pDialog.create(self.addonName, addonLanguage(30101))
     pDialog.update(0)
     dirty = False
     numShows = len(a)
     for i, (xurl,name, vidcnt) in list(enumerate(a, start=1)):
      try:
        (name, url, thumb, fanart, infoList) = meta['shows'][xurl]
      except:
       dirty = True
       durl = xurl
       if '/videos' in durl:
          durl = durl.replace('/videos','/shows').replace('all-of-','').replace('-2','').replace('-full-episodes','')
       else:
          durl = durl.rsplit('/',1)[0]+'.html'
       durl = durl.replace('chuck-s','chucks').replace('-suppers1','-suppers')
       durl = 'http://www.cookingchanneltv.com%s' % durl
       url = 'http://www.cookingchanneltv.com%s' % xurl
       name=name.strip()
       html = self.getRequest(durl)
       fanart  = self.addonFanart
       try:    plot, thumb = re.compile('"og:description" content="(.+?)".+?"og:image" content="(.+?)"',re.DOTALL).search(html).groups()
       except: 
              plot = name
              thumb = self.addonIcon
       infoList = {}
       infoList['TVShowTitle'] = name
       infoList['Title']       = name
       infoList['Studio']      = addonLanguage(30010)
       infoList['Genre']       = ''
       try:    infoList['Episode'] = int(vidcnt)
       except: infoList['Episode'] = 0
       infoList['Plot'] = h.unescape(plot)
       meta['shows'][xurl] = (name, url, thumb, fanart, infoList)
      ilist = self.addMenuItem(name,'GE', ilist, url+'|'+name, thumb, fanart, infoList, isFolder=True)
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
        html = self.getRequest(gcurl)
        vids  = re.compile("data\-video='(.+?)'",re.DOTALL).findall(html)
        pDialog = xbmcgui.DialogProgress()
        pDialog.create(self.addonName, addonLanguage(30101))
        pDialog.update(0)
        numShows = len(vids)
        dirty = False
        for i,c in list(enumerate(vids, start=1)):
         try: 
            b = json.loads(c)
            url     = b['releaseUrl']
         except: continue
         try:
           (name, url, thumb, fanart, infoList) = meta[sname][url]
         except:
           dirty = True
           name    = h.unescape(b['title'])
           thumb   = b['thumbnailUrl'].replace('92x69.jpg','480x360.jpg')
           fanart = thumb
           infoList = {}
           infoList['Duration']    = b['length']
           infoList['Title']       = h.unescape(b['title'])
           infoList['Studio']      = b['publisherId']
           html = self.getRequest(url)
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
           meta[sname][url] = (name, url, thumb, fanart, infoList)
         try: ilist = self.addMenuItem(name,'GV', ilist, url, thumb, fanart, infoList, isFolder=False)
         except: pass
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
   try:
     url   = re.compile('<video src="(.+?)"',re.DOTALL).search(html).group(1)
   except:
     url, msg   = re.compile('<ref src="(.+?)".+?abstract="(.+?)"',re.DOTALL).search(html).groups()
     xbmc.executebuiltin('XBMC.Notification("%s", "%s", %s)' % ( self.addonName, msg , 5000) )
     return

   liz = xbmcgui.ListItem(path = url)
   if suburl != "" : liz.setSubtitles([suburl])
   xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)

