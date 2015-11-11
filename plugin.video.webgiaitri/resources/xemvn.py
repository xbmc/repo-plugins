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
web_name="XEM.VN"
web_url = "http://xem.vn/" 

def get_Web_Name():
	return web_name
def get_img_thumb_url():
	return CMDTools.get_path_img('resources/media/xemvn.png')
    
def view():		
	addon_handle = int(sys.argv[1])
	addon       = xbmcaddon.Addon()
	addonname   = addon.getAddonInfo('name')
	
	args = urlparse.parse_qs(sys.argv[2][1:])

	xbmcplugin.setContent(addon_handle, 'movies')

	cat=args.get('cat', None)
	page = args.get('page', None)
	link = args.get('link', None)	
	
	catalogues=[{'label':'\x56\x69\x64\x65\x6F\x20\x4D\xE1\xBB\x9B\x69'.decode('utf-8'),'id':'video/new/'},
				{'label':'Video Hot','id':'video/hot/'}]
	#play link
	if link!=None:
		link_video=link[0]
		if link_video.startswith(web_url):
			r = requests.get(link[0])
			html = r.text
			#xbmc.log(html.encode('utf-8'))
			soup = BeautifulSoup(html)
			video_src=soup.find('embed', attrs={'id':'zplayer'})
			video_flashvars=video_src.get('flashvars')
			args_video = urlparse.parse_qs(video_flashvars)
			link_video=args_video['file'][0]					
		xbmc.Player().play(link_video)
		return
	#Load cats
	if cat==None:
		for cat in catalogues:
			li = xbmcgui.ListItem(cat['label'])
			urlList = CMDTools.build_url(base_url,{'web':get_Web_Name(), 'cat':cat['id']})
			xbmcplugin.addDirectoryItem(handle=addon_handle, url=urlList, listitem=li, isFolder=True)			
		return
	#Load noi dung cat
	if cat!=None:
		if page==None:
			page=1
		else:
			page=int(page[0])
		r = requests.get(web_url+cat[0]+str(page))
		html = r.text				
		soup = BeautifulSoup(html) 
		#, convertEntities=BeautifulSoup.HTML_ENTITIES)			
		data_List=soup.findAll('a',attrs={'class':'play'})
		#load item menu
		for item in data_List:			
			link_item=web_url+item.get('href')			
			if item.get('data-youtubeid')!='':
				link_item="plugin://plugin.video.youtube/play/?video_id="+item.get('data-youtubeid')
			img_item=item.find('img')
			img_src=img_item.get('src')
			img_alt=img_item.get('alt')
			
			li = xbmcgui.ListItem(img_alt)
			
			li.setThumbnailImage(img_src)
			li.setInfo(type='image',infoLabels="")					
			
			urlList = CMDTools.build_url(base_url,{'web':get_Web_Name(), 'link':link_item, 'type':cat[0]})
			xbmcplugin.addDirectoryItem(handle=addon_handle, url=urlList, listitem=li)			
		
		#Tao nut next	
		li = xbmcgui.ListItem("Next")	
		urlList=CMDTools.build_url(base_url,{'web':web_name, 'cat':cat[0],'page': page+1});
		xbmcplugin.addDirectoryItem(handle=addon_handle, url=urlList, listitem=li, isFolder=True)		
		return