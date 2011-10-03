# Dump.com by Insayne

import os,sys,time
import urllib,urllib2,re
import xbmcplugin,xbmcgui,xbmcaddon

# plugin Constants
__plugin__ = "Dump.com"
__author__ = "Insayne"
__url__ = "http://code.google.com/p/insayne-projects/"
__svn_url__ = "https://insayne-projects.googlecode.com/svn/trunk/XBMC/Video/plugin.video.dump/"
__version__ = "0.2"
__svn_revision__ = "$Revision$"
__XBMC_Revision__ = xbmc.getInfoLabel('System.BuildVersion')
__settings__ = xbmcaddon.Addon(id='plugin.video.dump')

# Archive Listing
def get_archives():
	url = 'http://www.dump.com/'
	req = urllib2.Request(url)
	response = urllib2.urlopen(req)
	html=response.read()
	response.close()
	html = html.replace("\n", "")
	html = html.replace("\r", "")
	thumb = ''
	regex = '<li><a href=\'(.+?)\' title=\'.+?\'>(.+?)<span>(.+?) Posts</span></a></li>'
	archives = re.compile(regex).findall(html)
	for link,title,posts in archives:
			title = cleanstring(remove_spaces(title))
			link = link + "|" + posts
			addDir(title,link,3,thumb)
			
# Page Generator	
def Generate_Page(date,page):
	url = 'http://www.dump.com'
	page = int(page)
	if page!=1:
		url = url + "/" + date + "/page/" + str(page)
	else:
		url = url + "/" + date
	url = url.replace('.com//', '.com/')

   
	req = urllib2.Request(url)
	response = urllib2.urlopen(req)
	html=response.read()
	response.close()
	html = html.replace("\n", "")
	html = html.replace("\r", "")
	thumb = ''
	regex = '<h2><a href="(.+?)" rel="bookmark" title=".+?">(.+?)</a></h2>.+?<span class="date">(.+?)</span>.+?autostart: false,image: "(.+?)",flashplayer: "http://www.dump.com/player/player.swf"'
	videos = re.compile(regex).findall(html)

	for link,title,date,thumb in videos:
		title = "[" + date + "] " + cleanstring(remove_spaces(title))
		addVideo(title,link,1, thumb)
	
	
# Link Handler
def lh(url):
		link = url
		link = link.replace("http://www.dump.com/", "")
		argvs = len(link.split("/",-1))
		if argvs > 1:
				argv1 = link.split("/",-1)[0]
				argv2 = link.split("/",-1)[1]
				argv3 = link.split("/",-1)[2]
		else:
				argv1 = "Empty"
				argv2 = "Empty"
				Generate_Page("", 1)
				
		if argv1 == "page":
				Generate_Page("", argv2)
		elif argv1.isdigit():
				if argvs <= 3:
						date = argv1 + "/" + argv2
						Generate_Page(date, 1)
				else:
						argv4 = link.split("/",-1)[3]
						argv5 = link.split("/",-1)[4]
						date = argv1 + "/" + argv2
						page = argv4
						Generate_Page(date, page)

# Month Generator
def Generate_Month(url,posts,mode):
	if url == "None":
		url = 'http://www.dump.com/'
	if posts == "None":
		posts = "None"

	# Here we create the index Page (Bottom should have archives
	if mode=="index":
		req = urllib2.Request(url)
		response = urllib2.urlopen(req)
		html=response.read()
		response.close()
		html = html.replace("\n", "")
		html = html.replace("\r", "")
		thumb = ''
		regex = '<li><a href=\'(.+?)\' title=\'.+?\'>(.+?)<span>(.+?) Posts</span></a></li>'
		archives = re.compile(regex).findall(html)
		titles = []
		links = []
		posts = []
		for link,title,post in archives:
				title = "[" + post + " Posts] " + cleanstring(remove_spaces(title))
				titles.append(title)
				links.append(link)
				posts.append(post)

		title = titles[0]
		link = links[0]
		post = posts[0]
		
		pages = int(post) / 5
		pages = pages + 1
		
		global posts_max
		posts_max = int(post)

		for page in range(1,pages):
			lhurl = link + "page/" + str(page) + "/"
			lh(lhurl)
	
	else:
		pages = int(posts) / 5
		pages = pages + 1
		link = url
		for page in range(1,pages):
			lhurl = link + "page/" + str(page) + "/"
			lh(lhurl)
			

			
	
def Play_Video(url):
	global set_video_type
	
	# Request the Page
	req = urllib2.Request(url)
	response = urllib2.urlopen(req)
	html=response.read()
	response.close()
		
	html = html.replace("\n", "")
	html = html.replace("\r", "")

	regex = '<script type="text/javascript">jwplayer\(.+?\).setup\(.+?file: "(.+?)".+?</script>'
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
	global posts_max
	u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
	ok=True
	liz=xbmcgui.ListItem(name, iconImage=iconimage, thumbnailImage=iconimage)
	liz.setInfo( type="Video", infoLabels={ "Title": name } )
	liz.setProperty("Fanart_image", iconimage)
	liz.setProperty("IsPlayable","true")
	ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=False,totalItems=posts_max)
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
	string = string.replace("[VIDEO]", "")
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
	Generate_Month("None", "None", "index")
	#Archive Link
	thumb = ''
	link = "Empty"
	title = "[Archives]"
	addDir(title,link,2,thumb)

elif mode==1:
	video_url = Play_Video(url)
	if video_url!="ERROR":
		li=xbmcgui.ListItem(path = video_url)
		xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, li)

elif mode==2:
	get_archives()

elif mode==3:

	# Prepare Month Data
	link = url.split("|")[0]
	posts = url.split("|")[1]
	global posts_max
	posts_max = int(posts)
	
	# Generate the Month
	Generate_Month(link, posts, "Other")
	
xbmcplugin.setContent(handle=int(sys.argv[1]), content="movies" )
xbmcplugin.endOfDirectory(int(sys.argv[1]))
