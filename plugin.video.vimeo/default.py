import sys, xbmc, xbmcaddon, xbmcplugin, xbmcgui
import BeautifulSoup as soup 

# plugin constants
version = "1.1.0"
plugin = "Vimeo-" + version
author = "TheCollective"
url = "www.xbmc.com"

# xbmc hooks
settings = xbmcaddon.Addon(id='plugin.video.vimeo')
language = settings.getLocalizedString
dbg = settings.getSetting("debug") == "true"
dbglevel = 1

# plugin structure 
scraper = ""
core = ""
navigation = ""
client = ""
cache = ""
utils = ""
login = ""
common = ""


if (__name__ == "__main__" ):
	
	if dbg:
		print plugin + " ARGV: " + repr(sys.argv)
	else:
		print plugin
		
	import vimeo
	client = vimeo.VimeoClient()

	import CommonFunctions
	common = CommonFunctions.CommonFunctions() 
	
	import VimeoUtils
	utils = VimeoUtils.VimeoUtils()
	
	import VimeoLogin
	login = VimeoLogin.VimeoLogin()
	
	import VimeoCore
	core = VimeoCore.VimeoCore()
	
	import VimeoScraperCore
	scraper = VimeoScraperCore.VimeoScraperCore()
	
	import VimeoNavigation
	navigation = VimeoNavigation.VimeoNavigation()
	
	if ( not settings.getSetting( "firstrun" ) ):
		settings.setSetting( "firstrun", '1' )
		login.login()
	
	if (not sys.argv[2]):
		navigation.listMenu()
	else:
		params = navigation.getParameters(sys.argv[2])
		get = params.get
		if (get("action")):
			navigation.executeAction(params)
		elif (get("path")):
			navigation.listMenu(params)
