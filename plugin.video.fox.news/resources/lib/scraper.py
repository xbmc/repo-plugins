# -*- coding: utf-8 -*-
# Fox News Kodi Video Addon
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
BASEURL = 'https://video.foxnews.com'


class myAddon(t1mAddon):

  def getAddonMenu(self,url,ilist):
      html = requests.get(BASEURL).text
      a1,a2,a3 = re.compile('<a href="#">Video.+?">(.+?)<.+?">(.+?)<.+?">(.+?)<', re.DOTALL).search(html).groups()
      ilist = self.addMenuItem(a2,'GM', ilist, 'show', self.addonIcon, self.addonFanart, {}, isFolder=True)
      ilist = self.addMenuItem(a3,'GM', ilist, 'news', self.addonIcon, self.addonFanart, {}, isFolder=True)
      return(ilist)


  def getAddonMovies(self,url,ilist):
      html = requests.get(BASEURL).text
      html = re.compile(''.join(['<div class="column footer-',url,'-clips">(.+?)</div']), re.DOTALL).search(html).group(1)
      a = re.compile('href="(.+?)">(.+?)<', re.DOTALL).findall(html)
      for url, name in a:
          name = UNESCAPE(name)
          infoList ={'mediatype': 'tvshow',
                     'Title': name,
                     'Plot': name,
                     'TVShowTitle': name}
          ilist = self.addMenuItem(name,'GS', ilist, url, self.addonIcon, self.addonFanart, infoList, isFolder=True)
      return(ilist)


  def getAddonShows(self,url,ilist):
      html = requests.get(''.join([BASEURL,url])).text
      html = re.compile('<div class="main">.+?<ul>(.+?)</ul>', re.DOTALL).search(html).group(1)
      a = re.compile('aria-label="(.+?)".+?href="(.+?)"', re.DOTALL).findall(html)
      if len(a) > 15 :
          self.getAddonEpisodes(url, ilist)
          return(ilist)
      for name,url in a:
          name = UNESCAPE(name)
          infoList ={'mediatype': 'tvshow',
                     'Title': name,
                     'Plot': name,
                     'TVShowTitle': xbmc.getInfoLabel('ListItem.TVShowTitle')}
          ilist = self.addMenuItem(name,'GE', ilist, url, self.addonIcon, self.addonFanart, infoList, isFolder=True)
      return(ilist)
      

  def getAddonEpisodes(self,url,ilist):
      html = requests.get(''.join([BASEURL,url])).text
      s,p = re.compile('site: "(.+?)".+?playlistId: "(.+?)"', re.DOTALL).search(html).groups()
      html = requests.get(''.join(['https://video.',s,'.com/v/feed/playlist/',p,'.json?template=fox&cb='])).text
      if html.startswith('{'):
          a = json.loads(html)
          c = []
          if (type (a["channel"]["item"]) is dict):
              c.append(a["channel"]["item"])
          else:
              c = a["channel"]["item"]
          for b in c:
              url = b["guid"]
              adate = b.get("dc-date")
              studio = b.get("dc-source")
              duration = b.get("itunes-duration")
              b = b["media-group"]
              name = b["media-title"]
              thumb = b["media-thumbnail"]["@attributes"]["url"]
              fanart = b["media-image"]["@attributes"]["url"]
              infoList = {'mediatype': 'episode',
                          'Title': name,
                          'TVShowTitle': xbmc.getInfoLabel('ListItem.TVShowTitle'),
                          'Plot': b.get("media-description"),
                          'Studio': studio,
                          'Genre': 'News'}
              if adate != None:
                  infoList['dateadded'] = adate.rsplit('-',1)[0].replace('T',' ')
                  infoList['aired'] = infoList['dateadded'].split(' ',1)[0]
                  infoList['premiered'] = infoList['aired']
              if duration != None:
                  duration = duration.split(':')
                  d = int(duration[2])+int(duration[1])*60+int(duration[0])*3600
                  infoList['duration'] = d
              ilist = self.addMenuItem(name,'GV', ilist, url, thumb, fanart, infoList, isFolder=False)
      return(ilist)


  def getAddonVideo(self,url):
      a = requests.get(''.join([BASEURL,'/v/feed/video/',url,'.json?template=fox&cb='])).json()
      a = a["channel"]["item"]
      suburl = a["media-group"].get("media-subTitle")
      if suburl != None:
          suburl = suburl["@attributes"]["href"]
      url = a["enclosure"]["@attributes"]["url"]
      for b in a["media-group"]["media-content"]:
          if( b["@attributes"]["type"] == 'video/mp4') and (b["media-category"]["@attributes"]["label"] == "PDL_HD"):
              url = b["@attributes"]["url"]
              break
      if url == '':
          for b in a["media-group"]["media-content"]:
              if( b["@attributes"]["type"] == 'application/x-mpegURL'):
                  url = b["@attributes"]["url"]
                  break
      liz = xbmcgui.ListItem(path = url, offscreen=True)
      liz.setSubtitles([suburl])
      xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)

