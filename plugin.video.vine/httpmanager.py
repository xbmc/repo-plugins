# -*- coding: utf-8 -*-
import os
import time
import sys
import codecs

import urllib, urllib2
import httplib
import socket
import gzip
import StringIO
import random
import glob
import re

import xbmc
import utils

#TODO Separate HTTP and Cache classes. Separate subclasses for Post Binary and regular
#==============================================================================
class HttpManager:

    def __init__(self):
        self.getFromCache = True
        self.gotFromCache = False
        self.cacheDir = u""
        self.cacheSize = 20
        self.lastCode = -1
        self.forwardedForIP = None
        self.DisableForwardedForIP()
        self.proxyConfig = None
        
        self.defaultHeaders = {}
        
        if hasattr(sys.modules["__main__"], "log"):
            self.log = sys.modules["__main__"].log
        else:
            from utils import log
            self.log = log
            

    def SetOpener(self, opener):
        urllib2.install_opener(opener)
        
    def EnableForwardedForIP(self):
        self.isForwardedForIP = True

    def DisableForwardedForIP(self):
        self.isForwardedForIP = False

    def GetIsForwardedForIP(self):
        return self.isForwardedForIP

    def GetForwardedForIP(self):
        return self.forwardedForIP


    def SetForwardedForIP(self, ip):
        self.forwardedForIP = ip

    def SetDefaultHeaders(self, headers):
        self.defaultHeaders = headers

    def SetProxyConfig(self, proxyConfig):
        self.proxyConfig = proxyConfig

    """
    Use the given maxAge on cache attempt. If this attempt fails then try again with maxAge = 0 (don't retrieve from cache)
    """
    def ifCacheMaxAge(self, maxAge):
        if self.getFromCache:
            return maxAge

        return 0

    """
     Log level is debug if we are processes a page from the cache, 
     because we don't want to display errors or halt processing 
     unless we are processing a page directly from the web
    """
    def ifCacheLevel(self, logLevel):
        self.log(u"self: %s" % unicode(self))
        self.log(u"ifCacheLevel(%s)" % unicode(logLevel))
        self.log(u"ifCacheLevel self.getFromCache: %s" % unicode(self.getFromCache))
        if self.getFromCache and self.getGotFromCache():
            self.log(u"return xbmc.LOGDEBUG")
            return xbmc.LOGDEBUG;

        self.log(u"ifCacheLevel return logLevel: %s" % unicode(logLevel))
        return logLevel

    def setGetFromCache(self, getFromCache):
        self.log(u"self: %s" % unicode(self))
        self.getFromCache = getFromCache
        self.log(u"setGetFromCache(%s)" % unicode(self.getFromCache))

    def getGetFromCache(self):
        return self.getFromCache


    def getGotFromCache(self):
        return self._Cache_GetFromFlag()

    def PostBinary(self, site, path, data, headers = None):
        self.log(u"(%s)" % (site + path), xbmc.LOGDEBUG)
        
        try:
            if self.proxyConfig is not None: 
                self.proxyConfig.Enable()
                
            repeat = True
            firstTime = True
            addon = sys.modules[u"__main__"].addon
    
            while repeat:
                repeat = False
                try:
                    if site.startswith(u"http://"):
                        site = site[7:]
                    
                    headers = self.PrepareHeaders(addon, headers)
    
                    self.log(u"headers: " + repr(headers))
                    
                    conn = httplib.HTTPConnection(site)
                    conn.request("POST", path, data, headers)
                    response = conn.getresponse()
                except ( httplib.HTTPException ) as exception:
                    self.log ( u'HTTPError: ' + unicode(exception), xbmc.LOGERROR)
                    raise exception
                except ( socket.timeout ) as exception:
                    self.log ( u'Timeout exception: ' + unicode(exception), xbmc.LOGERROR )
                    if firstTime:
                        self.log ( u'Timeout exception: ' + unicode(exception), xbmc.LOGERROR )
                        xbmc.executebuiltin(u'XBMC.Notification(%s, %s)' % (u'Socket timed out', 'Trying again'))
                        repeat = True
                    else:
                        """
                        The while loop is normally only processed once.
                        When a socket timeout happens it executes twice.
                        The following code executes after the second timeout.
                        """
                        self.log ( u'Timeout exception: ' + unicode(exception) + ", if you see this msg often consider changing your Socket Timeout settings", xbmc.LOGERROR )
                        raise exception
        
                    firstTime = False
        except ( Exception ) as exception:
            raise exception
        finally:
            if self.proxyConfig is not None: 
                self.proxyConfig.Disable()
    
        self.log (u"response.status: " + unicode(response.status), xbmc.LOGDEBUG)
        
        if response.getheader(u'content-encoding', u'') == u'gzip':
            self.log (u"gzipped page", xbmc.LOGDEBUG)
            gzipper = gzip.GzipFile(fileobj=StringIO.StringIO(response.read()))
            return gzipper.read()
        
        return response.read()

    def GetHttpLibResponse(self, site, path, headers = None):
        self.log(u"(%s)" % (site + path), xbmc.LOGDEBUG)

        try:
            if self.proxyConfig is not None: 
                self.proxyConfig.Enable()
            repeat = True
            firstTime = True
            addon = sys.modules["__main__"].addon
    
            while repeat:
                repeat = False
                try:
                    if site.startswith("http://"):
                        site = site[7:]
                    
                    headers = self.PrepareHeaders(addon, headers)
    
                    self.log("headers: " + repr(headers))
                    
                    conn = httplib.HTTPConnection(site)
                    conn.request("GET", path, headers = headers)
                    #conn.putheader('Connection','Keep-Alive')
                    response = conn.getresponse()
                except ( httplib.HTTPException ) as exception:
                    self.log ( u'HTTPError: ' + unicode(exception), xbmc.LOGERROR)
                    raise exception
                except ( socket.timeout ) as exception:
                    self.log ( u'Timeout exception: ' + unicode(exception), xbmc.LOGERROR )
                    if firstTime:
                        self.log ( u'Timeout exception: ' + unicode(exception), xbmc.LOGERROR )
                        xbmc.executebuiltin(u'XBMC.Notification(%s, %s)' % (u'Socket timed out', 'Trying again'))
                        repeat = True
                    else:
                        """
                        The while loop is normally only processed once.
                        When a socket timeout happens it executes twice.
                        The following code executes after the second timeout.
                        """
                        self.log ( u'Timeout exception: ' + unicode(exception) + ", if you see this msg often consider changing your Socket Timeout settings", xbmc.LOGERROR )
                        raise exception
        
                    firstTime = False
        except ( Exception ) as exception:
            raise exception
        finally:
            if self.proxyConfig is not None: 
                self.proxyConfig.Disable()

        self.log (u"response.status: " + unicode(response.status), xbmc.LOGDEBUG)
        
        return response

    def GetViaHttpLib(self,  url, path, headers):
        response = self.GetHttpLibResponse(url, path, headers)

        if response.getheader(u'content-encoding', u'') == u'gzip':
            self.log (u"gzipped page", xbmc.LOGDEBUG)
            gzipper = gzip.GzipFile(fileobj=StringIO.StringIO(response.read()))
            return gzipper.read()
        
        return response.read()
        
    
    """
    Get url from cache iff 'getFromCache' is True, otherwise get directly from web (maxAge = 0)
    If the page was not in the cache then set cacheAttempt to False, indicating that the page was
    retrieved from the web
    """
    def GetWebPage(self, url, maxAge, values = None, headers = None, logUrl = True):
        if logUrl:
            self.log(u"GetWebPage(%s)" % url, xbmc.LOGDEBUG)
        maxAge = self.ifCacheMaxAge(maxAge)
        self.gotFromCache = False
        return self.GetURL( url, maxAge, values, headers, logUrl )

    #==============================================================================
    
    def GetWebPageDirect(self, url, values = None, headers = None, logUrl = True):
        self.log(u"GetWebPageDirect(%s)" % url, xbmc.LOGDEBUG)
        return self.GetWebPage(url, 0, values, headers, logUrl)

    #==============================================================================
    
    def GetLastCode(self):
        return lastCode
    
    #==============================================================================
    
    def SetCacheDir(self,  cacheDir ):
        self.log (u"cacheDir: " + cacheDir, xbmc.LOGDEBUG)    
        self.cacheDir = cacheDir
        if not os.path.isdir(cacheDir):
            os.makedirs(cacheDir)
    
    #==============================================================================
    def _Cache_GetFromFlag(self):
        self.log(u"_Cache_GetFromFlag() - gotFromCache = %s" % unicode(self.gotFromCache))
        return self.gotFromCache
    
    def _CheckCacheDir(self):
        if ( self.cacheDir == u'' ):
            return False
    
        return True
    
    #==============================================================================
    def GetCharset(self, response):
        if u'content-type' in response.info():
            contentType = response.info()[u'content-type']
            self.log (u"content-type: " + contentType, xbmc.LOGDEBUG)

            typeItems = contentType.split('; ')
            pattern = "charset=(.+)"
            for item in typeItems:
                try:
                    match = re.search(pattern, item, re.DOTALL | re.IGNORECASE)
                    return match.group(1)
                except:
                    pass
        
        return None
                
    
    #==============================================================================
    def GetMaxAge(self, response):
        if u'cache-control' in response.info():
            cacheControl = response.info()[u'cache-control']
            self.log (u"cache-control: " + cacheControl, xbmc.LOGDEBUG)
            
            cacheItems = cacheControl.split(', ')
            maxAgeLen = len('max-age=')
            for item in cacheItems:
                if item.startswith('max-age='):
                    return int(item[maxAgeLen:])
                
                if item.startswith('no-cache') or item.startswith('no-store'):
                    return 0 
        
        return None
                
    
    def _GetURL_NoCache(self,  url, values, headers, logUrl):
        url = url.replace("+", "%20")
        response = self.GetHTTPResponse(url, values, headers, logUrl)

        charset = self.GetCharset(response)
        maxAge = self.GetMaxAge(response)
        
        if u'content-encoding' in response.info() and response.info()[u'content-encoding'] == u'gzip':
            self.log (u"gzipped page", xbmc.LOGDEBUG)
            gzipper = gzip.GzipFile(fileobj=StringIO.StringIO(response.read()))
            data =  gzipper.read()
        else:
            data = response.read()
        
        if charset is None:
            try:
                data.decode('utf-8')
                charset = 'utf-8'
            except:
                charset = 'latin1'
            
        self.log (u"charset, maxAge: " + unicode((charset, maxAge)), xbmc.LOGDEBUG)
        
        return data.decode(charset), maxAge
        
    
    def GetHTTPResponse(self,  url, values = None, headers = None, logUrl = True):
        global lastCode
    
        if logUrl:
            self.log (u"url: " + url, xbmc.LOGDEBUG)    

        try:    
            if self.proxyConfig is not None: 
                self.proxyConfig.Enable()

            repeat = True
            firstTime = True
            addon = sys.modules["__main__"].addon
    
            while repeat:
                repeat = False
                try:
                    # Test socket.timeout
                    #raise socket.timeout
                    postData = None
                    if values is not None:
                        postData = urllib.urlencode(values)
                        self.log("postData: " + repr(postData))
                    
                    headers = self.PrepareHeaders(addon, headers)
                    
                    self.log("headers: " + repr(headers), xbmc.LOGDEBUG)
                    
                    request = urllib2.Request(url, postData, headers)
                    response = urllib2.urlopen(request)
                    """
                    self.log( 'Here are the headers of the page :', xbmc.LOGDEBUG )
                    self.log( handle.info(), xbmc.LOGDEBUG )
                    cookiejar = sys.modules["__main__"].cookiejar
                    self.log( cookiejar, xbmc.LOGDEBUG )
                    self.log( 'These are the cookies we have received so far :', xbmc.LOGDEBUG )

                    for index, cookie in enumerate(cookiejar):
                        self.log( index + '  :  ' + cookie, xbmc.LOGDEBUG )
                    cookiejar.save(COOKIE_PATH)
                    """
                except ( urllib2.HTTPError ) as err:
                    self.log ( u'HTTPError: ' + unicode(err), xbmc.LOGERROR)
                    lastCode = err.code
                    self.log (u"lastCode: " + unicode(lastCode), xbmc.LOGDEBUG)
                    raise err
                except ( urllib2.URLError ) as err:
                    self.log ( u'URLError: ' + unicode(err), xbmc.LOGERROR )
                    lastCode = -1
                    raise err
                except ( socket.timeout ) as exception:
                    self.log ( u'Timeout exception: ' + unicode(exception), xbmc.LOGERROR )
                    if firstTime:
                        self.log ( u'Timeout exception: ' + unicode(exception), xbmc.LOGERROR )
                        xbmc.executebuiltin(u'XBMC.Notification(%s, %s)' % (u'Socket timed out', 'Trying again'))
                        repeat = True
                    else:
                        """
                        The while loop is normally only processed once.
                        When a socket timeout happens it executes twice.
                        The following code executes after the second timeout.
                        """
                        self.log ( u'Timeout exception: ' + unicode(exception) + ", if you see this msg often consider changing your Socket Timeout settings", xbmc.LOGERROR )
                        raise exception
        
                    firstTime = False
                """
                else:
                    print 'Here are the headers of the page :'
                    print response.info()
                    print self.cookiejar
                    print 'These are the cookies we have received so far :'

                    for index, cookie in enumerate(self.cookiejar):
                        print index, '  :  ', cookie
                    #self.cookiejar.save(sys.modules["__main__"].COOKIE_PATH)
                    self.cookiejar.save() 
                """

        except ( Exception ) as exception:
            raise exception
        finally:
            if self.proxyConfig is not None: 
                self.proxyConfig.Disable()
    
        lastCode = response.getcode()
        self.log (u"lastCode: " + unicode(lastCode), xbmc.LOGDEBUG)

        return response
        
    #==============================================================================
    
    def PrepareHeaders(self, addon, newHeaders):
        headers = {}
        headers.update(self.defaultHeaders)

        if newHeaders is not None:
            headers.update(newHeaders)

        if self.isForwardedForIP is True:
            headers[u'X-Forwarded-For'] = self.forwardedForIP
            self.log(u"Using header 'X-Forwarded-For': " + self.forwardedForIP)
            
        return headers
            
    #==============================================================================
    
    def CachePage(self, url, data, values, expiryTime, logUrl):
        global lastCode
    
        if lastCode <> 404 and data is not None and len(data) > 0:    # Don't cache "page not found" pages, or empty data
            self.log (u"Add page to cache", xbmc.LOGDEBUG)

            self._Cache_Add( url, data, values, expiryTime, logUrl )
    
        
    def GetURL(self,  url, maxAgeSeconds=0, values = None, headers = None, logUrl = True):
        global lastCode
    
        if logUrl:
            self.log (url, xbmc.LOGDEBUG)
        # If no cache dir has been specified then return the data without caching
        if self._CheckCacheDir() == False:
            self.log (u"Not caching HTTP", xbmc.LOGDEBUG)
            data, responseMaxAge = self._GetURL_NoCache( url, values, headers, logUrl)
            return data
    
        currentTime = int(round(time.time()))
        
        if ( maxAgeSeconds > 0 ):
            self.log (u"maxAgeSeconds: " + unicode(maxAgeSeconds), xbmc.LOGDEBUG)
            # Is this URL in the cache?
            expiryString = self.GetExpiryTimeForUrl(url, values, logUrl)
            if expiryString is not None:
                self.log (u"expiryString: " + unicode(expiryString), xbmc.LOGDEBUG)
                # We have file in cache,_GetURL_NoCache but is it too old?
                if currentTime > int(expiryString):
                    self.log (u"Cached version is too old", xbmc.LOGDEBUG)
                    # Too old, so need to get it again
                    data, responseMaxAge = self._GetURL_NoCache( url, values, headers, logUrl)
    
                    if responseMaxAge is not None:
                        maxAgeSeconds = responseMaxAge
                        
                    if maxAgeSeconds <> 0:
                        # Cache it
                        self.CachePage(url, data, values, currentTime + maxAgeSeconds, logUrl)
    
                    # Cache size maintenance
                    self._Cache_Trim(currentTime)
    
                    # Return data
                    return data
                else:
                    self.log (u"Get page from cache", xbmc.LOGDEBUG)
                    # Get it from cache
                    data = self._Cache_GetData( url, values, expiryString, logUrl)
                    
                    if (data <> 0):
                        return data
                    else:
                        self.log(u"Error retrieving page from cache. Zero length page. Retrieving from web.")
        
        # maxAge = 0 or URL not in cache, so get it
        data, responseMaxAge = self._GetURL_NoCache( url, values, headers, logUrl)

        if responseMaxAge is not None:
            maxAgeSeconds = responseMaxAge
            
        if maxAgeSeconds > 0:
            self.CachePage(url, data, values, currentTime + maxAgeSeconds, logUrl)
    
        # Cache size maintenance
        self._Cache_Trim(currentTime)
        # Return data
        return data
    
    #==============================================================================
    
    def GetExpiryTimeForUrl(self, url, values, logUrl):
        cacheKey = self._Cache_CreateKey( url, values, logUrl )
        
        return self.GetExpiryTimeStr(cacheKey)
            
    #==============================================================================
    def GetExpiryTimeStr(self, cacheKey):
        files = glob.iglob( self.cacheDir + "/*" )
        for file in files:
            match=re.search( u"%s_(\d{10})" % cacheKey, file)
    
            if match is not None:
                return match.group(1)
        
        return None
            
        
    def _Cache_GetData(self,  url, values, expiryString, logUrl):
        global lastCode
        lastCode = 200
        cacheKey = self._Cache_CreateKey( url, values, logUrl )
        filename = cacheKey + "_" + expiryString
        cacheFileFullPath = os.path.join( self.cacheDir, filename )
        self.log (u"Cache file: %s" % cacheFileFullPath, xbmc.LOGDEBUG)
        f = codecs.open(cacheFileFullPath, u"r", u'utf-8')
        data = f.read()
        f.close()
    
        if len(data) == 0:
            os.remove(cacheFileFullPath)
    
        self.gotFromCache = True
        return data
    
    #==============================================================================
    
    def _Cache_Add(self,  url, data, values, currentTime, logUrl  ):
        cacheKey = self._Cache_CreateKey( url, values, logUrl )
        filename = cacheKey + "_" + str(currentTime)
        cacheFileFullPath = os.path.join( self.cacheDir, filename )
        self.log (u"Cache file: %s" % cacheFileFullPath, xbmc.LOGDEBUG)
        f = codecs.open(cacheFileFullPath, u"w", u'utf-8')
        f.write(data)
        f.close()
    
    #==============================================================================
    
    def _Cache_CreateKey(self,  url, values, logUrl ):
        try:
            if values is not None:
                url = url + "?" + urllib.urlencode(values)

            if logUrl:
                self.log("url: " + url)
            from hashlib import md5
            return md5(url).hexdigest()
        except:
            import md5
            if logUrl:
                self.log("url to be hashed: " + url)
            return  md5.new(url).hexdigest()
    
    #==============================================================================
    
    def IsDeleteFile(self, filename, filenameLen, currentTime):
       if (len(filename) != filenameLen):
           self.log("Invalid cache filename: " + filename, xbmc.LOGWARNING)
           return True
       
       match=re.search( u"(.{32})_(\d{10})", filename)

       if match is None:
           self.log("Invalid cache filename: " + filename, xbmc.LOGWARNING)
           return True

       expireTime = int(match.group(2))
       if currentTime > expireTime:
           self.log("Expired cache file: " + filename, xbmc.LOGDEBUG)
           return True

       return False
        
    #==============================================================================
        
    def ClearCache(self):
        files = glob.iglob( self.cacheDir + "/*" )
        for fileFullPath in files:
            self.log("Deleting cache fileFullPath: " + fileFullPath, xbmc.LOGDEBUG)
            if os.path.exists(fileFullPath):
                os.remove(fileFullPath)
        

    def _Cache_Trim(self, currentTime):
        epochLen = 10
        cacheKeyLen = 32
        filenameLen = cacheKeyLen + epochLen + 1
        
        pathOffset = len(self.cacheDir) + 1
        files = glob.iglob( self.cacheDir + "/*" )
        for fileFullPath in files:
            filename = os.path.basename(fileFullPath)
            if self.IsDeleteFile(filename, filenameLen, currentTime):
                self.log("Deleting cache fileFullPath: " + fileFullPath, xbmc.LOGDEBUG)
                if os.path.exists(fileFullPath):
                    os.remove(fileFullPath)
        
    #==============================================================================
