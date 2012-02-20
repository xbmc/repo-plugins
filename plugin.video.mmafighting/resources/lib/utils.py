#!/usr/bin/env python

import os
import sys

import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin

try:
    import StorageServer
except:
    import storageserverdummy as StorageServer

from resources.lib.mmafighting import *

### get addon info
__addon__             = xbmcaddon.Addon()
__addonid__           = __addon__.getAddonInfo('id')
__addonidint__        = int(sys.argv[1])
__addondir__          = xbmc.translatePath(__addon__.getAddonInfo('path'))

# initialise cache object to speed up plugin operation
cache = StorageServer.StorageServer(__addonid__ + '-videos', 24)

def getParams():
    
    """Parse and return the arguments passed to the addon in a usable form
    
    Returns:    param -- A dictionary containing the parameters which have been passed to the addon"""
    
    # initialise empty list to store params
    param=[]
    
    # store params as string
    paramstring=sys.argv[2]
    
    # check if params were provided
    if len(paramstring)>=2:
        
        # store params as string
        params=sys.argv[2]
        
        # remove ? from param string
        cleanedparams=params.replace('?','')
        
        # check if last argument is /
        if (params[len(params)-1]=='/'):
            params=params[0:len(params)-2]
        
        # split param string into individual params
        pairsofparams=cleanedparams.split('&')
        
        # initialise empty dict to store params
        param={}
        
        # loop through all params
        for i in range(len(pairsofparams)):
            
            # initialise empty dict to store split params
            splitparams={}
            
            # get name and value of param
            splitparams=pairsofparams[i].split('=')
            
            # check if param has value
            if (len(splitparams))==2:
                
                # add value to param dict
                param[splitparams[0]]=splitparams[1]
    
    # return dict of params
    return param


def log(txt, severity=xbmc.LOGDEBUG):
    
    """Log txt to xbmc.log at specified severity
    
    Arguments:  txt -- A string containing the text to be logged
                severity -- Logging level to log text at (Default to LOGDEBUG)"""

    # generate log message from addon name and txt
    message = ('%s: %s' % (__addonid__, txt))
    
    # write message to xbmc.log
    xbmc.log(msg=message, level=severity)


def addVideo(linkName = '', url = '', thumbPath = '', date = ''):
    
    """Add a video to an XBMC directory listing
    
    Arguments:  linkName -- A string containg the name of the video
                url -- A string containing the direct url to the video
                thumbPath -- A string containg the url/path of the video's thumbnail image
                date -- a dataetime object containg the date of the video"""
    
    # initialise a listitem object to store video details
    li = xbmcgui.ListItem(linkName, iconImage = thumbPath, thumbnailImage = thumbPath)
    
    # set the video to playable
    li.setProperty("IsPlayable", 'true')
    
    # set the infolabels for the video
    li.setInfo( type="Video", infoLabels={ "title": linkName, "date":date} )
    
    # set fanart image for video
    li.setProperty( "Fanart_Image", os.path.join(__addondir__, 'fanart.jpg'))
    
    # add listitem object to list
    xbmcplugin.addDirectoryItem(handle = __addonidint__, url = url, listitem = li, isFolder = False)


def addNext(page):
    
    """Add a 'Next Page' button to a directory listing"""
    
    # construct url of next page
    u = sys.argv[0] + "?page=%s" % str(page)
    
    # initialise listitem object
    li = xbmcgui.ListItem('Next Page', iconImage = "DefaultFolder.png", thumbnailImage = "DefaultFolder.png")
    
    # set title of list item
    li.setInfo( type = "Video", infoLabels = { "Title" : 'Next Page' })
    
    # add listitem object to list
    xbmcplugin.addDirectoryItem(handle = __addonidint__, url = u, listitem = li, isFolder = True)

def playVideo(url):
    
    """Retrieve video details and play video
    
    Arguments:  url -- A string containing the url of the videos page on mmafighting.com"""
    
    # get video details
    video = cache.cacheFunction(getVideoDetails, url)
    
    # add video details to listitem
    listitem = xbmcgui.ListItem(label=video['title'], iconImage=video['thumb'], thumbnailImage=video['thumb'], path=video['url'])
    
    # play listitem
    xbmcplugin.setResolvedUrl(handle=int(sys.argv[1]), succeeded=True, listitem=listitem)  
