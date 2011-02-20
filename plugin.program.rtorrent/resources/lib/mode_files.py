#Imports
from functions import *
import globals as g
import xbmcgui
import xbmcplugin
import urllib
import xbmc

#Files inside a multi-file torrent code
def main(hash,numfiles):
	files = []
	files = g.rtc.f.multicall(hash,1,"f.get_path=","f.get_completed_chunks=","f.get_size_chunks=","f.get_priority=","f.get_size_bytes=")
	i=0
	for f in files:	
		f_name = f[0]
		f_completed_chunks = int(f[1])
		f_size_chunks = int(f[2])
		f_size_bytes = int(f[4])
		f_percent_complete = f_completed_chunks*100/f_size_chunks
		f_priority = f[3]
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
		li.setInfo('video',{'title':li_name,'size':f_size_bytes})
		if not xbmcplugin.addDirectoryItem(int(sys.argv[1]), \
			sys.argv[0]+"?mode=play&arg1="+str(i)+"&hash="+hash, \
			li,totalItems=numfiles): break
		i=i+1
	xbmcplugin.addSortMethod(int(sys.argv[1]), sortMethod=xbmcplugin.SORT_METHOD_TITLE )
	xbmcplugin.addSortMethod(int(sys.argv[1]), sortMethod=xbmcplugin.SORT_METHOD_SIZE )
	xbmcplugin.endOfDirectory(int(sys.argv[1]), cacheToDisc=False)