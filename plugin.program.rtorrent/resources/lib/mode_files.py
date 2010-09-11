#Imports
from functions import *
g = __import__('global')
import xbmcgui
import xbmcplugin
import urllib
import xbmc

#Files inside a multi-file torrent code
def main(hash,numfiles):
	for i in range(0,numfiles):
		f_name = g.rtc.f.get_path(hash, i)
		f_frozen_path = g.rtc.f.get_frozen_path(hash, i)
		f_completed_chunks = g.rtc.f.get_completed_chunks(hash, i)
		f_size_chunks = g.rtc.f.get_size_chunks(hash, i)
		f_percent_complete = f_completed_chunks*100/f_size_chunks
		f_priority = g.rtc.f.get_priority(hash,i)
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
		cm = [(g.__lang__(30120),"xbmc.runPlugin(%s?mode=action&method=f.set_priority&arg1=%s&arg2=%s&arg3=2)" % ( sys.argv[0], hash,i)), \
			(g.__lang__(30121),"xbmc.runPlugin(%s?mode=action&method=f.set_priority&arg1=%s&arg2=%s&arg3=1)" % ( sys.argv[0], hash,i)), \
			(g.__lang__(30124),"xbmc.runPlugin(%s?mode=action&method=f.set_priority&arg1=%s&arg2=%s&arg3=0)" % ( sys.argv[0], hash,i))]
		li.addContextMenuItems(items=cm,replaceItems=True)
		if not xbmcplugin.addDirectoryItem(int(sys.argv[1]), \
			sys.argv[0]+"?mode=play&arg1="+str(i)+"&hash="+hash, \
			li,totalItems=numfiles): break
	xbmcplugin.endOfDirectory(int(sys.argv[1]), cacheToDisc=False)