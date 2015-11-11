import sys
import urllib
import urlparse
import xbmcgui
import xbmcplugin
import xbmcaddon
import xbmc
import requests
import CommonFunctions
from bs4 import BeautifulSoup 
from lib import CMDTools



base_url = sys.argv[0]
web_name="GIOITRE.NET"
web_url = "http://gioitre.net/" 

def get_Web_Name():
	return web_name
def get_img_thumb_url():
	return CMDTools.get_path_img('resources/media/gioitre.png')
def show_photos(url):		
	r = requests.get('http://gioitre.net'+url)
	html = r.text	
	soup=BeautifulSoup(html,'html5lib')
	div_contentDeatil=soup.find("div", attrs = {"class":"contentDeatil"})	
	imgs=div_contentDeatil.findAll("img")
	for img in imgs:						
		img_src=img['src']
		li = xbmcgui.ListItem(label="",thumbnailImage=img_src) 
		li.setInfo(type='image', infoLabels={'Title': ''})
		xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=img_src,listitem=li,isFolder=False)
	xbmcplugin.endOfDirectory(int(sys.argv[1]))

    
def view():	
	#xbmc.executebuiltin("SlideShow(,,notrandom)")
	addon_handle = int(sys.argv[1])

	addon       = xbmcaddon.Addon()
	addonname   = addon.getAddonInfo('name')
	
	args = urlparse.parse_qs(sys.argv[2][1:])

	xbmcplugin.setContent(addon_handle, 'movies')

	common = CommonFunctions
	#get args
	cat=args.get('cat', None)
	page = args.get('page', None)
	link = args.get('link', None)
	show=args.get('show', None)
	
	catalogues=[{'label':'Video','id':'video'},
				{'label':'Girl Xinh','id':'girl-xinh'},
				{'label':'\xC4\x90\xE1\xBA\xB9\x70'.decode('utf-8'),'id':'dep'}]
	if (show!=None):
		show_photos(show[0])
		return
	#play link
	if link!=None:
		type = args.get('type', None)
		if type[0]!='video':			
			xbmc.executebuiltin("SlideShow(%s,recursive,notrandom)" % CMDTools.build_url(base_url,{'web':get_Web_Name(), 'show':link[0]}))
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
		if page==None:
			page=1
		else:
			page=int(page[0])
		r = requests.get(web_url+cat[0]+'?page='+str(page))
		html = r.text		
		soup=BeautifulSoup(html,'html5lib')
		data_list=soup.find("div", attrs = {"class":"listLage"})
		if data_list==None:
			data_list=soup.find("div", attrs = {"class":"listItemnews"})
		
		data=data_list.findAll('li')
		#load item menu
		for item in data:			
			img=item.find('img')
			img_alt=img['alt']			
			img_src=img['src']
			li = xbmcgui.ListItem(img_alt)			
			li.setThumbnailImage(img_src)
			li.setInfo(type='image',infoLabels="")
			xbmc.log(item.encode('utf-8'))
			if cat[0]=='video':			
				urlList = CMDTools.build_url(base_url,{'web':get_Web_Name(), 'link':img_src[26:-6], 'type':cat[0]})
			else:	
				img_link=(item.find('a'))['href']
				urlList = CMDTools.build_url(base_url,{'web':get_Web_Name(), 'link':img_link, 'type':cat[0]})
			xbmcplugin.addDirectoryItem(handle=addon_handle, url=urlList, listitem=li)			
		
		#Tao nut next	
		li = xbmcgui.ListItem("Next")	
		urlList=CMDTools.build_url(base_url,{'web':web_name, 'cat':cat[0],'page': page+1});
		xbmcplugin.addDirectoryItem(handle=addon_handle, url=urlList, listitem=li, isFolder=True)			
		return	