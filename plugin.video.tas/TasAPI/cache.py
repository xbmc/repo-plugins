import os, time
import urllib,urllib2
import xbmc,xbmcaddon

__settings__ = xbmcaddon.Addon(id='plugin.video.tas')

# Global Settings
set_rss_interval = __settings__.getSetting( "feed_update" )
set_image_interval = __settings__.getSetting( "image_update" )

# Function to get the RSS interval from settings
def get_rss_interval():
	global set_rss_interval
	if set_rss_interval=="0":
		rss_interval = 60
	elif set_rss_interval=="1":
		rss_interval = 120
	elif set_rss_interval=="2":
		rss_interval = 240
	elif set_rss_interval=="3":
		rss_interval = 360
	elif set_rss_interval=="4":
		rss_interval = 720
	elif set_rss_interval=="5":
		rss_interval = 1440
	elif set_rss_interval=="6":
		rss_interval = 0
	else:
		rss_interval = 60
	return rss_interval

# Function to get the Image interval from settings
def get_image_interval():
	global set_image_interval
	if set_image_interval=="0":
		image_interval = 30
	elif set_image_interval=="1":
		image_interval = 90
	elif set_image_interval=="2":
		image_interval = 180
	elif set_image_interval=="3":
		image_interval = 270
	elif set_image_interval=="4":
		image_interval = 360
	elif set_image_interval=="5":
		image_interval = 0
	else:
		image_interval = 30
	return image_interval

# ------------
#  RSS Caching
# ------------

def check(fn):
    return ((time.time() - os.path.getmtime(fn))/60)

# Verifies a Directory if it exists (Cache) If not, it creates it

def refresh(fn,url,UAS):
    req = urllib2.Request(url)
    req.add_header('User-Agent', UAS)
    response = urllib2.urlopen(req)
    link=response.read()
    response.close()
    file = open(fn, 'w')
    file.write(link)
    file.close()
    return True

def getcontent(link,UAS):
	content = ""
	tfn = link.rsplit('/',1)
	tfnf = tfn[-1]
	filename = xbmc.translatePath(os.path.join( 'special://profile/addon_data/plugin.video.tas/', 'cache', 'feeds',  tfnf ))
	filecheck = os.path.isfile(filename)
	if filecheck==False:
		refresh(filename,link,UAS)
		content = open(filename, "r").read()
	elif filecheck==True:
		interval = get_rss_interval()
		if not interval==0:
			if check(filename)>interval:
				refresh(filename,link,UAS)
				content = open(filename, "r").read()
			else:
				content = open(filename, "r").read()
		else:
			content = open(filename, "r").read()

	else:
		content=False
	return content

# -------------
# Image Caching
# -------------

def img_check(fn):
    return (((time.time() - os.path.getmtime(fn))/60) / 24)

# Image Downloader
def img_download(fname,url,id,UAS):
	from urllib2 import Request, urlopen, URLError, HTTPError
	req = Request(url)
	try:
		f = urlopen(req)
		local_file = open(fname, "wb")
		local_file.write(f.read())
		local_file.close()

	except HTTPError, e:
		print "HTTP Error:",e.code , url
	except URLError, e:
		print "URL Error:",e.reason , url
	return

# Main Function to get the image
# If the file doesnt exist, it will check the modified date, if the modified date is off, it will update
def img_getcontent(link,id,UAS):
	content = ""
	tfn = link.rsplit('/',1)
	ext = tfn[-1]
	ext = ext.split(".", 1)
	ext = ext[-1]
	tfnf = ""+str(id)+"."+ext+""
	filename = xbmc.translatePath(os.path.join( 'special://profile/addon_data/plugin.video.tas/', 'cache', 'images', tfnf ))
	filecheck = os.path.isfile(filename)
	if filecheck==False:
		img_download(filename,link,id,UAS)
		content = filename
	elif filecheck==True:
		interval = get_image_interval()
		if not interval==0:
			if img_check(filename)>interval:
				img_download(filename,link,id,UAS)
				content = filename
			else:
				content = filename
		else:
			content = filename
	else:
		content=False
	return content