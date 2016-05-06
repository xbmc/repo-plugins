# -*- coding: utf-8 -*-
# WNBC Kodi Video Addon
#
from t1mlib import t1mAddon
import json
import re
import os
import datetime
import urllib
import xbmc
import xbmcplugin
import xbmcgui
import sys

qp  = urllib.quote_plus
uqp = urllib.unquote_plus
UTF8 = 'utf-8'


class myAddon(t1mAddon):

  def getAddonMenu(self,url,ilist):
     html = self.getRequest('http://tve-atcnbce.nbcuni.com/live/3/nbce/containers/iPad')
     a = json.loads(html)
     for b in a:
        infoList ={}
        url  = b['assetID']
        name = b['title']
        infoList['Title'] = name
        infoList['TVShowTitle'] = name
        infoList['Plot'] = b['description']
        if (b['seasons'] != []):
           infoList['Season'] = int(b['seasons'][0]['number'])
        fanart = b['images'][0]['images']['featured_large_3']
        thumb  = b['images'][0]['images']['show_tile']
        mode = 'GE'
        if (b['seasons'] != []):
           if (b['seasons'][0]['hasClips']): mode = 'GC'
        ilist = self.addMenuItem(name, mode, ilist, url, thumb, fanart, infoList, isFolder=True)
     return(ilist)

  def getAddonCats(self,url,ilist):
     thumb  = xbmc.getInfoLabel('ListItem.Art(thumb)')
     fanart = xbmc.getInfoLabel('ListItem.Art(fanart)')
     ilist = self.addMenuItem('Episodes','GE', ilist, url, thumb, fanart, {}, isFolder=True)
     ilist = self.addMenuItem('Clips','GM', ilist, url, thumb, fanart, {}, isFolder=True)
     return(ilist)

  def getAddonMovies(self,url,ilist):
     xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
     self.getAddonEpisodes(url,ilist,dtype='clip')
     return(ilist)


  def getAddonEpisodes(self,url,ilist, dtype='episode'):
     url = uqp(url)
     html = self.getRequest('http://tve-atcnbce.nbcuni.com/live/3/nbce/containers/%s/iPad' % url)
     a = json.loads(html)
     for b in a['results']:
       if b['subtype'] == dtype:
        infoList = {}
        name = b['title']
        fanart = b['images'][0]['images'].get('featured_large_5')
        thumb  = b['images'][0]['images'].get('episode_tile')
        if not b['requiresAuth']:
           url = b['videoURL']
        else:
           url    = b['videoURL'].split('?',1)[0]
           if url == '': continue
           url   += '?format=preview'
           html   = self.getRequest(url)
           c = json.loads(html)
           catQuoted  = urllib.quote(c['categories'][0]['name'])
           pubDateStr = str(c['pubDate'])
           url = 'http://feed.theplatform.com/f/NnzsPC/end_card?range=1-10&byCustomValue={fullEpisode}{true},{showInNavigation}{true}&byCategories='+catQuoted+'&form=json&sort=nbcu:seasonNumber,nbcu:airOrder,pubDate&byPubDate='+pubDateStr+'~'
           html = self.getRequest(url)
           c = json.loads(html)
           if c['entries'] == []: continue
           for d in c['entries'][0]['media$content']:
             if d['plfile$isDefault']:
                url = d['plfile$url']+'&manifest=m3u'
                break
        infoList['Title'] = name
        infoList['TVShowTitle'] = b.get('parentContainerTitle')
        season = b.get('seasonNumber', False)
        if season: infoList['Season']  = int(season)
        episode = b.get('episodeNumber', False)
        if episode: infoList['Episode'] = int(episode)
        duration = b.get('totalDuration')
        if duration: infoList['Duration']= int(duration/1000)
        airDate = int(b['firstAiredDate'])
        infoList['date'] = datetime.datetime.fromtimestamp(airDate).strftime('%d.%m.%Y')
        airDate = datetime.datetime.fromtimestamp(airDate).strftime('%Y-%m-%d')
        infoList['aired'] = airDate
        infoList['premiered']  = airDate
        infoList['year'] = int(airDate.split('-',1)[0])
        infoList['MPAA'] = b.get('rating')
        infoList['Plot'] = b.get('description')
        infoList['Studio'] = 'NBC'
        infoList['mediatype'] = 'episode'
        ilist = self.addMenuItem(name,'GV', ilist, url, thumb, fanart, infoList, isFolder=False)
     return(ilist)


  def getAddonVideo(self,url):
     if not '&format=redirect' in url:
       html = self.getRequest(url)
       if 'video src="' in html:
          url  = re.compile('video src="(.+?)"', re.DOTALL).search(html).group(1)
       else:
          url  = re.compile('ref src="(.+?)"', re.DOTALL).search(html).group(1)
     liz = xbmcgui.ListItem(path = url)
     xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)
