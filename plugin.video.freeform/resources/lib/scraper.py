# -*- coding: utf-8 -*-
# Freeform Channel Kodi Video Addon
#
from t1mlib import t1mAddon
import json
import re
import os
import xbmc
import xbmcplugin
import xbmcgui
import sys
import requests


class myAddon(t1mAddon):

  def getAddonMenu(self,url,ilist):
      html = requests.get('https://freeform.go.com/shows', headers=self.defaultHeaders).text
      a = re.compile('<div class="col-xs-4 shows-grid">.+?href="(.+?)".+?img src="(.+?)".+?<h3>(.+?)<',re.DOTALL).findall(html)
      for url, thumb, name in a:
          fanart = thumb
          infoList ={'mediatype':'tvshow',
                     'Title': name,
                     'TvShowTitle': name}
          contextMenu = [(self.addon.getLocalizedString(30002),'RunPlugin(%s?mode=AS&url=%s)' % (sys.argv[0], url))]
          ilist = self.addMenuItem(name,'GE', ilist, url, thumb, fanart, infoList, isFolder=True, cm=contextMenu)
      return(ilist)


  def getAddonEpisodes(self,url,ilist):
      if not url.startswith('http'):
         url = ''.join(['https://freeform.go.com', url])
      html = requests.get(url, headers=self.defaultHeaders).text
      vids = re.compile('<hr />.+?\<\!\-\- (.+?) \-\-\>', re.DOTALL).findall(html)
      for vid in vids:
          if not vid.startswith('{'):
              continue
          a = json.loads(vid)
          name = a['Episode']['Title']
          thumb = a['DisplayImageUrl']
          fanart = thumb
          url = a['PartnerApiId']
          infoList = {'mediatype':'episode',
                      'Season': a['Episode'].get('SeasonNumber'),
                      'Episode': a['Episode'].get('EpisodeNumber'),
                      'Title': name,
                      'Plot': a.get('LongDescription'),
                      'MPAA':'TV-PG',
                      'TVShowTitle': xbmc.getInfoLabel('ListItem.TVShowTitle'),
                      'Studio':'Freeform'}
          ilist = self.addMenuItem(name,'GV', ilist, url, thumb, fanart, infoList, isFolder=False)
      return(ilist)


  def doFunction(self, url):
      func = url[0:2]
      url  = url[2:]
      if func == 'AL':
        name  = xbmc.getInfoLabel('ListItem.Title')
        profile = self.addon.getAddonInfo('profile')
        moviesDir  = xbmc.translatePath(os.path.join(profile,'TV Shows'))
        movieDir  = xbmc.translatePath(os.path.join(moviesDir, name))
        if not os.path.isdir(movieDir):
            os.makedirs(movieDir)
        ilist = []
        ilist = self.getAddonEpisodes(url, ilist, getFileData = True)
        for season, episode, url in ilist:
            se = ''.join(['S',str(season),'E',str(episode)])
            xurl = ''.join([sys.argv[0],'?mode=GV&url=',url])
            strmFile = xbmc.translatePath(os.path.join(movieDir, se+'.strm'))
            with open(strmFile, 'w') as outfile:
               outfile.write(xurl)
      json_cmd = '{"jsonrpc":"2.0","method":"VideoLibrary.Scan", "params": {"directory":"%s/"},"id":1}' % movieDir.replace('\\','/')
      xbmc.executeJSONRPC(json_cmd)


  def getAddonVideo(self,url):
      xurl = ''.join(['https://api.pluto.watchabc.go.com/api/ws/pluto/v1/module/videoplayer/2185739?brand=002&device=001&authlevel=1&layout=2185738&video=', str(url)])
      html = requests.get(xurl, headers=self.defaultHeaders).text
      ua = re.compile('"ULNK","value":"(.+?)"', re.DOTALL).search(html).group(1)
      udata = ''.join(['video%5Fid=',str(url),'&device=001&video%5Ftype=lf&brand=002'])
      url = 'https://api.entitlement.watchabc.go.com/vp2/ws-secure/entitlement/2020/authorize.json'
      uheaders = self.defaultHeaders.copy()
      uheaders.update({'Content-Type':'application/x-www-form-urlencoded',
                       'Accept':'application/json',
                       'X-Requested-With':'ShockwaveFlash/24.0.0.194',
                       'Origin':'http://cdn1.edgedatg.com',
                       'DNT':'1',
                       'Referer':'http://cdn1.edgedatg.com/aws/apps/datg/web-player-unity/1.0.6.13/swf/player_vod.swf',
                       'Pragma':'no-cache',
                       'Connection':'keep-alive',
                       'Cache-Control':'no-cache'})
      a = requests.post(url, data=udata, headers=uheaders).json()
      if a.get('uplynkData') is None:
          xbmcgui.Dialog().notification(self.addonName, self.addon.getLocalizedString(30001), self.addonIcon)
          return
      url = ''.join([ua,'?',a['uplynkData']['sessionKey']])
      liz = xbmcgui.ListItem(path = url, offscreen=True)
# No need to process subtitles, all shows have closed captions
      liz.setProperty('inputstream','inputstream.adaptive')
      liz.setProperty('inputstream.adaptive.manifest_type','hls')
      liz.setMimeType('application/x-mpegURL')
      xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)

