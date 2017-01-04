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
import json

h = HTMLParser.HTMLParser()
qp  = urllib.quote_plus
uqp = urllib.unquote_plus
UTF8     = 'utf-8'


class myAddon(t1mAddon):

  def getAddonMenu(self,url,ilist):
      urls = {}
      html = self.getRequest('http://abc.go.com/shows')
      html = re.compile('<main class="content(.+?)<section  data-m-id="1904281', re.DOTALL).search(html).group(1)
      a = re.compile('data-sm-id="".+?href="(.+?)".+?class="tablet-source.+?srcset="(.+?) ',re.DOTALL).findall(html)
      for url, thumb in a:
        if not '/' in url:
          continue
        if urls.get(url,None) is None:
          if url.endswith('/index'):
              url = url.replace('/index','',1)
          urls[url] = url
          name = url.rsplit('/',1)[1]
          name = name.replace('-',' ').title()
          fanart = thumb
          infoList ={}
          infoList['Title'] = name
          infoList['TVShowTitle'] = name
          infoList['mediatype'] = 'tvshow'
          contextMenu = [('Add To Library','XBMC.RunPlugin(%s?mode=DF&url=AL%s)' % (sys.argv[0], url))]
          ilist = self.addMenuItem(name,'GE', ilist, url, thumb, fanart, infoList, isFolder=True, cm=contextMenu)
      return(ilist)


  def getAddonEpisodes(self,url,ilist, getFileData = False):
      if not url.startswith('http:'):
          url = 'http://abc.go.com'+url
      if not url.endswith('/episode-guide'):
          url = url+'/episode-guide'
      html = self.getRequest(url)
      vids = re.compile('data-video-id="VDKA(.+?)".+?data-title="(.+?)".+?data-background="(.+?)".+?class="tablet-source".+?srcset="(.+?) .+?class="season-number(.+?)<.+?class="episode-number(.+?)<.+?class="m-episode-summary.+?<p>(.+?)</p>.+?<div class="m-episode-meta(.+?)</div',re.DOTALL).findall(html)
      for url, name, fanart, thumb, season, episode, plot, meta in vids:
          name = h.unescape(name.decode(UTF8))
          name = h.unescape(name) # get rid of &apos; as well
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
          meta1 = re.compile('<span class="m-episode-meta-item m-episode-meta-duration">(.+?)</span>', re.DOTALL).findall(meta)
          if meta1 is not None:
              duration = 0
              tmp = meta1[0].split(':')
              for dur in tmp:
                  duration = duration*60 + int(dur) 
              infoList['Duration'] = duration

          meta1 = re.compile('<span class="m-episode-meta-item">(.+?)</span>', re.DOTALL).findall(meta)
          if meta1 is not None:
              mo, day, year = meta1[0].split('/')
              year = int(year)
              if year < 55:
                  year = year + 2000
              else:
                  year = year + 1900
              infoList['Date'] = '%s-%s-%s' % ( str(year), mo, day)
              infoList['Aired'] = infoList['Date']
              infoList['Year'] = int(infoList['Aired'].split('-',1)[0])
              if len(meta1)>1:
                  infoList['MPAA'] = meta1[1]
          infoList['TVShowTitle'] = xbmc.getInfoLabel('ListItem.TVShowTitle')
          infoList['Studio'] = 'ABC'
          infoList['mediatype'] = 'episode'
          if getFileData == False:
              ilist = self.addMenuItem(name,'GV', ilist, url, thumb, fanart, infoList, isFolder=False)
          else:
              if infoList.get('Season') is not None and infoList.get('Episode') is not None:
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
      url = 'https://api.entitlement.watchabc.go.com/vp2/ws-secure/entitlement/2020/authorize.json'
      udata = 'video%5Fid=VDKA'+str(vd)+'&device=001&video%5Ftype=lf&brand=001'
      uheaders = self.defaultHeaders.copy()
      uheaders['Content-Type'] = 'application/x-www-form-urlencoded'
      uheaders['Accept'] = 'application/json'
      uheaders['X-Requested-With'] = 'ShockwaveFlash/22.0.0.209'
      uheaders['Origin'] = 'http://cdn1.edgedatg.com'
      html = self.getRequest(url, udata, uheaders)
      a = json.loads(html)
      if a.get('uplynkData', None) is None:
          xbmc.executebuiltin('XBMC.Notification("%s", "%s", %s, "%s")' % (self.addonName, self.addon.getLocalizedString(30001), 5000, self.addonIcon))
          return

      sessionKey = a['uplynkData']['sessionKey']
      if not '&cid=' in sessionKey:
          oid, eid = re.compile('&oid=(.+?)&eid=(.+?)&', re.DOTALL).search(sessionKey).groups()
          url = 'http://content.uplynk.com/ext/%s/%s.m3u8?%s' % (oid, eid, sessionKey)
      else:
          cid = re.compile('&cid=(.+?)&', re.DOTALL).search(sessionKey).group(1)
          url = 'http://content.uplynk.com/%s.m3u8?%s' % (cid, sessionKey)
      html = self.getRequest(url)
      url = re.compile('#UPLYNK-MEDIA0.+?http(.+?)\n',re.DOTALL).search(html).group(1)
      url = 'http'+url
      liz = xbmcgui.ListItem(path = url.strip())
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


