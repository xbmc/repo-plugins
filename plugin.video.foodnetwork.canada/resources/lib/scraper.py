# -*- coding: utf-8 -*-
# Food Network Canada Kodi Video Addon
#
from t1mlib import t1mAddon
import re
import os
import xbmc
import datetime
import xbmcplugin
import xbmcgui
import html.parser
import sys
import requests

UNESCAPE = html.parser.HTMLParser().unescape


class myAddon(t1mAddon):

  def getAddonMenu(self,url,ilist):
    html = requests.get('https://www.foodnetwork.ca/shows/', headers=self.defaultHeaders).text
    html = re.compile('<section class="top-shows">(.+?)</ul>', re.DOTALL).search(html).group(1)
    a = re.compile('href="(.+?)".+?data-src="(.+?)".+?<h3>(.+?)<(.+?)</li>', re.DOTALL).findall(html)
    for url, thumb, name, extracrap in a:
        if 'Full Episodes' in extracrap:
            name = UNESCAPE(name)
            thumb = thumb.replace(' ','%20') #really? spaces in a url?
            fanart = thumb
            infoList = {'mediatype':'tvshows',
                        'Title' : name,
                        'TVShowTitle' : name,
                        'Plot' : name}
            ilist = self.addMenuItem(name,'GE', ilist, url, thumb, fanart, infoList, isFolder=True)
    return(ilist)


  def getAddonEpisodes(self,url,ilist):
    self.defaultVidStream['width']  = 960
    self.defaultVidStream['height'] = 540
    if not url.endswith('/video/'):
        if url.endswith('/'):
            urlend = 'video/'
        else:
            urlend = '/video/'
    else:
        urlend = ''
    url = ''.join(['https://www.foodnetwork.ca',url,urlend])
    html = requests.get(url).text
    endpoint, geurl = re.compile('endpoint: "(.+?)".+?categories: "(.+?)"', re.DOTALL).search(html).groups()
    url = ''.join([endpoint,'?byCategories=',geurl,'&form=cjson&count=true&startIndex=1&endIndex=150&fields=id,content,defaultThumbnailUrl,title,description,:show,:season,:episode,pubdate,availableDate,:clipType,restrictionID,:allowHTML5&sort=pubDate|desc&callback='])
    a = requests.get(url).json()
    for b in a['entries']:
        for c in b['sources']:
            if c['type'] == 'hls':
                url = c['file']
        name = UNESCAPE(b['title'])
        thumb = b.get('defaultThumbnailUrl')
        fanart = thumb
        adate = datetime.datetime.fromtimestamp(b['pubDate']/1000).strftime('%Y-%m-%d')
        infoList = {'mediatype': 'episode',
                    'Title': name,
                    'TVShowTitle': b.get('pl1$show'),
                    'Plot': UNESCAPE(b["description"]),
                    'Duration': int(b['content'][0]['duration']),
                    'Studio': b.get('pl1$network'),
                    'Date': adate,
                    'Aired': adate,
                    'Year': int(adate.split('-',1)[0])}
        episode = b.get('pl1$episode')
        if episode is not None and episode.isdigit():
            infoList['Episode'] = int(episode)
        season = b.get('pl1$season')
        if season is not None and season.isdigit():
            infoList['Season'] = int(season)
        else:
            infoList['Season'] = 1
        ilist = self.addMenuItem(name,'GV', ilist, url, thumb, fanart, infoList, isFolder=False)
    return(ilist)


  def getAddonVideo(self,url):
    html = requests.get(url).text #Canada Only
    url = re.compile('video src="(.+?)"', re.DOTALL).search(html).group(1)
    liz = xbmcgui.ListItem(path = url)
    liz.setProperty('inputstream','inputstream.adaptive')
    liz.setProperty('inputstream.adaptive.manifest_type','hls')
    liz.setMimeType('application/x-mpegURL')
    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)
