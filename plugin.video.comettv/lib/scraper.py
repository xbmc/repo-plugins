# -*- coding: utf-8 -*-
# KodiAddon (Comet TV Live)
#
from t1mlib import t1mAddon
import json
import re
import urllib
import xbmcplugin
import calendar
import datetime
import sys

UTF8 = 'utf-8'

class myAddon(t1mAddon):

  def getAddonMenu(self,url,ilist):
      xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
      html = self.getRequest('http://comettv.com/live.html')
      url = re.compile('file: "(.+?)"', re.DOTALL).search(html).group(1)
      infoList = {}
      thumb  = self.addonIcon
      fanart = self.addonFanart
      d = datetime.datetime.utcnow()
      now = calendar.timegm(d.utctimetuple())
      html = self.getRequest('http://mobilelistings.tvguide.com/Listingsweb/ws/rest/airings/20405/start/'+str(now)+'/duration/20160?channelsourceids=74313%7C62.4&formattype=json')
      a = json.loads(html)
      st = datetime.datetime.fromtimestamp(float(a[0]['ProgramSchedule']['StartTime'])).strftime('%H:%M')
      et = datetime.datetime.fromtimestamp(float(a[0]['ProgramSchedule']['EndTime'])).strftime('%H:%M')
      infoList['Title'] = a[0]['ProgramSchedule']['Title']
      plot = '%s - %s\n%s' % (st, et, a[0]['ProgramSchedule']['CopyText'])
      infoList['Plot'] = plot
      ilist = self.addMenuItem('Comet TV Live','GV', ilist, url, thumb, fanart, infoList, isFolder=False)
      return(ilist)
