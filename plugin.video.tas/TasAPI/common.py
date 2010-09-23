#TAS Videos by Insayne
import os, time
import urllib,urllib2,re,httplib
import xbmc,xbmcaddon

__settings__ = xbmcaddon.Addon(id='plugin.video.tas')

# Global Settings
set_icon_size = __settings__.getSetting( "icon_size" )
set_fanart_size = __settings__.getSetting( "fanart_size" )

# This function Resolves the URL to the Final URL
# Used in Mode 5 
def ResolveURL(url):
	nurl = '/' + url
	domain = 'www.archive.org'
	conn = httplib.HTTPConnection(domain)
	conn.request("HEAD", nurl)
	res = conn.getresponse()
	if res.status==302:
		url = res.getheader('Location')
	else:
		url = domain + url
	conn.close()
	return url

# Get Fanart Image Path
# Using the settings, we define the Path for Fanart images
def get_fimage_path(path):
	global set_fanart_size
	if set_fanart_size=="0":
		endpath = xbmc.translatePath(os.path.join(path, "16-9_small" ))
	elif set_fanart_size=="1":
		endpath = xbmc.translatePath(os.path.join(path, "16-9_medium" ))
	elif set_fanart_size=="2":
		endpath = xbmc.translatePath(os.path.join(path, "16-9_high" ))
	elif set_fanart_size=="3":
		endpath = xbmc.translatePath(os.path.join(path, "4-3_small" ))
	elif set_fanart_size=="4":
		endpath = xbmc.translatePath(os.path.join(path, "4-3_medium" ))
	elif set_fanart_size=="5":
		endpath = xbmc.translatePath(os.path.join(path, "4-3_high" ))
	else:
		endpath = xbmc.translatePath(os.path.join(path, "16-9_medium" ))
	return endpath

# Get Image Path
# Using the settings, we define the Path for Thubmnail images
def get_image_path(path):
	global set_icon_size
	if set_icon_size=="0":
		endpath = xbmc.translatePath(os.path.join(path, "small" ))
	elif set_icon_size=="1":
		endpath = xbmc.translatePath(os.path.join(path, "medium" ))
	elif set_icon_size=="2":
		endpath = xbmc.translatePath(os.path.join(path, "high" ))
	else:
		endpath = xbmc.translatePath(os.path.join(path, "medium" ))
	return endpath

# Get Category Fanart or Thumbnail
# Based on names, we will give it different images, respecting the Settings too
def get_category_fanthumb(name,catfa):
	if catfa=="Thumbnail":
		dimg = get_image_path(xbmc.translatePath( os.path.join( os.getcwd(), 'resources', 'images', 'icons', 'categories' ) ))
	else:
		dimg = get_fimage_path(xbmc.translatePath( os.path.join( 'special://profile/addon_data/plugin.video.tas/', 'fanart', 'categories' ) ))
	noimg = get_image_path(xbmc.translatePath( os.path.join( os.getcwd(), 'resources', 'images', 'icons', 'default' ) ))
	# Main Categories
	if name=="Browse By System":
		thumbnail = xbmc.translatePath(os.path.join(dimg, "bbs.png"))
	elif name=="Notables":
		thumbnail = xbmc.translatePath(os.path.join(dimg, "not.png"))
	elif name=="Latest Videos":
		thumbnail = xbmc.translatePath(os.path.join(dimg, "latest.png"))
	elif name=="Addon Utilities":
		thumbnail = xbmc.translatePath(os.path.join(dimg, "tools.png"))

	# Browse By System
	elif name=="Arcade":
		thumbnail = xbmc.translatePath(os.path.join(dimg, "arcade.png"))
	elif name=="DOS":
		thumbnail = xbmc.translatePath(os.path.join(dimg, "dos.png"))
	elif name=="Famicom Disk System":
		thumbnail = xbmc.translatePath(os.path.join(dimg, "fds.png"))
	elif name=="Game Boy":
		thumbnail = xbmc.translatePath(os.path.join(dimg, "gb.png"))
	elif name=="Game Boy Advance":
		thumbnail = xbmc.translatePath(os.path.join(dimg, "gba.png"))
	elif name=="Game Boy Color":
		thumbnail = xbmc.translatePath(os.path.join(dimg, "gbc.png"))
	elif name=="Game Gear":
		thumbnail = xbmc.translatePath(os.path.join(dimg, "gg.png"))
	elif name=="Nintendo 64":
		thumbnail = xbmc.translatePath(os.path.join(dimg, "n64.png"))
	elif name=="Nintendo DS":
		thumbnail = xbmc.translatePath(os.path.join(dimg, "nds.png"))
	elif name=="Nintendo Entertainment System":
		thumbnail = xbmc.translatePath(os.path.join(dimg, "nes.png"))
	elif name=="Sega 32X":
		thumbnail = xbmc.translatePath(os.path.join(dimg, "32x.png"))
	elif name=="Sega CD":
		thumbnail = xbmc.translatePath(os.path.join(dimg, "scd.png"))
	elif name=="Sega Genesis":
		thumbnail = xbmc.translatePath(os.path.join(dimg, "gen.png"))
	elif name=="Sega MasterSystem":
		thumbnail = xbmc.translatePath(os.path.join(dimg, "sms.png"))
	elif name=="Sega Saturn":
		thumbnail = xbmc.translatePath(os.path.join(dimg, "sat.png"))
	elif name=="Sony PlayStation":
		thumbnail = xbmc.translatePath(os.path.join(dimg, "psx.png"))
	elif name=="Super Game Boy":
		thumbnail = xbmc.translatePath(os.path.join(dimg, "sgb.png"))
	elif name=="Super NES":
		thumbnail = xbmc.translatePath(os.path.join(dimg, "snes.png"))
	elif name=="TurboGrafx 16":
		thumbnail = xbmc.translatePath(os.path.join(dimg, "pce.png"))
	elif name=="TurboGrafx 16 CD":
		thumbnail = xbmc.translatePath(os.path.join(dimg, "pcecd.png"))
	elif name=="Virtual Boy":
		thumbnail = xbmc.translatePath(os.path.join(dimg, "vb.png"))
	
	# Notables Subcategory
	elif name=="Recommended Movies":
		thumbnail = xbmc.translatePath(os.path.join(dimg, "rmovies.png"))
	elif name=="Top Rated Movies":
		thumbnail = xbmc.translatePath(os.path.join(dimg, "pop.png"))
	# Awards
	elif not name.find("Award Winning Movies for")==-1:
		fn = "aw_" + name[-4:] + ".png"
		fn = xbmc.translatePath(os.path.join(dimg, fn))
		filecheck = os.path.isfile(fn)
		if filecheck==True:
			thumbnail = xbmc.translatePath(os.path.join(dimg, fn))
		else:
			thumbnail = xbmc.translatePath(os.path.join(dimg, "aw.png"))
		
	else:
		if catfa=="Thumbnail":
			thumbnail = xbmc.translatePath(os.path.join(noimg, "noimg.png"))
		else:
			thumbnail = ""

	filecheck = os.path.isfile(thumbnail)
	if filecheck==False:
		if catfa=="Thumbnail":
			thumbnail = xbmc.translatePath(os.path.join(noimg, "noimg.png"))
		else:
			thumbnail = ""
	return thumbnail

# Here comes a bunch of small functions to fix encoding issues of strings 
# and generally clean formatting

def cleanstring(strvar):
	string = strvar
	string = string.replace("&amp;", "&")
	string = string.replace("&quot;", "\"")
	return string

def fixtags(strvar):
	string = strvar
	string = string.replace('&lt;', '<')
	string = string.replace('&gt;', '>')
	return string

def cleanformatting(strvar):
	string = strvar
	string = string.replace('<p/>', '\n\n')
	string = string.replace('<br/>', '\n\n')
	string = remove_html_tags(string)
	return string

def remove_html_tags(strvar):
	string = strvar
	string = re.sub('<.+?>', '', string)
	return string
	
def clean_plot(strvar):
	string = strvar
	string = fixtags(string)
	string = cleanlinks_leave_text(string)
	string = cleanformatting(string)
	string = cleanstring(string)
	return string
	
def get_year(strvar):
	match=re.compile('.+?, .+? .+? (.+?) .+? .+?').findall(strvar)
	for year in match:
		years = year
	return int(years)
	
def get_month(abmon):
	if (abmon=="Jan"):
		return 1
	elif (abmon=="Feb"):
		return 2
	elif (abmon=="Mar"):
		return 3
        elif (abmon=="Apr"):
		return 4
	elif (abmon=="May"):
		return 5
	elif (abmon=="Jun"):
		return 6
	elif (abmon=="Jul"):
		return 7
	elif (abmon=="Aug"):
		return 8
	elif (abmon=="Sep"):
		return 9
	elif (abmon=="Oct"):
		return 10
	elif (abmon=="Nov"):
		return 11
	elif (abmon=="Dec"):
		return 12
	raise ValueError("can't parse month abbreviation:  abmon=%s " % (monab))

		
def get_date(strvar):
	match=re.compile('.+?, (.+?) (.+?) (.+?) .+?').findall(strvar)
	for day,abmon,year in match:
		datestring = day+"."+str(get_month(abmon))+"."+year
	return datestring

	
def clean_director(strvar):
	match=re.compile('.+? \((.+?)\)').findall(strvar)
	directors = ""
	for director in match:
		directors = ""+directors+""+director+""
	return directors

def get_writer(strvar):
	match=re.compile('.+?by (.+?) in.+?').findall(strvar)
	writers = ""
	for writer in match:
		writers = ""+writers+""+writer+""
	return cleanstring(writers)
	
def getgenres(strvar):
	string = strvar
	genres = ""
	match=re.compile('<category>Genre: (.+?)<\/category>.+?').findall(string)
	for genre in match:
		genres = ""+genres+"/"+genre+""
	return genres[1:]
	
def removelink(strvar):
	string = strvar
	match=re.search('<a href=.+?>(.+?)</a>', string)
	matchresult = str(match)
	if matchresult=="None":
		inby = string
	else:
		match=re.compile('(.+?)<a href=".+?">(.+?)</a>').findall(string)
		for time,by in match:
			inby = ""+time+""+by+""
	return inby

def get_categories(strvar):
	string = clean_from_genres(strvar)
	categories = ""
	match=re.compile('<category>(.+?)<\/category>.+?').findall(string)
	for category in match:
		categories = ""+categories+"/"+category+""
	if categories=="":
		categories=" Unknown"
	return categories[1:]

def getsorting(url):
	match=re.compile('http://tasvideos.org/(.+?)/.+?').findall(url)
	for result in match:
		category = result
		
	if url=="http://tasvideos.org/publications.rss":
		sorting = 2
	elif category=="notable-feed":
		sorting = 3
	else:
		sorting = 1
	return sorting

def get_video(string):
	vid_list = []
	match=re.compile('.+?<media:content url="http://.+?archive.org/(.+?)" type=".+?" medium="video" />.+?').findall(string)
	for vid in match:
		vid_list.append(vid)
		
	if len(vid_list)==0:
		vid_list = ["None"]

	return vid_list[0]
	
def get_prettyname(name):
	name = "<start>"+name+""
	match=re.compile('<start>(.+?) by .+?').findall(name)
	for name in match:
		prettyname = name
	return prettyname
		
def get_duration(name):
	match=re.compile('.+? in (.+?) .+?').findall(name)
	for duration in match:
		timestring = duration
	timecheck = timestring.count(":")
	
	if timecheck==1:
		hours = '%02d' % 0
		minutes = '%02d' % int(timestring.split(":", timecheck)[0])
		seconds = timestring.split(":", timecheck)[1]
		seconds = '%02d' % int(seconds.split(".", 1)[0])
		duration = ""+str(hours)+":"+str(minutes)+":"+str(seconds)+""

	elif timecheck==2:
		hours = '%02d' % int(timestring.split(":", timecheck)[0])
		minutes = '%02d' % int(timestring.split(":", timecheck)[1])
		seconds = timestring.split(":", timecheck)[2]
		seconds = '%02d' % int(seconds.split(".", 1)[0])
		duration = ""+str(hours)+":"+str(minutes)+":"+str(seconds)+""
	else:
		duration = "00:00:00"
		
	return duration

def clean_from_genres(strvar):
	string = strvar
	string = re.sub('<category>Genre:.+?</category>', '', string)
	return string
	
def cleanlinks_leave_text(strvar):
	string = strvar
	string = re.sub('<a.+?href=.+?">', '', string)
	string = re.sub('<\/a>', '', string)
	return string

def convert_bytes(bytes):
    bytes = float(bytes)
    if bytes >= 1099511627776:
        terabytes = bytes / 1099511627776
        size = '%.2fT' % terabytes
    elif bytes >= 1073741824:
        gigabytes = bytes / 1073741824
        size = '%.2fG' % gigabytes
    elif bytes >= 1048576:
        megabytes = bytes / 1048576
        size = '%.2fM' % megabytes
    elif bytes >= 1024:
        kilobytes = bytes / 1024
        size = '%.2fK' % kilobytes
    else:
        size = '%.2fb' % bytes
    return size