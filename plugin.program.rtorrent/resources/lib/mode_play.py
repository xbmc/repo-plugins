# Imports
import os
import xbmc
import xbmcgui
g = __import__('global')

#XBMC file player code
def main(hash,arg1):
	print "Hash is "+hash+" and arg1 is "+arg1
	arg1=int(arg1)
	# Check to see if the file has completely downloaded.
	if g.__islocal__==1:
		url = g.rtc.f.get_frozen_path(hash,arg1)
	else:
		f_name = g.rtc.f.get_path(hash, arg1)
		if g.rtc.d.get_complete(hash)==1:
			url = os.path.join(g.__setting__('remote_folder_complete'),f_name)
		else:
			url = os.path.join(g.__setting__('remote_folder_downloading'),f_name)

	f_completed_chunks = g.rtc.f.get_completed_chunks(hash, arg1)
	f_size_chunks = g.rtc.f.get_size_chunks(hash, arg1)
	f_percent_complete = f_completed_chunks*100/f_size_chunks
	
	if int(f_percent_complete)<100:
		dialog = xbmcgui.Dialog()
		ret = dialog.yesno(g.__lang__(30150), g.__lang__(30151), g.__lang__(30152))
		if ret==True:
			xbmc.Player().play(url);
	else:
		xbmc.Player().play(url);
	print "Tried to play file: "+url