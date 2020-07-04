# -*- coding: utf-8 -*-
# KodiAddon (Adultswim)
#
from t1mlib import t1mAddon
import json
import re
import xbmcplugin
import xbmcgui
import sys
import xbmc
import requests

ASBASE = 'https://www.adultswim.com/'

class myAddon(t1mAddon):

  def getAddonMenu(self,url,ilist):
      html = requests.get(''.join([ASBASE,'/videos']), headers=self.defaultHeaders).text
      html = re.compile('type="application/json">(.+?)</script>', re.DOTALL).search(html).group(1)
      a = json.loads(html)
      for b in a['props']['pageProps']['shows']:
         name = b['title']
         url = b['url']
         thumb = b['poster']
         fanart = thumb
         infoList = {'mediatype':'tvshow',
                     'TVShowTitle': name,
                     'Title': name,
                     'Plot': name}
         ilist = self.addMenuItem(name,'GE', ilist, url, thumb, fanart, infoList, isFolder=True)
      return(ilist)

  def getAddonEpisodes(self,url,ilist):
      html = requests.get(''.join([ASBASE,url]), headers=self.defaultHeaders).text
      html = re.compile('"application/json">(.+?)</script>', re.DOTALL).search(html).group(1)
      a = json.loads(html)
      x = a["props"]["pageProps"]["__APOLLO_STATE__"].keys()
      for b in x:
          if b.startswith("Video:"):
            b = a["props"]["pageProps"]["__APOLLO_STATE__"][b]
            if b.get('auth',True) == False:
              name = b['title']
              thumb = b.get('poster')
              fanart = thumb
              url = b['id']
              infoList = {'mediatype':'episode',
                          'Title': name,
                          'TVShowTitle': xbmc.getInfoLabel('ListItem.TVShowTitle'),
                          'Plot': b.get('description'),
                          'Duration': b.get('duration'),
                          'MPAA': b.get('tvRating'),
                          'Episode': b.get('episodeNumber'),
                          'Premiered': b.get('launchDate').split('T',1)[0]}
              ilist = self.addMenuItem(name,'GV', ilist, url, thumb, fanart, infoList, isFolder=False)
      return(ilist)


  def getAddonVideo(self,url):
      a = requests.get(''.join([ASBASE,'api/shows/v1/videos/',url,'?fields=title%2Ctype%2Cduration%2Ccollection_title%2Cposter%2Cstream%2Csegments%2Ctitle_id']), headers=self.defaultHeaders).json()
      for b in a['data']['video']['stream']['assets']:
          if (b.get('mime_type') == 'application/x-mpegURL') and (b.get('url').endswith('stream_full.m3u8') or b.get('url').endswith('/stream.m3u8') ):
              liz = xbmcgui.ListItem(path = b.get('url'), offscreen=True)
              liz.setProperty('inputstream','inputstream.adaptive')
              liz.setProperty('inputstream.adaptive.manifest_type','hls')
              liz.setMimeType('application/x-mpegURL')
              xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)
