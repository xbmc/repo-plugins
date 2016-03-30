# -*- coding: utf-8 -*-
# KodiAddon (NHK TV Live)
#
from t1mlib import t1mAddon
import json
import re
import urllib
import xbmcplugin
import calendar
import datetime
import sys
import xml.etree.ElementTree as ET

UTF8 = 'utf-8'

class myAddon(t1mAddon):


  def getAddonMenu(self,url,ilist):
      xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
      html = self.getRequest('http://www3.nhk.or.jp/nhkworld/app/tv/hlslive_tv.xml')
      root = ET.fromstring(html)
      a ={}
      for utype in root:
          a[utype.tag] = {}
          for url in utype:
              a[utype.tag][url.tag] = url.text
      nhkurl = a['tv_url']['wstrm']

      html = self.getRequest('http://www3.nhk.or.jp/nhkworld/common/js/common.js')
      nw_api_prefix, nw_api_key = re.compile("nw_api_prefix = '(.+?)'.+?nw_api_key = '(.+?)'", re.DOTALL).search(html).groups()
      nw_region = 'world'
      url = nw_api_prefix + 'epg/v3/' + nw_region + '/now.json' + '?apikey=' + nw_api_key
      html = self.getRequest(url)
      b = json.loads(html)
      for a in b['channel']['item']:
         infoList = {}
         plot = a['description']
         content = a['content']
         name = a['title']
         thumb  = a['thumbnail_s']
         fanart = a['thumbnail']
         subtitle = a['subtitle']
         genre = a['genre']['TV']
         infoList['Title'] = name
         st = datetime.datetime.fromtimestamp(int(a['pubDate'])/1000).strftime('%H:%M')
         et = datetime.datetime.fromtimestamp(int(a['endDate'])/1000).strftime('%H:%M')
         duration = (int(a['endDate'])-int(a['pubDate']))/1000
         infoList['Plot']  = st +' - '+ et + '        ' + str(duration/60) + ' min.\n' + subtitle + '\n'+ plot +'\n'+content
         infoList['duration'] = duration
         infoList['genre'] = genre
         ilist = self.addMenuItem(name,'GV', ilist, nhkurl, thumb, fanart, infoList, isFolder=False)
      return(ilist)
