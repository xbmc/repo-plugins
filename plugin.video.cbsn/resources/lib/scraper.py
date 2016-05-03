# -*- coding: utf-8 -*-
# KodiAddon (CBSN News Live)
#
from t1mlib import t1mAddon
import json
import re
import urllib
import xbmcplugin
import datetime
import sys

UTF8 = 'utf-8'

class myAddon(t1mAddon):

 def getAddonMenu(self,url,ilist):

   xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
   html = self.getRequest('http://cbsn1.cbsistatic.com/scripts/VideoPlayer.js')
   try:
       urlbase = re.compile("this.hlsurl =  '(.+?)'", re.DOTALL).search(html).group(1)
   except:
       urlbase = re.compile("this.hlsurl_na =  '(.+?)'", re.DOTALL).search(html).group(1)
   urlbase = urlbase.rsplit('/',1)[0]
   bselect = int(self.addon.getSetting('bselect'))
   bwidth = ['120','360','700','1200','1800','2200','4000']
   bw = 'index_%s' % (bwidth[bselect])
   c = [{'type':'dvr',
        'url' :'%s/%s_av-p.m3u8?sd=10&rebase=on' % (urlbase, bw),
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
      infoList['mediatype']   = 'episode'
      thumb  = b['thumbnail_url_hd'].replace('\\','')
      fanart = self.addonFanart
      name   = b['headlineshort']
      ilist = self.addMenuItem(name,'GV', ilist, url, thumb, fanart, infoList, isFolder=False)
   return(ilist)
