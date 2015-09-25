import sys
import urllib
import urlparse
import xbmcgui
import xbmcplugin
import xbmcaddon
import xbmc
import json
import urllib2
import httplib 
from lib import requests
from lib import CMDTools
from lib import CommonFunctions
from lib import BeautifulSoup

base_url = sys.argv[0]
web_name="BEAT.VN"
web_url = "https://m.facebook.com/Beat.vn" 

#xbmc.log(r.text)

def get_Web_Name():
	return web_name
def get_img_thumb_url():
	xbmc.log(CMDTools.get_path_img('resources/media/beatvn.jpg'))
	return CMDTools.get_path_img('resources/media/beatvn.jpg')
    
def view():	
	#xbmc.executebuiltin("SlideShow(,,notrandom)")
	addon_handle = int(sys.argv[1])

	addon       = xbmcaddon.Addon()
	addonname   = addon.getAddonInfo('name')
	
	args = urlparse.parse_qs(sys.argv[2][1:])

	xbmcplugin.setContent(addon_handle, 'movies')
	common = CommonFunctions

	cat=args.get('cat', None)
	page = args.get('page', None)
	link = args.get('link', None)
	show=args.get('show', None)
	
	catalogues=[{'label':'Video','id':'video'},
				{'label':'Girl Xinh','id':'girl-xinh'}]
	if (show!=None):
		show_photos(show[0])
		return
	#play link
	if link!=None:
		#xbmc.executebuiltin("ClearSlideshow")    
		
		#xbmc.executebuiltin("SlideShow(,,)")
		type = args.get('type', None)
		if type[0]=='girl-xinh':			
			xbmc.executebuiltin("SlideShow(%s,recursive,notrandom)" % CMDTools.build_url(base_url,{'web':get_Web_Name(), 'show':link[0]}))
		elif type[0]=='video':
			xbmc.Player().play("plugin://plugin.video.youtube/play/?video_id="+link[0])
		return
	#Load cats
	#Load noi dung cat
	else:
		if page==None:
			page=0
		else:
			page=int(page[0])
		r = requests.get(web_url+'?page='+str(page))
		html = r.text
		soup = BeautifulSoup.BeautifulSoup(html, convertEntities=BeautifulSoup.BeautifulSoup.HTML_ENTITIES)		
		#xbmc.log("------------soup:"+str(soup))
		soup=soup.find('div',attrs={"id":"recent"})
		#load item menu
		for item in soup.findAll('a'):	
			text_src=""
			video_src=None
			img_thumb=None
			img_src=None
			if item.get('href')!=None:
				if item.get('href').startswith('/video_redirect'):
					video_src=item.get('href')
					img_thumb=item.find('img').get('src')
				elif item.get('href').startswith('/Beat.vn/photos/'):		
					i=item.find('img')
					if i.get('width')!=None:
						if (int(i.get('width'))>80):
							img_src=i.get('src').encode('utf-8')
				text_src=item.findPrevious('div').findPrevious('div').findPrevious('div').findPrevious('div').find('span')
				if (text_src!=None):
					text_src=text_src.getText().encode('utf-8')
			if video_src!=None:				
				li = xbmcgui.ListItem(text_src)			
				li.setThumbnailImage(img_thumb)									
				params=urlparse.parse_qs(video_src.encode('utf-8')[17:])				
				xbmcplugin.addDirectoryItem(handle=addon_handle, url=params['src'][0], listitem=li)
			elif img_src!=None:
				li = xbmcgui.ListItem(text_src)			
				li.setThumbnailImage(img_src)											
				xbmcplugin.addDirectoryItem(handle=addon_handle, url=img_src, listitem=li)			
		#Tao nut next	
		li = xbmcgui.ListItem("Next")	
		urlList=CMDTools.build_url(base_url,{'web':web_name, 'page': page+1});
		xbmcplugin.addDirectoryItem(handle=addon_handle, url=urlList, listitem=li, isFolder=True)	
		
		xbmc.executebuiltin('Container.SetViewMode(501)')
		#xbmc.executebuiltin("ClearSlideshow")		
		#xbmc.executebuiltin("SlideShow(,,notrandom)")		
		xbmcplugin.endOfDirectory(addon_handle)
		return
					
	xbmcplugin.endOfDirectory(addon_handle)