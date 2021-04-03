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
      b = requests.get('https://api.nhk.or.jp/nhkworld/vodpglist/v7a/en/voice/list.json?apikey=EJfK8jdS57GqlupFgAfAAwr573q01y6k', headers=self.defaultHeaders).json()
      b = b['vod_programs']['programs']
      b = sorted(b.items(),key=lambda t:t[1]["sort_key"])
      for a in b:
         url = ''.join(['https://api.nhk.or.jp/nhkworld/vodesdlist/v7a/program/',a[0],'/en/all/all.json?apikey=EJfK8jdS57GqlupFgAfAAwr573q01y6k'])
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
      nhkurl = 'https://nhkwlive-fo-ojp.akamaized.net/hls/live/2003459/nhkwlive-ojp-en/index_4M.m3u8'
      html = requests.get('http://www3.nhk.or.jp/nhkworld/common/js/common.js', headers=self.defaultHeaders).text
      nw_api_prefix, nw_api_key = re.compile('nw_api_prefix\|\|"(.+?)".+?nw_api_key\|\|"(.+?)"', re.DOTALL).search(html).groups()
      nw_region = 'world'
      nw_api_prefix = nw_api_prefix.replace('nhkworldstg','nhkworld')
      url = ''.join([nw_api_prefix,'epg/v7a/',nw_region,'/now.json?apikey=',nw_api_key])
      if not url.startswith('http'):
         url = ''.join(['https:',url])
      b = requests.get(url, headers=self.defaultHeaders).json()
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
          uid = re.compile('data-src="(.+?)"', re.DOTALL).search(html).group(1)
          url = ''.join(['https://movie-s.nhk.or.jp/v/refid/nhkworld/prefid/',uid,'?embed=js&targetId=videoplayer&de-responsive=true&de-callback-method=nwCustomCallback&de-appid=',uid,'&de-subtitle-on=false'])
          html = requests.get(url, headers=self.defaultHeaders).text
          akey = re.compile("'data-de-api-key','(.+?)'", re.DOTALL).search(html).group(1)
          uuid = re.compile("'data-de-program-uuid','(.+?)'", re.DOTALL).search(html).group(1)
          a = requests.get(''.join(['https://movie-s.nhk.or.jp/ws/ws_program/api/',str(akey),'/apiv/5/mode/json?v=',str(uuid)])).json()
          b = a['response']['WsProgramResponse']['program']['asset']['referenceFile']
          if b['videoWidth'] >= 1920:
              url = a['response']['WsProgramResponse']['program']['asset']['m3u8AndroidURL']
              stream1080 = b['rtmp']['stream_name']
              stream1080 = re.compile('flvmedia/(.+?)\?', re.DOTALL).search(stream1080).group(1)
              ux = url.split('&media=',1)
              url = ''.join([ux[0],'&media=',str(b['videoBitrate']),':',stream1080,',',ux[1]])
          else:
              url = a['response']['WsProgramResponse']['program']['asset']['ipadM3u8Url']
      liz = xbmcgui.ListItem(path = url, offscreen=True)
      liz.setProperty('inputstream','inputstream.adaptive')
      liz.setProperty('inputstream.adaptive.manifest_type','hls')
      liz.setMimeType('application/x-mpegURL')
      xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)

