# -*- coding: utf-8 -*-
# WABC Kodi Video Addon
#
from t1mlib import t1mAddon
import re
import urllib
import xbmc
import xbmcplugin
import xbmcgui
#import HTMLParser
import sys
import os
import json


#h = HTMLParser.HTMLParser()
qp  = urllib.quote_plus
uqp = urllib.unquote_plus
UTF8 = 'utf-8'


class myAddon(t1mAddon):

  def getAddonMenu(self,url,ilist):
      html = self.getRequest('https://abc.com/shows?category=A-Z')
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
        infoList ={}
        infoList['Title'] = name
        infoList['TVShowTitle'] = name
        infoList['mediatype'] = 'tvshow'
        ilist = self.addMenuItem(name,'GE', ilist, url, thumb, fanart, infoList, isFolder=True)
      return(ilist)


  def getAddonEpisodes(self,url,ilist, getFileData = False):
      if not url.startswith('http'):
          url = 'https://abc.com'+url
      if not url.endswith('/episode-guide') and (not 'movies-and-specials' in url):
          url = url+'/episode-guide'
      html = self.getRequest(url)
      html = re.compile("window\['__abc_com__'\]=(.+?);</script>", re.DOTALL).search(html)
      if html == None:
          return(ilist)
      html= html.group(1)
      a = json.loads(html)
      if a["page"]["content"].get("show", None) != None:
          b = a["page"]["content"]["show"]["modulesData"]
          for a in b:
             if a.get("tiles",None) != None:
                 break
          a = a.get("tiles",None)
          if a == None:
             return(ilist)
      else:
          a = [a["page"]["content"]["video"]["layout"]]
      for b in a:
          infoList = {}
          name = b.get("title", b["video"]["title"])
          infoList['Title'] = name
          infoList['Plot'] = b["video"]["longdescription"]
          url = b["id"].strip('video.')
          if not url.startswith('V'):
              url = b["video"]["id"].strip('video.')
          thumb = b.get("images", None)
          if thumb == None:
              thumb = b["theme"]["images"][-1]["value"]
          else:
              thumb = b["images"][-1]["value"]
          fanart = thumb
          infoList['Season'] = int(b["video"].get('seasonNumber','0'))
          infoList['Episode'] = int(b["video"].get('episodeNumber','0'))
          infoList['TVShowTitle'] = b["video"].get("showTitle",name)
          infoList['Studio'] = 'ABC'
          infoList['mediatype'] = 'episode'
          ilist = self.addMenuItem(name,'GV', ilist, url, thumb, fanart, infoList, isFolder=False)
      return(ilist)

  def getAddonVideo(self,url):
      vd = uqp(url)
      url = 'https://prod.gatekeeper.us-abc.symphony.edgedatg.com/api/ws/pluto/v1/module/videoplayer/2185737?brand=001&device=001&authlevel=0&layout=2185698&video='+str(vd)
      html = self.getRequest(url)
      ua = re.compile('"ULNK","value":"(.+?)"', re.DOTALL).search(html).group(1)
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
      url = ua+'?'+sessionKey
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


