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


class myAddon(t1mAddon):

  def getAddonMenu(self,url,ilist):
      html = requests.get('https://abc.com/shows?category=A-Z',headers=self.defaultHeaders).text
      html = re.compile("window\['__abc_com__'\]=(.+?);</script>", re.DOTALL).search(html).group(1)
      a = json.loads(html)
      c = a["page"]["content"]["shows"]["categoryTilegroups"][1]["tiles"]
      if c == []:
          c = a["page"]["content"]["shows"]["categoryTilegroups"][2]["tiles"]
      for b in c:
          name = b["title"]
          url = b["link"]["urlValue"]
          thumb = b["images"][-1]["value"]
          fanart = thumb
          infoList ={'mediatype': 'tvshow',
                   'Title': name,
                   'TVShowTitle': name}
          contextMenu = [(self.addon.getLocalizedString(30002),'RunPlugin(%s?mode=AS&url=%s)' % (sys.argv[0], url))]
          ilist = self.addMenuItem(name,'GE', ilist, url, thumb, fanart, infoList, isFolder=True, cm=contextMenu)
      return(ilist)


  def getAddonEpisodes(self,url,ilist):
      if not url.startswith('http'):
          url = ''.join(['https://abc.com',url])
      if not url.endswith('/episode-guide') and (not 'movies-and-specials' in url):
          url = ''.join([url,'/episode-guide'])
      html = requests.get(url, headers=self.defaultHeaders).text
      html = re.compile("window\['__abc_com__'\]=(.+?);</script>", re.DOTALL).search(html)
      if html == None:
          return(ilist)
      a = json.loads(html.group(1))
      if a["page"]["content"].get("show", None) != None:
          b = a["page"]["content"]["show"]["modulesData"]
          for a in b:
             a = a.get("tiles")
             if a != None:
                 break
          if a == None:
             return(ilist)
      else:
          if a["page"]["content"].get("video") == None:
              return(ilist)
          a = [a["page"]["content"]["video"]["layout"]]
      for b in a:
          name = b.get("title", b["video"]["title"])
          url = b["id"].strip('video.')
          if not url.startswith('V'):
              url = b["video"]["id"].strip('video.')
          thumb = b.get("images", None)
          if thumb == None:
              thumb = b["theme"]["images"][-1]["value"]
          else:
              thumb = b["images"][-1]["value"]
          fanart = thumb
          infoList = {'mediatype': 'episode',
                      'Title': name,
                      'TVShowTitle': b["video"].get("showTitle",name),
                      'Plot': b["video"]["longdescription"],
                      'Season': int(b["video"].get('seasonNumber','0')),
                      'Episode': int(b["video"].get('episodeNumber','0')),
                      'Studio': 'ABC'}
          ilist = self.addMenuItem(name,'GV', ilist, url, thumb, fanart, infoList, isFolder=False)
      return(ilist)


  def getAddonVideo(self, vd):
      url = ''.join(['https://prod.gatekeeper.us-abc.symphony.edgedatg.com/api/ws/pluto/v1/module/videoplayer/2185737?brand=001&device=001&authlevel=0&layout=2185698&video=',str(vd)])
      a = requests.get(url, headers=self.defaultHeaders).json()
      if a.get('video') != None:
          for b in a['video']['assets']:
              if b.get('format') == 'ULNK':
                  url = 'https://api.entitlement.watchabc.go.com/vp2/ws-secure/entitlement/2020/authorize.json'
                  udata = ''.join(['video%5Fid=VDKA',str(vd),'&device=001&video%5Ftype=lf&brand=001'])
                  uheaders = self.defaultHeaders.copy()
                  uheaders.update({'Content-Type': 'application/x-www-form-urlencoded',
                               'Accept': 'application/json',
                               'X-Requested-With': 'ShockwaveFlash/22.0.0.209',
                               'Origin': 'http://cdn1.edgedatg.com'})
                  a = requests.post(url, data=udata, headers=uheaders).json()
                  if a.get('uplynkData') is None:
                      xbmcgui.Dialog().notification(self.addonName, self.addon.getLocalizedString(30001), 5000, self.addonIcon)
                      return
                  url = ''.join([str(b.get('value')),'?',str(a['uplynkData'].get('sessionKey'))]).strip()
                  liz = xbmcgui.ListItem(path=url, offscreen=True)
# No need to process subtitles, all shows have closed captions
                  liz.setProperty('inputstream','inputstream.adaptive')
                  liz.setProperty('inputstream.adaptive.manifest_type','hls')
                  liz.setMimeType('application/x-mpegURL')
                  xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)

