#TAS Videos by Insayne
import os,sys,time
import urllib,urllib2,re
import xbmcplugin,xbmcgui,xbmcaddon
from operator import itemgetter, attrgetter
from TasAPI import common as common
from TasAPI import cache as cache

# plugin Constants
__plugin__ = "Tool-assisted Speedruns"
__author__ = "Insayne (Code) & HannaK (Graphics)"
__url__ = "http://code.google.com/p/xbmc-plugin-video-tas/"
__svn_url__ = "https://xbmc-plugin-video-tas.googlecode.com/svn/trunk/plugin.videos.tas/"
__version__ = "0.94"
__svn_revision__ = "$Revision$"
__XBMC_Revision__ = xbmc.getInfoLabel('System.BuildVersion')
__settings__ = xbmcaddon.Addon(id='plugin.video.tas')

# Global Settings
set_snames = __settings__.getSetting( "snames" )
set_smethod = __settings__.getSetting( "smethod" )
set_umethod = __settings__.getSetting( "umethod" )

#Variables
dimg = xbmc.translatePath( os.path.join( os.getcwd(), 'Images', 'Icons' ) )
xbmcrev = str(xbmc.getInfoLabel('System.BuildVersion'))
xbmcrev = xbmcrev.split(" ",1)
UAS = "XBMC/"+xbmcrev[0]+" (Revision: "+xbmcrev[1].replace("r","")+") TAS-Videos/"+__version__+""
UAS = str(UAS)
prev_letter = "Unset"
sorting = 0

def Generate_Index():
	dimg = common.get_image_path(xbmc.translatePath(os.path.join( os.getcwd(), 'resources', 'images', 'icons', 'default' )))
	latest = xbmc.translatePath(os.path.join(dimg, "latest.png"))
	notables = xbmc.translatePath(os.path.join(dimg, "not.png"))
	bbs = xbmc.translatePath(os.path.join(dimg, "bbs.png"))
	addDir('Latest Videos','http://tasvideos.org/publications.rss',2, latest, common.get_category_fanthumb("Latest Videos", "Fanart"))
	addDir('Notables','http://tasvideos.org/notables.rss',1, notables, common.get_category_fanthumb("Notables", "Fanart"))
	addDir('Browse by System','http://tasvideos.org/systems.rss',1, bbs, common.get_category_fanthumb("Browse by System", "Fanart"))
	
def Get_Categories(url):
	link = cache.getcontent(url,UAS)
	link = link.replace("\r", "")
	link = link.replace("\n", "")
	match=re.compile('<item>.+?<title>(.+?)</title>.+?<link>(.+?)<\/link>').findall(link)
	for name,link in match:
		fanart = common.get_category_fanthumb(name, "Fanart")
		addDir(name,link,2,common.get_category_fanthumb(name, "Thumbnail"),fanart)

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
		if set_umethod=="0":
			url = "http://www.archive.org/" + link
		elif set_umethod=="1":
			url = "http://www.insayne.net/xbmc/tas.php?url=http://www.archive.org/"+link+""
		else:
			url = "http://www.archive.org/" + link
		addLink(common.cleanstring(name),url,thumbnail,year,plot,rating,director,writer,genre,categories,fanart,num,totalitems,date,sort_letter,duration)
	prev_letter = "Unset"
	return

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
			if set_umethod=="0":
				url = "http://www.archive.org/" + link
			elif set_umethod=="1":
				url = "http://www.insayne.net/xbmc/tas.php?url=http://www.archive.org/"+link+""
			else:
				url = "http://www.archive.org/" + link
			addLink(common.cleanstring(name),url,thumbnail,year,plot,rating,director,writer,genre,categories,fanart,num,totalitems,date,sort_letter,duration)
		else:
			totalitems = totalitems - 1
	prev_letter = "Unset"
	return

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
				if set_umethod=="0":
					url = "http://www.archive.org/" + link
				elif set_umethod=="1":
					url = "http://www.insayne.net/xbmc/tas.php?url=http://www.archive.org/"+link+""
				else:
					url = "http://www.archive.org/" + link
				addLink(common.cleanstring(name),url,thumbnail,year,plot,rating,director,writer,genre,categories,fanart,num,totalitems,date,sort_letter,duration)
			else:
				totalitems = totalitems - 1
	prev_letter = "Unset"
	return

def addLink(name,url,iconimage,year,plot,rating,director,writer,genre,tagline,fanart,id,totalitems,date,sort_letter,duration):
	global set_pnames
	filecheck = os.path.isfile(fanart)
	name = str(name)
	if set_snames=="false":
		pname = name
	else:
		pname = common.get_prettyname(name)
	plot = common.clean_plot(plot)
	path = url.replace('http://www.insayne.net/xbmc/tas.php?url=', "")
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
	ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=liz,totalItems=totalitems)
	return ok

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
       
elif mode==1:
		Get_Categories(url)

elif mode==2:
		if set_smethod=="0":
			Get_RSS_Videos_fast(url)
		elif set_smethod=="1":
			Get_RSS_Videos_default(url)
		elif set_smethod=="2":
			Get_RSS_Videos_strict(url)
		else:
			Get_RSS_Videos_default(url)
		
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
