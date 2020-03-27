# -*- coding: utf-8 -*-
# KodiAddon PBSKids
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
import sys
import HTMLParser

h = HTMLParser.HTMLParser()
UTF8 = 'utf-8'


class myAddon(t1mAddon):

  def getAddonMenu(self,url,ilist):
      html = self.getRequest('https://content.services.pbskids.org/v2/kidspbsorg/home/?imgsizes=showLogo:88x88,showLogoSquare:100x100')
      a = json.loads(html)
      a = a["collections"]
      b = a["kids-programs-tier-1"]["content"]
      b.extend(a["kids-programs-tier-2"]["content"])
      b.extend(a["kids-programs-tier-3"]["content"])
      for c in b:
          name = c["title"]
          url = c["slug"]
          thumb = c["images"]["mezzanine_16x9"]
          fanart = c["images"]["background"]
          infoList = {}
          infoList['Title'] = name
          infoList['Plot'] = name
          infoList['TVShowTitle'] = name
          infoList['mediatype'] = 'tvshow'
          ilist = self.addMenuItem(name,'GE', ilist, url, thumb, fanart, infoList, isFolder=True)
      return(ilist)


  def getAddonEpisodes(self,url,ilist):
      html = self.getRequest('https://content.services.pbskids.org/v2/kidspbsorg/programs/'+url+'?imgsizes=showLogo:88x88,showLogoSquare:100x100')
      a = json.loads(html)
      a = a['collections']['episodes']['content']
      for b in a:
          url = b.get('mp4')
          if not url is None:
              name = b.get('title','no title')
              thumb  = b.get('images',{'x':None}).get('mezzanine', self.addonIcon)
              fanart  = b.get('images',{'x':None}).get('mezzanine', self.addonFanart)
              c = b.get('closedCaptions',[])
              captions = ''
              for d in c:
                 if d.get('format') == 'SRT':
                     captions = d.get('URI','')
                     break
              infoList={}
              infoList['Title'] = name
              infoList['TVShowTitle'] = xbmc.getInfoLabel('ListItem.TVShowTitle')
              infoList['Plot']  = b.get('description')
              infoList['mediatype'] = 'episode'
              ilist = self.addMenuItem(name,'GV', ilist, url+'|'+captions, thumb, fanart, infoList, isFolder=False)
      return(ilist)


  def getAddonVideo(self,url):
      url, captions = url.split('|',1)
      html = self.getRequest('%s?format=json' % url)
      a = json.loads(html)
      url = a.get('url')
      if url is not None:
              liz = xbmcgui.ListItem(path = url)
              if len(captions) > 0:
                  liz.setSubtitles([captions])
              xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)