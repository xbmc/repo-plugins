# -*- coding: utf-8 -*-
# TV Ontario Kodi Video Addon
#
from t1mlib import t1mAddon
import json
import re
import os
import urllib
import xbmc
import xbmcplugin
import xbmcgui
import HTMLParser
import sys

h = HTMLParser.HTMLParser()
qp  = urllib.quote_plus
uqp = urllib.unquote_plus
UTF8  = 'utf-8'


class myAddon(t1mAddon):

  def getAddonMenu(self,url,ilist):
      azurl = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ1'
      for a in azurl:
          name = a
          plot = ''
          url  = a
          infoList = {}
          infoList['mediatype'] = 'tvshow'
          ilist = self.addMenuItem(name,'GS', ilist, url, self.addonIcon, self.addonFanart, infoList, isFolder=True)
      return(ilist)

  def getAddonShows(self,url,ilist):
      html = self.getRequest("https://tvo.org/programs/%s/filter-ajax" % url)
      a = re.compile('href="(.+?)">(.+?)<',re.DOTALL).findall(html)
      for url,name in a:
          infoList = {}
          infoList['mediatype'] = 'tvshow'
          ilist = self.addMenuItem(name,'GE', ilist, url, self.addonIcon, self.addonFanart, infoList, isFolder=True)
      return(ilist)

  def getAddonEpisodes(self,url,ilist):
      self.defaultVidStream['width']  = 640
      self.defaultVidStream['height'] = 480
      html = self.getRequest('https://tvo.org%s' % url)
      vids = re.compile('<div class="content-list__first.+?href="(.+?)".+?src="(.+?)".+?href=.+?>(.+?)<.+?field-summary"><div class="field-content">(.+?)<',re.DOTALL).findall(html)
      if vids == []:
          vids = re.compile('"og:url" content="(.+?)".+?content="(.+?)".+?content="(.+?)".+?".+?content="(.+?)"',re.DOTALL).search(html).groups()
          vids = [(vids[0],vids[2],vids[1],vids[3])]
      TVShowTitle = re.compile('property="dc:title" content="(.+?)"', re.DOTALL).search(html).group(1)
      for (url, thumb, name, plot) in vids:
          if not url.startswith('http'):
              url = 'https://tvo.org' + url
          fanart = thumb
          infoList = {}
          infoList['Title'] = h.unescape(name)
          infoList['Studio'] = 'TV Ontario'
          infoList['Plot'] = h.unescape(plot)
          infoList['TVShowTitle'] = TVShowTitle
          infoList['mediatype'] = 'episode'
          ilist = self.addMenuItem(name,'GV', ilist, url, thumb, fanart, infoList, isFolder=False)
      return(ilist)


  def getAddonVideo(self,url):
      html = self.getRequest(url)
      vid = re.compile('data-video-id="(.+?)"',re.DOTALL).search(html).group(1)
      url = 'https://secure.brightcove.com/services/viewer/htmlFederated?&width=1280&height=720&flashID=BrightcoveExperience&bgcolor=%23FFFFFF&playerID=756015080001&playerKey=AQ~~,AAAABDk7A3E~,xYAUE9lVY9-LlLNVmcdybcRZ8v_nIl00&isVid=true&isUI=true&dynamicStreaming=true&%40videoPlayer='+vid+'&secureConnections=true&secureHTMLConnections=true'
      html = self.getRequest(url)
      m = re.compile('experienceJSON = (.+?)\};',re.DOTALL).search(html)
      a = json.loads(html[m.start(1):m.end(1)+1])
      b = a['data']['programmedContent']['videoPlayer']['mediaDTO']['IOSRenditions']
      u =''
      rate = 0
      suburl = a['data']['programmedContent']['videoPlayer']['mediaDTO'].get('captions')
      if suburl is not None:
          suburl = suburl[0].get('URL')
      for c in b:
          if c['encodingRate'] > rate:
              rate = c['encodingRate']
              u = c['defaultURL']
          b = a['data']['programmedContent']['videoPlayer']['mediaDTO']['renditions']
          for c in b:
              if c['encodingRate'] > rate:
                 rate = c['encodingRate']
                 u = c['defaultURL']
              if rate == 0:
                 u = a['data']['programmedContent']['videoPlayer']['mediaDTO'].get('FLVFullLengthURL')
      liz = xbmcgui.ListItem(path = u)
      if suburl is not None :
          subfile = self.procConvertSubtitles(suburl)
          liz.setSubtitles([(subfile)])
      xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)
