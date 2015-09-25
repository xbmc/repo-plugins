import sys
import urllib
import urlparse
import xbmcgui
import xbmcplugin
import xbmcaddon
import xbmc
import json
import urllib2
import webbrowser
import httplib 
from lib import requests
from lib import CMDTools
from lib import CommonFunctions

base_url = sys.argv[0]
web_name="HAIVAINOI.COM"
web_url = "http://www.haivainoi.com/" 

#xbmc.log(r.text)

def get_Web_Name():
	return web_name
def get_img_thumb_url():
	return CMDTools.get_path_img('resources/media/haivainoi.png')
def image_viewer(img):
    w = xbmcgui.Window()
    w.addControl(xbmcgui.ControlImage(0,0,w.getWidth(), w.getHeight(), img, 2))
    w.doModal()
    del w
def view():	

	addon_handle = int(sys.argv[1])

	addon       = xbmcaddon.Addon()
	addonname   = addon.getAddonInfo('name')
	
	args = urlparse.parse_qs(sys.argv[2][1:])

	xbmcplugin.setContent(addon_handle, 'movies')

	#common = CommonFunctions
	#common.plugin = "Your Plugin name-1.0"
	#response = urllib2.urlopen(web_url)
	
	
	#jar = cookielib.CookieJar()
	#handler = urllib2.HTTPCookieProcessor(jar)
	#opener = urllib2.build_opener(handler)
	#urllib2.install_opener(opener)

	#data = urllib2.urlopen(web_url).read()	
	
	#xbmc.log(token[0])
	#modes={folder, play}
	mode = args.get('mode', None)
	page = args.get('page', 1)
	link = args.get('link', None)
	
	xbmc.log(str(link))
	cat=args.get('cat', None)

	urlBase = "www.haivainoi.com" 
	url=urlBase
	
	catalogues=[{'label':'Home','id':'hot'},
				{'label':'\x42\xC3\xAC\x6E\x68\x20\x63\x68\xE1\xBB\x8D\x6E'.decode('utf-8'),'id':'fresh'},
				{'label':'18+','id':'18'},
				{'label':'\xC3\x81\x20\xC4\x91\xC3\xB9'.decode('utf-8'),'id':'adu'},
				{'label':'Meme','id':'meme'},
				{'label':'Girl xinh','id':'girlxinh'},
				{'label':'\xE1\xBA\xA2\x6E\x68\x20\xC4\x91\xE1\xBB\x99\x6E\x67'.decode('utf-8'),'id':'anhdong'},
				{'label':'Video','id':'video'}]
	#play link
	if link!=None:
		type = args.get('type', None)
		if type[0]=='image':
			xbmc.executebuiltin('ShowPicture('+'http://s107.haivainoi.com/images'+link[0]+')')
		elif type[0]=='gif':
			xbmc.Player().play('http://s107.haivainoi.com/images'+link[0])
			#play_list=xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
			#play_list.clear()
			#play_list.add("http://s107.haivainoi.com/images"+link[0])
			#xbmc.Player().play(play_list)
			#image_viewer("http://s107.haivainoi.com/images"+link[0])
			#xbmc.executebuiltin( "PlayMedia(http://s107.haivainoi.com/images"+link[0]+")" )
			#xbmc.executebuiltin('ShowPicture('+'http://s107.haivainoi.com/images'+link[0]+')')
		elif type[0]=='video':
			xbmc.Player().play("plugin://plugin.video.youtube/play/?video_id="+link[0])
		return
	#Load cats
	if cat==None:
		for cat in catalogues:
			li = xbmcgui.ListItem(cat['label'])
			urlList = CMDTools.build_url(base_url,{'web':get_Web_Name(), 'cat':cat['id']})
			xbmcplugin.addDirectoryItem(handle=addon_handle, url=urlList, listitem=li, isFolder=True)	
		xbmc.executebuiltin('Container.SetViewMode(501)')		 			
		xbmcplugin.endOfDirectory(addon_handle)
		return
	#Load noi dung cat
	if cat!=None:
		r = requests.get(web_url)

		common = CommonFunctions
		common.plugin = "Your Plugin name-1.0"
	
		html=r.text
		token=common.parseDOM(html, name="input", attrs = {"name":"_token"},ret="value")

		page = args.get('page', None)
		if page==None:
			page=1
		else:
			page=int(page[0])
			
		header={
			'Host': 'www.haivainoi.com',
			'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; rv:40.0) Gecko/20100101 Firefox/40.0',
			'Accept': '*/*',
			'Accept-Language': 'en-US,en;q=0.5',
			'Accept-Encoding': 'gzip, deflate',
			'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
			'X-Requested-With': 'XMLHttpRequest',
			'Referer': 'http://www.haivainoi.com/',
			'Cookie': '__cfduid=dff13c94cccfa0a7a33718fbcd5fc7eb11441153851; _ga=GA1.2.884414249.1441153857; XSRF-TOKEN=eyJpdiI6Imd2a3dMUlwvcmplUFRBcHltckhUQ0F3PT0iLCJ2YWx1ZSI6IkZjNHdKbnA5TVNnXC9SWWRuT1VyXC93QVpla2FtV2x6U2c4aW9TVys2NVNVbmdiR0ZnbTNPNnJUYWtcL0lsRDg0bEVSTytLWGdTMUErZDBQdWJNT1E0K3VBPT0iLCJtYWMiOiJkYWMwZWE2M2EzMWI2MTFlYWM2OWFkMzM0N2RjYzFlMGFlOGYyOGM4YTMxNmVmNTljM2U3MzVmM2Q5MzZiYTM5In0%3D; laravel_session=eyJpdiI6IjRDVG45VzgycnJ2dzRkSWJveFFaUlE9PSIsInZhbHVlIjoiZVVZWWpta3doTEZYS1JYVkJhNGdkK1l1ZGZzK0RmRVdNRktLdzI3RFRUVXNtV2k1bTZqOEw1UHIwbXJQUnhlOVlRN2FjMVE3akJIQ1NCOVFPT0ZQdWc9PSIsIm1hYyI6IjcyNTZlY2FkMDZlMDAzOGU3Mjc3YTliMTEyM2E1ZjZlOWQwY2FiOWI5MGZkZjU4ZmQ0YWQwMzJjYzg3MDg1NDUifQ%3D%3D; device=laptop',
			'Connection': 'keep-alive',
			'Pragma': 'no-cache',
			'Cache-Control': 'no-cache'
		}
		payload = {'id': 'all', 'postPage': page, 'type': '', 'category':cat[0] , 'action':'getPost','_token':token[0]}
		r = requests.post('http://www.haivainoi.com/post-handler', data=payload, cookies=r.cookies)
		data=r.json()
		
		#load item menu
		for item in data:
			li = xbmcgui.ListItem(item['title'])
			if item['type']=='image' or item['type']=='gif':
				li.setThumbnailImage('http://s107.haivainoi.com/images'+item['content'])
			elif item['type']=='video':
				li.setThumbnailImage('http://img.youtube.com/vi/'+item['content']+'/0.jpg')
			
			if item['type']=='gif':
				urlList = CMDTools.build_url(base_url,{'web':get_Web_Name(), 'link':item['GIFcontent'], 'type':item['type']})
			else: 
				urlList = CMDTools.build_url(base_url,{'web':get_Web_Name(), 'link':item['content'], 'type':item['type']})
			xbmcplugin.addDirectoryItem(handle=addon_handle, url=urlList, listitem=li)			
		
		#Tao nut next	
		li = xbmcgui.ListItem("Next")	
		urlList=CMDTools.build_url(base_url,{'web':web_name, 'cat':cat[0],'page': page+1});
		xbmcplugin.addDirectoryItem(handle=addon_handle, url=urlList, listitem=li, isFolder=True)	
		
		xbmc.executebuiltin('Container.SetViewMode(501)')		 
		xbmcplugin.endOfDirectory(addon_handle)
		return
					
	xbmcplugin.endOfDirectory(addon_handle)