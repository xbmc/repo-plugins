# coding: utf-8
'''
Created on 10 jan 2011

@author: Emuller
'''
import os,sys
import urllib,urllib2,re
import xbmc,xbmcplugin,xbmcgui,xbmcaddon #@UnresolvedImport
from xml.dom import minidom
from traceback import print_exc
''' sys.setdefaultencoding('utf-8') '''

# plugin modes
MODE_SHOW_SEARCH = 10
MODE_SHOWVIDEOS = 20
MODE_PLAYVIDEO = 30
MODE_PLAYALL = 40

# parameter keys
PARAMETER_KEY_MODE = "mode"

# control id's
CONTROL_MAIN_LIST_START  = 50
CONTROL_MAIN_LIST_END    = 59

# plugin handle
handle = int(sys.argv[1])
__addonname__ = "plugin.video.musicvideojukebox"
__settings__ = xbmcaddon.Addon(id='plugin.video.musicvideojukebox')
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
        li.setProperty("IsPlayable", "true")
        li.setProperty( "Video", "true" )  
        li.setInfo(type='Video', infoLabels=parameters)    
        
    
    url = sys.argv[0] + '?' + urllib.urlencode(parameters)
    
    xbmcplugin.setContent( handle=int( sys.argv[ 1 ] ), content="movies" )    
    return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=li, isFolder=isFolder)

# UI builder functions
def show_root_menu():
    ''' Show the plugin root menu. '''
    addDirectoryItem(name=__language__(30201), isFolder=True, parameters={PARAMETER_KEY_MODE: MODE_SHOW_SEARCH}, isVideo=False)
    
    ''' show stored searchqueries '''
    searchqueries = getSearchQueries()
    
    for index, query in enumerate(searchqueries):
        addDirectoryItem(name=query, isFolder=True, parameters={PARAMETER_KEY_MODE:MODE_PLAYALL, "artist":query}, isVideo=False)
            
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)
    
    
def show_search():
    viewmode = getCurrentViewmode()
    q = getKeyboardInput(title=__language__(30201), default="")
    
    artistname = getArtistName(q)
    
    artistxml = getArtistMatches(artistname)
    
    if artistxml.length>0:
        ''' build menu '''
        for artist in artistxml:
            name = artist.getElementsByTagName("name")[0].childNodes.item(0).data
            addDirectoryItem(name=name.encode("utf-8"), isFolder=True, parameters={PARAMETER_KEY_MODE:MODE_PLAYALL, "artist":name.encode("utf-8")}, isVideo=False)
        
        xbmcplugin.endOfDirectory(handle=handle, succeeded=True)     
        xbmc.executebuiltin("Container.SetViewMode(%i)" %  viewmode)   
    else:
        ''' do exact search '''
        xbmc.executebuiltin('XBMC.RunPlugin(%s?%s)' % (sys.argv[0], urllib.urlencode( { "mode" : MODE_PLAYALL, "artist" : artistname} ) ) )        
    
    

def show_videos(params):
    ''' search on youtube for music videos of the current artist '''
    
    url = "http://gdata.youtube.com/feeds/api/videos?max-results=50&v=2&category=Music&format=5&" + urllib.urlencode({ "q" : params.get('artist') })
    
    xmldoc = getXmlResponse(url)
    
    entries = xmldoc.getElementsByTagName("entry")
    
    for entry in entries:
        title = entry.getElementsByTagName("title")[0].childNodes.item(0).data
        thumbnail = entry.getElementsByTagNameNS("http://search.yahoo.com/mrss/", "thumbnail")[0].getAttribute('url')
        videoId = entry.getElementsByTagNameNS("http://gdata.youtube.com/schemas/2007", "videoid")[0].childNodes.item(0).data
        
        addDirectoryItem(name=title.encode("utf-8"), isFolder=False, parameters={PARAMETER_KEY_MODE:MODE_PLAYVIDEO, "title":title.encode("utf-8"), "videoId":videoId.encode("utf-8"), "thumbnail":thumbnail.encode("utf-8")}, image=thumbnail.encode("utf-8"), isVideo=True)
    
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)
    

def playVideo(params):
    ''' get video url based on guid '''    
    
    videoId = params.get("videoId")
    
    ''' call the youtube player '''
    url = "plugin://plugin.video.youtube?path=/root&action=play_video&videoid=%s" % params.get( "videoId")
        
    listitem=xbmcgui.ListItem(label=params.get('title'), iconImage=params.get('thumbnail'), thumbnailImage=params.get('thumbnail'), path=url)
    xbmcplugin.setResolvedUrl(handle=int(sys.argv[1]), succeeded=True, listitem=listitem)
    
        
def playAll(params):
    showMessage(__language__(30302), __language__(30301))
    
    ''' store current search query '''
    artistname = urllib.unquote_plus(params.get("artist"))
    storeSearchQuery( artistname )    
                   
    player = xbmc.Player()
    if player.isPlaying():
        player.stop()
    
    playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
    playlist.clear()
    
    totalresults = addEntriesToPlaylist( playlist=playlist, q=artistname, startindex=1)
    if totalresults>50:
        totalresults = addEntriesToPlaylist( playlist=playlist, q=artistname, startindex=51)
    if totalresults>100:
        totalresults = addEntriesToPlaylist( playlist=playlist, q=artistname, startindex=101)
    elif totalresults<=0:
        showMessage(__language__(30305), __language__(30306) % artistname)
    
    shuffle = parseBoolString(__settings__.getSetting("shuffle"))
    if shuffle:
        playlist.shuffle()
    
    ''' play playlist'''
    xbmc.executebuiltin('playlist.playoffset(video,0)' )
        

def addEntriesToPlaylist( playlist, q, startindex=1):    
    url = "http://gdata.youtube.com/feeds/api/videos?max-results=50&v=2&category=Music&format=5&start-index=%i&%s" % ( startindex, urllib.urlencode({ "q" : q }) )
    
    xmldoc = getXmlResponse(url)
    
    entries = xmldoc.getElementsByTagName("entry")
    
    for entry in entries:
         title = entry.getElementsByTagName("title")[0].childNodes.item(0).data
         thumbnail = entry.getElementsByTagNameNS("http://search.yahoo.com/mrss/", "thumbnail")[0].getAttribute('url')
         videoId = entry.getElementsByTagNameNS("http://gdata.youtube.com/schemas/2007", "videoid")[0].childNodes.item(0).data
         
         description = ""
         if entry.getElementsByTagNameNS("http://search.yahoo.com/mrss/", "description")[0].childNodes.length>0:
             description = entry.getElementsByTagNameNS("http://search.yahoo.com/mrss/", "description")[0].childNodes.item(0).data
         
         author = ""
         if entry.getElementsByTagName("author")[0].getElementsByTagName("name")[0].childNodes.length>0:
             author = entry.getElementsByTagName("author")[0].getElementsByTagName("name")[0].childNodes.item(0).data
         
         parameters = {PARAMETER_KEY_MODE:MODE_PLAYVIDEO, "videoId":videoId.encode("utf-8"), "title": title.encode("utf-8"), "author": author.encode("utf-8"), "plot":description.encode("utf-8"),"thumbnail": thumbnail.encode("utf-8") }
        
         listitem=xbmcgui.ListItem(label=title, iconImage=thumbnail, thumbnailImage=thumbnail)
         listitem.setProperty('IsPlayable', 'true')
         listitem.setProperty( "Video", "true" )  
         listitem.setInfo(type='Video', infoLabels=parameters)
         
         url = sys.argv[0] + '?' + urllib.urlencode(parameters)        
         playlist.add(url=url, listitem=listitem)

    return int(xmldoc.getElementsByTagNameNS("http://a9.com/-/spec/opensearch/1.1/", "totalResults")[0].childNodes.item(0).data)
    

def getArtistName(q):
    ''' search on Google Suggest to get most likely artist name '''
    showMessage(__language__(30303), __language__(30301))
    
    url = "http://suggestqueries.google.com/complete/search?hl=en&ds=yt&output=toolbar&" + urllib.urlencode({ "q" : q })
    
    xmldoc = getXmlResponse(url)
    
    ''' get the first item '''
    suggestions = xmldoc.getElementsByTagName("CompleteSuggestion")
    if suggestions.length>0:
        firstitem = suggestions[0]
        artist = firstitem.getElementsByTagName("suggestion")[0].getAttribute('data')
    else:
        artist = q
    
    return artist

def getArtistMatches(artist):
    ''' search on last.fm for matching artist names '''
    showMessage(__language__(30304), __language__(30301))
    
    url = "http://ws.audioscrobbler.com/2.0/?method=artist.search&api_key=c8a19b7361e56044be8432c023c30888&" + urllib.urlencode({ "artist" : artist })
    
    xmldoc = getXmlResponse(url)
        
    return xmldoc.getElementsByTagName('artist')


def getSearchQueries():
    try:
        searchqueries = eval(__settings__.getSetting("searchqueries"))
    except:
        searchqueries = []
        
    return searchqueries

def storeSearchQuery(query):
    searchqueries = getSearchQueries()
    
    ''' if query already in list abort this function '''
    for index, storedquery in enumerate(searchqueries):
        if query.lower() == storedquery.lower():
            return False
        
    maxsearches = (10, 20, 40, 60, 80, 100)[ int(__settings__.getSetting("maxsearches")) ]
    
    searchqueries = [query] + searchqueries[:maxsearches-1]
    searchqueries.sort(myComp)
    __settings__.setSetting("searchqueries", repr(searchqueries))
    return True

def myComp (a,b):    
    if (a.lower() > b.lower()):
        return 1
    else:
        return -1
    

def parseBoolString(theString):
    return theString[0].upper()=='T'

# Log NOTICE
def log_notice(msg):
    xbmc.output("### [%s] - %s" % (__addonname__,msg,),level=xbmc.LOGNOTICE )

def showMessage(heading, message, duration=10):
    xbmc.executebuiltin('XBMC.Notification("%s", "%s", %s)' % ( heading, message, duration) )

def getCurrentViewmode():
    for id in range( CONTROL_MAIN_LIST_START, CONTROL_MAIN_LIST_END + 1 ):
        try:
            if xbmc.getCondVisibility( "Control.IsVisible(%i)" % id ):
                break
        except:
            print_exc()
    return id

def getKeyboardInput(title = "Input", default="", hidden=False):
    result = None
        
    kbd = xbmc.Keyboard(default, title)
    kbd.setHiddenInput(hidden)
    kbd.doModal()
    
    if kbd.isConfirmed():
        result = kbd.getText()
    
    return result

def getJsonResponse(url):
    
    response = urllib2.urlopen(url)
    responsetext = response.read()
    objs = xbmc.executeJSONRPC(responsetext)
    response.close()
    
    return objs

def getXmlResponse(url):
    log_notice("getXmlResponse from " + url)
    response = urllib2.urlopen(url)
    encoding = re.findall("charset=([a-zA-Z0-9\-]+)", response.headers['content-type'])
    responsetext = unicode( response.read(), encoding[0] );
    xmldoc = minidom.parseString(responsetext.encode("utf-8"))
    response.close()
    return xmldoc

def getHttpResponse(url):
    log_notice("getHttpResponse from " + url)
    response = urllib2.urlopen(url)
    encoding = re.findall("charset=([a-zA-Z0-9\-]+)", response.headers['content-type'])
    responsetext = unicode( response.read(), encoding[0] );
    response.close()
    return responsetext.encode("utf-8")

# parameter values
params = parameters_string_to_dict(sys.argv[2])
mode = int(params.get(PARAMETER_KEY_MODE, "0"))

# Depending on the mode, call the appropriate function to build the UI.
if not sys.argv[2]:
    # new start
    ok = show_root_menu()
elif mode == MODE_SHOW_SEARCH:
    ok = show_search()
elif mode == MODE_SHOWVIDEOS:
    ok = show_videos(params)
elif mode == MODE_PLAYVIDEO:
    ok = playVideo(params)
elif mode == MODE_PLAYALL:
    ok = playAll(params)