# Put this file into Q:\scripts folder to be executed when XBMC starts.
import os
import xbmc

# Change this path according your XBMC setup (you may not need 'My Scripts')
mavudprcvr = xbmc.translatePath(os.path.join( "special://home/", "addons", "plugin.program.multiroomaudio", "resources", "lib", "rcvUDP.py" ) )
xbmc.executescript(mavudprcvr)
mavudpsndr = xbmc.translatePath(os.path.join( "special://home/", "addons", "plugin.program.multiroomaudio", "resources", "lib", "sendUDP.py" ) )
xbmc.executescript(mavudpsndr)

