#/bin/python
# -*- coding: utf-8 -*-


# http://wiki.xbmc.org/index.php?title=How-to:Debug_Python_Scripts_with_Eclipse

REMOTE_DBG = False	

# append pydev remote debugger
if REMOTE_DBG:
	# Make pydev debugger works for auto reload.
	# Note pydevd module need to be copied in XBMC\system\python\Lib\pysrc
	try:
		import pysrc.pydevd as pydevd
	# stdoutToServer and stderrToServer redirect stdout and stderr to eclipse console
		pydevd.settrace('localhost', stdoutToServer=True, stderrToServer=True)
		#pydevd.settrace('localhost', port=5678, stdoutToServer=True, stderrToServer=True)
		
	except ImportError:
		sys.stderr.write("Error: " +
			"You must add org.python.pydev.debug.pysrc to your PYTHONPATH.")
		sys.exit(1)


import os
import xbmcplugin
import xbmcgui
import xbmc
import re
import cookielib
import urllib2
import xbmcvfs

from xbmcaddon import Addon
from loggingexception import LoggingException
from BeautifulSoup import BeautifulSoup


pluginName  = u'plugin.video.irishtv'
pluginHandle = int(sys.argv[1])
baseURL = sys.argv[0]

addon = Addon(pluginName)
language = addon.getLocalizedString

import mycgi

from httpmanager import HttpManager

dbg = addon.getSetting("debug") == "true"
dbglevel = 3

from utils import log
from socket import setdefaulttimeout
from socket import getdefaulttimeout

import utils
import rtmp

import providerfactory
from provider import Provider
#import SimpleDownloader
#__downloader__ = SimpleDownloader.SimpleDownloader()
xhausUrl = "http://www.xhaus.com/headers"

# Use masterprofile rather profile, because we are caching data that may be used by more than one user on the machine
DATA_FOLDER	  = xbmc.translatePath( os.path.join( u"special://masterprofile", u"addon_data", pluginName ) )
CACHE_FOLDER	 = os.path.join( DATA_FOLDER, u'cache' )
RESOURCE_PATH = os.path.join( sys.modules[u"__main__"].addon.getAddonInfo( u"path" ), u"resources" )
MEDIA_PATH = os.path.join( RESOURCE_PATH, u"media" )
ADDON_DATA_FOLDER = xbmc.translatePath( os.path.join( u"special://profile", u"addon_data", pluginName) )
COOKIE_PATH = os.path.join( ADDON_DATA_FOLDER, u"cookiejar.txt" )
#player.Player.RESUME_FILE    = os.path.join( ADDON_DATA_FOLDER, u'player_resume.txt')
#player.Player.RESUME_LOCK_FILE = os.path.join(ADDON_DATA_FOLDER, u'player_resume_lock.txt')

log("Loading cookies from :" + repr(COOKIE_PATH))
cookiejar = cookielib.LWPCookieJar(COOKIE_PATH)

if xbmcvfs.exists(COOKIE_PATH):
    try:
        #cookiejar.load(COOKIE_PATH)
        cookiejar.load()
    except:
        pass

cookie_handler = urllib2.HTTPCookieProcessor(cookiejar)
opener = urllib2.build_opener(cookie_handler)

httpManager = HttpManager()


#SUBTITLE_FILE	= os.path.join( DATA_FOLDER, 'subtitle.smi' )
#NO_SUBTITLE_FILE = os.path.join( RESOURCE_PATH, 'nosubtitles.smi' )

def get_system_platform():
	platform = u"unknown"
	if xbmc.getCondVisibility( u"system.platform.linux" ):
		platform = u"linux"
	elif xbmc.getCondVisibility( u"system.platform.xbox" ):
		platform = u"xbox"
	elif xbmc.getCondVisibility( u"system.platform.windows" ):
		platform = u"windows"
	elif xbmc.getCondVisibility( u"system.platform.osx" ):
		platform = u"osx"

	log(u"Platform: %s" % platform, xbmc.LOGDEBUG)
	return platform

__platform__	 = get_system_platform()


def ShowProviders():
	listItems = []
	contextMenuItems = []
	contextMenuItems.append(('Clear HTTP Cache', "XBMC.RunPlugin(%s?clearcache=1)" % sys.argv[0] ))
	contextMenuItems.append(('Test Forwarded IP', "XBMC.RunPlugin(%s?testforwardedip=1)" % sys.argv[0] ))
	
	providers = providerfactory.getProviderList()


	for provider in providers:
		providerName = provider.GetProviderId()
		log(u"Adding " + providerName + u" provider", xbmc.LOGDEBUG)
		newListItem = xbmcgui.ListItem( providerName )
		url = baseURL + u'?provider=' + providerName

		log(u"url: " + url, xbmc.LOGDEBUG)
		thumbnailPath = provider.GetThumbnailPath(providerName)
		log(providerName + u" thumbnail: " + thumbnailPath, xbmc.LOGDEBUG)
		newListItem.setThumbnailImage(thumbnailPath)
		newListItem.addContextMenuItems( contextMenuItems )
		listItems.append( (url,newListItem,True) )
	

	xbmcplugin.addDirectoryItems( handle=pluginHandle, items=listItems )
	xbmcplugin.endOfDirectory( handle=pluginHandle, succeeded=True )
		

#==============================================================================

def InitTimeout():
	log(u"getdefaulttimeout(): " + str(getdefaulttimeout()), xbmc.LOGDEBUG)
	environment = os.environ.get( u"OS", u"xbox" )
	if environment in [u'Linux', u'xbox']:
		try:
			timeout = int(addon.getSetting(u'socket_timeout'))
			if (timeout > 0):
				setdefaulttimeout(timeout)
		except:
			setdefaulttimeout(None)

def TestForwardedIP(forwardedIP):
	try:
		html = None
		log(u"TestForwardedIP: " + forwardedIP)
		httpManager.EnableForwardedForIP()
		httpManager.SetForwardedForIP( forwardedIP )
		html = httpManager.GetWebPageDirect( xhausUrl )
		
		soup = BeautifulSoup(html)
		xForwardedForString = soup.find(text='X-Forwarded-For')
		
		if xForwardedForString is None:
			dialog = xbmcgui.Dialog()
			dialog.ok(language(30028), language(30032))
		else:
			forwardedForIP = xForwardedForString.parent.findNextSibling('td').text
			
			dialog = xbmcgui.Dialog()
			dialog.ok(language(30029), language(30033) + forwardedForIP)
			
		return True
		
	except (Exception) as exception:
		if not isinstance(exception, LoggingException):
			exception = LoggingException.fromException(exception)

		dialog = xbmcgui.Dialog()
		dialog.ok(language(30031), language(30034))
		
		# Error getting web page
		exception.addLogMessage(language(30050))
		exception.printLogMessages(xbmc.LOGERROR)
		return False


	
#==============================================================================
def executeCommand():
	pluginHandle = int(sys.argv[1])
	success = False

	if ( mycgi.EmptyQS() ):
		success = ShowProviders()
	else:
		(providerName, clearCache, testForwardedIP) = mycgi.Params( u'provider', u'clearcache', u'testforwardedip')

		if clearCache != u'':
			httpManager.ClearCache()
			return True
		
		elif testForwardedIP != u'':
			provider = Provider()
			provider.addon = sys.modules[u"__main__"].addon

			httpManager.SetDefaultHeaders( provider.GetHeaders() )
			forwardedIP = provider.CreateForwardedForIP('0.0.0.0')
			
			return TestForwardedIP(forwardedIP)
			
		elif providerName != u'':
			log(u"providerName: " + providerName, xbmc.LOGDEBUG)
			if providerName <> u'':
				provider = providerfactory.getProvider(providerName)
				
				if provider is None:
					# ProviderFactory return none for providerName: %s
					logException = LoggingException(language(30000) % providerName)
					# 'Cannot proceed', Error processing provider name
					logException.process(language(30755), language(30020), xbmc.LOGERROR)
					return False
				
				provider.initialise(httpManager, sys.argv[0], pluginHandle)
				success = provider.ExecuteCommand(mycgi)
				log (u"executeCommand done", xbmc.LOGDEBUG)

				"""
				print cookiejar
				print 'These are the cookies we have received so far :'

				for index, cookie in enumerate(cookiejar):
					print index, '  :  ', cookie
				cookiejar.save() 
				"""

	return success
#		if ( search <> '' ):
#			error = DoSearch()
#		elif ( showId <> '' and episodeId == ''):
#			error = ShowEpisodes( showId, title )
#		elif ( category <> '' ):
#			error = ShowCategory( category, title, order, page )
#		elif ( episodeId <> '' ):
#			(episodeNumber, seriesNumber, swfPlayer) = mycgi.Params( 'episodeNumber', 'seriesNumber', 'swfPlayer' )
#			error = PlayOrDownloadEpisode( showId, int(seriesNumber), int(episodeNumber), episodeId, title, swfPlayer )
#	


if __name__ == "__main__":

		try:
			if addon.getSetting('http_cache_disable') == 'false':
				httpManager.SetCacheDir( CACHE_FOLDER )
	
			InitTimeout()
		
			# Each command processes a web page
			# Get the web page from the cache if it's there
			# If there is an error when processing the web page from the cache
			# we want to try again, this time getting the page from the web
			httpManager.setGetFromCache(True)
			success = executeCommand()			
	
			xbmc.log(u"success: %s, getGotFromCache(): %s" % (unicode(success), unicode(httpManager.getGotFromCache())), xbmc.LOGDEBUG)
			
			if success is not None and success == False and httpManager.getGotFromCache() == True:
				httpManager.setGetFromCache(False)
				executeCommand()
				log (u"executeCommand after", xbmc.LOGDEBUG)
				
		except:
			# Make sure the text from any script errors are logged
			import traceback
			traceback.print_exc(file=sys.stdout)
			raise

