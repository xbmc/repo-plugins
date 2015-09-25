import sys
import urllib
import urlparse
import xbmcgui
import xbmcplugin
import xbmcaddon
import xbmc
import urllib2
import httplib
import requests
from resources.lib import CMDTools
from resources import xemvn


#?web
base_url = sys.argv[0]

def build_url(query):
    return base_url + '?' + urllib.urlencode(query)

addon_handle = int(sys.argv[1])
addon       = xbmcaddon.Addon()
addonname   = addon.getAddonInfo('name')

args = urlparse.parse_qs(sys.argv[2][1:])

xbmcplugin.setContent(addon_handle, 'movies')
web = args.get('web', None)
xemvn.view()