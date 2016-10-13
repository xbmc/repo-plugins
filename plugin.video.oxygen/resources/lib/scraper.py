# -*- coding: utf-8 -*-
# KodiAddon (Oxygen Channel)
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

h = HTMLParser.HTMLParser()
qp  = urllib.quote_plus
uqp = urllib.unquote_plus
UTF8     = 'utf-8'
OXYGENBASE = 'http://www.oxygen.com%s'

class myAddon(t1mAddon):

  def getAddonMenu(self,url,ilist):
    addonLanguage  = self.addon.getLocalizedString
    basehtml = self.getRequest('http://www.oxygen.com/full-episodes')
    cats = re.compile('<article class="all-shows">.+?href="(.+?)".+?title="(.+?)".+?data-src="(.+?)".+?</article',re.DOTALL).findall(basehtml)
    numShows = len(cats)
    for url, name, thumb in cats:
        url = OXYGENBASE % (url)
        name = name.strip()
        fanart = thumb
        infoList = {}
        infoList['TVShowTitle'] = name
        infoList['Title']       = name
        ilist = self.addMenuItem(name,'GE', ilist, url, thumb, fanart, infoList, isFolder=True)
    return(ilist)


  def getAddonEpisodes(self,url,ilist):
    addonLanguage  = self.addon.getLocalizedString
    self.defaultVidStream['width']  = 1920
    self.defaultVidStream['height'] = 1080
    sname = url
    epiHTML = self.getRequest(url)
    (tvshow,  fanart) = re.compile('og:title" content="(.+?)".+?"og:image" content="(.+?)"',re.DOTALL).search(epiHTML).groups()
    epis = re.compile('<li class="watch__thumbnail.+?href="(.+?)".+?</ul>',re.DOTALL).findall(epiHTML)
    for url in epis:
        burl  = OXYGENBASE % url
        print "burl = "+str(burl)
        html = self.getRequest(burl)
        purl = re.compile('data-src="(.+?)"',re.DOTALL).search(html)
        if not purl is None:
            purl = purl.group(1)
        else:
            continue
        purl = purl.split('?',1)[0]
        purl = purl.split('/select/',1)[1]
        url = purl
        purl = 'http://link.theplatform.com/s/HNK2IC/'+purl+'?mbr=true&player=Oxygen%20VOD%20Player%20%28Phase%203%29&format=Script&height=576&width=1024'
        html = self.getRequest(purl)
        a = json.loads(html)
        infoList = {}
        infoList['Date']        = datetime.datetime.fromtimestamp(a['pubDate']/1000).strftime('%Y-%m-%d')
        infoList['Aired']       = infoList['Date']
        infoList['MPAA']        = a['ratings'][0]['rating']
        infoList['Studio']      = a['provider']
        infoList['Genre']       = (a['nbcu$advertisingGenre']).replace('and','/')
        try: infoList['Episode'] = int(a['pl1$episodeNumber'])
        except: infoList['Episode'] = -1
        try: infoList['Season']  = int(a['pl1$seasonNumber'])
        except: infoList['Season']  = 0
        infoList['Year']        = int(infoList['Aired'].split('-',1)[0])
        infoList['Plot'] = h.unescape(a['description'])
        infoList['TVShowTitle'] = tvshow
        infoList['Title']       = a['title']
        name = a['title']
        thumb = a['defaultThumbnailUrl']
        name = name.encode(UTF8)
        ilist = self.addMenuItem(name,'GV', ilist, url, thumb, fanart, infoList, isFolder=False)
    return(ilist)


  def getAddonVideo(self,url):
    gvu1 = 'https://tveoxygen-vh.akamaihd.net/i/prod/video/%s_,40,25,18,12,7,4,2,00.mp4.csmil/master.m3u8?b=&__b__=1000&hdnea=st=%s~exp=%s'
    gvu2 = 'https://tveoxygen-vh.akamaihd.net/i/prod/video/%s_,1696,1296,896,696,496,240,306,.mp4.csmil/master.m3u8?b=&__b__=1000&hdnea=st=%s~exp=%s'
    url = 'http://link.theplatform.com/s/HNK2IC/'+url+'?mbr=true&player=Oxygen%20VOD%20Player%20%28Phase%203%29&format=Script&height=576&width=1024'
    html = self.getRequest(url)
    a = json.loads(html)
    suburl = a["captions"][0]["src"]
    url = suburl.split('/caption/',1)[1]
    url = url.split('.',1)[0]
    td = (datetime.datetime.utcnow()- datetime.datetime(1970,1,1))
    unow = int((td.microseconds + (td.seconds + td.days * 24 * 3600) * 10**6) / 10**6)
    u   =  gvu1 % (url, str(unow), str(unow+60))
    req = urllib2.Request(u.encode(UTF8), None, self.defaultHeaders)
    try:
       response = urllib2.urlopen(req, timeout=20) # check to see if video file exists
    except:
       u   =  gvu2 % (url, str(unow), str(unow+60))
    liz = xbmcgui.ListItem(path = u)

    subfile = self.procConvertSubtitles(suburl)
    if subfile != "" : liz.setSubtitles([subfile])
    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)
