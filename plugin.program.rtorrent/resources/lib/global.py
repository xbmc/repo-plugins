# Imports
from functions import *
import os
import sys
import xbmc
import xbmcaddon
import xbmcgui
import xmlrpc2scgi

# Addon constants
__plugin__ = "RTorrent"
__addonID__= "plugin.program.rtorrent"
__author__ = "Daniel Jolly"
__url__ = "http://www.danieljolly.com"
__credits__ = "See README"
__version__ = "0.10.1"
__date__ = "11/09/2010"

#Set a variable for Addon info and language strings
__addon__ = xbmcaddon.Addon( __addonID__ )
__setting__ = __addon__.getSetting
__lang__ = __addon__.getLocalizedString

# Connection constants
# Check to see if addon is set to socket or port mode
if int(__setting__('use_socket')) == 1:
	__connection__ = 'scgi://'+__setting__('domain_socket')
else:
	__connection__ = 'scgi://'+str(__setting__('scgi_server'))+':'+str(__setting__('scgi_port'))
	
rtc_test = xmlrpc2scgi.RTorrentXMLRPCClient(__connection__)

# Check to see if we can connect to rTorrent. If not ask to open Settings page. Good practice for first time user experience!
def connectionOK(): 
	#establishing connection
	# TODO: Add checking to make sure it establishes correctly
	try:
		rtc_test.system.client_version()
	except:
		dialog = xbmcgui.Dialog()
		ret = dialog.yesno(__lang__(30155),__lang__(30156),__lang__(30157))
		if ret==True:
			__addon__.openSettings()
			connectionOK()
		else:
			sys.exit()
	else:
		return rtc_test 

rtc = connectionOK()

# Directory containing status icons for torrents
__icondir__ = xbmc.translatePath(os.path.join(os.getcwd(),'resources','icons'))

# Try to ork out if the copy of rTorrent we're connecting to is running on the same machine.
if __setting__('use_socket')=='0': # Currently this feature is untested with remote domain sockets
	if __setting__('scgi_server')=='localhost' or __setting__('scgi_server')=='127.0.0.1' or __setting__('scgi_server')==os.getenv('COMPUTERNAME'):
		__islocal__=1
	else:
		__islocal__=0
else:
		__islocal__=1
print "the plugin is local to where rTorrent is running? "+str(__islocal__)