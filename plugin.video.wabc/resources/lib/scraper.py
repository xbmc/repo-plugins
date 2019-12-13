# -*- coding: utf-8 -*-
# WABC Kodi Video Addon
#
from t1mlib import t1mAddon
import re
import urllib
import xbmc
import xbmcplugin
import xbmcgui
import HTMLParser
import sys
import os
import json
import time
import zlib

h = HTMLParser.HTMLParser()
qp  = urllib.quote_plus
uqp = urllib.unquote_plus
UTF8     = 'utf-8'


class myAddon(t1mAddon):

  def getAddonMenu(self,url,ilist):
      urls = {}
      html = ''
      try:
        url = xbmc.translatePath('special://home/addons/plugin.video.wabc/resources/lib/shows.zip')
        html = urllib.urlopen(url).read()
        d = zlib.decompressobj(16+zlib.MAX_WBITS)
        html = d.decompress(html)
      except:
        html = self.getRequest('https://abc.com/shows?category=A-Z')
      html = re.compile("<script type=['\"]text/javascript['\"].?>window\['__abc_com__'\]=(.+?);</script>", re.DOTALL).search(html).group(1)
      jo = json.loads(html);
      modules = jo['page']['content']['shell']['module']
      for m in modules:
        if 'tiles' in m.keys():
            tiles = m['tiles']
            if isinstance(tiles,list):
                for show in tiles:
                    images = show.get('images')
                    thumb = None
                    if isinstance(images,list):
                        thumb = images[len(images)-1].get('value')
                    url = show.get('link').get('urlValue')
                    if url is None or not '/' in url:
                        continue
                    if urls.get(url,None) is None and show.get('show') is not None:
                        if url.endswith('/index'):
                            url = url.replace('/index','',1)
                        urls[url] = url
                        name = show.get('title')
                        fanart = thumb
                        infoList ={}
                        if 'about' in show.get('show').keys():
                            infoList['Plot'] = h.unescape(show['show']['about'])
                        infoList['Title'] = name
                        infoList['TVShowTitle'] = name
                        infoList['mediatype'] = 'tvshow'
                        contextMenu = [('Add To Library','XBMC.RunPlugin(%s?mode=DF&url=AL%s)' % (sys.argv[0], url))]
                        ilist = self.addMenuItem(name,'GE', ilist, url, thumb, fanart, infoList, isFolder=True, cm=contextMenu)
      return(ilist)


  def getAddonEpisodes(self,url,ilist, getFileData = False):
      if not url.startswith('http'):
          u = 'https://abc.com'+url
      if not url.endswith('/episode-guide'):
          u = u+'/episode-guide'
      html = self.getRequest(u)
      if len(html) is 0 or re.search('module-404-wrapper', html, re.DOTALL):    #no root episode-guide
          u = 'https://abc.com'+url
          html = self.getRequest(u)
          a = re.compile('<div class="tilegroup__group-action"><a href="(.+?)">See All</a>',re.DOTALL).findall(html)
          if a is not None and len(a) > 0:                                      #only gets latest, should get all?
              u = 'https://abc.com'+a[0]
              html = self.getRequest(u)
      html = re.compile("<script type='text/javascript' >window\['__abc_com__'\]=(.+?);</script>", re.DOTALL).search(html).group(1)
      jo = json.loads(html)
      tiles = None
      video = None
      modules = jo['page']['content']['shell']['module']
      for m in modules:
            if 'tiles' in m.keys():
                tiles = m['tiles']
                break
            if 'video' in m.keys():
                video = m['video']
                break;
      if tiles is None and isinstance(video,dict):      #page just has a single video player
        self.addVideo(ilist,getFileData,video,None)
      elif isinstance(tiles,list):                      #page has tiles of episodes
            for t in tiles:
                video = t.get('video')
                images = t.get('images')
                self.addVideo(ilist,getFileData,video,images)
      if len(ilist) == 0:
          xbmc.executebuiltin('XBMC.Notification("%s", "%s", %s, "%s")' % (self.addonName, self.addon.getLocalizedString(30001), 5000, self.addonIcon))
      return(ilist)

  def addVideo(self,ilist,getFileData,video,images):
    if video is not None:  
        season = video.get('seasonnumber')
        episode = video.get('episodenumber')
        plot = h.unescape(video.get('longdescription'))
        airdate = video.get('displayAirtime')
        aired = time.strptime(airdate, '%a, %d %b %Y %H:%M:%S')
        url = video.get('id')[4:]
        name = h.unescape(video.get('title'))
        thumb = None
        if isinstance(images,list):
            thumb = images[len(images)-1].get('value')
        fanart = thumb
        infoList = {}
        if season.isdigit():
            infoList['Season'] = int(season)
        if episode.isdigit():
            infoList['Episode'] = int(episode)
        infoList['Duration'] = int(video.get('duration')) / 60000
        infoList['Date'] = time.strftime('%Y-%m-%d',aired)
        infoList['Aired'] = infoList['Date']
        infoList['Year'] = int(infoList['Aired'].split('-',1)[0])
        infoList['MPAA'] = video.get('tvrating')
        infoList['Title'] = '[COLOR=FFFF8040]' + name + '[/COLOR]' if int(video.get('accesslevel')) else name
        infoList['Plot'] = plot
        infoList['TVShowTitle'] = xbmc.getInfoLabel('ListItem.TVShowTitle')
        infoList['Studio'] = 'ABC'
        infoList['mediatype'] = 'episode'
        if getFileData == False:
              ilist = self.addMenuItem(name,'GV', ilist, url, thumb, fanart, infoList, isFolder=False)
        else:
            if infoList.get('Season') is not None and infoList.get('Episode') is not None:
                ilist.append((infoList['Season'], infoList['Episode'], url))

  def doFunction(self, url):
    func = url[0:2]
    url  = url[2:]
    if func == 'AL':
      name  = xbmc.getInfoLabel('ListItem.Title')
      profile = self.addon.getAddonInfo('profile').decode(UTF8)
      moviesDir  = xbmc.translatePath(os.path.join(profile,'TV Shows'))
      movieDir  = xbmc.translatePath(os.path.join(moviesDir, name))
      if not os.path.isdir(movieDir):
           os.makedirs(movieDir)
      ilist = []
      ilist = self.getAddonEpisodes(url, ilist, getFileData = True)
      for season, episode, url in ilist:
            se = 'S%sE%s' % (str(season), str(episode))
            xurl = '%s?mode=GV&url=%s' % (sys.argv[0], url)
            strmFile = xbmc.translatePath(os.path.join(movieDir, se+'.strm'))
            with open(strmFile, 'w') as outfile:
               outfile.write(xurl)         
    json_cmd = '{"jsonrpc":"2.0","method":"VideoLibrary.Scan", "params": {"directory":"%s/"},"id":1}' % movieDir.replace('\\','/')
    jsonRespond = xbmc.executeJSONRPC(json_cmd)

  def getAddonVideo(self,url):
      vd = uqp(url)
      url = 'https://api.pluto.watchabc.go.com/api/ws/pluto/v1/module/videoplayer/2185737?brand=001&device=001&authlevel=0&layout=2185698&video=VDKA'+str(vd)
      html = self.getRequest(url)
      ua = re.compile('"ULNK","value":"(.+?)"', re.DOTALL).search(html).group(1)
      url = 'https://api.entitlement.watchabc.go.com/vp2/ws-secure/entitlement/2020/authorize.json'
      udata = 'video%5Fid=VDKA'+str(vd)+'&device=001&video%5Ftype=lf&brand=001'
      uheaders = self.defaultHeaders.copy()
      uheaders['Content-Type'] = 'application/x-www-form-urlencoded'
      uheaders['Accept'] = 'application/json'
      uheaders['X-Requested-With'] = 'ShockwaveFlash/22.0.0.209'
      uheaders['Origin'] = 'http://cdn1.edgedatg.com'
      html = self.getRequest(url, udata, uheaders)
      a = json.loads(html)
      if a.get('uplynkData', None) is None:
          xbmc.executebuiltin('XBMC.Notification("%s", "%s", %s, "%s")' % (self.addonName, self.addon.getLocalizedString(30001), 5000, self.addonIcon))
          return

      sessionKey = a['uplynkData']['sessionKey']
      url = ua+'?'+sessionKey
      html = self.getRequest(url)
      url = re.compile('#UPLYNK-MEDIA0.+?http(.+?)\n',re.DOTALL).search(html).group(1)
      url = 'http'+url
      liz = xbmcgui.ListItem(path = url.strip())
# No need to process subtitles, all shows have closed captions
      infoList={}
      infoList['mediatype'] = xbmc.getInfoLabel('ListItem.DBTYPE')
      infoList['Title'] = xbmc.getInfoLabel('ListItem.Title')
      infoList['TVShowTitle'] = xbmc.getInfoLabel('ListItem.TVShowTitle')
      infoList['Year'] = xbmc.getInfoLabel('ListItem.Year')
      infoList['Premiered'] = xbmc.getInfoLabel('Premiered')
      infoList['Plot'] = xbmc.getInfoLabel('ListItem.Plot')
      infoList['Studio'] = xbmc.getInfoLabel('ListItem.Studio')
      infoList['Genre'] = xbmc.getInfoLabel('ListItem.Genre')
      infoList['Duration'] = xbmc.getInfoLabel('ListItem.Duration')
      infoList['MPAA'] = xbmc.getInfoLabel('ListItem.Mpaa')
      infoList['Aired'] = xbmc.getInfoLabel('ListItem.Aired')
      infoList['Season'] = xbmc.getInfoLabel('ListItem.Season')
      infoList['Episode'] = xbmc.getInfoLabel('ListItem.Episode')
      liz.setInfo('video', infoList)
      xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)


