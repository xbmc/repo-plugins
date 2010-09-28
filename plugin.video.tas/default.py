#TAS by Insayne
import os,sys,time
import urllib,urllib2,re
import xbmcplugin,xbmcgui,xbmcaddon
from operator import itemgetter, attrgetter
from TasAPI import common as common
from TasAPI import cache as cache
from TasAPI import utilities as util

# plugin Constants
__plugin__ = "Tool-assisted Superplays"
__author__ = "Insayne (Code) & HannaK (Graphics)"
__url__ = "http://code.google.com/p/xbmc-plugin-video-tas/"
__svn_url__ = "https://xbmc-plugin-video-tas.googlecode.com/svn/trunk/plugin.videos.tas/"
__version__ = "1.0.3"
__svn_revision__ = "$Revision$"
__XBMC_Revision__ = xbmc.getInfoLabel('System.BuildVersion')
__settings__ = xbmcaddon.Addon(id='plugin.video.tas')

# Global Settings
set_snames = __settings__.getSetting( "snames" )
set_smethod = __settings__.getSetting( "smethod" )
set_dpath = __settings__.getSetting( "download_path" )

#Variables
dimg = xbmc.translatePath( os.path.join( os.getcwd(), 'Images', 'Icons' ) )
xbmcrev = str(xbmc.getInfoLabel('System.BuildVersion'))
xbmcrev = xbmcrev.split(" ",1)
UAS = "XBMC/"+xbmcrev[0]+" (Revision: "+xbmcrev[1].replace("r","")+") TAS-Videos/"+__version__+""
UAS = str(UAS)
prev_letter = "Unset"
sorting = 0

def init_addon():
	path = xbmc.translatePath(os.path.join('special://profile/addon_data/plugin.video.tas/' , 'cache', 'images'))
	if os.path.isdir(path)==False:
		os.makedirs(path)

	path = xbmc.translatePath(os.path.join('special://profile/addon_data/plugin.video.tas/' , 'cache', 'feeds'))
	if os.path.isdir(path)==False:
		os.makedirs(path)
		
	frf = xbmc.translatePath(os.path.join( 'special://profile/addon_data/plugin.video.tas/', 'startup.txt' ))
	firstrun = os.path.isfile(frf)
	if firstrun==False:
		dia_title = common.get_lstring(32000)
		dia_l1 = common.get_lstring(32001)
		dia_l2 = common.get_lstring(32002)
		dia_l3 = common.get_lstring(32003)
		dialog = xbmcgui.Dialog()
		ret = dialog.yesno(dia_title, dia_l1, dia_l2, dia_l3)
		if ret==1:	
			util.download_cache()
		
		file = open(frf, 'w')
		file.write("Startup Completed")
		file.close()


# Generates the main Index
def Generate_Index():
	dimg = common.get_image_path(xbmc.translatePath(os.path.join( os.getcwd(), 'resources', 'images', 'icons', 'default' )))
	latest = xbmc.translatePath(os.path.join(dimg, "latest.png"))
	notables = xbmc.translatePath(os.path.join(dimg, "not.png"))
	bbs = xbmc.translatePath(os.path.join(dimg, "bbs.png"))
	tools = xbmc.translatePath(os.path.join(dimg, "tools.png"))
	string_latest_videos = common.get_lstring(30800)
	string_notables = common.get_lstring(30801)
	string_bbs = common.get_lstring(30802)
	string_ad_util = common.get_lstring(30803)
	addDir(string_latest_videos,'http://tasvideos.org/publications.rss',2, latest, common.get_category_fanthumb("Latest Videos", "Fanart"))
	addDir(string_notables,'http://tasvideos.org/notables.rss',1, notables, common.get_category_fanthumb("Notables", "Fanart"))
	addDir(string_bbs,'http://tasvideos.org/systems.rss',1, bbs, common.get_category_fanthumb("Browse By System", "Fanart"))
	addDir(string_ad_util,'none',3, tools, common.get_category_fanthumb("Addon Utilities", "Fanart"))	

# Genereates the Tool-chain links
def Get_Tools():
	dimg = common.get_image_path(xbmc.translatePath(os.path.join( os.getcwd(), 'resources', 'images', 'icons', 'default' )))
	clean_rss = xbmc.translatePath(os.path.join(dimg, "clear_rss.png"))
	clean_ico = xbmc.translatePath(os.path.join(dimg, "clear_icons.png"))
	clean_all = xbmc.translatePath(os.path.join(dimg, "clear_cache.png"))
	dl = xbmc.translatePath(os.path.join(dimg, "dl_cache.png"))
	string_crss = common.get_lstring(30810)
	string_cthumb = common.get_lstring(30811)
	string_cboth = common.get_lstring(30812)
	string_cdlimg = common.get_lstring(30813)
	addLinkTool(string_crss, 'plugin://plugin.video.tas?mode=4&url=clean_rss', clean_rss)
	addLinkTool(string_cthumb, 'plugin://plugin.video.tas?mode=4&url=clean_ico', clean_ico)
	addLinkTool(string_cboth, 'plugin://plugin.video.tas?mode=4&url=clean_all', clean_all)
	addLinkTool(string_cdlimg, 'plugin://plugin.video.tas?mode=4&url=download_img', dl)

# Generates the Categories
def Get_Categories(url):
	link = cache.getcontent(url,UAS)
	link = link.replace("\r", "")
	link = link.replace("\n", "")
	match=re.compile('<item>.+?<title>(.+?)</title>.+?<link>(.+?)<\/link>').findall(link)
	for name,link in match:
		fanart = common.get_category_fanthumb(name, "Fanart")
		print fanart
		addDir(name,link,2,common.get_category_fanthumb(name, "Thumbnail"),fanart)

# Get Videos from RSS Feed - Fast Method
# This method relies on non-erroneous RSS entries (i.e, no empty Video Link)
# It can bug quite badly but its here for the slow machines
def Get_RSS_Videos_fast(url):
	global prev_letter
	global sorting
	sorting = common.getsorting(url)
	sort_letter = "None"
	link = cache.getcontent(url,UAS)
	link = link.replace("\r", "")
	link = link.replace("\n", "")
	match=re.compile('<item>.+?<title>\[(.+?)\] (.+?) (.+?)</title>.+?<description>(.+?)<\/description>.+?<author>(.+?)<\/author>.+?<category>(.+?)<comments>.+?<media:thumbnail url="(.+?)".+?<media:content url=".+?archive.org/(.+?)" type=".+?" medium="video" \/>.+?<media:starRating average="(.+?)".+?\/>.+?<pubDate>(.+?)<\/pubDate>.+?<\/item>').findall(link)
	totalitems = len(match)
	for num,platform,name,plot,director,categories,thumbnail,link,rating,pubdate in match:
		num = int(num)
		year = common.get_year(pubdate)
		date = common.get_date(pubdate)
		duration = common.get_duration(name)
		if sorting==1:
			if not prev_letter==name[:1]:
				prev_letter = name[:1]
				sort_letter = prev_letter
			else:
				sort_letter = "None"
		fanart = ""+str(num)+".png"
		fanart = xbmc.translatePath( os.path.join( os.getcwd(), 'Images', 'Fanart', 'Games', fanart ) )
		year = int(year)
		rating = round(float(rating),2)
		name = ""+name+" ["+str(rating)+"]"
		director = common.clean_director(director)
		category = "<category>"+categories+""
		genre = common.getgenres(category)
		categories = common.get_categories(category)
		writer = common.get_writer(name)
		thumbnail = cache.img_getcontent(thumbnail,num,UAS)
		url = "plugin://plugin.video.tas?mode=5&url=" + link
		addLink(common.cleanstring(name),url,thumbnail,year,plot,rating,director,writer,genre,categories,fanart,num,totalitems,date,sort_letter,duration)
	prev_letter = "Unset"
	return

# Get Videos from RSS Feed - Default Method
# This method should be 99% Accurate if not 100% but faster than the strict method.
def Get_RSS_Videos_default(url):
	global prev_letter
	global sorting
	sorting = common.getsorting(url)
	sort_letter = "None"
	link = cache.getcontent(url,UAS)
	link = link.replace("\r", "")
	link = link.replace("\n", "")
	match=re.compile('<item>.+?<title>\[(.+?)\] (.+?) (.+?)</title>.+?<description>(.+?)<\/description>.+?<author>(.+?)<\/author>.+?<category>(.+?)<comments>.+?<media:thumbnail url="(.+?)" \/>(.+?)<media:community>.+?<media:starRating average="(.+?)".+?\/>.+?<pubDate>(.+?)<\/pubDate>.+?<\/item>').findall(link)
	totalitems = len(match)
	for num,platform,name,plot,director,categories,thumbnail,link,rating,pubdate in match:
		link = common.get_video(link)
		if not link=="None":
			num = int(num)
			year = common.get_year(pubdate)
			date = common.get_date(pubdate)
			duration = common.get_duration(name)
			if sorting==1:
				if not prev_letter==name[:1]:
					prev_letter = name[:1]
					sort_letter = prev_letter
				else:
					sort_letter = "None"
			fanart = ""+str(num)+".png"
			fanart = xbmc.translatePath( os.path.join( os.getcwd(), 'Images', 'Fanart', 'Games', fanart ) )
			year = int(year)
			rating = round(float(rating),2)
			name = ""+name+" ["+str(rating)+"]"
			director = common.clean_director(director)
			category = "<category>"+categories+""
			genre = common.getgenres(category)
			categories = common.get_categories(category)
			writer = common.get_writer(name)
			thumbnail = cache.img_getcontent(thumbnail,num,UAS)
			url = "plugin://plugin.video.tas?mode=5&url=" + link
			addLink(common.cleanstring(name),url,thumbnail,year,plot,rating,director,writer,genre,categories,fanart,num,totalitems,date,sort_letter,duration)
		else:
			totalitems = totalitems - 1
	prev_letter = "Unset"
	return

# Get Videos from RSS Content - Strict Mode
# This employs a matching system with <item> </item>
# It is slower than any other method but 100% accurate
def Get_RSS_Videos_strict(url):
	global prev_letter
	global sorting
	sorting = common.getsorting(url)
	sort_letter = "None"
	link = cache.getcontent(url,UAS)
	link = link.replace("\r", "")
	link = link.replace("\n", "")
	nmatch = re.compile('<item>(.+?)<\/item>').findall(link)
	totalitems = len(nmatch)
	for link in nmatch:
		tmatch=re.compile('.+?<title>\[(.+?)\] (.+?) (.+?)</title>.+?<description>(.+?)<\/description>.+?<author>(.+?)<\/author>.+?<category>(.+?)<comments>.+?<media:thumbnail url="(.+?)".+?<media:content url=".+?archive.org/(.+?)" type=".+?" medium="video" \/>.+?<media:starRating average="(.+?)".+?\/>.+?<pubDate>(.+?)<\/pubDate>.+?').findall(link)
		for num,platform,name,plot,director,categories,thumbnail,link,rating,pubdate in tmatch:
			if not link=="":
				num = int(num)
				year = common.get_year(pubdate)
				date = common.get_date(pubdate)
				duration = common.get_duration(name)
				if sorting==1:
					if not prev_letter==name[:1]:
						prev_letter = name[:1]
						sort_letter = prev_letter
					else:
						sort_letter = "None"
				fanart = ""+str(num)+".png"
				fanart = xbmc.translatePath( os.path.join( os.getcwd(), 'Images', 'Fanart', 'Games', fanart ) )
				year = int(year)
				rating = round(float(rating),2)
				name = ""+name+" ["+str(rating)+"]"
				director = common.clean_director(director)
				category = "<category>"+categories+""
				genre = common.getgenres(category)
				categories = common.get_categories(category)
				writer = common.get_writer(name)
				thumbnail = cache.img_getcontent(thumbnail,num,UAS)
				url = "plugin://plugin.video.tas?mode=5&url=" + link
				addLink(common.cleanstring(name),url,thumbnail,year,plot,rating,director,writer,genre,categories,fanart,num,totalitems,date,sort_letter,duration)
			else:
				totalitems = totalitems - 1
	prev_letter = "Unset"
	return

# Add Link
# This is to add a video link in our list. Quite extensive in information
def addLink(name,url,iconimage,year,plot,rating,director,writer,genre,tagline,fanart,id,totalitems,date,sort_letter,duration):
	global set_pnames
	filecheck = os.path.isfile(fanart)
	name = str(name)
	if set_snames=="false":
		pname = name
	else:
		pname = common.get_prettyname(name)
	plot = common.clean_plot(plot)
	path = url
	ok=True
	liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
	if sort_letter=="None":
		liz.setInfo( type="Video", infoLabels={ "Title": pname, "Duration": duration, "Label": name, "date": date, "Year": year, "Plot":plot, "Rating":rating, "Path":path, "Director":director, "Genre":genre, "Tagline":tagline, "Writer":writer, "Studio": str(id)  } )
	else:
		liz.setInfo( type="Video", infoLabels={ "Title": pname, "Duration": duration, "Label": name, "SortLetter":sort_letter, "date": date, "Year": year, "Plot":plot, "Rating":rating, "Path":path, "Director":director, "Genre":genre, "Tagline":tagline, "Writer":writer, "Studio": str(id)  } )
	if filecheck==False:
		liz.setProperty("Fanart_image", iconimage)
	if filecheck==True:
		liz.setProperty("Fanart_image", fanart)
	liz.setProperty("IsPlayable","true");
	
	dlpatherror = 0
	
	if not set_dpath=="":
		if os.path.isdir(set_dpath)==True:
			dl = xbmc.translatePath(os.path.join( os.getcwd() , 'TasAPI', 'download.py'))
			turl = "http://www.archive.org/" + url.replace('plugin://plugin.video.tas?mode=5&url=', '')
			cm = [('Download Video', 'XBMC.RunScript(' + dl + ', ' + turl + ', ' + set_dpath + ')',)]
			liz.addContextMenuItems(cm)
		else:
			dlpatherror = 1
	else:
		dlpatherror = 1
		
	if dlpatherror==1:
		dl = xbmc.translatePath(os.path.join( os.getcwd() , 'TasAPI', 'download.py'))
		turl = "nofolder"
		cm = [('Download Video', 'XBMC.RunScript(' + dl + ', ' + turl + ')',)]
		liz.addContextMenuItems(cm)
		
	
	ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=liz,isFolder=False,totalItems=totalitems)
	return ok

# Add Link Tool
# This is the Add Link version to add tools - it requires much less parameters
# as we do not need as many.
def addLinkTool(name,url,iconimage):
	ok=True
	liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
	liz.setInfo( type="Video", infoLabels={ "Title": name } )
	ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=liz)
	return ok

# Add Directory
def addDir(name,url,mode,iconimage,Fanart):
	u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
	ok=True
	liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
	liz.setInfo( type="Video", infoLabels={ "Title": name } )
	if not Fanart=="":
		liz.setProperty("Fanart_image", Fanart)
	ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)
	return ok

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
	xbmcplugin.endOfDirectory(int(sys.argv[1]))
	init_addon()

	
# Mode 1:
# This Mode reads "Directories" or links to RSS Feeds and lists them
elif mode==1:
		Get_Categories(url)

# Mode 2:
# This Mode lists video content from an RSS Feed
elif mode==2:
		if set_smethod=="0":
			Get_RSS_Videos_fast(url)
		elif set_smethod=="1":
			Get_RSS_Videos_default(url)
		elif set_smethod=="2":
			Get_RSS_Videos_strict(url)
		else:
			Get_RSS_Videos_default(url)

# Mode 3:
# This Mode Lists the tool-chain of the Addon
elif mode==3:
	Get_Tools()

# Mode 4:
# This Mode gets a parameter as URL so we can do various tasks 
# It is currently in use to run addon built-in functions
elif mode==4:
	if url=="clean_rss":
		util.clean_rss()
			
	elif url=="clean_ico":
		util.clean_ico()

	elif url=="clean_all":
		util.clean_all()

	elif url=="download_img":
		util.download_cache()

# Mode 5:
# This mode is to grab the actual URL and pass it to XBMC
elif mode==5:
	newurl = common.ResolveURL(url)
	li=xbmcgui.ListItem(path = newurl)
	xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, li)

# Sorting Methods:
# Sorting order is added in different orders here dependant on the category, as it does defeine
# the default sorting type if the User has not interacted with it.
if sorting==1:
	xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_LABEL)
	xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_DATE)
	xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_RUNTIME)
	xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_RATING)
	xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_GENRE)
elif sorting==2:
	xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_DATE)
	xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_LABEL)
	xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_RUNTIME)
	xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_RATING)
	xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_GENRE)
elif sorting==3:
	xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_RATING)
	xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_DATE)
	xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_LABEL)
	xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_RUNTIME)
	xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_GENRE)

else:
	xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_NONE)
	
xbmcplugin.setContent(handle=int(sys.argv[1]), content="movies" )
xbmcplugin.endOfDirectory(int(sys.argv[1]))
