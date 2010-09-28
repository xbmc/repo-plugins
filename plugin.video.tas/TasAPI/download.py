import os, sys, urllib, time
import xbmc,xbmcgui, xbmcaddon
import common as common
import datetime

# Settings (This is required for Language Support)
__settings__ = xbmcaddon.Addon(id='plugin.video.tas')

# Hook to update the Dialog
def download_cache_hook(count, blockSize, totalSize):
	global pDialog
	global fn
	global start_time
	global downloaded
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

#Download Function			
def download(url,dir):
	global pDialog
	global start_time
	global downloaded
	error = 0
	downloaded = 0
	start_time = time.time()
	pDialog = xbmcgui.DialogProgress()
	dia_title = common.get_lstring(32000)
	dia_l1 = common.get_lstring(32014)
	ret = pDialog.create(dia_title, dia_l1)
	global fn
	fn = url.rsplit("/")[-1]
	filename = xbmc.translatePath(os.path.join(dir, url.rsplit("/")[-1]))
	remoteaddr = url
	try:
		urllib.urlretrieve(remoteaddr,filename, reporthook=download_cache_hook)
		
	except:
		error = 1
		dialog = xbmcgui.Dialog()
		dia_title = common.get_lstring(32000)
		dia_l1 = common.get_lstring(32015)
		ok = dialog.ok(dia_title, dia_l1)
	
	if not error==1:
		dialog = xbmcgui.Dialog()
		dia_title = common.get_lstring(32000)
		dia_l1 = common.get_lstring(32016)
		ok = dialog.ok(dia_title, dia_l1)
	

# Logic Handler :)
if not sys.argv[1]=="":

	if sys.argv[1]=="nofolder":
		dialog = xbmcgui.Dialog()
		dia_title = common.get_lstring(32000)
		dia_l1 = common.get_lstring(30907)
		dia_l2 = common.get_lstring(30908)
		ret = dialog.yesno(dia_title, dia_l1, dia_l2)
		if ret==1:
			__settings__.openSettings(url=sys.argv[0])
		
	else:
		if not sys.argv[2]=="":
			download(sys.argv[1], sys.argv[2])
	