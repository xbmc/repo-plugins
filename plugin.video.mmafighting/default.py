#!/usr/bin/env python

import os
import sys
import traceback
import urllib
import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin

try:
    import StorageServer
except:
    import storageserverdummy as StorageServer

from BeautifulSoup import BeautifulSoup

from resources.lib.mmafighting import *
from resources.lib.utils import *

### get addon info
__addon__             = xbmcaddon.Addon()
__addonidint__        = int(sys.argv[1])
__addonname__         = __addon__.getAddonInfo('name')
__addonid__         = __addon__.getAddonInfo('id')
__addondir__          = xbmc.translatePath(__addon__.getAddonInfo('path'))

# initialise cache object to speed up plugin operation
cache = StorageServer.StorageServer(__addonid__ + '-pages', 1)

if __name__ == '__main__':

    # parse script arguments
    params = getParams()

    # get video url
    try:
        
        # check if video url has been passed to script
        videoURL = urllib.unquote_plus(params["videoURL"])
        
    except:
        
        # set videoURL to None if none passed
        videoURL = None

    # check if videoURL was found
    if videoURL:
        
        # play video
        playVideo(videoURL)
    
    # display list if videourl not passed
    else:
        
        # get current page number
        try:
            
            # check if a page number was passed to script
            page = int(urllib.unquote_plus(params["page"]))
            
        except:
            
            # set page number to 1 if none passed
            page = 1
    
        # enable episode viewtypes in xbmc
        xbmcplugin.setContent(__addonidint__, 'episodes')
    
        # loop over all videos on page
        for video in cache.cacheFunction(getVideoPages, page):
            
            # add video to directory list
            addVideo(linkName = video['title'], url = video['url'], thumbPath = video['thumb'])
        
        # add next page listitem
        addNext(page + 1)
        
        ## finish adding items to list and display
        xbmcplugin.endOfDirectory(__addonidint__)
    
