# -*- coding: utf-8 -*-
# DIY Network Kodi Video Addon
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

class myAddon(t1mAddon):

  def getAddonMenu(self,url,ilist):
      html = self.getRequest('https://www.diynetwork.com/shows/full-episodes')
      html = re.compile('<section class="o-Capsule o-EditorialPromo(.+?)<div class="container-aside">', re.DOTALL).search(html).group(1)
      a = re.compile('m-MediaBlock--PLAYLIST">.+?href="(.+?)".+?data-src="(.+?)".+?HeadlineText.+?>(.+?)<', re.IGNORECASE | re.DOTALL).findall(html)
      for (url, thumb, name) in a:
          infoList = {'mediatype':'tvshow'}
          thumb = ''.join(['https:',thumb])
          fanart = thumb
          name = name.strip()
          infoList.update(dict.fromkeys(['Title','TVShowTitle','Plot'], name))
          ilist = self.addMenuItem(name,'GE', ilist, url, thumb, fanart, infoList, isFolder=True)
      return(ilist)


  def getAddonEpisodes(self,url,ilist):
      if not url.startswith('http'):
          url = ''.join(['https:',url])
      showName = xbmc.getInfoLabel('ListItem.Title')
      html = self.getRequest(url)
      html = re.compile('<div id="video-player".+?type="text/x-config">(.+?)</script>',re.DOTALL).search(html)
      if html != None:
          a = json.loads(html.group(1))
          for b in a['channels'][0]['videos']:
              url = b['releaseUrl']
              name = h.unescape(b['title'])
              thumb = 'https://www.hgtv.com%s' % b['thumbnailUrl']
              fanart = thumb
              infoList = {'mediatype':'episode'}
              infoList['Duration'] = b.get('length')
              infoList['Title'] = name
              infoList['Studio'] = b.get('publisherId')
              infoList['Plot'] = h.unescape(b.get('description'))
              infoList['TVShowTitle'] = showName
              ilist = self.addMenuItem(name,'GV', ilist, url, thumb, fanart, infoList, isFolder=False)
      return(ilist)


  def getAddonVideo(self,url):
      html = self.getRequest(url)
      url = re.compile('<video src="(.+?)"',re.DOTALL).search(html)
      if url != None:
          liz = xbmcgui.ListItem(path = url.group(1))
          subs = re.compile('<textstream src="(.+?\.srt)"',re.DOTALL).search(html)
          liz.setSubtitles([subs.group(1)])
          xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)


