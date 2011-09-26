# Wimp.com by Insayne

import os,sys,time
import urllib,urllib2,re
import xbmcplugin,xbmcgui,xbmcaddon

# plugin Constants
__plugin__ = "Wimp.com"
__author__ = "Insayne"
__url__ = "http://code.google.com/p/insayne-projects/"
__svn_url__ = "https://insayne-projects.googlecode.com/svn/trunk/XBMC/Video/plugin.video.wimp/"
__version__ = "0.6"
__svn_revision__ = "$Revision$"
__XBMC_Revision__ = xbmc.getInfoLabel('System.BuildVersion')
__settings__ = xbmcaddon.Addon(id='plugin.video.wimp')

# Global Setting Variables
set_video_type = __settings__.getSetting( "video_type" )

# Generates the main Index
def Generate_Index():
	url = 'http://wimp.com/'
	req = urllib2.Request(url)
	response = urllib2.urlopen(req)
	html=response.read()
	response.close()
	html = html.replace("\n", "")
	html = html.replace("\r", "")
	thumb = ''
	regex = '<span class="video_date">(.+?)</span> - <a class=".+?" href="(.+?)">(.+?)</a><br/>'
	videos = re.compile(regex).findall(html)
	
	for date,link,title in videos:
		link = 'http://wimp.com' + link
		title = "[" + date + "] " + cleanstring(remove_spaces(title))
		addVideo(title,link,1, thumb)

	root_path = xbmc.translatePath(__settings__.getAddonInfo('path'))
	thumb = xbmc.translatePath(os.path.join( root_path, 'resources', 'images', 'archives.png'))
	link = '1'
	title = "[Archives]"
	addDir(title,link,3, thumb)

def get_archives():
	# Request the Page
	url = 'http://wimp.com/archives/'
	req = urllib2.Request(url)
	response = urllib2.urlopen(req)
	html=response.read()
	response.close()
	html = html.replace("\n", "")
	html = html.replace("\r", "")
	thumb = ''
	regex = '<a class="b" href="(.+?)">(.+?)</a><br/>'
	videos = re.compile(regex).findall(html)
	

	
	for link,title in videos:
		link = 'http://wimp.com' + link
		title = cleanstring(remove_spaces(title))
		addDir(title,link,2, thumb)
	
	# Link back to Current Month
	root_path = xbmc.translatePath(__settings__.getAddonInfo('path'))
	thumb = xbmc.translatePath(os.path.join( root_path, 'resources', 'images', 'back.png'))
	link = ""
	title = "<< Back to Current Month"
	addDir(title,link,4, thumb)


def Generate_archive_page(link):
	# Request the Page
	url = str(link)
	req = urllib2.Request(url)
	response = urllib2.urlopen(req)
	html=response.read()
	response.close()
	html = html.replace("\n", "")
	html = html.replace("\r", "")
	thumb = ''
	regex = '<span class="video_date">(.+?)</span> - <a class=".+?" href="(.+?)">(.+?)</a><br/>'
	videos = re.compile(regex).findall(html)
	
	for date,link,title in videos:
		link = 'http://wimp.com' + link
		title = "[" + date + "] " + cleanstring(remove_spaces(title))
		addVideo(title,link,1, thumb)
	
	root_path = xbmc.translatePath(__settings__.getAddonInfo('path'))
	thumb = xbmc.translatePath(os.path.join( root_path, 'resources', 'images', 'archives.png'))
	link = ""
	title = "<< Back to Archives Listing"
	addDir(title,link,3, thumb)
	
	
def Play_Video(url):
	global set_video_type
	
	# Request the Page
	req = urllib2.Request(url)
	response = urllib2.urlopen(req)
	html=response.read()
	response.close()
		
	html = html.replace("\n", "")
	html = html.replace("\r", "")

	if "www.dump.com" in response.geturl():
		regex = '<script type="text/javascript">jwplayer\(.+?\).setup\(.+?file: "(.+?)".+?</script>'
		video_urls = re.compile(regex).findall(html)
		videos = []
		for link in video_urls:
			videos.append(link)
		if len(videos) > 0:
			return videos[0]
		else:
			return "ERROR"
			
	else:
		# Get the Stream Type
		if set_video_type=="0":
			# Flash 
			regex = 's1.addVariable\("file","(.+?)"'
		elif set_video_type=="1":
			# Mobile Device
			regex = '<div id="player">.+?<a target="_self".+?href="(.+?)".+?</div>'
		else:
			# Fallback to Flash
			regex = 's1.addVariable\("file","(.+?)"'
			
		video_urls = re.compile(regex).findall(html)
		videos = []
		for link in video_urls:
			videos.append(link)
		
		if len(videos) > 0:
			return videos[0]
		else:
			return "ERROR"

# Add Video
def addVideo(name,url,mode,iconimage):
	u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
	ok=True
	liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
	liz.setInfo( type="Video", infoLabels={ "Title": name } )
	liz.setProperty("Fanart_image", iconimage)
	liz.setProperty("IsPlayable","true")
	ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=False)
	return ok
	
# Add Directory
def addDir(name,url,mode,iconimage):
	u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
	ok=True
	liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
	liz.setInfo( type="Video", infoLabels={ "Title": name } )
	liz.setProperty("Fanart_image", iconimage)
	ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)
	return ok

# Clean the String 
def cleanstring(string):
	string = string.replace("&amp;", "&")
	string = string.replace("&quot;", "\"")
	return string

# Remove double spaces, etc
def remove_spaces(string):
	newstrg=''
	for word in string.split():
		newstrg=newstrg+' '+word
	return newstrg

def get_params():
        param=[]
        paramstring=sys.argv[2]
        if len(paramstring)>=2:
                params=sys.argv[2]
                cleanedparams=params.replace('?','')
                if (params[len(params)-1]=='/'):
                        params=params[0:len(params)-2]
                pairsofparams=cleanedparams.split('&')
                param={}
                for i in range(len(pairsofparams)):
                        splitparams={}
                        splitparams=pairsofparams[i].split('=')
                        if (len(splitparams))==2:
                                param[splitparams[0]]=splitparams[1]
                                
        return param

params=get_params()
url=None
name=None
mode=None

try:
        url=urllib.unquote_plus(params["url"])
except:
        pass
try:
        name=urllib.unquote_plus(params["name"])
except:
        pass
try:
        mode=int(params["mode"])
except:
        pass

if mode==None or url==None or len(url)<1:
	Generate_Index()


elif mode==1:
	video_url = Play_Video(url)
	if video_url!="ERROR":
		li=xbmcgui.ListItem(path = video_url)
		xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, li)

elif mode==2:
	Generate_archive_page(url)

elif mode==3:
	get_archives()

elif mode==4:
	Generate_Index()
	
xbmcplugin.setContent(handle=int(sys.argv[1]), content="movies" )
xbmcplugin.endOfDirectory(int(sys.argv[1]))
