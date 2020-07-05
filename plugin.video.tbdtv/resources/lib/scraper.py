# -*- coding: utf-8 -*-
# KodiAddon (TBD TV Live)
#
from t1mlib import t1mAddon
import re
import requests

class myAddon(t1mAddon):

  def getAddonMenu(self,url,ilist):
      html = requests.get('https://tbd.com/live', headers=self.defaultHeaders).text
      url = re.compile("'file':"+' "(.+?)"', re.DOTALL).search(html).group(1)
      url = ''.join([url,'|20534|17075%7C13.2'])
      return self.getAddonListing(url, ilist)
