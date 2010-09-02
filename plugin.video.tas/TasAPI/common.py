#TAS Videos by Insayne
import os, time
import urllib,urllib2,re
import xbmc,xbmcaddon

__settings__ = xbmcaddon.Addon(id='plugin.video.tas')

# Global Settings
set_icon_size = __settings__.getSetting( "icon_size" )
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

def get_category_fanthumb(name,catfa):
	if catfa=="Thumbnail":
		dimg = get_image_path(xbmc.translatePath( os.path.join( os.getcwd(), 'resources', 'images', 'icons', 'categories' ) ))
	else:
		dimg = get_image_path(xbmc.translatePath( os.path.join( os.getcwd(), 'resources', 'images', 'icons', 'fanart' ) ))
	noimg = get_image_path(xbmc.translatePath( os.path.join( os.getcwd(), 'resources', 'images', 'icons', 'default' ) ))
	if name=="Arcade":
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
		
	# Here comes the Notables Block

	elif name=="Recommended Movies":
		thumbnail = xbmc.translatePath(os.path.join(dimg, "rmovies.png"))
	elif name=="Top Rated Movies":
		thumbnail = xbmc.translatePath(os.path.join(dimg, "pop.png"))
	elif name=="Virtual Boy":
		thumbnail = xbmc.translatePath(os.path.join(dimg, "vb.png"))
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
	
# Here we remove ugly strings - so it looks nice (encoding ones)
def cleanstring(strvar):
	string = strvar
	string = string.replace("&amp;", "&")
	string = string.replace("&quot;", "\"")
	return string

# Here we remove ugly strings - so it looks nice (encoding ones)
def fixtags(strvar):
	string = strvar
	string = string.replace('&lt;', '<')
	string = string.replace('&gt;', '>')
	return string

# Here we remove ugly strings - so it looks nice (encoding ones)
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
	
def get_date(strvar):
	match=re.compile('.+?, (.+?) (.+?) (.+?) .+?').findall(strvar)
	for day,mon,year in match:
		datestring = day + mon + year
		date = time.strptime(datestring,"%d%b%Y")
	return str(time.strftime("%d.%m.%Y",date))
	
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
	
# Utility - Removes links from a string
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
	link=""
	match=re.compile('.+?<media:content url="http://.+?archive.org/(.+?)" type=".+?" medium="video" />.+?').findall(string)
	for vid in match:
		link = vid
	
	if link=="":
		link = "None"
	return link
	
	
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

def context_remove_feed(url):
	c_feed_file = xbmc.translatePath(os.path.join( os.getcwd(), 'TasAPI', 'test.py'))
	tfn = url.rsplit('/',1)
	tfn = tfn[-1]
	c_feed_arg = xbmc.translatePath(os.path.join( os.getcwd(), 'resources', 'cache', 'feeds', tfn ))
	c_feed = 'XBMC.RunScript(' + c_feed_file + ', category, removefeed, ' + c_feed_arg + ')'
	contextmenu = [('Delete Cached Feed', c_feed,)]
	return contextmenu

def clean_from_genres(strvar):
	string = strvar
	string = re.sub('<category>Genre:.+?</category>', '', string)
	return string
	
def cleanlinks_leave_text(strvar):
	string = strvar
	string = re.sub('<a.+?href=.+?">', '', string)
	string = re.sub('<\/a>', '', string)
	return string