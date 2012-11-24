#/bin/python

import os
import time

import xbmc,xbmcaddon

import urllib2,socket,gzip,StringIO
import socks

from errorhandler import ErrorCodes
from errorhandler import ErrorHandler

__PluginName__  = 'plugin.video.4od'
__addon__ = xbmcaddon.Addon(__PluginName__)
__language__ = __addon__.getLocalizedString

gCacheDir = ""
gCacheSize = 20
gLastCode = -1
gFromCache = False
gSocketTimedOut = False



#==============================================================================
class CacheHelper:

	def __init__(self):
		self.cacheAttempt = True

	# Use the given maxAge on cache attempt. If this attempt fails then try again with maxAge = 0 (don't retrieve from cache)
	def ifCacheMaxAge(self, maxAge):
		if self.cacheAttempt:
			return maxAge

		return 0

	# Log level is debug if we are processes a page from the cache, 
	# because we don't want to display errors or halt processing 
	# unless we are processing a page directly from the web
	def ifCacheLevel(self, logLevel):
		xbmc.log("self: %s" % str(self))
		xbmc.log("ifCacheLevel(%s)" % str(logLevel))
		xbmc.log("ifCacheLevel self.cacheAttempt: %s" % str(self.cacheAttempt))
		if self.cacheAttempt and self.getGotFromCache():
			xbmc.log("return xbmc.LOGDEBUG")
			return xbmc.LOGDEBUG;

		xbmc.log("ifCacheLevel return logLevel: %s" % str(logLevel))
		return logLevel

	def setCacheAttempt(self, cacheAttempt):
		xbmc.log("self: %s" % str(self))
		self.cacheAttempt = cacheAttempt
		xbmc.log("setCacheAttempt(%s)" % str(self.cacheAttempt))

	def getCacheAttempt(self):
		return self.cacheAttempt


	def getGotFromCache(self):
		return _Cache_GetFromFlag()
	# Get url from cache iff cacheAttempt is True, otherwise get directly from web (maxAge = 0)
	# If the page was not in the cache then set cacheAttempt to False, indicating that the page was
	# retrieved from the web
	def GetURLFromCache(self, url, maxAge):
		xbmc.log("GetURLFromCache(%s)" % url, xbmc.LOGDEBUG)
		maxAge = self.ifCacheMaxAge(maxAge)
		html = GetURL( url, self.ifCacheLevel(xbmc.LOGERROR), maxAge )

		logLevel = self.ifCacheLevel(xbmc.LOGERROR)

		return html, logLevel


def GetProxy():
    proxy_server = None
    proxy_type_id = 0
    proxy_port = 8080
    proxy_user = None
    proxy_pass = None
    try:
        proxy_server = __addon__.getSetting('proxy_server')
        proxy_type_id = __addon__.getSetting('proxy_type')
        proxy_port = int(__addon__.getSetting('proxy_port'))
        proxy_user = __addon__.getSetting('proxy_user')
        proxy_pass = __addon__.getSetting('proxy_pass')
    except:
        pass

    if   proxy_type_id == '0': proxy_type = socks.PROXY_TYPE_HTTP_NO_TUNNEL
    elif proxy_type_id == '1': proxy_type = socks.PROXY_TYPE_HTTP
    elif proxy_type_id == '2': proxy_type = socks.PROXY_TYPE_SOCKS4
    elif proxy_type_id == '3': proxy_type = socks.PROXY_TYPE_SOCKS5

    proxy_dns = True

    if proxy_user == '':
	    proxy_user = None

    if proxy_pass == '':
	    proxy_pass = None

    return (proxy_type, proxy_server, proxy_port, proxy_dns, proxy_user, proxy_pass)


#==============================================================================

def SetupProxy():
        if __addon__.getSetting('proxy_use') == 'true':
		(proxy_type, proxy_server, proxy_port, proxy_dns, proxy_user, proxy_pass) = GetProxy()

                xbmc.log("Using proxy: type %i rdns: %i server: %s port: %s user: %s pass: %s" % (proxy_type, proxy_dns, proxy_server, proxy_port, "***", "***") )

		socks.setdefaultproxy(proxy_type, proxy_server, proxy_port, proxy_dns, proxy_user, proxy_pass)
		socks.wrapmodule(urllib2)

#==============================================================================

def GetLastCode():
	return gLastCode

#==============================================================================

def SetCacheDir( cacheDir ):
	global gCacheDir

	xbmc.log ("cacheDir: " + cacheDir, xbmc.LOGDEBUG)	
	gCacheDir = cacheDir
	if not os.path.isdir(gCacheDir):
		os.makedirs(gCacheDir)

#==============================================================================
def _Cache_ResetFromFlag():
	gFromCache = False

def _Cache_GetFromFlag():
	xbmc.log("_Cache_GetFromFlag() - gFromCache = %s" % str(gFromCache))
	return gFromCache

def _CheckCacheDir():
	if ( gCacheDir == '' ):
		return False

	return True


#==============================================================================

def _GetURL_NoCache( url, logLevel ):

	global gLastCode
	#global gSocketTimedOut

	xbmc.log ("url: " + url, xbmc.LOGDEBUG)	

	SetupProxy()
	repeat = True
	firstTime = True
	while repeat:
		repeat = False
		try:
			# Test socket.timeout
			#raise socket.timeout
			response = urllib2.urlopen(url)

		except ( urllib2.HTTPError ) as err:
			xbmc.log ( 'HTTPError: ' + str(err), xbmc.LOGERROR)
			gLastCode = err.code
			xbmc.log ("gLastCode: " + str(gLastCode), xbmc.LOGDEBUG)
			return ''
		except ( urllib2.URLError ) as err:
			xbmc.log ( 'URLError: ' + str(err), xbmc.LOGERROR )
			gLastCode = -1
			return ''
		except ( socket.timeout ) as exception:
			xbmc.log ( 'Timeout exception: ' + str(exception), xbmc.LOGERROR )
			if firstTime:
				xbmc.executebuiltin('XBMC.Notification(4oD %s, %s)' % ('', __language__(30895)))
				repeat = True
			else:
				# The while loop is normally only processed once.
				# When a socket timeout happens it executes twice.
				# The following code executes after the second timeout.
				
				# The cache retry mechanism may cause this code to be executed twice,
				# 'gSocketTimedOut' ensures that the Socket timeout error message only appears once   
				##if not gSocketTimedOut:
				##	xbmc.log ( 'NOT gSocketTimedOut', xbmc.LOGDEBUG )
				##	xbmc.executebuiltin('XBMC.Notification(4oD %s, %s)' % ('', __language__(30895)))
				##	gSocketTimedOut = True
				##	return None
				##else:
				##   xbmc.log ( 'gSocketTimedOut', xbmc.LOGDEBUG )
				# 'Change the socket timeout in the plugin setting if you see this problem a lot', 'Timeout occurred two times in a row' 
				error = ErrorHandler('_GetURL_NoCache', ErrorCodes.CHANGE_SOCKET_TIMEOUT, __language__(30865))

				# 'Socket timed out'
				error.process(__language__(30870), '', logLevel )
				return None

			firstTime = False

	#gSocketTimedOut = False
	
	gLastCode = response.getcode()
	xbmc.log ("gLastCode: " + str(gLastCode), xbmc.LOGDEBUG)
#	xbmc.log ("response info: " + response.info(), xbmc.LOGDEBUG)

        try:
                if response.info()['content-encoding'] == 'gzip':
        		xbmc.log ("gzipped page", xbmc.LOGDEBUG)
                        gzipper = gzip.GzipFile(fileobj=StringIO.StringIO(response.read()))
                        return gzipper.read()
        except KeyError:
		pass
	
	return response.read()

#==============================================================================

def CachePage(url, data):
	global gLastCode

	if gLastCode <> 404 and data is not None and len(data) > 0:	# Don't cache "page not found" pages, or empty data
		xbmc.log ("Add page to cache", xbmc.LOGDEBUG)
		_Cache_Add( url, data )


def GetURL( url, logLevel, maxAgeSeconds=0 ):
	global gLastCode

	xbmc.log ("GetURL: " + url, xbmc.LOGDEBUG)
	# If no cache dir has been specified then return the data without caching
	if _CheckCacheDir() == False:
       		xbmc.log ("Not caching HTTP", xbmc.LOGDEBUG)
		return _GetURL_NoCache( url )


	if ( maxAgeSeconds > 0 ):
       		xbmc.log ("maxAgeSeconds: " + str(maxAgeSeconds), xbmc.LOGDEBUG)
		# Is this URL in the cache?
		cachedURLTimestamp = _Cache_GetURLTimestamp( url )
		if ( cachedURLTimestamp > 0 ):
	       		xbmc.log ("cachedURLTimestamp: " + str(cachedURLTimestamp), xbmc.LOGDEBUG)
			# We have file in cache, but is it too old?
			if ( (time.time() - cachedURLTimestamp) > maxAgeSeconds ):
	       			xbmc.log ("Cached version is too old", xbmc.LOGDEBUG)
				# Too old, so need to get it again
				data = _GetURL_NoCache( url, logLevel )

				# Cache it
				CachePage(url, data)

				# Cache size maintenance
				_Cache_Trim

				# Return data
				return data
			else:
	       			xbmc.log ("Get page from cache", xbmc.LOGDEBUG)
				# Get it from cache
				data = _Cache_GetData( url )
				
				if (data <> 0):
					return data
				else:
					xbmc.log("Error retrieving page from cache. Zero length page. Retrieving from web.")
	
	# maxAge = 0 or URL not in cache, so get it
	data = _GetURL_NoCache( url, logLevel )
	CachePage(url, data)

	# Cache size maintenance
	_Cache_Trim
	# Return data
	return data

#==============================================================================

def _Cache_GetURLTimestamp( url ):
	cacheKey = _Cache_CreateKey( url )
	cacheFileFullPath = os.path.join( gCacheDir, cacheKey )
	if ( os.path.isfile( cacheFileFullPath ) ):
		return os.path.getmtime(cacheFileFullPath)
	else:
		return 0

#==============================================================================

def _Cache_GetData( url ):
	global gLastCode
	gLastCode = 200
	cacheKey = _Cache_CreateKey( url )
	cacheFileFullPath = os.path.join( gCacheDir, cacheKey )
	xbmc.log ("Cache file: %s" % cacheFileFullPath, xbmc.LOGDEBUG)
	f = file(cacheFileFullPath, "r")
	data = f.read()
	f.close()

	if len(data) == 0:
		os.remove(cacheFileFullPath)

	gFromCache = True
	#xbmc.log("gFromCache = %s" % str(gFromCache))
	
	return data

#==============================================================================

def _Cache_Add( url, data ):
	cacheKey = _Cache_CreateKey( url )
	cacheFileFullPath = os.path.join( gCacheDir, cacheKey )
	xbmc.log ("Cache file: %s" % cacheFileFullPath, xbmc.LOGDEBUG)
	f = file(cacheFileFullPath, "w")
	f.write(data)
	f.close()

#==============================================================================

def _Cache_CreateKey( url ):
	try:
		from hashlib import md5
		return md5(url).hexdigest()
	except:
		import md5
		return  md5.new(url).hexdigest()

#==============================================================================

def _Cache_Trim():
	files = glob.glob( gCacheDir )
	if ( len(files) > gCacheSize ):
		oldestFile = get_oldest_file( files )
		cacheFileFullPath = os.path.join( gCacheDir, oldestFile )
        if os.path.exists(cacheFileFullPath):
            os.remove(cacheFileFullPath)

#==============================================================================

def get_oldest_file(files, _invert=False):
    """ Find and return the oldest file of input file names.
    Only one wins tie. Values based on time distance from present.
    Use of `_invert` inverts logic to make this a youngest routine,
    to be used more clearly via `get_youngest_file`.
    """
    if _invert:
    	gt = operator.lt
    else:
    	gt = operator.gt
    # Check for empty list.
    if not files:
        return None
    # Raw epoch distance.
    now = time.time()
    # Select first as arbitrary sentinel file, storing name and age.
    oldest = files[0], now - os.path.getctime(files[0])
    # Iterate over all remaining files.
    for f in files[1:]:
        age = now - os.path.getctime(f)
        if gt(age, oldest[1]):
            # Set new oldest.
            oldest = f, age
    # Return just the name of oldest file.
    return oldest[0]
