# -*- coding: utf-8 -*-
# KodiAddon (CBC News)
#
from t1mlib import t1mAddon
import datetime
import json
import re
import urllib
import urllib2
import xbmcplugin
import xbmcgui
import HTMLParser
import sys
import xbmc

h = HTMLParser.HTMLParser()
UTF8 = 'utf-8'

class myAddon(t1mAddon):

 def getAddonMenu(self,url,ilist):
   html = self.getRequest('https://www.cbc.ca/player')
   shows = re.compile('<h2 class="section-title"[^>]*><a[^>]* href="(.+?)">(.+?)</a>', re.DOTALL).findall(html)
   shows.append(('/player/news/TV%20Shows/MarketPlace', self.addon.getLocalizedString(30001)))
   shows.append(('/player/news/TV%20Shows/Power%20&%20Politics', self.addon.getLocalizedString(30003)))
   shows.append(('/player/news/TV%20Shows/The%20Fifth%20Estate', self.addon.getLocalizedString(30004)))
   shows.append(('/player/news/TV%20Shows/The%20National/Latest%20Broadcast', self.addon.getLocalizedString(30005)))
   shows.append(('/player/news/TV%20Shows/The%20Weekly', self.addon.getLocalizedString(30006)))
   for url, name in shows:
      mode = 'GS'
      if 'TV%20Shows' in url:
          mode = 'GE'
      infoList = {}
      infoList['mediatype'] = 'tvshow'
      infoList['Title'] = name
      infoList['TVShowTitle'] = name
      infoList['Plot'] = name
      ilist = self.addMenuItem(name, mode, ilist, url, self.addonIcon, self.addonFanart, infoList, isFolder=True)
   return(ilist)


 def getAddonCats(self,url,ilist):
   html = self.getRequest('https://www.cbc.ca/news/local')
   html = re.compile('window.__INITIAL_STATE__ = (.+?);</script>', re.DOTALL).search(html).group(1)
   a = json.loads(html)
   for b in a['regions']['regionList']:
       name = b['title']
       url = b['link']
       infoList = {}
       infoList['mediatype'] = 'tvshow'
       infoList['Title'] = name
       infoList['TVShowTitle'] = name
       infoList['Plot'] = name
       lurl = "/player/"+url
       ilist = self.addMenuItem(name, 'GE', ilist, lurl, self.addonIcon, self.addonFanart, infoList, isFolder=True)
   return(ilist)


 def getAddonShows(self,url,ilist):
   html  = self.getRequest('https://www.cbc.ca%s' % url)
   shows = re.compile('<h2 class="section-title"[^>]*><a[^>]* href="(.+?)">(.+?)</a>', re.DOTALL).findall(html)
   if not any(shows) or ('TV%20Shows' in url) or url.endswith('world') or url.endswith('live'):
       ilist = self.getAddonEpisodes(url, ilist)
   else:
       mshows = re.compile('<li class="more-categories">(.+?)</li', re.DOTALL).search(html)
       if not (mshows is None):
           mshows = mshows.group(1)
           mshows = re.compile('<option value="(.+?)">(.+?)<', re.DOTALL).findall(mshows)
           shows.extend(mshows)
       for lurl, name in shows:
           name = h.unescape(name)
           infoList = {}
           infoList['mediatype'] = 'tvshow'
           infoList['Title'] = name
           infoList['TVShowTitle'] = name
           infoList['Plot'] = name
           if lurl == '/player/news/canada':
              mode = 'GC'
           elif ('TV%20Shows' in lurl) or not (mshows is None):
              mode = 'GE'
           else:
              mode = 'GS'
           ilist = self.addMenuItem(name, mode, ilist, lurl, self.addonIcon, self.addonFanart, infoList, isFolder=True)
   return(ilist)


 def getAddonEpisodes(self,url,ilist):
   usubst = [('//','/'), ('prince-edward-island','pei'),('british-columbia','bc'),
             ('thunder-bay','thunder%20bay'), ('new-brunswick','nb'), ('nova-scotia','ns'), ('newfoundland-labrador','nl'),
             ('print&#x27;s',"print's")]
   self.defaultVidStream['width']  = 1280
   self.defaultVidStream['height'] = 720
   for (u1,u2) in usubst:
       url = url.replace(u1,u2)
   cat = url.rsplit('/',1)[1].replace('%20',' ').lower()
   html = self.getRequest('https://cbc.ca' + url)
   html = re.compile('window.__INITIAL_STATE__ = (.+?);</script>', re.DOTALL).search(html).group(1)
   a = json.loads(html)
   if cat == 'live':
       a = a['video']['liveClips']['onNow']
   else:
       a = [v for k,v in a['video']['clipsByCategory'].items() if k.lower().endswith(cat)][0]
   for b in a['items']:
      name = h.unescape(b['title'])
      plot = h.unescape(b['description'])
      vurl = str(b['id'])  # mediaID
      thumb = b['thumbnail']
      fanart = thumb
      if b['captions']:
         captions = b['captions']['src']
      else:
         captions = ''
      vurl = str(vurl)+'|'+str(captions)
      infoList = {}
      infoList['mediatype'] = 'episode'
      infoList['Title'] = name
      infoList['TVShowTitle'] = name
      infoList['Plot'] = plot
      infoList['Duration'] = b['duration']
      infoList['Aired'] = datetime.datetime.fromtimestamp(b['airDate']/1000).strftime('%Y-%m-%d')
      ilist = self.addMenuItem(name, 'GV', ilist, vurl, thumb, fanart, infoList, isFolder=False)
   return(ilist)


 def getAddonVideo(self,url):
      url = url.split('|',1)
      captions = url[1]
      u = ''.join(['https://link.theplatform.com/s/ExhSPC/media/guid/2655402169/',url[0],'/meta.smil?mbr=true&manifest=m3u&feed=Player%20Selector%20-%20Prod'])
      liz = xbmcgui.ListItem(path = u)
      if len(captions) > 0:
          liz.setSubtitles([captions])
      liz.setProperty('inputstreamaddon','inputstream.adaptive')
      liz.setProperty('inputstream.adaptive.manifest_type','hls')
      liz.setMimeType('application/x-mpegURL')
      xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)
