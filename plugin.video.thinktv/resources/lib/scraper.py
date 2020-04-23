# -*- coding: utf-8 -*-
# ThinkTV Kodi Video Addon
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
UTF8 = 'utf-8'


class myAddon(t1mAddon):


  def getShows(self, a, ilist):
      for b in a:
          url = b['slug']
          name = b['title']
          thumb = b['image']
          fanart = thumb
          infoList ={}
          infoList['Title'] = name
          infoList['TVShowTitle'] = name
          plot = b.get('description_long',b.get('description'))
          infoList['Plot'] = h.unescape(plot)
          infoList['Genre'] = b.get('genre_titles')
          infoList['mediatype'] = 'tvshow'
          c = (name, url, thumb, infoList)
          contextMenu = [(self.addon.getLocalizedString(30009),'RunPlugin(%s?mode=DF&url=AS%s)' % (sys.argv[0], str(c)))]
          ilist = self.addMenuItem(name, 'GE', ilist, url, thumb, fanart, infoList, isFolder=True, cm=contextMenu)
      return(ilist)


  def getAddonMenu(self,url,ilist):
# Leia+ hack until I rewrite script.module.timlib
      self.homeDir = self.addon.getAddonInfo('path').decode(UTF8)
      self.homeDir = xbmc.translatePath(os.path.join(self.homeDir,'resources'))
      self.addonIcon = xbmc.translatePath(os.path.join(self.homeDir,'icon.png'))
      self.addonFanart = xbmc.translatePath(os.path.join(self.homeDir,'fanart.jpg'))

      ilist = self.addMenuItem(self.addon.getLocalizedString(30005), 'GS', ilist, 'false|0', self.addonIcon, self.addonFanart, {} , isFolder=True)
      ilist = self.addMenuItem(self.addon.getLocalizedString(30006), 'GS', ilist, 'true|0', self.addonIcon, self.addonFanart, {} , isFolder=True)
      ilist = self.addMenuItem(self.addon.getLocalizedString(30008), 'GC', ilist, 'myshows', self.addonIcon, self.addonFanart, {} , isFolder=True)
      ilist = self.addMenuItem(self.addon.getLocalizedString(30007), 'GM', ilist, 'search', self.addonIcon, self.addonFanart, {} , isFolder=True)
      return(ilist)


  def getAddonShows(self,url,ilist):
      url = url.split('|',1)
      uheaders = self.defaultHeaders.copy()
      uheaders['X-Requested-With'] = 'XMLHttpRequest'
      uheaders['Connection'] = 'keep-alive'
      html = self.getRequest('https://video.thinktv.org/shows-page/%s/?stationId=7bad8720-1c01-4189-ad48-4b203e571b94&title=&genre=all-genres&source=all-sources&alphabetically=%s' % (url[1], url[0]), '', uheaders)
      nextPg = str(int(url[1])+1)
      nextPg = url[0]+'|'+nextPg
      a = json.loads(html)
      ilist = self.getShows(a['results']['content'], ilist) 
      if len(ilist) >= 30:
          ilist = self.addMenuItem('[COLOR red]%s[/COLOR]' % self.addon.getLocalizedString(30004), 'GS', ilist, nextPg, self.addonIcon, self.addonFanart, {} , isFolder=True)
      return(ilist)

  def getAddonMovies(self,url,ilist):
      keyb = xbmc.Keyboard('', self.addon.getLocalizedString(30007))
      keyb.doModal()
      if (keyb.isConfirmed()):
          answer = keyb.getText()
          if len(answer) > 0:
              url = 'https://video.thinktv.org/search-videos/?page=1&q=%s&rank=relevance&station_id=7bad8720-1c01-4189-ad48-4b203e571b94' % uqp(answer)
              html = self.getRequest(url)
              a = json.loads(html)
              ilist = self.getShows(a["results"]["shows"], ilist)
      return(ilist)

      
  def getAddonEpisodes(self,url,ilist):
      burl = url
      if not burl.startswith('http'):
          burl = 'https://video.thinktv.org/show/%s/all-season-episodes/?start=0&limit=24' % url
      else:
          start = burl.split('?start=',1)[1].split('&',1)[0]
          burl = burl.replace('?start='+start, '?start='+str(int(start)+24), 1)
      html = self.getRequest(burl)
      a = json.loads(html)
      for b in a["content"]:
             url = str(b["legacy_tp_media_id"])+'|'+b["slug"]
             name = b["title_sortable"]
             thumb = b.get("image")
             fanart = thumb
             adate = b.get("premiere_date")
             infoList ={}
             infoList["Season"] = b["show"].get("season")
             infoList["Episode"] = b["show"].get("episode")
             infoList['Title'] = name
             infoList['TVShowTitle'] = xbmc.getInfoLabel('ListItem.TVShowTitle')
             infoList['Plot'] = b.get("description_long")
             if adate != None:
                 infoList['dateadded'] = adate.rsplit('-',1)[0].replace('T',' ')
                 infoList['aired'] = infoList['dateadded'].split(' ',1)[0]
                 infoList['premiered'] = infoList['aired']
             infoList['duration'] = b.get("duration")
             infoList['mediatype'] = 'episode'
             ilist = self.addMenuItem(name,'GV', ilist, url, thumb, fanart, infoList, isFolder=False)
      if len(ilist) >= 24:
          ilist = self.addMenuItem('[COLOR red]%s[/COLOR]' % self.addon.getLocalizedString(30004), 'GE', ilist, burl, self.addonIcon, self.addonFanart, {} , isFolder=True)
      return(ilist)


  def getAddonCats(self,url,ilist):
      profile = self.addon.getAddonInfo('profile').decode(UTF8)
      profile = xbmc.translatePath(os.path.join(profile, 'Data'))
      maFile = xbmc.translatePath(os.path.join(profile, 'myshows.json'))
      a = []
      if os.path.exists(maFile):
          with open(maFile) as infile:
              a = json.load(infile)
              for b in a:
                  b = eval(b)
                  name,url,thumb,infoList = b
                  fanart = thumb
                  contextMenu = [(self.addon.getLocalizedString(30010),'Container.Update(%s?mode=DF&url=DS%s)' % (sys.argv[0], name))]
                  ilist = self.addMenuItem(name, 'GE', ilist, url, thumb, fanart, infoList, isFolder=True, cm=contextMenu)
      return(ilist)
 

  def doFunction(self, url):
      func = url[0:2]
      url  = url[2:]
      if func == 'DS':
          profile = self.addon.getAddonInfo('profile').decode(UTF8)
          profile = xbmc.translatePath(os.path.join(profile, 'Data'))
          maFile = xbmc.translatePath(os.path.join(profile, 'myshows.json'))
          a = []
          if os.path.exists(maFile):
              with open(maFile) as infile:
                  a = json.load(infile)
          for idx,b in enumerate(a):
             c = eval(b)
             if c[0] == url:
                 a.pop(idx)
                 break
          with open(maFile, 'w') as outfile:
              json.dump(a, outfile)
          outfile.close()
      elif func == 'AS':
          profile = self.addon.getAddonInfo('profile').decode(UTF8)
          profile = xbmc.translatePath(os.path.join(profile, 'Data'))
          if not os.path.isdir(profile):
              os.makedirs(profile)
          maFile = xbmc.translatePath(os.path.join(profile, 'myshows.json'))
          a = []
          if os.path.exists(maFile):
              with open(maFile) as infile:
                  a = json.load(infile)
          a.append((url))
          with open(maFile, 'w+') as outfile:
              json.dump(a, outfile)
          outfile.close()


  def getAddonVideo(self,url):
      u = url.split('|',1)
      url = 'https://player.pbs.org/stationplayer/'+u[0]+'/?parentURL=https%3A%2F%2Fvideo.thinktv.org%2Fvideo%2F'+u[1]+'%2F&callsign=WPTD&unsafePostMessages=true&unsafeDisableUpsellHref=true'
      html = self.getRequest(url)
      html = re.compile('window.videoBridge = \{(.+?)\};', re.DOTALL).search(html).group()
      a = json.loads(html[21:-1])
      url = a["encodings"][0]
      suburl = a.get("subtitle_url")
      if suburl == None:
         if a.get("cc") != None:
             suburl = a["cc"].get("SRT")
      url += '?format=jsonp&callback=__jp1'
      html = self.getRequest(url)
      html = re.compile('__jp1\((.+?)\)', re.DOTALL).search(html).group(1)
      a = json.loads(html)
      url = a["url"]
      liz = xbmcgui.ListItem(path = url)
      liz.setSubtitles([suburl])
      xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)
