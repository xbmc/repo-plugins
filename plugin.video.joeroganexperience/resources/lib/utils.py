#!/usr/bin/env python

import os
import re
import sys
import urllib
import urllib2

import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin

import StorageServer

from elementtree import ElementTree as ET

### get addon info
__addon__             = xbmcaddon.Addon()
__addonid__           = __addon__.getAddonInfo('id')
__addonidint__        = int(sys.argv[1])
__addondir__          = xbmc.translatePath(__addon__.getAddonInfo('path'))

# initialise cache object to speed up plugin operation
cache = StorageServer.StorageServer(__addonid__ + '-ustreamvideos', 96)

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


def getHtml(url):
    
    """Retrieve and return remote resource as string
    
    Arguments:  url -- A string containing the url of a remote page to retrieve
    Returns:    data -- A string containing the contents to the remote page"""

    # Build the page request including setting the User Agent
    req  = urllib2.Request(url)
    req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')

    # connect to url using urlopen
    client = urllib2.urlopen(req)
    
    # read data from page
    data = client.read()
    
    # close connection to url
    client.close()
    
    # return the retrieved data
    return data


def log(txt, severity=xbmc.LOGDEBUG):
    
    """Log txt to xbmc.log at specified severity
    
    Arguments:  txt -- A string containing the text to be logged
                severity -- Logging level to log text at (Default to LOGDEBUG)"""

    # generate log message from addon name and txt
    message = ('%s: %s' % (__addonid__, txt))
    
    # write message to xbmc.log
    xbmc.log(msg=message, level=severity)


def addVideo(linkName = '', source = '', videoID = '', thumbPath = '', date = ''):
    
    """Add a video to an XBMC directory listing
    
    Arguments:  linkName -- A string containg the name of the video
                url -- A string containing the direct url to the video
                thumbPath -- A string containg the url/path of the video's thumbnail image
                date -- a dataetime object containg the date of the video"""
    
    url = sys.argv[0] + "?source=" + source + "&id=" + videoID
    
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
    
    """Add a 'Next Page' button to a directory listing
    
    Arguments:  page -- An Integer containing the number of the page to load on clicking the next page button"""
    
    # construct url of next page
    u = sys.argv[0] + "?page=%s" % str(page)
    
    # initialise listitem object
    li = xbmcgui.ListItem('Next Page', iconImage = "DefaultFolder.png", thumbnailImage = "DefaultFolder.png")
    
    # set title of list item
    li.setInfo( type = "Video", infoLabels = { "Title" : 'Next Page' })
    
    # set fanart image for video
    li.setProperty( "Fanart_Image", os.path.join(__addondir__, 'fanart.jpg'))
    
    # add listitem object to list
    xbmcplugin.addDirectoryItem(handle = __addonidint__, url = u, listitem = li, isFolder = True)


def endDir():
    
    """Tell XBMC we have finished adding items to the directory list"""
    
    xbmcplugin.endOfDirectory(handle = __addonidint__)


def playVideo(vidSrc, vidID):
    
    """Resolve the provided url and play video
    
    Arguments:  url -- A string containing the url of the videos page on mmafighting.com"""
    
    # call getVideoUrl to resolve url for playback
    videoUrl = getVideoUrl(vidSrc, vidID)
    
    # set success to true if video found
    if videoUrl:
        log('Successfully resolved video url: %s' % videoUrl)
        success = True
    else:
        log('Unable to resolve video url', xbmc.LOGERROR)
        success = False
    
    # add video details to listitem
    listitem = xbmcgui.ListItem(path = videoUrl)
    
    # play listitem
    xbmcplugin.setResolvedUrl(handle = __addonidint__, succeeded = success, listitem = listitem)  


def getVideoUrl(vidSrc, vidID):

    """Resolve the video url based on source and video id
    
    Arguments:  vidSrc -- A string containing the video's source: 'vimeo' or 'ustream'
                vidID -- A string containing the video's ID number
    Returns:    videoUrl -- A string containing the url of the video to be played"""

    # check if video is from Vimeo
    if vidSrc == 'vimeo':

        # construct path to play video using vimeo plugin
        videoUrl = 'plugin://plugin.video.vimeo?action=play_video&videoid=' + vidID
    
    # check if video is from ustream
    elif vidSrc == 'ustream':
        
        # construct url to use for API call
        apiUrl = 'http://api.ustream.tv/xml/video/%s/getInfo?key=A5379FCD5891A9F9A029F84422CAC98C' % vidID
        
        # initialise the tree object using the returned data so it can be parsed
        tree = ET.fromstring(cache.cacheFunction(getHtml, apiUrl))
        video = tree.find('results')

        # get episode url
        videoUrl = video.findtext('mp4Url')

        # check if video url was found
        if not videoUrl:
            
            # check alternate field for video url
            videoUrl = video.findtext('liveHttpUrl')

    #return video url
    return videoUrl
