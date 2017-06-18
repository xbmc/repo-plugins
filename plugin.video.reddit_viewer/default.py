#!/usr/bin/python
# encoding: utf-8
import urllib
import urllib2
import sys
import os
import json
import xbmc
import xbmcplugin
import xbmcgui
import xbmcaddon


from urllib import urlencode
from decimal import DivisionByZero

from resources.lib.utils import log

reload(sys)
sys.setdefaultencoding("utf-8")

addon         = xbmcaddon.Addon()
addon_path    = addon.getAddonInfo('path')      #where the addon resides
profile_path  = addon.getAddonInfo('profile')   #where user settings are stored
pluginhandle  = int(sys.argv[1])
addonID       = addon.getAddonInfo('id')  #plugin.video.reddit_viewer

WINDOW        = xbmcgui.Window(10000)

reddit_userAgent = "XBMC:"+addonID+":v"+addon.getAddonInfo('version')+" (by /u/gsonide)"
reddit_clientID      ="hXEx62LGqxLj8w"
reddit_redirect_uri  ='http://localhost:8090/'   #specified when registering for a clientID
reddit_refresh_token =addon.getSetting("reddit_refresh_token")
reddit_access_token  =addon.getSetting("reddit_access_token") #1hour token

urlMain = "https://www.reddit.com"

autoplayAll          = addon.getSetting("autoplayAll") == "true"
autoplayUnwatched    = addon.getSetting("autoplayUnwatched") == "true"
autoplayUnfinished   = addon.getSetting("autoplayUnfinished") == "true"
autoplayRandomize    = addon.getSetting("autoplayRandomize") == "true"

forceViewMode        = addon.getSetting("forceViewMode") == "true"
viewMode             = str(addon.getSetting("viewMode"))
comments_viewMode    = str(addon.getSetting("comments_viewMode"))
album_viewMode       = str(addon.getSetting("album_viewMode"))

hide_nsfw            = addon.getSetting("hide_nsfw") == "true"
domain_filter        = addon.getSetting("domain_filter")
subreddit_filter     = addon.getSetting("subreddit_filter")

r_AccessToken         = addon.getSetting("r_AccessToken")

sitemsPerPage        = addon.getSetting("itemsPerPage")
try: itemsPerPage = int(sitemsPerPage)
except: itemsPerPage = 50

itemsPerPage          = ["10", "25", "50", "75", "100"][itemsPerPage]
TitleAddtlInfo        = addon.getSetting("TitleAddtlInfo") == "true"   #Show additional post info on title</string>

DoNotResolveLinks     = addon.getSetting("DoNotResolveLinks") == 'true'

CommentTreshold          = addon.getSetting("CommentTreshold")
try: int_CommentTreshold = int(CommentTreshold)
except: int_CommentTreshold = -1000    #if CommentTreshold can't be converted to int, show all comments

try:istreamable_quality=int(addon.getSetting("streamable_quality"))  #values 0 or 1
except:istreamable_quality=0
streamable_quality  =["full", "mobile"][istreamable_quality]       #https://streamable.com/documentation

addonUserDataFolder = xbmc.translatePath("special://profile/addon_data/"+addonID)
subredditsFile      = xbmc.translatePath("special://profile/addon_data/"+addonID+"/subreddits")
subredditsPickle    = xbmc.translatePath("special://profile/addon_data/"+addonID+"/subreddits.pickle")  #new type of saving the settings

ytdl_core_path=xbmc.translatePath(  addon_path+"/resources/lib/youtube_dl/" )

REQUEST_TIMEOUT=5 #requests.get timeout in seconds

if not os.path.isdir(addonUserDataFolder):
    os.mkdir(addonUserDataFolder)

def parameters_string_to_dict(parameters):
    paramDict = {}
    if parameters:
        paramPairs = parameters[1:].split("&")
        for paramsPair in paramPairs:
            paramSplits = paramsPair.split('=')
            if (len(paramSplits)) == 2:
                paramDict[paramSplits[0]] = paramSplits[1]
    return paramDict

if __name__ == '__main__':

    params = parameters_string_to_dict(sys.argv[2])
    mode   = urllib.unquote_plus(params.get('mode', ''))
    url    = urllib.unquote_plus(params.get('url', ''))
    type_  = urllib.unquote_plus(params.get('type', '')) #type is a python function, try not to use a variable name same as function
    name   = urllib.unquote_plus(params.get('name', ''))


    log( "----------------v" + addon.getAddonInfo('version')  + ' ' + ( mode+': '+url if mode else '' ) +'-----------------')


    from resources.lib.slideshow import autoSlideshow
    from resources.lib.utils import addtoFilter,open_web_browser
    from resources.lib.actions import addSubreddit,editSubreddit,removeSubreddit,viewImage,viewTallImage,listAlbum,playURLRVideo, loopedPlayback,error_message,update_youtube_dl_core,searchReddits
    from resources.lib.actions import playVideo, playYTDLVideo, parse_url_and_play, listRelatedVideo #queueVideo

    from resources.lib.autoplay import autoPlay
    from resources.lib.reddit import reddit_get_refresh_token, reddit_get_access_token, reddit_revoke_refresh_token, reddit_save
    from resources.lib.main_listing import index, listSubReddit, listLinksInComment

    if mode=='':mode='index'  #default mode is to list start page (index)

    plugin_modes = {'index'                 : index
                    ,'listSubReddit'        : listSubReddit
                    ,'playVideo'            : playVideo
                    ,'addSubreddit'         : addSubreddit
                    ,'editSubreddit'        : editSubreddit
                    ,'removeSubreddit'      : removeSubreddit
                    ,'autoPlay'             : autoPlay
                    ,'viewImage'            : viewImage
                    ,'viewTallImage'        : viewTallImage
                    ,'listAlbum'            : listAlbum
                    ,'addtoFilter'          : addtoFilter
                    ,'openBrowser'          : open_web_browser

                    ,'searchReddits'        : searchReddits
                    ,'listLinksInComment'   : listLinksInComment
                    ,'playYTDLVideo'        : playYTDLVideo
                    ,'playURLRVideo'        : playURLRVideo
                    ,'loopedPlayback'       : loopedPlayback
                    ,'error_message'        : error_message
                    ,'update_youtube_dl_core':update_youtube_dl_core
                    ,'get_refresh_token'    : reddit_get_refresh_token
                    ,'get_access_token'     : reddit_get_access_token
                    ,'revoke_refresh_token' : reddit_revoke_refresh_token
                    ,'play'                 : parse_url_and_play
                    ,'reddit_save'          : reddit_save
                    ,'listRelatedVideo'     : listRelatedVideo
                    }

    plugin_modes[mode](url,name,type_)
