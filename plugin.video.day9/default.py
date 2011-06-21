import urllib, urllib2, re, sys, os, string, day9
import xbmc, xbmcaddon, xbmcgui, xbmcplugin

__version__ = "0.5.2"
__plugin__ = "Day9-" + __version__
__author__ = "Kristoffer Petersson"
__settings__ = xbmcaddon.Addon(id='plugin.video.day9')
__language__ = __settings__.getLocalizedString

Day9 = day9.Day9()

if (not sys.argv[2]):
    Day9.root()
else:
	print __plugin__

	params = Day9.getParams(sys.argv[2])
	get = params.get
	if (get("action")):
		Day9.action(params)
		
xbmcplugin.endOfDirectory(int(sys.argv[1]))