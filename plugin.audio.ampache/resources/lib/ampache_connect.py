from future import standard_library
from future.utils import PY2
standard_library.install_aliases()
from builtins import str
from builtins import object
import hashlib
import ssl
import socket
import time
import urllib.request, urllib.parse, urllib.error
import xbmc, xbmcaddon
import sys
import xml.etree.ElementTree as ET

from resources.lib import json_storage
from resources.lib import utils as ut

class AmpacheConnect(object):
    
    class ConnectionError(Exception):
        pass
    
    def __init__(self):
        self._ampache = xbmcaddon.Addon()
        jsStorServer = json_storage.JsonStorage("servers.json")
        serverStorage = jsStorServer.getData()
        self._connectionData = serverStorage["servers"][serverStorage["current_server"]]
        #self._connectionData = None
        self.filter=None
        self.add=None
        self.limit=None
        self.offset=None
        self.type=None
        self.exact=None 
        self.mode=None
        self.id=None
        self.rating=None

    def getBaseUrl(self):
        return '/server/xml.server.php'

    def getHashedPassword(self,timeStamp):
        enablePass = self._connectionData["enable_password"]
        if enablePass:
            sdf = self._connectionData["password"]
        else:
            sdf = ""
        hasher = hashlib.new('sha256')
        sdf = sdf.encode()
        hasher.update(sdf)
        myKey = hasher.hexdigest()
        hasher = hashlib.new('sha256')
        timeK = timeStamp + myKey
        timeK = timeK.encode()
        hasher.update(timeK)
        passwordHash = hasher.hexdigest()
        return passwordHash

    def get_user_pwd_login_url(self,nTime):
        myTimeStamp = str(nTime)
        myPassphrase = self.getHashedPassword(myTimeStamp)
        myURL = self._connectionData["url"] + self.getBaseUrl() + '?action=handshake&auth='
        myURL += myPassphrase + "&timestamp=" + myTimeStamp
        myURL += '&version=' + self._ampache.getSetting("api-version") + '&user=' + self._connectionData["username"]
        return myURL

    def get_auth_key_login_url(self):
        myURL = self._connectionData["url"] +  self.getBaseUrl() + '?action=handshake&auth='
        myURL += self._connectionData["api_key"]
        myURL += '&version=' + self._ampache.getSetting("api-version")
        return myURL

    def handle_request(self,url):
        xbmc.log("AmpachePlugin::handle_request: url " + url, xbmc.LOGDEBUG)
        ssl_certs_str = self._ampache.getSetting("disable_ssl_certs")
        try:
            req = urllib.request.Request(url)
            if ut.strBool_to_bool(ssl_certs_str):
                gcontext = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
                response = urllib.request.urlopen(req, context=gcontext, timeout=400)
                xbmc.log("AmpachePlugin::handle_request: ssl",xbmc.LOGDEBUG)
            else:
                response = urllib.request.urlopen(req, timeout=400)
                xbmc.log("AmpachePlugin::handle_request: nossl",xbmc.LOGDEBUG)
        except urllib.error.HTTPError as e:
            xbmc.log("AmpachePlugin::handle_request: HTTPError " +\
                    repr(e),xbmc.LOGDEBUG)
            xbmc.executebuiltin("ConnectionError" )
            raise self.ConnectionError
        except urllib.error.URLError as e:
            xbmc.log("AmpachePlugin::handle_request: URLError " +\
                    repr(e),xbmc.LOGDEBUG)
            xbmc.executebuiltin("ConnectionError" )
            raise self.ConnectionError
        except Exception  as e:
            xbmc.log("AmpachePlugin::handle_request: Generic Error "  +\
                    repr(e),xbmc.LOGDEBUG)
            xbmc.executebuiltin("ConnectionError" )
            raise self.ConnectionError
        headers = response.headers
        contents = response.read()
        response.close()
        return headers,contents

    def AMPACHECONNECT(self,showok=False):
        amp_notif = ""
        version = 350001
        socket.setdefaulttimeout(3600)
        nTime = int(time.time())
        use_api_key = self._connectionData["use_api_key"]
        if ut.strBool_to_bool(use_api_key):
            xbmc.log("AmpachePlugin::AMPACHECONNECT api_key",xbmc.LOGDEBUG)
            myURL = self.get_auth_key_login_url()
        else: 
            xbmc.log("AmpachePlugin::AMPACHECONNECT login password",xbmc.LOGDEBUG)
            myURL = self.get_user_pwd_login_url(nTime)
        try:
            headers,contents = self.handle_request(myURL)
        except self.ConnectionError:
            xbmc.log("AmpachePlugin::AMPACHECONNECT ConnectionError",xbmc.LOGDEBUG)
            amp_notif = "Notification(" + ut.tString(30198)  +  "," +\
                    ut.tString(30202)   + ")"
            #connection error
            xbmc.executebuiltin(amp_notif)
            raise self.ConnectionError
        except Exception  as e:
            xbmc.log("AmpachePlugin::AMPACHECONNECT: Generic Error "  +\
                    repr(e),xbmc.LOGDEBUG)
        xbmc.log("AmpachePlugin::AMPACHECONNECT ConnectionOk",xbmc.LOGDEBUG)
        try:
            xbmc.log("AmpachePlugin::AMPACHECONNECT: contents " +\
                    contents.decode(),xbmc.LOGDEBUG)
        except Exception as e:
            xbmc.log("AmpachePlugin::AMPACHECONNECT: unable to print contents " + \
                   repr(e) , xbmc.LOGDEBUG)
        tree=ET.XML(contents)
        errormess = tree.findtext('error')
        if errormess:
            errornode = tree.find("error")
            if errornode.attrib["code"]=="401":
                if "time" in errormess:
                    amp_notif = "Notification(" + ut.tString(30198)   +\
                            "," + ut.tString(30204) + ")"
                    #permission error, check password or api_key
                    xbmc.executebuiltin(amp_notif)
                else:
                    amp_notif = "Notification(" + ut.tString(30198)   +\
                            "," + ut.tString(30202)  + ")"
                    #connection error
                    xbmc.executebuiltin(amp_notif)
            raise self.ConnectionError
            return
        if showok:
                #use it only if notification of connection is necessary, like
                #switch server, display connection ok and the name of the
                #current server
                amp_notif = "Notification(" + ut.tString(30197)   +\
                        "," + ut.tString(30203) + "\n" + ut.tString(30181) +\
                        " : " + self._connectionData["name"] + ")"
                #connection ok
                xbmc.executebuiltin(amp_notif)
        token = tree.findtext('auth')
        version = tree.findtext('api')
        if not version:
        #old api
            version = tree.findtext('version')
        #setSettings only string or unicode
        self._ampache.setSetting("api-version",version)
        self._ampache.setSetting("artists", tree.findtext("artists"))
        self._ampache.setSetting("albums", tree.findtext("albums"))
        self._ampache.setSetting("songs", tree.findtext("songs"))
        self._ampache.setSetting("playlists", tree.findtext("playlists"))
        self._ampache.setSetting("add", tree.findtext("add"))
        self._ampache.setSetting("token", token)
        self._ampache.setSetting("token-exp", str(nTime+24000))
        return

    #handle request to the xml api that return binary files
    def ampache_binary_request(self,action):
        thisURL = self.build_ampache_url(action)
        try:
            headers,contents  = self.handle_request(thisURL)
        except self.ConnectionError:
            raise self.ConnectionError
        return headers,contents
   
    #handle request to the xml api that return xml content
    def ampache_http_request(self,action):
        thisURL = self.build_ampache_url(action)
        try:
            headers,contents  = self.handle_request(thisURL)
        except self.ConnectionError:
            raise self.ConnectionError
        if PY2:
            contents = contents.replace("\0", "")
        #parser = ET.XMLParser(recover=True)
        #tree=ET.XML(contents, parser = parser)
        try:
            xbmc.log("AmpachePlugin::ampache_http_request: contents " + \
                    contents.decode(),xbmc.LOGDEBUG)
        except Exception as e:
            xbmc.log("AmpachePlugin::ampache_http_request: unable print contents " + \
                    repr(e) , xbmc.LOGDEBUG)
        tree=ET.XML(contents)
        if tree.findtext("error"):
            errornode = tree.find("error")
            if errornode.attrib["code"]=="401":
                try:
                    self.AMPACHECONNECT()
                except self.ConnectionError:
                    raise self.ConnectionError
                thisURL = self.build_ampache_url(action)
                try:
                    headers,contents = self.handle_request(thisURL)
                except self.ConnectionError:
                    raise self.ConnectionError
                tree=ET.XML(contents)
            elif errornode.attrib["code"]=="400":
                xbmc.log("AmpachePlugin::ampache_http_request Bad Request",xbmc.LOGDEBUG)
            elif errornode.attrib["code"]=="404":
                xbmc.log("AmpachePlugin::ampache_http_request Not Found",xbmc.LOGDEBUG)

        return tree
    
    def build_ampache_url(self,action):
        if ut.check_tokenexp():
            xbmc.log("refreshing token...", xbmc.LOGDEBUG )
            try:
                self.AMPACHECONNECT()
            except:
                return
        token = self._ampache.getSetting("token")
        thisURL = self._connectionData["url"] +  self.getBaseUrl() + '?action=' + action
        thisURL += '&auth=' + token
        if self.limit:
            thisURL += '&limit=' +str(self.limit)
        if self.offset:
            thisURL += '&offset=' +str(self.offset)
        if self.filter:
            thisURL += '&filter=' +urllib.parse.quote_plus(str(self.filter))
        if self.add:
            thisURL += '&add=' + self.add
        if self.type:
            thisURL += '&type=' + self.type
        if self.mode:
            thisURL += '&mode=' + self.mode
        if self.exact:
            thisURL += '&exact=' + self.exact
        if self.id:
            thisURL += '&id=' + self.id
        if self.rating:
            thisURL += '&rating=' + self.rating
        return thisURL

