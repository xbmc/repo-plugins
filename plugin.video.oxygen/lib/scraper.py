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
    meta = self.getAddonMeta()
    try:    i = len(meta['shows'])
    except: meta['shows']={}
    basehtml = self.getRequest('http://www.oxygen.com/full-episodes')
    cats = re.compile('<article class="all-shows">.+?href="(.+?)".+?title="(.+?)".+?data-src="(.+?)".+?</article',re.DOTALL).findall(basehtml)
    dirty = False
    pDialog = xbmcgui.DialogProgress()
    pDialog.create(self.addonName, addonLanguage(30101))
    pDialog.update(0)
    numShows = len(cats)
    for i, (url, name, thumb) in list(enumerate(cats, start=1)):
      url = OXYGENBASE % (url)
      try:   (name, thumb, fanart, infoList) = meta['shows'][url]
      except:
        dirty = True
        name = name.strip()
        fanart = thumb
        epiHTML = self.getRequest(url)
        epis = re.compile('<li class="watch__episode.+?href="(.+?)".+?</ul>',re.DOTALL).findall(epiHTML)
        vcnt = len(epis)
        if vcnt == 0: continue
        if epis[len(epis)-1][0] != '/' : epis[len(epis)-1] = '/'+epis[len(epis)-1]
        html = self.getRequest(OXYGENBASE % epis[len(epis)-1])
        try:
          purl = re.compile('data-src="(.+?)"',re.DOTALL).search(html).group(1)
        except:
          continue

        purl = purl.split('?',1)[0]
        purl = purl.split('/select/',1)[1]
        purl = 'http://link.theplatform.com/s/HNK2IC/'+purl+'?mbr=true&player=Oxygen%20VOD%20Player%20%28Phase%203%29&format=Script&height=576&width=1024'
        html = self.getRequest(purl)
        a = json.loads(html)
        infoList = {}
        infoList['Date']        = datetime.datetime.fromtimestamp(a['pubDate']/1000).strftime('%Y-%m-%d')
        infoList['Aired']       = infoList['Date']
        infoList['MPAA']        = a['ratings'][0]['rating']
        infoList['TVShowTitle'] = name
        infoList['Title']       = name
        infoList['Studio']      = a['provider']
        infoList['Genre']       = (a['nbcu$advertisingGenre']).replace('and','/')
        infoList['Episode']     = vcnt
        infoList['Year']        = int(infoList['Aired'].split('-',1)[0])
        try:
           infoList['Plot'] = re.compile('"og:description" content="(.+?)"',re.DOTALL).search(epiHTML).group(1)
           infoList['Plot'] = h.unescape(infoList['Plot'].decode('utf-8'))
        except: pass
        meta['shows'][url] = (name, thumb, fanart, infoList)
      ilist = self.addMenuItem(name,'GE', ilist, url, thumb, fanart, infoList, isFolder=True)
      pDialog.update(int((100*i)/numShows))
    pDialog.close()
    if dirty == True: self.updateAddonMeta(meta)
    return(ilist)


  def getAddonEpisodes(self,url,ilist):
    addonLanguage  = self.addon.getLocalizedString
    self.defaultVidStream['width']  = 1920
    self.defaultVidStream['height'] = 1080
    sname = url
    meta = self.getAddonMeta()
    try:    i = len(meta[sname])
    except: meta[sname]={}
    epiHTML = self.getRequest(url)
    (tvshow,  fanart) = re.compile('og:title" content="(.+?)".+?"og:image" content="(.+?)"',re.DOTALL).search(epiHTML).groups()
    epis = re.compile('<li class="watch__episode.+?href="(.+?)".+?</ul>',re.DOTALL).findall(epiHTML)
    pDialog = xbmcgui.DialogProgress()
    pDialog.create(self.addonName, addonLanguage(30101))
    pDialog.update(0)
    numShows = len(epis)
    dirty = False
    for i,url in list(enumerate(epis, start=1)):
      burl  = OXYGENBASE % url
      try:
        (name, url, thumb, fanart, infoList) = meta[sname][burl]
      except: 
        html = self.getRequest(burl)
        try:
           purl = re.compile('data-src="(.+?)"',re.DOTALL).search(html).group(1)
        except: continue
        dirty = True
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
        meta[sname][burl] = (name, url, thumb, fanart, infoList)
      name = name.encode(UTF8)
      ilist = self.addMenuItem(name,'GV', ilist, url, thumb, fanart, infoList, isFolder=False)
      pDialog.update(int((100*i)/numShows))
    pDialog.close()
    if dirty == True: self.updateAddonMeta(meta)
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

    subfile = ""
    profile = self.addon.getAddonInfo('profile').decode(UTF8)
    prodir  = xbmc.translatePath(os.path.join(profile))
    if not os.path.isdir(prodir):
       os.makedirs(prodir)

    pg = self.getRequest(suburl)
    if pg != "":
        subfile = xbmc.translatePath(os.path.join(profile, 'subtitles.srt'))
        ofile = open(subfile, 'w+')
        captions = re.compile('<p begin="(.+?)" end="(.+?)">(.+?)</p>',re.DOTALL).findall(pg)
        for idx, (cstart, cend, caption) in list(enumerate(captions, start=1)):
          cstart = cstart.replace('.',',')
          cend   = cend.replace('.',',').split('"',1)[0]
          caption = caption.replace('<br/>','\n')
          try:    caption = h.unescape(caption)
          except: pass
          ofile.write( '%s\n%s --> %s\n%s\n\n' % (idx, cstart, cend, caption))
        ofile.close()

    if subfile != "" : liz.setSubtitles([subfile])
    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)
