# -*- coding: utf-8 -*-
# Sprout Kodi Video Addon
#
from t1mlib import t1mAddon
import json
import re
import os
import datetime
import urllib
import urllib2
import xbmc
import xbmcplugin
import xbmcgui
import HTMLParser
import sys

h = HTMLParser.HTMLParser()
qp  = urllib.quote_plus
uqp = urllib.unquote_plus
UTF8     = 'utf-8'

SPROUTBASE = 'http://www.sproutonline.com%s'

class myAddon(t1mAddon):

  def getAddonMenu(self,url,ilist):
      basehtml = self.getRequest('http://www.sproutonline.com/now/')
      cats = re.compile('<li class="filter-option'+".+?'name': '(.+?)'"+'.+?src="(.+?)".+?<span>(.+?)<.+?</li', re.DOTALL).findall(basehtml)
      for url, thumb, name in cats:
          url = SPROUTBASE % '/watch?show=%s' % (url)
          html = self.getRequest(url)
          epis = re.compile('<li class="video-reference.+?href="(.+?)"(.+?)</li>', re.DOTALL).findall(html)
          for showurl, utype in epis:
              if 'FULL EPISODE' in utype:
                  name = name.strip()
                  infoList = {}
                  infoList['MPAA'] = 'TV-G'
                  infoList['TVShowTitle'] = name
                  infoList['Title'] = name
                  infoList['Studio'] = 'Sprout'
                  infoList['Genre'] = 'Kids'
                  infoList['TVShowTitle'] = name
                  infoList['mediatype'] = 'tvshow'
                  ilist = self.addMenuItem(name,'GE', ilist, url, thumb, self.addonFanart, infoList, isFolder=True)
                  break
      return(ilist)

  def getAddonEpisodes(self,url,ilist):
      self.defaultVidStream['width']  = 1920
      self.defaultVidStream['height'] = 1080
      html = self.getRequest(url)
      epis = re.compile('<li class="video-reference.+?href="(.+?)"(.+?)</li>', re.DOTALL).findall(html)
      for url, utype in epis:
          if 'FULL EPISODE' in utype:
              html = self.getRequest(SPROUTBASE % url)
              url = re.compile('"video": "(.+?)"', re.DOTALL).search(html).group(1)
              html = self.getRequest('%s?format=script' % url)
              a = json.loads(html)
              infoList = {}
              infoList['MPAA'] = 'TV-G'
              infoList['TVShowTitle'] = xbmc.getInfoLabel('ListItem.TVShowTitle')
              infoList['Title'] = a['title']
              infoList['Studio'] = 'Sprout'
              duration = a.get('duration')
              if duration is not None:
                  infoList['Duration'] = int(duration/1000)
              infoList['Genre'] = a.get('nbcu$advertisingGenre')
              infoList['Season'] = a.get('pl1$seasonNumber')
              infoList['Episode'] = a.get('pl1$episodeNumber')
              infoList['Plot'] = a.get('description')
              thumb = a.get('defaultThumbnailUrl')
              fanart = thumb
              name = a['title']
              infoList['mediatype'] = 'episode'
              ilist = self.addMenuItem(name,'GV', ilist, url, thumb, fanart, infoList, isFolder=False)
      return(ilist)

  def getAddonVideo(self,url):
      gvUrls = ['http://sproutonline-vh.akamaihd.net/i/MPX/video/NBCU_Sprout/%s_,40,25,18,12,7,4,2,00',
                'https://tvesprout-vh.akamaihd.net/i/prod/video/%s_,40,25,18,12,7,4,2,00',
                'http://sproutonline-vh.akamaihd.net/i/MPX/video/NBCU_Sprout/%s_,1696,1296,896,696,496,240,306,',
                'http://sproutonline-vh.akamaihd.net/i/MPX/video/NBCU_Sprout/%s_,25,18,12,7,4,2,00']

      gvUrlEnd= '.mp4.csmil/master.m3u8?b=&__b__=1000&hdnea=st=%s~exp=%s'
      html = self.getRequest('%s?format=script' % uqp(url))
      a = json.loads(html)
      suburl = a["captions"][0]["src"]
      try:    url = suburl.split('/caption/',1)[1]
      except: url = suburl.split('/NBCU_Sprout/',1)[1]
      url = url.rsplit('.',1)[0]
      td = (datetime.datetime.utcnow()- datetime.datetime(1970,1,1))
      unow = int((td.microseconds + (td.seconds + td.days * 24 * 3600) * 10**6) / 10**6)
      for gvUrl in gvUrls:
          u = (gvUrl+gvUrlEnd) % (url, str(unow), str(unow+60))
          if gvUrl != gvUrls[-1]:
              req = urllib2.Request(u.encode(UTF8), None, self.defaultHeaders)
              try:
                  response = urllib2.urlopen(req, timeout=20) # check to see if video file exists
                  break
              except:
                  pass
      liz = xbmcgui.ListItem(path = u)
# No need to process subtitles, all shows have closed captions
      infoList={}
      infoList['mediatype'] = xbmc.getInfoLabel('ListItem.DBTYPE')
      infoList['Title'] = xbmc.getInfoLabel('ListItem.Title')
      infoList['TVShowTitle'] = xbmc.getInfoLabel('ListItem.TVShowTitle')
      infoList['Year'] = xbmc.getInfoLabel('ListItem.Year')
      infoList['Premiered'] = xbmc.getInfoLabel('Premiered')
      infoList['Plot'] = xbmc.getInfoLabel('ListItem.Plot')
      infoList['Studio'] = xbmc.getInfoLabel('ListItem.Studio')
      infoList['Genre'] = xbmc.getInfoLabel('ListItem.Genre')
      infoList['Duration'] = xbmc.getInfoLabel('ListItem.Duration')
      infoList['MPAA'] = xbmc.getInfoLabel('ListItem.Mpaa')
      infoList['Aired'] = xbmc.getInfoLabel('ListItem.Aired')
      infoList['Season'] = xbmc.getInfoLabel('ListItem.Season')
      infoList['Episode'] = xbmc.getInfoLabel('ListItem.Episode')
      liz.setInfo('video', infoList)
      xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)

