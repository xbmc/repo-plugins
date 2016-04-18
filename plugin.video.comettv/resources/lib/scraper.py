# -*- coding: utf-8 -*-
# KodiAddon (Comet TV Live)
#
from t1mlib import t1mAddon
import json
import re
import urllib
import xbmcplugin
import xbmcgui
import calendar
import datetime
import sys

UTF8 = 'utf-8'

class myAddon(t1mAddon):

  def getAddonMenu(self,url,ilist):
      xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
      self.defaultVidStream['width']  = 960
      self.defaultVidStream['height'] = 540
      html = self.getRequest('http://comettv.com/watch-live/')
      url = re.compile('file: "(.+?)"', re.DOTALL).search(html).group(1)
      thumb  = self.addonIcon
      fanart = self.addonFanart
      d = datetime.datetime.utcnow()
      now = calendar.timegm(d.utctimetuple())
      html = self.getRequest('http://mobilelistings.tvguide.com/Listingsweb/ws/rest/airings/20405/start/'+str(now)+'/duration/20160?channelsourceids=74313%7C62.4&formattype=json')
      a = json.loads(html)
      for b in a[:10]:
         infoList = {}
         b = b['ProgramSchedule']
         st = datetime.datetime.fromtimestamp(float(b['StartTime'])).strftime('%H:%M')
         et = datetime.datetime.fromtimestamp(float(b['EndTime'])).strftime('%H:%M')
         infoList['duration'] = int(float(b['EndTime']) - float(b['StartTime']))
         name = b['Title']
         if b['EpisodeTitle'] != '':
            infoList['TVShowTitle'] = name
            try: infoList['Season'] = int(b['TVObject']['SeasonNumber'])
            except: pass
            try: infoList['Episode'] = int(b['TVObject']['EpisodeNumber'])
            except: pass
         plot = '%s - %s                 %s min.\n[COLOR blue]%s[/COLOR]\n%s' % (st, et, infoList['duration'] / 60,  b['EpisodeTitle'], b['CopyText'])
         infoList['Plot'] = plot
         try: infoList['MPAA'] = b['Rating']
         except: pass
         ilist = self.addMenuItem(name,'GV', ilist, url, thumb, fanart, infoList, isFolder=False)
      return(ilist)

  def getAddonVideo(self,url):
      liz = xbmcgui.ListItem(path = url)
      xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)






