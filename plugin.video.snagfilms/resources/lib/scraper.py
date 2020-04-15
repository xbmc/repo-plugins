# -*- coding: utf-8 -*-
# Snag Films Kodi Video Addon
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
UTF8  = 'utf-8'


class myAddon(t1mAddon):

  def getAddonMenu(self,url,ilist):
    ilist = self.addMenuItem(self.addon.getLocalizedString(30001), 'GC', ilist, 'https://prod-api-cached-2.viewlift.com/content/pages?site=snagfilms&path=%2Fshows&includeContent=true&countryCode=US&languageCode=default', self.addonIcon, self.addonFanart, {} , isFolder=True)
    url = 'https://prod-api-cached-2.viewlift.com/content/pages?site=snagfilms&path=%2Fcategories&includeContent=true&moduleOffset=0&moduleLimit=4&countryCode=US&languageCode=default'
    html = self.getRequest(url)
    a = json.loads(html)
    a = a["categoryMap"]
    b = list(a.items())
    for name, url in b:
       ilist = self.addMenuItem(name, 'GM', ilist, url, self.addonIcon, self.addonFanart, {} , isFolder=True)
    return(ilist)

  def getAddonCats(self,url,ilist):
    html = self.getRequest(url)
    a = json.loads(html)
    for b in a["modules"]:
        if b.get("moduleType") != 'CuratedTrayModule':
            continue
        name = b["title"]
        url = name
        ilist = self.addMenuItem(name,'GS', ilist, url, self.addonIcon, self.addonFanart, {}, isFolder=True)
    return(ilist)
     

  def getAddonShows(self,url,ilist):
    html = self.getRequest('https://prod-api-cached-2.viewlift.com/content/pages?site=snagfilms&path=%2Fshows&includeContent=true&countryCode=US&languageCode=default')
    a = json.loads(html)
    for b in a["modules"]:
          if b.get("moduleType") != 'CuratedTrayModule':
              continue
          if url != b["title"]:
              continue
          b = b["contentData"]
          for c in b:
              c = c["gist"]
              infoList = {}
              name = c["title"]
              url = c["permalink"]
              thumb = c.get("videoImageUrl")
              fanart = thumb
              infoList['Title'] = name
              infoList['Plot'] = h.unescape(c["description"])
              infoList['mediatype'] = 'tvshow'
              ilist = self.addMenuItem(name,'GE', ilist, url, thumb, fanart, infoList, isFolder=True)
    return(ilist)

  def getAddonEpisodes(self,url,ilist):
    html = self.getRequest('https://prod-api-cached-2.viewlift.com/content/pages?site=snagfilms&path='+url+'&includeContent=true&countryCode=US&languageCode=default')
    a = json.loads(html)
    for b in a["modules"]:
          if b.get("moduleType") != 'ShowDetailModule':
              continue
          b = b["contentData"]
          for d in b:
           for e in d["seasons"]:
             for c in e["episodes"]:
              c = c["gist"]
              infoList = {}
              name = c["title"]
              url = c["id"]
              thumb = c.get("videoImageUrl")
              fanart = thumb
              infoList['Title'] = name
              infoList['Plot'] = h.unescape(c["description"])
              infoList['mediatype'] = 'episode'
              ilist = self.addMenuItem(name,'GV', ilist, url, thumb, fanart, infoList, isFolder=False)
    return(ilist)

  def getAddonMovies(self,url,ilist):
      burl = url
      if not ('&offset' in burl):
          burl += '&offset=0'
      else:
          b = burl.rsplit('=',1)
          cnt = int(b[1])+20
          burl = b[0]+'='+str(cnt)
      url = 'https://prod-api-cached-2.viewlift.com/content/pages?site=snagfilms&path='+burl+'&includeContent=true&countryCode=US&languageCode=default'
      html = self.getRequest(url)
      a = json.loads(html)
      for b in a["modules"]:
          if b.get("moduleType") != 'CategoryDetailModule':
              continue
          b = b["contentData"]
          for c in b:
              c = c["gist"]
              infoList = {}
              name = c["title"]
              url = c["id"]
              thumb = c.get("posterImageUrl")
              fanart = c.get("videoImageUrl")
              infoList['Title'] = name
              infoList['Plot'] = h.unescape(c["description"])
              infoList['mediatype'] = 'movie'
              contextMenu = [(self.addon.getLocalizedString(30003),'XBMC.RunPlugin(%s?mode=DF&url=AM%s)' % (sys.argv[0], url))]
              ilist = self.addMenuItem(name,'GV', ilist, url, thumb, fanart, infoList, isFolder=False, cm=contextMenu)
      if len(ilist) >= 20:
          ilist = self.addMenuItem('[COLOR red]%s[/COLOR]' % self.addon.getLocalizedString(30004), 'GM', ilist, burl, self.addonIcon, self.addonFanart, {} , isFolder=True)
      return(ilist)



  def doFunction(self, url):
      func = url[0:2]
      url  = url[2:]
      if func == 'AL':
          name = xbmc.getInfoLabel('ListItem.Title')
          profile = self.addon.getAddonInfo('profile').decode(UTF8)
          moviesDir = xbmc.translatePath(os.path.join(profile,'TV Shows'))
          movieDir = xbmc.translatePath(os.path.join(moviesDir, name))
          if not os.path.isdir(movieDir):
              os.makedirs(movieDir)
          ilist = []
          ilist = self.getAddonEpisodes(url, ilist, getFileData = True)
          for season, episode, url in ilist:
              se = 'S%sE%s' % (str(season), str(episode))
              xurl = '%s?mode=GV&url=%s' % (sys.argv[0], qp(url))
              strmFile = xbmc.translatePath(os.path.join(movieDir, se+'.strm'))
              with open(strmFile, 'w') as outfile:
                  outfile.write(xurl)         
      elif func == 'AM':
          name  = xbmc.getInfoLabel('ListItem.Title')
          profile = self.addon.getAddonInfo('profile').decode(UTF8)
          moviesDir  = xbmc.translatePath(os.path.join(profile,'Movies'))
          movieDir  = xbmc.translatePath(os.path.join(moviesDir, name))
          if not os.path.isdir(movieDir):
              os.makedirs(movieDir)
          strmFile = xbmc.translatePath(os.path.join(movieDir, name+'.strm'))
          with open(strmFile, 'w') as outfile:
              outfile.write('%s?mode=GV&url=%s' %(sys.argv[0], url))
      json_cmd = '{"jsonrpc":"2.0","method":"VideoLibrary.Scan", "params": {"directory":"%s/"},"id":1}' % movieDir.replace('\\','/')
      jsonRespond = xbmc.executeJSONRPC(json_cmd)


  def getAddonVideo(self,url):
      html = self.getRequest('https://prod-api-cached-2.viewlift.com/content/videos/%s?site=snagfilms&countryCode=US&languageCode=default' % url)
      a = json.loads(html)
      u = a["streamingInfo"]["videoAssets"]["mpeg"][-1]["url"]
      liz = xbmcgui.ListItem(path=u)
      infoList ={}
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
      SubTitle = []     
      for st in a["contentDetails"]["closedCaptions"]:
          if st["type"] == 'SRT':
              SubTitle.append(st["url"])
      liz.setSubtitles(SubTitle)
      liz.setInfo('video', infoList)
      xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)

