# -*- coding: utf-8 -*-
# DIY Network Kodi Video Addon
#
from t1mlib import t1mAddon
import json
import re
import xbmc
import xbmcplugin
import xbmcgui
import html.parser
import sys
import requests

UNESCAPE = html.parser.HTMLParser().unescape

class myAddon(t1mAddon):

  def getAddonMenu(self,url,ilist):
      html = requests.get('https://www.diynetwork.com/shows/full-episodes', headers=self.defaultHeaders).text
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
      url = ''.join(['https:',url])
      showName = xbmc.getInfoLabel('ListItem.Title')
      html = requests.get(url, headers=self.defaultHeaders).text
      html = re.compile('<div id="video-player".+?type="text/x-config">(.+?)</script>',re.DOTALL).search(html)
      if html != None:
          a = json.loads(html.group(1))
          for b in a['channels'][0]['videos']:
              url = b['releaseUrl']
              name = UNESCAPE(b['title'])
              thumb = ''.join(['https://www.hgtv.com',b['thumbnailUrl']])
              fanart = thumb
              infoList = {'mediatype': 'episode',
                          'Duration': b.get('length'),
                          'Title': name,
                          'Studio': b.get('publisherId'),
                          'Plot': UNESCAPE(b.get('description')),
                          'TVShowTitle': showName}
              ilist = self.addMenuItem(name,'GV', ilist, url, thumb, fanart, infoList, isFolder=False)
      return(ilist)


  def getAddonVideo(self,url):
      html = requests.get(url, headers=self.defaultHeaders).text
      url = re.compile('<video src="(.+?)"',re.DOTALL).search(html)
      if url != None:
          liz = xbmcgui.ListItem(path = url.group(1), offscreen=True)
          subs = re.compile('<textstream src="(.+?\.srt)"',re.DOTALL).search(html)
          if subs != None:
              subs = subs.group(1)
          liz.setSubtitles([subs])
          xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)


