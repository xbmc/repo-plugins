#################################################################
## MAV UDP Broadcast Receiver
## Author: VortexRotor
##
from pysqlite2 import dbapi2 as sqlite3
from time import time, ctime, sleep
import os, sys, socket, urllib, select, subprocess
import xbmc, xbmcgui, xbmcplugin, xbmcaddon
import re, traceback

__settings__   = xbmcaddon.Addon("plugin.program.multiroomaudio")
mavdb          = xbmc.translatePath( os.path.join( "special://profile/addon_data", "plugin.program.multiroomaudio", "database", "mav.db" ) )
AVSOURCES      = xbmc.translatePath( os.path.join( "special://profile/addon_data", "plugin.program.multiroomaudio", "avsources.xml" ) )
STRTSTRMR_FILE = xbmc.translatePath( os.path.join( "special://profile/addon_data", "plugin.program.multiroomaudio", "strtstrmr_win.ps1" ) )
LOOPBACK_FILE  = xbmc.translatePath( os.path.join( "special://profile/addon_data", "plugin.program.multiroomaudio", "loopback_win.ps1" ) )
ADDONDATA_PATH = xbmc.translatePath( os.path.join( "special://profile/addon_data", "plugin.program.multiroomaudio", "" ) )
DEFAULT_IMG    = xbmc.translatePath( os.path.join( "special://home/", "addons", "plugin.program.multiroomaudio", "icon.png" ) )
SRCPLS_PATH    = xbmc.translatePath( os.path.join( __settings__.getSetting( "pls_path" ), "Multiroom-AV", "" ) )
VIDEO_PATH     = xbmc.translatePath( os.path.join( SRCPLS_PATH, "VIDEO", "" ) )
AUDIO_PATH     = xbmc.translatePath( os.path.join( SRCPLS_PATH, "AUDIO", "" ) )
MSTR           = __settings__.getSetting(id="mstr_sync" )
MSTRNM         = __settings__.getSetting(id="mstr_name" )
localhost      = xbmc.getIPAddress()
#############################################################################################################
def log(msg):
	loglevel = 1
	try:
		if (loglevel == 1):
		    xbmc.output("[%s]: %s\n" % ("MAV",msg))
	except:
		pass

#############################################################################################################
##  Start streamer if Streamer on Startup is True
def _strtstrmr():
    if (__settings__.getSetting(id="dedicated" ) == "true"):
        if (__settings__.getSetting(id="strtstrm_strtup" ) == "true"):
            if (sys.platform == 'win32'):
 	        subprocess.call("powershell -WindowStyle \"hidden\" \"& '"+STRTSTRMR_FILE+"\'\"")

	        if (__settings__.getSetting( "playlocal" ) == "true"):
 	            subprocess.call("powershell -WindowStyle \"hidden\" \"& '"+LOOPBACK_FILE+"\'\"")
	            xbmc.executebuiltin("Notification(Multiroom Audio,Streamer Started,5000,"+DEFAULT_IMG+")")
	            __settings__.setSetting(id="mstrrunningflag", value="true")

	    else:
	        if (sys.platform.startswith('linux')):
		    os.system(""+ADDONDATA_PATH+"./strtstrmr_lin")
		    xbmc.executebuiltin("Notification(Multiroom Audio,Streamer Started,5000,"+DEFAULT_IMG+")")
		    ## if (Addon.getSetting( "playlocal" ) == "true"):
 		    ##    subprocess.call(""+ADDONDATA_PATH+"./loopback_lin")
		__settings__.setSetting(id="mstrrunningflag", value="true")
	    log("MAV Streamer Started and Running...")
	    ##xbmc.executebuiltin("Notification(Multiroom Audio,Master Streamer Started,3000,"+DEFAULT_IMG+")")

#############################################################################################################
# Stop Stream
def _stop():
    __settings__.setSetting(id="clientrunningflag", value="false")
    __settings__.setSetting(id="activesrcnm", value="")
    __settings__.setSetting(id="activesrcip", value="")
    xbmc.executehttpapi("Stop()")
    xbmc.executebuiltin("playlist.clear()")
    xbmc.executebuiltin("Notification(Multiroom Audio,All Streaming Stopped,7000,"+DEFAULT_IMG+")")
    if (sys.platform == 'win32'):
        subprocess.Popen(r'C:\WINDOWS\system32\cmd.exe /c "taskkill /F /IM vlc.exe"',shell=True) 
        ##os.system("taskkill /F /IM vlc.exe")
    else:
    	if (sys.platform.startswith('linux')):
 	    os.system("killall vlc | killall screen")
    	else: 
            os.system("killall vlc | killall screen")

#############################################################################################################
# Create MAV db
def _createmavdb():
    if (not os.path.isdir(os.path.dirname(mavdb))):
        os.makedirs(os.path.dirname(mavdb));
        conn = sqlite3.connect(mavdb)
        c = conn.cursor()
        c.execute('''CREATE TABLE sources(src_name varchar NOT NULL PRIMARY KEY UNIQUE,src_hostip varchar,src_url varchar,src_type varchar,src_pid integer,src_actflag integer)''')
        conn.commit()
        c.close()
        log("MAV-DB - MAV Database created successfully...")
    else:
	log("MAV-DB - MAV Database already exists...")
    return

#############################################################################################################
# add/update source to MAV db
def _addsrc(name, srcip, strmmrl, srctype):
    conn = sqlite3.connect(mavdb)
    c = conn.cursor()
    sql = 'UPDATE sources SET src_hostip=?,src_url=?,src_type=? WHERE src_name=?;' 
    if (name == "Loopback"):
        try:
            c.execute("INSERT INTO sources(src_name, src_hostip, src_url, src_type) VALUES (?, ?, ?, ?)", (name, srcip, strmmrl, srctype))
            log("MAV-DB - New Source "+name+" added to DB")
            ##xbmc.executebuiltin("Notification(Multiroom Audio,New Source "+name+" added to DB,10000,"+DEFAULT_IMG+")")
        except:
            print "MAV-DB error...Source Already exists in the table"
            c.execute(sql, (srcip,strmmrl,srctype,name))
            log("MAV-DB - Source "+name+" updated to DB")
            ##xbmc.executebuiltin("Notification(Multiroom Audio,Source "+name+" Updated,10000,"+DEFAULT_IMG+")")
    else:
        try:
            c.execute("INSERT INTO sources(src_name, src_hostip, src_url, src_type) VALUES (?, ?, ?, ?)", ("AV-Source-"+name+"", srcip, strmmrl, srctype))
            log("MAV-DB - New Source "+name+" added to DB")
            ##xbmc.executebuiltin("Notification(Multiroom Audio,New Source "+name+" added to DB,10000,"+DEFAULT_IMG+")")
        except:
            print "MAV-DB error...Source Already exists in the table"
            c.execute(sql, (srcip,strmmrl,srctype,"AV-Source-"+name+""))
            log("MAV-DB - Source "+name+" updated to DB")
            ##xbmc.executebuiltin("Notification(Multiroom Audio,Source "+name+" Updated,10000,"+DEFAULT_IMG+")")

    conn.commit()
    c.close()
    return

#############################################################################################################
# Parse the Message received and get the action needed
def _action(msg):
    if msg.startswith('MAV Master'):
	parts   = msg.split(' ')
	name    = (parts[4])
	srcip   = (parts[3])
	srctype = (parts[1])
	strmmrl = (parts[5])
	if (srctype == "Master"):
	    if (srcip != localhost):
              __settings__.setSetting(id="mstr_name", value=""+name+"")
              __settings__.setSetting(id="mstr_sync", value=""+srcip+"")
              __settings__.setSetting(id="mstr_mrl", value=""+strmmrl+"")
              log("MAV - Global Master "+name+" found @ "+srcip+"")
              _addsrc(name, srcip, strmmrl, srctype)
	      #xbmc.executebuiltin("Notification(Multiroom Audio,Source Found: "+name+",5000,"+DEFAULT_IMG+")")
            else:
                if (srcip == localhost):
                    name = "Loopback"
                    _addsrc(name, srcip, strmmrl, srctype)

    if msg.startswith('MAV Client'):
	parts   = msg.split(' ')
	name    = (parts[4])
	srcip   = (parts[3])
	srctype = (parts[1])
	strmmrl = (parts[5])
	if (srctype == "Client"):
	    if (srcip != localhost):
              log("MAV - Client "+name+" found @ "+srcip+"")
              _addsrc(name, srcip, strmmrl, srctype)
	      #xbmc.executebuiltin("Notification(Multiroom Audio,Client Found: "+name+",5000,"+DEFAULT_IMG+")")
            else:
                if (srcip == localhost):
                    name = "Loopback"
                    _addsrc(name, srcip, strmmrl, srctype)
                    
    else:
	# XBMC Restart eg: <b>StartUp;192.168.100.152;1</b>
        if msg.startswith('<b>StartUp'):
	    l = msg.lstrip('<b>StartUp;')
	    r = l.rstrip('</b>')
	    parts = msg.split(';')
	    srcip = (parts[1])
	    if (srcip == MSTR):
	        xbmc.executebuiltin("Notification(Multiroom Audio,"+MSTRNM+" Restarted,5000,"+DEFAULT_IMG+")")
	    #else:
	        #xbmc.executebuiltin("Notification(Multiroom Audio,Event Action: Startup ME,15000,"+DEFAULT_IMG+")")
	# Vol Up eg: <b>OnAction:88;x.x.x.x;2</b>
        if msg.startswith('<b>OnAction:88'):
	    l = msg.lstrip('<b>OnAction:88;')
	    r = l.rstrip('</b>')
	    parts = msg.split(';')
	    srcip = (parts[1])
	    if (srcip == MSTR):
	        xbmc.executebuiltin("Notification(Volume Up,"+MSTRNM+",2000,"+DEFAULT_IMG+")")
	    #else:
	        #xbmc.executebuiltin("Notification(Multiroom Audio,Event Action: Volume Up ME,15000,"+DEFAULT_IMG+")")
	# Vol Dn eg: <b>OnAction:89;x.x.x.x;2</b>
        if msg.startswith('<b>OnAction:89'):
	    l = msg.lstrip('<b>OnAction:89;')
	    r = l.rstrip('</b>')
	    parts = msg.split(';')
	    srcip = (parts[1])
	    if (srcip == MSTR):
	        xbmc.executebuiltin("Notification(Volume Dn,"+MSTRNM+",2000,"+DEFAULT_IMG+")")
	    #else:
	        #xbmc.executebuiltin("Notification(Multiroom Audio,Event Action: Volume Dn ME,15000,"+DEFAULT_IMG+")")
	# Mute eg: <b>OnAction:91;x.x.x.x;2</b>
        if msg.startswith('<b>OnAction:91'):
	    l = msg.lstrip('<b>OnAction:91;')
	    r = l.rstrip('</b>')
	    parts = msg.split(';')
	    srcip = (parts[1])
	    if (srcip == MSTR):
	        xbmc.executebuiltin("Notification(Mute,"+MSTRNM+",2000,"+DEFAULT_IMG+")")
	    #else:
	        #xbmc.executebuiltin("Notification(Multiroom Audio,Event Action: Mute ME,15000,"+DEFAULT_IMG+")")
	# Stop eg: <b>OnAction:13;x.x.x.x;2</b>
        if msg.startswith('<b>OnAction:13'):
	    l = msg.lstrip('<b>OnAction:13;')
	    r = l.rstrip('</b>')
	    parts = msg.split(';')
	    srcip = (parts[1])
	    if (srcip == MSTR):
		_stop()
		_strtstrmr()
	        xbmc.executebuiltin("Notification(Multiroom Audio,"+MSTRNM+" Stopped Playing,3000,"+DEFAULT_IMG+")")
		log("Master "+MSTRNM+" Playback Stopped...")
	    if (srcip == localhost):
		_stop()
		_strtstrmr()
	        xbmc.executebuiltin("Notification(Multiroom Audio,Local Playback Stopped,3000,"+DEFAULT_IMG+")")
		log("Local Playback Stopped...")

	    #else:
	        #xbmc.executebuiltin("Notification(Multiroom Audio,Event Action: Stop ME,15000,"+DEFAULT_IMG+")")
	# OK eg: <b>OnAction:7;x.x.x.x;2</b>
        if msg.startswith('<b>OnAction:7'):
	    l = msg.lstrip('<b>OnAction:7;')
	    r = l.rstrip('</b>')
	    parts = msg.split(';')
	    srcip = (parts[1])
	    #if (srcip == MSTR):
	        #xbmc.executebuiltin("Notification(Multiroom Audio,Event Action: OK "+srcip+",5000,"+DEFAULT_IMG+")")
	# Play eg: <b>OnPlayBackStarted;x.x.x.x;1</b>
        if msg.startswith('<b>OnPlayBackStarted'):
	    l = msg.lstrip('<b>OnPlayBackStarted;')
	    r = l.rstrip('</b>')
	    parts = msg.split(';')
	    srcip = (parts[1])
	    if (srcip == MSTR):
		if (xbmc.executehttpapi("GetCurrentlyPlaying()") == "<li>Filename:[Nothing Playing]"):
		    if (__settings__.getSetting( "src_auto" ) == "true"):
		        if (__settings__.getSetting( "clientrunningflag" ) == "false"):
		            xbmc.executehttpapi("PlayFile("+VIDEO_PATH+"AV-Source-"+MSTRNM+".pls)")
		            xbmc.executebuiltin("PlayerControl(RepeatOff)")
		            __settings__.setSetting(id="clientrunningflag", value="true")
		            __settings__.setSetting(id="activesrcnm", value=""+MSTRNM+"")
		            __settings__.setSetting(id="activesrcip", value=""+MSTR+"")
		            ## xbmc.executebuiltin("Notification(Multiroom Audio,"+MSTRNM+" Playback Started,1000,"+DEFAULT_IMG+")")
	                    log("Master "+MSTRNM+" Playback Started...")

	        ##xbmc.executebuiltin("Notification("+MSTRNM+",Play Started,2000,"+DEFAULT_IMG+")")
	    #else:
	        #xbmc.executebuiltin("Notification(Multiroom Audio,Event Action: Play ME,15000,"+DEFAULT_IMG+")")
	# Pause eg: <b>OnPlayBackPaused;192.168.100.152;1</b>
        if msg.startswith('<b>OnPlayBackPaused'):
	    l = msg.lstrip('<b>OnPlayBackPaused;')
	    r = l.rstrip('</b>')
	    parts = msg.split(';')
	    srcip = (parts[1])
	    if (srcip == MSTR):
	        xbmc.executebuiltin("Notification("+MSTRNM+",Paused,2000,"+DEFAULT_IMG+")")
	    #else:
	        #xbmc.executebuiltin("Notification(Multiroom Audio,Event Action: Pause ME,15000,"+DEFAULT_IMG+")")
	# Queue Next Item eg: <b>OnQueueNextItem;x.x.x.x;1</b>
        if msg.startswith('<b>OnQueueNextItem'):
	    l = msg.lstrip('<b>OnQueueNextItem;')
	    r = l.rstrip('</b>')
	    parts = msg.split(';')
	    srcip = (parts[1])
	    if (srcip == MSTR):
	        xbmc.executebuiltin("Notification(Coming Up on..,"+MSTRNM+",2000,"+DEFAULT_IMG+")")
	    #else:
	        #xbmc.executebuiltin("Notification(Multiroom Audio,Event Action: QueuedNext ME,15000,"+DEFAULT_IMG+")")
	# MediaChanged Audio eg: <b>MediaChanged:<li>AudioTitle:Wish You Were Here<li>AudioArtist:Pink Floyd;x.x.x.x;1</b>
        # For Shoucast Streams   <b>MediaChanged:<li>AudioTitle:1060;x.x.x.x;1</b>
        if msg.startswith('<b>MediaChanged:<li>AudioTitle'):
	    l = msg.lstrip('<b>MediaChanged:<li>AudioTitle:')
	    r = l.rstrip('</b>')
            if (r.find('<li>AudioArtist:') >= 0 ):
	        parts = r.split('<li>AudioArtist:')
	        song = (parts[0])
	        m1 = (parts[1])
	        m2 = m1.split(';')
	        artist = (m2[0])
	        srcip = (m2[1])
	        if (srcip == MSTR):
		    xbmc.executebuiltin("Notification(Now Playing on "+MSTRNM+", "+song+" By:"+artist+",15000,"+DEFAULT_IMG+")")
	        #else:
	            #xbmc.executebuiltin("Notification(Multiroom Audio,Event Action: Audio Playing ME,15000,"+DEFAULT_IMG+")")
            #else:
                #xbmc.executebuiltin("Notification(Multiroom Audio,Event Action: Shoutcast Playing,15000,"+DEFAULT_IMG+")")

	# MediaChanged Movie eg: <b>MediaChanged:<li>MovieTitle:21;192.168.100.152;1</b>
        if msg.startswith('<b>MediaChanged:<li>MovieTitle'):
	    l = msg.lstrip('<b>MediaChanged:<li>MovieTitle:')
	    r = l.rstrip('</b>')
	    parts = r.split(';')
	    title = (parts[0])
	    srcip = (parts[1])
	    if (srcip == MSTR):
		if (srcip == __settings__.getSetting(id="mstr_sync" )):
	            xbmc.executebuiltin("Notification(Now Playing on "+MSTRNM+", "+title+",15000,"+DEFAULT_IMG+")")
	    #else:
	        #xbmc.executebuiltin("Notification(Multiroom Audio,Now Playing: "+title+",15000,"+DEFAULT_IMG+")")

#############################################################################################################
 # Running Script Starts here:
#############################################################################################################
## Assumes XBMC was Restarted or worse.. Crashed. So we need to reset the running flags to false when XBMC restarts
_createmavdb()
__settings__.setSetting(id="mstrrunningflag", value="false")
__settings__.setSetting(id="clientrunningflag", value="false")
_strtstrmr()

##    def _bcasttoggle(self):
log("MAV UDP Receiver Started and Running in background...")
port = 8278  # where do you expect to get a msg?
bufferSize = 1024 # whatever you need
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.bind(('0.0.0.0', 8278)) ## You also specify a specific intf, like '255.255.255.255' for Bcast or '127.0.0.1' for localhost...
s.setblocking(0)
xbmc.executebuiltin("Notification(Multiroom Audio,MAV Service Started,2000,"+DEFAULT_IMG+")")
while True:
    result = select.select([s],[],[])
    msg    = result[0][0].recv(bufferSize) 
    _action(msg)
