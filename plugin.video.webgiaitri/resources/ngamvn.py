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
from lib import CommonFunctions
from lib import CMDTools

base_url = sys.argv[0]
web_name="NGAMVN.COM"
web_url = "http://www.ngamvn.com/" 


def build_url(query):
    return base_url + '?' + urllib.urlencode(query)
def get_Web_Name():
	return web_name
def get_img_thumb_url():
	return CMDTools.get_path_img('resources/media/ngamvn.png')
def view():	
	catalogues={'1.home':{'label':'Home','url':'/list/home/'},
				'2.new': {'label':"\x4D\xE1\xBB\x9B\x69\x20\x6E\x68\xE1\xBA\xA5\x74".decode('utf-8'),'url':'/list/new/'},
				'3.vote':{'label':'\x42\xC3\xAC\x6E\x68\x20\x63\x68\xE1\xBB\x8D\x6E'.decode('utf-8'),'url':'/list/vote/'},
				'4.hot':{'label':'\xE1\xBA\xA2\x6E\x68\x20\xC4\x91\x61\x6E\x67\x20\x68\x6F\x74'.decode('utf-8'),'url':'/list/hot/'},
				'5.clip':{'label':'Clip','url':'/list/pl/clip/'},
				'6.anh-vui-anh-che':{'cat':'anh-vui-anh-che','label':'\xE1\xBA\xA2\x6E\x68\x20\x56\x75\x69\x20\x2D\x20\xE1\xBA\xA2\x6E\x68\x20\x43\x68\xE1\xBA\xBF'.decode('utf-8'),'url':'/list/pl/anh-vui-anh-che/'},
				'7.anh-girl':{'label':'\xE1\xBA\xA2\x6E\x68\x20\x47\x69\x72\x6C'.decode('utf-8'),'url':'/list/pl/anh-girl/'},
				}
				
	xbmc.log(str(sorted(catalogues.keys())))
	addon_handle = int(sys.argv[1])

	addon       = xbmcaddon.Addon()
	addonname   = addon.getAddonInfo('name')
	
	args = urlparse.parse_qs(sys.argv[2][1:])
		

	xbmcplugin.setContent(addon_handle, 'movies')

	common = CommonFunctions
	common.plugin = "Your Plugin name-1.0"

	#cat: catalog
	#page: So thu tu page
	#url: Dia chi trang web
	cat = args.get('cat', None)
	mode = args.get('mode', None)
	page = args.get('page', None)
	urlLink = args.get('url', None)

	
	url=web_url

	#Neu click vao link play
	if urlLink != None:
		#xbmc.executebuiltin('ShowPicture('+urlLink[0]+')')
		response = urllib2.urlopen(urlLink[0])	
		html = response.read()	
		imgDiv=common.parseDOM(html, name="div", attrs = {"class":"photoImg"})	
		videoSrc=common.parseDOM(imgDiv[0], name="iframe", ret="src")	
		if(len(videoSrc)>0):		
			src=videoSrc[0]		
			id1=src.rfind('/')+1
			id2=src.rfind('?')-len(src)
			src=src[id1:id2]
			#xbmc.log(src)
			xbmc.Player().play("plugin://plugin.video.youtube/play/?video_id="+src)
		else: 
			imgSrc=common.parseDOM(imgDiv[0], name="img", ret="src")
			xbmc.executebuiltin('ShowPicture('+web_url+imgSrc[0]+')')
		xbmcplugin.endOfDirectory(addon_handle)
		return	
	
	#Neu vao trang chon muc
	if cat==None:		
		for cats in sorted(catalogues.keys()):			
			li = xbmcgui.ListItem(catalogues[cats]['label'])
			urlList = CMDTools.build_url(base_url,{'web':get_Web_Name(), 'cat':cats})
			xbmcplugin.addDirectoryItem(handle=addon_handle, url=urlList, listitem=li, isFolder=True)			
		xbmcplugin.endOfDirectory(addon_handle)
		return
	#Load noi dung trang
	else:
		#Dat url trang		
		if page != None:						
			page=int(page[0])
		else: 
			page=1		
		url=web_url+catalogues[cat[0]]['url']+str(page)
		#Load noi dung
		response = urllib2.urlopen(url)
		html = response.read()

		divImgs=common.parseDOM(html, name="div", attrs = {"class":"pic"})	
		#Tao list Item
		for divItem in divImgs:			
			#xbmc.log(divItem.encode('utf-8'))	
			url_Item_Link=common.parseDOM(divItem, name="a", ret="href")
			url_Item_Thumb=common.parseDOM(divItem, name="img", attrs = {"class":"thumb"}, ret="src")
			url_Item_Label=common.parseDOM(divItem, name="img", attrs = {"class":"thumb"}, ret="alt")

			if len(url_Item_Link)>0 and len(url_Item_Thumb)>0 and len(url_Item_Label)>0 :				
				url_Item_Link=url_Item_Link[0]
				url_Item_Thumb=url_Item_Thumb[0]
				url_Item_Label=url_Item_Label[0]
				
				if(url_Item_Thumb.startswith("http://")!=True):
					url_Item_Thumb=web_url+url_Item_Thumb	

				li = xbmcgui.ListItem(url_Item_Label.encode('utf-8'))		
				li.setThumbnailImage(url_Item_Thumb)
				#li.setArt({"fanart":url+urlItem.encode('utf-8')})
				urlList=build_url({'web':web_name,'url': url_Item_Link.encode('utf-8')});	
				xbmcplugin.addDirectoryItem(handle=addon_handle , url=urlList, listitem=li)		
		#Tao nut next	
		li = xbmcgui.ListItem("Next")	
		urlList=CMDTools.build_url(base_url,{'web':web_name, 'cat':cat[0],'page': page+1});
		xbmcplugin.addDirectoryItem(handle=addon_handle, url=urlList, listitem=li, isFolder=True)		
	#set view
	xbmc.executebuiltin('Container.SetViewMode(501)')
		 
	xbmcplugin.endOfDirectory(addon_handle)