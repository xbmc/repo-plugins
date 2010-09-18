# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# Author: VortexRotor (teshephe)
# v.1.0.9 (BETA)r2

"""
    Plugin for True "Syncronized" Multiroom Streaming Audio/Video
"""

# main imports
import sys, os, time, re, urllib, shutil, subprocess
import xbmc, xbmcgui, xbmcplugin, xbmcaddon

Addon   = xbmcaddon.Addon(id=os.path.basename(os.getcwd()))
pDialog = xbmcgui.DialogProgress()
pDialog.create( sys.modules[ "__main__" ].__plugin__ )

# source path for multiroomaudio data
BASE_CURRENT_SOURCE_PATH = xbmc.translatePath( os.path.join( "special://profile/addon_data", sys.modules[ "__main__" ].__plugin__, "avsources.xml" ) )
SHORTCUT_FILE            = xbmc.translatePath( os.path.join( "special://profile/addon_data", sys.modules[ "__main__" ].__plugin__, "shortcut.cut" ) )
PLAYERCORE               = xbmc.translatePath( os.path.join( "special://profile", "playercorefactory.xml" ) )
STREAMER		 = xbmc.translatePath( os.path.join( "special://profile/addon_data", sys.modules[ "__main__" ].__plugin__, "strtstrmr_lin" ) )
STRTSTRMR_FILE           = xbmc.translatePath( os.path.join( "special://profile/addon_data", sys.modules[ "__main__" ].__plugin__, "strtstrmr_win.ps1" ) )
STRTSTRMRBAT_FILE        = xbmc.translatePath( os.path.join( "special://profile/addon_data", sys.modules[ "__main__" ].__plugin__, "strtstrmr.bat" ) )
LOOPBACK_FILE            = xbmc.translatePath( os.path.join( "special://profile/addon_data", sys.modules[ "__main__" ].__plugin__, "loopback_win.ps1" ) )
WINMAVlb_FILE            = xbmc.translatePath( os.path.join( "special://profile/addon_data", sys.modules[ "__main__" ].__plugin__, "winMavlb.bat" ) )
WINMAV_FILE              = xbmc.translatePath( os.path.join( "special://profile/addon_data", sys.modules[ "__main__" ].__plugin__, "winMav.bat" ) )
LINMAVlb_FILE            = xbmc.translatePath( os.path.join( "special://profile/addon_data", sys.modules[ "__main__" ].__plugin__, "linMavlb" ) )
LINMAV_FILE              = xbmc.translatePath( os.path.join( "special://profile/addon_data", sys.modules[ "__main__" ].__plugin__, "linMav" ) )
DEFAULT_IMG      	 = xbmc.translatePath(os.path.join( "special://home/", "addons", sys.modules[ "__main__" ].__plugin__, "icon.png" ) )
MAVFOO			 = xbmc.translatePath(os.path.join( "special://home/", "addons", sys.modules[ "__main__" ].__plugin__, "resources", "" ) )
# avsource - source script file generation operators for sources related file creation/maintenance respectfully
ADDONDATA_PATH		 = xbmc.translatePath( os.path.join( "special://profile/addon_data", sys.modules[ "__main__" ].__plugin__, "" ) )
SRCPLS_PATH              = xbmc.translatePath( os.path.join( Addon.getSetting( "pls_path" ), "Multiroom-AV", "" ) )
VIDEO_PATH               = xbmc.translatePath( os.path.join( SRCPLS_PATH, "VIDEO", "" ) )
AUDIO_PATH               = xbmc.translatePath( os.path.join( SRCPLS_PATH, "AUDIO", "" ) )
PULSE                    = xbmc.translatePath( "~/" )
REMOVE_COMMAND   	 = "%%REMOVE%%"
ADD_COMMAND      	 = "%%ADD%%"
IMPORT_COMMAND   	 = "%%IMPORT%%"
SCAN_COMMAND     	 = "%%SCAN%%"
RENAME_COMMAND   	 = "%%RENAME%%"
EDIT_COMMAND     	 = "%%EDIT%%"
EDITIP_COMMAND     	 = "%%EDITIP%%"
WAIT_TOGGLE_COMMAND 	 = "%%WAIT_TOGGLE%%"
COMMAND_ARGS_SEPARATOR   = "^^"

class Main:
    BASE_CACHE_PATH = xbmc.translatePath(os.path.join( "special://profile/Thumbnails", "Pictures" ))
    avsources = {}

    ''' initializes plugin and run the requiered action arguments:
            
                (blank)     - open a list of the available avsources. if no avsource exists - open the avsource creation wizard.
    '''                        
#############################################################################################################
    def __init__( self ):
        # store an handle pointer
        self._handle = int(sys.argv[ 1 ])
        print self._handle

        self._path = sys.argv[ 0 ]

        # get settings
        self._get_settings()
        Addon.setSetting(id="localhost", value=xbmc.getIPAddress())
	# have we ever started this sucker before?
	self._firstime()
	# now lets see what we have in the box...
        self._load_avsources(self.get_xml_source())

        if (Addon.getSetting(id="dedicated" ) == "true"):
	    if (Addon.getSetting( "strtstrm_strtup" ) == "true"):
                self._startstrmr()

        # if a commmand is passed as parameter
        param = sys.argv[ 2 ]
        if param:
            param = param[1:]
            command = param.split(COMMAND_ARGS_SEPARATOR)
            dirname = os.path.dirname(command[0])
            basename = os.path.basename(command[0])
            
            # check the action needed
            if (dirname):
                avsource = dirname
                avclient = basename
                if (avclient == REMOVE_COMMAND):
                    # check if it is a single avclient or a avsource
                    if (not os.path.dirname(avsource)):
			self._remove_avsource(avsource)
                    else:
                        self._remove_avclient(os.path.dirname(avsource), os.path.basename(avsource))
                if (avclient == RENAME_COMMAND):
                    # check if it is a single avclient or a avsource
                    if (not os.path.dirname(avsource)):
                        self._rename_avsource(avsource)
                    else:
                        self._rename_avclient(os.path.dirname(avsource), os.path.basename(avsource))
                if (avclient == EDIT_COMMAND):
                    # check if it is a single avclient or a avsource
                    if (not os.path.dirname(avsource)):
                        self._edit_avsource(avsource)
                    else:
                        self._edit_avclient(os.path.dirname(avsource), os.path.basename(avsource))
                elif (avclient == EDITIP_COMMAND):
                    # check if it is a single avclient or a avsource
                    if (not os.path.dirname(avsource)):
                        self._editip_avsource(avsource)
                    else:
                        self._edit_avclient(os.path.dirname(avsource), os.path.basename(avsource))
                else:
                    self._run_avclient(avsource, avclient)
            else:
                avsource = basename
                # if it's an add command
                if (avsource == ADD_COMMAND):
                    self._add_new_avsource()
                else:
                    self._run_avsource(avsource)
        else:
            # otherwise get the list of sources in the db
            if (not self._get_avsources()):
                # if no avsource found - attempt to add a new one
                if (self._add_new_avsource()):
                    self._get_avsources()
                else:
                    xbmcplugin.endOfDirectory( handle=int( self._handle ), succeeded=False , cacheToDisc=False)

#############################################################################################################                    
    def _remove_avclient(self, avsource, avclient):        
        dialog = xbmcgui.Dialog()
        ret = dialog.yesno(Addon.getLocalizedString( 30000 ), Addon.getLocalizedString( 30010 ) % avclient)
        if (ret):
            self.avsources[avsource]["avclients"].pop(avclient)
            self._save_avsources()
            xbmc.executebuiltin("Container.Refresh")

#############################################################################################################            
    def _remove_avsource(self, avsourceName):
	if (avsourceName == "Start Streamer"):
	    return ""
	if (avsourceName == "Stop Multiroom-AV"):
	    return ""
	if (avsourceName == "Generate Files"):
	    return ""
	if (avsourceName == "Loopback"):
	    return ""


        dialog = xbmcgui.Dialog()
        ret = dialog.yesno(Addon.getLocalizedString( 30000 ), Addon.getLocalizedString( 30010 ) % avsourceName)
	srcname = avsourceName
        if (sys.platform == 'win32'):
	    subprocess.Popen([r"del",r""+VIDEO_PATH+""+srcname+"*"],shell=True) 	 
	    subprocess.Popen([r"del",r""+AUDIO_PATH+""+srcname+"*"],shell=True) 	 
        else:
            if (sys.platform.startswith('linux')):
		os.system("rm "+VIDEO_PATH+""+srcname+"*") 	 
		os.system("rm "+AUDIO_PATH+""+srcname+"*") 	 
            else: 
		os.system("rm "+VIDEO_PATH+""+srcname+"*") 	 
		os.system("rm "+AUDIO_PATH+""+srcname+"*") 	 

        if (ret):
            self.avsources.pop(avsourceName)
	    self._save_avsources()
            xbmc.executebuiltin("Container.Refresh")

#############################################################################################################            
    def _rename_avclient(self, avsource, avclient):        
        keyboard = xbmc.Keyboard(self.avsources[avsource]["avclients"][avclient]["name"], Addon.getLocalizedString( 30018 ))
        keyboard.doModal()
        if (keyboard.isConfirmed()):
            self.avsources[avsource]["avclients"][avclient]["name"] = keyboard.getText()
            self._save_avsources()
            xbmc.executebuiltin("Container.Refresh")

#############################################################################################################        
    def _rename_avsource(self, avsourceName):
	if (avsourceName == "Start Streamer"):
	    return ""
	if (avsourceName == "Stop Multiroom-AV"):
	    return ""
	if (avsourceName == "Generate Files"):
	    return ""
	if (avsourceName == "Loopback"):
	    return ""

	srcname = avsourceName
        keyboard = xbmc.Keyboard(self.avsources[avsourceName]["name"], Addon.getLocalizedString( 30025 ))
        keyboard.doModal()
        if (keyboard.isConfirmed()):

            if (sys.platform == 'win32'):
	    	subprocess.Popen([r"del",r""+VIDEO_PATH+""+srcname+"*"],shell=True) 	 
	    	subprocess.Popen([r"del",r""+AUDIO_PATH+""+srcname+"*"],shell=True) 	 
            else:
                if (sys.platform.startswith('linux')):
		    os.system("rm "+VIDEO_PATH+""+srcname+"*") 	 
		    os.system("rm "+AUDIO_PATH+""+srcname+"*") 	 
                else: 
		    os.system("rm "+VIDEO_PATH+""+srcname+"*") 	 
		    os.system("rm "+AUDIO_PATH+""+srcname+"*") 	 
	    
            self.avsources[avsourceName]["name"] = keyboard.getText()
            self._save_avsources()
            xbmc.executebuiltin("Container.Refresh")

#############################################################################################################
    def _edit_avclient(self, avsource, avclient):        
        keyboard = xbmc.Keyboard(self.avsources[avsource]["avclients"][avclient]["name"], Addon.getLocalizedString( 30036 ))
        keyboard.doModal()
        if (keyboard.isConfirmed()):
            self.avsources[avsource]["avclients"][avclient]["name"] = keyboard.getText()
            self._save_avsources()
            xbmc.executebuiltin("Container.Refresh")

#############################################################################################################        
    def _edit_avsource(self, avsourceName):
	if (avsourceName == "Start Streamer"):
	    return ""
	if (avsourceName == "Stop Multiroom-AV"):
	    return ""
	if (avsourceName == "Generate Files"):
	    return ""

        keyboard = xbmc.Keyboard(self.avsources[avsourceName]["streamsrc"], Addon.getLocalizedString( 30036 ))
        keyboard.doModal()
        if (keyboard.isConfirmed()):

            self.avsources[avsourceName]["streamsrc"] = keyboard.getText()
            self._save_avsources()
            xbmc.executebuiltin("Container.Refresh")

#############################################################################################################        
    def _editip_avsource(self, avsourceName):
	if (avsourceName == "Start Streamer"):
	    return ""
	if (avsourceName == "Stop Multiroom-AV"):
	    return ""
	if (avsourceName == "Generate Files"):
	    return ""
	if (avsourceName == "Loopback"):
	    return ""

        keyboard = xbmc.Keyboard(self.avsources[avsourceName]["srcA"], Addon.getLocalizedString( 30003 ))
        keyboard.doModal()
        if (keyboard.isConfirmed()):
            self.avsources[avsourceName]["srcA"] = keyboard.getText()
            self._save_avsources()
            xbmc.executebuiltin("Container.Refresh")

#############################################################################################################
    def _run_avsource(self, avsourceName):
        if (self.avsources.has_key(avsourceName)):
	    avsource = self.avsources[avsourceName]
            if (avsourceName == 'Generate Files'):
                dialog = xbmcgui.Dialog()
                if dialog.yesno(Addon.getLocalizedString( 30001 ), Addon.getLocalizedString( 30004 ) % avsourceName):		
                   self._generate()
		else:
		    xbmc.executebuiltin("Notification(Multiroom Audio, File Generation Cancelled,3000,"+DEFAULT_IMG+")")
            if (avsourceName == 'Start Streamer'):
		if (Addon.getSetting( "mstrrunningflag" ) == "false"):
		    self._startstrmr()
	    if (avsourceName == 'Stop Multiroom-AV'):
		stopdialog = xbmcgui.Dialog()
		if stopdialog.yesno(Addon.getLocalizedString( 30000 ), Addon.getLocalizedString( 30005 ) ):
		   self._kill()
		##  We will implement decisive kill control later - for now we kill all vlc streams
		##if (Addon.getSetting( "mstrrunningflag" ) == "true"):
		    ##self._kill()
		##else:
		    ##xbmc.executebuiltin("Notification(Multiroom Audio,Streamer Already Stopped,15000,"+DEFAULT_IMG+")")

	    	##if (Addon.getSetting( "clientrunningflag" ) == "true"):
		    ##self._kill()
		##else:
		    ##xbmc.executebuiltin("Notification(Multiroom Audio,All Sources Stopped,15000,"+DEFAULT_IMG+")")

	    if (avsourceName == 'Loopback'):
		if (Addon.getSetting( "clientrunningflag" ) == "false"):
		    xbmc.executehttpapi("PlayFile("+VIDEO_PATH+""+avsource["name"]+".pls)")
		    xbmc.executebuiltin("PlayerControl(RepeatOff)")
		    Addon.setSetting(id="clientrunningflag", value="true")
		    xbmc.executebuiltin("Notification(Multiroom Audio,"+avsource["name"]+" Active,10000,"+DEFAULT_IMG+")")
		else:
		    xbmc.executebuiltin("Notification(Multiroom Audio,A source is already Active,5000,"+DEFAULT_IMG+")")
	
	    if "AV-Source" in avsourceName:
		if (Addon.getSetting( "clientrunningflag" ) == "false"):
		    xbmc.executehttpapi("PlayFile("+VIDEO_PATH+""+avsource["name"]+".pls)")
		    xbmc.executebuiltin("PlayerControl(RepeatOff)")
		    Addon.setSetting(id="clientrunningflag", value="true")
		    xbmc.executebuiltin("Notification(Multiroom Audio,"+avsource["name"]+" Active,10000,"+DEFAULT_IMG+")")
		else:
		    xbmc.executebuiltin("Notification(Multiroom Audio,A source is already Active,5000,"+DEFAULT_IMG+")")

#############################################################################################################
    def _run_avclient(self, avsourceName, avclientName):
        if (self.avsources.has_key(avsourceName)):
            avsource = self.avsources[avsourceName]
            if (avsource["avclients"].has_key(avclientName)):
                avclient = self.avsources[avsourceName]["avclients"][avclientName]
                if (os.environ.get( "OS", "xbox" ) == "xbox"):
                    f=open(SHORTCUT_FILE, "wb")
                    f.write("<shortcut>\n")
                    f.write("    <path>" + avsource["application"] + "</path>\n")
                    f.write("    <custom>\n")
                    f.write("       <game>" + avclient["filename"] + "</game>\n")
                    f.write("    </custom>\n")
                    f.write("</shortcut>\n")
                    f.close()
                    xbmc.executebuiltin('XBMC.Runxbe(' + SHORTCUT_FILE + ')')                    
                else:
                    if (sys.platform == 'win32'):
                        if (avsource["wait"] == "true"):
                            cmd = "System.ExecWait"
                        else:
                            cmd = "System.Exec"
                        xbmc.executebuiltin("%s(\"%s\" %s \"%s\")" % (cmd, avsource["application"], avsource["args"], avclient["filename"]))
                    elif (sys.platform.startswith('linux')):
 						os.system("\"%s\" %s \"%s\"" % (avsource["application"], avsource["args"], avclient["filename"]))
                    elif (sys.platform.startswith('darwin')):
                        os.system("\"%s\" %s \"%s\"" % (avsource["application"], avsource["args"], avclient["filename"]))
                    else:
                        pass;
                        # unsupported platform

#############################################################################################################
    def _startstrmr( self ):
        if (Addon.getSetting(id="dedicated" ) == "true"):
	    if (Addon.getSetting( "mstrrunningflag" ) == "false"):
	    	if (sys.platform == 'win32'):
 		    subprocess.call("powershell -WindowStyle \"hidden\" \"& '"+STRTSTRMR_FILE+"\'\"")
		    if (Addon.getSetting( "playlocal" ) == "true"):
 		        subprocess.call("powershell -WindowStyle \"hidden\" \"& '"+LOOPBACK_FILE+"\'\"")
## 		        os.system(""+STRTSTRMRBAT_FILE+"")
		    xbmc.executebuiltin("Notification(Multiroom Audio,Streamer Started,5000,"+DEFAULT_IMG+")")
		    Addon.setSetting(id="mstrrunningflag", value="true")
	    	else:
		    if (sys.platform.startswith('linux')):
		        os.system(""+ADDONDATA_PATH+"./strtstrmr_lin")
		        xbmc.executebuiltin("Notification(Multiroom Audio,Streamer Started,10000,"+DEFAULT_IMG+")")
		        ## if (Addon.getSetting( "playlocal" ) == "true"):
 		        ##    subprocess.call(""+ADDONDATA_PATH+"./loopback_lin")
		        Addon.setSetting(id="mstrrunningflag", value="true")
	    else:
	        xbmc.executebuiltin("Notification(Multiroom Audio,Streamer is already Started,5000,"+DEFAULT_IMG+")")
	else:
	    xbmc.executebuiltin("Notification(Multiroom Audio,Not setup as a Dedicated Master,10000,"+DEFAULT_IMG+")")

#############################################################################################################
    def _kill( self ):
	Addon.setSetting(id="mstrrunningflag", value="false")
	Addon.setSetting(id="clientrunningflag", value="false")
	xbmc.executehttpapi("Stop()")
	xbmc.executebuiltin("playlist.clear()")
	xbmc.executebuiltin("Notification(Multiroom Audio,All Streaming Stopped,7000,"+DEFAULT_IMG+")")
	if (sys.platform == 'win32'):
##	    os.spawnl(os.P_NWAIT,r"taskkill /IM vlc.exe")
	    os.system("taskkill /F /IM vlc.exe")
	else:
      	    if (sys.platform.startswith('linux')):
 		os.system("killall vlc | killall screen")
            else: 
                os.system("killall vlc | killall screen")
	

    ''' get an xml data from an xml file '''
#############################################################################################################
    def get_xml_source( self ):
        try:
            usock = open( BASE_CURRENT_SOURCE_PATH, "r" )
            # read source
            xmlSource = usock.read()
            # close socket
            usock.close()
            ok = True
        except:
            # oops print error message
            print "ERROR: %s::%s (%d) - %s" % ( self.__class__.__name__, sys.exc_info()[ 2 ].tb_frame.f_code.co_name, sys.exc_info()[ 2 ].tb_lineno, sys.exc_info()[ 1 ], )
            ok = False
        if ( ok ):
            # return the xml string without \n\r (newline)
            return xmlSource.replace("\n","").replace("\r","")
        else:
            return ""

#############################################################################################################
    def _save_avsources (self):
        # make settings directory if doesn't exists
        if (not os.path.isdir(os.path.dirname(BASE_CURRENT_SOURCE_PATH))):
            os.makedirs(os.path.dirname(BASE_CURRENT_SOURCE_PATH));
        
	self._save_srcpls()
	self._save_Mavfiles()

	usock = open( BASE_CURRENT_SOURCE_PATH, "w" )
        usock.write("<?xml version=\"1.0\" encoding=\"utf-8\" standalone=\"yes\"?>\n")
        usock.write("<avsources>\n")
        for avsourceIndex in self.avsources:
            avsource       = self.avsources[avsourceIndex]
	    vlc_loc        =  xbmc.translatePath(Addon.getSetting( "vlc_loc" ))
	    localhost      =  Addon.getSetting( "localhost" )
	    streaming_ip   =  Addon.getSetting( "streaming_ip" )
	    streaming_port =  Addon.getSetting( "streaming_port" )
	    vstrm_type     =  Addon.getSetting( "vstrm_type" )
            usock.write("\t<avsource>\n")
            usock.write("\t\t<name>"+avsource["name"]+"</name>\n")

	    # This can be any valid application on the OS but for the purpose of this 
	    # we are using it as a stop-gap measure to give the ability to manually
	    # Kill the VLC processes for a given source in case something FUNKY happens.
	    if (avsource == 'Stop Multiroom-AV'):
                if (sys.platform == 'win32'):
		    usock.write("\t\t<application>taskkill /F /IM vlc.exe</application>\n")
                else:
            	    if (sys.platform.startswith('linux')):
 		        usock.write("\t\t<application>killall vlc</application>\n")
            	    else: 
                        usock.write("\t\t<application>killall vlc</application>\n")
	    else:
		usock.write("\t\t<application>"+avsource["application"]+"</application>\n")

	    # PLACEHOLDER: We can add these too as an option to force overlay playing audio only
	    #  --audio-visual visual --effect-list spectrometer 
            if (sys.platform == 'win32'):
		usock.write("\t\t<args></args>\n")
            else:
            	if (sys.platform.startswith('linux')):
 		    usock.write("\t\t<args></args>\n")
            	else: 
                    usock.write("\t\t<args></args>\n")

	    if (avsource == 'Loopback'):		
	        usock.write("\t\t<streamsrc>"+vstrm_type+"://@"+streaming_ip+":"+streaming_port+"</streamsrc>\n")
	    else:
	        usock.write("\t\t<streamsrc>"+avsource["streamsrc"]+"</streamsrc>\n")

            usock.write("\t\t<avclientpath>"+VIDEO_PATH+""+avsource["name"]+".pls</avclientpath>\n")
            usock.write("\t\t<asrcpath>"+AUDIO_PATH+""+avsource["name"]+".pls</asrcpath>\n")

	    if (avsource == 'Loopback'):		
            	usock.write("\t\t<srcA>"+localhost+"</srcA>\n")
	    else:
                usock.write("\t\t<srcA>"+avsource["srcA"]+"</srcA>\n")

            usock.write("\t\t<srcB></srcB>\n")
            usock.write("\t\t<thumb>"+DEFAULT_IMG+"</thumb>\n")
	    usock.write("\t\t<srctype>"+avsource["srctype"]+"</srctype>\n")
            usock.write("\t\t<wait>false</wait>\n")
            usock.write("\t\t<avclients>\n")
            for avclientIndex in avsource["avclients"]:
                avclientdata = avsource["avclients"][avclientIndex]
                usock.write("\t\t\t<avclient>\n")
                usock.write("\t\t\t\t<name>"+avclientdata["name"]+"</name>\n")
                usock.write("\t\t\t\t<filename>"+avclientdata["filename"]+"</filename>\n")
                usock.write("\t\t\t\t<thumb>"+avclientdata["thumb"]+"</thumb>\n")
                usock.write("\t\t\t</avclient>\n")
            usock.write("\t\t</avclients>\n")
            usock.write("\t</avsource>\n")            
        usock.write("</avsources>")
        usock.close()
	
#############################################################################################################
    def _save_Mavfiles(self):
        # make settings directory if doesn't exists
        if (not os.path.isdir(os.path.dirname(ADDONDATA_PATH))):
            os.makedirs(os.path.dirname(ADDONDATA_PATH));
            
	localhost      =  Addon.getSetting( "localhost" )
	streaming_ip   =  Addon.getSetting( "streaming_ip" )
	streaming_port =  Addon.getSetting( "streaming_port" )
	vlc_loc        =  xbmc.translatePath(Addon.getSetting( "vlc_loc" ))
	default_vp     =  Addon.getSetting( "default_vp" )
	default_ap     =  Addon.getSetting( "default_ap" )
	mstr_sync      =  Addon.getSetting( "mstr_sync" )
	sound_dev      =  Addon.getSetting( "sound_dev" )
	sap_name       =  Addon.getSetting( "sap_name" )
    	playlocal      =  Addon.getSetting( "playlocal" )
	vstrm_type     =  Addon.getSetting( "vstrm_type" )
	video_sout     =  Addon.getSetting( "video_sout" )
	video_fc       =  Addon.getSetting( "video_fc" )
	astrm_type     =  Addon.getSetting( "vstrm_type" )
	audio_sout     =  Addon.getSetting( "video_sout" )
	audio_fc       =  Addon.getSetting( "video_fc" )
        if (sys.platform == 'win32'):
	    usock    = open( STRTSTRMR_FILE, "w" )
            usock.write("[Diagnostics.Process]::Start(\'"+vlc_loc+"\',\" -I dummy --dummy-quiet dshow:// --dshow-vdev=none --dshow-adev=`\""+sound_dev+"`\" --dshow-caching=10 --sout=#transcode{vcodec=none,acodec=mp3,ab=128,channels=2,samplerate=44100}:"+astrm_type+"{dst="+streaming_ip+":"+streaming_port+"} --netsync-master --sout-rtp-sap --sout-rtp-name="+sap_name+" --sout-standard-sap --sout-standard-name=xbmc_"+sap_name+" --sout-standard-group=Multiroom_AV --file-caching="+audio_fc+"\")\n")
            usock.write("\n")
            usock.close()

	    usock    = open( LOOPBACK_FILE, "w" )
            usock.write("[Diagnostics.Process]::Start(\'"+vlc_loc+"\',\" -I dummy --dummy-quiet "+vstrm_type+"://@"+streaming_ip+":"+streaming_port+" --netsync-master-ip="+mstr_sync+" --netsync-timeout=500 --fullscreen --file-caching="+video_fc+"\")\n")
            usock.write("\n")
            usock.close()

            usock    = open( WINMAV_FILE, "w" )
            usock.write("echo off\n")
            usock.write("echo WINMAV\n")
            usock.write("\n")
            usock.write("taskkill /F /IM vlc.exe\n")
            usock.write("\n")
            usock.write("\n")
            usock.write("echo %1\n")
            usock.write("echo So far so good... now Lets Broadcast the stuff were play'n\n")
	    usock.write("\""+vlc_loc+"\" -I dummy --dummy-quiet --started-from-file --playlist-enqueue \"%1\" --play-and-exit --extraintf=http --http-host "+localhost+":8084 --sout=\'#std{access="+vstrm_type+",mux=ts,dst="+streaming_ip+":"+streaming_port+"}\' --netsync-master --sout-rtp-sap --sout-rtp-name="+sap_name+" --sout-standard-sap --sout-standard-name=xbmc_"+sap_name+" --sout-standard-group=Multiroom_AV --file-caching=300\n")
            usock.write("\n")
	    usock.write("taskkill /F /IM vlc.exe\n")
	    if (Addon.getSetting( "default_vp" ) == "MR-Video_Stream"):
                usock.write("\n")
                usock.write("echo Restarting Master Streamer\n")
                usock.write("powershell -WindowStyle \"hidden\" \"& \'"+STRTSTRMR_FILE+"\'\"\n")
	    else:
                usock.close()
	
	    if (Addon.getSetting( "playlocal" ) == "true"):
                usock = open( WINMAVlb_FILE, "w" )
                usock.write("echo off\n")
                usock.write("echo WINMAV w/ Loopback via WINMAVlb\n")
                usock.write("\n")
                usock.write("taskkill /F /IM vlc.exe\n")
                usock.write("\n")
                usock.write("echo Lets start the loopback session\n")
                usock.write("powershell -WindowStyle \"hidden\" \"& \'"+LOOPBACK_FILE+"\'\"\n")
                usock.write("\n")
                usock.write("echo %1\n")
                usock.write("echo So far so good... now Lets Broadcast the stuff were play'n\n")
		usock.write("\""+vlc_loc+"\" -I dummy --dummy-quiet \"%1\" --play-and-exit --extraintf=http --http-host "+localhost+":8084 --sout=#std{access="+vstrm_type+",mux=ts,dst="+streaming_ip+":"+streaming_port+"} --netsync-master --sout-rtp-sap --sout-rtp-name="+sap_name+" --sout-standard-sap --sout-standard-name=xbmc_"+sap_name+" --sout-standard-group=Multiroom_AV --file-caching=300\n")
                usock.write("\n")
	        usock.write("taskkill /F /IM vlc.exe\n")
	        if (Addon.getSetting( "default_vp" ) == "MR-Video_Stream"):
                    usock.write("\n")
                    usock.write("echo Restarting Master Streamer\n")
                    usock.write("powershell -WindowStyle \"hidden\" \"& \'"+STRTSTRMR_FILE+"\'\"\n")
                usock.write("\n")
                usock.write("echo Restarting the Loopback\n")
                usock.write("powershell -WindowStyle \"hidden\" \"& \'"+LOOPBACK_FILE+"\'\"\n")
                usock.close()

	else:
            if (sys.platform.startswith('linux')):
	        usock    = open( STREAMER, "w" )
                usock.write("#!/bin/bash\n")
                usock.write("\n")
                usock.write("if pidof vlc | grep [0-9] > /dev/null\n")
                usock.write("then\n")
                usock.write("killall vlc\n")
                usock.write("killall screen\n")
                usock.write("exit\n")
                usock.write("else\n")
		if (Addon.getSetting( "playlocal" ) == "true"):
                    usock.write("screen -d -m -S MAV-Loopback\n")
                usock.write("screen -d -m -S MAV-Streamer\n")
		if (Addon.getSetting( "playlocal" ) == "true"):
                    usock.write("screen -S MAV-Loopback -p 0 -X exec "+vlc_loc+" --intf dummy --extraintf=http --http-host "+localhost+":8085 "+vstrm_type+"://@"+streaming_ip+":"+streaming_port+" --netsync-master-ip="+localhost+" --netsync-timeout=500 --fullscreen --file-caching="+audio_fc+"\n")
                usock.write("screen -S MAV-Streamer -p 0 -X exec "+vlc_loc+" --intf dummy rtp://@127.0.0.1:46998 --rtp-caching=1000 --extraintf=http --http-host "+localhost+":8084 --sout=\'#transcode{vcodec=none,acodec=mp3,ab=128,channels=2,samplerate=44100}:"+vstrm_type+"{dst="+streaming_ip+":"+streaming_port+"}\' --sout-rtp-sap --sout-rtp-name="+sap_name+" --sout-standard-sap --sout-standard-name=xbmc_"+sap_name+" --sout-standard-group=Multiroom_AV --sout-keep\n")
                usock.write("fi\n")
                usock.close()
		os.system("chmod +x "+STREAMER+"") 

#############################################################################################################
    def _save_srcpls (self):
        # make settings directory if doesn't exists
        if (not os.path.isdir(os.path.dirname(SRCPLS_PATH))):
            os.makedirs(os.path.dirname(SRCPLS_PATH));
        if (not os.path.isdir(os.path.dirname(VIDEO_PATH))):
            os.makedirs(os.path.dirname(VIDEO_PATH));
        if (not os.path.isdir(os.path.dirname(AUDIO_PATH))):
            os.makedirs(os.path.dirname(AUDIO_PATH));

        for avsourceIndex in self.avsources:
            avsource = self.avsources[avsourceIndex]            
	    plsv1  = VIDEO_PATH
	    plsv2  = ""+avsource["name"]+""
	    plsv   = ""+plsv1+plsv2+".pls"
            usock  = open( plsv, "w" )
            usock.write("[playlist]\n")
            usock.write("NumberOfEntries=1\n")
            usock.write("File1="+avsource["streamsrc"]+"\n")
            usock.close()
            plsa1  = AUDIO_PATH
            plsa2  = ""+avsource["name"]+""
            plsa   = ""+plsa1+plsa2+".pls"
            usock  = open( plsa, "w" )
            usock.write("[playlist]\n")
            usock.write("NumberOfEntries=1\n")
            usock.write("File1="+avsource["streamsrc"]+"\n")
            usock.close()

            if (sys.platform == 'win32'):
                subprocess.Popen([r"copy",r""+DEFAULT_IMG+"",r""+plsv1+""+plsv2+".tbn"],shell=True)
	        subprocess.Popen([r"copy",r""+DEFAULT_IMG+"",r""+plsv1+"default.tbn"],shell=True)
	        subprocess.Popen([r"copy",r""+DEFAULT_IMG+"",r""+plsa1+""+plsa2+".tbn"],shell=True)
	        subprocess.Popen([r"copy",r""+DEFAULT_IMG+"",r""+plsa1+"default.tbn"],shell=True)
	        subprocess.Popen([r"del",r""+plsv1+"St*"],shell=True)
	        subprocess.Popen([r"del",r""+plsv1+"Gen*"],shell=True)
	        subprocess.Popen([r"del",r""+plsa1+"St*"],shell=True)
	        subprocess.Popen([r"del",r""+plsa1+"Gen*"],shell=True)

            else:
                if (sys.platform.startswith('linux')):
		    os.system("cp "+DEFAULT_IMG+" "+plsv1+""+plsv2+".tbn") 	 
		    os.system("cp "+DEFAULT_IMG+" "+plsv1+"default.tbn") 	 
		    os.system("rm "+plsv1+"St*") 	 
		    os.system("rm "+plsv1+"Gen*") 	 
		    os.system("cp "+DEFAULT_IMG+" "+plsa1+""+plsa2+".tbn") 	 
		    os.system("cp "+DEFAULT_IMG+" "+plsa1+"default.tbn") 	 
		    os.system("rm "+plsa1+"Gen*") 	 
		    os.system("rm "+plsa1+"St*") 	 
                else: 
		    os.system("cp "+DEFAULT_IMG+" "+plsv1+""+plsv2+".tbn") 	 
		    os.system("cp "+DEFAULT_IMG+" "+plsv1+"default.tbn") 	 
		    os.system("rm "+plsv1+"St*") 	 
		    os.system("rm "+plsv1+"Gen*") 	 
		    os.system("cp "+DEFAULT_IMG+" "+plsa1+""+plsa2+".tbn") 	 
		    os.system("cp "+DEFAULT_IMG+" "+plsa1+"default.tbn") 	 
		    os.system("rm "+plsa1+"St*") 	 
		    os.system("rm "+plsa1+"Gen*") 	 
	    
#############################################################################################################
    def _save_serverXXfile (self):
        # make settings directory if doesn't exists
        if (not os.path.isdir(os.path.dirname(SRCPLS_PATH))):
            os.makedirs(os.path.dirname(SRCPLS_PATH));
            
        for avsourceIndex in self.avsources:
            avsource = self.avsources[avsourceIndex]
	    vlc_loc  = xbmc.translatePath(Addon.getSetting( "vlc_loc" ))
            usock    = open( SRCPLS_PATH, "w" )
            usock.write("#!/bin/bash\n")
            usock.write("\n")
            usock.write("if pidof vlc | grep [0-9] > /dev/null\n")
            usock.write("then\n")
	    usock.write("WID=`xdotool search --class \"XBMC\"`;\n")
	    usock.write("wmctrl -c \""+avsource["srctype"]+"B\"\n")
	    usock.write("xdotool windowactivate $WID\n")
	    usock.write("wget -q \"http://localhost:8081/xbmcCmds/xbmcHttp?command=ExecBuiltIn(Notification(Multiroom Audio,"+avsource["name"]+" - DeActivated,30000,"+ DEFAULT_IMG +"))\"\n")
	    usock.write("else\n")
            usock.write("xterm -display :0 -T "+avsource["srctype"]+"B -e "+SRCPLS_PATH+"./"+avsource["srcB"]+"\n")
	    usock.write("\n")
            usock.write("fi")
            usock.close()

            if (sys.platform == 'win32'):
##		os.spawnl(r'copy '+SRCPLS_PATH+' '+SRCPLS_PATH+''+avsource["srcA"]+'')  
                os.system('copy '+SRCPLS_PATH+' '+SRCPLS_PATH+''+avsource["srcA"]+'')
            else:
            	if (sys.platform.startswith('linux')):
 		    os.system('cp '+SRCPLS_PATH+' '+SRCPLS_PATH+''+avsource["srcA"]+'')
            	else: 
                    os.system('cp '+SRCPLS_PATH+' '+SRCPLS_PATH+''+avsource["srcA"]+'')

#############################################################################################################
    def	_save_serverXXdatafile(self): 
        # make settings directory if doesn't exists
        if (not os.path.isdir(os.path.dirname(SRCPLS_PATH))):
            os.makedirs(os.path.dirname(SRCPLS_PATH));
	    
        for avsourceIndex in self.avsources:
            avsource = self.avsources[avsourceIndex]            
	    vlc_loc  =  Addon.getSetting( "vlc_loc" )
            usock    = open( SRCPLS_PATH, "w" )
            usock.write("#!/bin/bash\n")
            usock.write("\n")
            usock.write("WID=`xdotool search --class \"XBMC\"`;\n")
            usock.write("xdotool windowactivate $WID\n")
            usock.write("wmctrl -c \""+avsource["srctype"]+"A\"\n")
	    # (Additional options: --audio-visual visual --effect-list spectrometer)
	    usock.write(""+vlc_loc+"vlc "+avsource["streamsrc"]+"\n")
            usock.close()

            if (sys.platform == 'win32'):
##		os.spawnl(r'copy '+SRCPLS_PATH+' '+SRCPLS_PATH+''+avsource["srcB"]+'')  
                os.system('copy '+SRCPLS_PATH+' '+SRCPLS_PATH+''+avsource["srcB"]+'')
            else:
            	if (sys.platform.startswith('linux')):
 		    os.system('cp '+SRCPLS_PATH+' '+SRCPLS_PATH+''+avsource["srcB"]+'')
            	else: 
                    os.system('cp '+SRCPLS_PATH+' '+SRCPLS_PATH+''+avsource["srcB"]+'')
	    
#############################################################################################################
    def	_save_playercorefactoryfile( self ): 
	    localhost      =  Addon.getSetting( "localhost" )
	    streaming_ip   =  Addon.getSetting( "streaming_ip" )
	    streaming_port =  Addon.getSetting( "streaming_port" )
	    vlc_loc        =  xbmc.translatePath(Addon.getSetting( "vlc_loc" ))
	    default_vp     =  Addon.getSetting( "default_vp" )
	    default_ap     =  Addon.getSetting( "default_ap" )
	    sap_name       =  Addon.getSetting( "sap_name" )
	    mstr_sync      =  Addon.getSetting( "mstr_sync" )
	    vstrm_type     =  Addon.getSetting( "vstrm_type" )
	    video_sout     =  Addon.getSetting( "video_sout" )
	    video_fc       =  Addon.getSetting( "video_fc" )
	    avisualize	   =  Addon.getSetting( "avisualize" )
	    astrm_type     =  Addon.getSetting( "astrm_type" )
	    audio_sout     =  Addon.getSetting( "audio_sout" )
	    audio_fc       =  Addon.getSetting( "audio_fc" )
            usock = open( PLAYERCORE, "w" )
            usock.write("<playercorefactory>\n")
            usock.write("  <players>\n")
            usock.write("    <!-- This File was created by Multiroom Streaming AV Plugin for XBMC\n")
            usock.write("    These are compiled-in as re-ordering them would break scripts\n")
            usock.write("    The following aliases may also be used:\n")
            usock.write("    audiodefaultplayer, videodefaultplayer, videodefaultdvdplayer\n")
            usock.write("    <player name=\"DVDPlayer\" audio=\"true\" video=\"true\" />\n")
            usock.write("    <player name=\"DVDPlayer\" /> placeholder for MPlayer\n")
            usock.write("    <player name=\"PAPlayer\" audio=\"true\" />\n")
            usock.write("    -->\n")
            usock.write("    <player name=\"MR-Video_Stream\" type=\"ExternalPlayer\" audio=\"false\" video=\"true\">\n")

            if (sys.platform == 'win32'):
		if (Addon.getSetting( "playlocal" ) == "true"):
                    usock.write("      <filename>"+WINMAVlb_FILE+"</filename>\n")
                    usock.write("      <args>\"{1}\"</args>\n")
		else:
                    usock.write("      <filename>"+WINMAV_FILE+"</filename>\n")
                    usock.write("      <args>\"{1}\"</args>\n")
            else:
            	if (sys.platform.startswith('linux')):
		    if (Addon.getSetting( "dedicated" ) == "true"):
                	usock.write("      <filename>"+vlc_loc+"</filename>\n")
 		        usock.write("      <args>--started-from-file --playlist-enqueue \"{1}\" --play-and-exit --extraintf=http --http-host "+localhost+":8084 "+video_sout+" --sout=\'#std{access="+vstrm_type+",mux=ts,dst="+streaming_ip+":"+streaming_port+"}\' --netsync-master --sout-rtp-sap --sout-rtp-name="+sap_name+" --sout-standard-sap --sout-standard-name=xbmc_"+sap_name+" --sout-standard-group=Multiroom_AV --file-caching="+video_fc+"</args>\n")
		    else: 
			if (Addon.getSetting( "playlocal" ) == "true"):
                	    usock.write("      <filename>"+vlc_loc+"</filename>\n")
 		            usock.write("      <args>--started-from-file --playlist-enqueue \"{1}\" --play-and-exit --extraintf=http --http-host "+localhost+":8084 "+video_sout+" --sout=\'#std{access="+vstrm_type+",mux=ts,dst="+streaming_ip+":"+streaming_port+"}\' --netsync-master --sout-rtp-sap --sout-rtp-name="+sap_name+" --sout-standard-sap --sout-standard-name=xbmc_"+sap_name+" --sout-standard-group=Multiroom_AV --file-caching="+video_fc+" | "+vlc_loc+" --intf dummy "+vstrm_type+"://@"+streaming_ip+":"+streaming_port+" --file-caching=0 --fullscreen</args>\n")
		        else:
	                    usock.write("      <filename>"+vlc_loc+"</filename>\n")
                    	    usock.write("      <args>--started-from-file --playlist-enqueue \"{1}\" --play-and-exit --extraintf=http --http-host "+localhost+":8084 "+video_sout+" --sout=\'#std{access="+vstrm_type+",mux=ts,dst="+streaming_ip+":"+streaming_port+"}\' --netsync-master --sout-rtp-sap --sout-rtp-name="+sap_name+" --sout-standard-sap --sout-standard-name=xbmc_"+sap_name+" --sout-standard-group=Multiroom_AV --file-caching="+video_fc+"</args>\n")
		else: 
		    if (Addon.getSetting( "dedicated" ) == "true"):
                	usock.write("      <filename>"+vlc_loc+"</filename>\n")
 		        usock.write("      <args>--started-from-file --playlist-enqueue \"{1}\" --play-and-exit --extraintf=http --http-host "+localhost+":8084 "+video_sout+" --sout=\'#std{access="+vstrm_type+",mux=ts,dst="+streaming_ip+":"+streaming_port+"}\' --netsync-master --sout-rtp-sap --sout-rtp-name="+sap_name+" --sout-standard-sap --sout-standard-name=xbmc_"+sap_name+" --sout-standard-group=Multiroom_AV --file-caching="+video_fc+"</args>\n")
		    else: 
			if (Addon.getSetting( "playlocal" ) == "true"):
                	    usock.write("      <filename>"+vlc_loc+"</filename>\n")
 		            usock.write("      <args>--started-from-file --playlist-enqueue \"{1}\" --play-and-exit --extraintf=http --http-host "+localhost+":8084 "+video_sout+" --sout=\'#std{access="+vstrm_type+",mux=ts,dst="+streaming_ip+":"+streaming_port+"}\' --netsync-master --sout-rtp-sap --sout-rtp-name="+sap_name+" --sout-standard-sap --sout-standard-name=xbmc_"+sap_name+" --sout-standard-group=Multiroom_AV --file-caching="+video_fc+" | "+vlc_loc+" --intf dummy "+vstrm_type+"://@"+streaming_ip+":"+streaming_port+" --file-caching=0 --fullscreen</args>\n")
		        else:
	                    usock.write("      <filename>"+vlc_loc+"</filename>\n")
                    	    usock.write("      <args>--started-from-file --playlist-enqueue \"{1}\" --play-and-exit --extraintf=http --http-host "+localhost+":8084 "+video_sout+" --sout=\'#std{access="+vstrm_type+",mux=ts,dst="+streaming_ip+":"+streaming_port+"}\' --netsync-master --sout-rtp-sap --sout-rtp-name="+sap_name+" --sout-standard-sap --sout-standard-name=xbmc_"+sap_name+" --sout-standard-group=Multiroom_AV --file-caching="+video_fc+"</args>\n")

            usock.write("      <hidexbmc>false</hidexbmc>\n")
            usock.write("      <hideconsole>true</hideconsole>\n")
            usock.write("      <warpcursor>none</warpcursor>\n")
            usock.write("      <playonestackitem>false</playonestackitem>\n")
            usock.write("    </player>\n")
            usock.write("    <player name=\"MR-Audio_Stream\" type=\"ExternalPlayer\" audio=\"true\" video=\"false\">\n")

            if (sys.platform == 'win32'):
		if (Addon.getSetting( "playlocal" ) == "true"):
                    usock.write("      <filename>"+WINMAVlb_FILE+"</filename>\n")
                    usock.write("      <args>\"{1}\"</args>\n")
		else:
                    usock.write("      <filename>"+WINMAV_FILE+"</filename>\n")
                    usock.write("      <args>\"{1}\"</args>\n")
            else:
            	if (sys.platform.startswith('linux')):
		    if (Addon.getSetting( "dedicated" ) == "true"):
                	usock.write("      <filename>"+vlc_loc+"</filename>\n")
 		        usock.write("      <args>--started-from-file --playlist-enqueue \"{1}\" --play-and-exit --extraintf=http --http-host "+localhost+":8084 "+audio_sout+" --sout=\'#std{access="+astrm_type+",mux=ts,dst="+streaming_ip+":"+streaming_port+"}\' --netsync-master --sout-rtp-sap --sout-rtp-name="+sap_name+" --sout-standard-sap --sout-standard-name=xbmc_"+sap_name+" --sout-standard-group=Multiroom_AV --file-caching="+audio_fc+"</args>\n")
		    else: 
			if (Addon.getSetting( "playlocal" ) == "true"):
                	    usock.write("      <filename>"+vlc_loc+"</filename>\n")
 		            usock.write("      <args>--started-from-file --playlist-enqueue \"{1}\" --play-and-exit --extraintf=http --http-host "+localhost+":8084 "+audio_sout+" --sout=\'#std{access="+astrm_type+",mux=ts,dst="+streaming_ip+":"+streaming_port+"}\' --netsync-master --sout-rtp-sap --sout-rtp-name="+sap_name+" --sout-standard-sap --sout-standard-name=xbmc_"+sap_name+" --sout-standard-group=Multiroom_AV --file-caching="+audio_fc+" | "+vlc_loc+" --intf dummy "+astrm_type+"://@"+streaming_ip+":"+streaming_port+" --file-caching=0 --fullscreen</args>\n")
		    	else:
	                    usock.write("      <filename>"+vlc_loc+"</filename>\n")
                    	    usock.write("      <args>--started-from-file --playlist-enqueue \"{1}\" --play-and-exit --extraintf=http --http-host "+localhost+":8084 "+audio_sout+" --sout=\'#std{access="+astrm_type+",mux=ts,dst="+streaming_ip+":"+streaming_port+"}\' --netsync-master --sout-rtp-sap --sout-rtp-name="+sap_name+" --sout-standard-sap --sout-standard-name=xbmc_"+sap_name+" --sout-standard-group=Multiroom_AV --file-caching="+audio_fc+"</args>\n")
		else: 
		    if (Addon.getSetting( "dedicated" ) == "true"):
                	usock.write("      <filename>"+vlc_loc+"</filename>\n")
 		        usock.write("      <args>--started-from-file --playlist-enqueue \"{1}\" --play-and-exit --extraintf=http --http-host "+localhost+":8084 "+audio_sout+" --sout=\'#std{access="+astrm_type+",mux=ts,dst="+streaming_ip+":"+streaming_port+"}\' --netsync-master --sout-rtp-sap --sout-rtp-name="+sap_name+" --sout-standard-sap --sout-standard-name=xbmc_"+sap_name+" --sout-standard-group=Multiroom_AV --file-caching="+audio_fc+"</args>\n")
		    else: 
			if (Addon.getSetting( "playlocal" ) == "true"):
                	    usock.write("      <filename>"+vlc_loc+"</filename>\n")
 		            usock.write("      <args>--started-from-file --playlist-enqueue \"{1}\" --play-and-exit --extraintf=http --http-host "+localhost+":8084 "+audio_sout+" --sout=\'#std{access="+astrm_type+",mux=ts,dst="+streaming_ip+":"+streaming_port+"}\' --netsync-master --sout-rtp-sap --sout-rtp-name="+sap_name+" --sout-standard-sap --sout-standard-name=xbmc_"+sap_name+" --sout-standard-group=Multiroom_AV --file-caching="+audio_fc+" | "+vlc_loc+" --intf dummy "+astrm_type+"://@"+streaming_ip+":"+streaming_port+" --file-caching=0 --fullscreen</args>\n")
		    	else:
	                    usock.write("      <filename>"+vlc_loc+"</filename>\n")
                    	    usock.write("      <args>--started-from-file --playlist-enqueue \"{1}\" --play-and-exit --extraintf=http --http-host "+localhost+":8084 "+audio_sout+" --sout=\'#std{access="+astrm_type+",mux=ts,dst="+streaming_ip+":"+streaming_port+"}\' --netsync-master --sout-rtp-sap --sout-rtp-name="+sap_name+" --sout-standard-sap --sout-standard-name=xbmc_"+sap_name+" --sout-standard-group=Multiroom_AV --file-caching="+audio_fc+"</args>\n")

            usock.write("      <hidexbmc>false</hidexbmc>\n")
            usock.write("      <hideconsole>true</hideconsole>\n")
            usock.write("      <warpcursor>none</warpcursor>\n")
            usock.write("      <playonestackitem>false</playonestackitem>\n")
            usock.write("    </player>\n")
            usock.write("    <player name=\"MR-AV_VPlay\" type=\"ExternalPlayer\" audio=\"true\" video=\"true\">\n")

            if (sys.platform == 'win32'):
                usock.write("      <filename>"+vlc_loc+"</filename>\n")
		usock.write("      <args>--intf dummy --dummy-quiet \"{1}\" --play-and-exit --extraintf=http --http-host="+localhost+":8085  --netsync-master --netsync-master-ip="+mstr_sync+" --netsync-timeout=500 --file-caching=0 --fullscreen </args>\n")
            else:
            	if (sys.platform.startswith('linux')):
            	    usock.write("      <filename>"+vlc_loc+"</filename>\n")
 		    usock.write("      <args>--intf dummy \"{1}\" --play-and-exit --extraintf=http --http-host "+localhost+":8085 --netsync-master-ip="+mstr_sync+" --netsync-timeout=500 --file-caching=0 --fullscreen</args>\n")
            	else: 
            	    usock.write("      <filename>"+vlc_loc+"</filename>\n")
                    usock.write("      <args>--intf dummy \"{1}\" --play-and-exit --extraintf=http --http-host "+localhost+":8085 --netsync-master-ip="+mstr_sync+" --netsync-timeout=500 --file-caching=0 --fullscreen</args>\n")

            usock.write("      <hidexbmc>false</hidexbmc>\n")
            usock.write("      <hideconsole>true</hideconsole>\n")
            usock.write("      <warpcursor>none</warpcursor>\n")
            usock.write("      <playonestackitem>false</playonestackitem>\n")
            usock.write("    </player>\n")
            usock.write("    <player name=\"MR-AV_APlay\" type=\"ExternalPlayer\" audio=\"true\" video=\"true\">\n")
            usock.write("      <filename>"+vlc_loc+"</filename>\n")

            if (sys.platform == 'win32'):
		usock.write("      <args>--intf dummy --dummy-quiet \"{1}\" --play-and-exit --extraintf=http --http-host="+localhost+":8085 --netsync-master-ip="+mstr_sync+" --netsync-timeout=500 --file-caching=0 --fullscreen --audio-visual visual --effect-list "+avisualize+"</args>\n")
            else:
            	if (sys.platform.startswith('linux')):
 		    usock.write("      <args>--intf dummy \"{1}\" --play-and-exit --extraintf=http --http-host "+localhost+":8085 --netsync-master-ip="+mstr_sync+" --netsync-timeout=500 --file-caching=0 --fullscreen --audio-visual visual --effect-list "+avisualize+"</args>\n")
            	else: 
                    usock.write("      <args>--intf dummy \"{1}\" --play-and-exit --extraintf=http --http-host "+localhost+":8085 --netsync-master-ip="+mstr_sync+" --netsync-timeout=500 --file-caching=0 --fullscreen --audio-visual visual --effect-list "+avisualize+"</args>\n")

            usock.write("      <hidexbmc>false</hidexbmc>\n")
            usock.write("      <hideconsole>true</hideconsole>\n")
            usock.write("      <warpcursor>none</warpcursor>\n")
            usock.write("      <playonestackitem>false</playonestackitem>\n")
            usock.write("    </player>\n")
            usock.write("  </players>\n")
            usock.write("    <rules action=\"overwrite\">\n")
            usock.write("      <!-- DVDs -->\n")
            usock.write("      <rule name=\"dvd\" dvd=\"true\" player=\""+default_vp+"\" />\n")
            usock.write("      <rule name=\"dvdfile\" dvdfile=\"true\" player=\""+default_vp+"\" />\n")
            usock.write("      <rule name=\"dvdimage\" dvdimage=\"true\" player=\""+default_vp+"\" />\n")
            usock.write("\n")
            usock.write("      <!-- Multiroom AV Plugin will play the pls files -->\n")
            usock.write("      <rule name=\"rtv\" protocols=\"rtv\" player=\""+default_vp+"\" />\n")
            usock.write("      <rule name=\"pls\" filetypes=\"pls\" player=\"MR-AV_VPlay\" />\n")
            usock.write("      <rule name=\"pls/udp\" protocols=\"rtmp|mms|mmsh|udp|http|rtsp|rtp\" player=\"MR-AV_VPlay\" />\n")
            usock.write("      <rule name=\"hdhomerun/myth/\" protocols=\"hdhomerun|myth|cmyth\" player=\""+default_vp+"\" />\n")
            usock.write("      <rule name=\"lastfm/shout\" protocols=\"lastfm|shout\" player=\"PAPlayer\" />\n")
            usock.write("      <rule video=\"true\" player=\""+default_vp+"\" />\n")
            usock.write("      <rule audio=\"true\" player=\""+default_ap+"\" />\n")
            usock.write("\n")  
            usock.write("      <!-- dvdplayer can play standard rtsp streams -->\n")
            usock.write("      <rule name=\"rtsp\" protocols=\"rtsp\" filetypes=\"!(rm|ra)\"  player=\""+default_ap+"\" />\n")
            usock.write("\n")  
            usock.write("      <!-- Internet streams -->\n")
            usock.write("      <rule name=\"streams\" internetstream=\"true\">\n")
            usock.write("        <rule name=\"flv/aacp/sdp\" mimetypes=\"video/x-flv|video-flv|audio/aacp|application/sdp\" player=\""+default_vp+"\" />\n")
            usock.write("        <rule name=\"mp2\" mimetypes=\"application/octet-stream\" filetypes=\"mp2\" player=\""+default_ap+"\" />\n")
            usock.write("      </rule>\n")
            usock.write("\n")  
            usock.write("      <!-- Only dvdplayer can handle these normally -->\n")
            usock.write("      <rule name=\"sdp/asf\" filetypes=\"sdp|asf\" player=\""+default_vp+"\" />\n")
            usock.write("\n")  
            usock.write("      <!-- Pass these to dvdplayer as we do not know if they are audio or video -->\n")
            usock.write("      <rule name=\"nsv\" filetypes=\"nsv\" player=\""+default_vp+"\" />\n")
            usock.write("    </rules>\n")
            usock.write("</playercorefactory>\n")
            usock.close()

    ''' read the list of avsources and avclients from avsources.xml file '''
#############################################################################################################
    def _load_avsources( self , xmlSource):
        avsources = re.findall( "<avsource>(.*?)</avsource>", xmlSource )
        print "AVsource: found %d avsources" % ( len(avsources) )
        for avsource in avsources:
            name = re.findall( "<name>(.*?)</name>", avsource )
            application = re.findall( "<application>(.*?)</application>", avsource )
            args = re.findall( "<args>(.*?)</args>", avsource )
            streamsrc = re.findall( "<streamsrc>(.*?)</streamsrc>", avsource )
            avclientpath = re.findall( "<avclientpath>(.*?)</avclientpath>", avsource )
            asrcpath = re.findall( "<asrcpath>(.*?)</asrcpath>", avsource )
            srcA = re.findall( "<srcA>(.*?)</srcA>", avsource )
            srcB = re.findall( "<srcB>(.*?)</srcB>", avsource )
            thumb = re.findall( "<thumb>(.*?)</thumb>", avsource )
	    srctype = re.findall( "<srctype>(.*?)</srctype>", avsource )
            wait = re.findall( "<wait>(.*?)</wait>", avsource )
            avclientsxml = re.findall( "<avclient>(.*?)</avclient>", avsource )

            if len(name) > 0 : name = name[0]
            else: name = "unknown"

            if len(application) > 0 : application = application[0]
            else: application = ""

            if len(args) > 0 : args = args[0]
            else: args = ""

	    if len(streamsrc) > 0 : streamsrc = streamsrc[0]
	    else: streamsrc = ""

            if len(avclientpath) > 0 : avclientpath = avclientpath[0]
            else: avclientpath = ""

            if len(asrcpath) > 0: asrcpath = asrcpath[0]
            else: asrcpath = ""

	    if len(srcA) > 0 : srcA = srcA[0]
	    else: srcA = ""

	    if len(srcB) > 0 : srcB = srcB[0]
	    else: srcB = ""

            if len(thumb) > 0: thumb = thumb[0]
            else: thumb = ""

            if len(srctype) > 0: srctype = srctype[0]
	    else: srctype = ""

            if len(wait) > 0: wait = wait[0]
            else: wait = ""
            
            avclients = {}
            for avclient in avclientsxml:
                avclientname = re.findall( "<name>(.*?)</name>", avclient )
                avclientfilename = re.findall( "<filename>(.*?)</filename>", avclient )
                avclientthumb = re.findall( "<thumb>(.*?)</thumb>", avclient )

                if len(avclientname) > 0 : avclientname = avclientname[0]
                else: avclientname = "unknown"

                if len(avclientfilename) > 0 : avclientfilename = avclientfilename[0]
                else: avclientfilename = ""

                if len(avclientthumb) > 0 : avclientthumb = avclientthumb[0]
                else: avclientthumb = ""

                # prepare avclient object data
                avclientdata = {}
                avclientdata["name"] = avclientname
                avclientdata["filename"] = avclientfilename
                avclientdata["thumb"] = avclientthumb

                # add avclient to the avclients list (using name as index)
                avclients[avclientname] = avclientdata

            # prepare avsource object data
            avsourcedata = {}
            avsourcedata["name"] = name
            avsourcedata["application"] = application
            avsourcedata["args"] = args
	    avsourcedata["streamsrc"] = streamsrc
            avsourcedata["avclientpath"] = avclientpath
            avsourcedata["asrcpath"] = asrcpath
            avsourcedata["srcA"] = srcA
            avsourcedata["srcB"] = srcB
            avsourcedata["thumb"] = thumb
            avsourcedata["srctype"] = srctype
            avsourcedata["wait"] = wait
            avsourcedata["avclients"] = avclients

            # add avsource to the avsources list (using name as index)
	    self._save_playercorefactoryfile()
            self.avsources[name] = avsourcedata

#############################################################################################################    
    def _get_avsources( self ):
        if (len(self.avsources) > 0):
            for index in self.avsources:
                avsource = self.avsources[index]
                self._add_avsource(avsource["name"], avsource["application"], avsource["avclientpath"], avsource["asrcpath"], avsource["thumb"], avsource["wait"], avsource["avclients"], len(self.avsources))
            xbmcplugin.endOfDirectory( handle=int( self._handle ), succeeded=True, cacheToDisc=False )
            return True
        else:
            return False

#############################################################################################################
##    def _get_avclients( self, avsourceName ):
##        if (self.avsources.has_key(avsourceName)):
##            selectedAVsource = self.avsources[avsourceName]
##            avclients = selectedAVsource["avclients"]
##            print "AVsource: %s : found %d avclients " % (avsourceName, len(avclients))
##            if (len(avclients) > 0) :
##                for index in avclients :
##                    avclient = avclients[index]
##                    self._add_avclient(avsourceName, avclient["name"], avclient["filename"], avclient["thumb"], len(avclients))
##            else:
##                dialog = xbmcgui.Dialog()
##                ret = dialog.yesno(Addon.getLocalizedString( 30000 ), Addon.getLocalizedString( 30013 ))
##                if (ret):
##                    self._import_avclients(avsourceName, addavclients = True)
##            xbmcplugin.endOfDirectory( handle=int( self._handle ), succeeded=True, cacheToDisc=False )
##            return True
##        else:
##            return False
##
#############################################################################################################
    def _report_hook( self, count, blocksize, totalsize ):
         percent = int( float( count * blocksize * 100) / totalsize )
         msg1 = Addon.getLocalizedString( 30033 )  % ( os.path.split( self.url )[ 1 ], )
         pDialog.update( percent, msg1 )
         if ( pDialog.iscanceled() ): raise

#############################################################################################################        
    def _scan_avsource(self, avsourcename):
        self._save_avsources()

#############################################################################################################
    def _import_avclients(self, avsourceName, addavclients = False):
        dialog = xbmcgui.Dialog()
        avclientsCount = 0
        filesCount = 0
        skipCount = 0
        selectedAVsource = self.avsources[avsourceName]
        pDialog = xbmcgui.DialogProgress()
        path = selectedAVsource["avclientpath"]
        exts = selectedAVsource["asrcpath"]
        avclients = selectedAVsource["avclients"]
        ret = pDialog.create(Addon.getLocalizedString( 30000 ), Addon.getLocalizedString( 30014 ) % (path));
        
        files = os.listdir(path)
        for f in files:
            pDialog.update(filesCount * 100 / len(files))
            fullname = os.path.join(path, f)
            for ext in exts.split("|"):
                avclientadded = False
                if f.upper().endswith("." + ext.upper()):
                    avclientname =  f[:-len(ext)-1].capitalize()
                    if (not avclients.has_key(avclientname)):
                        # prepare avclient object data
                        avclientdata = {}
                        avclientname =  f[:-len(ext)-1].capitalize()
                        avclientdata["name"] = avclientname
                        avclientdata["filename"] = fullname 
                        avclientdata["thumb"] = ""

                        # add avclient to the avclients list (using name as index)
                        avclients[avclientname] = avclientdata
                        avclientsCount = avclientsCount + 1
                        
                        if (addavclients):
                            self._add_avclient(avsourceName, avclientdata["name"], avclientdata["filename"], avclientdata["thumb"], len(files))
                            avclientadded = True
                if not avclientadded:
                    skipCount = skipCount + 1
               
            filesCount = filesCount + 1    
        pDialog.close()
        self._save_avsources()
        if (skipCount == 0):
            xbmc.executebuiltin("XBMC.Notification(%s,%s, 6000)" % (Addon.getLocalizedString( 30000 ), Addon.getLocalizedString( 30015 ) % (avclientsCount) + " " + Addon.getLocalizedString( 30050 )))
            #dialog.ok(Addon.getLocalizedString( 30000 ), (Addon.getLocalizedString( 30015 )+ "\n" + Addon.getLocalizedString( 30050 )) % (avclientsCount))
        else:
            xbmc.executebuiltin("XBMC.Notification(%s,%s, 12000)" % (Addon.getLocalizedString( 30000 ), Addon.getLocalizedString( 30016 ) % (avclientsCount, skipCount) + " " + Addon.getLocalizedString( 30050 )))
            #dialog.ok(Addon.getLocalizedString( 30000 ), (Addon.getLocalizedString( 30016 )+ "\n" + Addon.getLocalizedString( 30050 )) % (avclientsCount, skipCount))

#############################################################################################################
    def _get_thumbnail( self, thumbnail_url ):
        # make the proper cache filename and path so duplicate caching is unnecessary
        if ( not thumbnail_url.startswith( "http://" ) ): return thumbnail_url
        try:
            filename = xbmc.getCacheThumbName( thumbnail_url )
            filepath = xbmc.translatePath( os.path.join( self.BASE_CACHE_PATH, filename[ 0 ], filename ) )
            # if the cached thumbnail does not exist fetch the thumbnail
            if ( not os.path.isfile( filepath ) ):
                # fetch thumbnail and save to filepath
                info = urllib.urlretrieve( thumbnail_url, filepath )
                # cleanup any remaining urllib cache
                urllib.urlcleanup()
            return filepath
        except:
            # return empty string if retrieval failed
            print "ERROR: %s::%s (%d) - %s" % ( self.__class__.__name__, sys.exc_info()[ 2 ].tb_frame.f_code.co_name, sys.exc_info()[ 2 ].tb_lineno, sys.exc_info()[ 1 ], )
            return ""

#############################################################################################################        
    def _get_thumb(self, displayName, fileName):
        exts = ["jpg", "png", "gif","bmp"]
        for ext in exts:
            thumbfilename = os.path.join(self.settings[ "thumbs_path" ], "%s.%s" % (displayName, ext))
            if (os.path.isfile(thumbfilename)):
                return thumbfilename
            thumbfilename = os.path.join(self.settings[ "thumbs_path" ], "%s.%s" % (os.path.basename(fileName).split(".")[0], ext))
            if (os.path.isfile(thumbfilename)):
                return thumbfilename            

#############################################################################################################
    def _add_avsource(self, name, cmd, path, ext, thumb, wait, avclients, total) :
        commands = []
        commands.append((Addon.getLocalizedString( 30101 ), "XBMC.RunPlugin(%s?%s)" % (self._path, ADD_COMMAND) , ))
        if (sys.platform == "win32"):
##	    commands.append((Addon.getLocalizedString( 30103 ), "XBMC.RunPlugin(%s?%s/%s)" % (self._path, name, WAIT_TOGGLE_COMMAND) , ))
            commands.append((Addon.getLocalizedString( 30107 ), "XBMC.RunPlugin(%s?%s/%s)" % (self._path, name, RENAME_COMMAND) , ))
            commands.append((Addon.getLocalizedString( 30104 ), "XBMC.RunPlugin(%s?%s/%s)" % (self._path, name, REMOVE_COMMAND) , ))
            commands.append((Addon.getLocalizedString( 30108 ), "XBMC.RunPlugin(%s?%s/%s)" % (self._path, name, EDIT_COMMAND) , ))
            commands.append((Addon.getLocalizedString( 30110 ), "XBMC.RunPlugin(%s?%s/%s)" % (self._path, name, EDITIP_COMMAND) , ))
	else:
            if (sys.platform.startswith('linux')):
                commands.append((Addon.getLocalizedString( 30107 ), "XBMC.RunPlugin(%s?%s/%s)" % (self._path, name, RENAME_COMMAND) , ))
                commands.append((Addon.getLocalizedString( 30104 ), "XBMC.RunPlugin(%s?%s/%s)" % (self._path, name, REMOVE_COMMAND) , ))
                commands.append((Addon.getLocalizedString( 30108 ), "XBMC.RunPlugin(%s?%s/%s)" % (self._path, name, EDIT_COMMAND) , ))
                commands.append((Addon.getLocalizedString( 30110 ), "XBMC.RunPlugin(%s?%s/%s)" % (self._path, name, EDITIP_COMMAND) , ))
            else: 
                commands.append((Addon.getLocalizedString( 30107 ), "XBMC.RunPlugin(%s?%s/%s)" % (self._path, name, RENAME_COMMAND) , ))
                commands.append((Addon.getLocalizedString( 30104 ), "XBMC.RunPlugin(%s?%s/%s)" % (self._path, name, REMOVE_COMMAND) , ))
                commands.append((Addon.getLocalizedString( 30108 ), "XBMC.RunPlugin(%s?%s/%s)" % (self._path, name, EDIT_COMMAND) , ))
                commands.append((Addon.getLocalizedString( 30110 ), "XBMC.RunPlugin(%s?%s/%s)" % (self._path, name, EDITIP_COMMAND) , ))
       
        if (path == ""):
            folder = False
            icon = "DefaultProgram.png"
        else:
            folder = True
            icon = "DefaultFolder.png"
##            commands.append((Addon.getLocalizedString( 30105 ), "XBMC.RunPlugin(%s?%s/%s)" % (self._path, name, IMPORT_COMMAND) , ))
##            commands.append((Addon.getLocalizedString( 30106 ), "XBMC.RunPlugin(%s?%s/%s)" % (self._path, name, ADD_COMMAND) , ))            
##            commands.append((Addon.getLocalizedString( 30107 ), "XBMC.RunPlugin(%s?%s/%s)" % (self._path, name, RENAME_COMMAND) , ))
##            commands.append((Addon.getLocalizedString( 30104 ), "XBMC.RunPlugin(%s?%s/%s)" % (self._path, name, REMOVE_COMMAND) , ))
##            commands.append((Addon.getLocalizedString( 30108 ), "XBMC.RunPlugin(%s?%s/%s)" % (self._path, name, EDIT_COMMAND) , ))
##            commands.append((Addon.getLocalizedString( 30110 ), "XBMC.RunPlugin(%s?%s/%s)" % (self._path, name, EDITIP_COMMAND) , ))
        if (thumb):
            thumbnail = thumb
        else:
            thumbnail = self._get_thumb(name, cmd)
           
        if (thumbnail):
            listitem = xbmcgui.ListItem( name, iconImage=icon, thumbnailImage=thumbnail)
        else:
            listitem = xbmcgui.ListItem( name, iconImage=icon )
        listitem.addContextMenuItems( commands )
        xbmcplugin.addDirectoryItem( handle=int( self._handle ), url="%s?%s"  % (self._path, name), listitem=listitem, isFolder=folder, totalItems=total)

#############################################################################################################
    def _add_avclient( self, avsource, name, cmd , thumb, total):
        if (thumb):
            thumbnail = thumb
        else:
            thumbnail = self._get_thumb(name, cmd)
        icon = "DefaultProgram.png"
        if (thumbnail):
            listitem = xbmcgui.ListItem( name, iconImage=icon, thumbnailImage=thumbnail)
        else:
            listitem = xbmcgui.ListItem( name, iconImage=icon )
        commands = []
        commands.append(( Addon.getLocalizedString( 30107 ), "XBMC.RunPlugin(%s?%s/%s/%s)" % (self._path, avsource, name, RENAME_COMMAND) , ))
        commands.append(( Addon.getLocalizedString( 30108 ), "XBMC.RunPlugin(%s?%s/%s/%s)" % (self._path, avsource, name, EDIT_COMMAND) , ))
        commands.append(( Addon.getLocalizedString( 30110 ), "XBMC.RunPlugin(%s?%s/%s/%s)" % (self._path, avsource, name, EDITIP_COMMAND) , ))
        commands.append(( Addon.getLocalizedString( 30104 ), "XBMC.RunPlugin(%s?%s/%s/%s)" % (self._path, avsource, name, REMOVE_COMMAND) , ))
        listitem.addContextMenuItems( commands )
        xbmcplugin.addDirectoryItem( handle=int( self._handle ), url="%s?%s/%s"  % (self._path, avsource, name), listitem=listitem, isFolder=False, totalItems=total)

#############################################################################################################
    def _add_new_avclient ( self , avsourceName) :
        dialog = xbmcgui.Dialog()
        avsource = self.avsources[avsourceName]
        ext = avsource["asrcpath"]
        avclients = avsource["avclients"]
        avclientpath = avsource["avclientpath"]
        
        avclientfile = dialog.browse(1, Addon.getLocalizedString( 30017 ),"files", "."+ext, False, False, avclientpath)
        if (avclientfile):
            title=os.path.basename(avclientfile).split(".")[0].capitalize()
            keyboard = xbmc.Keyboard(title, Addon.getLocalizedString( 30018 ))
            keyboard.doModal()
            if (keyboard.isConfirmed()):
                title = keyboard.getText()

                # prepare avclient object data
                avclientdata = {}
                avclientdata["name"] = title
                avclientdata["filename"] = avclientfile
                avclientdata["thumb"] = ""

                # add avclient to the avclients list (using name as index)
                avclients[title] = avclientdata

                xbmc.executebuiltin("XBMC.Notification(%s,%s, 6000)" % (Addon.getLocalizedString( 30000 ), Addon.getLocalizedString( 30019 ) + " " + Addon.getLocalizedString( 30050 )))
                #xbmcgui.Dialog().ok(Addon.getLocalizedString( 30000 ), Addon.getLocalizedString( 30019 )+ "\n" + Addon.getLocalizedString( 30050 ))
        self._save_avsources()

#############################################################################################################
    def _add_new_avsource ( self ) :
        dialog = xbmcgui.Dialog()
        type = dialog.select(Addon.getLocalizedString( 30020 ), [Addon.getLocalizedString( 30021 )])
        if (os.environ.get( "OS", "xbox" ) == "xbox"):
            filter = ".xbe|.cut"
        else:
            if (sys.platform == "win32"):
                filter = ".bat|.exe"
            else:
                filter = ""
            
        if (type == 0):
	    srctype = "client"
	    srcprfx = "AV-Source-"
	    srcsufx = "NAME"
            app = "" 
            args = ""
            title = os.path.basename(app).split(".")[0].capitalize()
            keyboard = xbmc.Keyboard(title, Addon.getLocalizedString( 30025 ))
            keyboard.doModal()
            if (keyboard.isConfirmed()):
                title = keyboard.getText()                    
                streamsrckeyboard = xbmc.Keyboard("", Addon.getLocalizedString( 30037 ))
                streamsrckeyboard.doModal()
                if (streamsrckeyboard.isConfirmed()):
                    streamsrc = streamsrckeyboard.getText();
		    sourceipkeyboard = xbmc.Keyboard("", Addon.getLocalizedString( 30023 ))
                    sourceipkeyboard.doModal()	
		    if (sourceipkeyboard.isConfirmed()):
			sourceip = sourceipkeyboard.getText()
                    	# prepare avsource object data
                    	avsourcedata = {}
                    	avsourcedata["name"] = srcprfx+title
                    	avsourcedata["application"] = app
                    	avsourcedata["args"] = args
   		    	avsourcedata["streamsrc"] = streamsrc 
                    	avsourcedata["avclientpath"] = ""
                    	avsourcedata["asrcpath"] = ""
   		    	avsourcedata["srcA"] = sourceip
   		    	avsourcedata["srcB"] = ""
                    	avsourcedata["thumb"] = ""
                    	avsourcedata["srctype"] = srctype
                    	avsourcedata["wait"] = "true"
                    	avsourcedata["avclients"] = {}
                     
                # add avsource to the avsources list (using name as index)
                self.avsources[title] = avsourcedata
                self._save_avsources()
		    
                xbmc.executebuiltin("Container.Refresh")
                return True

        elif (type == 1):
            appkeyboard = xbmc.Keyboard("", Addon.getLocalizedString( 30038 ))
            appkeyboard.doModal()
            ### app = xbmcgui.Dialog().browse(1,Addon.getLocalizedString( 30023 ),"files",filter)
            if (appkeyboard.isConfirmed()): ### (app):
		srctype = "srvr" 
                appvarA = "xterm -display :0 -T srvrA -e "
                appvar1 = SRCPLS_PATH
		appvar2 = "./"
		appvar3 = "server"
		appvar4 = "data"              
		appvar5 = appkeyboard.getText();
                app = appvarA+appvar1+appvar2+appvar3+appvar5 
                argkeyboard = xbmc.Keyboard("", Addon.getLocalizedString( 30024 ))
                argkeyboard.doModal()
                if (argkeyboard.isConfirmed()):
                    args = argkeyboard.getText();
                    streamsrckeyboard = xbmc.Keyboard("", Addon.getLocalizedString( 30039 ))
                    streamsrckeyboard.doModal()
                    if (streamsrckeyboard.isConfirmed()):
                        streamsrc = streamsrckeyboard.getText();
			titleprefix = "Master Streamer - "
                        titlesuffix = os.path.basename(app).split(".")[0].capitalize()
			title = titleprefix+titlesuffix
                        keyboard = xbmc.Keyboard(title, Addon.getLocalizedString( 30025 ))
                        keyboard.doModal()
                        if (keyboard.isConfirmed()):
                            title = keyboard.getText()                    
			    sourceipkeyboard = xbmc.Keyboard("", Addon.getLocalizedString( 30023 ))
                            sourceipkeyboard.doModal()	
			    if (sourceipkeyboard.isConfirmed()):
				sourceip = sourceipkeyboard.getText()
                            	# prepare avsource object data
                            	avsourcedata = {}
                            	avsourcedata["name"] = title
                            	avsourcedata["application"] = app
                            	avsourcedata["args"] = args
   		      	    	avsourcedata["streamsrc"] = streamsrc 
                            	avsourcedata["avclientpath"] = ""
                            	avsourcedata["asrcpath"] = ""
   		      	    	avsourcedata["srcA"] = sourceip
   		      	    	avsourcedata["srcB"] = ""
                            	avsourcedata["thumb"] = ""
                            	avsourcedata["srctype"] = srctype
                            	avsourcedata["wait"] = "true"
                            	avsourcedata["avclients"] = {}
                    
                        # add avsource to the avsources list (using name as index)
                        self.avsources[title] = avsourcedata
                        self._save_avsources()

                        xbmc.executebuiltin("Container.Refresh")
                        return True
        return False

#############################################################################################################
    def _get_search_engine( self ):
        exec "import resources.search_engines.%s.search_engine as search_engine" % ( self.settings[ "search_engine" ], )
        return search_engine.SearchEngine()

#############################################################################################################                                
    def _get_settings( self ):
        self.settings = {}
	self.settings[ "streaming_ip" ]   =  Addon.getSetting( "streaming_ip" )      
	self.settings[ "streaming_port" ] =  Addon.getSetting( "streaming_port" )      
	self.settings[ "default_vp" ]     =  Addon.getSetting( "default_vp" )
	self.settings[ "default_ap" ]     =  Addon.getSetting( "default_ap" )
	self.settings[ "vlc_loc" ]        =  xbmc.translatePath(Addon.getSetting( "vlc_loc" ))      
	self.settings[ "video_sout" ]     =  Addon.getSetting( "video_sout" )      
	self.settings[ "video_fc" ]       =  Addon.getSetting( "video_fc" )      
	self.settings[ "audio_sout" ]     =  Addon.getSetting( "audio_sout" )      
	self.settings[ "audio_fc" ]       =  Addon.getSetting( "audio_fc" )      
	self.settings[ "pls_path" ]       =  xbmc.translatePath(Addon.getSetting( "pls_path" ))
	self.settings[ "thumbs_path" ]    =  xbmc.translatePath(Addon.getSetting( "thumbs_path" ))
	self.settings[ "search_engine" ]  =  Addon.getSetting( "search_engine" )      

        ## if (not os.path.isdir(os.path.dirname(self.settings[ "pls_path" ]))):
        ##	os.makedirs(os.path.dirname(self.settings[ "pls_path" ]));

	if (not os.path.isdir(os.path.dirname(self.settings[ "thumbs_path" ]))):
	    os.makedirs(os.path.dirname(self.settings[ "thumbs_path" ]));

#############################################################################################################                                
    def _firstime( self ):
	if (Addon.getSetting( "firstimeflag" ) == "true"):
	    if (not os.path.isdir(os.path.dirname(BASE_CURRENT_SOURCE_PATH))):
                os.makedirs(os.path.dirname(BASE_CURRENT_SOURCE_PATH));
	    hostip    =  xbmc.getIPAddress()
	    vlc_loc   =  xbmc.translatePath(Addon.getSetting( "vlc_loc" ))
	    pulseloc  =  xbmc.translatePath(Addon.getSetting( "pls_path" ))
	    usock = open( BASE_CURRENT_SOURCE_PATH, "w" )
            usock.write("<?xml version=\"1.0\" encoding=\"utf-8\" standalone=\"yes\"?>\n")
            usock.write("<avsources>\n")
            usock.write("\t<avsource>\n")
            usock.write("\t\t<name>Stop Multiroom-AV</name>\n")

            if (sys.platform == 'win32'):
	        usock.write("\t\t<application>taskkill /F /IM vlc.exe</application>\n")
            else:
                if (sys.platform.startswith('linux')):
 		    usock.write("\t\t<application>killall vlc | killall screen</application>\n")
		    os.system("cp "+MAVFOO+"default.pa "+pulseloc+".pulse/default.pa")
                else: 
                    usock.write("\t\t<application>killall vlc | killall screen</application>\n")
		    os.system("cp "+MAVFOO+"default.pa "+pulseloc+".pulse/default.pa")

	    usock.write("\t\t<args></args>\n")
            usock.write("\t\t<streamsrc></streamsrc>\n")
            usock.write("\t\t<avclientpath></avclientpath>\n")
            usock.write("\t\t<asrcpath></asrcpath>\n")
            usock.write("\t\t<srcA></srcA>\n")
            usock.write("\t\t<srcB></srcB>\n")
            usock.write("\t\t<thumb>"+DEFAULT_IMG+"stp.png</thumb>\n")
            usock.write("\t\t<srctype></srctype>\n")
            usock.write("\t\t<wait></wait>\n")
            usock.write("\t</avsource>\n")            
            usock.write("\t<avsource>\n")
            usock.write("\t\t<name>Generate Files</name>\n")
	    usock.write("\t\t<application></application>\n")
	    usock.write("\t\t<args></args>\n")
            usock.write("\t\t<streamsrc></streamsrc>\n")
            usock.write("\t\t<avclientpath></avclientpath>\n")
            usock.write("\t\t<asrcpath></asrcpath>\n")
            usock.write("\t\t<srcA></srcA>\n")
            usock.write("\t\t<srcB></srcB>\n")
            usock.write("\t\t<thumb>"+DEFAULT_IMG+"gen.png</thumb>\n")
            usock.write("\t\t<srctype></srctype>\n")
            usock.write("\t\t<wait></wait>\n")
            usock.write("\t</avsource>\n")
            usock.write("\t<avsource>\n")
            usock.write("\t\t<name>Start Streamer</name>\n")
	    usock.write("\t\t<application></application>\n")
	    usock.write("\t\t<args></args>\n")
            usock.write("\t\t<streamsrc></streamsrc>\n")
            usock.write("\t\t<avclientpath></avclientpath>\n")
            usock.write("\t\t<asrcpath></asrcpath>\n")
            usock.write("\t\t<srcA></srcA>\n")
            usock.write("\t\t<srcB></srcB>\n")
            usock.write("\t\t<thumb>"+MAVFOO+"strt.png</thumb>\n")
            usock.write("\t\t<srctype></srctype>\n")
            usock.write("\t\t<wait></wait>\n")
            usock.write("\t</avsource>\n")
            usock.write("\t<avsource>\n")
            usock.write("\t\t<name>Loopback</name>\n")
	    usock.write("\t\t<application></application>\n")
	    usock.write("\t\t<args></args>\n")
            usock.write("\t\t<streamsrc>udp://@224.1.1.152:1152</streamsrc>\n")
            usock.write("\t\t<avclientpath></avclientpath>\n")
            usock.write("\t\t<asrcpath></asrcpath>\n")
            usock.write("\t\t<srcA>"+hostip+"</srcA>\n")
            usock.write("\t\t<srcB></srcB>\n")
            usock.write("\t\t<thumb>"+MAVFOO+"lb.png</thumb>\n")
            usock.write("\t\t<srctype></srctype>\n")
            usock.write("\t\t<wait></wait>\n")
            usock.write("\t</avsource>\n")
            usock.write("</avsources>")
            usock.close()
            Addon.setSetting(id="firstimeflag", value="false")

#############################################################################################################                                
    def _generate( self ):
##      if (self.avsources.has_key(avsourceName)):
##	if (avsourceName == "Generate Files"):
	pulseloc  =  xbmc.translatePath(Addon.getSetting( "pls_path" ))
        if (sys.platform.startswith('linux')):
	    os.system("cp "+MAVFOO+"default.pa "+PULSE+".pulse/default.pa")
	else:
	    os.system("cp "+MAVFOO+"default.pa "+PULSE+".pulse/default.pa") 	 
	self._save_srcpls()
	self._save_Mavfiles()
	self._save_playercorefactoryfile()
	xbmc.executebuiltin("Notification(Multiroom Audio, Files Generated Successfully,10000,"+DEFAULT_IMG+")")

