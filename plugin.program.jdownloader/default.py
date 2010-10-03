# script constants
__plugin__		= "JDownloader"
__addonID__		= "plugin.program.jdownloader"
__author__		= "Ppic & pgoeri"
__url__			= "http://pgoeri-xbmc-plugins.googlecode.com"
__svn_url__		= "http://pgoeri-xbmc-plugins.googlecode.com/svn/trunk/plugin.program.jdownloader/"
__credits__		= "Team XBMC passion, http://passion-xbmc.org & pgoeri"
__platform__		= "xbmc media center, [LINUX, OS X, WIN32, XBOX]"
__date__			= "02-10-2010"
__version__		= "1.0.0"
__svn_revision__	= "$Revision:  $".replace( "Revision", "" ).strip( "$: " )
__XBMC_Revision__	= "34354" #XBMC Dharma branch
__useragent__		= "Mozilla/5.0 (Windows; U; Windows NT 5.1; fr; rv:1.9.0.1) Gecko/2008070208 Firefox/3.0.1"

from traceback import print_exc
import xbmcplugin
import xbmc
import xbmcgui
import xbmcaddon
import os
import urllib
import time
BASE_RESOURCE_PATH = os.path.join( os.getcwd(), "resources" )
sys.path.append( os.path.join( BASE_RESOURCE_PATH, "lib" ) )
dialog = xbmcgui.Dialog()

import jdownloader

__addon__ = xbmcaddon.Addon(__addonID__)
__language__ = __addon__.getLocalizedString

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
	

params=get_params()
url=None
mode=None

try: url=urllib.unquote_plus(params["url"])
except: pass
try: mode=int(params["mode"])
except: pass

print "Mode: "+str(mode)
print "URL: "+str(url)

OK = True

#check connection
try:
	jdownloader.get(jdownloader.GET_STATUS)
except jdownloader.JDError, error:
	d = xbmcgui.Dialog()
	(type, e, traceback) = sys.exc_info()
	d.ok(__language__(257), e.message)
	mode=-1
	url="error"
	#xbmc.executebuiltin("Action(ParentDir)")

#main menu:
if mode==None or url==None or len(url)<1:
	
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
	addDir( __language__(30051) + ": %s - %s: %s KB/s - %s %s" % (status , __language__(30052) , downloadspeed, jdownloader.get(jdownloader.GET_CURRENTFILECNT), __language__(30053)) , "" , 2 , "" )
	addDir( __language__(30050), "currentlist" , 1 , "" )
	addDir( __language__(30056), "finishedlist" , 1 , "" )
	
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
		else:
			result = jdownloader.action(actions[select])
		dialog.ok("JDownloader" , result )
		time.sleep(1)
		xbmc.executebuiltin("XBMC.Container.Update")
	OK = False
	
end_of_directory( OK )
