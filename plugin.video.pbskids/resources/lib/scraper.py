# -*- coding: utf-8 -*-
# KodiAddon PBSKids
#
from t1mlib import t1mAddon
import re
import xbmc
import xbmcplugin
import xbmcgui
import sys
import requests


class myAddon(t1mAddon):

  def getAddonMenu(self,url,ilist):
      a = requests.get('https://content.services.pbskids.org/v2/kidspbsorg/home/?imgsizes=showLogo:88x88,showLogoSquare:100x100', headers=self.defaultHeaders).json()
      a = a["collections"]
      ilist = self.addMenuItem('Live','GS', ilist, ''.join([a['kids-livestream']['content'][0]['URI']]), self.addonIcon, self.addonFanart, {}, isFolder=True)
      b = a["kids-programs-tier-1"]["content"]
      b.extend(a["kids-programs-tier-2"]["content"])
      b.extend(a["kids-programs-tier-3"]["content"])
      for c in b:
          name = c["title"]
          url = c["slug"]
          thumb = c["images"]["mezzanine_16x9"]
          fanart = c["images"]["background"]
          infoList = {'mediatype': 'tvshow',
                      'Title': name,
                      'Plot': name,
                      'TVShowtitle': name,
                      'Studio': 'PBS'}
          ilist = self.addMenuItem(name,'GE', ilist, url, thumb, fanart, infoList, isFolder=True)
      return(ilist)


  def getAddonEpisodes(self,url,ilist):
      a = requests.get(''.join(['https://content.services.pbskids.org/v2/kidspbsorg/programs/',url,'?imgsizes=showLogo:88x88,showLogoSquare:100x100']), headers=self.defaultHeaders).json()
      a = a['collections']['episodes']['content']
      for b in a:
          url = b.get('mp4')
          if not url is None:
              name = b.get('title','no title')
              thumb  = b.get('images',{'x':None}).get('mezzanine', self.addonIcon)
              fanart  = b.get('images',{'x':None}).get('mezzanine', self.addonFanart)
              c = b.get('closedCaptions',[])
              captions = ''
              for d in c:
                 if d.get('format') == 'SRT':
                     captions = d.get('URI','')
                     break
              infoList={'mediatype': 'episode',
                        'Title': name,
                        'TVShowTitle': xbmc.getInfoLabel('ListItem.TVShowTitle'),
                        'Plot': name,
                        'Studio': 'PBS'}
              ilist = self.addMenuItem(name,'GV', ilist, ''.join([url,'|',captions]), thumb, fanart, infoList, isFolder=False)
      return(ilist)

  def getAddonShows(self,url,ilist):
      url = ''.join([url,'|20534|39303%7C10.4'])
      return self.getAddonListing(url, ilist)


  def getAddonVideo(self,url):
      url, captions = url.split('|',1)
      if not url.endswith('.m3u8'):
          a = requests.get(''.join([url,'?format=json']), headers=self.defaultHeaders).json()
          url = a.get('url')
      if url is not None:
              liz = xbmcgui.ListItem(path=url, offscreen=True)
              if len(captions) > 0:
                  liz.setSubtitles([captions])
              xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)

