# -*- coding: utf-8 -*-
# KodiAddon (BUZZR TV Live)
#
from t1mlib import t1mAddon
import re
import requests

class myAddon(t1mAddon):

  def getAddonMenu(self,url,ilist):
      html = requests.get('https://buzzrtv.com/watch', headers=self.defaultHeaders).text
      url = re.compile('<source src="(.+?)"', re.DOTALL).search(html).group(1)
      url = ''.join([url,'|20517|35211%7C9.3'])
      return self.getAddonListing(url, ilist)
