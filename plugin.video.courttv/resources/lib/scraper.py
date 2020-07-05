# -*- coding: utf-8 -*-
# KodiAddon (BUZZR TV Live)
#
from t1mlib import t1mAddon
import re
import requests
import urllib.parse


class myAddon(t1mAddon):

  def getAddonMenu(self,url,ilist):
      html = requests.get('https://www.courttv.com/title/court-tv-live-stream-web/', headers=self.defaultHeaders).text
      url = re.compile('&m3u8=(.+?)&', re.DOTALL).search(html).group(1)
      url = urllib.parse.unquote_plus(url)
      url = ''.join([url,'|20517|94072%7C33.5'])
      return self.getAddonListing(url, ilist)
