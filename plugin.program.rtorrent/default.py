
# main imports
import sys
import os
import urllib
import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin

# Colour scheme
# Dld & File Completed: Green
# Dld & File P: High  : Yellow
# Dld & File P: Normal: Blue 
# Dld P: Low   : Purple
# Dld Priority: Idle  : Orange
# Dld Stopped & File Don't Download: Red

#Set plugin paths
PATH_CWD = xbmc.translatePath(os.getcwd())
PATH_LIB = xbmc.translatePath(os.path.join(PATH_CWD, 'resources', 'lib'))
PATH_ICONS = xbmc.translatePath(os.path.join(PATH_CWD,'resources','icons'))

print PATH_CWD

#Set plugin fanart
xbmcplugin.setPluginFanart(int(sys.argv[1]), PATH_CWD+'fanart.jpg')

#adding plugin libary to python library path
sys.path.append (PATH_LIB)

# plugin dependant imports
#custom xmlrpc2scgi script that loads the Python 2.6 module of xmlrpclib
import xmlrpc2scgi

# plugin constants
__plugin__ = "RTorrent"
__addonID__= "plugin.program.rTorrent"
__author__ = "Daniel Jolly"
__url__ = "http://www.danieljolly.com"
__credits__ = "Team XBMC for amazing XBMC! Jari \"Rakshasa\" Sundell, the developer of the fantastic rTorrent"
__version__ = "0.6"
__date__ = "08/01/2010"
# TODO: Add checking to make sure XBMC is a compatiable version
# __svn_revision__ = "$Revision$"
# __XBMC_Revision__ = "19001"

__addon__ = xbmcaddon.Addon( __addonID__ )
__settings__ = __addon__
__language__ = xbmc.getLocalizedString

SCGI_PORT = _settings_.getSetting(int("scgi_port")
SCGI_SERVER = 'scgi://localhost:'+str(SCGI_PORT)

#establishing connection
# TODO: Add checking to make sure it establishes correctly
rtc = xmlrpc2scgi.RTorrentXMLRPCClient(SCGI_SERVER)

#logging with xbmc
# xbmc.log("Loaded rTorrent Control plugin", xbmc.LOGNOTICE )
# xbmc.log("Attempting to establish connection on " + SCGI_SERVER, xbmc.LOGNOTICE )

#Get parameters script from Voinage's tutorial
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

def getIcon(isdir,active,complete,p):
	if isdir>1:
		icon = "dir"
		p=p+3
	elif isdir==0:
		icon = "file"
	else:
		icon = "file"
		p=p+3
	if active==1:
		if complete==1:
			iconcol = "green"
		else:
			if p==0: #Don't Download
				iconcol = "red"
			elif p==1: #Normal
				iconcol = "blue"
			elif p==2: #High
				iconcol = "yellow"
			#Now for downloads, not files
			elif p==3: #Idle
				iconcol = "orange"
			elif p==4: #Low
				iconcol = "purple"
			elif p==5: #Normal
				iconcol = "blue"
			elif p==6: #High
				iconcol = "yellow"
	else:
		iconcol = "red"	
	return PATH_ICONS+'/'+icon+'_'+iconcol+'.png'
#Main program code		
def main():
	dlds = []
	dlds = rtc.d.multicall('main', "d.get_name=", "d.get_hash=", "d.get_completed_chunks=", "d.get_size_chunks=", "d.get_size_files=", "d.get_directory=", "d.is_active=", "d.get_complete=", "d.get_priority=", "d.is_multi_file=")
	dlds_len = len(dlds)

	for dld in dlds:
		dld_name = dld[0]
		dld_hash = dld[1]
		dld_completed_chunks = dld[2]
		dld_size_chunks = dld[3]
		dld_percent_complete = dld_completed_chunks*100/dld_size_chunks
		dld_size_files = dld[4]
		dld_directory = dld[5]
		dld_is_active = dld[6]
		dld_complete = dld[7]
		dld_priority = dld[8]
		dld_is_multi_file = dld[9]
		
		tbn=getIcon(dld_size_files,dld_is_active,dld_complete,dld_priority)		
		
		if dld_is_active==1:
			cm_action = 'Stop Download',"xbmc.runPlugin(%s?mode=action&method=d.stop&arg1=%s)" % ( sys.argv[0], dld_hash)
		else:
			cm_action = 'Start Download',"xbmc.runPlugin(%s?mode=action&method=d.start&arg1=%s)" % ( sys.argv[0], dld_hash)
		if dld_percent_complete<100:
			li_name = dld_name+' ('+str(dld_percent_complete)+'%)'
		else:
			li_name = dld_name	

		cm = [cm_action,('Erase Download',"xbmc.runPlugin(%s?mode=action&method=d.erase&arg1=%s)" % ( sys.argv[0], dld_hash)), \
			('Set Priority: High',"xbmc.runPlugin(%s?mode=action&method=d.set_priority&arg1=%s&arg2=3)" % ( sys.argv[0], dld_hash)), \
			('Set Priority: Normal',"xbmc.runPlugin(%s?mode=action&method=d.set_priority&arg1=%s&arg2=2)" % ( sys.argv[0], dld_hash)), \
			('Set Priority: Low',"xbmc.runPlugin(%s?mode=action&method=d.set_priority&arg1=%s&arg2=1)" % ( sys.argv[0], dld_hash)), \
			('Set Priority: Idle',"xbmc.runPlugin(%s?mode=action&method=d.set_priority&arg1=%s&arg2=0)" % ( sys.argv[0], dld_hash))]	
			
		li = xbmcgui.ListItem( \
			label=li_name, \
			iconImage=tbn, thumbnailImage=tbn)
		li.addContextMenuItems(items=cm,replaceItems=True)		
		if dld_size_files>1:
			if not xbmcplugin.addDirectoryItem(int(sys.argv[1]), \
				sys.argv[0]+"?mode=files&hash="+dld_hash+"&numfiles="+str(dld_size_files), \
				li,isFolder=True,totalItems=dlds_len): break
		else:
			if not xbmcplugin.addDirectoryItem(int(sys.argv[1]), \
				sys.argv[0]+"?mode=play&arg1="+str(dld_complete)+"&url="+urllib.quote_plus(xbmc.translatePath(os.path.join(dld_directory,dld_name))), \
				li,totalItems=dlds_len): break
	xbmcplugin.endOfDirectory(int(sys.argv[1]), cacheToDisc=False)

#Files inside a multi-file torrent code
def files(hash,numfiles):
	for i in range(0,numfiles):
		f_name = rtc.f.get_path(hash, i)
		f_frozen_path = rtc.f.get_frozen_path(hash, i)
		f_completed_chunks = rtc.f.get_completed_chunks(hash, i)
		f_size_chunks = rtc.f.get_size_chunks(hash, i)
		f_percent_complete = f_completed_chunks*100/f_size_chunks
		f_priority = rtc.f.get_priority(hash,i)
		if f_percent_complete==100:
			f_complete = 1
		else:
			f_complete = 0
		tbn=getIcon(0,1,f_complete,f_priority)
		if f_percent_complete<100:
			li_name = f_name+' ('+str(f_percent_complete)+'%)'
		else:
			li_name = f_name
		li = xbmcgui.ListItem( \
			label=li_name, \
			iconImage=tbn, thumbnailImage=tbn)
		cm = [('Set Priority: High',"xbmc.runPlugin(%s?mode=action&method=f.set_priority&arg1=%s&arg2=%s&arg3=2)" % ( sys.argv[0], hash,i)), \
			('Set Priority: Normal',"xbmc.runPlugin(%s?mode=action&method=f.set_priority&arg1=%s&arg2=%s&arg3=1)" % ( sys.argv[0], hash,i)), \
			('Set Priority: Don\'t Download',"xbmc.runPlugin(%s?mode=action&method=f.set_priority&arg1=%s&arg2=%s&arg3=0)" % ( sys.argv[0], hash,i))]
		li.addContextMenuItems(items=cm,replaceItems=True)
		if not xbmcplugin.addDirectoryItem(int(sys.argv[1]), \
			sys.argv[0]+"?mode=play&arg1="+str(f_complete)+"&url="+urllib.quote_plus(xbmc.translatePath(f_frozen_path)), \
			li,totalItems=numfiles): break
	xbmcplugin.endOfDirectory(int(sys.argv[1]), cacheToDisc=False)		

#XBMC file player code
def play(url,arg1):
	if int(arg1)==0:
		dialog = xbmcgui.Dialog()
		#Need to make this text part of the language file
		ret = dialog.yesno('Play File', 'This file has not downloaded completely.', 'Are you sure you want to play it?')
		if ret==True:
			xbmc.Player().play(url);
	else:
		xbmc.Player().play(url);

def action(method, arg1, arg2, arg3):
	allok = 0
	if method.find('erase')!=-1:
		dialog = xbmcgui.Dialog()
		#Need to make this text part of the language file
		ret = dialog.yesno('Delete Download', 'Are you sure you want to delete this download?')
		if ret==True:
			allok = 1
	else:
		allok = 1
	if allok==1:
		if arg3:
			#only used at this stage to change priority on files in torrent
			#TODO: Must clean this up and put integer checking in place
			function = 'rtc.'+method+'("'+arg1+'",'+arg2+','+arg3+')'
		elif arg2:
			function = 'rtc.'+method+'("'+arg1+'","'+arg2+'")'
		else:
			function = 'rtc.'+method+'("'+arg1+'")'
		#print function	
		exec function
		xbmc.executebuiltin('Container.Refresh')
	
params=get_params()
url=None
hash=None
mode=None
numfiles=None
method=None
arg1=None
arg2=None
arg3=None
try:
        url=urllib.unquote_plus(params["url"])
except:
        pass
try:
        hash=str(params["hash"])
except:
        pass
try:
        mode=str(params["mode"])
except:
        pass
try:
        numfiles=int(params["numfiles"])
except:
        pass
try:
        method=str(urllib.unquote_plus(params["method"]))
except:
        pass		
try:
        arg1=str(urllib.unquote_plus(params["arg1"]))
except:
        pass		
try:
        arg2=str(urllib.unquote_plus(params["arg2"]))
except:
        pass		
try:
        arg3=str(urllib.unquote_plus(params["arg3"]))
except:
        pass
		
#print "Params: "+str(params)
#print "Mode: "+str(mode)
#print "Method: "+str(method)
#print "Arg1: "+str(arg1)
#print "Arg2: "+str(arg2)
#print "URL: "+str(url)
		
if mode==None:
        main()
     
elif mode=='files':
        files(hash,numfiles)
        
elif mode=='play':
        play(url,arg1)
		
elif mode=='action':
		action(method,arg1,arg2,arg3)
		
