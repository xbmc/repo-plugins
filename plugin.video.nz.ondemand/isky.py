import tools, urllib, string, re, sys, time, xbmcaddon
from BeautifulSoup import BeautifulSoup, SoupStrainer

addon = xbmcaddon.Addon(id = sys.argv[0][9:-1])
localize = addon.getLocalizedString
