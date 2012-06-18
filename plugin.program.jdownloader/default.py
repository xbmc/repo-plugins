# script constants
__plugin__			= "JDownloader"
__addonID__			= "plugin.program.jdownloader"
__author__			= "Ppic & pgoeri"
__url__				= "http://pgoeri-xbmc-plugins.googlecode.com"
__svn_url__			= "http://pgoeri-xbmc-plugins.googlecode.com/svn/trunk/plugin.program.jdownloader/"
__credits__			= "Team XBMC passion, http://passion-xbmc.org & pgoeri"
__platform__		= "xbmc media center, [LINUX, OS X, WIN32]"
__date__			= "11-06-2012"
__version__			= "1.3.0"
__XBMC_Revision__	= "11.0" # Eden
__useragent__		= "Mozilla/5.0 (Windows; U; Windows NT 5.1; fr; rv:1.9.0.1) Gecko/2008070208 Firefox/3.0.1"

from traceback import print_exc
import xbmc,xbmcplugin,xbmcgui,xbmcaddon
import os,urllib,time

__addon__		= xbmcaddon.Addon(__addonID__)
__dialog__		= xbmcgui.Dialog()
__language__	= __addon__.getLocalizedString
__dbg__			= __addon__.getSetting( "debug" ) == "true"
__logprefix__	= "p.p.jd-"+__version__+": "

# add lib directoy to sys path (in order to import the jdownloader python file)
BASE_RESOURCE_PATH = os.path.join( __addon__.getAddonInfo('path'), "resources" )
sys.path.append( os.path.join( BASE_RESOURCE_PATH, "lib" ) )

import jdownloader


# shows a more userfriendly notification
def showMessage(heading, message):
	xbmc.executebuiltin('XBMC.Notification("%s", "%s")' % ( heading, message, ) )
	
def showError(heading, message):
	xbmc.executebuiltin('XBMC.Notification("%s", "%s", 1500, "DefaultIconError.png")' % ( heading, message, ) )

def addDir(name,url,mode,iconimage, c_items = None ):
	u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)
	ok=True
	liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
	if c_items : liz.addContextMenuItems( c_items, replaceItems=True )
	liz.setInfo( type="Video", infoLabels={ "Title": name } )
	ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)

def addLink(name,url,iconimage, c_items = None ):
	ok=True
	liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
	if c_items : liz.addContextMenuItems( c_items, replaceItems=True )
	liz.setInfo( type="Video", infoLabels={ "Title": name } )
	ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=liz)
	return ok

def end_of_directory( OK ): 
	xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=OK )
	
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
	
def get_filename( mode = 0):
	if mode == 0:
		# mode 0 --> TXT File
		def_file_setting_id = "def_txt_file"
		heading = __language__(30069)
		mask = ".txt"
	else:
		# mode 1 --> DLC File
		def_file_setting_id = "def_dlc_file"
		heading = __language__(30070)
		mask = ".dlc"
	
	# get settings
	def_file_path = __addon__.getSetting("def_file_path")
	def_file = __addon__.getSetting(def_file_setting_id)
	
	# try default file
	if not def_file == "" and os.path.exists(def_file):
		filename = def_file
	else:
		# show browse dialog
		filename = __dialog__.browse( 1 , heading , "files", mask, False, False, def_file_path)
		# verify selection
		if not os.path.isfile(filename):
			filename = ""
	return filename

def item_is_finished(percent):
	if (percent == "100,00" or percent == "100.00"):
		return True
	else:
		return False
	
def force_view():
	# change to list view if set in settings
	if (__addon__.getSetting( "list_view" ) == "true"):
		xbmc.executebuiltin("Container.SetViewMode(51)")

def auto_refresh(status, force=False):
	refresh = False
	
	if (force):
		refresh = True
		seconds = 3
	elif (__addon__.getSetting( "auto_refresh" ) == "true" and status != jdownloader.STATE_NOTRUNNING):
		refresh = True
		seconds = int(__addon__.getSetting( "refresh_interval" ))
		seconds = min(seconds,60)
		seconds = max(seconds,1)
	
	if (refresh):
		xbmc.executebuiltin('XBMC.AlarmClock(JDAutoRefresh, XBMC.RunPlugin(plugin://%s?mode=5&url=refresh), 00:00:%02d, true)' % (__addonID__, seconds ) )


params=get_params()
url=None
mode=None

try: url=urllib.unquote_plus(params["url"])
except: pass

try: mode=int(params["mode"])
except: pass

try: 
	if "action" in params: mode=3
except: pass

if __dbg__:
	print __logprefix__ + "MODE: " + str(mode) + " URL: " + str(url)

#check connection (and get state only once)
try:
	status = jdownloader.get(jdownloader.GET_STATUS)
except jdownloader.JDError, error:
	(type, e, traceback) = sys.exc_info()
	showError(xbmc.getLocalizedString(257), e.message)
	mode=-1
	url="error"

#main menu:
if mode==None or mode==0:
	#status color
	if jdownloader.STATE_NOTRUNNING in status:
		status_display = status.replace( status , "[COLOR=FFFF0000]%s[/COLOR]" % ( status ))	# RED
	elif jdownloader.STATE_RUNNING in status:
		status_display = status.replace( status , "[COLOR=ff00FF00]%s[/COLOR]" % ( status ))	# GREEN
	elif jdownloader.STATE_STOPPING in status:
		status_display = status.replace( status , "[COLOR=ffFFFF00]%s[/COLOR]" % ( status ))	# YELLOW
	else:
		status_display = status
	
	#downloadspeed color (change color to YELLOW if speed limit is set)
	downloadspeed = jdownloader.get(jdownloader.GET_SPEED)
	speedlimit = jdownloader.get(jdownloader.GET_SPEEDLIMIT)
	if not speedlimit == 0 and not speedlimit == "none":
		downloadspeed = downloadspeed.replace( downloadspeed , "[COLOR=ffFFFF00]%s[/COLOR]" % ( downloadspeed ))
	
	#add the three main list entrys
	addDir( __language__(30051) + ": %s - %s: %s KB/s - %s %s" % (status_display , __language__(30052) , downloadspeed, jdownloader.get(jdownloader.GET_CURRENTFILECNT), __language__(30053)) , "actions" , 2 , "" )
	addDir( __language__(30050), "alllist" , 1 , "" )
	addDir( __language__(30056), "finishedlist" , 1 , "" )
	
	force_view()
	
	end_of_directory( True )
	
	auto_refresh(status)
	
#list of packages
if mode==1:
	addDir( __language__(30058), "", None, "") # add dummy entry in first line, for prettier behavior on auto refresh
	pkglist = jdownloader.get_pkglist(url)
	for pkg in pkglist:
		summary = pkg["percent"] + "%"
		if (pkg["eta"] != "~"):
			summary += " - " + pkg["eta"]
		summary += " | " + pkg["display"] + " | " + pkg["size"]
		
		#modify color (YELLOW = active downloading, GREEN = finished) 
		if not pkg["eta"] == "~": summary = summary.replace( summary , "[COLOR=ffFFFF00]%s[/COLOR]" % ( summary )) # YELLOW
		elif item_is_finished(pkg["percent"]): summary = summary.replace( summary , "[COLOR=ff00FF00]%s[/COLOR]" % ( summary )) # GREEN
		
		#only add finished packages in finishedlist
		if (url == "finishedlist" and not item_is_finished(pkg["percent"])): continue
			
		addDir( summary , pkg["name"] , 4, "" )
	
	force_view()
		
	end_of_directory( True )
	
	auto_refresh(status)

#choose action
if mode== 2:
	xbmc.executebuiltin('XBMC.CancelAlarm(JDAutoRefresh, true)')
	
	actions = jdownloader.getAvailableActions(status)
	actionlabels = []
	for i in actions:
		actionlabels.append(__language__(jdownloader.ALL_ACTIONS[i]))
	select = __dialog__.select(__language__(30054) , actionlabels)
	
	if not select == -1: 
		if actions[select] in [jdownloader.ACTION_SPEEDLIMIT,jdownloader.ACTION_MAXDOWNLOADS]:
			limit = __dialog__.numeric( 0 , __language__(30055) )
			result = jdownloader.action(actions[select],limit)
		elif actions[select] == jdownloader.ACTION_JD_UPDATE:
			limit = __dialog__.yesno( "JDownloader" , __language__(30057) )
			result = jdownloader.action(actions[select],limit) 
		elif actions[select] == jdownloader.ACTION_ADD_LINKS:
			filename = get_filename(0);
			if not filename == "":
				result = jdownloader.action_addlinks_from_file(filename)
			else:
				result = "No file selected"
		elif actions[select] == jdownloader.ACTION_ADD_DLC:
			filename = get_filename(1);
			if not filename == "":
				result = jdownloader.action_addcontainer(filename)
			else:
				result = "No file selected"
		else:
			result = jdownloader.action(actions[select])
		
		# correct result when changing reconnect setting
		if actions[select] == jdownloader.ACTION_ENA_RECONNECT:
			result = result.replace("reconnect=false","reconnect=true")
		elif actions[select] == jdownloader.ACTION_DIS_RECONNECT:
			result = result.replace("reconnect=true","reconnect=false")
		
		showMessage("JDownloader" , result )
		
		auto_refresh(status,True)

#interface for other addons
if mode==3:
	if (params["action"] == "addlink"):
		jdownloader.action_addlink(url)
	if (params["action"] == "addlinklist"):
		jdownloader.action_addlinklist(url)
	if (params["action"] == "addcontainer"):
		jdownloader.action_addcontainer(url)
	if (params["action"] == "reconnect"):
		jdownloader.action(jdownloader.ACTION_RECONNECT)

#list of files per package
if mode==4: 
	addLink( __language__(30059),"","") # add dummy entry in first line, for prettier behavior on auto refresh
	filelist = jdownloader.get_filelist(url)
	for file in filelist:
		summary = file["name"] + " | " + file["status"]
		
		#modify color (YELLOW = active downloading, GREEN = finished) 
		if not file["speed"] == "0": summary = summary.replace( summary , "[COLOR=ffFFFF00]%s[/COLOR]" % ( summary )) # YELLOW
		elif item_is_finished(file["percent"]): summary = summary.replace( summary , "[COLOR=ff00FF00]%s[/COLOR]" % ( summary )) # GREEN
		
		addLink( summary , "" , "" )
	
	force_view()
		
	end_of_directory( True )
	
	auto_refresh(status)

#refresh
if mode==5:
	xbmc.executebuiltin("XBMC.Container.Refresh") 