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
import sys

h = HTMLParser.HTMLParser()
UTF8 = 'utf-8'
showsPerPage = 24 # number of shows returned per page by PBS

class myAddon(t1mAddon):

 def doPBSLogin(self):
    if self.addon.getSetting('enable_login') != 'true':
        return

    profile = self.addon.getAddonInfo('profile').decode(UTF8)
    pdir  = xbmc.translatePath(profile).decode(UTF8)
    if not os.path.isdir(pdir):
        os.makedirs(pdir)
    cjFile = xbmc.translatePath(os.path.join(profile, 'PBSCookies.dat')).decode(UTF8)
    cj = cookielib.LWPCookieJar()
    badCookie = True
    try:
        cj.load(cjFile)
    except:
        cj=[]
    for cookie in cj:
        if cookie.name == 'sessionid':
            badCookie = cookie.is_expired()
    if self.addon.getSetting('first_run_done') != 'true':
        badCookie = True
    if badCookie:
       cj = cookielib.LWPCookieJar(cjFile)
       opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
       urllib2.install_opener(opener)
       html = self.getRequest('http://www.pbs.org/shows/')
       clientId = re.compile('id="signInServiceList".+?client_id=(.+?)"', re.DOTALL).search(html).group(1)
       html = self.getRequest('https://account.pbs.org/oauth2/login/')
       lcsr, lnext = re.compile("name='csrfmiddlewaretoken'.+?value='(.+?)'.+?"+'name="next".+?value="(.+?)"', re.DOTALL).search(html).groups()
       username = self.addon.getSetting('login_name')
       password = self.addon.getSetting('login_pass')
       if username !='' and password !='':
           url1  = ('https://account.pbs.org/oauth2/login/')
           xheaders = self.defaultHeaders.copy()
           xheaders["Referer"] = "https://account.pbs.org/oauth2/login/"
           xheaders["Host"] = "account.pbs.org"
           xheaders["Origin"] = "https://account.pbs.org"
           xheaders["Connection"] = "keep-alive"
           xheaders["Accept"] = "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
           xheaders["Content-Type"] = "application/x-www-form-urlencoded"
           udata = urllib.urlencode({'csrfmiddlewaretoken' : lcsr, 'next' : lnext, 'email' : username, 'password' : password})
           html = self.getRequest(url1, udata, xheaders)
           html = self.getRequest('https://account.pbs.org/oauth2/authorize/?scope=account&redirect_uri=http://www.pbs.org/login/&response_type=code&client_id=%s&confirmed=1' % clientId)
           for cookie in cj:
               if cookie.name == 'pbsol.station':
                   self.addon.setSetting('pbsol', cookie.value)
               elif cookie.name == 'pbs_uid':
                   self.addon.setSetting('pbs_uid', cookie.value)
           self.addon.setSetting('first_run_done', 'true')
           cj.save()
    else:
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
        urllib2.install_opener(opener)
        return


 def getAddonMenu(self,url,ilist):
    addonLanguage  = self.addon.getLocalizedString
    self.doPBSLogin()
    xheaders = self.defaultHeaders.copy()
    xheaders["Referer"] = "http://www.pbs.org/shows/?genre=All&title=&station=false&alphabetically=true&layout=grid"
    xheaders["X-Requested-With"] = "XMLHttpRequest"
    html = self.getRequest('http://www.pbs.org/shows-page/0/?genre=&title=&callsign=&alphabetically=true', None, xheaders)
    a = json.loads(html)
    for b in a['genres'][1:]:
        ilist = self.addMenuItem(b['title'],'GS', ilist, str(b['id'])+'|0', self.addonIcon, self.addonFanart, None, isFolder=True)
    if self.addon.getSetting('enable_login') == 'true':
        pbsol = self.addon.getSetting('pbsol')
        if pbsol != '':
           xheaders = self.defaultHeaders.copy()
           xheaders['X-Requested-With'] = 'XMLHttpRequest'
           html = self.getRequest('http://www.pbs.org/shows-page/0/?genre=&title=&callsign=%s&alphabetically=true' % pbsol, None, xheaders)
           if len(html) > 0:
               a = json.loads(html)
               if len(a['results']['content']) > 0:
                   ilist = self.addMenuItem(addonLanguage(30048) ,'GS', ilist, 'localpbs' , self.addonIcon, self.addonFanart, None, isFolder=True)
    html = self.getRequest('http://www.pbs.org/favorite-shows-page/1/')
    if len(html) > 0:
        a = json.loads(html)
        if a['totalResults'] > 0:
            ilist = self.addMenuItem(addonLanguage(30004),'GS', ilist, 'favorites' , self.addonIcon, self.addonFanart, None, isFolder=True)
    xheaders = self.defaultHeaders.copy()
    xheaders['X-Requested-With'] = 'XMLHttpRequest'
    html = self.getRequest('http://www.pbs.org/watchlist/page/1/', None, xheaders)
    if len(html) > 0:
        a = json.loads(html)
        if a.get('videos') is not None:
            if len(a['videos']) > 0:
                ilist = self.addMenuItem(addonLanguage(30005) ,'GM', ilist, 'pbswatchlist' , self.addonIcon, self.addonFanart, None, isFolder=True)
    ilist = self.addMenuItem(addonLanguage(30051) ,'GS', ilist, 'pbssearch' , self.addonIcon, self.addonFanart, None, isFolder=True)
    return ilist


 def getAddonShows(self,url,ilist):
    pgNum = ''
    addonLanguage  = self.addon.getLocalizedString
    self.doPBSLogin()
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
    elif gsurl == 'pbssearch':
        keyb = xbmc.Keyboard(self.addon.getSetting('last_search'), addonLanguage(30051))
        keyb.doModal()
        if (keyb.isConfirmed()):
           answer = keyb.getText()
           if len(answer) == 0: 
              return (ilist)
        self.addon.setSetting('last_search', answer)
        answer = answer.replace(' ','+')
        xheaders = self.defaultHeaders.copy()
        xheaders['X-Requested-With'] = 'XMLHttpRequest'
        html = self.getRequest('http://www.pbs.org/search-videos/?callsign=WNET&page=1&q=%s&rank=relevance' % (answer), None, xheaders)
        a = json.loads(html)
        cats = a['results']['articles']
    else:
        genreUrl, pgNum = url.split('|',1) 
        xheaders = self.defaultHeaders.copy()
        xheaders['X-Requested-With'] = 'XMLHttpRequest'
        html = self.getRequest('http://www.pbs.org/shows-page/%s/?genre=%s&title=&callsign=&alphabetically=true' % (pgNum, genreUrl), None, xheaders)
        a = json.loads(html)
        cats = a['results']['content']
    for i, (b) in list(enumerate(cats, start=1)):
        if gsurl == 'pbssearch':
            url = b['url']
        else:
            url = b.get('cid')
            if url is None:
                url = b['id']
        name   = b['title']
        thumb  = b['image']
        if thumb == None :
            thumb = self.addonIcon
        fanart = b['image']
        if fanart == None:
            fanart = self.addonFanart
        infoList = {}
        infoList['TVShowTitle'] = name
        infoList['Title']       = name
        infoList['Studio'] = b.get('producer')
        genres = b.get('genre_titles')
        if genres != [] and genres is not None:
            infoList['Genre'] = genres[0]
        infoList['Episode'] = b.get('video_count')
        infoList['Plot'] = b.get('description')
        if self.addon.getSetting('enable_login') == 'true':
            if gsurl == 'favorites':
                contextMenu = [(addonLanguage(30006),'XBMC.Container.Update(%s?mode=DF&url=RF%s)' % (sys.argv[0], url))]
            else:
                contextMenu = [(addonLanguage(30007),'XBMC.RunPlugin(%s?mode=DF&url=AF%s)' % (sys.argv[0], url))]
        else:
            contextMenu = None
        if gsurl == 'pbssearch':
            infoList['mediatype'] = 'episode'
            ilist = self.addMenuItem(name,'GV', ilist, url, thumb, fanart, infoList, isFolder=False)
        else:
            infoList['mediatype'] = 'tvshow'
            ilist = self.addMenuItem(name,'GC', ilist, url, thumb, fanart, infoList, isFolder=True, cm=contextMenu)
    if pgNum != '':
        ilist = self.addMenuItem('[COLOR blue]%s[/COLOR]' % addonLanguage(30050),'GS', ilist, genreUrl+'|'+str(int(pgNum)+1), self.addonIcon, self.addonFanart, None, isFolder=True)
    return(ilist)


 def getAddonCats(self,url,ilist):
    addonLanguage  = self.addon.getLocalizedString
    self.doPBSLogin()
    thumb = xbmc.getInfoLabel('ListItem.Art(thumb)')
    fanart = xbmc.getInfoLabel('ListItem.Art(fanart)')
    infoList = {}
    infoList['TVShowTitle'] = xbmc.getInfoLabel('ListItem.TVShowTitle')
    infoList['Title'] = infoList['TVShowTitle']
    infoList['mediatype'] = 'tvshow'
    ilist = self.addMenuItem('%s' % (addonLanguage(30045)),'GE', ilist, '%s|%s|1' %(url, 'episodes'), thumb, fanart, infoList, isFolder=True)
    ilist = self.addMenuItem('%s' % (addonLanguage(30046)),'GE', ilist, '%s|%s|1' %(url, 'clips'), thumb, fanart, infoList, isFolder=True)
    ilist = self.addMenuItem('%s' % (addonLanguage(30047)),'GE', ilist, '%s|%s|1' %(url, 'previews'), thumb, fanart, infoList, isFolder=True)
    return(ilist)


 def getAddonEpisodes(self,url,ilist):
    self.doPBSLogin()
    addonLanguage = self.addon.getLocalizedString
    url, stype, pageNum = url.split('|',2)
    sname = url
    html = self.getRequest('http://www.pbs.org/show/%s/%s/?page=%s' % (url, stype, pageNum))
    epis = re.compile('<article class="video-summary">.+?data-srcset="(.+?)".+?alt="(.+?)".+?class="description">(.+?)<.+?data-video-id="(.+?)"',re.DOTALL).findall(html)
    if len(epis) == 0:
        epis = re.compile('<div class="video-summary">.+?data-srcset="(.+?)".+?alt="(.+?)".+?class="description">(.+?)<.+?data-video-id="(.+?)"',re.DOTALL).findall(html)
    for i, (imgs, name, plot, url)  in list(enumerate(epis, start=1)):
        name = h.unescape(name.decode(UTF8))
        name = name.replace('Video thumbnail: ','',1)
        plot=plot.strip()
        infoList = {}
        imgs = imgs.split(',')
        thumb = '%s.jpg' % (imgs[2].split('.jpg',1)[0].strip())
        fanart = '%s.jpg' % (imgs[len(imgs)-1].split('.jpg',1)[0].strip())
        infoList['Title'] = name
        infoList['Plot'] = h.unescape(plot.decode(UTF8))
        infoList['mediatype'] = 'episode'
        infoList['TVShowTitle'] = xbmc.getInfoLabel('ListItem.TVShowTitle')
        if self.addon.getSetting('enable_login') == 'true': 
            contextMenu = [(addonLanguage(30008),'XBMC.RunPlugin(%s?mode=DF&url=AW%s)' % (sys.argv[0], url))]
        else:
            contextMenu = None
        ilist = self.addMenuItem(name,'GV', ilist, url, thumb, fanart, infoList, isFolder=False, cm=contextMenu)
        if i >= showsPerPage:
            ilist = self.addMenuItem('[COLOR blue]%s[/COLOR]' % addonLanguage(30050),'GE', ilist, '%s|%s|%s' %(sname, stype, str(int(pageNum)+1)), self.addonIcon, self.addonFanart, None, isFolder=True)
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
        infoList = {}
        name = b['title']
        plot = b['description']
        duration = b['duration']
        t = 0
        for dur in duration.split(':'):
            if dur.strip().isdigit(): 
                t = t*60 + int(dur.strip())
        if t != 0:
            infoList['duration'] = t
        thumb = b['image']
        fanart = b['image']
        infoList['TVShowTitle'] = b['show']['title']
        infoList['Title'] = name
        infoList['Plot'] = plot
        infoList['mediatype'] = 'episode'
        url = str(b['id'])
        contextMenu = [(addonLanguage(30009),'XBMC.Container.Update(%s?mode=DF&url=RW%s)' % (sys.argv[0], url))]
        ilist = self.addMenuItem(name,'GV', ilist, url, thumb, fanart, infoList, isFolder=False, cm=contextMenu)
    return(ilist)

 def doFunction(self, url):
    self.doPBSLogin()
    func = url[0:2]
    url  = url[2:]
    if func == 'AW':
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
    if url.startswith('/'):
        xheaders = self.defaultHeaders.copy()
        xheaders['X-Requested-With'] = 'XMLHttpRequest'
        html = self.getRequest('http://www.pbs.org%s' % (url), None, xheaders)
        url = re.compile('data-video-id="(.+?)"', re.DOTALL).search(html).group(1)
    addonLanguage = self.addon.getLocalizedString
    pbs_uid = self.addon.getSetting('pbs_uid')
    pg = self.getRequest('http://player.pbs.org/viralplayer/%s/?uid=%s' % (url, pbs_uid))
    urls = re.compile("PBS.videoData =.+?recommended_encoding.+?'url'.+?'(.+?)'.+?'closed_captions_url'.+?'(.+?)'", re.DOTALL).search(pg)
    if urls is not None:
        url,suburl = urls.groups()
        pg = self.getRequest('%s?format=json' % url)
        url = json.loads(pg)['url']
    else:
        xbmc.executebuiltin('XBMC.Notification("%s", "%s", %s)' % ( self.addonName, addonLanguage(30049) , 4000) )
        return

    if 'mp4:' in url:
        url = 'http://ga.video.cdn.pbs.org/%s' % url.split('mp4:',1)[1]
    elif ('.m3u8' in url) and self.addon.getSetting('vid_res') >= '1': 
        url = url.replace('800k','2500k')
        if ('hd-1080p' in url) and self.addon.getSetting('vid_res') == '2': 
            url = url.split('-hls-',1)[0]
            url = url+'-hls-6500k.m3u8'
    liz = xbmcgui.ListItem(path = url)
    subfile = self.procConvertSubtitles(suburl)
    liz.setSubtitles([(subfile)])
    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)
