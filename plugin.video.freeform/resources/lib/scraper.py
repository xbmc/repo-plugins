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
from datetime import datetime
import time


class myAddon(t1mAddon):

  def getAddonMenu(self,url,ilist):
      html = requests.get('https://www.freeform.com/shows?category=Unlocked%20Shows', headers=self.defaultHeaders).text
      html = re.compile("window\['__abc_com__'\]=(.+?);<\/script>", re.DOTALL).search(html).group(1)
      a = json.loads(html)
      for b in a['page']['content']['shell']['module']:
          if b.get('id') == '3376166':
              for c in b['tiles']:
                  url = ''.join(['https://freeform.go.com', c['link']['urlValue']])
                  thumb = c['images'][0]['value']
                  fanart = thumb
                  name = c['title']
                  infoList ={'mediatype':'tvshow',
                             'Title': name,
                             'TvShowTitle': name,
                             'Plot': c['show']['aboutTheShowSummary']}
                  contextMenu = [(self.addon.getLocalizedString(30002),'RunPlugin(%s?mode=AS&url=%s)' % (sys.argv[0], url))]
                  ilist = self.addMenuItem(name,'GE', ilist, url, thumb, fanart, infoList, isFolder=True, cm=contextMenu)
              break
      return(ilist)


  def getAddonEpisodes(self,url,ilist):
      html = requests.get(url, headers=self.defaultHeaders).text
      html = re.compile("window\['__abc_com__'\]=(.+?);<\/script>", re.DOTALL).search(html).group(1)
      a = json.loads(html)
      for b in a['page']['content']['shell']['module']:
          if b.get('type') == 'tilegroup':
              if not 'tilegroup' in b.get('name',''):
                  break
              a = b.get('tiles',[])
              for b in a:
                  url = b['resource']
                  if b.get('images') != None:
                      thumb = b['images'][0]['value']
                      fanart = thumb
                  else:
                      thumb = self.addonIcon
                      fanart = self.addonFanart
                  name = b['title']
                  infoList ={'mediatype':'episode',
                             'Title': name,
                             'TvShowTitle': b['video']['show']['title'],
                             'Plot': b['video']['longdescription'],
                             'Season': int(b['video']['seasonnumber']),
                             'Episode': int(b['video']['episodenumber']),
                             'MPAA': b['video']['tvrating'],
                             'Duration': int(b['video']['duration'])/1000}
                  aired = b['video']['airtime'].split(', ',1)[1].rsplit(' ',2)[0]
                  if aired[1] == ' ':
                      aired = ''.join(['0',aired])
                  aired = datetime(*(time.strptime(aired, "%d %b %Y")[0:6]))
                  infoList['aired'] = aired.strftime("%Y-%m-%d")
                  infoList['FirstAired'] = infoList['aired']
                  ilist = self.addMenuItem(name,'GV', ilist, url, thumb, fanart, infoList, isFolder=False)
      return(ilist)



  def getAddonVideo(self,url):
      a = requests.get(url, headers=self.defaultHeaders).json()
      a = requests.get(a['modules'][0]['resource'], headers=self.defaultHeaders).json()
      vid = a['video']['id']
      for b in a['video']['assets']:
          if b['format'] == 'ULNK':
              ua = b['value']
              udata = ''.join(['video%5Fid=',str(vid),'&device=001&video%5Ftype=lf&brand=002'])
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

