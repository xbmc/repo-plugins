# -*- coding: utf-8 -*-
# KodiAddon PBS ThinkTV
#
from t1mlib import t1mAddon
import json
import re
import os
import urllib
import urllib2
import cookielib
import xbmcplugin
import datetime
import xbmc
import xbmcgui
import HTMLParser

h = HTMLParser.HTMLParser()

UTF8 = 'utf-8'
showsPerPage = 24 # number of shows returned per page by PBS

class myAddon(t1mAddon):

 def doPBSLogin(self):
  if self.addon.getSetting('enable_login') != 'true' : return
  profile = self.addon.getAddonInfo('profile').decode(UTF8)
  pdir  = xbmc.translatePath(os.path.join(profile))
  if not os.path.isdir(pdir):
     os.makedirs(pdir)
  cjFile = xbmc.translatePath(os.path.join(profile, 'PBSCookies.dat'))
  try:
   cj = cookielib.LWPCookieJar()
   cj.load(cjFile)
   badCookie = True
   if self.addon.getSetting('init_meta') != 'true' :
     for cookie in cj:
      if cookie.name == 'sessionid':
         if not cookie.is_expired(): badCookie = False
   if badCookie == True:  raise ValueError('No valid cookie')
   opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
   urllib2.install_opener(opener)
   return

  except:
   cj = cookielib.LWPCookieJar(cjFile)
   opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
   urllib2.install_opener(opener)

   html = self.getRequest('http://www.pbs.org/shows/')
   url = re.compile('class="pbsColor inherit-link".+?href="(.+?)"', re.DOTALL).search(html).group(1)
   clientId = url.split('client_id=',1)[1]
   html = self.getRequest('https://account.pbs.org/oauth2/login/')
   lcsr, lnext = re.compile("name='csrfmiddlewaretoken'.+?value='(.+?)'.+?"+'name="next".+?value="(.+?)"', re.DOTALL).search(html).groups()
   username = self.addon.getSetting('login_name')
   password = self.addon.getSetting('login_pass')
   if username !='' and password !='':
        url1  = ('https://account.pbs.org/oauth2/login/')
        xheaders = self.defaultHeaders.copy()
        xheaders["Referer"]      = "https://account.pbs.org/oauth2/login/"
        xheaders["Host"]         = "account.pbs.org"
        xheaders["Origin"]       = "https://account.pbs.org"
        xheaders["Connection"]   = "keep-alive"
        xheaders["Accept"]       = "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
        xheaders["Content-Type"] = "application/x-www-form-urlencoded"
        udata = urllib.urlencode({'csrfmiddlewaretoken' : lcsr, 'next' : lnext, 'email' : username, 'password' : password})
        html = self.getRequest(url1, udata, xheaders)
        html = self.getRequest('https://account.pbs.org/oauth2/authorize/?scope=account&redirect_uri=http://www.pbs.org/login/&response_type=code&client_id=%s&confirmed=1' % clientId)
        for cookie in cj:
         if cookie.name == 'pbsol.station':
            self.addon.setSetting('pbsol', cookie.value)
        cj.save()


 def getAddonMenu(self,url,ilist):
   addonLanguage  = self.addon.getLocalizedString
   self.doPBSLogin()
   html = self.getRequest('http://www.pbs.org/shows-page/0/?genre=&title=&callsign=')
   a = json.loads(html)
   for b in a['genres'][1:]:
      ilist = self.addMenuItem(b['title'],'GS', ilist, str(b['id'])+'|0', self.addonIcon, self.addonFanart, None, isFolder=True)

   try:
     if self.addon.getSetting('enable_login') == 'true':
       pbsol = self.addon.getSetting('pbsol')
       if pbsol != '':
        xheaders = self.defaultHeaders.copy()
        xheaders['X-Requested-With'] = 'XMLHttpRequest'
        html = self.getRequest('http://www.pbs.org/shows-page/0/?genre=&title=&callsign=%s' % pbsol, None, xheaders)
        a = json.loads(html)
        if len(a['results']['content']) > 0:
           ilist = self.addMenuItem(addonLanguage(30048) ,'GS', ilist, 'localpbs' , self.addonIcon, self.addonFanart, None, isFolder=True)
   except: pass
   try:
        html = self.getRequest('http://www.pbs.org/favorite-shows-page/1/')
        a = json.loads(html)
        if a['totalResults'] > 0:
           ilist = self.addMenuItem(addonLanguage(30004),'GS', ilist, 'favorites' , self.addonIcon, self.addonFanart, None, isFolder=True)
   except: pass
   try:
        xheaders = self.defaultHeaders.copy()
        xheaders['X-Requested-With'] = 'XMLHttpRequest'
        html = self.getRequest('http://www.pbs.org/watchlist/page/1/', None, xheaders)
        a = json.loads(html)
        if len(a['videos']) > 0:
           ilist = self.addMenuItem(addonLanguage(30005) ,'GM', ilist, 'pbswatchlist' , self.addonIcon, self.addonFanart, None, isFolder=True)
   except: pass
   return ilist


 def getAddonShows(self,url,ilist):
    pgNum = ''
    addonLanguage  = self.addon.getLocalizedString
    self.doPBSLogin()
    addonLanguage  = self.addon.getLocalizedString
    meta = self.getAddonMeta()
    try:    i = len(meta['shows'])
    except: meta['shows']={}
    gsurl = url
    if gsurl == 'favorites':
        html = self.getRequest('http://www.pbs.org/favorite-shows-page/1/')
        a = json.loads(html)
        cats = a['content']
    elif gsurl == 'localpbs':
        xheaders = self.defaultHeaders.copy()
        xheaders['X-Requested-With'] = 'XMLHttpRequest'
        pbsol = self.addon.getSetting('pbsol')
        html = self.getRequest('http://www.pbs.org/shows-page/0/?genre=&title=&callsign=%s&alphabetically=true' % (pbsol), None, xheaders)
        a = json.loads(html)
        cats = a['results']['content']
    else:
        genreUrl, pgNum = url.split('|',1) 
        xheaders = self.defaultHeaders.copy()
        xheaders['X-Requested-With'] = 'XMLHttpRequest'
        html = self.getRequest('http://www.pbs.org/shows-page/%s/?genre=%s&title=&callsign=' % (pgNum, genreUrl), None, xheaders)
        a = json.loads(html)
        cats = a['results']['content']
    dirty = False
    pDialog = xbmcgui.DialogProgress()
    pDialog.create(self.addonName, addonLanguage(30101))
    pDialog.update(0)
    numShows = len(cats)
    for i, (b) in list(enumerate(cats, start=1)):
      url = b['id']
      try:   (name, thumb, fanart, infoList) = meta['shows'][url]
      except:
        dirty = True
        name   = b['title']
        thumb  = b['image']
        if thumb == None : thumb = self.addonIcon
        fanart = b['image']
        if fanart == None: fanart = self.addonFanart
        infoList = {}
        infoList['TVShowTitle'] = name
        infoList['Title']       = name
        try:    infoList['Studio'] = b['producer']
        except: pass
        try:    infoList['Genre']  = b['genre_titles'][0]
        except: pass
        try:    infoList['Episode'] = b['video_count']
        except: pass
        try:    infoList['Plot'] = b['description']
        except: pass
        meta['shows'][url] = (name, thumb, fanart, infoList)
      if self.addon.getSetting('enable_login') == 'true':
        if gsurl == 'favorites': contextMenu = [(addonLanguage(30006),'XBMC.Container.Update(%s?mode=DF&url=RF%s)' % (sys.argv[0], url))]
        else:           contextMenu = [(addonLanguage(30007),'XBMC.RunPlugin(%s?mode=DF&url=AF%s)' % (sys.argv[0], url))]
      else: contextMenu = None
      ilist = self.addMenuItem(name,'GC', ilist, '%s|%s|%s' % (url, thumb, fanart), thumb, fanart, infoList, isFolder=True, cm=contextMenu)
      pDialog.update(int((100*i)/numShows))
    if pgNum != '': ilist = self.addMenuItem('[COLOR blue]%s[/COLOR]' % addonLanguage(30050),'GS', ilist, genreUrl+'|'+str(int(pgNum)+1), self.addonIcon, self.addonFanart, None, isFolder=True)
    pDialog.close()
    if dirty == True: self.updateAddonMeta(meta)
    return(ilist)


 def getAddonCats(self,url,ilist):
    addonLanguage  = self.addon.getLocalizedString
    self.doPBSLogin()
    url, thumb, fanart =  url.split('|',2)
    html= self.getRequest('http://www.pbs.org/show/%s/episodes/' % url)
    try:   ecnt, ccnt, pcnt = re.compile('<ul class="video-catalog-nav">.+?<strong>(.+?)<.+?<strong>(.+?)<.+?<strong>(.+?)<', re.DOTALL).search(html).groups()
    except: 
      ecnt=''
      ccnt=''
      pcnt=''
    ilist = self.addMenuItem('%s (%s)' % (addonLanguage(30045),ecnt),'GE', ilist, '%s|%s|1' %(url, 'episodes'), thumb, fanart, None, isFolder=True)
    ilist = self.addMenuItem('%s (%s)' % (addonLanguage(30046),ccnt),'GE', ilist, '%s|%s|1' %(url, 'clips'), thumb, fanart, None, isFolder=True)
    ilist = self.addMenuItem('%s (%s)' % (addonLanguage(30047),pcnt),'GE', ilist, '%s|%s|1' %(url, 'previews'), thumb, fanart, None, isFolder=True)
    return(ilist)


 def getAddonEpisodes(self,url,ilist):
    self.doPBSLogin()
    addonLanguage  = self.addon.getLocalizedString
    url, stype, pageNum = url.split('|',2)
    sname = url
    meta = self.getAddonMeta()
    try:    i = len(meta[sname])
    except: meta[sname]={}
    html = self.getRequest('http://www.pbs.org/show/%s/%s/?page=%s' % (url, stype, pageNum))
    epis = re.compile('<article class="video-summary">.+?href="/video/(.+?)/.+?data-srcset="(.+?)".+?alt="(.+?)".+?class="description">(.+?)<.+?class="video-popover__duration">(.+?)<',re.DOTALL).findall(html)
    dirty = False
    pDialog = xbmcgui.DialogProgress()
    pDialog.create(self.addonName, addonLanguage(30101))
    pDialog.update(0)
    numShows = len(epis)
    for i, (url, imgs, name, plot, duration)  in list(enumerate(epis, start=1)):
      try:   (name, thumb, fanart, infoList) = meta[sname][url]
      except:
        dirty = True
        name = h.unescape(name.decode(UTF8))
        plot=plot.strip()
        duration = duration.strip()
        try:
           t = 0
           for dur in duration.split(':'): t = t*60 + int(dur.strip())
           duration = t
           infoList['duration'] = duration
        except: pass
        imgs = imgs.split(',')
        thumb  = '%s.jpg' % (imgs[2].split('.jpg',1)[0].strip())
        fanart = '%s.jpg' % (imgs[len(imgs)-1].split('.jpg',1)[0].strip())
        infoList = {}
        infoList['Title']       = name
        infoList['Plot'] = h.unescape(plot.decode(UTF8))
        meta[sname][url] = (name, thumb, fanart, infoList)
      if self.addon.getSetting('enable_login') == 'true': 
          contextMenu = [(addonLanguage(30008),'XBMC.RunPlugin(%s?mode=DF&url=AW%s)' % (sys.argv[0], url))]
      else: contextMenu = None
      ilist = self.addMenuItem(name,'GV', ilist, url, thumb, fanart, infoList, isFolder=False, cm=contextMenu)
      pDialog.update(int((100*i)/numShows))
    if numShows >= showsPerPage: ilist = self.addMenuItem('[COLOR blue]%s[/COLOR]' % addonLanguage(30050),'GE', ilist, '%s|%s|%s' %(sname, stype, str(int(pageNum)+1)), self.addonIcon, self.addonFanart, None, isFolder=True)
    pDialog.close()
    if dirty == True: self.updateAddonMeta(meta)
    return(ilist)


 def getAddonMovies(self,url,ilist):
    addonLanguage  = self.addon.getLocalizedString
    xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
    self.doPBSLogin()
    xheaders = self.defaultHeaders.copy()
    xheaders['X-Requested-With'] = 'XMLHttpRequest'
    html = self.getRequest('http://www.pbs.org/watchlist/page/1/', None, xheaders)
    a = json.loads(html)
    epis = a['videos']
    for i, b  in list(enumerate(epis, start=1)):
        infoList = []
        name = b['title']
        plot = b['description']
        duration = b['duration']
        try:
           t = 0
           for dur in duration.split(':'): t = t*60 + int(dur.strip())
           duration = t
           infoList['duration'] = duration
        except: pass
        thumb  = b['image']
        fanart = b['image']
        infoList = {}
        infoList['TVShowTitle'] = b['show']['title']
        infoList['Title'] = name
        infoList['Plot'] = plot
        url = b['id']
        contextMenu = [(addonLanguage(30009),'XBMC.Container.Update(%s?mode=DF&url=RW%s)' % (sys.argv[0], url))]
        ilist = self.addMenuItem(name,'GV', ilist, url, thumb, fanart, infoList, isFolder=False, cm=contextMenu)
    return(ilist)

 def doFunction(self, url):
    self.doPBSLogin()
    func = url[0:2]
    url  = url[2:]
    if   func == 'AW':
       html = self.getRequest('http://www.pbs.org/profile/addFavoriteVideo/%s/' % url)
    elif func == 'AF':
       html = self.getRequest('http://www.pbs.org/profile/addFavoriteProgram/%s/' % url)
    elif   func == 'RW':
       html = self.getRequest('http://www.pbs.org/profile/removeFavoriteVideo/%s/' % url)
    elif func == 'RF':
       html = self.getRequest('http://www.pbs.org/profile/removeFavoriteProgram/%s/' % url)
    try:
       a = json.loads(html)
       xbmc.executebuiltin('XBMC.Notification("%s", "%s", %s)' % ( self.addonName, a['errorMessage'] , 4000) )
    except: pass
       

 def getAddonVideo(self,url):
    addonLanguage  = self.addon.getLocalizedString
    pg = self.getRequest('http://player.pbs.org/viralplayer/%s' % (url))
    try:
       url,suburl = re.compile("PBS.videoData =.+?recommended_encoding.+?'url'.+?'(.+?)'.+?'closed_captions_url'.+?'(.+?)'", re.DOTALL).search(pg).groups()
       pg = self.getRequest('%s?format=json' % url)
       url = json.loads(pg)['url']
    except:
       xbmc.executebuiltin('XBMC.Notification("%s", "%s", %s)' % ( self.addonName, addonLanguage(30049) , 4000) )
       return
    if 'mp4:' in url: url = 'http://ga.video.cdn.pbs.org/%s' % url.split('mp4:',1)[1]
    elif ('.m3u8' in url) and self.addon.getSetting('vid_res') >= '1': 
         url = url.replace('800k','2500k')
         if ('hd-1080p' in url) and self.addon.getSetting('vid_res') == '2': 
           url = url.split('-hls-',1)[0]
           url = url+'-hls-6500k.m3u8'
    liz = xbmcgui.ListItem(path = url)
    subfile = self.procConvertSubtitles(suburl)
    liz.setSubtitles([(subfile)])
    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)

# Start of Module

addonName = re.search('plugin\://plugin.video.(.+?)/',str(sys.argv[0])).group(1)
ma = myAddon(addonName)
ma.processAddonEvent()
del myAddon
