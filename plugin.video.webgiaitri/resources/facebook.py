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
web_name="FACEBOOK.COM"
web_url = "https://m.facebook.com" 

#xbmc.log(r.text)

def get_Web_Name():
	return web_name
def get_img_thumb_url():
	xbmc.log(CMDTools.get_path_img('resources/media/fb.png'))
	return CMDTools.get_path_img('resources/media/fb.png')
    
def view():		
	addon       = xbmcaddon.Addon()
	addonname   = addon.getAddonInfo('name')
	addon_handle = int(sys.argv[1])
	
	args = urlparse.parse_qs(sys.argv[2][1:])
	
	cat=args.get('cat', None)
	page = args.get('page', None)
	link = args.get('link', None)	
	
	catalogues=[{'label':'BEATVN','id':'https://m.facebook.com/beatvn.jsc'},
				{'label':'\x47\x69\xE1\xBA\xA3\x69\x20\x54\x72\xC3\xAD\x20\x2B','id':'https://m.facebook.com/VuiVeFans'}]

	#play link
	if link!=None:	
		r = requests.get(link[0])
		html = r.text
		soup = BeautifulSoup(html)				
		imgItem=soup.find('img',attrs={"id":"fbPhotoImage"})				
		xbmc.executebuiltin('ShowPicture('+imgItem['src']+')')
		return
	#Load cats
	if cat==None:
		for c in catalogues:
			li = xbmcgui.ListItem(c['label'])
			urlList = CMDTools.build_url(base_url,{'web':get_Web_Name(), 'cat':c['id']})
			xbmcplugin.addDirectoryItem(handle=addon_handle, url=urlList, listitem=li, isFolder=True)							
	#Load noi dung cat
	else:
		if page==None:
			page=0
		else:
			page=int(page[0])
		r = requests.get(cat[0]+'?page='+str(page))
		html = r.text
		soup = BeautifulSoup(html)				
		soup=soup.find('div',attrs={"id":"recent"})
		
		#load item menu
		for div_item in soup.div.div:			
			for item in div_item.findAll('a'):			
				text_src=""
				video_src=None
				img_thumb=None
				img_src=None
				if item.get('href')!=None:
					if item.get('href').startswith('/video_redirect'):
						video_src=item.get('href')
						img_thumb=item.find('img').get('src')
					elif item.get('href').startswith(cat[0][len('https://m.facebook.com'):]+'/photos'):
						i=item.find('img')
						if i!=None and i.get('width')!=None:
							if (int(i.get('width'))>80):
								img_src=i.get('src').encode('utf-8')
					text_src=div_item.getText().encode('utf-8')
				if video_src!=None:				
					li = xbmcgui.ListItem(text_src)			
					li.setThumbnailImage(img_thumb)									
					params=urlparse.parse_qs(video_src.encode('utf-8')[17:])						
					xbmcplugin.addDirectoryItem(handle=addon_handle, url=params['src'][0], listitem=li)				
				elif img_src!=None:
					li = xbmcgui.ListItem(text_src)			
					li.setThumbnailImage(img_src)		
					urlImg=CMDTools.build_url(base_url,{'web':web_name, 'link': "https://facebook.com/"+item['href']});					
					xbmcplugin.addDirectoryItem(handle=addon_handle, url=urlImg, listitem=li)				
		#Tao nut next	
		li = xbmcgui.ListItem("Next")	
		urlList=CMDTools.build_url(base_url,{'web':web_name, 'cat':cat[0], 'page': page+1});
		xbmcplugin.addDirectoryItem(handle=addon_handle, url=urlList, listitem=li, isFolder=True)	