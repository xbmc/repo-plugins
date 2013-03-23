# -*- coding: utf-8 -*-
import sys
import os
import re
import time
import random
import urllib

import simplejson

if hasattr(sys.modules[u"__main__"], u"xbmc"):
    xbmc = sys.modules[u"__main__"].xbmc
else:
    import xbmc
    
if hasattr(sys.modules[u"__main__"], u"xbmcgui"):
    xbmcgui = sys.modules[u"__main__"].xbmcgui
else:
    import xbmcgui

if hasattr(sys.modules[u"__main__"], u"xbmcplugin"):
    xbmcplugin = sys.modules[u"__main__"].xbmcplugin
else:
    import xbmcplugin

import mycgi
import utils

from loggingexception import LoggingException
from provider import Provider
from vineplayer import VinePlayer
#from watched import WatchedPlayer

apiUrl = u"http://vinetube-api.appspot.com/mostrecent"

class VineProvider(Provider):

    def GetProviderId(self):
        return u"Vine"

    def ExecuteCommand(self, mycgi):
        return super(VineProvider, self).ExecuteCommand(mycgi)
    
    def GetHeaders(self):
        headers = {
                   u'DNT' : u'1'
                   }
        return headers

    def GetWarningFile(self):
        return os.path.join( sys.modules[u"__main__"].DATA_FOLDER, 'warning_shown')

    def ShowRootMenu(self):
        self.log(u"", xbmc.LOGDEBUG)

        warningFilePath = self.GetWarningFile()
        if not os.path.exists(warningFilePath):
            dialog = xbmcgui.Dialog()
            # WARNING: These videos are not moderated. By using this plugin you are accepting sole responsibility for any and all consequences of said use.
            action = dialog.yesno(self.GetProviderId(), self.language(60040), self.language(60041), self.language(60042), self.language(60060), self.language(60050) ) # 1=Continue; 0=Cancel
    
            if action == 0:
                return True
            
            f = open(warningFilePath, u"w")
            f.write('')
            f.close()
            
        try:
            listItems = []
            # Latest Vines
            label = self.language(60000)
            thumbnailPath = self.GetThumbnailPath(label)

            newListItem = xbmcgui.ListItem( label=label )
            newListItem.setThumbnailImage(thumbnailPath)
            url = self.GetURLStart()  + u'&hashtag='
            
            listItems.append((url, newListItem, False))
            
            # Search by #tag
            label = self.language(60010)
            thumbnailPath = self.GetThumbnailPath(label)

            newListItem = xbmcgui.ListItem( label=self.language(60010) )
            newListItem.setThumbnailImage(thumbnailPath)
            url = self.GetURLStart() + u'&search=1'
            
            listItems.append((url, newListItem, False))
            
            xbmcplugin.addDirectoryItems( handle=self.pluginhandle, items=listItems )
            xbmcplugin.endOfDirectory( handle=self.pluginhandle, succeeded=True )
            
            return True
        except (Exception) as exception:
            exception = LoggingException.fromException(exception)

            #TODO Change text
            # Error processing categories
            exception.addLogMessage(self.language(30795))
            exception.process(self.language(30765), self.language(30795), severity = xbmc.LOGWARNING)
    
            return False
    
        

    def ParseCommand(self, mycgi):
        self.log(u"", xbmc.LOGDEBUG)

        (search) = mycgi.Param( u'search')

        if search <> '':
            return self.DoSearch()

        return self.PlayVideoWithDialog(self.PlayVideos, ())

    def GetPlayer(self):
        if self.addon.getSetting( u'show_tweets' ) == u'true':
            player = VinePlayer(xbmc.PLAYER_CORE_AUTO)
            player.initialise(self.log)
            return player
        else:
            return xbmc.Player(xbmc.PLAYER_CORE_AUTO)

    def PlayVideos(self, hashTag = None, dummy = None):
        queuedVideos = []
        epochTimeMS = int(round(time.time() * 1000.0))
        callback = "jQuery1900%s_%s" % ( random.randint(1000000000000000, 9999999999999999), epochTimeMS)

        self.log("callback: " + callback)
        self.log("hashTag: " + repr(hashTag))
        offset = 1
        stop = False
        
        playList=xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
        playList.clear()
        
        listItems = self.GetListItems(callback, epochTimeMS, offset, hashTag)
        if listItems is not None:
            for item in listItems:
                (url, listItem) = item
                if url not in queuedVideos:
                    queuedVideos.append(url)
                    playList.add(url, listItem)

        if playList.size() == 0:
            dialog = xbmcgui.Dialog()
            dialog.ok(self.GetProviderId(), self.language(60070))
            
        if self.dialog.iscanceled():
            return False

        player = self.GetPlayer()
        player.play(playList)

        self.dialog.close()
        
        if isinstance(player, VinePlayer):
            # Keep script alive so that player can process the onPlayBackStart event
            while playList.getposition() != -1 and not player.isStopped():
                xbmc.sleep(2000)
                self.log("player.isStopped(): " + repr(player.isStopped()), xbmc.LOGDEBUG)

        return True

    def GetListItems(self, callback, epoch, offset, hashTag = None):
        values = {
                   'callback':callback,
                   '_':epoch + 1 
                }

        if offset == 1:
            values['count'] = 50

        if hashTag is None:
            values['a'] = 1
        else:
            values['tag'] = '#' + hashTag
            
        try:
            jsonText = None
            jsonText = self.httpManager.GetWebPageDirect(apiUrl + "?" + urllib.urlencode(values))
    
            jsonData = simplejson.loads(utils.extractJSON(jsonText))
            
            playList=xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
            playList.clear()
            
            listItems = []
            for vineData in jsonData:
                """
                title = ""
                if len(vineData['name']) > 0:
                    title = vineData['name'] + ": "
                
                if len(vineData['message']) > 0:
                        title = title + vineData['message']
                """
                url = vineData['video_url']
                icon = vineData['avatar_73']
              
                infoLabels = {u'Title': vineData['name'], u'Plot': vineData['message']}
                
                self.log("infoLabels: " + utils.drepr(infoLabels))
                listItem = xbmcgui.ListItem(vineData['message'], iconImage = icon )
                listItem.setInfo(u'video', infoLabels)
                listItems.append((url, listItem))
            
            listItems.reverse()
            self.log( "listItems: " + repr(listItems)) 

            return listItems
        except (Exception) as exception:
            exception = LoggingException.fromException(exception)

            if jsonText is not None:
                msg = u"jsonText:\n\n%s\n\n" % jsonText
                exception.addLogMessage(msg)
                
            # Error processing web page
            exception.addLogMessage(self.language(30780))
            exception.process(self.language(60080), self.language(30780), severity = self.logLevel( xbmc.LOGERROR ))
    
            return None

    def DoSearchQuery( self, query ):
        self.log("query: %s" % query, xbmc.LOGDEBUG)
        
        query = query.replace('#','')
        query = query.replace(' ','')
        
        return self.PlayVideoWithDialog(self.PlayVideos, (query, None))
