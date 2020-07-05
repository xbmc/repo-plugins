# -*- coding: utf-8 -*-
# KodiAddon (LIGHTtv Live)
#
from t1mlib import t1mAddon
import re
import requests

class myAddon(t1mAddon):

  def getAddonMenu(self,url,ilist):
      html = requests.get('https://lighttv.com/watch-now/', headers=self.defaultHeaders).text
      url = re.compile('<iframe id="iframe-player".+?src="(.+?)"', re.DOTALL).search(html).group(1)
      url = url.split('tokens=',1)[1]
      url = ''.join(['https://mgmlight.akamaized.net/hls/live/2009506/mgmlight/master.m3u8?',url])
      html = requests.get(url, headers=self.defaultHeaders).text
      url = re.compile('hdntl=(.+?)\.m3u8', re.DOTALL).findall(html)
      url = ''.join(['https://mgmlight.akamaized.net/hls/live/2009506/mgmlight/hdntl=',url[-1],'.m3u8'])
      url = ''.join([url,'|20517|86071%7C5.4'])
      return self.getAddonListing(url, ilist)
