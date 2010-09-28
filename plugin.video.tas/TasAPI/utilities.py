import os,xbmc,xbmcgui,xbmcaddon, urllib, zipfile,time, datetime
from TasAPI import common as common

# Settings (This is required for Language Support)
__settings__ = xbmcaddon.Addon(id='plugin.video.tas')

# Clean RSS
# This function cleans the cached RSS Feeds
def clean_rss():
	count = 1
	dialog = xbmcgui.Dialog()
	dia_title = common.get_lstring(32000)
	dia_l1 = common.get_lstring(32020)
	dia_l2 = common.get_lstring(32021)
	ret = dialog.yesno(dia_title, dia_l1, dia_l2)
	if ret==1:
		dir = xbmc.translatePath(os.path.join( 'special://profile/addon_data/plugin.video.tas/', 'cache', 'feeds'))
		pDialog = xbmcgui.DialogProgress()
		dia_title = common.get_lstring(32000)
		dia_l1 = common.get_lstring(32022)
		nret = pDialog.create(dia_title, dia_l1)
		for subdir, dirs, files in os.walk(dir):
			total = int(len(files))
			for file in files:
				if not (pDialog.iscanceled()):
					percent = int(((float(count) / total) * 100))
					count = count + 1
					cfile = xbmc.translatePath(os.path.join( 'special://profile/addon_data/plugin.video.tas/', 'cache', 'feeds', file))
					dia_l1 = common.get_lstring(32025) + ": "
					pDialog.update(percent, dia_l1, file)
					os.remove(cfile)
				else:
					dialog = xbmcgui.Dialog()
					dia_title = common.get_lstring(32000)
					dia_l1 = common.get_lstring(32023)
					ok = dialog.ok(dia_title, dia_l1)
					return
	else:
		dialog = xbmcgui.Dialog()
		dia_title = common.get_lstring(32000)
		dia_l1 = common.get_lstring(32023)
		ok = dialog.ok(dia_title, dia_l1)			
		return

	dialog = xbmcgui.Dialog()
	dia_title = common.get_lstring(32000)
	dia_l1 = common.get_lstring(32024)
	ok = dialog.ok(dia_title, dia_l1)
	return
	
# Clean Icons/Thumbnails
# This function cleans the cached Icons/Thumbnail Images
def clean_ico():
	count = 1
	dialog = xbmcgui.Dialog()
	dia_title = common.get_lstring(32000)
	dia_l1 = common.get_lstring(32020)
	dia_l2 = common.get_lstring(32031)
	ret = dialog.yesno(dia_title, dia_l1, dia_l2)
	if ret==1:
		dir = xbmc.translatePath(os.path.join( 'special://profile/addon_data/plugin.video.tas/', 'cache', 'images'))
		pDialog = xbmcgui.DialogProgress()
		dia_title = common.get_lstring(32000)
		dia_l1 = common.get_lstring(32030)
	
		nret = pDialog.create(dia_title , dia_l1 )
		for subdir, dirs, files in os.walk(dir):
			total = int(len(files))
			for file in files:
				if not (pDialog.iscanceled()):
					percent = int(((float(count) / total) * 100))
					count = count + 1
					cfile = xbmc.translatePath(os.path.join( 'special://profile/addon_data/plugin.video.tas/', 'cache', 'images', file))
					dia_removing = common.get_lstring(32025) + ":" 
					pDialog.update(percent, dia_removing, file)
					os.remove(cfile)
				else:
					dialog = xbmcgui.Dialog()
					dia_title = common.get_lstring(32000)
					dia_l1 = common.get_lstring(32032)
					ok = dialog.ok(dia_title, dia_l1)
					return
	else:
		dialog = xbmcgui.Dialog()
		dia_title = common.get_lstring(32000)
		dia_l1 = common.get_lstring(32032)
		ok = dialog.ok(dia_title, dia_l1)
		return

	dialog = xbmcgui.Dialog()
	dia_title = common.get_lstring(32000)
	dia_l1 = common.get_lstring(32033)
	ok = dialog.ok(dia_title, dia_l1)
	return

# Clean RSS Internal
# This function cleans the cached RSS Feeds 
# It is almost a dupe of the function above, BUT!
# it is meant for sequentual usage with clean_ico_int for a proper dialog flow
def clean_rss_int():
	count = 1
	dialog = xbmcgui.Dialog()
	dia_title = common.get_lstring(32000)
	dia_l1 = common.get_lstring(32020)
	dia_l2 = common.get_lstring(32101)
	ret = dialog.yesno(dia_title, dia_l1, dia_l2)
	if ret==1:
		dir = xbmc.translatePath(os.path.join( 'special://profile/addon_data/plugin.video.tas/', 'cache', 'feeds'))
		pDialog = xbmcgui.DialogProgress()
		dia_title = common.get_lstring(32000)
		dia_l1 = common.get_lstring(32022)
		nret = pDialog.create(dia_title, dia_l1)
		for subdir, dirs, files in os.walk(dir):
			total = int(len(files))
			for file in files:
				if not (pDialog.iscanceled()):
					percent = int(((float(count) / total) * 100))
					count = count + 1
					cfile = xbmc.translatePath(os.path.join( 'special://profile/addon_data/plugin.video.tas/', 'cache', 'feeds', file))
					dia_removing = common.get_lstring(32025) + ":" 
					pDialog.update(percent, dia_removing, file)
					os.remove(cfile)
				else:
					dialog = xbmcgui.Dialog()
					dia_title = common.get_lstring(32000)
					dia_l1 = common.get_lstring(32102)
					ok = dialog.ok(dia_title, dia_l1)
					return "C"
	else:
		dialog = xbmcgui.Dialog()
		dia_title = common.get_lstring(32000)
		dia_l1 = common.get_lstring(32102)
	
		ok = dialog.ok(dia_title, dia_l1)
		return "C"

	return

# Clean Icon/Image cache Internal
# This function cleans the cached Icon/Thumbnail Cache 
# It is almost a dupe of the function above, BUT!
# it is meant for sequentual usage with clean_rss_int for a proper dialog flow
def clean_ico_int():
	count = 1
	dialog = xbmcgui.Dialog()
	ret = 1
	if ret==1:
		dir = xbmc.translatePath(os.path.join( 'special://profile/addon_data/plugin.video.tas/', 'cache', 'images'))
		pDialog = xbmcgui.DialogProgress()
		dia_title = common.get_lstring(32000)
		dia_l1 = common.get_lstring(32030)
		nret = pDialog.create(dia_title, dia_l1)
		for subdir, dirs, files in os.walk(dir):
			total = int(len(files))
			for file in files:
				if not (pDialog.iscanceled()):
					percent = int(((float(count) / total) * 100))
					count = count + 1
					cfile = xbmc.translatePath(os.path.join( 'special://profile/addon_data/plugin.video.tas/', 'cache', 'images', file))
					dia_l1 = common.get_lstring(32030) + ": " + file
					pDialog.update(percent, dia_l1)
					os.remove(cfile)
				else:
					dialog = xbmcgui.Dialog()
					dia_title = common.get_lstring(32000)
					dia_l1 = common.get_lstring(32032)
					ok = dialog.ok(dia_l1, dia_l1)
					return "C"
	else:
		dialog = xbmcgui.Dialog()
		dia_title = common.get_lstring(32000)
		dia_l1 = common.get_lstring(32032)
		ok = dialog.ok(dia_title, dia_l1)
		return "C"

	dialog = xbmcgui.Dialog()
	dia_title = common.get_lstring(32000)
	dia_l1 = common.get_lstring(32049)
	ok = dialog.ok(dia_title, dia_l1)
	return

def clean_all():
	rss = clean_rss_int()
	if not rss=="C":
		clean_ico_int()
	return

# Download Cache Hook
# The hook that will be called when downloading - Updates the Progress Dialog
def download_cache_hook(count, blockSize, totalSize):
	global pDialog
	global start_time
	global downloaded
	fn = "images.zip"
	if not (pDialog.iscanceled()):
		downloaded = downloaded + blockSize
		if downloaded > totalSize:
			downloaded = totalSize
		try:
			percent = int(min((count*blockSize*100)/totalSize, 100))
		except:
			 percent = 100
		if count != 0:
			time_elapsed = time.time() - start_time
			kbs = downloaded / time_elapsed
			dl_left = totalSize - downloaded
			time_remaining = int(dl_left) / int(kbs)
			time_total = time_remaining + time_elapsed
			kbs = common.convert_bytes(kbs)
			dia_l1 = common.get_lstring(32010) + ": " + fn
			dia_l2 = common.get_lstring(32011) + ": " + str(common.convert_bytes(downloaded)) + "/" + str(common.convert_bytes(totalSize)) + " @ " + str(kbs) + "/s"
			dia_l3 = common.get_lstring(32012) + ": " + str(datetime.timedelta(seconds=int(time_elapsed))) + "/" + str(datetime.timedelta(seconds=int(time_total))) + " (" + common.get_lstring(32013) + ": " + str(datetime.timedelta(seconds=int(time_remaining))) + ")"
			pDialog.update(percent, dia_l1, dia_l2, dia_l3)
	else:
		if not percent==100:
			raise "Cancelled"
			
# Download Cache
# This downloads the Cache (zip file) from google, extracting it later on
def download_cache():
	global pDialog
	global start_time
	global downloaded
	downloaded = 0
	error = 0
	start_time = time.time()
	pDialog = xbmcgui.DialogProgress()
	dia_title = common.get_lstring(32000)
	dia_l1 = common.get_lstring(32100)
	ret = pDialog.create(dia_title, dia_l1)
	filename = 'images.zip'
	archive = xbmc.translatePath(os.path.join( 'special://profile/addon_data/plugin.video.tas/', 'cache', filename))
	remoteaddr = 'http://xbmc-plugin-video-tas.googlecode.com/files/'
	try:
		urllib.urlretrieve(remoteaddr + filename,archive, reporthook=download_cache_hook)
	except:
		error = 1
		dialog = xbmcgui.Dialog()
		dia_title = common.get_lstring(32000)
		dia_l1 = common.get_lstring(32040)
		ok = dialog.ok(dia_title, dia_l1)
	
	if not error==1:
		unzip_downloaded_cache()
		dialog = xbmcgui.Dialog()
		dia_title = common.get_lstring(32000)
		dia_l1 = common.get_lstring(32042)
		dia_l2 = common.get_lstring(32043)
		ok = dialog.ok(dia_title, dia_l1, dia_l2)
	return

# Unzipping of the Cache
def unzip_downloaded_cache():
	filename = 'images.zip'
	archive = xbmc.translatePath(os.path.join( 'special://profile/addon_data/plugin.video.tas/', 'cache', filename))
	outdir = xbmc.translatePath(os.path.join( 'special://profile/addon_data/plugin.video.tas/', 'cache', 'images'))
	pDialog = xbmcgui.DialogProgress()
	dia_title = common.get_lstring(32000)
	dia_l1 = common.get_lstring(32044)
	ret = pDialog.create(dia_title, dia_l1)
	count = 0
	zfobj = zipfile.ZipFile(archive)
	ico_total = len(zfobj.namelist())
	for name in zfobj.namelist():
		count = count + 1
		percent = int(((float(count) / ico_total) * 100))
		outfile = open(os.path.join(outdir, name), 'wb')
		outfile.write(zfobj.read(name))
		outfile.close()
		dia_l1 = common.get_lstring(32045) + ":"
		dia_l2 = common.get_lstring(32046) + ": " + str(name)
		dia_l3 = common.get_lstring(32047) + ": " + str(count) + " " + common.get_lstring(32048) + " " + str(ico_total)
		pDialog.update(int(percent), dia_l1, dia_l2, dia_l3 )
	zfobj.close()
	os.remove(archive)
	return
