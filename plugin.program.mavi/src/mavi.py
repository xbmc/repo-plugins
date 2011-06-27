import os
import xbmc #@UnresolvedImport
import xbmcplugin #@UnresolvedImport

from class_wiring import ClassWiring
from ui.main_window import MainWindow
from ui.comments_window import CommentsWindow

'''
Created on 8 jun 2011

@author: Nick
'''

class Program:


    def __init__(self, sysArgs):
        # get app params
        self._addonPath = sysArgs[0]
        self._addonHandle = int(sysArgs[1])
        addonParams = sysArgs[2]
        
        if addonParams:
            addonParams = [part.split('=') for part in addonParams[1:].split('&')]
            addonParams = dict(addonParams)

        if addonParams:
            self._checkParams(addonParams)
        else:
            self._startApp()
        
    def _checkParams(self, params):
        if "action" in params:
            if params["action"] == "main":
                self._startApp(params["id"])
            
            elif params["action"] == "image":
                cacheManager = ClassWiring().getTempImageManager()
                file = ClassWiring().getConnectionManager().doRequest(params["file"])
                filePath = cacheManager.storeFile(file, cacheManager.urlToFilename(params["file"]))
                filePath = os.path.dirname(filePath)
                xbmc.executebuiltin("SlideShow(" + filePath + ")")
                xbmcplugin.endOfDirectory(self._addonHandle, cacheToDisc=False, updateListing=True)
            
            elif params["action"] == "comment":
                handle = params["addonHandle"]
                window = CommentsWindow(handle, self._addonPath)
                window.showComments(params["id"])
                
                xbmcplugin.endOfDirectory(self._addonHandle)
        else :
            # TODO show warning
            pass        
        

    
    def _startApp(self, after = None):
        # clear the cache
        ClassWiring().getTempImageManager().clearCache()
        
        window = MainWindow(self._addonHandle, self._addonPath)
        window.showLatestPosts(after)
        
        xbmcplugin.endOfDirectory(self._addonHandle)