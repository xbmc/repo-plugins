import sys
import urllib
import urlparse
import xbmcgui
import xbmcplugin
import xbmcaddon
import xbmc
import urllib, json
import urllib2
import webbrowser
import httplib
from resources.lib import requests
from resources.lib import CMDTools
from resources.lib import CommonFunctions


from resources import ngamvn
from resources import haivainoi
from resources import gioitre
from resources import beatvn
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
xbmc.log(str(args))

webs=[{'name':ngamvn.get_Web_Name(), 'img':ngamvn.get_img_thumb_url()},
	  {'name':haivainoi.get_Web_Name(), 'img':haivainoi.get_img_thumb_url()},
	  {'name':gioitre.get_Web_Name(), 'img':gioitre.get_img_thumb_url()},
	  {'name':beatvn.get_Web_Name(), 'img':beatvn.get_img_thumb_url()}]
if web==None:
	for w in webs:
		li = xbmcgui.ListItem(w['name'], iconImage=w['img'])
		urlList = build_url({'web' : w['name']})	
		xbmcplugin.addDirectoryItem(handle=addon_handle , url=urlList, listitem=li, isFolder=True)		
		xbmc.executebuiltin('Container.SetViewweb(501)')
	xbmcplugin.endOfDirectory(addon_handle)
elif web[0]==ngamvn.get_Web_Name():	
	ngamvn.view()
elif web[0]==haivainoi.get_Web_Name():	
	haivainoi.view()
elif web[0]==gioitre.get_Web_Name():	
	gioitre.view()
elif web[0]==beatvn.get_Web_Name():	
	beatvn.view()