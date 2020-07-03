# -*- coding: utf-8 -*-
# ConTV Kodi Video Addon
#
from t1mlib import t1mAddon
import re
import xbmc
import xbmcplugin
import xbmcgui
import sys
import requests


class myAddon(t1mAddon):

  def getAddonMenu(self,url,ilist):
      ilist = self.addMenuItem('Live TV','GV', ilist, 'livetv', self.addonIcon, self.addonFanart, {}, isFolder=False)
      a = requests.get('https://contv-metax.service.junctiontv.net/metax/2.5/shelf/nav/newgenres/NO_SUB?allowBook=true&jloc=us', headers=self.defaultHeaders).json()
      a = a["subCategories"]
      for b in a[:-1]:
          if b["title_type"] == 'video':
              url = b["url"]
              infoList ={}
              infoList['Title'] = b["name"]
              infoList['TVShowTitle'] = b["name"]
              infoList['mediatype'] = 'tvshow'
              ilist = self.addMenuItem(b["name"],'GS', ilist, url, self.addonIcon, self.addonFanart, infoList, isFolder=True)
      return(ilist)

  def getAddonShows(self,url,ilist):
      a = requests.get(url, headers=self.defaultHeaders).json()
      for b in a:
          url = b["id"]
          name = b["title"]
          thumb = b.get("thumbnail")
          fanart = b.get(u"thumb_high")
          infoList ={}
          infoList['Title'] = name
          infoList['TVShowTitle'] = name
          infoList['Plot'] = b.get("description")
          if b["type"] == 'vod':
              infoList['mediatype'] = 'movie'
              ilist = self.addMenuItem(name,'GV', ilist, url, thumb, fanart, infoList, isFolder=False)
          elif b["type"] == 'episodic':
              infoList['mediatype'] = 'tvshow'
              ilist = self.addMenuItem(name,'GE', ilist, url, thumb, fanart, infoList, isFolder=True)
      return(ilist)
      
  def getAddonEpisodes(self,url,ilist):
      a = requests.get(''.join(['https://contv-metax.service.junctiontv.net/metax/2.5/seriesfeed/json/',url,'?device=web&subid=__JTV__SUBSCRIBER__ID__&jloc=us']), headers=self.defaultHeaders).json()
      for b in a:
          season = int(b["season"])
          for c in b["episodes"]:
             url = c["id"]
             name = c["title"]
             thumb = c.get("thumbnail")
             fanart = thumb
             infoList ={}
             infoList["Season"] = season
             infoList["Episode"] = c["episode"]
             infoList['Title'] = name
             infoList['TVShowTitle'] = xbmc.getInfoLabel('ListItem.TVShowTitle')
             infoList['Plot'] = c.get("description")
             infoList['mediatype'] = 'episode'
             ilist = self.addMenuItem(name,'GV', ilist, url, thumb, fanart, infoList, isFolder=False)
      return(ilist)


  def getAddonVideo(self,url):
      a = requests.get(''.join(['https://contv-metax.service.junctiontv.net/metax/3.1/media/',url,'?subid=NO_SUB&subtype=free&dev_id=&dev_type=web&device_cat=web&jloc=us']), headers=self.defaultHeaders).json()
      url = a["url"].replace("main.m3u8","4300.m3u8")
      liz = xbmcgui.ListItem(path = url, offscreen=True)
      liz.setSubtitles([a.get("subtitle_url")])
      liz.setProperty('inputstream','inputstream.adaptive')
      liz.setProperty('inputstream.adaptive.manifest_type','hls')
      liz.setMimeType('application/x-mpegURL')
      xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)

