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

import mycgi

from httpmanager import HttpManager
from fourOD import FourODProvider

from socket import setdefaulttimeout
from socket import getdefaulttimeout
from urlparse import urlunparse
from xbmcaddon import Addon

import utils
import rtmp

from utils import log

pluginHandle = int(sys.argv[1])

addon = Addon()
version = addon.getAddonInfo('version')
pluginName = addon.getAddonInfo('id')
name = addon.getAddonInfo('name')
language = addon.getLocalizedString
httpManager = HttpManager()

RESOURCE_PATH = os.path.join( addon.getAddonInfo( "path" ), "resources" )
MEDIA_PATH = os.path.join( RESOURCE_PATH, "media" )

# Use masterprofile rather profile, because we are caching data that may be used by more than one user on the machine
DATA_FOLDER      = xbmc.translatePath( os.path.join( "special://masterprofile","addon_data", pluginName ) )
CACHE_FOLDER     = os.path.join( DATA_FOLDER, 'cache' )
SUBTITLE_FILE    = os.path.join( DATA_FOLDER, 'subtitle.smi' )
NO_SUBTITLE_FILE = os.path.join( RESOURCE_PATH, 'nosubtitles.smi' )
PROFILE_DATA_FOLDER = xbmc.translatePath( os.path.join( u"special://profile", u"addon_data", pluginName) )



def get_system_platform():
    platform = "unknown"
    if xbmc.getCondVisibility( "system.platform.linux" ):
        platform = "linux"
    elif xbmc.getCondVisibility( "system.platform.xbox" ):
        platform = "xbox"
    elif xbmc.getCondVisibility( "system.platform.windows" ):
        platform = "windows"
    elif xbmc.getCondVisibility( "system.platform.osx" ):
        platform = "osx"

    log("Platform: %s" % platform, xbmc.LOGDEBUG)
    return platform

__platform__     = get_system_platform()


def InitTimeout():
	log("getdefaulttimeout(): " + str(getdefaulttimeout()), xbmc.LOGDEBUG)
	environment = os.environ.get( "OS", "xbox" )
	if environment in ['Linux', 'xbox']:
		try:
			timeout = int(addon.getSetting('socket_timeout'))
			if (timeout > 0):
				setdefaulttimeout(timeout)
		except:
			setdefaulttimeout(None)


#==============================================================================
def executeCommand():
    success = False

    provider = FourODProvider()
    provider.initialise(httpManager, sys.argv[0], pluginHandle, addon, language, PROFILE_DATA_FOLDER, RESOURCE_PATH)
    provider.SetSubtitlePaths(SUBTITLE_FILE, NO_SUBTITLE_FILE)
    
    success = provider.ExecuteCommand(mycgi)
    log (u"executeCommand done", xbmc.LOGDEBUG)
            
    return success


if __name__ == "__main__":

        try:
            log (u"Name: %s, Version: %s" % (name, version), xbmc.LOGDEBUG)

            if addon.getSetting('http_cache_disable_adv') == 'false':
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

