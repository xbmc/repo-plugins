# -*- coding: utf-8 -*-
# Russia Today Kodi Video Addon
#
from t1mlib import t1mAddon
import re
import os
import xbmc
import xbmcplugin
import xbmcaddon
import xbmcgui
import html.parser
import sys
import requests

UNESCAPE = html.parser.HTMLParser().unescape
RTBASE  = 'https://www.rt.com/rtmobile/'
LCL = xbmcaddon.Addon('plugin.video.rt').getLocalizedString


class myAddon(t1mAddon):

  def cleanPlot(self, plot):
      return UNESCAPE(plot.replace('<p>','').replace('</p>',''))

  def buildDir(self, url, ilist, mode):
      a = requests.get(url).json()
      for b in a['data']:
          thumb = b.get('thumbnailUrl')
          fanart = b.get('imageUrl')
          name = b['title']
          if mode == 'GE':
              infoList = {'mediatype': 'tvshow',
                          'Title': name,
                          'TVShowTitle': name,
                          'Plot': self.cleanPlot(b.get('text'))}
              isfolder = True
              url = str(b['id'])
          else:
              infoList = {'mediatype': 'episode',
                          'Title': name,
                          'TVShowTitle': xbmc.getInfoLabel('ListItem.TVShowTitle'),
                          'Plot': self.cleanPlot(b.get('summary'))}
              isfolder = False
              url = b['video'].get('url')
              if url == None:
                  continue
          ilist = self.addMenuItem(name, mode, ilist, url, thumb, fanart, infoList, isFolder=isfolder)
      return(ilist)
 

  def getAddonMenu(self,url,ilist):
      ilist = self.addMenuItem(LCL(30000),'GS', ilist, 'live', self.addonIcon, self.addonFanart, {}, isFolder=True)
      return self.buildDir(''.join([RTBASE,'shows']), ilist, 'GE')


  def getAddonEpisodes(self,url,ilist):
      return self.buildDir(''.join([RTBASE,'shows/',url, '/episodes']), ilist, 'GV')


  def getAddonShows(self,url,ilist):
      chans = [(LCL(30001),'news','1103'),
              (LCL(30002),'usa','1105'),
              (LCL(30003),'uk','1106'),
              (LCL(30004),'doc','1101'),
              (LCL(30005),'esp','1102'),
              (LCL(30006),'france','1107'),
              (LCL(30007),'arab','1104')]
      for (name, url1, url2) in chans:
          url = ''.join(['https://rt-',url1,'-gd.secure2.footprint.net/',url2,'.m3u8'])
          ilist = self.addMenuItem(name,'GV', ilist, url, self.addonIcon, self.addonFanart, {}, isFolder=False)
      return(ilist)

