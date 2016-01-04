# Imports
import os
import xbmc
import xbmcgui
import globals as g

#XBMC file player code
def main(hash,arg1):
	arg1=int(arg1)
	# Check to see if the file has completely downloaded.
	if g.__islocal__==1:
		url = g.rtc.f.get_frozen_path(hash,arg1)
	else:
		f_name = g.rtc.f.get_path(hash, arg1)
		dld_name = g.rtc.d.get_name(hash)
		dld_is_multi_file = int(g.rtc.d.is_multi_file(hash))
		dld_complete = int(g.rtc.d.get_complete(hash))
		# Create the path to file to be played 
		if dld_is_multi_file==0:
			path = f_name
		else:
			path = os.path.join(dld_name,f_name)
		# Files that would be in the complete folder
		if dld_complete==1:
			url = os.path.join(g.__setting__('remote_folder_complete'),path)
		else:
			url = os.path.join(g.__setting__('remote_folder_downloading'),path)

	f_completed_chunks = int(g.rtc.f.get_completed_chunks(hash, arg1))
	f_size_chunks = int(g.rtc.f.get_size_chunks(hash, arg1))
	f_percent_complete = f_completed_chunks*100/f_size_chunks
	
	if f_percent_complete<100:
		dialog = xbmcgui.Dialog()
		ret = dialog.yesno(g.__lang__(30150), g.__lang__(30151), g.__lang__(30152))
		if ret==True:
			xbmc.Player().play(url);
	else:
		xbmc.Player().play(url);