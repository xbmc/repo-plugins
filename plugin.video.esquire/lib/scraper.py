# -*- coding: utf-8 -*-
# KodiAddon (Esquire TV)
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
ESQUIREBASE = 'http://tv.esquire.com%s'

class myAddon(t1mAddon):

  def getAddonMenu(self,url,ilist):
    addonLanguage  = self.addon.getLocalizedString
    meta = self.getAddonMeta()
    try:    i = len(meta['shows'])
    except: meta['shows']={}

    html = self.getRequest('http://tv.esquire.com/now/')
    blob = re.compile('<div class="shows">(.+?)</div',re.DOTALL).search(html).group(1)
    cats = re.compile('<a href="(.+?)".+?>(.+?)</a',re.DOTALL).findall(blob)

    dirty = False
    pDialog = xbmcgui.DialogProgress()
    pDialog.create(self.addonName, addonLanguage(30101))
    pDialog.update(0)
    numShows = len(cats)
    for i, (url, name) in list(enumerate(cats, start=1)):

      name = name.strip()
      name = h.unescape(name.decode(UTF8))
      url = ESQUIREBASE % (url)
      try:   (name, thumb, fanart, infoList) = meta['shows'][url]
      except:
        dirty = True
        html  = self.getRequest(url)
        thumb = self.addonIcon
        try:    fanart = re.compile('<img class="showBaner" src="(.+?)"',re.DOTALL).search(html).group(1)
        except: fanart = addonfanart
        try:    plot = re.compile('"twitter:description" content="(.+?)"',re.DOTALL).search(html).group(1)
        except: plot = ''
        html = re.compile("Drupal\.settings, (.+?)\);<",re.DOTALL).search(html).group(1)
        a = json.loads(html)
        try:    b = a["tve_widgets"]["clone_of_latest_episodes"]["assets1"][0]
        except: continue
        infoList = {}
        dstr = (b['aired_date'].split('-'))
        infoList['Date']        = '%s-%s-%s' % (dstr[2], dstr[0].zfill(2), dstr[1].zfill(2))
        infoList['Aired']       = infoList['Date']
        infoList['MPAA']        = ''
        infoList['TVShowTitle'] = b['show_title']
        infoList['Title']       = b['show_title']
        infoList['Studio']      = 'Esquire'
        infoList['Genre']       = ''
        infoList['Episode']     = int(a["tve_widgets"]["clone_of_latest_episodes"]["assets_number"])
        infoList['Year']        = int(infoList['Aired'].split('-',1)[0])
        infoList['Plot']        = h.unescape(plot.decode(UTF8))
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
    html = self.getRequest(url)
    try:    fanart = re.compile('<img class="showBaner" src="(.+?)"',re.DOTALL).search(html).group(1)
    except: fanart = self.addonfanart
    html = re.compile("Drupal\.settings, (.+?)\);<",re.DOTALL).search(html).group(1)
    epis = json.loads(html)
    epis = epis["tve_widgets"]["clone_of_latest_episodes"]["assets1"]
    pDialog = xbmcgui.DialogProgress()
    pDialog.create(self.addonName, addonLanguage(30101))
    pDialog.update(0)
    numShows = len(epis)
    for i,b in list(enumerate(epis, start=1)):
      infoList = {}
      dstr = (b['aired_date'].rsplit('-'))
      infoList['Date']        = '%s-%s-%s' % (dstr[2], dstr[0].zfill(2), dstr[1].zfill(2))
      infoList['Aired']       = infoList['Date']
      infoList['MPAA']        = ''
      infoList['TVShowTitle'] = b['show_title']
      infoList['Title']       = b['episode_title']
      infoList['Studio']      = 'Esquire'
      infoList['Genre']       = ''
      infoList['Season']      = b['season_n']
      infoList['Episode']     = b['episode_n']
      infoList['Year']        = int(infoList['Aired'].split('-',1)[0])
      infoList['Plot']        = h.unescape(b["synopsis"])
      thumb = b["episode_thumbnail"]["url"]
      url   = b['link']
      name  = b['episode_title']
      ilist = self.addMenuItem(name,'GV', ilist, url, thumb, fanart, infoList, isFolder=False)
      pDialog.update(int((100*i)/numShows))
    pDialog.close()
    return(ilist)


  def getAddonVideo(self,url):
    gvu1 = 'https://tveesquire-vh.akamaihd.net/i/prod/video/%s_,1696,1296,896,696,496,240,306,.mp4.csmil/master.m3u8?__b__=1000&hdnea=st=%s~exp=%s'
    url = ESQUIREBASE % url
    html = self.getRequest(url)
    url = re.compile('data-release-url="(.+?)"',re.DOTALL).search(html).group(1)
    url = 'http:'+url+'&player=Esquire%20VOD%20Player%20%28Phase%203%29&format=Script&height=576&width=1024'
    html = self.getRequest(url)

    a = json.loads(html)
    suburl = a["captions"][0]["src"]
    url = suburl.split('/caption/',1)[1]
    url = url.split('.',1)[0]
    td = (datetime.datetime.utcnow()- datetime.datetime(1970,1,1))
    unow = int((td.microseconds + (td.seconds + td.days * 24 * 3600) * 10**6) / 10**6)
    u   =  gvu1 % (url, str(unow), str(unow+60))
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

