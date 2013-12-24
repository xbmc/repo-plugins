'''
    @document   : default.py
    @package    : XBMB3C add-on
    @author     : xnappo
    @copyleft   : 2013, xnappo
    @version    : 0.6.5 (frodo)

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

__settings__ = xbmcaddon.Addon(id='plugin.video.xbmb3c')
__cwd__ = __settings__.getAddonInfo('path')
__addon__       = xbmcaddon.Addon(id='plugin.video.xbmb3c')
__addondir__    = xbmc.translatePath( __addon__.getAddonInfo('profile') ) 
__language__     = __addon__.getLocalizedString

BASE_RESOURCE_PATH = xbmc.translatePath( os.path.join( __cwd__, 'resources', 'lib' ) )
PLUGINPATH=xbmc.translatePath( os.path.join( __cwd__) )

sDto='{http://schemas.datacontract.org/2004/07/MediaBrowser.Model.Dto}'
sEntities='{http://schemas.datacontract.org/2004/07/MediaBrowser.Model.Entities}'
sArrays='{http://schemas.microsoft.com/2003/10/Serialization/Arrays}'

sys.path.append(BASE_RESOURCE_PATH)
XBMB3C_VERSION="0.6.5"

xbmc.log ("===== XBMB3C START =====")

xbmc.log ("XBMB3C -> running Python: " + str(sys.version_info))
xbmc.log ("XBMB3C -> running XBMB3C: " + str(XBMB3C_VERSION))

try:
  import lxml.etree.ElementTree as etree
  xbmc.log("XBMB3C -> Running with lxml.etree")
except ImportError:
  try:
    # Python 2.5
    import xml.etree.cElementTree as etree
    xbmc.log("XBMB3C -> Running with cElementTree on Python 2.5+")
  except ImportError:
    try:
      # Python 2.5
      import xml.etree.ElementTree as etree
      xbmc.log("XBMB3C -> Running with ElementTree on Python 2.5+")
    except ImportError:
      try:
        # normal cElementTree install
        import cElementTree as etree
        xbmc.log("XBMB3C -> Running with built-in cElementTree")
      except ImportError:
        try:
          # normal ElementTree install
          import elementtree.ElementTree as etree
          xbmc.log("XBMB3C -> Running with built-in ElementTree")
        except ImportError:
            try:
                import ElementTree as etree
                xbmc.log("XBMB3C -> Running addon ElementTree version")
            except ImportError:
                xbmc.log("XBMB3C -> Failed to import ElementTree from any known place")
    
#Get the setting from the appropriate file.
DEFAULT_PORT="32400"
_MODE_GETCONTENT=0
_MODE_MOVIES=0
_MODE_BASICPLAY=12

#Check debug first...
g_debug = __settings__.getSetting('debug')
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
    html = getURL(ip_address+":"+port+"/mediabrowser/Users?format=xml")
    userid=''
    printDebug("Looking for user name: " + __settings__.getSetting('username'))
    printDebug("userhtml:" + html)
    tree= etree.fromstring(html).getiterator(sDto + 'UserDto')
    for UserDto in tree:
        if __settings__.getSetting('username')==UserDto.find(sDto+'Name').text:
            userid=str(UserDto.find(sDto + 'Id').text)
    if __settings__.getSetting('password')!="":
        authenticate('http://'+ip_address+":"+port+"/mediabrowser/Users/AuthenticateByName")
    if userid=='':
        return_value = xbmcgui.Dialog().ok(__language__(30045),__language__(30045))
        sys.exit()
    printDebug("userid:" + userid)
    WINDOW = xbmcgui.Window( 10000 )
    WINDOW.setProperty("userid",userid)
    return userid
    
def getLocalServers( ip_address, port ):
    '''
        Connect to the defined local server (either direct or via bonjour discovery)
        and get a list of all known servers.
        @input: nothing
        @return: a list of servers (as Dict)
    '''
    printDebug("== ENTER: getLocalServers ==", False)
    url_path="/mediabrowser/Users/" + getUserId( ip_address, port) + "/items?format=xml"
    html = getURL(ip_address+":"+port+url_path)

    if html is False:
         return []
    server=etree.fromstring(html)

    return {'serverName': server.get('friendlyName','Unknown').encode('utf-8') ,
                        'server'    : ip_address,
                        'port'      : port ,
                        'discovery' : 'local' ,
                        'token'     : None ,
                        'uuid'      : server.get('machineIdentifier') ,
                        'owned'     : '1' ,
                        'master'    : 1 }

def getServerSections ( ip_address, port, name, uuid):
    printDebug("== ENTER: getServerSections ==", False)
    userid=str(getUserId( ip_address, port))
    html = getURL(ip_address+":"+port+"/mediabrowser/Users/"+userid+"/Items/Root?format=xml")
    printDebug("html:" + html)
    tree= etree.fromstring(html).getiterator(sDto + 'BaseItemDto')
    for BaseItemDto in tree:
        parentid=str(BaseItemDto.find(sDto + 'Id').text)
    htmlpath=("http://%s:%s/mediabrowser/Users/" % ( ip_address, port))
    html=getURL(htmlpath + userid + "/items?ParentId=" + parentid + "&format=xml")

    if html is False:
        return {}

    
    tree = etree.fromstring(html).getiterator(sDto + "BaseItemDto")
    temp_list=[]
    for BaseItemDto in tree:
        if(str(BaseItemDto.find(sDto + 'RecursiveItemCount').text)!='0'):
            Name=(BaseItemDto.find(sDto + 'Name').text).encode('utf-8')
            if __settings__.getSetting(urllib.quote('sortbyfor'+Name)) == '':
                __settings__.setSetting(urllib.quote('sortbyfor'+Name),'SortName')
                __settings__.setSetting(urllib.quote('sortorderfor'+Name),'Ascending')
            temp_list.append( {'title'      : Name,
                    'address'    : ip_address+":"+port ,
                    'serverName' : name ,
                    'uuid'       : uuid ,
                    'path'       : ('/mediabrowser/Users/' + userid + '/items?ParentId=' + str(BaseItemDto.find(sDto + 'Id').text) + '&IsVirtualUnaired=false&IsMissing=False&Fields=Path,Overview,Genres,People,MediaStreams&SortOrder='+__settings__.getSetting('sortorderfor'+urllib.quote(Name))+'&SortBy='+__settings__.getSetting('sortbyfor'+urllib.quote(Name))+'&Genres=&format=xml') ,
                    'token'      : str(BaseItemDto.find(sDto + 'Id').text)  ,
                    'location'   : "local" ,
                    'art'        : str(BaseItemDto.text) ,
                    'local'      : '1' ,
                    'type'       : "movie",
                    'owned'      : '1' })
            printDebug("Title " + str(BaseItemDto.tag))

# Add recent movies
    temp_list.append( {'title'      : 'Recently Added Movies',
            'address'    : ip_address+":"+port ,
            'serverName' : name ,
            'uuid'       : uuid ,
            'path'       : ('/mediabrowser/Users/' + userid + '/Items?Limit=' + __settings__.getSetting("numRecentMovies") +'&Recursive=true&SortBy=DateCreated&Fields=Path,Overview,Genres,People,MediaStreams&SortOrder=Descending&Filters=IsUnplayed,IsNotFolder&IncludeItemTypes=Movie&format=xml') ,
            'token'      : ''  ,
            'location'   : "local" ,
            'art'        : '' ,
            'local'      : '1' ,
            'type'       : "movie",
            'owned'      : '1' })
            
# Add recent Episodes
    temp_list.append( {'title'      : 'Recently Added Episodes',
            'address'    : ip_address+":"+port ,
            'serverName' : name ,
            'uuid'       : uuid ,
            'path'       : ('/mediabrowser/Users/' + userid + '/Items?Limit=' + __settings__.getSetting("numRecentTV") +'&Recursive=true&SortBy=DateCreated&Fields=Path,Overview,Genres,People,MediaStreams&SortOrder=Descending&Filters=IsUnplayed,IsNotFolder&IsVirtualUnaired=false&IsMissing=False&IncludeItemTypes=Episode&format=xml') ,
            'token'      : ''  ,
            'location'   : "local" ,
            'art'        : '' ,
            'local'      : '1' ,
            'type'       : "movie",
            'owned'      : '1' })            
# Add NextUp Episodes
    temp_list.append( {'title'      : 'Next Episodes',
            'address'    : ip_address+":"+port ,
            'serverName' : name ,
            'uuid'       : uuid ,
            'path'       : ('/mediabrowser/Shows/NextUp/?Userid=' + userid + '&Recursive=true&SortBy=DateCreated&Fields=Path,Overview,Genres,People,MediaStreams&SortOrder=Descending&Filters=IsUnplayed,IsNotFolder&IsVirtualUnaired=false&IsMissing=False&IncludeItemTypes=Episode&format=xml') ,
            'token'      : ''  ,
            'location'   : "local" ,
            'art'        : '' ,
            'local'      : '1' ,
            'type'       : "movie",
            'owned'      : '1' })            
            # Add Favorite Movies
    temp_list.append( {'title'      : 'Favorite Movies',
            'address'    : ip_address+":"+port ,
            'serverName' : name ,
            'uuid'       : uuid ,
            'path'       : ('/mediabrowser/Users/' + userid + '/Items?Recursive=true&SortBy=sortName&Fields=Path,Overview,Genres,People,MediaStreams&SortOrder=Descending&Filters=IsFavorite,IsNotFolder&IncludeItemTypes=Movie&format=xml') ,
            'token'      : ''  ,
            'location'   : "local" ,
            'art'        : '' ,
            'local'      : '1' ,
            'type'       : "movie",
            'owned'      : '1' })            

# Add Favorite Episodes
    temp_list.append( {'title'      : 'Favorite Episodes',
            'address'    : ip_address+":"+port ,
            'serverName' : name ,
            'uuid'       : uuid ,
            'path'       : ('/mediabrowser/Users/' + userid + '/Items?Limit=' + __settings__.getSetting("numRecentTV") +'&Recursive=true&SortBy=DateCreated&Fields=Path,Overview,Genres,People,MediaStreams&SortOrder=Descending&Filters=IsNotFolder,IsFavorite&IncludeItemTypes=Episode&format=xml') ,
            'token'      : ''  ,
            'location'   : "local" ,
            'art'        : '' ,
            'local'      : '1' ,
            'type'       : "movie",
            'owned'      : '1' })                       
            
# Add Upcoming TV
    temp_list.append( {'title'      : 'Upcoming TV',
            'address'    : ip_address+":"+port ,
            'serverName' : name ,
            'uuid'       : uuid ,
            'path'       : ('/mediabrowser/Users/' + userid + '/Items?Recursive=true&SortBy=PremiereDate&Fields=Path,Overview,Genres,People,MediaStreams&SortOrder=Ascending&Filters=IsUnplayed&IsVirtualUnaired=true&IsNotFolder&IncludeItemTypes=Episode&format=xml') ,
            'token'      : ''  ,
            'location'   : "local" ,
            'art'        : '' ,
            'local'      : '1' ,
            'type'       : "movie",
            'owned'      : '1' })                            
    #printDebug("Title " + str(BaseItemDto.tag))

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
    xbmc.executebuiltin("Container.Refresh")

def markUnwatched (url):
    headers={'Accept-encoding': 'gzip','Authorization' : 'MediaBrowser', 'Client' : 'Dashboard', 'Device' : "Chrome 31.0.1650.57", 'DeviceId' : "f50543a4c8e58e4b4fbb2a2bcee3b50535e1915e", 'Version':"3.0.5070.20258", 'UserId':"ff"}
    resp = requests.delete(url, data='', headers=headers)
    xbmc.executebuiltin("Container.Refresh")

def markFavorite (url):
    headers={'Accept-encoding': 'gzip','Authorization' : 'MediaBrowser', 'Client' : 'Dashboard', 'Device' : "Chrome 31.0.1650.57", 'DeviceId' : "f50543a4c8e58e4b4fbb2a2bcee3b50535e1915e", 'Version':"3.0.5070.20258", 'UserId':"ff"}
    resp = requests.post(url, data='', headers=headers)
    xbmc.executebuiltin("Container.Refresh")
    
def unmarkFavorite (url):
    headers={'Accept-encoding': 'gzip','Authorization' : 'MediaBrowser', 'Client' : 'Dashboard', 'Device' : "Chrome 31.0.1650.57", 'DeviceId' : "f50543a4c8e58e4b4fbb2a2bcee3b50535e1915e", 'Version':"3.0.5070.20258", 'UserId':"ff"}
    resp = requests.delete(url, data='', headers=headers)
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

def playall ():
    temp_list = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
    temp_list.clear()
    html=getURL(WINDOW.getProperty("currenturl"))
    tree = etree.fromstring(html).getiterator(sDto + "BaseItemDto")
    for BaseItemDto in tree:
        if(str(BaseItemDto.find(sDto + 'RecursiveItemCount').text)!='0'):
            u=(BaseItemDto.find(sDto + 'Path').text)
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
        headers={'Accept-encoding': 'gzip','Authorization' : 'MediaBrowser', 'Client' : 'Dashboard', 'Device' : "Chrome 31.0.1650.57", 'DeviceId' : "f50543a4c8e58e4b4fbb2a2bcee3b50535e1915e", 'Version':"3.0.5070.20258", 'UserId':"ff"}
        resp = requests.delete(url, data='', headers=headers)
        xbmc.sleep(8000)
        xbmc.executebuiltin("Container.Refresh")
def getURL( url, suppress=True, type="GET", popup=0 ):
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
        conn.request(type, urlPath)
        data = conn.getresponse()
        if int(data.status) == 200:
            link=data.read()
            printDebug("====== XML 200 returned =======")
            printDebug(link, False)
            printDebug("====== XML 200 finished ======")

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
            return False
        else:
            link=data.read()
            printDebug("====== XML returned =======")
            printDebug(link, False)
            printDebug("====== XML finished ======")
    except socket.gaierror :
        error = 'Unable to lookup host: ' + server + "\nCheck host name is correct"
        xbmc.log (error)
        if suppress is False:
            if popup==0:
                xbmc.executebuiltin("XBMC.Notification(\"XBMB3C\": URL error: Unable to find server,)")
            else:
                xbmcgui.Dialog().ok("","Unable to contact host")
        xbmc.log (error)
        return False
    except socket.error, msg :
        error="Unable to connect to " + server +"\nReason: " + str(msg)
        xbmc.log (error)
        if suppress is False:
            if popup == 0:
                xbmc.executebuiltin("XBMC.Notification(\"XBMB3C\": URL error: Unable to connect to server,)")
            else:
                xbmcgui.Dialog().ok("","Unable to connect to host")
        xbmc.log (error)
        return False
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
        
        WINDOW = xbmcgui.Window( 10000 )
        if WINDOW.getProperty("addshowname") == "true":
            if extraData.get('locationtype')== "Virtual":
                list=xbmcgui.ListItem(extraData.get('premieredate')+" - "+details.get('SeriesName','')+" - " +"S"+details.get('season')+"E"+details.get('title','Unknown'), iconImage=thumbPath, thumbnailImage=thumbPath)
            else:
                list=xbmcgui.ListItem(details.get('SeriesName','')+" - " +"S"+details.get('season')+"E"+details.get('title','Unknown'), iconImage=thumbPath, thumbnailImage=thumbPath)
        else:
            list=xbmcgui.ListItem(details.get('title','Unknown'), iconImage=thumbPath, thumbnailImage=thumbPath)
        printDebug("Setting thumbnail as " + thumbPath)
        #Set the properties of the item, such as summary, name, season, etc
        list.setInfo( type=extraData.get('type','Video'), infoLabels=details )

        #For all end items    
        if ( not folder):
            #list.setProperty('IsPlayable', 'true')

            if extraData.get('type','video').lower() == "video":
                list.setProperty('TotalTime', str(extraData.get('duration')))
                list.setProperty('ResumeTime', str(extraData.get('resume')))
            

                

        #Set the fanart image if it has been enabled
        fanart=str(extraData.get('fanart_image',''))
        if '?' in fanart:
            list.setProperty('fanart_image', fanart)
        else:
            list.setProperty('fanart_image', fanart)

        printDebug( "Setting fan art as " + fanart )

        #if extraData.get('banner'):
        #    list.setProperty('banner', extraData.get('banner'))
        #    printDebug( "Setting banner as " + extraData.get('banner'))

        printDebug("Building Context Menus")
        commands = []
        watched=extraData.get('watchedurl')
        if watched != None:
            scriptToRun = PLUGINPATH + "/default.py"
            if extraData.get('playcount')=='0':
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
            argsToPass = 'playall'
            commands.append(( __language__(30041), "XBMC.RunScript(" + scriptToRun + ", " + argsToPass + ")", ))            
            #argsToPass = 'xbmc.Container.Update()'
            commands.append(( __language__(30042), "XBMC.RunScript(" + scriptToRun + ", " + argsToPass + ")", ))
            argsToPass = 'delete,' + extraData.get('deleteurl')
            commands.append(( __language__(30043), "XBMC.RunScript(" + scriptToRun + ", " + argsToPass + ")", ))
            list.addContextMenuItems( commands, g_contextReplace )

        list.setInfo('video', {'duration' : extraData.get('duration')})
        list.setInfo('video', {'playcount' : extraData.get('playcount')})
        if extraData.get('favorite')=='true':
            list.setInfo('video', {'top250' : '1'})
        if extraData.get('totaltime') != None:
            list.setProperty('TotalTime', extraData.get('totaltime'))
            list.setProperty('ResumeTime', str(int(extraData.get('resumetime'))/60))
        list.setInfo('video', {'director' : extraData.get('director')})
        list.setInfo('video', {'writer' : extraData.get('writer')})
        list.setInfo('video', {'year' : extraData.get('year')})
        list.setInfo('video', {'genre' : extraData.get('genre')})
        #list.setInfo('video', {'cast' : extraData.get('cast')}) --- Broken in Frodo
        #list.setInfo('video', {'castandrole' : extraData.get('cast')}) --- Broken in Frodo
        list.setInfo('video', {'plotoutline' : extraData.get('cast')}) # Hack to get cast data into skin
        list.setInfo('video', {'episode': details.get('episode')})
        list.setInfo('video', {'season': details.get('season')})        
        list.setInfo('video', {'mpaa': extraData.get('mpaa')})
        list.setInfo('video', {'rating': extraData.get('rating')})
        if watched!=None:
            list.setProperty('watchedurl', extraData.get('watchedurl'))
        list.addStreamInfo('video', {'duration': extraData.get('duration'), 'aspect': extraData.get('aspectratio'),'codec': extraData.get('videocodec'), 'width' : extraData.get('width'), 'height' : extraData.get('height')})
        list.addStreamInfo('audio', {'codec': extraData.get('audiocodec'),'channels': extraData.get('channels')})
        xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_NONE  )
        return xbmcplugin.addDirectoryItem(handle=pluginhandle,url=u,listitem=list,isFolder=True)

def displaySections( filter=None, shared=False ):
        printDebug("== ENTER: displaySections() ==", False)
        xbmcplugin.setContent(pluginhandle, 'files')
        ds_servers=discoverAllServers()
        numOfServers=len(ds_servers)
        printDebug( "Using list of "+str(numOfServers)+" servers: " +  str(ds_servers))
        
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
            addGUIItem(s_url, details,extraData)

        if shared:
            xbmcplugin.endOfDirectory(pluginhandle,cacheToDisc=False)
            return
                    
        #For each of the servers we have identified
        allservers=ds_servers
        numOfServers=len(allservers)

        #All XML entries have been parsed and we are ready to allow the user to browse around.  So end the screen listing.
        xbmcplugin.endOfDirectory(pluginhandle,cacheToDisc=False)

def remove_html_tags( data ):
    p = re.compile(r'<.*?>')
    return p.sub('', data)

def PLAY( url ):
        printDebug("== ENTER: PLAY ==", False)
        url=urllib.unquote(url)
        server,id=url.split(',;')
        ip,port=server.split(':')
        userid=getUserId(ip,port)
        seekTime=0
        resume=0

        html=getURL("http://" + server + "/mediabrowser/Users/" + userid + "/Items/" + id + "?format=xml", suppress=False, popup=1 )        
        if __settings__.getSetting('playFromStream')=='false':
            html=getURL("http://" + server + "/mediabrowser/Users/" + userid + "/Items/" + id + "?format=xml", suppress=False, popup=1 )
            playurl= etree.fromstring(html).find(sDto+"Path").text
            if __settings__.getSetting('smbusername')=='':
                playurl=playurl.replace("\\\\","smb://")
            else:
                playurl=playurl.replace("\\\\","smb://"+__settings__.getSetting('smbusername')+':'+__settings__.getSetting('smbpassword')+'@')
            playurl=playurl.replace("\\","/")
        else:
            if __settings__.getSetting('transcode')=='true':
                playurl='http://' + server + '/mediabrowser/Videos/' + id + '/stream.ts'
            else:
                playurl='http://' + server + '/mediabrowser/Videos/' + id + '/stream?static=true'
                
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
        UserData=etree.fromstring(html).find(sDto+'UserData')
        if UserData.find(sDto + "PlaybackPositionTicks").text != '0' and __settings__.getSetting('transcode')=='false':
            reasonableTicks=int(UserData.find(sDto + "PlaybackPositionTicks").text)/1000
            seekTime=reasonableTicks/10000
            displayTime = str(datetime.timedelta(seconds=seekTime))
            display_list = [ "Resume from " + displayTime , "Start from beginning"]
            resumeScreen = xbmcgui.Dialog()
            result = resumeScreen.select('Resume',display_list)
            if result == -1:
                return False
            if result == 0:
                resume=1

        xbmc.Player().play(playurl,item)
        #xbmcplugin.setResolvedUrl(pluginhandle, True, item)
        WINDOW = xbmcgui.Window( 10000 )
        WINDOW.setProperty("watchedurl", watchedurl)
        WINDOW.setProperty("positionurl", positionurl)
        WINDOW.setProperty("runtimeticks", str(etree.fromstring(html).find(sDto+"RunTimeTicks").text))

        #Set a loop to wait for positive confirmation of playback
        count = 0
        while not xbmc.Player().isPlaying():
            printDebug( "Not playing yet...sleep for 2")
            count = count + 2
            if count >= 20:
                return
            else:
                time.sleep(1)
        if resume==1:
            while xbmc.Player().getTime()<(seekTime-1):
                xbmc.Player().pause
                xbmc.sleep(100)
                xbmc.Player().seekTime(seekTime-1)
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
    html=getURL(url, suppress=False, popup=1 )

    if html is False:
        return
    tree = etree.fromstring(html).getiterator(sDto + "BaseItemDto")
    processDirectory(url,tree)
    return

def processDirectory( url, tree=None ):
    printDebug("== ENTER: processDirectory ==", False)
    parsed = urlparse(url)
    parsedserver,parsedport=parsed.netloc.split(':')
    userid=getUserId(parsedserver,parsedport)
    printDebug("Processing secondary menus")
    xbmcplugin.setContent(pluginhandle, 'movies')

    server=getServerFromURL(url)
    setWindowHeading(url)
    for directory in tree:
        try:
            tempTitle=((directory.find(sDto + 'Name').text)).encode('utf-8')
        except TypeError:
            tempTitle="Missing Title"
        id=str(directory.find(sDto + 'Id').text).encode('utf-8')
        isFolder=str(directory.find(sDto + 'IsFolder').text).encode('utf-8')
        type=str(directory.find(sDto + 'Type').text).encode('utf-8')
        try:
            tempEpisode=directory.find(sDto + "IndexNumber").text
            if int(tempEpisode)<10:
                tempEpisode='0'+tempEpisode
            tempSeason=directory.find(sDto + "ParentIndexNumber").text
        except TypeError:
            tempEpisode=''
            tempSeason=''
        if directory.find(sDto + "DisplayMediaType").text=='Episode':
            tempTitle=tempEpisode+' - '+tempTitle
            xbmcplugin.setContent(pluginhandle, 'episodes')
        if directory.find(sDto + "DisplayMediaType").text=='Season':
            xbmcplugin.setContent(pluginhandle, 'tvshows')
        if directory.find(sDto + "DisplayMediaType").text=='Audio':
            xbmcplugin.setContent(pluginhandle, 'songs')            
        if directory.find(sDto + "DisplayMediaType").text=='Series':
            xbmcplugin.setContent(pluginhandle, 'tvshows')            
# Process MediaStreams
        channels=''
        videocodec=''
        audiocodec=''
        height=''
        width=''
        aspectratio='1:1'
        aspectfloat=1.85
        MediaStreams=directory.find(sDto+'MediaStreams')
        for MediaStream in MediaStreams.findall(sEntities + 'MediaStream'):
            if(MediaStream.find(sEntities + 'Type').text=='Video'):
                videocodec=MediaStream.find(sEntities + 'Codec').text
                height=MediaStream.find(sEntities + 'Height').text
                width=MediaStream.find(sEntities + 'Width').text
                aspectratio=MediaStream.find(sEntities + 'AspectRatio').text
                if aspectratio != None:
                    aspectwidth,aspectheight=aspectratio.split(':')
                    aspectfloat=float(aspectwidth)/float(aspectheight)
            if(MediaStream.find(sEntities + 'Type').text=='Audio'):
                audiocodec=MediaStream.find(sEntities + 'Codec').text
                channels=MediaStream.find(sEntities + 'Channels').text
# Process People
        director=''
        writer=''
        cast=''
        People=directory.find(sDto+'People')
        for BaseItemPerson in People.findall(sDto+'BaseItemPerson'):
            if(BaseItemPerson.find(sDto+'Type').text=='Director'):
                director=director + BaseItemPerson.find(sDto + 'Name').text + ' ' 
            if(BaseItemPerson.find(sDto+'Type').text=='Writing'):
                writer=(BaseItemPerson.find(sDto + 'Name').text)                
            if(BaseItemPerson.find(sDto+'Type').text=='Actor'):
                Name=(BaseItemPerson.find(sDto + 'Name').text)
                Role=(BaseItemPerson.find(sDto + 'Role').text)
                if Role==None:
                    Role=''
                if cast=='':
                    cast=Name+' as '+Role
                else:
                    cast=cast+'\n'+Name+' as '+Role
# Process Genres
        genre=''
        Genres=directory.find(sDto+'Genres')
        for string in Genres.findall(sArrays+'string'):
            if genre=="": #Just take the first genre
                genre=string.text
            else:
                genre=genre+" / "+string.text
                
# Process UserData
        UserData=directory.find(sDto+'UserData')
        if UserData.find(sDto + "PlayCount").text != '0':
            overlay='7'
            watched='true'
        else:
            overlay='6'
            watched='false'
        if UserData.find(sDto + "IsFavorite").text == 'true':
            overlay='5'
            favorite='true'
        else:
            favorite='false'
        if UserData.find(sDto + "PlaybackPositionTicks").text != None:
            PlaybackPositionTicks=str(UserData.find(sDto + "PlaybackPositionTicks").text)
            reasonableTicks=int(UserData.find(sDto + "PlaybackPositionTicks").text)/1000
            seekTime=reasonableTicks/10000
        else:
            PlaybackPositionTicks='100'

# Populate the details list
        details={'title'        : tempTitle,
                 'plot'         : directory.find(sDto + "Overview").text ,
                 'episode'      : tempEpisode,
                 #'watched'      : watched,
                 'Overlay'      : overlay,
                 'playcount'    : UserData.find(sDto + "PlayCount").text,
                 #'aired'       : episode.get('originallyAvailableAt','') ,
                 'SeriesName'  :  directory.find(sDto + "SeriesName").text
                 
                 
                 ,
                 'season'       : tempSeason
                 }
        try:
            tempDuration=str(int(directory.find(sDto + "RunTimeTicks").text)/(10000000*60))
            RunTimeTicks=str(directory.find(sDto + "RunTimeTicks").text)
        except TypeError:
            tempDuration='100'
            RunTimeTicks='100'
        
        if((directory.find(sDto + "PremiereDate").text) != None):
            premieredatelist=(directory.find(sDto + "PremiereDate").text).split("T")
            premieredate=premieredatelist[0]
        else:
            premieredate=""

# Populate the extraData list
        extraData={'thumb'        : getThumb(directory, server) ,
                   'fanart_image' : getFanart(directory, server) ,
                   'mpaa'         : directory.find(sDto + "OfficialRating").text ,
                   'rating'       : directory.find(sDto + "CommunityRating").text,
                   'year'         : directory.find(sDto + "ProductionYear").text,
                   'locationtype' : directory.find(sDto + "LocationType").text,
                   'premieredate' : premieredate,
                   'genre'        : genre,
                   'playcount'    : UserData.find(sDto + "PlayCount").text,
                   'director'     : director,
                   'writer'       : writer,
                   'channels'     : channels,
                   'videocodec'   : videocodec,
                   'aspectratio'  : aspectfloat,
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
                   'duration'     : tempDuration}
        if extraData['thumb'] == '':
            extraData['thumb']=extraData['fanart_image']

        extraData['mode']=_MODE_GETCONTENT
        
        if isFolder=='true':
            if type=='Season' or type=='BoxSet' or type=='MusicAlbum' or type=='MusicArtist':
                u= 'http://' + server + '/mediabrowser/Users/'+ userid + '/items?ParentId=' +id +'&IsVirtualUnAired=false&IsMissing=false&Fields=Path,Overview,Genres,People,MediaStreams&SortBy='+__settings__.getSetting('sortby')+'&format=xml'
                if (str(directory.find(sDto + 'RecursiveItemCount').text).encode('utf-8')!='0'):
                    addGUIItem(u,details,extraData)
            else:
                if __settings__.getSetting('autoEnterSingle')=='true':
                    if directory.find(sDto + 'ChildCount').text=='1':
                        newid=findChildId('http://' + server + '/mediabrowser/Users/'+ userid + '/items?ParentId=' +id +'&IsVirtualUnAired=false&IsMissing=false&Fields=Path,Overview,Genres,People,MediaStreams&SortBy='+__settings__.getSetting('sortby')+'&format=xml')
                        if newid!=None:
                            id=newid
                u= 'http://' + server + '/mediabrowser/Users/'+ userid + '/items?ParentId=' +id +'&IsVirtualUnAired=false&IsMissing=false&Fields=Path,Overview,Genres,People,MediaStreams&SortBy='+__settings__.getSetting('sortby')+'&format=xml'

                if (str(directory.find(sDto + 'RecursiveItemCount').text).encode('utf-8')!='0'):
                    addGUIItem(u,details,extraData)

        else:
            u=server+',;'+id
            addGUIItem(u,details,extraData,folder=False)
        
    xbmcplugin.endOfDirectory(pluginhandle,cacheToDisc=False)

def findChildId(u):
    html=getURL(u)
    tree = etree.fromstring(html).getiterator(sDto + "BaseItemDto")
    for BaseItemDto in tree:
        return(BaseItemDto.find(sDto + 'Id').text)

def getThumb( data, server, transcode=False, width=None, height=None ):
    '''
        Simply take a URL or path and determine how to format for images
        @ input: elementTree element, server name
        @ return formatted URL
    '''
    
    printDebug('getThumb server:' + server)
    id=data.find(sDto + 'Id').text
    if data.find(sDto + 'DisplayMediaType').text == 'Episode':
        id=data.find(sDto + 'SeriesId').text
    thumbnail=('http://'+server+'/mediabrowser/Items/'+str(id)+'/Images/Primary?Format=png')
    printDebug('The temp path is:' + __addondir__)
    from urllib import urlretrieve
    try:
      with open(__addondir__ + id + '.png'):
         printDebug('Already there')
    except IOError:
         urlretrieve(thumbnail, (__addondir__ + id+ '.png'))
    thumbnail=(__addondir__ + id + '.png')
    printDebug('Thumb:' + thumbnail)
    return thumbnail
    


    if thumbnail == '':
        return g_loc+'/resources/mb3.png'

    elif thumbnail[0:4] == "http" :
        return thumbnail

    elif thumbnail[0] == '/':
        if transcode:
            return photoTranscode(server,'http://localhost:32400'+thumbnail,width,height)
        else:
            return 'http://'+server+thumbnail

    else:
        return g_loc+'/resources/mb3.png'

def getFanart( data, server, transcode=False ):
    '''
        Simply take a URL or path and determine how to format for fanart
        @ input: elementTree element, server name
        @ return formatted URL for photo resizing
    '''
    id=data.find(sDto + 'Id').text
    if data.find(sDto + 'DisplayMediaType').text == 'Episode' or data.find(sDto + 'DisplayMediaType').text == 'Season':
        id=data.find(sDto + 'SeriesId').text    
    fanart=('http://'+server+'/mediabrowser/Items/'+str(id)+'/Images/Backdrop?Format=png')
    from urllib import urlretrieve
    try:
      with open(__addondir__+'fanart_' + id + '.png'):
         printDebug('Already there')
    except IOError:
         urlretrieve(fanart, (__addondir__+'fanart_' + id+ '.png'))
    fanart=(__addondir__+'fanart_' + id + '.png')
    printDebug('Fanart:' + fanart)
    return fanart

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

    #For each of the servers we have identified
    for mediaserver in Servers.values():

        details={'title' : mediaserver.get('serverName','Unknown') }

        if mediaserver.get('token',None):
            extraData={'token' : mediaserver.get('token') }
        else:
            extraData={}

        addGUIItem(s_url, details, extraData )

    xbmcplugin.endOfDirectory(pluginhandle,cacheToDisc=False)

def setWindowHeading(url) :
    WINDOW = xbmcgui.Window( 10000 )
    WINDOW.setProperty("addshowname", "false")
    WINDOW.setProperty("currenturl",url)
    WINDOW.setProperty("currentpluginhandle",str(pluginhandle))
    if 'ParentId' in url:
        dirUrl=url.replace('items?ParentId=','Items/')
        splitUrl=dirUrl.split('&')
        dirUrl=splitUrl[0]+'?format=xml'
        html=getURL(dirUrl)
        tree= etree.fromstring(html).getiterator(sDto + 'BaseItemDto')
        for BaseItemDto in tree:
            title=(BaseItemDto.find(sDto + 'Name').text)
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
try:
    params=get_params(sys.argv[2])
except:
    params={}

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
    #xbmc.executebuiltin("Container.Update(plugin://plugin.video.xbmb3c/?url="+WINDOW.getProperty('currenturl')+","replace")")
elif sys.argv[1] == "sortby":
    sortby()
elif sys.argv[1] == "sortorder":
    sortorder()
elif sys.argv[1] == "genrefilter":
    genrefilter()
elif sys.argv[1] == "playall":
    playall()    
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
        getContent(param_url)

    elif mode == _MODE_BASICPLAY:
        PLAY(param_url)
xbmc.log ("===== XBMB3C STOP =====")

#clear done and exit.
sys.modules.clear()

