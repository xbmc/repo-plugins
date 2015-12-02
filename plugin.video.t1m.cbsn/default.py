# -*- coding: utf-8 -*-
# KodiAddon (CBSN News Live)
#
from t1mlib import t1mAddon
import json
import re
import urllib
import xbmcplugin
import datetime

UTF8 = 'utf-8'

class myAddon(t1mAddon):

 def getAddonMenu(self,url,ilist):

   xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
   bselect = int(self.addon.getSetting('bselect'))
   bwidth = ['120','360','700','1200','1800','2200','4000']
   bw = 'index_%s' % (bwidth[bselect])
   c = [{'type':'dvr',
        'url' :'http://cbsnewshd-lh.akamaihd.net/i/CBSN_2@199302/%s_av-b.m3u8?sd=10&rebase=on' % bw,
        'startDate' : str(datetime.date.today()),
        'segmentDur'  : '59:59',
        'headline'  : 'LIVE',
        'headlineshort' : 'LIVE',
        'thumbnail_url_hd' : self.addonIcon.replace('\\','/')}]

   html = self.getRequest('http://cbsn.cbsnews.com/rundown/?device=desktop')
   a = json.loads(html)
   a = a["navigation"]["data"]
   c.extend(a)
   for b in c:
    if b['type'] == 'dvr':
      url = b["url"].replace('index_700',bw)
      url = url.encode(UTF8)
      infoList = {}
      infoList['Date']        = b['startDate'].split(' ',1)[0]
      infoList['Aired']       = infoList['Date']
      dur = b['segmentDur'].split(':')
      infoList['Duration']    = str(int(dur[0])*60+int(dur[1]))
      infoList['MPAA']        = ''
      infoList['TVShowTitle'] = 'CBSN News Live'
      infoList['Title']       = b['headlineshort']
      infoList['Studio']      = 'CBSN'
      infoList['Genre']       = 'News'
      infoList['Season']      = None
      infoList['Episode']     = -1
      infoList['Year']        = int(infoList['Aired'].split('-',1)[0])
      infoList['Plot']        = '%s UTC\n%s' % (b['startDate'], b['headline'])
      thumb  = b['thumbnail_url_hd'].replace('\\','')
      fanart = self.addonFanart
      name   = b['headlineshort']
      ilist = self.addMenuItem(name,'GV', ilist, url, thumb, fanart, infoList, isFolder=False)
   return(ilist)

# Start of Module

addonName = re.search('plugin\://plugin.video.(.+?)/',str(sys.argv[0])).group(1)
ma = myAddon(addonName)
ma.processAddonEvent()
del myAddon
