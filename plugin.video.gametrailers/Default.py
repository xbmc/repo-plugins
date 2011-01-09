# coding: utf-8
'''
Created on 7 jan 2011

@author: Emuller
'''
import os,sys
import urllib,urllib2,re
import xbmc,xbmcplugin,xbmcgui,xbmcaddon #@UnresolvedImport
from xml.dom import minidom

# plugin modes
MODE_FIRST = 10
MODE_SECOND = 20
MODE_SHOWFEED = 30
MODE_SHOW_PLATFORMS = 40
MODE_SHOWTYPE = 50
MODE_SHOWORDERBY = 60
MODE_SHOWFEEDS = 70
MODE_PLAYVIDEO = 100
MODE_PLAYALL = 150

# parameter keys
PARAMETER_KEY_MODE = "mode"

# control id's
CONTROL_MAIN_LIST_START  = 50
CONTROL_MAIN_LIST_END    = 59

# plugin handle
handle = int(sys.argv[1])
__addonname__ = "plugin.video.gametrailers"
__settings__ = xbmcaddon.Addon(id='plugin.video.gametrailers')
__language__ = __settings__.getLocalizedString


# utility functions
def parameters_string_to_dict(parameters):
    ''' Convert parameters encoded in a URL to a dict. '''
    paramDict = {}
    if parameters:
        paramPairs = parameters[1:].split("&")
        for paramsPair in paramPairs:
            paramSplits = paramsPair.split('=')
            if (len(paramSplits)) == 2:
                paramDict[paramSplits[0]] = paramSplits[1]
    return paramDict

def addDirectoryItem(name, isFolder=True, parameters={},image="", isVideo=True):
    ''' Add a list item to the XBMC UI.'''
    li = xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=image)
        
    if isVideo:
        li.addContextMenuItems( [ 
                                 (__language__(30202), 'XBMC.RunPlugin(%s?%s)' % (sys.argv[0], urllib.urlencode( { "mode" : MODE_PLAYALL, "feed" : parameters.get('feed') } ) ) ),
                                 (__language__(30201), "XBMC.Action(Queue)")                                  
                                 ], replaceItems=False )
        li.setProperty("IsPlayable", "true")
        li.setProperty( "Video", "true" )  
        li.setInfo(type='Video', infoLabels=parameters)
         
    url = sys.argv[0] + '?' + urllib.urlencode(parameters)
    
    xbmcplugin.setContent( handle=int( sys.argv[ 1 ] ), content="movies" )    
    return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=li, isFolder=isFolder)

# UI builder functions
def show_root_menu():
    ''' Show the plugin root menu. '''
    numresults = (5,10,15,20,25,30,35,40,45,50,60,70,80,90,100)[ int(__settings__.getSetting( "numresults" ) )]   
    
    addDirectoryItem(name=__language__(30301) % numresults, isFolder=True, parameters={PARAMETER_KEY_MODE: MODE_SHOWFEEDS, "orderby":"newest"})
    addDirectoryItem(name=__language__(30302) % numresults, isFolder=True, parameters={PARAMETER_KEY_MODE: MODE_SHOWFEEDS, "orderby":"curpopular"})
    addDirectoryItem(name=__language__(30303) % numresults, isFolder=True, parameters={PARAMETER_KEY_MODE: MODE_SHOWFEEDS, "orderby":"yespopular"})
    addDirectoryItem(name=__language__(30304) % numresults, isFolder=True, parameters={PARAMETER_KEY_MODE: MODE_SHOWFEEDS, "orderby":"allpopular"})
    addDirectoryItem(name=__language__(30305) % numresults, isFolder=True, parameters={PARAMETER_KEY_MODE: MODE_SHOWFEEDS, "orderby":"toprated"})
    
    addDirectoryItem(name=__language__(30306), isFolder=True, parameters={PARAMETER_KEY_MODE: MODE_SHOW_PLATFORMS}, isVideo=False)
    
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)
    
def show_feeds(params):
    ''' Show feeds submenu. '''
    getAndSetCurrentViewmode()
    
    numresults = (5,10,15,20,25,30,35,40,45,50,60,70,80,90,100)[ int(__settings__.getSetting( "numresults" ) )] 
    
    orderby = params.get("orderby")
    if orderby == "newest":
        label = __language__(30301) % numresults
    elif orderby == "curpopular":
        label = __language__(30302) % numresults
    elif orderby == "yespopular":
        label = __language__(30303) % numresults
    elif orderby == "allpopular":
        label = __language__(30304) % numresults
    elif orderby == "toprated":
        label = __language__(30305) % numresults

    addDirectoryItem(name="%s - %s" % (label, __language__(30401)), isFolder=True, parameters={PARAMETER_KEY_MODE: MODE_SHOWFEED, "kind":"", "type":"", "orderby": orderby})    
    addDirectoryItem(name="%s - %s" % (label, __language__(30402)), isFolder=True, parameters={PARAMETER_KEY_MODE: MODE_SHOWFEED, "kind":"xb360", "type":"", "orderby": orderby})
    addDirectoryItem(name="%s - %s" % (label, __language__(30403)), isFolder=True, parameters={PARAMETER_KEY_MODE: MODE_SHOWFEED, "kind":"ds", "type":"", "orderby": orderby})
    addDirectoryItem(name="%s - %s" % (label, __language__(30404)), isFolder=True, parameters={PARAMETER_KEY_MODE: MODE_SHOWFEED, "kind":"gba", "type":"", "orderby": orderby})
    addDirectoryItem(name="%s - %s" % (label, __language__(30405)), isFolder=True, parameters={PARAMETER_KEY_MODE: MODE_SHOWFEED, "kind":"wii", "type":"", "orderby": orderby})
    addDirectoryItem(name="%s - %s" % (label, __language__(30406)), isFolder=True, parameters={PARAMETER_KEY_MODE: MODE_SHOWFEED, "kind":"pc", "type":"", "orderby": orderby})
    addDirectoryItem(name="%s - %s" % (label, __language__(30407)), isFolder=True, parameters={PARAMETER_KEY_MODE: MODE_SHOWFEED, "kind":"ps2", "type":"", "orderby": orderby})
    addDirectoryItem(name="%s - %s" % (label, __language__(30408)), isFolder=True, parameters={PARAMETER_KEY_MODE: MODE_SHOWFEED, "kind":"ps3", "type":"", "orderby": orderby})
    addDirectoryItem(name="%s - %s" % (label, __language__(30409)), isFolder=True, parameters={PARAMETER_KEY_MODE: MODE_SHOWFEED, "kind":"psp", "type":"", "orderby": orderby})    
    
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)
    
    
def show_platforms(params):
    ''' Show platforms submenu. '''
    getAndSetCurrentViewmode()
    
    addDirectoryItem(name=__language__(30401), isFolder=True, parameters={PARAMETER_KEY_MODE: MODE_SHOWTYPE, "kind":""}, isVideo=False)
    addDirectoryItem(name=__language__(30402), isFolder=True, parameters={PARAMETER_KEY_MODE: MODE_SHOWTYPE, "kind":"xb360"}, isVideo=False)
    addDirectoryItem(name=__language__(30403), isFolder=True, parameters={PARAMETER_KEY_MODE: MODE_SHOWTYPE, "kind":"ds"}, isVideo=False)
    addDirectoryItem(name=__language__(30404), isFolder=True, parameters={PARAMETER_KEY_MODE: MODE_SHOWTYPE, "kind":"gba"}, isVideo=False)
    addDirectoryItem(name=__language__(30405), isFolder=True, parameters={PARAMETER_KEY_MODE: MODE_SHOWTYPE, "kind":"wii"}, isVideo=False)
    addDirectoryItem(name=__language__(30406), isFolder=True, parameters={PARAMETER_KEY_MODE: MODE_SHOWTYPE, "kind":"pc"}, isVideo=False)
    addDirectoryItem(name=__language__(30407), isFolder=True, parameters={PARAMETER_KEY_MODE: MODE_SHOWTYPE, "kind":"ps2"}, isVideo=False)
    addDirectoryItem(name=__language__(30408), isFolder=True, parameters={PARAMETER_KEY_MODE: MODE_SHOWTYPE, "kind":"ps3"}, isVideo=False)
    addDirectoryItem(name=__language__(30409), isFolder=True, parameters={PARAMETER_KEY_MODE: MODE_SHOWTYPE, "kind":"psp"}, isVideo=False)
    
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)

def show_types(params):
    ''' Show types submenu. '''
    getAndSetCurrentViewmode()
    
    addDirectoryItem(name=__language__(30501), isFolder=True, parameters={PARAMETER_KEY_MODE: MODE_SHOWORDERBY, "kind":params.get("kind"), "type":""})
    addDirectoryItem(name=__language__(30502), isFolder=True, parameters={PARAMETER_KEY_MODE: MODE_SHOWORDERBY, "kind":params.get("kind"), "type":"review"})
    addDirectoryItem(name=__language__(30503), isFolder=True, parameters={PARAMETER_KEY_MODE: MODE_SHOWORDERBY, "kind":params.get("kind"), "type":"preview"})
    addDirectoryItem(name=__language__(30504), isFolder=True, parameters={PARAMETER_KEY_MODE: MODE_SHOWORDERBY, "kind":params.get("kind"), "type":"interview"})
    addDirectoryItem(name=__language__(30505), isFolder=True, parameters={PARAMETER_KEY_MODE: MODE_SHOWORDERBY, "kind":params.get("kind"), "type":"gameplay"})
    addDirectoryItem(name=__language__(30506), isFolder=True, parameters={PARAMETER_KEY_MODE: MODE_SHOWORDERBY, "kind":params.get("kind"), "type":"feature"})
    
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)

def show_orderby(params):
    ''' Show order by submenu. '''
    getAndSetCurrentViewmode()
    
    addDirectoryItem(name=__language__(30601), isFolder=True, parameters={PARAMETER_KEY_MODE: MODE_SHOWFEED, "kind":params.get("kind"), "type":params.get("type"), "orderby": "newest"})
    addDirectoryItem(name=__language__(30602), isFolder=True, parameters={PARAMETER_KEY_MODE: MODE_SHOWFEED, "kind":params.get("kind"), "type":params.get("type"), "orderby": "curpopular"})
    addDirectoryItem(name=__language__(30603), isFolder=True, parameters={PARAMETER_KEY_MODE: MODE_SHOWFEED, "kind":params.get("kind"), "type":params.get("type"), "orderby": "yespopular"})
    addDirectoryItem(name=__language__(30604), isFolder=True, parameters={PARAMETER_KEY_MODE: MODE_SHOWFEED, "kind":params.get("kind"), "type":params.get("type"), "orderby": "allpopular"})
    addDirectoryItem(name=__language__(30605), isFolder=True, parameters={PARAMETER_KEY_MODE: MODE_SHOWFEED, "kind":params.get("kind"), "type":params.get("type"), "orderby": "toprated"})
    
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)
    
    

    
def show_feed(params):
    ''' make call to http://feeds.gametrailers.com/rssgenerate.php?s1=&vidformat[wmv]=on&quality[hd]=on&orderby=newest&limit=20 '''    
    getAndSetCurrentViewmode()
    
    hd = parseBoolString(__settings__.getSetting( "hd" ))
    sd = parseBoolString(__settings__.getSetting( "sd" )) 
    numresults = (5,10,15,20,25,30,35,40,45,50,60,70,80,90,100)[ int(__settings__.getSetting( "numresults" ) )]
    
    feedurl = "http://feeds.gametrailers.com/rssgenerate.php?s1=&vidformat[flv]=on&limit=" + str( numresults ) 
    
    type = params.get("orderby")
    if type != "":
        feedurl += "&orderby=" + type
    
    if hd and sd:
        feedurl += "&quality[either]=on"
    elif hd and not sd:
        feedurl += "&quality[hd]=on"
    elif sd and not hd:
        feedurl += "&quality[sd]=on"
    
    kind = params.get("kind")
    if kind!="":
        feedurl += "&favplats[" + kind + "]=" + kind
    
    type = params.get("type")
    if type!="":
        feedurl += "&type[" + type + "]=on"
                
    log_notice(feedurl)
    
    '''fsock = urllib.urlopen(feedurl)                        
    xmldoc = minidom.parse(fsock)                     
    fsock.close()   '''
    
    response = urllib2.urlopen(feedurl)
    responsetext = response.read()
    ''' gametrailers has invalid characters in xml doc, fix it by ignoring them '''
    xmldoc = minidom.parseString(responsetext.decode('ascii','ignore') )
    response.close()
    
    for item in xmldoc.getElementsByTagName("item"):
        try:
            guid = item.getElementsByTagName("guid")[0].childNodes.item(0).data
            title = item.getElementsByTagName("title")[0].childNodes.item(0).data
            thumbnail = item.getElementsByTagNameNS("http://www.gametrailers.com/rssexplained.php", "image")[0].childNodes.item(0).data 
            description = item.getElementsByTagName("description")[0].childNodes.item(0).data
            pubDate = item.getElementsByTagName("pubDate")[0].childNodes.item(0).data
            platform = item.getElementsByTagNameNS("http://www.gametrailers.com/rssexplained.php", "platform")[0].childNodes.item(0).data             
            filesize = item.getElementsByTagName("fileSize")[0].childNodes.item(0).data
            
            addDirectoryItem(name=title, isFolder=False, parameters={PARAMETER_KEY_MODE:MODE_PLAYVIDEO, "movieId":guid, "title": title, "thumbnail": thumbnail, "plot": description, "plotoutline" : description, "genre": platform, "size": long(filesize), "feed" : feedurl }, image=thumbnail)
        except:
            pass
    
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)


def playVideo(params):
    ''' get video url based on guid '''    
    getAndSetCurrentViewmode()
    
    get_video_url = "http://www.gametrailers.com/neo/?page=xml.mediaplayer.Mediagen&movieId=" + params.get('movieId') + "&width=960&height=572&prerollOption=&siteNameInAdTags=&ssc=&impressiontype=24&swfserver=media.mtvnservices.com&testmode=&hd=1&um=0"
    
    log_notice("get_video_url="+get_video_url)
    
    fsock = urllib.urlopen(get_video_url)
    xmldoc = minidom.parse(fsock)
    fsock.close()
    
    url = xmldoc.getElementsByTagName("src")[0].childNodes.item(0).data
    
    log_notice("video_url="+url)
        
    listitem=xbmcgui.ListItem(label=params.get('title'), iconImage=params.get('thumbnail'), thumbnailImage=params.get('thumbnail'), path=url);    
    ''' listitem.setInfo(type='Video', infoLabels=labels) '''

    xbmcplugin.setResolvedUrl(handle=int(sys.argv[1]), succeeded=True, listitem=listitem)
    
def playAll(params):
    getAndSetCurrentViewmode()
    
    feedurl = urllib.unquote(params.get('feed'))
    log_notice( "play all = " + feedurl)
    
    player = xbmc.Player()
    player.stop()
    
    playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
    playlist.clear()
    
    response = urllib2.urlopen(feedurl)
    responsetext = response.read()
    xmldoc = minidom.parseString(responsetext.decode('ascii','ignore') )
    response.close()
    
    for item in xmldoc.getElementsByTagName("item"):
        try:
            guid = item.getElementsByTagName("guid")[0].childNodes.item(0).data
            title = item.getElementsByTagName("title")[0].childNodes.item(0).data
            thumbnail = item.getElementsByTagNameNS("http://www.gametrailers.com/rssexplained.php", "image")[0].childNodes.item(0).data 
            description = item.getElementsByTagName("description")[0].childNodes.item(0).data
            pubDate = item.getElementsByTagName("pubDate")[0].childNodes.item(0).data
            platform = item.getElementsByTagNameNS("http://www.gametrailers.com/rssexplained.php", "platform")[0].childNodes.item(0).data             
            filesize = item.getElementsByTagName("fileSize")[0].childNodes.item(0).data
            
            parameters = {PARAMETER_KEY_MODE:MODE_PLAYVIDEO, "movieId":guid, "title": title, "thumbnail": thumbnail, "plot": description, "plotoutline" : description, "genre": platform, "size": long(filesize) }
            
            url = sys.argv[0] + '?' + urllib.urlencode(parameters)
            
            listitem=xbmcgui.ListItem(label=title, iconImage=thumbnail, thumbnailImage=thumbnail)
            listitem.setProperty('IsPlayable', 'true')
            listitem.setProperty( "Video", "true" )  
            listitem.setInfo(type='Video', infoLabels=parameters)
            
            playlist.add(url=url, listitem=listitem)
        except:
            pass
    
    ''' play playlist'''
    xbmc.executebuiltin('playlist.playoffset(video,0)' )
    
    return True    

def parseBoolString(theString):
    return theString[0].upper()=='T'

# Log NOTICE
def log_notice(msg):
    xbmc.output("### [%s] - %s" % (__addonname__,msg,),level=xbmc.LOGNOTICE )

def showMessage(heading, message):
    duration = 10
    xbmc.executebuiltin('XBMC.Notification("%s", "%s", %s)' % ( heading, message, duration) )

def getAndSetCurrentViewmode():
    for id in range( CONTROL_MAIN_LIST_START, CONTROL_MAIN_LIST_END + 1 ):
        try:
            if xbmc.getCondVisibility( "Control.IsVisible(%i)" % id ):
                log_notice("current viewmode=" + str(id))
                xbmc.executebuiltin("Container.SetViewMode(%i)" % id)
                break
        except:
            pass


# parameter values
params = parameters_string_to_dict(sys.argv[2])
mode = int(params.get(PARAMETER_KEY_MODE, "0"))

# Depending on the mode, call the appropriate function to build the UI.
if not sys.argv[2]:
    # new start
    ok = show_root_menu()
elif mode == MODE_SHOW_PLATFORMS:
    ok = show_platforms(params)
elif mode == MODE_SHOWTYPE:
    ok = show_types(params)
elif mode == MODE_SHOWORDERBY:
    ok = show_orderby(params)
elif mode == MODE_SHOWFEEDS:
    ok = show_feeds(params)
elif mode == MODE_SHOWFEED:
    ok = show_feed(params)
elif mode == MODE_PLAYVIDEO:
    ok = playVideo(params)
elif mode == MODE_PLAYALL:
    ok = playAll(params)

