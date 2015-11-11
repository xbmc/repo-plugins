import sys
import urllib
import urlparse
import xbmcgui
import xbmcplugin
import xbmcaddon
import xbmc
import requests
from bs4 import BeautifulSoup
from lib import CMDTools

base_url = sys.argv[0]
web_name="NGAMVN.COM"
web_url = "http://www.ngamvn.com/" 

def get_Web_Name():
	return web_name
	
def get_img_thumb_url():
	return CMDTools.get_path_img('resources/media/ngamvn.png')
	
def view():	
	catalogues=[{'label':'Clip','id':'/list/pl/clip/'},
				{'label':'Home','id':'/list/home/'},
				{'label':"\x4D\xE1\xBB\x9B\x69\x20\x6E\x68\xE1\xBA\xA5\x74".decode('utf-8'),'id':'/list/new/'},
				{'label':'\x42\xC3\xAC\x6E\x68\x20\x63\x68\xE1\xBB\x8D\x6E'.decode('utf-8'),'id':'/list/vote/'},
				{'label':'\xE1\xBA\xA2\x6E\x68\x20\xC4\x91\x61\x6E\x67\x20\x68\x6F\x74'.decode('utf-8'),'id':'/list/hot/'},
				{'cat':'anh-vui-anh-che','label':'\xE1\xBA\xA2\x6E\x68\x20\x56\x75\x69\x20\x2D\x20\xE1\xBA\xA2\x6E\x68\x20\x43\x68\xE1\xBA\xBF'.decode('utf-8'),'id':'/list/pl/anh-vui-anh-che/'},
				{'label':'\xE1\xBA\xA2\x6E\x68\x20\x47\x69\x72\x6C'.decode('utf-8'),'id':'/list/pl/anh-girl/'}]
				
	addon_handle = int(sys.argv[1])
	addon       = xbmcaddon.Addon()
	addonname   = addon.getAddonInfo('name')
	
	args = urlparse.parse_qs(sys.argv[2][1:])
		

	xbmcplugin.setContent(addon_handle, 'movies')


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
		response = requests.get(urlLink[0])
		html = response.text
		soup = BeautifulSoup(html)
		imgDiv=soup.find("div", attrs = {"class":"photoImg"})	
		videoSrc=imgDiv.find("iframe")
		if videoSrc!=None:
			src=videoSrc.get("src")		
			id1=src.rfind('/')+1
			id2=src.rfind('?')-len(src)
			src=src[id1:id2]
			#xbmc.log(src)
			xbmc.Player().play("plugin://plugin.video.youtube/play/?video_id="+src)
		else:			
			imgSrc=imgDiv.find("img").get("src")		
			xbmc.executebuiltin('ShowPicture('+web_url+imgSrc+')')		
		return	
	
	#Neu vao trang chon muc
	if cat==None:		
		for c in catalogues:			
			li = xbmcgui.ListItem(c['label'])
			urlList = CMDTools.build_url(base_url,{'web':get_Web_Name(), 'cat':c['id']})
			xbmcplugin.addDirectoryItem(handle=addon_handle, url=urlList, listitem=li, isFolder=True)					
		return
	#Load noi dung trang
	else:
		#Dat url trang		
		if page != None:						
			page=int(page[0])
		else: 
			page=1		
		url=web_url+cat[0]+str(page)
		
		#Load noi dung
		response = requests.get(url)
		html = response.text
		soup = BeautifulSoup(html)
		divImgs=soup.findAll("div", attrs = {"class":"pic"})
		
		#Tao list Item
		for divItem in divImgs:			
			#xbmc.log(divItem.encode('utf-8'))	
			url_Item_Link=divItem.find("a").get("href")
			url_Item_Thumb=divItem.find("img", attrs = {"class":"thumb"}).get("src")
			url_Item_Label=divItem.find("img", attrs = {"class":"thumb"}).get("alt")
			if url_Item_Link!=None and url_Item_Thumb!=None:
				if(url_Item_Thumb.startswith("http://")!=True):
					url_Item_Thumb=web_url+url_Item_Thumb
				li = xbmcgui.ListItem(url_Item_Label.encode('utf-8'))
				li.setThumbnailImage(url_Item_Thumb)
				urlList=CMDTools.build_url(base_url,{'web':web_name,'url': url_Item_Link.encode('utf-8')});	
				xbmcplugin.addDirectoryItem(handle=addon_handle , url=urlList, listitem=li)		
		#Tao nut next	
		li = xbmcgui.ListItem("Next")	
		urlList=CMDTools.build_url(base_url,{'web':web_name, 'cat':cat[0],'page': page+1});
		xbmcplugin.addDirectoryItem(handle=addon_handle, url=urlList, listitem=li, isFolder=True)				 	