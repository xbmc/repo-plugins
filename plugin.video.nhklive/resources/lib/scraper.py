# -*- coding: utf-8 -*-
# KodiAddon (NHK TV Live)
#
from t1mlib import t1mAddon
import re
import xbmcplugin
import xbmc
import datetime
import sys
import xbmcgui
import requests
import urllib.parse

NHKBASE = 'https://www3.nhk.or.jp'
qp = urllib.parse.quote_plus


class myAddon(t1mAddon):

  def getAddonMenu(self,url,ilist):
      ilist = self.addMenuItem('NHK Live','GS', ilist, 'Live', self.addonIcon, self.addonFanart, {}, isFolder=True)
      b = requests.get('https://nwapi.nhk.jp/nhkworld/vodpglist/v8b/en/voice/list.json', headers=self.defaultHeaders).json()
      b = b['vod_programs']['programs']
      b = sorted(b.items(),key=lambda t:t[1]["sort_key"])
      for a in b:
         url = ''.join(['https://nwapi.nhk.jp/nhkworld/vodesdlist/v8b/program/',a[0],'/en/all/all.json'])
         a = a[1]
         name = a['title']
         thumb  =  a['image']
         if not thumb.startswith('http'): thumb  = ''.join([NHKBASE,a['image']])
         fanart =  a['image_l']
         if not fanart.startswith('http'): fanart = ''.join([NHKBASE,a['image_l']])
         infoList = {'mediatype':'tvshow',
                    'Title': name,
                    'TVShowTitle':name,
                    'Plot': a['description'],
                    'studio':'NHK'}
         contextMenu = [('Add Show To Library','RunPlugin(%s?mode=AD&url=%s)' % (sys.argv[0], qp(url)))]
         ilist = self.addMenuItem(name,'GE', ilist, url, thumb, fanart, infoList, isFolder=True, cm=contextMenu)
      return(ilist)


  def getAddonEpisodes(self,url,ilist):
      b = requests.get(url, headers=self.defaultHeaders).json()
      b = b["data"]["episodes"]
      for a in b:
         url = ''.join([NHKBASE,a['url'] ])
         name = a['sub_title_clean']
         if name == "":
             name = a['title_clean']
         thumb = a['image']
         if not thumb.startswith('http'):
             thumb  = ''.join([NHKBASE,a['image']])
         fanart = a['image_l']
         if not fanart.startswith('http'):
             fanart = ''.join([NHKBASE,a['image_l']])
         infoList = {'mediatype':'episode',
                    'Title': name,
                    'TVShowTitle': a['title_clean'],
                    'Plot': a['description_clean'],
                    'duration': a['movie_duration'],
                    'studio':'NHK'}
         dt = a.get('onair')
         if dt != None:
             aired = datetime.datetime.fromtimestamp(dt/1000)
             infoList['aired'] = aired.strftime("%Y-%m-%d")
             infoList['FirstAired'] = infoList['aired']
         ilist = self.addMenuItem(name,'GV', ilist, url, thumb, fanart, infoList, isFolder=False)
      return(ilist)


  def getAddonShows(self,url,ilist):
      nhkurl = 'https://nhkwlive-ojp.akamaized.net/hls/live/2003459/nhkwlive-ojp-en/index.m3u8'
      b = requests.get('https://nwapi.nhk.jp/nhkworld/epg/v7b/world/now.json', headers=self.defaultHeaders).json()
      for a in b['channel']['item']:
         thumb  =  a['thumbnail_s']
         if not thumb.startswith('http'): thumb  = ''.join([NHKBASE,a['thumbnail_s']])
         fanart =  a['thumbnail']
         if not fanart.startswith('http'): fanart = ''.join([NHKBASE,a['thumbnail']])
         st = datetime.datetime.fromtimestamp(int(a['pubDate'])/1000).strftime('%H:%M')
         et = datetime.datetime.fromtimestamp(int(a['endDate'])/1000).strftime('%H:%M')
         duration = (int(a['endDate'])-int(a['pubDate']))/1000
         name = ''.join([st,' - ',et,'  ',a['title']])
         infoList = {'mediatype':'episode',
                    'Title': name,
                    'duration': duration,
                    'genre': 'News',
                    'studio':'NHK'}
         infoList['Plot']  = ''.join([st,' - ',et,'        ',str(duration/60),' min.\n',a['subtitle'],'\n',a['description'],'\n',a['content']])
         ilist = self.addMenuItem(name,'GV', ilist, nhkurl, thumb, fanart, infoList, isFolder=False)
      return(ilist)


  def getAddonVideo(self,url):
      if not url.endswith('.m3u8'):
          html = requests.get(url, headers=self.defaultHeaders).text
          datakey = re.compile('data-key="(.+?)"', re.DOTALL).search(html).group(1)
          url = ''.join(['https://nwapi.nhk.jp/nhkworld/vodesdlist/v7b/episode/',datakey,'/en/all/all.json'])
          a = requests.get(url, headers=self.defaultHeaders).json()
          uid = a['data']['episodes'][0]['vod_id']
          html = requests.get('https://movie-a.nhk.or.jp/world/player/js/movie-player.js', headers=self.defaultHeaders).text
          token = re.compile('prod:.+?token:"(.+?)"', re.DOTALL).search(html).group(1)
          url = ''.join(['https://api01-platform.stream.co.jp/apiservice/getMediaByParam/?token=',token,'&type=json&optional_id=',uid,'&active_flg=1'])
          a = requests.get(url, headers=self.defaultHeaders).json()
          url = a['meta'][0]["movie_url"]["mb_hd"]

      liz = xbmcgui.ListItem(path = url, offscreen=True)
      liz.setProperty('inputstream','inputstream.adaptive')
      liz.setProperty('inputstream.adaptive.manifest_type','hls')
      liz.setMimeType('application/x-mpegURL')
      xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)

