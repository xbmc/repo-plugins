# -*- coding: utf-8 -*-
# KodiAddon (Comet TV Live)
#
from t1mlib import t1mAddon
import re
import requests

class myAddon(t1mAddon):

  def getAddonMenu(self,url,ilist):
      html = requests.get('https://comettv.com/watch-live/', headers=self.defaultHeaders).text
      url = re.compile('	file: "(.+?)"', re.DOTALL).search(html).group(1)
      url = ''.join([url,'|20517|77239%7C38.3'])
      return self.getAddonListing(url, ilist)
