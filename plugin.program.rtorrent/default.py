# main imports
import sys
import os
import urllib
import xbmc
import xbmcaddon
import xbmcgui

#extra imports
from resources.lib.functions import *
import resources.lib.globals as g

params=get_params()

url=None
hash=None
mode=None
numfiles=None
method=None
arg1=None
arg2=None
arg3=None
test=False

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

if mode==None:
	import resources.lib.mode_main as loader
	loader.main()
elif mode=='files':
	import resources.lib.mode_files as loader
	loader.main(hash,numfiles)
elif mode=='action':
	import resources.lib.mode_action as loader
	loader.main(method,arg1,arg2,arg3)
elif mode=='play':
	import resources.lib.mode_play as loader
	loader.main(hash,arg1)