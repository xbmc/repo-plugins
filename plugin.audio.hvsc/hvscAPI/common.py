#TAS Videos by Insayne
import os, sys, time
import urllib,urllib2,re,httplib
import xbmc,xbmcaddon, xbmcgui

__settings__ = xbmcaddon.Addon(id='plugin.audio.hvsc')

# Global Settings

def clean_name(name):
    name = name.replace("\t", "")
    newstrg=''
    for word in name.split():
        newstrg=newstrg+' '+word
    return newstrg

def verify_local():
	global __settings__
	set_stream_source = __settings__.getSetting( "smode" )
	if set_stream_source=="1":
		set_source = __settings__.getSetting( "sid_path" )
		source = xbmc.translatePath(set_source)
		filecheck = os.path.isfile(source)
		if filecheck==False:
			dialog = xbmcgui.Dialog()
			dia_title = get_lstring(50033)
			dia_l1 = get_lstring(50041)
			dia_l2 = get_lstring(50042)
			dia_l3 = get_lstring(50043)
			ret = dialog.yesno(dia_title, dia_l1, dia_l2, dia_l3)
			if ret==1:
				__settings__.openSettings(url=sys.argv[0])
				


def checkpaths():
	path = xbmc.translatePath(os.path.join('special://profile/addon_data/plugin.audio.hvsc/' , 'temp'))
	if os.path.isdir(path)==False:
		os.makedirs(path)
		
	path = xbmc.translatePath(os.path.join('special://profile/addon_data/plugin.audio.hvsc/' , 'db'))
	if os.path.isdir(path)==False:
		os.makedirs(path)
	return True

def check_database():
	filename = xbmc.translatePath(os.path.join( 'special://profile/addon_data/plugin.audio.hvsc/db/', 'database.db'  ))
	filecheck = os.path.isfile(filename)
	if filecheck==False:
		dialog = xbmcgui.Dialog()
		dia_title = get_lstring(50033)
		dia_l1 = get_lstring(50044)
		dia_l2 = get_lstring(50045)
		dia_l3 = get_lstring(50046)
		ret = dialog.yesno(dia_title, dia_l1, dia_l2, dia_l3)
		if ret==1:
			global __settings__ 
			path = xbmc.translatePath(__settings__.getAddonInfo('path'))
			script = xbmc.translatePath(os.path.join( path , 'hvscAPI', 'dbcreator.py'))
			xbmc.executebuiltin("XBMC.RunScript(" + script + ")")
			return True
		else:
			dialog = xbmcgui.Dialog()
			dia_title = get_lstring(50033)
			dia_l1 = get_lstring(50047)
			dia_l2 = get_lstring(50048)
			ret = dialog.ok(dia_title, dia_l1, dia_l2)
			return False
	else:
		return True

def get_lstring(id):
	global __settings__
	string = __settings__.getLocalizedString(id).encode("UTF-8")
	return string

def get_song_length(duration,songnumber):
	duration = str(duration)
	songnumber = int(songnumber)
	if songnumber<=1:
		time = duration.split(" ")[0]
		minutes_ev = time.split(":")[0]
		seconds_ev = time.split(":")[1]
		minutes = ''.join([letter for letter in minutes_ev if letter.isdigit()])
		seconds = ''.join([letter for letter in seconds_ev if letter.isdigit()])
		songtime = (int(minutes) * 60) + int(seconds)
		return songtime
	
	else:
		songfetch = int(songnumber) - 1
		if len(duration.split(" "))>=songfetch:
			time = duration.split(" ")[songfetch]
			minutes_ev = time.split(":")[0]
			seconds_ev = time.split(":")[1]
			minutes = ''.join([letter for letter in minutes_ev if letter.isdigit()])
			seconds = ''.join([letter for letter in seconds_ev if letter.isdigit()])
			songtime = (int(minutes) * 60) + int(seconds)
			return songtime
			
		else:
			global __settings__
			int(getsl(__settings__.getSetting( "sl_custom" )))
			return int(getsl(__settings__.getSetting( "sl_custom" )))

	
	
	
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