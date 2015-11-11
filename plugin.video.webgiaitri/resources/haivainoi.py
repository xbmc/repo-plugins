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
web_name="HAIVAINOI.COM"
web_url = "http://www.haivainoi.com/" 


def get_Web_Name():
	return web_name
def get_img_thumb_url():
	return CMDTools.get_path_img('resources/media/haivainoi.png')

def view():	

	addon_handle = int(sys.argv[1])
	addon       = xbmcaddon.Addon()
	addonname   = addon.getAddonInfo('name')
	
	args = urlparse.parse_qs(sys.argv[2][1:])

	xbmcplugin.setContent(addon_handle, 'movies')

	#get args
	mode = args.get('mode', None)
	page = args.get('page', 1)
	link = args.get('link', None)
	
	xbmc.log(str(link))
	cat=args.get('cat', None)

	urlBase = "www.haivainoi.com" 
	url=urlBase
	
	catalogues=[{'label':'Video','id':'video'},
				{'label':'Home','id':'hot'},
				{'label':'\x42\xC3\xAC\x6E\x68\x20\x63\x68\xE1\xBB\x8D\x6E'.decode('utf-8'),'id':'fresh'},
				{'label':'18+','id':'18'},
				{'label':'\xC3\x81\x20\xC4\x91\xC3\xB9'.decode('utf-8'),'id':'adu'},
				{'label':'Meme','id':'meme'},
				{'label':'Girl xinh','id':'girlxinh'},
				{'label':'\xE1\xBA\xA2\x6E\x68\x20\xC4\x91\xE1\xBB\x99\x6E\x67'.decode('utf-8'),'id':'anhdong'}]
	#play link
	if link!=None:
		type = args.get('type', None)
		if type[0]=='image':
			xbmc.executebuiltin('ShowPicture('+'http://s107.haivainoi.com/images'+link[0]+')')
		elif type[0]=='gif':
			xbmc.Player().play('http://s107.haivainoi.com/images'+link[0])
		elif type[0]=='video':
			xbmc.Player().play("plugin://plugin.video.youtube/play/?video_id="+link[0])
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
		r = requests.get(web_url)
		html=r.text
		soup=BeautifulSoup(html)
		token=soup.find("input", attrs = {"name":"_token"}).get("value")

		page = args.get('page', None)
		if page==None:
			page=1
		else:
			page=int(page[0])			
		payload = {'id': 'all', 'postPage': page, 'type': '', 'category':cat[0] , 'action':'getPost','_token':token}
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
		return
