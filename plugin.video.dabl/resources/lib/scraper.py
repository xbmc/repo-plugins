# -*- coding: utf-8 -*-
# KodiAddon (DABL Network Live)
#
from t1mlib import t1mAddon
import re
import requests

class myAddon(t1mAddon):

  def getAddonMenu(self,url,ilist):
      html = requests.get('https://www.dabl.com/schedule', headers=self.defaultHeaders).text
      url = re.compile('"streamUrl":"(.+?)"', re.DOTALL).search(html).group(1)
      url = ''.join([url,'|20517|95048%7C2.3'])
      return self.getAddonListing(url, ilist)
