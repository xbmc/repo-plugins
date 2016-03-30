# -*- coding: utf-8 -*-
# Popcornflix Kodi Video Addon
#
from t1mlib import t1mAddon
import json
import re
import os
import datetime
import urllib
import urllib2
import xbmc
import xbmcplugin
import xbmcgui
import HTMLParser
import sys
import cookielib

h = HTMLParser.HTMLParser()
qp  = urllib.quote_plus
uqp = urllib.unquote_plus
UTF8     = 'utf-8'


class myAddon(t1mAddon):

  def getAddonMenu(self,url,ilist):
    ilist = self.addMenuItem('TV Shows', 'GS', ilist, 'http://www.snagfilms.com/shows/', self.addonIcon, self.addonFanart, {} , isFolder=True)
    html = self.getRequest('http://www.snagfilms.com/categories/')
    html = re.compile('Snag.page.data = (.+?);',re.DOTALL).search(html).group(1)
    a = json.loads(html)
    a = a[3]['data']['items']
    for item in a:
       url  = item['permalink']
       name = item['title']
       thumb  = item['image']
       ilist = self.addMenuItem(name, 'GM', ilist, url, thumb, self.addonFanart, {} , isFolder=True)
    return(ilist)

  def getAddonShows(self,url,ilist):
    html = self.getRequest(url)
    html = re.compile('Snag.page.data = (.+?)];',re.DOTALL).search(html).group(1)
    html += ']'
    a = json.loads(html)
    for b in a[2:]:
      try: c = b['data']['items']
      except: break
      for item in c:
       url  = item['permalink']
       name = item['title']
       thumb  = item['images']['poster']
       fanart = item['images']['landscape']
       infoList ={}
       infoList['TVShowTitle'] = name
       infoList['Title'] = name
       try: infoList['MPAA'] = item['rating']
       except: pass
       infoList['Plot'] = h.unescape(item['description'])
       infoList['Season'] = -1
       infoList['Episode'] = item['no_of_episodes']
       ilist = self.addMenuItem(name, 'GE', ilist, url, thumb, fanart, infoList , isFolder=True)
    return(ilist)

  def getAddonEpisodes(self,url,ilist):
    c_url = uqp(url)
    cat_url = c_url.split('#',1)[0]
    if not (cat_url.startswith('http')): cat_url = 'http://www.snagfilms.com%s' % cat_url
    cj = cookielib.CookieJar()
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
    urllib2.install_opener(opener)
    html = self.getRequest(cat_url)
    x_url = re.compile('rel="canonical" href="(.+?)"',re.DOTALL).search(html).group(1)
    try:    showid = re.compile('data-content-id="(.+?)"',re.DOTALL).search(html).group(1)
    except: showid = ''
    url3 = 'http://www.snagfilms.com/apis/show/%s' % (showid)
    url2 = 'http://www.snagfilms.com/apis/user/incrementPageView'
    user_data = urllib.urlencode({'url': x_url})
    headers = self.defaultHeaders
    headers['X-Requested-With'] = 'XMLHttpRequest'
    html = self.getRequest(url2, user_data, headers)
    html = self.getRequest(url3, None , headers)
    a = json.loads(html)
    for season in a['show']:
     for show in a['show'][season]:
        url = show['id']
        name  = show['title']
        thumb = show['images']['image'][0]['src']
        if ('url=' in thumb):
          thumb = urllib.unquote_plus(thumb)
          thumb = thumb.split('url=',1)[1]
        if ('ytimg' in thumb):
          ytid = thumb.split('/')[4]
          url = 'plugin://plugin.video.youtube/?path=/root/video&action=play_video&videoid=%s' % (ytid)
        infoList ={}
        infoList['Title'] = name
        infoList['Plot']  = h.unescape(show['description'])
        infoList['Genre'] = show['primaryCategory']['title']
        try: infoList['Year']  = show['year']
        except: pass
        infoList['MPAA']  = show['parentalRating']
        infoList['duration'] = int(show['durationMinutes']*60)
        infoList['tagline'] = show['logline']
        infoList['Season'] = 0
        infoList['Episode'] = 0
        ilist = self.addMenuItem(name,'GV', ilist, url, thumb, self.addonFanart, infoList, isFolder=False)
    return(ilist)



  def getAddonMovies(self,url,ilist):
    self.defaultVidStream['width']  = 1280
    self.defaultVidStream['height'] = 720
    url = uqp(url)
    if not url.startswith('http'): url = 'http://www.snagfilms.com%s' % url
    html = self.getRequest(url)
    html = re.compile('Snag.page.data = (.+?)];',re.DOTALL).search(html).group(1)
    html = html + ']'
    a = json.loads(html)
    for item in a[1]['data']['items']:
            infoList ={}
            name = h.unescape(item['title'])
            infoList['Title'] = name
            infoList['Plot'] = h.unescape(item['description'])
            infoList['Duration'] = int(item['durationMinutes']*60)
            try: infoList['Year'] = int(item['year'])
            except: pass
            url = item['id']
            thumb  = item['images']['poster']
            fanart = item['images']['landscape']
            ilist = self.addMenuItem(name,'GV', ilist, url, thumb, fanart, infoList, isFolder=False)
    return(ilist)


  def getAddonVideo(self,url):
    html = self.getRequest('http://www.snagfilms.com/embed/player?filmId=%s' % uqp(url))
    url = re.compile('file: "(.+?)"', re.DOTALL).findall(html)
    u = ''
    for x in url: 
      if '6912k' in x: u = x
    if u == '' : u = url[-1]
    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, xbmcgui.ListItem(path=u))

