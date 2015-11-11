import sys
import urllib
import urlparse
import xbmcgui
import xbmcplugin
import xbmcaddon
import xbmc
import requests
import webbrowser
from bs4 import BeautifulSoup 
from lib import CMDTools
import datetime

base_url = sys.argv[0]
web_name="TALKVN.VN"
web_url = "http://talktv.vn/" 

def get_Web_Name():
	return web_name
def get_img_thumb_url():
	return CMDTools.get_path_img('resources/media/talktv.png')
    
def view():		
	addon_handle = int(sys.argv[1])
	addon       = xbmcaddon.Addon()
	addonname   = addon.getAddonInfo('name')
	
	args = urlparse.parse_qs(sys.argv[2][1:])

	xbmcplugin.setContent(addon_handle, 'movies')

	cat=args.get('cat', None)
	page = args.get('page', None)
	link = args.get('link', None)	
	
	catalogues=[{'label':'\x44\x61\x6E\x68\x20\x73\xC3\xA1\x63\x68\x20\x63\xC3\xA1\x63\x20\x6B\xC3\xAA\x6E\x68\x20\xC4\x91\x61\x6E\x67\x20\x63\x68\x69\xE1\xBA\xBF\x75'.decode('utf-8'),'id':'http://talktv.vn/browse/channels'},
	{'label':'\x47\x69\xE1\xBA\xA3\x69\x20\x54\x72\xC3\xAD'.decode('utf-8'),'id':'http://talktv.vn/browse/channels/151/Gi%E1%BA%A3i%20Tr%C3%AD'},
	{'label':'\x4C\x69\xC3\xAA\x6E\x20\x4D\x69\x6E\x68\x20\x48\x75\x79\xE1\xBB\x81\x6E\x20\x54\x68\x6F\xE1\xBA\xA1\x69'.decode('utf-8'),'id':'http://talktv.vn/browse/channels/112/Li%C3%AAn%20Minh%20Huy%E1%BB%81n%20Tho%E1%BA%A1i'},
	{'label':'\x56\x69\x64\x65\x6F\x20\x54\x75\xE1\xBA\xA7\x6E'.decode('utf-8'),'id':'http://talktv.vn/browse/videos/ajax-get-videos/page/week'},
	{'label':'\x56\x69\x64\x65\x6F\x20\x54\x68\xC3\xA1\x6E\x67'.decode('utf-8'),'id':'http://talktv.vn/browse/videos/ajax-get-videos/page/month'},
	{'label':'\x54\xE1\xBA\xA5\x74\x20\x63\xE1\xBA\xA3\x20\x56\x69\x64\x65\x6F'.decode('utf-8'),'id':'http://talktv.vn/browse/videos/ajax-get-videos/page/all'}]
	
		
	#play link
	if link!=None:		
		xbmc.log("--------------------:"+link[0])
		link_video=link[0]
		if (link_video.startswith('http://talktv.vn/video')):
			link_get_url=link_video
			r = requests.get(link_get_url)
			html_data = r.text			
			start_pos = html_data.find('loadVideo.mp4')
			start_pos = html_data.find('\"',start_pos)+1
			end_pos = html_data.find('\"',start_pos)-len(html_data)
			link_video=html_data[start_pos:end_pos]
			#xbmc.log("@@@"+link_video.encode('utf-8'))
			#link_video=json_data["manifestUrl"]
			xbmc.Player().play(link_video)			
		elif (link_video.startswith('http://talktv.vn/')):
			channel=link_video[len(web_url):]
			if channel.isdigit():				
				if channel=='2222':
					channel='30001'
				link_get_url="http://49.213.74.237/"+channel		
				r = requests.get(link_get_url)
				json_data = r.json()
				link_video=json_data["TALK_LIVE_URL"]
				link_video1=link_video[:(len(json_data)-link_video.find(';')-2)]
				link_video2=link_video[link_video.find(';')+1:]								
				
				#osWin = xbmc.getCondVisibility('system.platform.windows')
				#osOsx = xbmc.getCondVisibility('system.platform.osx')
				#osLinux = xbmc.getCondVisibility('system.platform.linux')
				#osAndroid = xbmc.getCondVisibility('System.Platform.Android')

				url = link_video1				
				
				#f = open(xbmcaddon.Addon().getSetting("file")+'\\ADM.txt', 'w')
				#f.write(link_video1+"\n")
				#f.write(link_video2)
				#f.close()
				#if osAndroid:
					# ___ Open media with standard android web browser
					#if page[0]!='0':
						#xbmc.executebuiltin("StartAndroidActivity(com.android.chrome,,,"+url+")")
						#xbmc.executebuiltin("StartAndroidActivity(com.android.browser,android.intent.action.VIEW,,"+url+")")
					#else:
						#xbmc.log(channel+": "+link_video1)
					# ___ Open media with Mozilla Firefox
					#xbmc.executebuiltin("StartAndroidActivity(org.mozilla.firefox,android.intent.action.VIEW,,"+url+")")                    
					
					# ___ Open media with Chrome
					#xbmc.executebuiltin("StartAndroidActivity(com.android.chrome,,,"+url+")")				
				xbmc.Player().play(link_video1)
			else:
				link_get_url="http://talktv.vn/streaming/play/get-stream-data/channel/"+channel+"/limit/1"
				r = requests.get(link_get_url)
				json_data = r.json()
				link_video=json_data["manifestUrl"]
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
			page=0
		else:
			page=int(page[0])
			
		r = requests.get(cat[0].replace('page',str(page)))
		html = r.text				
		soup = BeautifulSoup(html)
		data_List=soup.findAll('div',attrs={'class':'cellitem'})
		#load item menu
		for item in data_List:			
			link_item=item.find('a', attrs={'class':'cellthumb'}).get('href')
			img_item=item.find('img').get('data-src')
			img_avt=item.find('a', attrs={'class':'profileavt'}).find('img').get('src')
			text_item=item.find('p', attrs={'class':'txtname'}).find('strong').getText()
			
			li = xbmcgui.ListItem(text_item)
			
			channel=link_item[len(web_url):]
			if channel.isdigit():
				li.setThumbnailImage(img_avt)
			else:
				li.setThumbnailImage(img_item)
			li.setInfo(type='image',infoLabels=text_item)					
						
			urlList = CMDTools.build_url(base_url,{'web':get_Web_Name(), 'link':link_item.encode('utf-8'), 'type':cat[0], 'page':str(page)})
			xbmcplugin.addDirectoryItem(handle=addon_handle, url=urlList, listitem=li)			
		
		#Tao nut next	
		li = xbmcgui.ListItem("Next")	
		urlList=CMDTools.build_url(base_url,{'web':web_name, 'cat':cat[0],'page': page+1});
		xbmcplugin.addDirectoryItem(handle=addon_handle, url=urlList, listitem=li, isFolder=True)	
		return