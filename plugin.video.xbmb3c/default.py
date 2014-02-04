'''
    @document   : default.py
    @package    : XBMB3C add-on
    @authors    : xnappo, null_pointer, im85288
    @copyleft   : 2013, xnappo
    @version    : 0.8.0 (frodo)

    @license    : Gnu General Public License - see LICENSE.TXT
    @description: XBMB3C XBMC add-on

    This file is part of the XBMC XBMB3C Plugin.

    XBMB3C Plugin is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 2 of the License, or
    (at your option) any later version.

    XBMB3C Plugin is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with XBMB3C Plugin.  If not, see <http://www.gnu.org/licenses/>.
    
    Thanks to Hippojay for the PleXBMC plugin this is derived from

'''

import urllib
import glob
import re
import hashlib
import xbmcplugin
import xbmcgui
import xbmcaddon
import httplib
import socket
import sys
import os
import time
import inspect
import base64
import random
import datetime
import requests
from urlparse import urlparse
import cProfile
import pstats
import threading
import hashlib
import StringIO
import gzip

__settings__ = xbmcaddon.Addon(id='plugin.video.xbmb3c')
__cwd__ = __settings__.getAddonInfo('path')
__addon__       = xbmcaddon.Addon(id='plugin.video.xbmb3c')
__addondir__    = xbmc.translatePath( __addon__.getAddonInfo('profile') ) 
__language__     = __addon__.getLocalizedString

BASE_RESOURCE_PATH = xbmc.translatePath( os.path.join( __cwd__, 'resources', 'lib' ) )
PLUGINPATH=xbmc.translatePath( os.path.join( __cwd__) )

sys.path.append(BASE_RESOURCE_PATH)
XBMB3C_VERSION="0.8.0"

xbmc.log ("===== XBMB3C START =====")

xbmc.log ("XBMB3C -> running Python: " + str(sys.version_info))
xbmc.log ("XBMB3C -> running XBMB3C: " + str(XBMB3C_VERSION))
xbmc.log (xbmc.getInfoLabel( "System.BuildVersion" ))

#Get the setting from the appropriate file.
DEFAULT_PORT="32400"
_MODE_GETCONTENT=0
_MODE_MOVIES=0
_MODE_BASICPLAY=12

#Check debug first...
g_debug = __settings__.getSetting('debug')
if (__settings__.getSetting('useJson')=='true'):
    import json as json
else:
    import simplejson as json
    
def printDebug( msg, functionname=True ):
    if g_debug == "true":
        if functionname is False:
            xbmc.log (str(msg))
        else:
            print "XBMB3C -> " + inspect.stack()[1][3] + ": " + str(msg)

def getPlatform( ):

    if xbmc.getCondVisibility('system.platform.osx'):
        return "OSX"
    elif xbmc.getCondVisibility('system.platform.atv2'):
        return "ATV2"
    elif xbmc.getCondVisibility('system.platform.ios'):
        return "iOS"
    elif xbmc.getCondVisibility('system.platform.windows'):
        return "Windows"
    elif xbmc.getCondVisibility('system.platform.linux'):
        return "Linux/RPi"
    elif xbmc.getCondVisibility('system.platform.android'): 
        return "Linux/Android"

    return "Unknown"

XBMB3C_PLATFORM=getPlatform()
xbmc.log ("XBMB3C -> Platform: " + str(XBMB3C_PLATFORM))

g_flatten = __settings__.getSetting('flatten')
printDebug("XBMB3C -> Flatten is: "+ g_flatten, False)

if g_debug == "true":
    xbmc.log ("XBMB3C -> Setting debug to " + g_debug)
else:
    xbmc.log ("XBMB3C -> Debug is turned off.  Running silent")

g_contextReplace=True

g_loc = "special://home/addons/plugin.video.XBMB3C"

#Create the standard header structure and load with a User Agent to ensure we get back a response.
g_txheaders = {
              'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US;rv:1.9.2.3) Gecko/20100401 Firefox/3.6.3 ( .NET CLR 3.5.30729)',
              }

#Set up holding variable for session ID
global g_sessionID
g_sessionID=None

genreList=[__language__(30069),__language__(30070),__language__(30071),__language__(30072),__language__(30073),__language__(30074),__language__(30075),__language__(30076),__language__(30077),__language__(30078),__language__(30079),__language__(30080),__language__(30081),__language__(30082),__language__(30083),__language__(30084),__language__(30085),__language__(30086),__language__(30087),__language__(30088),__language__(30089)]
sortbyList=[__language__(30060),__language__(30061),__language__(30062),__language__(30063),__language__(30064),__language__(30065),__language__(30066),__language__(30067)]

def discoverAllServers( ):
    '''
        Take the users settings and add the required master servers
        to the server list.  These are the devices which will be queried
        for complete library listings.  There are 3 types:
            local server - from IP configuration
            bonjour server - from a bonjour lookup
        Alters the global g_serverDict value
        @input: None
        @return: None
    '''
    printDebug("== ENTER: discoverAllServers ==", False)
    
    das_servers={}
    das_server_index=0
    
    das_host = __settings__.getSetting('ipaddress')
    das_port =__settings__.getSetting('port')

    if not das_host or das_host == "<none>":
        das_host=None
    elif not das_port:
        printDebug( "XBMB3C -> No port defined.  Using default of " + DEFAULT_PORT, False)
        das_port=DEFAULT_PORT
       
    printDebug( "XBMB3C -> Settings hostname and port: %s : %s" % ( das_host, das_port), False)

    if das_host is not None:
        local_server = getLocalServers(das_host, das_port)
        if local_server:
            das_servers[das_server_index] = local_server
            das_server_index = das_server_index + 1

    return das_servers
    
def getUserId( ip_address, port ):

    jsonData = getURL(ip_address+":"+port+"/mediabrowser/Users?format=json")
    
    if(jsonData == False):
        return ""
        
    userid=""
    userName = __settings__.getSetting('username')
    printDebug("Looking for user name: " + userName)
    printDebug("jsonData : " + str(jsonData))
    result = json.loads(jsonData)
    
    for user in result:
        if(user.get("Name") == userName):
            userid = user.get("Id")

    if __settings__.getSetting('password') != "":
        authenticate('http://'+ip_address+":"+port+"/mediabrowser/Users/AuthenticateByName")
        
    if userid=='':
        return_value = xbmcgui.Dialog().ok(__language__(30045),__language__(30045))
        sys.exit()
        
    printDebug("userid : " + userid)
    
    WINDOW = xbmcgui.Window( 10000 )
    WINDOW.setProperty("userid", userid)
    
    return userid
    
def getLocalServers( ip_address, port ):
    '''
        Connect to the defined local server (either direct or via bonjour discovery)
        and get a list of all known servers.
        @input: nothing
        @return: a list of servers (as Dict)
    '''
    printDebug("== ENTER: getLocalServers ==", False)
    url_path="/mediabrowser/Users/" + getUserId( ip_address, port) + "/items?format=json"
    jsonData = getURL(ip_address + ":" + port + url_path)

    if jsonData is False:
         return []
         
    result = json.loads(jsonData)

    return {'serverName': result.get('friendlyName','Unknown').encode('utf-8') ,
                        'server'    : ip_address,
                        'port'      : port ,
                        'discovery' : 'local' ,
                        'token'     : None ,
                        'uuid'      : result.get('machineIdentifier') ,
                        'owned'     : '1' ,
                        'master'    : 1 }

def getServerSections( ip_address, port, name, uuid):
    printDebug("== ENTER: getServerSections ==", False)
    userid=str(getUserId( ip_address, port))
    jsonData = getURL(ip_address+":"+port+"/mediabrowser/Users/"+userid+"/Items/Root?format=json")
    printDebug("jsonData : " + jsonData)
    result = json.loads(jsonData)
    
    parentid = result.get("Id")
    printDebug("parentid : " + parentid)
       
    htmlpath = ("http://%s:%s/mediabrowser/Users/" % ( ip_address, port))
    jsonData = getURL(htmlpath + userid + "/items?ParentId=" + parentid + "&format=json")
    printDebug("jsonData : " + jsonData)
    temp_list=[]

    if jsonData is False:
        return {}

    result = json.loads(jsonData)
    result = result.get("Items")
    
    detailsString = "Path,Genres,Studios,CumulativeRunTimeTicks"
    
    if(__settings__.getSetting('includeStreamInfo') == "true"):
        detailsString += ",MediaStreams"
    
    if(__settings__.getSetting('includePeople') == "true"):
        detailsString += ",People"
        
    if(__settings__.getSetting('includeOverview') == "true"):
        detailsString += ",Overview"        
    
    for item in result:
        if(item.get("RecursiveItemCount") != "0"):
            Name =(item.get("Name")).encode('utf-8')
            if __settings__.getSetting(urllib.quote('sortbyfor'+Name)) == '':
                __settings__.setSetting(urllib.quote('sortbyfor'+Name),'SortName')
                __settings__.setSetting(urllib.quote('sortorderfor'+Name),'Ascending')
            
            total = str(item.get("RecursiveItemCount"))
            section = item.get("CollectionType")
            if (section == None):
              section = "movies"
            temp_list.append( {'title'      : Name,
                    'address'    : ip_address+":"+port ,
                    'serverName' : name ,
                    'uuid'       : uuid ,
                    'path'       : ('/mediabrowser/Users/' + userid + '/items?ParentId=' + item.get("Id") + '&IsVirtualUnaired=false&IsMissing=False&Fields=' + detailsString + '&SortOrder='+__settings__.getSetting('sortorderfor'+urllib.quote(Name))+'&SortBy='+__settings__.getSetting('sortbyfor'+urllib.quote(Name))+'&Genres=&format=json') ,
                    'token'      : item.get("Id")  ,
                    'location'   : "local" ,
                    'art'        : item.get("?") ,
                    'local'      : '1' ,
                    'type'       : "movie",
                    'section'    : section,
                    'total'      : total,
                    'owned'      : '1' })
            printDebug("Title " + Name)    
    
    # Add recent movies
    temp_list.append( {'title'      : 'Recently Added Movies',
            'address'    : ip_address+":"+port ,
            'serverName' : name ,
            'uuid'       : uuid ,
            'path'       : ('/mediabrowser/Users/' + userid + '/Items?Limit=' + __settings__.getSetting("numRecentMovies") +'&Recursive=true&SortBy=DateCreated&Fields=' + detailsString + '&SortOrder=Descending&Filters=IsUnplayed,IsNotFolder&IncludeItemTypes=Movie&format=json') ,
            'token'      : ''  ,
            'location'   : "local" ,
            'art'        : '' ,
            'local'      : '1' ,
            'type'       : "movie",
            'section'    : "movies",
            'owned'      : '1' })
            
    # Add recent Episodes
    temp_list.append( {'title'      : 'Recently Added Episodes',
            'address'    : ip_address+":"+port ,
            'serverName' : name ,
            'uuid'       : uuid ,
            'path'       : ('/mediabrowser/Users/' + userid + '/Items?Limit=' + __settings__.getSetting("numRecentTV") +'&Recursive=true&SortBy=DateCreated&Fields=' + detailsString + '&SortOrder=Descending&Filters=IsUnplayed,IsNotFolder&IsVirtualUnaired=false&IsMissing=False&IncludeItemTypes=Episode&format=json') ,
            'token'      : ''  ,
            'location'   : "local" ,
            'art'        : '' ,
            'local'      : '1' ,
            'type'       : "movie",
            'section'    : "tvshows",
            'owned'      : '1' })    
            
    # Add NextUp Episodes
    temp_list.append( {'title'      : 'Next Episodes',
            'address'    : ip_address+":"+port ,
            'serverName' : name ,
            'uuid'       : uuid ,
            'path'       : ('/mediabrowser/Shows/NextUp/?Userid=' + userid + '&Recursive=true&SortBy=DateCreated&Fields=' + detailsString + '&SortOrder=Descending&Filters=IsUnplayed,IsNotFolder&IsVirtualUnaired=false&IsMissing=False&IncludeItemTypes=Episode&format=json') ,
            'token'      : ''  ,
            'location'   : "local" ,
            'art'        : '' ,
            'local'      : '1' ,
            'type'       : "movie",
            'section'    : "tvshows",
            'owned'      : '1' })            
    # Add Favorite Movies
    temp_list.append( {'title'      : 'Favorite Movies',
            'address'    : ip_address+":"+port ,
            'serverName' : name ,
            'uuid'       : uuid ,
            'path'       : ('/mediabrowser/Users/' + userid + '/Items?Recursive=true&SortBy=sortName&Fields=' + detailsString + '&SortOrder=Descending&Filters=IsFavorite,IsNotFolder&IncludeItemTypes=Movie&format=json') ,
            'token'      : ''  ,
            'location'   : "local" ,
            'art'        : '' ,
            'local'      : '1' ,
            'type'       : "movie",
            'section'    : "movies",
            'owned'      : '1' })            

    # Add Favorite Episodes
    temp_list.append( {'title'      : 'Favorite Episodes',
            'address'    : ip_address+":"+port ,
            'serverName' : name ,
            'uuid'       : uuid ,
            'path'       : ('/mediabrowser/Users/' + userid + '/Items?Limit=' + __settings__.getSetting("numRecentTV") +'&Recursive=true&SortBy=DateCreated&Fields=' + detailsString + '&SortOrder=Descending&Filters=IsNotFolder,IsFavorite&IncludeItemTypes=Episode&format=json') ,
            'token'      : ''  ,
            'location'   : "local" ,
            'art'        : '' ,
            'local'      : '1' ,
            'type'       : "movie",
            'section'    : "tvshows",
            'owned'      : '1' })                       
            
    # Add Upcoming TV
    temp_list.append( {'title'      : 'Upcoming TV',
            'address'    : ip_address+":"+port ,
            'serverName' : name ,
            'uuid'       : uuid ,
            'path'       : ('/mediabrowser/Users/' + userid + '/Items?Recursive=true&SortBy=PremiereDate&Fields=' + detailsString + '&SortOrder=Ascending&Filters=IsUnplayed&IsVirtualUnaired=true&IsNotFolder&IncludeItemTypes=Episode&format=json') ,
            'token'      : ''  ,
            'location'   : "local" ,
            'art'        : '' ,
            'local'      : '1' ,
            'type'       : "movie",
            'section'    : "tvshows",
            'owned'      : '1' })                            

    # Add BoxSets
    temp_list.append( {'title'      : 'BoxSets',
            'address'    : ip_address+":"+port ,
            'serverName' : name ,
            'uuid'       : uuid ,
            'path'       : ('/mediabrowser/Users/' + userid + '/Items?Recursive=true&SortBy=PremiereDate&Fields=' + detailsString + '&SortOrder=Ascending&IncludeItemTypes=BoxSet&format=json') ,
            'token'      : ''  ,
            'location'   : "local" ,
            'art'        : '' ,
            'local'      : '1' ,
            'type'       : "movie",
            'section'    : "movies",
            'owned'      : '1' })                            
            
    for item in temp_list:
        printDebug ("temp_list: " + str(item))
    return temp_list

def getAllSections( server_list = None ):
    '''
        from server_list, get a list of all the available sections
        and deduplicate the sections list
        @input: None
        @return: None (alters the global value g_sectionList)
    '''
    printDebug("== ENTER: getAllSections ==", False)
    
    if not server_list:
        server_list = discoverAllServers()
    
    printDebug("Using servers list: " + str(server_list))

    section_list=[]
    local_complete=False
    
    for server in server_list.itervalues():

        if server['discovery'] == "local" or server['discovery'] == "auto":
            section_details =  getServerSections( server['server'], server['port'] , server['serverName'], server['uuid']) 
            section_list += section_details
            printDebug ("Sectionlist:" + str(section_list))
            local_complete=True
            
    return section_list

def authenticate (url):
    headers={'Content-Type': 'application/json'}
    sha1=hashlib.sha1(__settings__.getSetting('password'))
    resp = requests.post(url, '{\"password\":\"' +sha1.hexdigest() + '\",\"Username\":\"' + __settings__.getSetting('username') + "\"}", headers=headers)
    code=str(resp).split('[')[1]
    code=code.split(']')[0]
    if int(code) >= 200 and int(code)<300:
        printDebug ("User Authenticated")
    else:
        return_value = xbmcgui.Dialog().ok(__language__(30044),__language__(30044))
        sys.exit()

def markWatched (url):
    headers={'Accept-encoding': 'gzip','Authorization' : 'MediaBrowser', 'Client' : 'Dashboard', 'Device' : "Chrome 31.0.1650.57", 'DeviceId' : "f50543a4c8e58e4b4fbb2a2bcee3b50535e1915e", 'Version':"3.0.5070.20258", 'UserId':"ff"}
    resp = requests.post(url, data='', headers=headers)
    WINDOW = xbmcgui.Window( 10000 )
    WINDOW.setProperty("force_data_reload", "true")  
    xbmc.executebuiltin("Container.Refresh")

def markUnwatched (url):
    headers={'Accept-encoding': 'gzip','Authorization' : 'MediaBrowser', 'Client' : 'Dashboard', 'Device' : "Chrome 31.0.1650.57", 'DeviceId' : "f50543a4c8e58e4b4fbb2a2bcee3b50535e1915e", 'Version':"3.0.5070.20258", 'UserId':"ff"}
    resp = requests.delete(url, data='', headers=headers)
    WINDOW = xbmcgui.Window( 10000 )
    WINDOW.setProperty("force_data_reload", "true")      
    xbmc.executebuiltin("Container.Refresh")

def markFavorite (url):
    headers={'Accept-encoding': 'gzip','Authorization' : 'MediaBrowser', 'Client' : 'Dashboard', 'Device' : "Chrome 31.0.1650.57", 'DeviceId' : "f50543a4c8e58e4b4fbb2a2bcee3b50535e1915e", 'Version':"3.0.5070.20258", 'UserId':"ff"}
    resp = requests.post(url, data='', headers=headers)
    WINDOW = xbmcgui.Window( 10000 )
    WINDOW.setProperty("force_data_reload", "true")    
    xbmc.executebuiltin("Container.Refresh")
    
def unmarkFavorite (url):
    headers={'Accept-encoding': 'gzip','Authorization' : 'MediaBrowser', 'Client' : 'Dashboard', 'Device' : "Chrome 31.0.1650.57", 'DeviceId' : "f50543a4c8e58e4b4fbb2a2bcee3b50535e1915e", 'Version':"3.0.5070.20258", 'UserId':"ff"}
    resp = requests.delete(url, data='', headers=headers)
    WINDOW = xbmcgui.Window( 10000 )
    WINDOW.setProperty("force_data_reload", "true")    
    xbmc.executebuiltin("Container.Refresh")

def sortby ():
    sortOptions=["SortName","ProductionYear","PremiereDate","DateCreated","CriticRating","CommunityRating","PlayCount","Budget"]
    sortOptionsText=sortbyList
    return_value=xbmcgui.Dialog().select(__language__(30068),sortOptionsText)
    WINDOW = xbmcgui.Window( 10000 )
    __settings__.setSetting('sortbyfor'+urllib.quote(WINDOW.getProperty("heading")),sortOptions[return_value]+',SortName')
    newurl=re.sub("SortBy.*?&","SortBy="+ sortOptions[return_value] + ",SortName&",WINDOW.getProperty("currenturl"))
    WINDOW.setProperty("currenturl",newurl)
    u=urllib.quote(newurl)+'&mode=0'
    xbmc.executebuiltin("Container.Update(plugin://plugin.video.xbmb3c/?url="+u+",\"replace\")")#, WINDOW.getProperty('currenturl')

def genrefilter ():
    genreFilters=["","Action","Adventure","Animation","Crime","Comedy","Documentary","Drama","Fantasy","Foreign","History","Horror","Music","Musical","Mystery","Romance","Science%20Fiction","Short","Suspense","Thriller","Western"]
    genreFiltersText=genreList#["None","Action","Adventure","Animation","Crime","Comedy","Documentary","Drama","Fantasy","Foreign","History","Horror","Music","Musical","Mystery","Romance","Science Fiction","Short","Suspense","Thriller","Western"]
    return_value=xbmcgui.Dialog().select(__language__(30090),genreFiltersText)
    newurl=re.sub("Genres.*?&","Genres="+ genreFilters[return_value] + "&",WINDOW.getProperty("currenturl"))
    WINDOW.setProperty("currenturl",newurl)
    u=urllib.quote(newurl)+'&mode=0'
    xbmc.executebuiltin("Container.Update(plugin://plugin.video.xbmb3c/?url="+u+",\"replace\")")#, WINDOW.getProperty('currenturl')

def playall (startId):
    temp_list = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
    temp_list.clear()
    jsonData = getURL(WINDOW.getProperty("currenturl"))
    result = json.loads(jsonData)
    result = result.get("Items")
    found=0
    for item in result:
        if str(item.get('Id'))==startId:
            found=1
        if found==1:
            if(item.get('RecursiveItemCount')!=0):
                u=item.get('Path')
                if __settings__.getSetting('smbusername')=='':
                    u=u.replace("\\\\","smb://")
                else:
                    u=u.replace("\\\\","smb://"+__settings__.getSetting('smbusername')+':'+__settings__.getSetting('smbpassword')+'@')
                u=u.replace("\\","/")
                temp_list.add(u)
    xbmc.Player().play(temp_list)
    #Set a loop to wait for positive confirmation of playback
    count = 0
    while not xbmc.Player().isPlaying():
        printDebug( "Not playing yet...sleep for 2")
        count = count + 2
        if count >= 20:
            return
        else:
            time.sleep(2)

def sortorder ():
    WINDOW = xbmcgui.Window( 10000 )
    if(__settings__.getSetting('sortorderfor'+urllib.quote(WINDOW.getProperty("heading")))=="Ascending"):
        __settings__.setSetting('sortorderfor'+urllib.quote(WINDOW.getProperty("heading")),'Descending')
        newurl=re.sub("SortOrder.*?&","SortOrder=Descending&",WINDOW.getProperty("currenturl"))
    else:
        __settings__.setSetting('sortorderfor'+urllib.quote(WINDOW.getProperty("heading")),'Ascending')
        newurl=re.sub("SortOrder.*?&","SortOrder=Ascending&",WINDOW.getProperty("currenturl"))
    WINDOW.setProperty("currenturl",newurl)
    u=urllib.quote(newurl)+'&mode=0'
    xbmc.executebuiltin("Container.Update(plugin://plugin.video.xbmb3c/?url="+u+",\"replace\")")#, WINDOW.getProperty('currenturl')

    
def delete (url):
    return_value = xbmcgui.Dialog().yesno(__language__(30091),__language__(30092))
    if return_value:
        printDebug('Deleting via URL: ' + url)
        progress = xbmcgui.DialogProgress()
        progress.create(__language__(30052), __language__(30053))
        headers={'Accept-encoding': 'gzip','Authorization' : 'MediaBrowser', 'Client' : 'Dashboard', 'Device' : "Chrome 31.0.1650.57", 'DeviceId' : "f50543a4c8e58e4b4fbb2a2bcee3b50535e1915e", 'Version':"3.0.5070.20258", 'UserId':"ff"}
        resp = requests.delete(url, data='', headers=headers)
        deleteSleep=0
        while deleteSleep<10:
            xbmc.sleep(1000)
            deleteSleep=deleteSleep+1
            progress.update(deleteSleep*10,__language__(30053))
        progress.close()
        xbmc.executebuiltin("Container.Refresh")
                
def getURL( url, suppress=False, type="GET", popup=0 ):
    printDebug("== ENTER: getURL ==", False)
    try:
        if url[0:4] == "http":
            serversplit=2
            urlsplit=3
        else:
            serversplit=0
            urlsplit=1

        server=url.split('/')[serversplit]
        urlPath="/"+"/".join(url.split('/')[urlsplit:])

        printDebug("url = "+url)
        printDebug("server = "+str(server))
        printDebug("urlPath = "+str(urlPath))
        conn = httplib.HTTPConnection(server, timeout=20)
        #head = {"Accept-Encoding" : "gzip,deflate", "Accept-Charset" : "UTF-8,*"} 
        head = {"Accept-Encoding" : "gzip", "Accept-Charset" : "UTF-8,*"} 
        conn.request(method=type, url=urlPath, headers=head)
        #conn.request(method=type, url=urlPath)
        data = conn.getresponse()
        printDebug("GET URL HEADERS : " + str(data.getheaders()))
        link = ""
        contentType = "none"
        if int(data.status) == 200:
            retData = data.read()
            contentType = data.getheader('content-encoding')
            printDebug("Data Len Before : " + str(len(retData)))
            if(contentType == "gzip"):
                retData = StringIO.StringIO(retData)
                gzipper = gzip.GzipFile(fileobj=retData)
                link = gzipper.read()
            else:
                link = retData
                
            printDebug("Data Len After : " + str(len(link)))
            printDebug("====== 200 returned =======")
            printDebug("Content-Type : " + str(contentType), False)
            printDebug(link, False)
            printDebug("====== 200 finished ======")

        elif ( int(data.status) == 301 ) or ( int(data.status) == 302 ):
            try: conn.close()
            except: pass
            return data.getheader('Location')

        elif int(data.status) >= 400:
            error = "HTTP response error: " + str(data.status) + " " + str(data.reason)
            xbmc.log (error)
            if suppress is False:
                if popup == 0:
                    xbmc.executebuiltin("XBMC.Notification(URL error: "+ str(data.reason) +",)")
                else:
                    xbmcgui.Dialog().ok("Error",server)
            xbmc.log (error)
            try: conn.close()
            except: pass
            return ""
        else:
            link = ""
    except Exception, msg:
        error = "Unable to connect to " + str(server) + " : " + str(msg)
        xbmc.log (error)
        xbmc.executebuiltin("XBMC.Notification(\"XBMB3C\": URL error: Unable to connect to server,)")
        xbmcgui.Dialog().ok("","Unable to connect to host")
        #if suppress is False:
        #    if popup == 0:
        #        xbmc.executebuiltin("XBMC.Notification(\"XBMB3C\": URL error: Unable to connect to server,)")
        #    else:
        #        xbmcgui.Dialog().ok("","Unable to connect to host")
        raise
    else:
        try: conn.close()
        except: pass

    return link

def addGUIItem( url, details, extraData, folder=True ):
        printDebug("== ENTER: addGUIItem ==", False)
        printDebug("Adding Dir for [%s]" % details.get('title','Unknown'))
        printDebug("Passed details: " + str(details))
        printDebug("Passed extraData: " + str(extraData))
        #printDebug("urladdgui:" + str(url))
        if details.get('title','') == '':
            return

        if extraData.get('mode',None) is None:
            mode="&mode=0"
        else:
            mode="&mode=%s" % extraData['mode']

        #Create the URL to pass to the item
        if 'mediabrowser/Videos' in url:
            u=sys.argv[0]+"?url=" + url + '&mode=' + str(_MODE_BASICPLAY)
        elif url.startswith('http') or url.startswith('file'):
            u=sys.argv[0]+"?url="+urllib.quote(url)+mode
        else:
            u=sys.argv[0]+"?url=" + url + '&mode=' + str(_MODE_BASICPLAY)
            u=u.replace("\\\\","smb://")
            u=u.replace("\\","/")
        
        #Create the ListItem that will be displayed
        thumb=str(extraData.get('thumb',''))
        if thumb.startswith('http'):
            if '?' in thumb:
                thumbPath=thumb
            else:
                thumbPath=thumb.encode('utf-8') 
        else:
            thumbPath=thumb
        
        addCounts = __settings__.getSetting('addCounts') == 'true'
        
        WINDOW = xbmcgui.Window( 10000 )
        if WINDOW.getProperty("addshowname") == "true":
            if extraData.get('locationtype')== "Virtual":
                listItemName = extraData.get('premieredate').decode("utf-8") + u" - " + details.get('SeriesName','').decode("utf-8") + u" - " + u"S" + details.get('season').decode("utf-8") + u"E" + details.get('title','Unknown').decode("utf-8")
                if(addCounts and extraData.get("RecursiveItemCount") != None and extraData.get("RecursiveItemCount") != None):
                    listItemName = listItemName + " (" + str(extraData.get("RecursiveItemCount") - extraData.get("RecursiveUnplayedItemCount")) + "/" + str(extraData.get("RecursiveItemCount")) + ")"
                list=xbmcgui.ListItem(listItemName, iconImage=thumbPath, thumbnailImage=thumbPath)
            else:
                if details.get('season') == None:
                    season = '0'
                else:
                    season = details.get('season')
                listItemName = details.get('SeriesName','').decode("utf-8") + u" - " + u"S" + season + u"E" + details.get('title','Unknown').decode("utf-8")
                if(addCounts and extraData.get("RecursiveItemCount") != None and extraData.get("RecursiveItemCount") != None):
                    listItemName = listItemName + " (" + str(extraData.get("RecursiveItemCount") - extraData.get("RecursiveUnplayedItemCount")) + "/" + str(extraData.get("RecursiveItemCount")) + ")"
                list=xbmcgui.ListItem(listItemName, iconImage=thumbPath, thumbnailImage=thumbPath)
        else:
            listItemName = details.get('title','Unknown').decode("utf-8")
            if(addCounts and extraData.get("RecursiveItemCount") != None and extraData.get("RecursiveItemCount") != None):
                listItemName = listItemName + " (" + str(extraData.get("RecursiveItemCount") - extraData.get("RecursiveUnplayedItemCount")) + "/" + str(extraData.get("RecursiveItemCount")) + ")"
            list = xbmcgui.ListItem(listItemName, iconImage=thumbPath, thumbnailImage=thumbPath)
        printDebug("Setting thumbnail as " + thumbPath)
        #Set the properties of the item, such as summary, name, season, etc
        list.setInfo( type=extraData.get('type','Video'), infoLabels=details )

        #For all end items    
        if ( not folder):
            #list.setProperty('IsPlayable', 'true')

            if extraData.get('type','video').lower() == "video":
                list.setProperty('TotalTime', str(extraData.get('duration')))
                list.setProperty('ResumeTime', str(extraData.get('resume')))
            

                

        #Set the poster image if it has been enabled
        poster=str(extraData.get('poster',''))
        if '?' in poster:
            setArt(list,'poster', poster)
        else:
            setArt(list,'poster', poster)
        printDebug( "Setting poster as " + poster )

        #Set the fanart image if it has been enabled
        fanart=str(extraData.get('fanart_image',''))
        if '?' in fanart:
            list.setProperty('fanart_image', fanart)
        else:
            list.setProperty('fanart_image', fanart)

        printDebug( "Setting fan art as " + fanart )
        

        #Set the logo image if it has been enabled
        logo=str(extraData.get('logo',''))
        logoPath=logo.encode('utf-8')
        if '?' in logo:
            setArt(list,'clearlogo',logo)
        else:
            setArt(list,'clearlogo','logoPath')

        printDebug( "Setting logo as " + logoPath )
        
         #Set the disc image if it has been enabled
        disc=str(extraData.get('disc',''))
        discPath=disc.encode('utf-8')
        if '?' in disc:
            setArt(list,'discart',disc)
        else:
            setArt(list,'discart','discPath')

        printDebug( "Setting disc as " + discPath )
        
         #Set the banner image if it has been enabled
        banner=str(extraData.get('banner',''))
        bannerPath=banner.encode('utf-8')
        if '?' in banner:
            setArt(list,'banner',banner)
        else:
            setArt(list,'banner','bannerPath')

        printDebug( "Setting banner as " + bannerPath )
        
         #Set the clearart image if it has been enabled
        art=str(extraData.get('clearart',''))
        artPath=art.encode('utf-8')
        if '?' in art:
            setArt(list,'clearart',art)
        else:
            setArt(list,'clearart','artPath')

        printDebug( "Setting clearart as " + artPath )
        
         #Set the landscape image if it has been enabled
        landscape=str(extraData.get('landscape',''))
        landscapePath=landscape.encode('utf-8')
        if '?' in landscape:
            setArt(list,'landscape',landscape)
        else:
            setArt(list,'landscape','landscapePath')

        printDebug( "Setting landscape as " + landscapePath )
        #if extraData.get('banner'):
        #    list.setProperty('banner', extraData.get('banner'))
        #    printDebug( "Setting banner as " + extraData.get('banner'))

        printDebug("Building Context Menus")
        commands = []
        watched = extraData.get('watchedurl')
        if watched != None:
            scriptToRun = PLUGINPATH + "/default.py"
            if extraData.get("playcount") == "0":
                argsToPass = 'markWatched,' + extraData.get('watchedurl')
                commands.append(( __language__(30093), "XBMC.RunScript(" + scriptToRun + ", " + argsToPass + ")", ))
            else:
                argsToPass = 'markUnwatched,' + extraData.get('watchedurl')
                commands.append(( __language__(30094), "XBMC.RunScript(" + scriptToRun + ", " + argsToPass + ")", ))
            if extraData.get('favorite') != 'true':
                argsToPass = 'markFavorite,' + extraData.get('favoriteurl')
                commands.append(( __language__(30095), "XBMC.RunScript(" + scriptToRun + ", " + argsToPass + ")", ))
            else:
                argsToPass = 'unmarkFavorite,' + extraData.get('favoriteurl')
                commands.append(( __language__(30096), "XBMC.RunScript(" + scriptToRun + ", " + argsToPass + ")", ))
                
            argsToPass = 'sortby'
            commands.append(( __language__(30097), "XBMC.RunScript(" + scriptToRun + ", " + argsToPass + ")", ))
            if 'Ascending' in WINDOW.getProperty("currenturl"):
                argsToPass = 'sortorder'
                commands.append(( __language__(30098), "XBMC.RunScript(" + scriptToRun + ", " + argsToPass + ")", ))
            else:
                argsToPass = 'sortorder'
                commands.append(( __language__(30099), "XBMC.RunScript(" + scriptToRun + ", " + argsToPass + ")", ))
                
            argsToPass = 'genrefilter'
            commands.append(( __language__(30040), "XBMC.RunScript(" + scriptToRun + ", " + argsToPass + ")", ))
            argsToPass = 'playall,' + extraData.get('id')
            commands.append(( __language__(30041), "XBMC.RunScript(" + scriptToRun + ", " + argsToPass + ")", ))            
            argsToPass = 'refresh'
            commands.append(( __language__(30042), "XBMC.RunScript(" + scriptToRun + ", " + argsToPass + ")", ))
            argsToPass = 'delete,' + extraData.get('deleteurl')
            commands.append(( __language__(30043), "XBMC.RunScript(" + scriptToRun + ", " + argsToPass + ")", ))
            list.addContextMenuItems( commands, g_contextReplace )

        list.setInfo('video', {'duration' : extraData.get('duration')})
        list.setInfo('video', {'playcount' : extraData.get('playcount')})
        list.setProperty('CriticRating', str(extraData.get('criticrating')))
        if extraData.get('favorite')=='true':
            list.setInfo('video', {'top250' : '1'})
        if extraData.get('totaltime') != None:
            list.setProperty('TotalTime', extraData.get('totaltime'))
            #list.setProperty('ResumeTime', str(int(extraData.get('resumetime'))/60))
        list.setInfo('video', {'director' : extraData.get('director')})
        list.setInfo('video', {'writer' : extraData.get('writer')})
        list.setInfo('video', {'year' : extraData.get('year')})
        list.setInfo('video', {'studio' : extraData.get('studio')})
        list.setInfo('video', {'genre' : extraData.get('genre')})
        if extraData.get('cast')!=None:
            list.setInfo('video', {'cast' : tuple(extraData.get('cast'))}) #--- Broken in Frodo
        #list.setInfo('video', {'castandrole' : extraData.get('cast')}) --- Broken in Frodo
        #list.setInfo('video', {'plotoutline' : extraData.get('cast')}) # Hack to get cast data into skin
        list.setInfo('video', {'episode': details.get('episode')})
        list.setInfo('video', {'season': details.get('season')})        
        list.setInfo('video', {'mpaa': extraData.get('mpaa')})
        list.setInfo('video', {'rating': extraData.get('rating')})
        if watched != None:
            list.setProperty('watchedurl', extraData.get('watchedurl'))
        list.addStreamInfo('video', {'duration': extraData.get('duration'), 'aspect': extraData.get('aspectratio'),'codec': extraData.get('videocodec'), 'width' : extraData.get('width'), 'height' : extraData.get('height')})
        list.addStreamInfo('audio', {'codec': extraData.get('audiocodec'),'channels': extraData.get('channels')})
        xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_NONE  )
        
        return (u, list, folder)

def displaySections( filter=None, shared=False ):
        printDebug("== ENTER: displaySections() ==", False)
        xbmcplugin.setContent(pluginhandle, 'files')
        ds_servers=discoverAllServers()
        numOfServers=len(ds_servers)
        printDebug( "Using list of "+str(numOfServers)+" servers: " +  str(ds_servers))
        
        dirItems = []
        
        for section in getAllSections(ds_servers):
        
            if shared and section.get('owned') == '1':
                continue
                
        
            details={'title' : section.get('title', 'Unknown') }

            if len(ds_servers) > 1:
                details['title']=section.get('serverName')+": "+details['title']

            extraData={ 'fanart_image' : '' ,
                        'type'         : "Video" ,
                        'thumb'        : '' ,
                        'token'        : section.get('token',None) }

                        #Determine what we are going to do process after a link is selected by the user, based on the content we find

            path=section['path']

            if section.get('type') == 'show':
                mode=_MODE_TVSHOWS
                if (filter is not None) and (filter != "tvshows"):
                    continue

            elif section.get('type') == 'movie':
                mode=_MODE_MOVIES
                printDebug("MovieType!")
                if (filter is not None) and (filter != "movies"):
                    continue

            elif section.get('type') == 'artist':
                mode=_MODE_ARTISTS
                if (filter is not None) and (filter != "music"):
                    continue

            elif section.get('type') == 'photo':
                mode=_MODE_PHOTOS
                if (filter is not None) and (filter != "photos"):
                    continue
            else:
                printDebug("Ignoring section "+details['title']+" of type " + section.get('type') + " as unable to process")
                continue

            path=path+'/all'

            extraData['mode']=mode
            s_url='http://%s%s' % ( section['address'], path)

            #Build that listing..
            printDebug("addGUIItem:"+str(s_url)+str(details)+str(extraData))
            dirItems.append(addGUIItem(s_url, details, extraData))

        if shared:
            xbmcplugin.addDirectoryItems(pluginhandle, dirItems)
            xbmcplugin.endOfDirectory(pluginhandle,cacheToDisc=False)
            return
                    
        #For each of the servers we have identified
        allservers=ds_servers
        numOfServers=len(allservers)

        #All XML entries have been parsed and we are ready to allow the user to browse around.  So end the screen listing.
        xbmcplugin.addDirectoryItems(pluginhandle, dirItems)
        xbmcplugin.endOfDirectory(pluginhandle,cacheToDisc=False)
        
def skin( filter=None, shared=False ):
        printDebug("== ENTER: skin() ==", False)
        ds_servers=discoverAllServers()
        numOfServers=len(ds_servers)
        printDebug( "Using list of "+str(numOfServers)+" servers: " +  str(ds_servers))
        #Get the global host variable set in settings
        WINDOW = xbmcgui.Window( 10000 )
        sectionCount=0
        dirItems = []
        
        for section in getAllSections(ds_servers):
        
            if shared and section.get('owned') == '1':
                continue
                
        
            details={'title' : section.get('title', 'Unknown') }

            if len(ds_servers) > 1:
                details['title']=section.get('serverName')+": "+details['title']

            extraData={ 'fanart_image' : '' ,
                        'type'         : "Video" ,
                        'thumb'        : '' ,
                        'token'        : section.get('token',None) }

                        #Determine what we are going to do process after a link is selected by the user, based on the content we find

            path=section['path']

            if section.get('type') == 'show':
                mode=_MODE_TVSHOWS
                window="VideoLibrary"
                if (filter is not None) and (filter != "tvshows"):
                    continue

            elif section.get('type') == 'movie':
                mode=_MODE_MOVIES
                window="VideoLibrary"
                printDebug("MovieType!")
                if (filter is not None) and (filter != "movies"):
                    continue

            elif section.get('type') == 'artist':
                mode=_MODE_ARTISTS
                window="MusicFiles"
                if (filter is not None) and (filter != "music"):
                    continue

            elif section.get('type') == 'photo':
                mode=_MODE_PHOTOS
                window="Pictures"
                if (filter is not None) and (filter != "photos"):
                    continue
            else:
                printDebug("Ignoring section "+details['title']+" of type " + section.get('type') + " as unable to process")
                continue

            path=path+'/all'

            extraData['mode']=mode
            modeurl="&mode=0"
            s_url='http://%s%s' % ( section['address'], path)
            murl= "?url="+urllib.quote(s_url)+modeurl

            #Build that listing..
            total = section.get('total')
            if (total == None):
                total = 0
            WINDOW.setProperty("xbmb3c.%d.title"    % (sectionCount) , section.get('title', 'Unknown'))
            WINDOW.setProperty("xbmb3c.%d.path"     % (sectionCount) , "ActivateWindow("+window+",plugin://plugin.video.xbmb3c/" + murl+",return)")
            WINDOW.setProperty("xbmb3c.%d.type"     % (sectionCount) , section.get('section'))
            WINDOW.setProperty("xbmb3c.%d.total" % (sectionCount) , str(total))

            printDebug("Building window properties index [" + str(sectionCount) + "] which is [" + section.get('title') + " section - " + section.get('section') + " total - " + str(total) + "]")
            printDebug("PATH in use is: ActivateWindow("+window+",plugin://plugin.video.xbmb3c/" + murl+",return)")
            sectionCount += 1

            #For each of the servers we have identified
            allservers=ds_servers
            numOfServers=len(allservers)

def remove_html_tags( data ):
    p = re.compile(r'<.*?>')
    return p.sub('', data)

def PLAY( url, handle ):
        printDebug("== ENTER: PLAY ==", False)
        url=urllib.unquote(url)
        server,id=url.split(',;')
        ip,port=server.split(':')
        userid=getUserId(ip,port)
        seekTime=0
        resume=0

        jsonData = getURL("http://" + server + "/mediabrowser/Users/" + userid + "/Items/" + id + "?format=json", suppress=False, popup=1 )     
        result = json.loads(jsonData)

        if __settings__.getSetting('playFromStream') == 'false':

            playurl = result.get("Path")

            if (result.get("VideoType") == "Dvd"):
                playurl = playurl+"/VIDEO_TS/VIDEO_TS.IFO"
            if (result.get("LocationType") == "Virtual"):
                playurl = __cwd__ + "/resources/media/offair.mp4"
            if __settings__.getSetting('smbusername')=='':
                playurl = playurl.replace("\\\\","smb://")
            else:
                playurl = playurl.replace("\\\\","smb://" + __settings__.getSetting('smbusername') + ':' + __settings__.getSetting('smbpassword') + '@')
            
            playurl = playurl.replace("\\","/")
            
        else:
        
            if __settings__.getSetting('transcode')=='true':
                playurl = 'http://' + server + '/mediabrowser/Videos/' + id + '/stream.ts'
            else:
                playurl = 'http://' + server + '/mediabrowser/Videos/' + id + '/stream?static=true'
                
        #if (__settings__.getSetting("markWatchedOnPlay")=='true'):
        watchedurl='http://' + server + '/mediabrowser/Users/'+ userid + '/PlayedItems/' + id
        positionurl='http://' + server + '/mediabrowser/Users/'+ userid + '/PlayingItems/' + id
            #print watchedurl
            #markWatched (urllib.unquote(watchedurl))
        
        item = xbmcgui.ListItem(path=playurl)
        item.setProperty('IsPlayable', 'true')
        item.setProperty('IsFolder', 'false')
        #xbmcplugin.setResolvedUrl(pluginhandle, True, item)
        #tree=etree.fromstring(html).getiterator(sDto + "BaseItemDto")
        userData = result.get("UserData")
        resume_result = 0
        if userData.get("PlaybackPositionTicks") != 0 and __settings__.getSetting('transcode') == 'false':
            reasonableTicks = int(userData.get("PlaybackPositionTicks")) / 1000
            seekTime = reasonableTicks / 10000
            displayTime = str(datetime.timedelta(seconds=seekTime))
            display_list = [ "Resume from " + displayTime, "Start from beginning"]
            resumeScreen = xbmcgui.Dialog()
            resume_result = resumeScreen.select('Resume', display_list)
            if resume_result == -1:
                return
        xbmc.Player().play(playurl,item)
        #xbmcplugin.setResolvedUrl(pluginhandle, True, item)
        WINDOW = xbmcgui.Window( 10000 )
        WINDOW.setProperty("watchedurl", watchedurl)
        WINDOW.setProperty("positionurl", positionurl)
        WINDOW.setProperty("runtimeticks", str(result.get("RunTimeTicks")))

        #Set a loop to wait for positive confirmation of playback
        count = 0
        while not xbmc.Player().isPlaying():
            printDebug( "Not playing yet...sleep for 1 sec")
            count = count + 1
            if count >= 10:
                return
            else:
                time.sleep(1)
                
        if resume_result == 0:
            jumpBackSec = int(__settings__.getSetting("resumeJumpBack"))
            seekToTime = seekTime - jumpBackSec
            while xbmc.Player().getTime() < seekToTime:
                xbmc.Player().pause
                xbmc.sleep(100)
                xbmc.Player().seekTime(seekToTime)
                xbmc.sleep(100)
                xbmc.Player().play()
        return

def get_params( paramstring ):
    printDebug("== ENTER: get_params ==", False)
    xbmc.log("Parameter string: " + paramstring)
    param={}
    if len(paramstring)>=2:
            params=paramstring

            if params[0] == "?":
                cleanedparams=params[1:]
            else:
                cleanedparams=params

            if (params[len(params)-1]=='/'):
                    params=params[0:len(params)-2]

            pairsofparams=cleanedparams.split('&')
            for i in range(len(pairsofparams)):
                    splitparams={}
                    splitparams=pairsofparams[i].split('=')
                    if (len(splitparams))==2:
                            param[splitparams[0]]=splitparams[1]
                    elif (len(splitparams))==3:
                            param[splitparams[0]]=splitparams[1]+"="+splitparams[2]
    xbmc.log ("XBMB3C -> Detected parameters: " + str(param))
    return param

def getCacheValidator (server,url):
    parsedserver,parsedport = server.split(':')
    userid = getUserId(parsedserver, parsedport)
    idAndOptions = url.split("ParentId=")
    id = idAndOptions[1].split("&")
    jsonData = getURL("http://"+server+"/mediabrowser/Users/" + userid + "/Items/" +id[0]+"?format=json", suppress=False, popup=1 )
    result = json.loads(jsonData)
    
    printDebug ("RecursiveItemCount: " + str(result.get("RecursiveItemCount")))
    printDebug ("RecursiveUnplayedCount: " + str(result.get("RecursiveUnplayedItemCount")))
    printDebug ("RecursiveUnplayedCount: " + str(result.get("PlayedPercentage")))
    
    playedPercentage = 0.0
    if(result.get("PlayedPercentage") != None):
        playedPercentage = result.get("PlayedPercentage")
    
    playedTime = "{0:09.6f}".format(playedPercentage)
    playedTime = playedTime.replace(".","-")
    validatorString = str(result.get("RecursiveItemCount")) + "_" + str(result.get("RecursiveUnplayedItemCount")) + "_" + playedTime
    printDebug ("getCacheValidator : " + validatorString)
    return validatorString
    
def getCacheValidatorFromData(result):
    result = result.get("Items")
    if(result == None):
        result = []

    itemCount = 0
    unwatchedItemCount = 0
    totalPlayedPercentage = 0
    for item in result:
        userData = item.get("UserData")
        if(userData != None):
            if(item.get("IsFolder") == False):
                itemCount = itemCount + 1
                if userData.get("Played") == False:
                    unwatchedItemCount = unwatchedItemCount + 1
                    itemPossition = userData.get("PlaybackPositionTicks")
                    itemRuntime = item.get("RunTimeTicks")
                    if(itemRuntime != None and itemPossition != None):
                        itemPercent = float(itemPossition) / float(itemRuntime)
                        totalPlayedPercentage = totalPlayedPercentage + itemPercent
                else:
                    totalPlayedPercentage = totalPlayedPercentage + 100
            else:
                itemCount = itemCount + item.get("RecursiveItemCount")
                unwatchedItemCount = unwatchedItemCount + item.get("RecursiveUnplayedItemCount")
                PlayedPercentage=item.get("PlayedPercentage")
                if PlayedPercentage==None:
                    PlayedPercentage=0
                totalPlayedPercentage = totalPlayedPercentage + (item.get("RecursiveItemCount") * PlayedPercentage)
            
    if(itemCount == 0):
        totalPlayedPercentage = 0.0
    else:
        totalPlayedPercentage = totalPlayedPercentage / float(itemCount)
        
    playedTime = "{0:09.6f}".format(totalPlayedPercentage)
    playedTime = playedTime.replace(".","-")
    validatorString = "_" + str(itemCount) + "_" + str(unwatchedItemCount) + "_" + playedTime
    printDebug ("getCacheValidatorFromData : " + validatorString)
    return validatorString
    
def getContent( url ):
    '''
        This function takes the URL, gets the XML and determines what the content is
        This XML is then redirected to the best processing function.
        If a search term is detected, then show keyboard and run search query
        @input: URL of XML page
        @return: nothing, redirects to another function
    '''
    printDebug("== ENTER: getContent ==", False)
    server=getServerFromURL(url)
    lastbit=url.split('/')[-1]
    printDebug("URL suffix: " + str(lastbit))
    printDebug("server: " + str(server))
    printDebug("URL: " + str(url))    
    validator='special' #Ugly hack to allow special queries (recently added etc) to work
    if "Parent" in url:
        validator = "_" + getCacheValidator(server,url)
        
    # ADD VALIDATOR TO FILENAME TO DETERMINE IF CACHE IS FRESH
    
    m = hashlib.md5()
    m.update(url)
    urlHash = m.hexdigest()
   
    jsonData = ""
    cacheDataPath = __addondir__ + urlHash + validator
    
    result = None
    
    WINDOW = xbmcgui.Window( 10000 )
    force_data_reload = WINDOW.getProperty("force_data_reload")
    WINDOW.setProperty("force_data_reload", "false")
    
    # if a cached file exists use it
    # if one does not exist then load data from the url
    if(os.path.exists(cacheDataPath)) and validator != 'special' and force_data_reload != "true":
        cachedfie = open(cacheDataPath, 'r')
        jsonData = cachedfie.read()
        cachedfie.close()
        xbmc.log("Data Read From Cache : " + cacheDataPath)
        try:
            result = loadJasonData(jsonData)
        except:
            xbmc.log("Json load failed from cache data")
            result = []
        dataLen = len(result)
        xbmc.log("Json Load Result : " + str(dataLen))
        if(dataLen == 0):
            result = None
    
    # if there was no cache data for the cache data was not valid then try to load it again
    if(result == None):
        r = glob.glob(__addondir__ + urlHash + "*")
        for i in r:
            os.remove(i)
        xbmc.log("No Cache Data, download data now")
        jsonData = getURL(url, suppress=False, popup=1 )
        try:
            result = loadJasonData(jsonData)
        except:
            xbmc.log("Json load failed from downloaded data")
            result = []
        dataLen = len(result)
        xbmc.log("Json Load Result : " + str(dataLen))
        if(dataLen > 0 and validator != 'special'):
            cacheValidationString = getCacheValidatorFromData(result)
            xbmc.log("getCacheValidator : " + validator)
            xbmc.log("getCacheValidatorFromData : " + cacheValidationString)
            if(validator == cacheValidationString):
                xbmc.log("Validator String Match, Saving Cache Data")
                cacheDataPath = __addondir__ + urlHash + cacheValidationString
                xbmc.log("Saving data to cache : " + cacheDataPath)
                cachedfie = open(cacheDataPath, 'w')
                cachedfie.write(jsonData)
                cachedfie.close()        

    if jsonData == "":
        return
    
    printDebug("JSON DATA: " + str(result))
    dirItems = processDirectory(url, result)
    
    xbmcplugin.addDirectoryItems(pluginhandle, dirItems)
    xbmcplugin.endOfDirectory(pluginhandle, cacheToDisc=False)
    
    return

def loadJasonData(jsonData):
    return json.loads(jsonData)
    
def processDirectory(url, result):
    cast=['None']
    printDebug("== ENTER: processDirectory ==", False)
    parsed = urlparse(url)
    parsedserver,parsedport=parsed.netloc.split(':')
    userid=getUserId(parsedserver,parsedport)
    printDebug("Processing secondary menus")
    xbmcplugin.setContent(pluginhandle, 'movies')

    server=getServerFromURL(url)
    setWindowHeading(url)
    
    detailsString = "Path,Genres,Studios,CumulativeRunTimeTicks"
    
    if(__settings__.getSetting('includeStreamInfo') == "true"):
        detailsString += ",MediaStreams"
    
    if(__settings__.getSetting('includePeople') == "true"):
        detailsString += ",People"
        
    if(__settings__.getSetting('includeOverview') == "true"):
        detailsString += ",Overview"            
    
    dirItems = []
    result = result.get("Items")
    if(result == None):
        result = []

    for item in result:
    
        if(item.get("Name") != None):
            tempTitle = item.get("Name").encode('utf-8')
        else:
            tempTitle = "Missing Title"
            
        id = str(item.get("Id")).encode('utf-8')
        isFolder = item.get("IsFolder")
        item_type = str(item.get("Type")).encode('utf-8')
        
        tempEpisode = ""
        if (item.get("IndexNumber") != None):
            episodeNum = item.get("IndexNumber")
            if episodeNum < 10:
                tempEpisode = "0" + str(episodeNum)
            else:
                tempEpisode = str(episodeNum)
                
        tempSeason = ""
        if (str(item.get("ParentIndexNumber")) != None):
            tempSeason = str(item.get("ParentIndexNumber"))
      
        if item.get("Type") == "Episode":
            tempTitle = str(tempEpisode) + ' - ' + tempTitle
            xbmcplugin.setContent(pluginhandle, 'episodes')
        if item.get("Type") == "Season":
            xbmcplugin.setContent(pluginhandle, 'tvshows')
        if item.get("Type") == "Audio":
            xbmcplugin.setContent(pluginhandle, 'songs')            
        if item.get("Type") == "Series":
            xbmcplugin.setContent(pluginhandle, 'tvshows')         

        #Add show name to special TV collections RAL, NextUp etc
        WINDOW = xbmcgui.Window( 10000 )
        if WINDOW.getProperty("addshowname") == "true":
            tempTitle=item.get("SeriesName").encode('utf-8') + " - " + tempTitle
        else:
            tempTitle=tempTitle

        # Process MediaStreams
        channels = ''
        videocodec = ''
        audiocodec = ''
        height = ''
        width = ''
        aspectratio = '1:1'
        aspectfloat = 1.85
        mediaStreams = item.get("MediaStreams")
        if(mediaStreams != None):
            for mediaStream in mediaStreams:
                if(mediaStream.get("Type") == "Video"):
                    videocodec = mediaStream.get("Codec")
                    height = str(mediaStream.get("Height"))
                    width = str(mediaStream.get("Width"))
                    aspectratio = mediaStream.get("AspectRatio")
                    if aspectratio != None and len(aspectratio) >= 3:
                        try:
                            aspectwidth,aspectheight = aspectratio.split(':')
                            aspectfloat = float(aspectwidth) / float(aspectheight)
                        except:
                            aspectfloat = 1.85
                if(mediaStream.get("Type") == "Audio"):
                    audiocodec = mediaStream.get("Codec")
                    channels = mediaStream.get("Channels")
                
        # Process People
        director=''
        writer=''
        cast=[]
        people = item.get("People")
        if(people != None):
            for person in people:
                if(person.get("Type") == "Director"):
                    director = director + person.get("Name") + ' ' 
                if(person.get("Type") == "Writing"):
                    writer = person.get("Name")                
                if(person.get("Type") == "Actor"):
                    Name = person.get("Name")
                    Role = person.get("Role")
                    if Role == None:
                        Role = ''
                    cast.append(Name)

        # Process Studios
        studio = ""
        studios = item.get("Studios")
        if(studios != None):
            for studio_string in studios:
                if studio=="": #Just take the first one
                    temp=studio_string.get("Name")
                    studio=temp.encode('utf-8')
        # Process Genres
        genre = ""
        genres = item.get("Genres")
        if(genres != None):
            for genre_string in genres:
                if genre == "": #Just take the first genre
                    genre = genre_string
                else:
                    genre = genre + " / " + genre_string
                
        # Process UserData
        userData = item.get("UserData")
        if(userData != None):
            if userData.get("Played") != True:
                overlay = "7"
                watched = "true"
            else:
                overlay = "6"
                watched = "false"
            if userData.get("IsFavorite") == True:
                overlay = "5"
                favorite = "true"
            else:
                favorite = "false"
            if userData.get("PlaybackPositionTicks") != None:
                PlaybackPositionTicks = str(userData.get("PlaybackPositionTicks"))
                reasonableTicks = int(userData.get("PlaybackPositionTicks")) / 1000
                seekTime = reasonableTicks / 10000
            else:
                PlaybackPositionTicks = '100'

        playCount = 0
        if(userData.get("Played") == True):
            playCount = 1
        # Populate the details list
        details={'title'        : tempTitle,
                 'plot'         : item.get("Overview"),
                 'episode'      : tempEpisode,
                 #'watched'      : watched,
                 'Overlay'      : overlay,
                 'playcount'    : str(playCount),
                 #'aired'       : episode.get('originallyAvailableAt','') ,
                 'SeriesName'  :  item.get("SeriesName"),
                 'season'       : tempSeason
                 }
                 
        try:
            tempDuration = str(int(item.get("RunTimeTicks"))/(10000000*60))
            RunTimeTicks = str(item.get("RunTimeTicks"))
        except TypeError:
            try:
                tempDuration = str(int(item.get("CumulativeRunTimeTicks"))/(10000000*60))
                RunTimeTicks = str(item.get("CumulativeRunTimeTicks"))
            except TypeError:
                tempDuration = "0"
                RunTimeTicks = "0"
        
        if(item.get("PremiereDate") != None):
            premieredatelist = (item.get("PremiereDate")).split("T")
            premieredate = premieredatelist[0]
        else:
            premieredate = ""

        # Populate the extraData list
        extraData={'thumb'        : getThumb(item) ,
                   'fanart_image' : getFanart(item) ,
                   'poster'       : getThumb(item) ,
                   'banner'       : getBanner(item) ,
                   'logo'         : getLogo(item) ,
                   'disc'         : getDisc(item) ,
                   'clearart'     : getClearArt(item) ,
                   'landscape'    : getLandscape(item) ,
                   'id'           : id ,
                   'mpaa'         : item.get("OfficialRating"),
                   'rating'       : item.get("CommunityRating"),
                   'criticrating' : item.get("CriticRating"), 
                   'year'         : item.get("ProductionYear"),
                   'locationtype' : item.get("LocationType"),
                   'premieredate' : premieredate,
                   'studio'       : studio,
                   'genre'        : genre,
                   'playcount'    : str(playCount),
                   'director'     : director,
                   'writer'       : writer,
                   'channels'     : channels,
                   'videocodec'   : videocodec,
                   'aspectratio'  : str(aspectfloat),
                   'audiocodec'   : audiocodec,
                   'height'       : height,
                   'width'        : width,
                   'cast'         : cast,
                   'favorite'     : favorite,
                   'watchedurl'   : 'http://' + server + '/mediabrowser/Users/'+ userid + '/PlayedItems/' + id,
                   'favoriteurl'  : 'http://' + server + '/mediabrowser/Users/'+ userid + '/FavoriteItems/' + id,
                   'deleteurl'    : 'http://' + server + '/mediabrowser/Items/' + id,                   
                   'parenturl'    : url,
                   'resumetime'   : str(seekTime),
                   'totaltime'    : tempDuration,
                   'duration'     : tempDuration,
                   'RecursiveItemCount' : item.get("RecursiveItemCount"),
                   'RecursiveUnplayedItemCount' : item.get("RecursiveUnplayedItemCount")}
                   
        if extraData['thumb'] == '':
            extraData['thumb'] = extraData['fanart_image']

        extraData['mode'] = _MODE_GETCONTENT
        
        if isFolder == True:
            SortByTemp = __settings__.getSetting('sortby')
            if SortByTemp == '':
                SortByTemp = 'SortName'
                
            if  item_type == 'Season' or item_type == 'BoxSet' or item_type == 'MusicAlbum' or item_type == 'MusicArtist':
                u = 'http://' + server + '/mediabrowser/Users/'+ userid + '/items?ParentId=' +id +'&IsVirtualUnAired=false&IsMissing=false&Fields=' + detailsString + '&SortBy='+SortByTemp+'&format=json'
                if (item.get("RecursiveItemCount") != 0):
                    dirItems.append(addGUIItem(u, details, extraData))
            else:
                if __settings__.getSetting('autoEnterSingle') == "true":
                    if item.get("ChildCount") == 1:
                        u = 'http://' + server + '/mediabrowser/Users/'+ userid + '/items?ParentId=' +id +'&recursive=true&IncludeItemTypes=Episode&Fields=' + detailsString + '&SortBy='+SortByTemp+'&IsVirtualUnAired=false&IsMissing=false&format=json'
                    else:
                        u = 'http://' + server + '/mediabrowser/Users/'+ userid + '/items?ParentId=' +id +'&IsVirtualUnAired=false&IsMissing=false&Fields=' + detailsString + '&SortBy='+SortByTemp+'&format=json'
                else:
                    u = 'http://' + server + '/mediabrowser/Users/'+ userid + '/items?ParentId=' +id +'&IsVirtualUnAired=false&IsMissing=false&Fields=' + detailsString + '&SortBy='+SortByTemp+'&format=json'

                if (item.get("RecursiveItemCount") != 0):
                    dirItems.append(addGUIItem(u, details, extraData))

        else:
            u = server+',;'+id
            dirItems.append(addGUIItem(u, details, extraData, folder=False))
    
    return dirItems

def getThumb( data ):
    
    id = data.get("Id")
    if __settings__.getSetting('useSeriesArt') == "true":
        if data.get("Type") == "Episode":
            id = data.get("SeriesId")

    # use the local image proxy server that is made available by this addons service
    thumbnail = ("http://localhost:15001/?id=" + str(id) + "&type=t")
    printDebug("getThumb : " + thumbnail)
    return thumbnail
    
def getFanart( data ):

    id = data.get("Id")
    if data.get("Type") == "Episode" or data.get("Type") == "Season":
        id = data.get("SeriesId")   
    
    # use the local image proxy server that is made available by this addons service
    fanArt = ("http://localhost:15001/?id=" + str(id) + "&type=b")
    printDebug("getFanart : " + fanArt)
    return fanArt
    
def getBanner( data ):

    id = data.get("Id")
    if data.get("Type") == "Episode" or data.get("Type") == "Season":
        id = data.get("SeriesId")   
    
    # use the local image proxy server that is made available by this addons service
    banner = ("http://localhost:15001/?id=" + str(id) + "&type=banner")
    printDebug("getBanner : " + banner)
    return banner

def getLogo( data ):

    id = data.get("Id")
    if data.get("Type") == "Episode" or data.get("Type") == "Season":
        id = data.get("SeriesId")   
    
    # use the local image proxy server that is made available by this addons service
    logo = ("http://localhost:15001/?id=" + str(id) + "&type=logo")
    printDebug("getLogo : " + logo)
    return logo

def getDisc( data ):
    
    id = data.get("Id")
    if data.get("Type") == "Episode" or data.get("Type") == "Season":
        id = data.get("SeriesId")   
    
    # use the local image proxy server that is made available by this addons service
    disc = ("http://localhost:15001/?id=" + str(id) + "&type=disc")
    printDebug("getDisc : " + disc)
    return disc

def getClearArt( data ):
    
    id = data.get("Id")
    if data.get("Type") == "Episode" or data.get("Type") == "Season":
        id = data.get("SeriesId")   
    
    # use the local image proxy server that is made available by this addons service
    art = ("http://localhost:15001/?id=" + str(id) + "&type=clearart")
    printDebug("getClearArt : " + art)
    return art

def getLandscape( data ):
    
    id = data.get("Id")
    if data.get("Type") == "Episode" or data.get("Type") == "Season":
        id = data.get("SeriesId")   
    
    # use the local image proxy server that is made available by this addons service
    landscape = ("http://localhost:15001/?id=" + str(id) + "&type=landscape")
    printDebug("getLandscape : " + landscape)
    return landscape
    
def getServerFromURL( url ):
    '''
    Simply split the URL up and get the server portion, sans port
    @ input: url, woth or without protocol
    @ return: the URL server
    '''
    if url[0:4] == "http":
        return url.split('/')[2]
    else:
        return url.split('/')[0]

def getLinkURL( url, pathData, server ):
    '''
        Investigate the passed URL and determine what is required to
        turn it into a usable URL
        @ input: url, XML data and PM server address
        @ return: Usable http URL
    '''
    printDebug("== ENTER: getLinkURL ==")
    path=pathData.get('key','')
    printDebug("Path is " + path)

    if path == '':
        printDebug("Empty Path")
        return

    #If key starts with http, then return it
    if path[0:4] == "http":
        printDebug("Detected http link")
        return path

    #If key starts with a / then prefix with server address
    elif path[0] == '/':
        printDebug("Detected base path link")
        return 'http://%s%s' % ( server, path )

    elif path[0:5] == "rtmp:":
        printDebug("Detected  link")
        return path

    #Any thing else is assumed to be a relative path and is built on existing url
    else:
        printDebug("Detected relative link")
        return "%s/%s" % ( url, path )

    return url

def install( url, name ):
    printDebug("== ENTER: install ==", False)
    tree=getXML(url)
    if tree is None:
        return

    operations={}
    i=0
    for plums in tree.findall('Directory'):
        operations[i]=plums.get('title')

        #If we find an install option, switch to a yes/no dialog box
        if operations[i].lower() == "install":
            printDebug("Not installed.  Print dialog")
            ret = xbmcgui.Dialog().yesno("XBMB3C","About to install " + name)

            if ret:
                printDebug("Installing....")
                installed = getURL(url+"/install")
                tree = etree.fromstring(installed)

                msg=tree.get('message','(blank)')
                printDebug(msg)
                xbmcgui.Dialog().ok("XBMB3C",msg)
            return

        i+=1

    #Else continue to a selection dialog box
    ret = xbmcgui.Dialog().select("This plugin is already installed..",operations.values())

    if ret == -1:
        printDebug("No option selected, cancelling")
        return

    printDebug("Option " + str(ret) + " selected.  Operation is " + operations[ret])
    u=url+"/"+operations[ret].lower()

    action = getURL(u)
    tree = etree.fromstring(action)

    msg=tree.get('message')
    printDebug(msg)
    xbmcgui.Dialog().ok("XBMB3C",msg)
    xbmc.executebuiltin("Container.Refresh")

    return

def displayServers( url ):
    printDebug("== ENTER: displayServers ==", False)
    type=url.split('/')[2]
    printDebug("Displaying entries for " + type)
    Servers = discoverAllServers()
    Servers_list=len(Servers)

    dirItems = []
    
    #For each of the servers we have identified
    for mediaserver in Servers.values():

        details={'title' : mediaserver.get('serverName','Unknown') }

        if mediaserver.get('token',None):
            extraData={'token' : mediaserver.get('token') }
        else:
            extraData={}

        dirItems.append(addGUIItem(s_url, details, extraData ))

    xbmcplugin.addDirectoryItems(pluginhandle, dirItems)
    xbmcplugin.endOfDirectory(pluginhandle,cacheToDisc=False)

def setArt (list,name,path):
    if xbmcVersionNum >= 13:
        list.setArt({name:path})
        
def getXbmcVersion():
    version = 0.0
    jsonData = xbmc.executeJSONRPC('{ "jsonrpc": "2.0", "method": "Application.GetProperties", "params": {"properties": ["version", "name"]}, "id": 1 }') 
    
    result = json.loads(jsonData)
    
    try:
        result = result.get("result")
        versionData = result.get("version")
        version = float(str(versionData.get("major")) + "." + str(versionData.get("minor")))
        xbmc.log("Version : " + str(version) + " - " + str(versionData))
    except:
        version = 0.0
        xbmc.log("Version Error : RAW Version Data : " + str(result))

    return version        
    
def setWindowHeading(url) :
    WINDOW = xbmcgui.Window( 10000 )
    WINDOW.setProperty("addshowname", "false")
    WINDOW.setProperty("currenturl", url)
    WINDOW.setProperty("currentpluginhandle", str(pluginhandle))
    if 'ParentId' in url:
        dirUrl = url.replace('items?ParentId=','Items/')
        splitUrl = dirUrl.split('&')
        dirUrl = splitUrl[0] + '?format=json'
        jsonData = getURL(dirUrl)
        result = json.loads(jsonData)
        for name in result:
            title = name
        WINDOW.setProperty("heading", title)
    elif 'IncludeItemTypes=Episode' in url:
        WINDOW.setProperty("addshowname", "true")

def setMasterServer () :
    printDebug("== ENTER: setmasterserver ==", False)

    servers=getMasterServer(True)
    printDebug(str(servers))
    
    current_master=__settings__.getSetting('masterServer')
    
    displayList=[]
    for address in servers:
        found_server = address['name']
        if found_server == current_master:
            found_server = found_server+"*"
        displayList.append(found_server)
    
    audioScreen = xbmcgui.Dialog()
    result = audioScreen.select('Select master server',displayList)
    if result == -1:
        return False

    printDebug("Setting master server to: %s" % (servers[result]['name'],))
    __settings__.setSetting('masterServer',servers[result]['name'])
    return
    

###########################################################################  
##Start of Main
###########################################################################
printDebug( "XBMB3C -> Script argument is " + str(sys.argv[1]), False)
xbmcVersionNum = getXbmcVersion()
try:
    params=get_params(sys.argv[2])
except:
    params={}
#Check to see if XBMC is playing - we don't want to do anything if so
#if xbmc.Player().isPlaying():
#    printDebug ('Already Playing! Exiting...')
#    sys.exit()
#Now try and assign some data to them
param_url=params.get('url',None)

if param_url and ( param_url.startswith('http') or param_url.startswith('file') ):
        param_url = urllib.unquote(param_url)

param_name=urllib.unquote_plus(params.get('name',""))
mode=int(params.get('mode',-1))
param_transcodeOverride=int(params.get('transcode',0))
param_identifier=params.get('identifier',None)
param_indirect=params.get('indirect',None)
force=params.get('force')
WINDOW = xbmcgui.Window( 10000 )
WINDOW.setProperty("addshowname","false")
if str(sys.argv[1]) == "skin":
     skin()
elif str(sys.argv[1]) == "shelf":
     shelf()
elif str(sys.argv[1]) == "channelShelf":
     shelfChannel()
elif sys.argv[1] == "update":
    url=sys.argv[2]
    libraryRefresh(url)
elif sys.argv[1] == "markWatched":
    url=sys.argv[2]
    markWatched(url)
elif sys.argv[1] == "markUnwatched":
    url=sys.argv[2]
    markUnwatched(url)
elif sys.argv[1] == "markFavorite":
    url=sys.argv[2]
    markFavorite(url)
elif sys.argv[1] == "unmarkFavorite":
    url=sys.argv[2]
    unmarkFavorite(url)    
elif sys.argv[1] == "setting":
    __settings__.openSettings()
    WINDOW = xbmcgui.getCurrentWindowId()
    if WINDOW == 10000:
        printDebug("Currently in home - refreshing to allow new settings to be taken")
        xbmc.executebuiltin("XBMC.ActivateWindow(Home)")
#elif sys.argv[1] == "refresh":
#    server_list = discoverAllServers()
elif sys.argv[1] == "delete":
    url=sys.argv[2]
    delete(url)
elif sys.argv[1] == "refresh":
    WINDOW = xbmcgui.Window( 10000 )
    WINDOW.setProperty("force_data_reload", "true")    
    xbmc.executebuiltin("Container.Refresh")    
elif sys.argv[1] == "sortby":
    sortby()
elif sys.argv[1] == "sortorder":
    sortorder()
elif sys.argv[1] == "genrefilter":
    genrefilter()
elif sys.argv[1] == "playall":
    startId=sys.argv[2]
    playall(startId)    
else:

    pluginhandle = int(sys.argv[1])

    WINDOW = xbmcgui.Window( 10000 )
    WINDOW.clearProperty("heading")
    #mode=_MODE_BASICPLAY
    if g_debug == "true":
        xbmc.log ("XBMB3C -> Mode: "+str(mode))
        xbmc.log ("XBMB3C -> URL: "+str(param_url))
        xbmc.log ("XBMB3C -> Name: "+str(param_name))
        xbmc.log ("XBMB3C -> identifier: " + str(param_identifier))

    #Run a function based on the mode variable that was passed in the URL
    if ( mode == None ) or ( param_url == None ) or ( len(param_url)<1 ):
        displaySections()

    elif mode == _MODE_GETCONTENT:
        if __settings__.getSetting('profile') == "true":
            fileTimeStamp = time.strftime("%Y-%m-%d %H-%M-%S")
            profileFileName = __addondir__ + "profile_(" + fileTimeStamp + ").dat"
            filename = __addondir__ + "profile_cumulative_(" + fileTimeStamp + ").txt"
            cProfile.run("getContent(param_url)", profileFileName)
            stream = open(filename, "w")
            p = pstats.Stats(profileFileName, stream=stream)
            p.sort_stats('cumulative').print_stats()
        else:
            getContent(param_url)
        

    elif mode == _MODE_BASICPLAY:
        PLAY(param_url, pluginhandle)
    
xbmc.log ("===== XBMB3C STOP =====")

#clear done and exit.
sys.modules.clear()
