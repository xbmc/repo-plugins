# -*- coding: utf-8 -*-
# WABC Kodi Video Addon
#
from t1mlib import t1mAddon
import re
import urllib
import xbmc
import xbmcplugin
import xbmcgui
import HTMLParser
import sys
import os

h = HTMLParser.HTMLParser()
qp  = urllib.quote_plus
uqp = urllib.unquote_plus
UTF8     = 'utf-8'


class myAddon(t1mAddon):

  def getAddonMenu(self,url,ilist):
      ihtml = self.getRequest('http://abc.go.com/shows')
      html = self.getRequest('http://abc.go.com/shows/abc-updates/news/insider/143-for-free-watch-abc-watch-full-episodes-with-no-sign-in-042715?cid=abchp_143_for_free')
      html = re.compile('<section class="m-blog_detail-body(.+?)</section', re.DOTALL).search(html).group(1)
      a = re.compile('<p align="center".+?<a.+?name="(.+?)".+?<a href="(.+?)">(.+?)</a>',re.DOTALL).findall(html)
      for id, url, name in a:
          name = name.replace('<strong>','').replace('</strong>','').replace('<b>','').replace('</b>','')
          name=h.unescape(name.decode(UTF8))
          thumb = re.compile('<main class="content">.+?<a href="'+url.replace('http://abc.go.com','')+'".+?class="tablet-source".+?srcset="(.+?) ',re.DOTALL).search(ihtml)
          if thumb is not None:
              thumb = thumb.group(1)
              fanart = thumb
          else:
              thumb = self.addonIcon
              fanart = self.addonFanart
          infoList ={}
          infoList['Title'] = name
          infoList['TVShowTitle'] = name
          infoList['mediatype'] = 'tvshow'
          contextMenu = [('Add To Library','XBMC.RunPlugin(%s?mode=DF&url=AL%s)' % (sys.argv[0], url))]
          ilist = self.addMenuItem(name,'GE', ilist, url, thumb, fanart, infoList, isFolder=True, cm=contextMenu)
      return(ilist)


  def getAddonEpisodes(self,url,ilist, getFileData = False):
      self.defaultVidStream['width']  = 1920
      self.defaultVidStream['height'] = 1080
      if not url.endswith('/episode-guide'):
          url = url+'/episode-guide'
      html = self.getRequest(url)
      vids = re.compile('data-videoid="VDKA(.+?)".+?data-title="(.+?)".+?data-background="(.+?)".+?class="tablet-source".+?srcset="(.+?) .+?class="season-number(.+?)<.+?class="episode-number(.+?)<.+?class="m-episode-summary.+?<p>(.+?)</p>.+?<div class="m-episode-meta(.+?)</div',re.DOTALL).findall(html)
      for url, name, fanart, thumb, season, episode, plot, meta in vids:
          name = h.unescape(name.decode(UTF8))
          plot = h.unescape(plot.decode(UTF8))
          thumb = thumb.strip()
          infoList = {}
          season = season.split('>S',1)
          if len(season) > 1 and season[1].strip().isdigit():
              infoList['Season'] = int(season[1])
          episode = episode.split('>E',1)
          if len(season) > 1 and episode[1].strip().isdigit():
              infoList['Episode'] = int(episode[1])
          infoList['Title'] = name
          infoList['Plot'] = plot
          meta = re.compile('<span class="m-episode-meta-item">(.+?)</span>', re.DOTALL).findall(meta)
          if meta is not None:
              duration = 0
              tmp = meta[0].split(':')
              for dur in tmp:
                  duration = duration*60 + int(dur) 
              infoList['Duration'] = duration
              mo, day, year = meta[1].split('/')
              year = int(year)
              if year < 55:
                  year = year + 2000
              else:
                  year = year + 1900
              infoList['Date'] = '%s-%s-%s' % ( str(year), mo, day)
              infoList['Aired'] = infoList['Date']
              infoList['Year'] = int(infoList['Aired'].split('-',1)[0])
              infoList['MPAA'] = meta[2]
          infoList['TVShowTitle'] = xbmc.getInfoLabel('ListItem.TVShowTitle')
          infoList['Studio'] = 'ABC'
          infoList['mediatype'] = 'episode'
          if getFileData == False:
              ilist = self.addMenuItem(name,'GV', ilist, url, thumb, fanart, infoList, isFolder=False)
          else:
              ilist.append((infoList['Season'], infoList['Episode'], url))
      return(ilist)

  def doFunction(self, url):
    func = url[0:2]
    url  = url[2:]
    if func == 'AL':
      name  = xbmc.getInfoLabel('ListItem.Title')
      profile = self.addon.getAddonInfo('profile').decode(UTF8)
      moviesDir  = xbmc.translatePath(os.path.join(profile,'TV Shows'))
      movieDir  = xbmc.translatePath(os.path.join(moviesDir, name))
      if not os.path.isdir(movieDir):
           os.makedirs(movieDir)
      ilist = []
      ilist = self.getAddonEpisodes(url, ilist, getFileData = True)
      for season, episode, url in ilist:
            se = 'S%sE%s' % (str(season), str(episode))
            xurl = '%s?mode=GV&url=%s' % (sys.argv[0], url)
            strmFile = xbmc.translatePath(os.path.join(movieDir, se+'.strm'))
            with open(strmFile, 'w') as outfile:
               outfile.write(xurl)         
    json_cmd = '{"jsonrpc":"2.0","method":"VideoLibrary.Scan", "params": {"directory":"%s/"},"id":1}' % movieDir.replace('\\','/')
    jsonRespond = xbmc.executeJSONRPC(json_cmd)


  def getAddonVideo(self,url):
      vd = uqp(url)
      url = 'http://cdnapi.kaltura.com//api_v3/index.php?service=multirequest&action=null&ignoreNull=1&2%3Aaction=getContextData&3%3Aaction=list&2%3AcontextDataParams%3AflavorTags=uplynk&2%3AentryId='+vd+'&apiVersion=3%2E1%2E5&1%3Aversion=-1&2%3AcontextDataParams%3AstreamerType=http&3%3Afilter%3AentryIdEqual='+vd+'&clientTag=kdp%3Av3%2E9%2E2&1%3AentryId='+vd+'&2%3AcontextDataParams%3AobjectType=KalturaEntryContextDataParams&3%3Afilter%3AobjectType=KalturaCuePointFilter&2%3Aservice=baseentry&1%3Aservice=baseentry&1%3Aaction=get'
      html = self.getRequest(url)
      if '<error>' in html or 'Missing KS' in html:
          xbmc.executebuiltin('XBMC.Notification("%s", "%s", %s, "%s")' % (self.addonName, self.addon.getLocalizedString(30001), 5000, self.addonIcon))
          return
      url = re.compile('<dataUrl>(.+?)</dataUrl>',re.DOTALL).search(html).group(1)
      liz = xbmcgui.ListItem(path = url.strip())
# No need to process subtitles, all videos have closed captions
      infoList ={}
      infoList['Title'] = xbmc.getInfoLabel('ListItem.Title')
      infoList['Year'] = xbmc.getInfoLabel('ListItem.Year')
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


