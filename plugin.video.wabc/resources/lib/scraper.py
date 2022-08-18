# -*- coding: utf-8 -*-
# WABC Kodi Video Addon
#
from t1mlib import t1mAddon
import re
import xbmc
import xbmcplugin
import xbmcgui
import sys
import json
import requests
from datetime import datetime
import time


class myAddon(t1mAddon):

  def getAddonMenu(self,url,ilist):
      html = requests.get('https://abc.com/shows?category=A-Z', headers=self.defaultHeaders).text
      html = re.compile("window\['__abc_com__'\]=(.+?);<\/script>", re.DOTALL).search(html).group(1)
      a = json.loads(html)
      for b in a['page']['content']['shell']['module']:
          if b.get('id') == '2496325':
              for c in b['tiles']:
                  url = ''.join(['https://abc.go.com', c['link']['urlValue']])
                  thumb = c['images'][0]['value']
                  fanart = thumb
                  name = c['title']
                  infoList ={'mediatype':'tvshow',
                             'Title': name,
                             'TvShowTitle': name,
                             'Plot': c['show'].get('aboutTheShowSummary')}
                  contextMenu = [(self.addon.getLocalizedString(30002),'RunPlugin(%s?mode=AS&url=%s)' % (sys.argv[0], url))]
                  ilist = self.addMenuItem(name,'GE', ilist, url, thumb, fanart, infoList, isFolder=True, cm=contextMenu)
              break
      return(ilist)

  def getAddonEpisodes(self,url,ilist):
      html = requests.get(url, headers=self.defaultHeaders).text
      html = re.compile("window\['__abc_com__'\]=(.+?);<\/script>", re.DOTALL).search(html).group(1)
      a = json.loads(html)
      for b in a['page']['content']['shell']['module']:
              if 'Clips' in b.get('title',''):
                  break
              if b.get('type') == 'tilegroup':
                  a = b.get('tiles',[])
              elif b.get('type') == 'videoplayer':
                  a = [b]
              else:
                  continue
              for b in a:
                  if b.get('video') == None:
                      break
                  url = b.get('resource',''.join(['https://prod.gatekeeper.us-abc.symphony.edgedatg.com/api/ws/pluto/v1/layout?brand=001&device=001&authlevel=0&type=video&video=',b['video']['id']]))
                  if b.get('images') != None:
                      thumb = b['images'][0]['value']
                      fanart = thumb
                  else:
                      thumb = xbmc.getInfoLabel('ListItem.Art(thumb)')
                      fanart = xbmc.getInfoLabel('ListItem.Art(thumb)')
                  name = b['video']['title']
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
                  infoList['premiered'] = infoList['aired']
                  ilist = self.addMenuItem(name,'GV', ilist, url, thumb, fanart, infoList, isFolder=False)
      return(ilist)


  def getAddonVideo(self, url):
      a = requests.get(url, headers=self.defaultHeaders).json()
      a = requests.get(a['modules'][0]['resource'], headers=self.defaultHeaders).json()
      if a.get('video') != None:
          vid = a['video']['id'] # added
          for b in a['video']['assets']:
              if b.get('format') == 'ULNK':
                  url = 'https://api.entitlement.watchabc.go.com/vp2/ws-secure/entitlement/2020/authorize.json'
                  udata = ''.join(['video%5Fid=',str(vid),'&device=001&video%5Ftype=lf&brand=001'])
                  uheaders = self.defaultHeaders.copy()
                  uheaders.update({'Content-Type': 'application/x-www-form-urlencoded',
                               'Accept': 'application/json',
                               'X-Requested-With': 'ShockwaveFlash/22.0.0.209',
                               'Origin': 'http://cdn1.edgedatg.com'})
                  a = requests.post(url, data=udata, headers=uheaders).json()
                  if a.get('uplynkData') is None:
                      xbmcgui.Dialog().notification(self.addonName, self.addon.getLocalizedString(30001), time=5000, icon=self.addonIcon)
                      return
                  url = ''.join([str(b.get('value')),'?',str(a['uplynkData'].get('sessionKey'))]).strip()
                  liz = xbmcgui.ListItem(path=url, offscreen=True)
# No need to process subtitles, all shows have closed captions
                  liz.setProperty('inputstream','inputstream.adaptive')
                  liz.setProperty('inputstream.adaptive.manifest_type','hls')
                  liz.setMimeType('application/x-mpegURL')
                  xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)

