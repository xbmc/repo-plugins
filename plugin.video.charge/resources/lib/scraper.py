# -*- coding: utf-8 -*-
# KodiAddon (Charge! TV Live)
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
      html = self.getRequest('http://watchcharge.com/watch-live/')
      url = re.compile('file: "(.+?)"', re.DOTALL).search(html).group(1)
      thumb  = self.addonIcon
      fanart = self.addonFanart
      d = datetime.datetime.utcnow()
      now = calendar.timegm(d.utctimetuple())
      html = self.getRequest('http://mobilelistings.tvguide.com/Listingsweb/ws/rest/airings/20534/start/'+str(now)+'/duration/20160?channelsourceids=35794%7C23.2&formattype=json')
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
            season = b['TVObject'].get('SeasonNumber')
            if season is not None: 
                infoList['Season'] = int(season)
            episode = b['TVObject']['EpisodeNumber']
            if episode is not None:
                infoList['Episode'] = int(episode)
         plot = '%s - %s                 %s min.[CR][COLOR blue]%s[/COLOR][CR]%s' % (st, et, infoList['duration'] / 60,  b['EpisodeTitle'], b['CopyText'])
         infoList['Plot'] = plot
         infoList['MPAA'] = b.get('Rating')
         infoList['mediatype'] = 'episode'
         ilist = self.addMenuItem(name,'GV', ilist, url, thumb, fanart, infoList, isFolder=False)
      return(ilist)

  def getAddonVideo(self,url):
      liz = xbmcgui.ListItem(path = url)
      xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)


