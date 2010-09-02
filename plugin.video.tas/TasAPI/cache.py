#TAS Videos by Insayne
import os, time
import urllib,urllib2
import xbmc,xbmcaddon

__settings__ = xbmcaddon.Addon(id='plugin.video.tas')

# Global Settings
set_rss_interval = __settings__.getSetting( "feed_update" )
set_image_interval = __settings__.getSetting( "image_update" )

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
	
	
def check(fn):
    return ((time.time() - os.path.getmtime(fn))/60)

def vdir():
    dir = xbmc.translatePath(os.path.join( 'special://profile/addon_data/plugin.videos.tas/', 'cache', 'feeds'))
    if os.path.isdir(dir)==False:
            os.makedirs(dir)
    return True
    
def refresh(fn,url,UAS):
    #Grab the RSS content
    req = urllib2.Request(url)
    req.add_header('User-Agent', UAS)
    response = urllib2.urlopen(req)
    link=response.read()
    response.close()
    
    #write them to the file
    file = open(fn, 'w')
    file.write(link)
    file.close()
    return True


def getcontent(link,UAS):
	content = ""
	tfn = link.rsplit('/',1)
	tfnf = tfn[-1]
	filename = xbmc.translatePath(os.path.join( 'special://profile/addon_data/plugin.videos.tas/', 'cache', 'feeds',  tfnf ))
	filecheck = os.path.isfile(filename)
	#print "Cache: Filename: "+str(filename)+"\nCheck: "+str(filecheck)+"\nURL: "+str(link)+"\nTFNF: "+tfnf+"\n\n"
	if filecheck==False:
		#print "Cache: File not Found"
		vdir()
		#print "Cache: Directories Check Ran"
		refresh(filename,link,UAS)
		#print "Cache: Refreshed the Data"
		content = open(filename, "r").read()
		#print "Cache: Content Set"
	elif filecheck==True:
		interval = get_rss_interval()
		if not interval==0:
			if check(filename)>interval:
				refresh(filename,link,UAS)
				#print "Cache: Updating Feed"
				content = open(filename, "r").read()
			else:
				#print "Cache: Reading Feed from Cache"
				content = open(filename, "r").read()
		else:
			#print "Cache: NEVER UPDATING"
			content = open(filename, "r").read()
				
	else:
		#print "Cache: Error Occured"
		content=False
	return content

# Image Caching stuff

def img_check(fn):
    return (((time.time() - os.path.getmtime(fn))/60) / 24)
	
def img_vdir():
    dir = xbmc.translatePath(os.path.join( 'special://profile/addon_data/plugin.videos.tas/', 'cache', 'images'))
    if os.path.isdir(dir)==False:
            os.makedirs(dir)
    return True
	
def img_download(fname,url,id,UAS):
	from urllib2 import Request, urlopen, URLError, HTTPError
	#create the url and the request
	req = Request(url)
	# Open the url
	try:
		f = urlopen(req)
		#print "downloading " + url
		# Open our local file for writing
		local_file = open(fname, "wb")
		#Write to our local file
		local_file.write(f.read())
		local_file.close()
		#print "Finished"

	#handle errors
	except HTTPError, e:
		print "HTTP Error:",e.code , url
	except URLError, e:
		print "URL Error:",e.reason , url
	return
	
def img_getcontent(link,id,UAS):
	content = ""
	tfn = link.rsplit('/',1)
	#tfnf = ""+str(id)+"_"+tfn[-1]+""
	ext = tfn[-1]
	ext = ext.split(".", 1)
	ext = ext[-1]
	
	tfnf = ""+str(id)+"."+ext+""
	filename = xbmc.translatePath(os.path.join( 'special://profile/addon_data/plugin.videos.tas/', 'cache', 'images', tfnf ))
	filecheck = os.path.isfile(filename)
	#print "Cache: Filename: "+str(filename)+"\nCheck: "+str(filecheck)+"\nURL: "+str(link)+"\nTFNF: "+tfnf+"\n\n"
	if filecheck==False:
		#print "Cache: File not Found"
		img_vdir()
		#print "Cache: Directories Check Ran"
		img_download(filename,link,id,UAS)
		#print "Cache: Refreshed the Data"
		content = filename
		#print "Cache: Content Set"
	elif filecheck==True:
		interval = get_image_interval()
		#print "My Interval: " + str(interval)
		if not interval==0:
			if img_check(filename)>interval:
				img_download(filename,link,id,UAS)
				#print "Cache: Updating Feed"
				content = filename
			else:
				#print "Cache: Reading Feed from Cache"
				content = filename
		else:
			#print "Cache: Never Updating!"
			content = filename
	else:
		#print "Cache: Error Occured"
		content=False
	return content