# -*- coding: utf-8 -*-
# NPR Music Kodi Video Addon
#
from t1mlib import t1mAddon
import json
import re
import os
from datetime import datetime
import xbmc
import xbmcplugin
import xbmcgui
import xbmcaddon
import sys
import requests
import string
import urllib.parse

NPRBASE = 'http://www.npr.org'
VAPIBASE = 'https://vuhaus-production.global.ssl.fastly.net/api/'
addon = xbmcaddon.Addon('plugin.video.npr')
LCL = addon.getLocalizedString
homeDir = addon.getAddonInfo('path')
LSicon = xbmc.translatePath(os.path.join(homeDir, 'resources', 'LSicon.png'))
LSfanart = xbmc.translatePath(os.path.join(homeDir,'resources' 'LSfanart.jpg'))


class myAddon(t1mAddon):

  def getAddonMenu(self,url,ilist):
      feeds = ['92071316',
              '144918893',
              '172975546',
              '15667984',
              '149937282',
              '146587997']

      for feed in feeds:
          url = ''.join(['https://feeds.npr.org/feeds/',str(feed),'/feed.json'])
          a = requests.get(url, headers=self.defaultHeaders).json()
          name = a["title"]
          thumb = a.get("icon")
          infoList = {'Title': name,
                      'Plot': a.get("description")}
          ilist = self.addMenuItem(name,'GC', ilist, url, thumb, self.addonFanart, infoList, isFolder=True)
      name = LCL(30000)
      url = 'GS'
      infoList = {'Title': name,
                  'Plot': name}
      ilist = self.addMenuItem(name,'GS', ilist, url, LSicon, LSfanart, infoList, isFolder=True)
      return(ilist)


  def getAddonShows(self,url,ilist):
      liveSessions = [(LCL(30004),'BR'),
                      (LCL(30005),'PL01'),
                      (LCL(30006),'WL'),
                      (LCL(30007),'SE')]
      if url == 'GS':
          for name, url in liveSessions:
              infoList = {'Title': name,
                          'Plot': name}
              ilist = self.addMenuItem(name,'GS', ilist, url, LSicon, LSfanart, infoList, isFolder=True)

      elif url == 'BR':
          for name in string.ascii_uppercase:
              url = ''.join([VAPIBASE,'artists/search?letter=',name,'&page=1'])
              infoList = {'Title': name,
                          'Plot': ''.join([LCL(30008),str(name)])}
              ilist = self.addMenuItem(name,'SE', ilist, url, LSicon, LSfanart, infoList, isFolder=True)

      elif url == 'WL':
          a = requests.get(''.join([VAPIBASE,'performances']), headers=self.defaultHeaders).json()
          for b in a:
              url = b["hls_stream_url"]
              name = b["name"]
              fanart = b["images"]["wide"]["large"]["dpr_1_0"]["url"]
              thumb = b["images"]["square"]["large"]["dpr_1_0"]["url"]
              dt = datetime.fromisoformat(b.get("starting_at"))
              dt = dt.astimezone()
              plot = dt.strftime('%a, %b %d @ %I:%M%p %Z')
              infoList = {'mediatype': 'musicvideo',
                         'Title': name,
                         'Artist': [name],
                         'Plot': plot}
              ilist = self.addMenuItem(name, 'GE', ilist, url, thumb, fanart, infoList, isFolder=False)

      elif url.startswith('PL'):
          listNo = int(url.replace('PL','',1))
          url = ''.join([VAPIBASE,'playlists?page=', str(listNo)])
          a = requests.get(url, headers=self.defaultHeaders).json()
          for b in a:
              name = b["name"]
              url = b["url"]
              infoList = {'Title': name,
                          'Plot': b.get("description")}
              ilist = self.addMenuItem(name, 'GE', ilist, url, LSicon, LSfanart, infoList, isFolder=True)
          url = ''.join(['PL', str(listNo+1)])
          name = ''.join(['[COLOR red]',LCL(30001),'[/COLOR]'])
          infoList = {}
          ilist = self.addMenuItem(name,'GS', ilist, url, LSicon, LSfanart, infoList, isFolder=True)

      elif url == 'SE':
           keyb = xbmc.Keyboard('', LCL(30007))
           keyb.doModal()
           if (keyb.isConfirmed()):
               answer = keyb.getText()
               if len(answer) > 0:
                   url = ''.join([VAPIBASE,'search?scopes=video&q=',urllib.parse.quote_plus(answer)])
                   ilist = self.getAddonEpisodes(url, ilist)

      return(ilist)


  def getAddonSearch(self,url,ilist):
     a = requests.get(url, headers=self.defaultHeaders).json()
     if not (type(a) is list):
         a = [a]
     i = 0
     for i,b in enumerate(a,1):
         aurl = ''.join([VAPIBASE,'artists/',b["id"],'/videos'])
         name = b["name"]
         fanart = b["images"]["wide"]["large"]["dpr_1_0"]["url"]
         thumb = b["images"]["square"]["large"]["dpr_1_0"]["url"]
         infoList = {'mediatype': 'artist',
                     'Title': name,
                     'Artist': [name],
                     'Plot': b.get("bio")}
         x = ''.join(['Container.Update(',sys.argv[0],'?mode=SE&url=',VAPIBASE,'artists/',b["id"],'/related)'])
         contextMenu = [(LCL(30009), x)]
         ilist = self.addMenuItem(name, 'GE', ilist, aurl, thumb, fanart, infoList, isFolder=True, cm=contextMenu)
     if i >= 24:
         url = url.split('&page=',1)
         url = ''.join([url[0],'&page=',str(int(url[1])+1)])
         name = ''.join(['[COLOR red]',LCL(30001),'[/COLOR]'])
         infoList = {}
         ilist = self.addMenuItem(name,'SE', ilist, url, LSicon, LSfanart, infoList, isFolder=True)
     return(ilist)


  def getAddonEpisodes(self,url,ilist):
     xbmcplugin.setContent(int(sys.argv[1]), 'musicvideos')
     self.defaultVidStream = {'codec': 'h264', 'width': 1920, 'height': 1080, 'aspect': 1.78}
     a = requests.get(url, headers=self.defaultHeaders).json()
     if '/playlists/' in url:
         a = a["videos"]
     elif '/api/search' in url:
         a = a["items"]
     for b in a:
         aurl = b["hls_file_url"]
         name = b["name"]
         fanart = b["images"]["wide"]["large"]["dpr_1_0"]["url"]
         thumb = b["images"]["square"]["large"]["dpr_1_0"]["url"]
         infoList = {'mediatype': 'musicvideo',
                     'Title': name,
                     'Artist': [b["artist"]["name"]],
                     'Album': b.get("album_name"),
                     'Studio': b.get("publisher"),
                     'Plot': ''.join(['[COLOR blue]',b["artist"]["name"],'[/COLOR]\n','[COLOR green]',name,'[/COLOR]\n',b["description"]]),
                     'Duration': b.get('duration_in_ms',0)/1000,
                     'Aired': b.get('recorded_at')}
         x = ''.join(['Container.Update(',sys.argv[0],'?mode=SE&url=',VAPIBASE,'artists/',b["artist"]["slug"],')'])
         contextMenu = [(LCL(30010), x)]
         x = ''.join(['Container.Update(',sys.argv[0],'?mode=SE&url=',VAPIBASE,'artists/',b["artist"]["id"],'/related)'])
         contextMenu.append((LCL(30009), x))
         nfoData = { 'title': name,
                     'artist': b["artist"]["name"],
                     'album': b.get("album_name"),
                     'studio': b.get("publisher","NPR Music"),
                     'plot': b["description"],
                     'duration': b.get('duration_in_ms',0)/1000,
                     'aired': b.get('recorded_at'),
                     'thumb': str(thumb),
                     'fanart': ''.join(['\n<thumb>',str(fanart),'</thumb>\n'])}
         xurl = urllib.parse.quote_plus(''.join([aurl,'||',str(nfoData)]))
         x = ''.join(['RunPlugin(',sys.argv[0],'?mode=MU&url=',xurl,')'])
         contextMenu.append((LCL(30011), x))
         ilist = self.addMenuItem(name, 'GV', ilist, aurl, thumb, fanart, infoList, isFolder=False, cm=contextMenu)
     return(ilist)


  def getAddonCats(self,url,ilist):
     a = requests.get(url, headers=self.defaultHeaders).json()
     for b in a["items"]:
         url = b["url"]
         name = b["title"]
         thumb = b.get("image")
         fanart = thumb
         infoList = {'mediatype': 'musicvideos',
                     'Title': name,
                     'Plot': b["summary"]}
         if b["id"] == '761983313':   # playlist
             url = 'https://feeds.npr.org/761983313/feed.json'
             ilist = self.addMenuItem(name, 'GC', ilist, url, thumb, fanart, infoList, isFolder=True)
         elif '761983313' in a["feed_url"]:
             html = requests.get(url, headers=self.defaultHeaders).text
             url = ''.join(['https://feeds.npr.org/',str(re.compile("data-playlist-id='jwPlaylist(.+?)'", re.DOTALL).search(html).group(1)),'/feed.json'])
             ilist = self.addMenuItem(name, 'GC', ilist, url, thumb, fanart, infoList, isFolder=True)
         elif (b["title"] != xbmc.getInfoLabel('ListItem.Title')):
             ilist = self.addMenuItem(name, 'GV', ilist, url, thumb, fanart, infoList, isFolder=False)
     return(ilist)


  def getAddonVideo(self,url):
   if not url.endswith('.m3u8'):
      html = requests.get(url, headers=self.defaultHeaders).text
      a = re.compile("data-jwplayer='(.+?)'>", re.DOTALL).search(html)
      if a is not None:
           a = json.loads(a.group(1))
           finalurl = a['sources'][0]['file']
           for c in a['sources']:
               if c['label'] == 'HD':
                   finalurl = c['file']
                   break
      else:
          a = re.compile('<iframe src="https://www.vuhaus.com/embed/v2/videos/(.+?)\?', re.DOTALL).search(html)
          if a is not None:
              a = requests.get(''.join([VAPIBASE,'videos/',str(a.group(1))])).json()
              finalurl = a['hls_file_url']
          else:
               videoid = re.compile('<div class="video-wrap">.+?src="https://www\.youtube\.com/embed/(.+?)\?',re.DOTALL).search(html)
               if videoid is not None:
                   finalurl = 'plugin://plugin.video.youtube/?path=/root/video&action=play_video&videoid=%s' % (videoid.group(1))
               else:
                   xbmcgui.Dialog().notification(LCL(30002),LCL(30003)) #tell them no video found
                   return
   else:
       finalurl = url
   liz = xbmcgui.ListItem(path=finalurl, offscreen=True)
   if url.endswith('.m3u8'):
      liz.setProperty('inputstream','inputstream.adaptive')
      liz.setProperty('inputstream.adaptive.manifest_type','hls')
      liz.setMimeType('application/x-mpegURL')
   else:
      liz.setMimeType('video/mp4')
   xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)
