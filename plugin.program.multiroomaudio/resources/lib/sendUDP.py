from time import time, ctime, sleep
import os, sys, socket, urllib2, select
import xbmc, xbmcaddon
import re, traceback, time

__settings__   = xbmcaddon.Addon("plugin.program.multiroomaudio")
DEFAULT_IMG = xbmc.translatePath(os.path.join( "special://home/", "addons", "plugin.program.multiroomaudio", "icon.png" ) )

#############################################################################################################
def log(msg):
	try:
		xbmc.output("[%s]: %s\n" % ("MAV",msg))
	except:
		pass

#################################################################################################################
 # Starts here
#################################################################################################################
##    def _bcasttoggle(self):
localhost      = xbmc.getIPAddress()
port_xbmc      = "8080"
udp_xbmc       = "8278"
xbmc_level     = "129"
url = "http://" + str(localhost) + ":" + str(port_xbmc) + "/xbmcCmds/xbmcHttp?command=SetBroadcast(" + str(xbmc_level) + ";" + str(udp_xbmc) + ")"
usock = urllib2.urlopen(url)
data = usock.read()
usock.close()
print data

## xbmc.executebuiltin("Notification(Multiroom Audio,MAV Broadcast Started,10000,"+DEFAULT_IMG+")")
log("MAV UDP Sender Started and Running in background...")
outsock        = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
bcast          = "255.255.255.255"
poll           = 60  ## Poll time in seconds
name	       = __settings__.getSetting( "sap_name" )
strm_type      = __settings__.getSetting( "vstrm_type" )
streaming_ip   = __settings__.getSetting( "streaming_ip" )
streaming_port = __settings__.getSetting( "streaming_port" )
url	           = ""+strm_type+"://@"+streaming_ip+":"+streaming_port+""
if (__settings__.getSetting(id="glbl_mstr" ) == "true"):
    udpdata    = "MAV Master @ "+localhost+" "+name+" "+url+""
else:
    udpdata    = "MAV Client @ "+localhost+" "+name+" "+url+""

while 1: 
    outsock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    outsock.sendto(udpdata, ('255.255.255.255', 8278))
    log(">> MAV UDP Sent - "+udpdata+"")
    ## xbmc.executebuiltin("Notification(Multiroom Audio,Sent Broadcast Active,1000,"+DEFAULT_IMG+")")
    sleep(poll)
