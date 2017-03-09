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

UTF8     = 'utf-8'

class myAddon(t1mAddon):

  def getAddonMenu(self,url,ilist):
      pg = self.getRequest('http://pbskids.org/pbsk/video/api/getShows/?callback=&destination=national&return=images')
      pg = pg.strip('()')
      a = json.loads(pg)
      a = a.get('items')
      for b in a:
          name = b.get('title','no title')
          url = 'http://pbskids.org/pbsk/video/api/getVideos/?startindex=1&endindex=200&program=%s&type=episode&category=&group=&selectedID=&status=available&player=flash&flash=true' % (urllib.quote(name))
          thumb = b.get('images',{'x':None}).get('program-kids-square',{'x':None}).get('url', self.addonIcon)
          infoList = {}
          infoList['Title'] = name
          infoList['TVShowTitle'] = name
          infoList['Plot']  = b.get('description')
          infoList['mediatype'] = 'tvshow'
          ilist = self.addMenuItem(name,'GE', ilist, url, thumb, self.addonFanart, infoList, isFolder=True)
      return(ilist)


  def getAddonEpisodes(self,url,ilist):
      pg = self.getRequest(url)
      a = json.loads(pg)
      a = a.get('items')
      for b in a:
          url = b.get('videos',{'x':None}).get('flash',{'x':None})
          url = url.get('mp4-2500k',url.get('mp4-1200k',url)).get('url')
          if not url is None:
              name = b.get('title','no title')
              thumb  = b.get('images',{'x':None}).get('kids-mezzannine-16x9',{'x':None}).get('url', self.addonIcon)
              fanart  = b.get('images',{'x':None}).get('kids-mezzannine-16x9',{'x':None}).get('url', self.addonFanart)
              captions = b.get('captions',{'x':None}).get('srt',{'x':None}).get('url','')
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
          url = url.split(':videos/',1)
          if len(url) > 1:
              url = 'http://kids.video.cdn.pbs.org/videos/%s' % url[1]
              liz = xbmcgui.ListItem(path = url)
              if len(captions) > 0:
                  liz.setSubtitles([captions])
              xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)