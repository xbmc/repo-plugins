# -*- coding: utf-8 -*-
# Framework Video Addon Routines for Kodi
# Needs at least Kodi 14.2, preferably 15.0 and above
#  
#
import sys
import os
import re
import xbmc
import xbmcgui
import xbmcaddon
import xbmcplugin
import urllib
import urllib2
import zlib
import json
import HTMLParser

h = HTMLParser.HTMLParser()
qp  = urllib.quote_plus
uqp = urllib.unquote_plus
USERAGENT   = 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2272.101 Safari/537.36'

httpHeaders = {'User-Agent': USERAGENT,
                        'Accept':"application/json, text/javascript, text/html,*/*",
                        'Accept-Encoding':'gzip,deflate,sdch',
                        'Accept-Language':'en-US,en;q=0.8'
                       }


UTF8 = 'utf-8'

class t1mAddon(object):

  def __init__(self, aName):
    self.addon       = xbmcaddon.Addon('plugin.video.%s' % aName)
    self.addonName   = self.addon.getAddonInfo('name')
    self.localLang   = self.addon.getLocalizedString
    self.homeDir     = self.addon.getAddonInfo('path').decode(UTF8)
    self.addonIcon   = xbmc.translatePath(os.path.join(self.homeDir, 'icon.png'))
    self.addonFanart = xbmc.translatePath(os.path.join(self.homeDir, 'fanart.jpg'))

    self.defaultHeaders = httpHeaders
    self.defaultVidStream = { 'codec': 'h264', 
                              'width' : 1280, 
                              'height' : 720, 
                              'aspect' : 1.78 }

    self.defaultAudStream = { 'codec': 'aac', 'language' : 'en'}
    self.defaultSubStream = { 'language' : 'en'}


  def log(self, txt):
    try:
      message = '%s: %s' % (self.addonName, txt.encode('ascii', 'ignore'))
      xbmc.log(msg=message, level=xbmc.LOGDEBUG)
    except:
      pass


  def getRequest(self, url, udata=None, headers = httpHeaders):
    self.log("getRequest URL:"+str(url))
    req = urllib2.Request(url.encode(UTF8), udata, headers)
    try:
      response = urllib2.urlopen(req)
      page = response.read()
      if response.info().getheader('Content-Encoding') == 'gzip':
         self.log("Content Encoding == gzip")
         page = zlib.decompress(page, zlib.MAX_WBITS + 16)
    except:
      page = ""
    return(page)

  def getAddonMeta(self):
    if self.addon.getSetting('enable_meta') != 'true': return({})
    profile = self.addon.getAddonInfo('profile').decode(UTF8)
    pdir  = xbmc.translatePath(os.path.join(profile))
    if not os.path.isdir(pdir):
      os.makedirs(pdir)
    self.metafile = xbmc.translatePath(os.path.join(profile, 'meta.json'))
    meta = {}
    if self.addon.getSetting('init_meta') != 'true':
      try:
         with open(self.metafile) as infile:
             meta = json.load(infile)
      except: pass
    return(meta)

  def updateAddonMeta(self, meta):
    if self.addon.getSetting('enable_meta') != 'true': return
    with open(self.metafile, 'w') as outfile:
        json.dump(meta, outfile)
    outfile.close
    self.addon.setSetting(id='init_meta', value='false')
      
  def addMenuItem(self, name, mode, ilist=[], url=None, thumb=None, fanart=None, 
                  videoInfo={}, videoStream=None, audioStream=None,
                  subtitleStream=None, isFolder=True ):
      videoStream = self.defaultVidStream
      audioStream = self.defaultAudStream
      subtitleStream = self.defaultSubStream
      liz=xbmcgui.ListItem(name, '',None, thumb)
      liz.setInfo( 'Video', videoInfo)
      liz.addStreamInfo('video', videoStream)
      liz.addStreamInfo('audio', audioStream)
      liz.addStreamInfo('subtitle', subtitleStream)
      liz.setProperty('fanart_image', fanart)
      if not isFolder: liz.setProperty('IsPlayable', 'true')
      u = '%s?mode=%s&name=%s' % (sys.argv[0], mode, qp(name.encode(UTF8)))
      if url != None: u = u+'&url=%s' % qp(url)
      ilist.append((u, liz, isFolder))
      return(ilist)

#override or extend these functions in the specific addon default.py

  def getAddonMenu(self,url,ilist):
      return(ilist)

  def getAddonCats(self,url,ilist):
      return(ilist)

  def getAddonMovies(self,url,ilist):
      return(ilist)

  def getAddonShows(self,url,ilist):
      ilist = []
      return(ilist)

  def getAddonEpisodes(self,url,ilist):
      ilist = []
      return(ilist)

  def getAddonVideo(self, url):
      u = uqp(url)
      xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, xbmcgui.ListItem(path = u))



#internal functions for views, cache and directory management

  def procDir(self, dirFunc, url, contentType='files', viewType='default_view', cache2Disc=True):
      ilist = []
      xbmcplugin.setContent(int(sys.argv[1]), contentType)
      xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_UNSORTED)
      xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_TITLE)
      xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_EPISODE)

      ilist = dirFunc(url, ilist)
      if len(ilist) > 0:
         xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))
         if self.addon.getSetting('enable_views') == 'true':
           xbmc.executebuiltin("Container.SetViewMode(%s)" % self.addon.getSetting(viewType))
         xbmcplugin.endOfDirectory(int(sys.argv[1]), cacheToDisc=cache2Disc)

  def getVideo(self,url):
      self.getAddonVideo(url)

  def procConvertSubtitles(self, suburl):
    subfile = ""
    if (suburl != ""):
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
    return subfile   


  def getAddonParms(self):
    parms = {}
    try:
       parms = dict( arg.split( "=" ) for arg in ((sys.argv[2][1:]).split( "&" )) )
       for key in parms:
         try:    parms[key] = urllib.unquote_plus(parms[key]).decode(UTF8)
         except: pass
    except:
       parms = {}
    return(parms.get)


  def processAddonEvent(self):
    p = self.getAddonParms()
    mode = p('mode',None)

    if mode==  None:  self.procDir(self.getAddonMenu,    p('url'), 'files', 'default_view')
    elif mode=='GC':  self.procDir(self.getAddonCats,    p('url'), 'files', 'default_view')
    elif mode=='GM':  self.procDir(self.getAddonMovies,  p('url'), 'movies', 'movie_view')
    elif mode=='GS':  self.procDir(self.getAddonShows,   p('url'), 'tvshows', 'show_view')
    elif mode=='GE':  self.procDir(self.getAddonEpisodes,p('url'), 'episodes', 'episode_view')
    elif mode=='GV':  self.getVideo(p('url'))
    return(p)
