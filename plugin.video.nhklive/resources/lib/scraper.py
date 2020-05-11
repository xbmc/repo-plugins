# -*- coding: utf-8 -*-
# KodiAddon (NHK TV Live)
#
from t1mlib import t1mAddon
import json
import re
import urllib
import xbmcplugin
import xbmc
import calendar
import datetime
import sys
import xbmcgui

UTF8 = 'utf-8'
NHKBASE = 'https://www3.nhk.or.jp/%s'

class myAddon(t1mAddon):


  def getAddonMenu(self,url,ilist):
      infoList = {}
      ilist = self.addMenuItem('NHK Live','GS', ilist, url, self.addonIcon, self.addonFanart, infoList, isFolder=True)
      html = self.getRequest('https://api.nhk.or.jp/nhkworld/vodpglist/v7a/en/voice/list.json?apikey=EJfK8jdS57GqlupFgAfAAwr573q01y6k')
      b = json.loads(html)
      b = b['vod_programs']['programs']
      b = sorted(b.items(),key=lambda t:t[1]["sort_key"])
      for a in b:
         infoList = {}
         url = 'https://api.nhk.or.jp/nhkworld/vodesdlist/v7a/program/'+a[0]+'/en/all/all.json?apikey=EJfK8jdS57GqlupFgAfAAwr573q01y6k'
         a = a[1]
         plot = a['description']
         name = a['title']
         thumb  =  a['image']
         if not thumb.startswith('http'): thumb  = NHKBASE % a['image']
         fanart =  a['image_l']
         if not fanart.startswith('http'): fanart = NHKBASE % a['image_l']
         infoList['Title'] = name
         infoList['Plot']  = plot
         infoList['mediatype'] = 'tvshow'
         infoList['studio'] = 'NHK'
         ilist = self.addMenuItem(name,'GE', ilist, url, thumb, fanart, infoList, isFolder=True)
      return(ilist)

  def getAddonEpisodes(self,url,ilist):
      html = self.getRequest(url)
      b = json.loads(html)
      b = b["data"]["episodes"]
      for a in b:
         infoList = {}
         url = NHKBASE % a['url'] 
         plot = a['description_clean']
         name = a['sub_title_clean']
         if name == "":
             name = a['title_clean']
         thumb = a['image']
         if not thumb.startswith('http'):
             thumb  = NHKBASE % a['image']
         fanart = a['image_l']
         if not fanart.startswith('http'):
             fanart = NHKBASE % a['image_l']
         infoList['Title'] = name
         infoList['TVShowTitle'] = a['title_clean']
         infoList['duration'] = a['movie_duration']
         dt = a.get('onair')
         if dt != None:
             aired = datetime.datetime.fromtimestamp(dt/1000)
             infoList['aired'] = aired.strftime("%Y-%m-%d")
         infoList['Plot']  = plot
         infoList['studio'] = 'NHK'
         infoList['mediatype'] = 'episode'
         ilist = self.addMenuItem(name,'GV', ilist, url, thumb, fanart, infoList, isFolder=False)
      return(ilist)




  def getAddonShows(self,url,ilist):
      xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
      nhkurl = 'https://nhkwlive-ojp.akamaized.net/hls/live/2003459/nhkwlive-ojp/index_4M.m3u8'
      html = self.getRequest('http://www3.nhk.or.jp/nhkworld/common/js/common.js')
      nw_api_prefix, nw_api_key = re.compile('nw_api_prefix\|\|"(.+?)".+?nw_api_key\|\|"(.+?)"', re.DOTALL).search(html).groups()
      nw_region = 'world'
      nw_api_prefix = nw_api_prefix.replace('nhkworldstg','nhkworld')
      url = nw_api_prefix + 'epg/v7a/' + nw_region + '/now.json' + '?apikey=' + nw_api_key
      if not url.startswith('http'):
         url = 'https:' + url
      html = self.getRequest(url)
      b = json.loads(html)
      for a in b['channel']['item']:
         infoList = {}
         plot = a['description']
         content = a['content']
         name = a['title']
         thumb  =  a['thumbnail_s']
         if not thumb.startswith('http'): thumb  = NHKBASE % a['thumbnail_s']
         fanart =  a['thumbnail']
         if not fanart.startswith('http'): fanart = NHKBASE % a['thumbnail']
         subtitle = a['subtitle']
         st = datetime.datetime.fromtimestamp(int(a['pubDate'])/1000).strftime('%H:%M')
         et = datetime.datetime.fromtimestamp(int(a['endDate'])/1000).strftime('%H:%M')
         duration = (int(a['endDate'])-int(a['pubDate']))/1000
         infoList['Plot']  = st +' - '+ et + '        ' + str(duration/60) + ' min.\n' + subtitle + '\n'+ plot +'\n'+content
         name = st +' - '+ et + '  ' + name
         infoList['Title'] = name
         infoList['duration'] = duration
         infoList['genre'] = 'News'
         infoList['mediatype'] = 'episode'
         infoList['studio'] = 'NHK'
         ilist = self.addMenuItem(name,'GV', ilist, nhkurl, thumb, fanart, infoList, isFolder=False)
      return(ilist)

  def getAddonVideo(self,url):
   if not url.endswith('.m3u8'):
     html = self.getRequest(url)
     uid = re.compile('data-src="(.+?)"', re.DOTALL).search(html).group(1)
     url = 'https://movie-s.nhk.or.jp/v/refid/nhkworld/prefid/'+uid+'?embed=js&targetId=videoplayer&de-responsive=true&de-callback-method=nwCustomCallback&de-appid='+uid+'&de-subtitle-on=false'
     html = self.getRequest(url)
     akey = re.compile("'data-de-api-key','(.+?)'", re.DOTALL).search(html).group(1)
     uuid = re.compile("'data-de-program-uuid','(.+?)'", re.DOTALL).search(html).group(1)
     html = self.getRequest('https://movie-s.nhk.or.jp/ws/ws_program/api/'+akey+'/apiv/5/mode/json?v='+uuid)
     a = json.loads(html)
     url = a['response']['WsProgramResponse']['program']['asset']['ipadM3u8Url']
   liz = xbmcgui.ListItem(path = url)
   liz.setMimeType('application/x-mpegURL')
   xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)

