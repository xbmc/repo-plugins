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
import xbmc

UTF8 = 'utf-8'

class myAddon(t1mAddon):

  def getAddonMenu(self,url,ilist):
      self.defaultVidStream['width']  = 960
      self.defaultVidStream['height'] = 540
      html = self.getRequest('https://comettv.com/watch-live/')
      url = re.compile('	file: "(.+?)"', re.DOTALL).search(html).group(1)
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
      infoList ={}
      infoList['Artist'] = []
      infoList['Artist'].append(xbmc.getInfoLabel('ListItem.Artist'))
      infoList['Title'] = xbmc.getInfoLabel('ListItem.Title')
      vyear = xbmc.getInfoLabel('ListItem.Year')
      if vyear is not None and vyear != 0:
          infoList['Year'] = vyear
      infoList['Plot'] = xbmc.getInfoLabel('ListItem.Plot')
      infoList['Studio'] = xbmc.getInfoLabel('ListItem.Studio')
      infoList['Album'] = xbmc.getInfoLabel('ListItem.Album')
      infoList['Duration'] = xbmc.getInfoLabel('ListItem.Duration')
      infoList['mediatype']= 'tvshow'
      liz.setInfo('video', infoList)
      liz.setProperty('inputstreamaddon','inputstream.adaptive')
      liz.setProperty('inputstream.adaptive.manifest_type','hls')
      xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)






