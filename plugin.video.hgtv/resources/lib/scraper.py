# -*- coding: utf-8 -*-
# HGTV Kodi Video Addon
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
      html = requests.get('https://www.hgtv.com/shows/full-episodes', headers=self.defaultHeaders).text
      a = re.compile('<div class="m-MediaBlock o-Capsule__m-MediaBlock m-MediaBlock--PLAYLIST">.+?href="(.+?)".+?data-src="(.+?)".+?HeadlineText.+?>(.+?)<', re.IGNORECASE | re.DOTALL).findall(html)
      for (url, thumb, name) in a:
          url = ''.join(['https:',url])
          thumb = ''.join(['https:',thumb])
          name=UNESCAPE(name.strip().replace('<i>',''))
          html = requests.get(url.rsplit('/',1)[0], headers=self.defaultHeaders).text
          plot = re.compile('"og:description" content="(.+?)"',re.DOTALL).search(html)
          if plot is not None:
              plot = plot.group(1)
          else:
              plot = name
          infoList = {'mediatype':'tvshow',
                      'Plot': UNESCAPE(plot),
                      'TVShowTitle': name,
                      'Title': name,
                      'Studio': 'HGTV'}
          fanart = re.compile('property="og:image" content="(.+?)"',re.DOTALL).search(html)
          if fanart is not None:
              fanart = fanart.group(1).replace('616.347.jpeg','1280.720.jpeg',1)
          else:
              fanart = thumb
          ilist = self.addMenuItem(name,'GE', ilist, url, thumb, fanart, infoList, isFolder=True)
      return(ilist)


  def getAddonEpisodes(self,url,ilist):
      html = requests.get(url).text
      html = re.compile('<div id="video-player".+?type="text/x-config">(.+?)</script>',re.DOTALL).search(html)
      if html is None:
          return(ilist)
      vids = json.loads(html.group(1))['channels'][0]['videos']
      for b in vids:
          url = b['releaseUrl']
          name = UNESCAPE(b['title'])
          thumb = ''.join(['http://www.hgtv.com',b['thumbnailUrl']])
          fanart = thumb
          infoList = {'mediatype': 'episode',
                      'Title': name,
                      'Studio': b.get('publisherId'),
                      'Duration': b.get('length'),
                      'Plot': UNESCAPE(b.get('description')),
                      'TVShowTitle': xbmc.getInfoLabel('ListItem.Title')}
          ilist = self.addMenuItem(name,'GV', ilist, url, thumb, fanart, infoList, isFolder=False)
      return(ilist)


  def getAddonVideo(self,url):
      html = requests.get(url, headers=self.defaultHeaders).text
      subs = re.compile('<textstream src="(.+?\.srt)"',re.DOTALL).search(html)
      if subs != None:
          subs = subs.group(1)
      url = re.compile('<video src="(.+?)"',re.DOTALL).search(html).group(1)
      if url is None:
          url, msg = re.compile('<ref src="(.+?)".+?abstract="(.+?)"',re.DOTALL).search(html).groups()
          xbmcgui.Dialog().notification(self.addonName, msg)
          return
      liz = xbmcgui.ListItem(path = url, offscreen=True)
      liz.setSubtitles([subs])
      liz.setMimeType('application/x-mpegURL')
      xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)


