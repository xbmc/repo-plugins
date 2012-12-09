import urllib, urllib2, re, sys, os, string, day9
import xbmc, xbmcaddon, xbmcgui, xbmcplugin

__settings__ = xbmcaddon.Addon(id='plugin.video.day9')
__version__ = __settings__.getAddonInfo('version')
__plugin__ = "Day9-" + __version__
__author__ = "Robert"
__language__ = __settings__.getLocalizedString

Day9tv = day9.Day9()

if (not sys.argv[2]):
    Day9tv.root()
else:
	print __plugin__

	params = Day9tv.getParams(sys.argv[2])
	get = params.get
	if (get("action")):
		Day9tv.action(params)
		
xbmcplugin.endOfDirectory(int(sys.argv[1]))
