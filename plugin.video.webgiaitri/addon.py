import sys
import urllib
import urlparse
import xbmcgui
import xbmcplugin
import xbmcaddon
import xbmc
from resources.lib import CMDTools
from resources import ngamvn
from resources import haivainoi
from resources import gioitre
from resources import xemvn
from resources import talktv
from resources import facebook

#?web
base_url = sys.argv[0]

def build_url(query):
    return base_url + '?' + urllib.urlencode(query)

addon_handle = int(sys.argv[1])
addon       = xbmcaddon.Addon()
addonname   = addon.getAddonInfo('name')
args = urlparse.parse_qs(sys.argv[2][1:])

xbmcplugin.setContent(addon_handle, 'movies')
#Get web name
web = args.get('web', None)
xbmc.log(str(args))

#List Website
webs=[{'name':xemvn.get_Web_Name(), 'img':xemvn.get_img_thumb_url()},	  
	  {'name':gioitre.get_Web_Name(), 'img':gioitre.get_img_thumb_url()},	  	  
	  {'name':talktv.get_Web_Name(), 'img':talktv.get_img_thumb_url()},
	  {'name':facebook.get_Web_Name(), 'img':facebook.get_img_thumb_url()},
	  {'name':ngamvn.get_Web_Name(), 'img':ngamvn.get_img_thumb_url()},	  
	  {'name':haivainoi.get_Web_Name(), 'img':haivainoi.get_img_thumb_url()}]

#set view
if web==None:
	for w in webs:
		li = xbmcgui.ListItem(w['name'], iconImage=w['img'])
		urlList = build_url({'web' : w['name']})	
		xbmcplugin.addDirectoryItem(handle=addon_handle , url=urlList, listitem=li, isFolder=True)
elif web[0]==ngamvn.get_Web_Name():	
	ngamvn.view()
elif web[0]==haivainoi.get_Web_Name():	
	haivainoi.view()
elif web[0]==gioitre.get_Web_Name():	
	gioitre.view()
elif web[0]==xemvn.get_Web_Name():	
	xemvn.view()
elif web[0]==talktv.get_Web_Name():	
	talktv.view()
elif web[0]==facebook.get_Web_Name():	
	facebook.view()
xbmc.executebuiltin('Container.SetViewMode(501)')
xbmcplugin.endOfDirectory(addon_handle)				

