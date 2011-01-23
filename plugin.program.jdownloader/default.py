# script constants
__plugin__		= "JDownloader"
__addonID__		= "plugin.program.jdownloader"
__author__		= "Ppic & pgoeri"
__url__			= "http://pgoeri-xbmc-plugins.googlecode.com"
__svn_url__		= "http://pgoeri-xbmc-plugins.googlecode.com/svn/trunk/plugin.program.jdownloader/"
__credits__		= "Team XBMC passion, http://passion-xbmc.org & pgoeri"
__platform__		= "xbmc media center, [LINUX, OS X, WIN32]"
__date__			= "23-01-2011"
__version__		= "1.0.2"
__svn_revision__	= "$Revision:  $".replace( "Revision", "" ).strip( "$: " )
__XBMC_Revision__	= "ce6dff4f3480834cc1134072e45e5deb0c8557c4" # Trunk (15/01/11)
__useragent__		= "Mozilla/5.0 (Windows; U; Windows NT 5.1; fr; rv:1.9.0.1) Gecko/2008070208 Firefox/3.0.1"

from traceback import print_exc
import xbmcplugin
import xbmc
import xbmcgui
import xbmcaddon
import os
import urllib
import time

__addon__ = xbmcaddon.Addon(__addonID__)
__language__ = __addon__.getLocalizedString

BASE_RESOURCE_PATH = os.path.join( __addon__.getAddonInfo('path'), "resources" )
sys.path.append( os.path.join( BASE_RESOURCE_PATH, "lib" ) )
dialog = xbmcgui.Dialog()

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
		filename = dialog.browse( 1 , heading , "files", mask, False, False, def_file_path)
		# verify selection
		if not os.path.isfile(filename):
			filename = ""
	return filename

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

print "Mode: "+str(mode)
print "URL: "+str(url)

#check connection
try:
	jdownloader.get(jdownloader.GET_STATUS)
except jdownloader.JDError, error:
	(type, e, traceback) = sys.exc_info()
	showError(xbmc.getLocalizedString(257), e.message)
	mode=-1
	url="error"

#main menu:
if mode==None or mode==0:
	
	#status color
	status = jdownloader.get(jdownloader.GET_STATUS)
	if jdownloader.STATE_NOTRUNNING in status:
		status = status.replace( status , "[COLOR=FFFF0000]%s[/COLOR]" % ( status ))	# RED
	elif jdownloader.STATE_RUNNING in status:
		status = status.replace( status , "[COLOR=ff00FF00]%s[/COLOR]" % ( status ))	# GREEN
	elif jdownloader.STATE_STOPPING in status:
		status = status.replace( status , "[COLOR=ffFFFF00]%s[/COLOR]" % ( status ))	# YELLOW
	
	#downloadspeed color (change color to YELLOW if speed limit is set)
	downloadspeed = jdownloader.get(jdownloader.GET_SPEED)
	speedlimit = jdownloader.get(jdownloader.GET_SPEEDLIMIT)
	if not speedlimit == 0 and not speedlimit == "none":
		downloadspeed = downloadspeed.replace( downloadspeed , "[COLOR=ffFFFF00]%s[/COLOR]" % ( downloadspeed ))
	
	#add the three main list entrys
	addDir( __language__(30051) + ": %s - %s: %s KB/s - %s %s" % (status , __language__(30052) , downloadspeed, jdownloader.get(jdownloader.GET_CURRENTFILECNT), __language__(30053)) , "actions" , 2 , "" )
	addDir( __language__(30050), "currentlist" , 1 , "" )
	addDir( __language__(30056), "finishedlist" , 1 , "" )
	end_of_directory( True )
	
#list of packages
if mode==1: 
	filelist = jdownloader.get_downloadlist(url)
	for item in filelist:
		add = True
		summary = item["Name"] + item["Size"] + item["Percentage"] + "%"
		
		#modify color (YELLOW = active downloading, GREEN = finished) 
		if not item["Eta"] == "~ ": summary = summary.replace( summary , "[COLOR=ffFFFF00]%s[/COLOR]" % ( summary )) # YELLOW
		elif item["Percentage"] == "100,00": summary = summary.replace( summary , "[COLOR=ff00FF00]%s[/COLOR]" % ( summary )) # GREEN
		#only add finished packages in finishedlist
		if url == "finishedlist":
			if not item["Percentage"] == "100,00" : add = False
		if add: addLink( summary , "" , "" )
	end_of_directory( True )

#choose action
if mode== 2:
	actions = jdownloader.getAvailableActions()
	actionlabels = []
	for i in actions:
		actionlabels.append(__language__(jdownloader.ALL_ACTIONS[i]))
	select = dialog.select(__language__(30054) , actionlabels)
	
	if not select == -1: 
		if actions[select] in [jdownloader.ACTION_SPEEDLIMIT,jdownloader.ACTION_MAXDOWNLOADS]:
			limit = dialog.numeric( 0 , __language__(30055) )
			result = jdownloader.action(actions[select],limit)
		elif actions[select] == jdownloader.ACTION_JD_UPDATE:
			limit = dialog.yesno( "JDownloader" , __language__(30057) )
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
		
		showMessage("JDownloader" , result )
		time.sleep(3) # otherwise status is not correct after start/stop
		xbmc.executebuiltin("XBMC.Container.Update")

#interface for other addons
if mode==3:
	if (params["action"] == "addlink"):
		jdownloader.action_addlink(url)
	if (params["action"] == "addcontainer"):
		jdownloader.action_addcontainer(url)
