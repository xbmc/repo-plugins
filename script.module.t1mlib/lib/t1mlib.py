# -*- coding: utf-8 -*-
# Framework Video Addon Routines for Kodi
# For Kodi Matrix (v19) and above
#  
#
import sys
import os
import xbmc
import xbmcgui
import xbmcaddon
import xbmcplugin
import xbmcvfs
import urllib.parse
import calendar
import datetime
import requests
import string
import locale


qp = urllib.parse.quote_plus
uqp = urllib.parse.unquote_plus
USERAGENT = 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2272.101 Safari/537.36'
httpHeaders = {'User-Agent': USERAGENT,
               'Accept':"application/json, text/javascript, text/html,*/*",
               'Accept-Encoding':'gzip,deflate,sdch',
               'Accept-Language':'en-US,en;q=0.8'
               }


class t1mAddon(object):

    def __init__(self, aname):
        self.script = xbmcaddon.Addon('script.module.t1mlib')
        self.addon = xbmcaddon.Addon(''.join(['plugin.video.', aname]))
        self.addonName = self.addon.getAddonInfo('name')
        self.localLang = self.addon.getLocalizedString
        self.homeDir = self.addon.getAddonInfo('path')
        self.addonIcon = xbmcvfs.translatePath(os.path.join(self.homeDir, 'resources', 'icon.png'))
        self.addonFanart = xbmcvfs.translatePath(os.path.join(self.homeDir,'resources' 'fanart.jpg'))
        self.defaultHeaders = httpHeaders
        self.defaultVidStream = {'codec': 'h264', 'width': 1280, 'height': 720, 'aspect': 1.78}
        self.defaultAudStream = {'codec': 'aac', 'language': 'en'}
        self.defaultSubStream = {'language': 'en'}
        self.log(''.join(["Python version : ",str(sys.version)]))
        self.log(''.join(["locale.getpreferredencoding : ",str(locale.getpreferredencoding())]))


    def log(self, txt):
            message = ''.join([self.addonName, ' : ', txt])
            xbmc.log(msg=message, level=xbmc.LOGDEBUG)


    def addMenuItem(self, name, mode, ilist=None, url=None, thumb=None, fanart=None,
                    videoInfo=None, videoStream=None, audioStream=None,
                    subtitleStream=None, cm=None, isFolder=True):
        videoStream = self.defaultVidStream
        audioStream = self.defaultAudStream
        subtitleStream = self.defaultSubStream
        liz = xbmcgui.ListItem(name, offscreen=True)
        liz.setArt({'thumb': thumb, 'fanart': fanart, 'poster':thumb})
        liz.setInfo('Video', videoInfo)
        liz.addStreamInfo('video', videoStream)
        liz.addStreamInfo('audio', audioStream)
        liz.addStreamInfo('subtitle', subtitleStream)
        if cm is not None:
            liz.addContextMenuItems(cm)
        if not isFolder:
            liz.setProperty('IsPlayable', 'true')
        u = ''.join([sys.argv[0], '?mode=', str(mode), '&url='])
        if url is not None:
            u = ''.join([u, qp(url)])
        ilist.append((u, liz, isFolder))
        return ilist

    # override or extend these functions in the specific addon default.py

    def getAddonMenu(self, url, ilist):
        return ilist

    def getAddonCats(self, url, ilist):
        return ilist

    def getAddonMovies(self, url, ilist):
        return ilist

    def getAddonShows(self, url, ilist):
        return ilist

    def getAddonEpisodes(self, url, ilist):
        return ilist

    def getAddonSearch(self, url, ilist):
        return ilist


    def getAddonListing(self, url, ilist):
        url, sta, sids = url.split('|')
        sid = sids.split('%',1)[0]
        sid = int(sid)
        d = datetime.datetime.utcnow()
        now = calendar.timegm(d.utctimetuple())
# fix some legacy stuff for existing add-ons
        if sta == '20517':
             sta = '9133006313'
             if sid == 94072:
                 sid = 95652
        elif sta == '20534':
             sta = '9133000248'
             if sid == 35794:
                 sid = 93301
             elif sid == 39303:
                 sid = 14506
             elif sid ==17075:
                 sid = 87003
        a = requests.get(''.join(['https://cmg-prod.apigee.net/v1/xapi/tvschedules/tvguide/',sta,'/web?start=',str(now),'&duration=180']), headers=self.defaultHeaders).json()
        for c in a["data"]["items"]:
         if c["channel"]["legacySourceId"] == sid:
           for b in c["programSchedules"]:
            st = datetime.datetime.fromtimestamp(float(b['startTime'])).strftime('%H:%M')
            et = datetime.datetime.fromtimestamp(float(b['endTime'])).strftime('%H:%M')
            duration = int(float(b['endTime']) - float(b['startTime']))
            name = ''.join([st,' - ',et,'  ',str(b.get('title'))])
            d = requests.get(b["programDetails"], headers=self.defaultHeaders).json()['data']['item']
            if d.get('type') == 'show' or d.get('type') == None:
                name = b.get('title')
                epiname = d.get('episodeTitle',name)
                if epiname == None:
                    epiname = ''
                infoList = {'mediatype':'episode',
                            'Title': name,
                            'duration': duration,
                            'Plot':  ''.join([st,' - ',et,'        ',str(duration/60),' min.\n\n[COLOR blue]',str(name),'\n',str(epiname),'[/COLOR]\n\n',str(d.get('description',''))]),
                            'MPAA': b.get('rating')
                           }
            else:
                name = d.get('title')
                infoList = {'mediatype':'movie',
                            'Title': name,
                            'duration': duration,
                            'Plot':  ''.join([st,' - ',et,'        ',str(duration/60),' min.\n\n[COLOR blue]',str(d.get('title')),'[/COLOR]\n\n',str(d.get('description'))]),
                            'MPAA': b.get('rating')
                           }

            thumb = self.addonIcon
            fanart = self.addonFanart
            ilist = self.addMenuItem(name,'LV', ilist, url, thumb, fanart, infoList, isFolder=False)
           break
        return(ilist)


    def getAddonLiveVideo(self, url):
        liz = xbmcgui.ListItem(path = url, offscreen=True)
        liz.setProperty('inputstream','inputstream.adaptive')
        liz.setProperty('inputstream.adaptive.manifest_type','hls')
        liz.setMimeType('application/x-mpegURL')
        xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)


    def getAddonVideo(self, url):
        xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, xbmcgui.ListItem(path=uqp(url), offscreen=True))


    def doFunction(self, url):
        return


    def cleanFilename(self, filename):
        whitelist = "-_.() %s%s" % (string.ascii_letters, string.digits)
        filename = ''.join(c for c in filename if c in whitelist)
        return filename


    def makeLibraryPath(self, ftype, name=None):
        if name is None:
            name  = self.cleanFilename(xbmc.getInfoLabel('ListItem.Title').replace('(Series)','',1).strip())
        profile = self.script.getAddonInfo('profile')
        moviesDir  = xbmcvfs.translatePath(os.path.join(profile,str(ftype)))
        movieDir  = xbmcvfs.translatePath(os.path.join(moviesDir, name))
        if not os.path.isdir(movieDir):
            os.makedirs(movieDir)
        return movieDir

    def doScan(self,movieDir):
        json_cmd = '{"jsonrpc":"2.0","method":"VideoLibrary.Scan", "params": {"directory":"%s/"},"id":1}' % movieDir.replace('\\','/')
        jsonRespond = xbmc.executeJSONRPC(json_cmd)


    def addMusicVideoToLibrary(self, url):
        from xml.etree.ElementTree import Element
        from xml.etree.ElementTree import tostring
        import html.parser
        from xml.dom import minidom
        UNESCAPE = html.parser.HTMLParser().unescape

        url, infoList = urllib.parse.unquote_plus(url).split('||',1)
        infoList = eval(infoList)
        artist = infoList.get('artist')
        title = infoList.get('title')
        movieDir = self.makeLibraryPath('music_videos', name=self.cleanFilename(artist))
        strmFile = xbmcvfs.translatePath(os.path.join(movieDir, ''.join([self.cleanFilename(title),'.strm'])))
        url = ''.join([sys.argv[0],'?mode=GV&url=',url])
        with open(strmFile, 'w') as outfile:
            outfile.write(url)
        nfoFile = xbmcvfs.translatePath(os.path.join(movieDir, ''.join([self.cleanFilename(title),'.nfo'])))
        nfoData = Element('musicvideo')
        for key, val in infoList.items():
            child = Element(key)
            child.text = str(val)
            nfoData.append(child)

        nfoData = UNESCAPE(minidom.parseString(tostring(nfoData)).toprettyxml(indent="   "))
# the next lines of code fail with a Type Error on Android if 'wb' and .encode('utf-8) aren't used. Works ok on Windows and Linux though
        with open(nfoFile, 'wb') as outfile:
            outfile.write(nfoData.encode('utf-8'))
        self.doScan(movieDir)


    def addMovieToLibrary(self, url):
        name  = self.cleanFilename(''.join([xbmc.getInfoLabel('ListItem.Title'),'.strm']))
        movieDir = self.makeLibraryPath('movies')
        strmFile = xbmcvfs.translatePath(os.path.join(movieDir, name))
        url = ''.join([sys.argv[0],'?mode=GV&url=',url])
        with open(strmFile, 'w') as outfile:
            outfile.write(url)
        self.doScan(movieDir)


    def addShowByDate(self,url):
        url = uqp(url)
        movieDir = self.makeLibraryPath('shows')
        ilist = []
        ilist = self.getAddonEpisodes(url, ilist)
        for url, liz, isFolder in ilist:
            pdate = str(liz.getVideoInfoTag().getFirstAired())
            pdate = pdate.split('/')
            pdate = ''.join([pdate[2],'-',pdate[0],'-',pdate[1]])
            title = self.cleanFilename(str(liz.getVideoInfoTag().getTitle()))
            TVShowTitle = self.cleanFilename(str(liz.getVideoInfoTag().getTVShowTitle()))
            se = ''.join([TVShowTitle,' ',pdate,' [',title,'].strm'])
            strmFile = xbmcvfs.translatePath(os.path.join(movieDir, se))
            with open(strmFile, 'w') as outfile:
                outfile.write(url)
        self.doScan(movieDir)


    def addShowToLibrary(self,url):
        movieDir = self.makeLibraryPath('shows')
        ilist = []
        ilist = self.getAddonEpisodes(url, ilist)
        for url, liz, isFolder in ilist:
            season = str(liz.getVideoInfoTag().getSeason())
            episode = str(liz.getVideoInfoTag().getEpisode())
            title = self.cleanFilename(str(liz.getVideoInfoTag().getTitle()))
            se = ''.join(['S',season,'E',episode,'  ',title,'.strm'])
            strmFile = xbmcvfs.translatePath(os.path.join(movieDir, se))
            with open(strmFile, 'w') as outfile:
                outfile.write(url)
        self.doScan(movieDir)


    # internal functions for views, cache and directory management

    def procDir(self, dirFunc, url, content, cache2Disc=True):
        ih = int(sys.argv[1])
        xbmcplugin.setContent(ih, content)
        xbmcplugin.addSortMethod(ih, xbmcplugin.SORT_METHOD_UNSORTED)
        xbmcplugin.addSortMethod(ih, xbmcplugin.SORT_METHOD_TITLE)
        xbmcplugin.addSortMethod(ih, xbmcplugin.SORT_METHOD_EPISODE)
        ilist = dirFunc(url, [])
        xbmcplugin.addDirectoryItems(ih, ilist, len(ilist))
        xbmcplugin.endOfDirectory(ih, cacheToDisc=cache2Disc)

    def getVideo(self, url, ilist):
        self.getAddonVideo(url)


    def processAddonEvent(self):
        mtable = {None : [self.getAddonMenu, 'files'],
                  'GC' : [self.getAddonCats, 'files'],
                  'GM' : [self.getAddonMovies, 'movies'],
                  'GS' : [self.getAddonShows, 'tvshows'],
                  'GE' : [self.getAddonEpisodes, 'episodes'],
                  'SE' : [self.getAddonSearch, 'movies'],
                  'GL' : [self.getAddonListing, 'episodes']}
        ftable = {'GV' : self.getAddonVideo,
                  'LV' : self.getAddonLiveVideo,
                  'AM' : self.addMovieToLibrary,
                  'AS' : self.addShowToLibrary,
                  'AD' : self.addShowByDate,
                  'MU' : self.addMusicVideoToLibrary,
                  'DF' : self.doFunction}
        parms = {}
        if len((sys.argv[2][1:])) > 0:
            parms = dict(arg.split("=") for arg in ((sys.argv[2][1:]).split("&")))
            for key in parms:
                parms[key] = uqp(parms[key])
        fun = mtable.get(parms.get('mode'))
        if fun != None:
            self.procDir(fun[0],parms.get('url'),fun[1])
        else:
            fun = ftable.get(parms.get('mode'))
            if fun != None:
                fun(parms.get('url'))
