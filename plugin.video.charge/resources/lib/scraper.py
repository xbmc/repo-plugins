# -*- coding: utf-8 -*-
# KodiAddon (Charge! TV Live)
#
from t1mlib import t1mAddon
import re
import requests

class myAddon(t1mAddon):

  def getAddonMenu(self,url,ilist):
      html = requests.get('https://watchcharge.com/watch-live/', headers=self.defaultHeaders).text
      url = re.compile('file: "(.+?)"', re.DOTALL).search(html).group(1)
      url = ''.join([url,'|20534|35794%7C23.2'])
      return self.getAddonListing(url, ilist)
