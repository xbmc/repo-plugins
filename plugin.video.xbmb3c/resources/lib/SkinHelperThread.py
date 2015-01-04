#################################################################################################
# Skin HelperUpdater
#################################################################################################

import xbmc
import xbmcgui
import xbmcaddon

import json
import threading
import urllib
from DownloadUtils import DownloadUtils
from Database import Database
import MainModule

from datetime import datetime, timedelta, time
import urllib2
import random
import time
import os

__settings__ = xbmcaddon.Addon(id='plugin.video.xbmb3c')

#define our global download utils
downloadUtils = DownloadUtils()

class SkinHelperThread(threading.Thread):

    logLevel = 0
    user_art_links = []
    current_user_art = 0

    
    def __init__(self, *args):
        level = __settings__.getSetting('logLevel')
        self.logLevel = 0
        if(level != None):
            self.logLevel = int(level)
        if(self.logLevel == 2):
            self.LogCalls = True
        xbmc.log("XBMB3C SkinHelperThread -> Log Level:" +  str(self.logLevel))
        
        threading.Thread.__init__(self, *args)    
    
    def logMsg(self, msg, level = 1):
        if(self.logLevel >= level):
            xbmc.log("XBMB3C SkinHelperThread -> " + msg)
                
    def run(self):
        self.logMsg("Started")
        
        self.SetMB3WindowProperties()
        self.getImagesFromCache()

        lastRun = datetime.today()
        lastProfilePath = xbmc.translatePath('special://profile')
        
        while (xbmc.abortRequested == False):
            td = datetime.today() - lastRun
            secTotal = td.seconds
            profilePath = xbmc.translatePath('special://profile')
            
            updateInterval = 600
            if((secTotal > updateInterval or lastProfilePath != profilePath) and not xbmc.Player().isPlaying()):
                
                self.SetMB3WindowProperties()
                self.setImagesInCache()
                lastProfilePath = profilePath    
                lastRun = datetime.today()
            
            xbmc.sleep(500)
                        
        self.logMsg("Exited")
        
    # primitive cache by getting last known images from skin-settings           
    def getImagesFromCache(self):
        WINDOW = xbmcgui.Window( 10000 )
        self.logMsg("[MB3 skin helper] get properties from cache...")
        
        # user collections
        totalUserLinks = 0
        if WINDOW.getProperty("MediaBrowser.usr.Count") != '':
            totalUserLinks = int(WINDOW.getProperty("MediaBrowser.usr.Count"))
        linkCount = 0
        while linkCount !=totalUserLinks:
            mbstring = "MediaBrowser.usr." + str(linkCount)
            if xbmc.getInfoLabel("Skin.String(" + mbstring + '.background)') != "":
                WINDOW.setProperty(mbstring + '.background', xbmc.getInfoLabel("Skin.String(" + mbstring + '.background)'))
                WINDOW.setProperty(mbstring + '.background.small', xbmc.getInfoLabel("Skin.String(" + mbstring + '.background.small)'))
            linkCount += 1
        
        #global backgrounds
        mbstring = "MB3.Background.FavouriteMovies.FanArt"
        WINDOW.setProperty(mbstring, xbmc.getInfoLabel("Skin.String(" + mbstring + ')'))
        WINDOW.setProperty(mbstring + '.small', xbmc.getInfoLabel("Skin.String(" + mbstring + '.small)'))
        mbstring = "MB3.Background.FavouriteShows.FanArt"
        WINDOW.setProperty(mbstring, xbmc.getInfoLabel("Skin.String(" + mbstring + ')'))
        WINDOW.setProperty(mbstring + '.small', xbmc.getInfoLabel("Skin.String(" + mbstring + '.small)'))
        mbstring = "MB3.Background.Channels.FanArt"
        WINDOW.setProperty(mbstring, xbmc.getInfoLabel("Skin.String(" + mbstring + ')'))
        WINDOW.setProperty(mbstring + '.small', xbmc.getInfoLabel("Skin.String(" + mbstring + '.small)'))
        mbstring = "MB3.Background.MusicVideos.FanArt"
        WINDOW.setProperty(mbstring, xbmc.getInfoLabel("Skin.String(" + mbstring + ')'))
        WINDOW.setProperty(mbstring + '.small', xbmc.getInfoLabel("Skin.String(" + mbstring + '.small)'))
        mbstring = "MB3.Background.Photos.FanArt"
        WINDOW.setProperty(mbstring, xbmc.getInfoLabel("Skin.String(" + mbstring + ')'))
        WINDOW.setProperty(mbstring + '.small', xbmc.getInfoLabel("Skin.String(" + mbstring + '.small)'))
        mbstring = "MB3.Background.Movie.FanArt"
        WINDOW.setProperty(mbstring, xbmc.getInfoLabel("Skin.String(" + mbstring + ')'))
        WINDOW.setProperty(mbstring + '.small', xbmc.getInfoLabel("Skin.String(" + mbstring + '.small)'))
        mbstring = "MB3.Background.TV.FanArt"
        WINDOW.setProperty(mbstring, xbmc.getInfoLabel("Skin.String(" + mbstring + ')'))
        WINDOW.setProperty(mbstring + '.small', xbmc.getInfoLabel("Skin.String(" + mbstring + '.small)'))
        mbstring = "MB3.Background.Music.FanArt"
        WINDOW.setProperty(mbstring, xbmc.getInfoLabel("Skin.String(" + mbstring + ')'))
        WINDOW.setProperty(mbstring + '.small', xbmc.getInfoLabel("Skin.String(" + mbstring + '.small)'))

    # primitive cache by storing last known images in skin-settings
    def setImagesInCache(self):         
        WINDOW = xbmcgui.Window( 10000 )
        
        #user collections
        totalUserLinks = 10
        if WINDOW.getProperty("MediaBrowser.usr.Count") != '':
            totalUserLinks = int(WINDOW.getProperty("MediaBrowser.usr.Count"))
        else:
            totalUserLinks = 0
        linkCount = 0
        while linkCount !=totalUserLinks:
            mbstring = "MediaBrowser.usr." + str(linkCount)
            xbmc.executebuiltin('Skin.SetString(' + mbstring + '.background,' + WINDOW.getProperty(mbstring + '.background') + ")")
            xbmc.executebuiltin('Skin.SetString(' + mbstring + '.background.small,' + WINDOW.getProperty(mbstring + '.background.small') + ")")
            linkCount += 1
            
        #global backgrounds
        mbstring = "MB3.Background.FavouriteMovies.FanArt"
        xbmc.executebuiltin('Skin.SetString(' + mbstring + ',' + WINDOW.getProperty(mbstring) + ")")
        xbmc.executebuiltin('Skin.SetString(' + mbstring + '.small,' + WINDOW.getProperty(mbstring + '.small') + ")")
        mbstring = "MB3.Background.FavouriteShows.FanArt"
        xbmc.executebuiltin('Skin.SetString(' + mbstring + ',' + WINDOW.getProperty(mbstring) + ")")
        xbmc.executebuiltin('Skin.SetString(' + mbstring + '.small,' + WINDOW.getProperty(mbstring + '.small') + ")")
        mbstring = "MB3.Background.Channels.FanArt"
        xbmc.executebuiltin('Skin.SetString(' + mbstring + ',' + WINDOW.getProperty(mbstring) + ")")
        xbmc.executebuiltin('Skin.SetString(' + mbstring + '.small,' + WINDOW.getProperty(mbstring + '.small') + ")")
        mbstring = "MB3.Background.MusicVideos.FanArt"
        xbmc.executebuiltin('Skin.SetString(' + mbstring + ',' + WINDOW.getProperty(mbstring) + ")")
        xbmc.executebuiltin('Skin.SetString(' + mbstring + '.small,' + WINDOW.getProperty(mbstring + '.small') + ")")
        mbstring = "MB3.Background.Photos.FanArt"
        xbmc.executebuiltin('Skin.SetString(' + mbstring + ',' + WINDOW.getProperty(mbstring) + ")")
        xbmc.executebuiltin('Skin.SetString(' + mbstring + '.small,' + WINDOW.getProperty(mbstring + '.small') + ")")
        mbstring = "MB3.Background.Movie.FanArt"
        xbmc.executebuiltin('Skin.SetString(' + mbstring + ',' + WINDOW.getProperty(mbstring) + ")")
        xbmc.executebuiltin('Skin.SetString(' + mbstring + '.small,' + WINDOW.getProperty(mbstring + '.small') + ")")
        mbstring = "MB3.Background.TV.FanArt"
        xbmc.executebuiltin('Skin.SetString(' + mbstring + ',' + WINDOW.getProperty(mbstring) + ")")
        xbmc.executebuiltin('Skin.SetString(' + mbstring + '.small,' + WINDOW.getProperty(mbstring + '.small') + ")")
        mbstring = "MB3.Background.Music.FanArt"
        xbmc.executebuiltin('Skin.SetString(' + mbstring + ',' + WINDOW.getProperty(mbstring) + ")")
        xbmc.executebuiltin('Skin.SetString(' + mbstring + '.small,' + WINDOW.getProperty(mbstring + '.small') + ")")
        
    def SetMB3WindowProperties(self, filter=None, shared=False ):
        self.logMsg("[MB3 SkinHelper] setting skin properties...")
        try:
            #Get the global host variable set in settings
            WINDOW = xbmcgui.Window( 10000 )
            sectionCount=0
            usrMoviesCount=0
            usrMusicCount=0
            usrTVshowsCount=0
            stdMoviesCount=0
            stdTVshowsCount=0
            stdMusicCount=0
            stdPhotoCount=0
            stdChannelsCount=0
            stdPlaylistsCount=0
            stdSearchCount=0
            dirItems = []
            
            if __settings__.getSetting('collapseBoxSets')=='true':
                collapseBoxSets = True
            else:
                collapseBoxSets = False
            
            allSections = MainModule.getCollections()
            collectionCount = 0
            mode=0
            for section in allSections:
                details={'title' : section.get('title', 'Unknown') }

                extraData={ 'fanart_image' : '' ,
                            'type'         : "Video" ,
                            'thumb'        : '' ,
                            'token'        : section.get('token',None) }

                extraData['mode']=mode
                modeurl="&mode=0"
                s_url='http://%s%s' % (section['address'], section['path'])
                murl= "?url="+urllib.quote(s_url)+modeurl
                searchurl = "?url="+urllib.quote(s_url)+"&mode=2"

                #Build that listing..
                total = section.get('total')
                if (total == None):
                    total = 0
                
                window=""
                if section.get('sectype')=='photo':
                    window="Pictures"
                elif section.get('sectype')=='music':
                    window="MusicLibrary "
                else:
                    window="VideoLibrary"
                
                #get user collections
                if not "std." in section.get('sectype'):
                    collectionCount += 1
                    #get user collections - NOT indexed by type
                    WINDOW.setProperty("MediaBrowser.usr.%d.title"               % (sectionCount) , section.get('title', 'Unknown'))
                    WINDOW.setProperty("MediaBrowser.usr.%d.path"                % (sectionCount) , "ActivateWindow("+window+",plugin://plugin.video.xbmb3c/" + murl+",return)")
                    WINDOW.setProperty("MediaBrowser.usr.%d.type"                % (sectionCount) , section.get('section'))
                    WINDOW.setProperty("MediaBrowser.usr.%d.fanart"              % (sectionCount) , section.get('fanart_image'))
                    WINDOW.setProperty("MediaBrowser.usr.%d.recent.path"         % (sectionCount) , "ActivateWindow(" + window + ",plugin://plugin.video.xbmb3c/?url=http://" + urllib.quote(section['address'] + section.get('recent_path', '')) + modeurl + ",return)")
                    WINDOW.setProperty("MediaBrowser.usr.%d.recent.content"      % (sectionCount) , "plugin://plugin.video.xbmb3c/?url=http://" + urllib.quote(section['address'] + section.get('recent_path', '')) + modeurl)
                    WINDOW.setProperty("MediaBrowser.usr.%d.total" % (sectionCount) , str(total))
                    if section.get('sectype')=='movies':
                        if collapseBoxSets == True:
                            WINDOW.setProperty("MediaBrowser.usr.%d.path"      % (sectionCount) , "ActivateWindow(" + window + ",plugin://plugin.video.xbmb3c/?url=http://" + urllib.quote(section['address'] + section.get('collapsed_path', '')) + modeurl + ",return)")
                    if section.get('sectype')=='tvshows':
                        WINDOW.setProperty("MediaBrowser.usr.%d.nextepisodes.path"   % (sectionCount) , "ActivateWindow(" + window + ",plugin://plugin.video.xbmb3c/?url=http://" + urllib.quote(section['address'] + section.get('nextepisodes_path', '')) + modeurl + ",return)")
                        WINDOW.setProperty("MediaBrowser.usr.%d.nextepisodes.content"   % (sectionCount) , "plugin://plugin.video.xbmb3c/?url=http://" + urllib.quote(section['address'] + section.get('nextepisodes_path', '')) + modeurl)
                    if section.get('sectype')!='photo' and section.get('sectype')!='music':
                        WINDOW.setProperty("MediaBrowser.usr.%d.unwatched.path"      % (sectionCount) , "ActivateWindow(" + window + ",plugin://plugin.video.xbmb3c/?url=http://" + urllib.quote(section['address'] + section.get('unwatched_path', '')) + modeurl + ",return)")
                        WINDOW.setProperty("MediaBrowser.usr.%d.unwatched.content"      % (sectionCount) , "plugin://plugin.video.xbmb3c/?url=http://" + urllib.quote(section['address'] + section.get('unwatched_path', '')) + modeurl)
                        WINDOW.setProperty("MediaBrowser.usr.%d.inprogress.path"     % (sectionCount) , "ActivateWindow(" + window + ",plugin://plugin.video.xbmb3c/?url=http://" + urllib.quote(section['address'] + section.get('inprogress_path', '')) + modeurl + ",return)")
                        WINDOW.setProperty("MediaBrowser.usr.%d.inprogress.content"     % (sectionCount) , "plugin://plugin.video.xbmb3c/?url=http://" + urllib.quote(section['address'] + section.get('inprogress_path', '')) + modeurl)
                        WINDOW.setProperty("MediaBrowser.usr.%d.genre.path"          % (sectionCount) , "ActivateWindow(" + window + ",plugin://plugin.video.xbmb3c/?url=http://" + urllib.quote(section['address'] + section.get('genre_path', '')) + modeurl + ",return)")
          
                    #get user collections - indexed by type
                    if section.get('sectype')=='movies':
                        WINDOW.setProperty("MediaBrowser.usr.movies.%d.title"         % (usrMoviesCount) , section.get('title', 'Unknown'))
                        WINDOW.setProperty("MediaBrowser.usr.movies.%d.path"          % (usrMoviesCount) , "ActivateWindow("+window+",plugin://plugin.video.xbmb3c/" + murl+",return)")
                        WINDOW.setProperty("MediaBrowser.usr.movies.%d.type"          % (usrMoviesCount) , section.get('section'))
                        WINDOW.setProperty("MediaBrowser.usr.movies.%d.content"       % (usrMoviesCount) , "plugin://plugin.video.xbmb3c/" + murl)
                        WINDOW.setProperty("MediaBrowser.usr.movies.%d.recent.path"         % (usrMoviesCount) , "ActivateWindow(" + window + ",plugin://plugin.video.xbmb3c/?url=http://" + urllib.quote(section['address'] + section.get('recent_path', '')) + modeurl + ",return)")
                        WINDOW.setProperty("MediaBrowser.usr.movies.%d.unwatched.path"      % (usrMoviesCount) , "ActivateWindow(" + window + ",plugin://plugin.video.xbmb3c/?url=http://" + urllib.quote(section['address'] + section.get('unwatched_path', '')) + modeurl + ",return)")
                        WINDOW.setProperty("MediaBrowser.usr.movies.%d.inprogress.path"     % (usrMoviesCount) , "ActivateWindow(" + window + ",plugin://plugin.video.xbmb3c/?url=http://" + urllib.quote(section['address'] + section.get('inprogress_path', '')) + modeurl + ",return)")
                        WINDOW.setProperty("MediaBrowser.usr.movies.%d.genre.path"          % (usrMoviesCount) , "ActivateWindow(" + window + ",plugin://plugin.video.xbmb3c/?url=http://" + urllib.quote(section['address'] + section.get('genre_path', '')) + modeurl + ",return)")
                        usrMoviesCount +=1
                        
                    if section.get('sectype')=='tvshows':
                        WINDOW.setProperty("MediaBrowser.usr.tvshows.%d.title"        % (usrTVshowsCount) , section.get('title', 'Unknown'))
                        WINDOW.setProperty("MediaBrowser.usr.tvshows.%d.path"         % (usrTVshowsCount) , "ActivateWindow("+window+",plugin://plugin.video.xbmb3c/" + murl+",return)")
                        WINDOW.setProperty("MediaBrowser.usr.tvshows.%d.type"         % (usrTVshowsCount) , section.get('section'))
                        WINDOW.setProperty("MediaBrowser.usr.tvshows.%d.content"       % (usrTVshowsCount) , "plugin://plugin.video.xbmb3c/" + murl)
                        WINDOW.setProperty("MediaBrowser.usr.tvshows.%d.recent.path"         % (usrTVshowsCount) , "ActivateWindow(" + window + ",plugin://plugin.video.xbmb3c/?url=http://" + urllib.quote(section['address'] + section.get('recent_path', '')) + modeurl + ",return)")
                        WINDOW.setProperty("MediaBrowser.usr.tvshows.%d.unwatched.path"      % (usrTVshowsCount) , "ActivateWindow(" + window + ",plugin://plugin.video.xbmb3c/?url=http://" + urllib.quote(section['address'] + section.get('unwatched_path', '')) + modeurl + ",return)")
                        WINDOW.setProperty("MediaBrowser.usr.tvshows.%d.inprogress.path"     % (usrTVshowsCount) , "ActivateWindow(" + window + ",plugin://plugin.video.xbmb3c/?url=http://" + urllib.quote(section['address'] + section.get('inprogress_path', '')) + modeurl + ",return)")
                        WINDOW.setProperty("MediaBrowser.usr.tvshows.%d.genre.path"          % (usrTVshowsCount) , "ActivateWindow(" + window + ",plugin://plugin.video.xbmb3c/?url=http://" + urllib.quote(section['address'] + section.get('genre_path', '')) + modeurl + ",return)")
                        WINDOW.setProperty("MediaBrowser.usr.tvshows.%d.nextepisodes.path"   % (usrTVshowsCount) , "ActivateWindow(" + window + ",plugin://plugin.video.xbmb3c/?url=http://" + urllib.quote(section['address'] + section.get('nextepisodes_path', '')) + modeurl + ",return)")
                        usrTVshowsCount +=1
                        
                    if section.get('sectype')=='music':
                        WINDOW.setProperty("MediaBrowser.usr.music.%d.title"        % (usrMusicCount) , section.get('title', 'Unknown'))
                        WINDOW.setProperty("MediaBrowser.usr.music.%d.path"         % (usrMusicCount) , "ActivateWindow("+window+",plugin://plugin.video.xbmb3c/" + murl+",return)")
                        WINDOW.setProperty("MediaBrowser.usr.music.%d.type"         % (usrMusicCount) , section.get('section'))
                        WINDOW.setProperty("MediaBrowser.usr.music.%d.content"       % (usrMusicCount) , "plugin://plugin.video.xbmb3c/" + murl)
                        usrMusicCount +=1
                    
                else:    
                    # get standard MB3 root items
                    if section.get('sectype')=='std.movies':
                        WINDOW.setProperty("MediaBrowser.std.movies.%d.title"               % (stdMoviesCount) , section.get('title', 'Unknown'))
                        if collapseBoxSets == True:
                            collapsed_url = murl.replace("&mode=0", "")
                            collapsed_url = collapsed_url + "%26CollapseBoxSetItems%3Dtrue&mode=0"
                        else:
                            collapsed_url = murl
                        WINDOW.setProperty("MediaBrowser.std.movies.%d.path"                % (stdMoviesCount) , "ActivateWindow("+window+",plugin://plugin.video.xbmb3c/" + collapsed_url+",return)")
                        WINDOW.setProperty("MediaBrowser.std.movies.%d.content"                % (stdMoviesCount) , "plugin://plugin.video.xbmb3c/" + murl)
                        WINDOW.setProperty("MediaBrowser.std.movies.%d.type"                % (stdMoviesCount) , section.get('section'))
                        stdMoviesCount +=1
                    elif section.get('sectype')=='std.tvshows':
                        WINDOW.setProperty("MediaBrowser.std.tvshows.%d.title"        % (stdTVshowsCount) , section.get('title', 'Unknown'))
                        WINDOW.setProperty("MediaBrowser.std.tvshows.%d.path"         % (stdTVshowsCount) , "ActivateWindow("+window+",plugin://plugin.video.xbmb3c/" + murl+",return)")
                        WINDOW.setProperty("MediaBrowser.std.tvshows.%d.type"         % (stdTVshowsCount) , section.get('section'))
                        WINDOW.setProperty("MediaBrowser.std.tvshows.%d.content"       % (stdTVshowsCount) , "plugin://plugin.video.xbmb3c/" + murl)
                        stdTVshowsCount +=1    
                    elif section.get('sectype')=='std.music':
                        WINDOW.setProperty("MediaBrowser.std.music.%d.title"        % (stdMusicCount) , section.get('title', 'Unknown'))
                        WINDOW.setProperty("MediaBrowser.std.music.%d.path"         % (stdMusicCount) , "ActivateWindow("+window+",plugin://plugin.video.xbmb3c/" + murl+",return)")
                        WINDOW.setProperty("MediaBrowser.std.music.%d.type"         % (stdMusicCount) , section.get('section'))
                        WINDOW.setProperty("MediaBrowser.std.music.%d.content"       % (stdMusicCount) , "plugin://plugin.video.xbmb3c/" + murl)  
                        stdMusicCount +=1     
                    elif section.get('sectype')=='std.photo':
                        WINDOW.setProperty("MediaBrowser.std.photo.%d.title"        % (stdPhotoCount) , section.get('title', 'Unknown'))
                        WINDOW.setProperty("MediaBrowser.std.photo.%d.path"         % (stdPhotoCount) , "ActivateWindow("+window+",plugin://plugin.video.xbmb3c/" + murl+",return)")
                        WINDOW.setProperty("MediaBrowser.std.photo.%d.type"         % (stdPhotoCount) , section.get('section'))
                        WINDOW.setProperty("MediaBrowser.std.photo.%d.content"       % (stdPhotoCount) , "plugin://plugin.video.xbmb3c/" + murl) 
                        stdPhotoCount +=1
                    elif section.get('sectype')=='std.channels':
                        WINDOW.setProperty("MediaBrowser.std.channels.%d.title"        % (stdChannelsCount) , section.get('title', 'Unknown'))
                        WINDOW.setProperty("MediaBrowser.std.channels.%d.path"         % (stdChannelsCount) , "ActivateWindow("+window+",plugin://plugin.video.xbmb3c/" + murl+",return)")
                        WINDOW.setProperty("MediaBrowser.std.channels.%d.type"         % (stdChannelsCount) , section.get('section'))
                        WINDOW.setProperty("MediaBrowser.std.channels.%d.content"       % (stdChannelsCount) , "plugin://plugin.video.xbmb3c/" + murl)  
                        stdChannelsCount +=1
                    elif section.get('sectype')=='std.playlists':
                        WINDOW.setProperty("MediaBrowser.std.playlists.%d.title"        % (stdPlaylistsCount) , section.get('title', 'Unknown'))
                        WINDOW.setProperty("MediaBrowser.std.playlists.%d.path"         % (stdPlaylistsCount) , "ActivateWindow("+window+",plugin://plugin.video.xbmb3c/" + murl+",return)")
                        WINDOW.setProperty("MediaBrowser.std.playlists.%d.type"         % (stdPlaylistsCount) , section.get('section'))
                        WINDOW.setProperty("MediaBrowser.std.playlists.%d.content"       % (stdPlaylistsCount) , "plugin://plugin.video.xbmb3c/" + murl)  
                        stdPlaylistsCount +=1
                    elif section.get('sectype')=='std.search':
                        WINDOW.setProperty("MediaBrowser.std.search.%d.title"        % (stdSearchCount) , section.get('title', 'Unknown'))
                        WINDOW.setProperty("MediaBrowser.std.search.%d.path"         % (stdSearchCount) , "ActivateWindow("+window+",plugin://plugin.video.xbmb3c/" + searchurl+",return)")
                        WINDOW.setProperty("MediaBrowser.std.search.%d.type"         % (stdSearchCount) , section.get('section')) 
                        stdSearchCount +=1 
                sectionCount += 1 
            WINDOW.setProperty("MediaBrowser.usr.Count", str(collectionCount))
        except Exception, e:
            self.logMsg("[XBMB3C SkinHelperThread] exception in SetMB3WindowProperties: " + str(e), level=0)
            return False

        return True
    