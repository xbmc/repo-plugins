#!/usr/bin/env python

import urllib, urllib2, re, xbmcplugin, xbmcgui, xbmc
from datetime import datetime, timedelta
from scraper import showtree, tabs, get_episodes, get_stream_info, get_latest_episodes

user_agent = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3'
action_key = None
action_value = None
name = None


def forsida():
	for tab in tabs:
		title, url = tab
		addDir(title.encode('utf-8'), 'nytt', url)
	for i,stod in enumerate(showtree[:-1]):
		title = u'%s \xfe\xe6ttir' % stod['name']
		addDir(title.encode('utf-8'), 'stod', i)
#	addDir(u'V\xf6ktun K\xf6tlu'.encode('utf-8'), 'eldfjall', 'katla')
	addDir(u'Bein \xfatsending R\xdaV'.encode('utf-8'), 'spila', 'http://www.ruv.is/ruv')

def nytt(flokkur):
	pageurl = u'http://www.ruv.is%s' % flokkur
	for name, url in get_latest_episodes(pageurl.encode('utf-8')):
		addDir(name.encode('utf-8'), 'spila', url.encode('utf-8'))
                       
def flokkar(stod):
        for i, flokkur in enumerate(showtree[stod]['categories']):
                addDir(flokkur['name'].encode('utf-8'), 'flokkur', "%d;%d" % (stod,i))

def thaettir(stod, flokkur):
	for show in showtree[stod]['categories'][flokkur][u'shows']:
		name, url = show
		if url[0] == '/':
			url = 'http://dagskra.ruv.is%s' % url
		addDir(name.encode('utf-8'), 'thattur', url.encode('utf-8'))

def upptokur(url):
	episodes = get_episodes(url)
	if not episodes:
		w = xbmcgui.Dialog()
		w.ok(u"Engar uppt\xf6kur".encode('utf-8'),
                     u"Engar uppt\xf6kur eru \xed bo\xf0i fyrir \xfeennan \xfe\xe1tt.".encode('utf-8'))
	else:
		for episode in episodes:
			name, url = episode
			addDir(name.encode('utf-8'), 'spila', url, "DefaultVideo.png") 

def spila(url):
	stream_info = get_stream_info(url)
#rtmpdump -r rtmp://178.19.48.74/ruvvod?key=93292 -a vod -y mp4:ruvvod/4621116.f4v -o dagur.f4v
	#playpath = "mp4:ruvvod/4621116.f4v"
	#rtmp_url = "rtmp://178.19.48.74/ruvvod?key=93292"
	item = xbmcgui.ListItem("RTL")
	item.setProperty("PlayPath", stream_info['playpath'])
	item.setProperty("SWFPlayer", "http://www.ruv.is/files/spilari/player.swf")
	item.setProperty("PageURL", url)
	xbmc.Player(xbmc.PLAYER_CORE_DVDPLAYER).play(stream_info['rtmp_url'], item)

def eldfjall(nafn):
	url = "http://www.ruv.is/%s/" % nafn
	item = xbmcgui.ListItem("RTL")
        #item.setProperty("PlayPath", "rtsp://10.31.98.2:554/axis-media/media.amp?videocodec=h264&resolution=4CIF&compression=25&textstring=R%DAV%20-%20KATLA%20S%C9%D0%20FR%C1%20H%C1FELLI&textposition=bottom&text=1&clock=1&date=1&overlayimage=0&fps=15&audio=0&videokeyframeinterval=30&videobitrate=250&videobitratepriority=framerate&squarepixel=0&videocodec=h264&rotation=0")
        item.setProperty("SWFPlayer", "http://uppfaersla.ruv.is/files/spilari/player.swf")
        item.setProperty("PageURL", url)
        #xbmc.Player(xbmc.PLAYER_CORE_DVDPLAYER).play("rtmp://vefur-vod.ruv.is/katla", item)
        xbmc.Player(xbmc.PLAYER_CORE_DVDPLAYER).play("rtsp://10.31.98.2:554/axis-media/media.amp?videocodec=h264&resolution=4CIF&compression=25&textstring=R%DAV%20-%20KATLA%20S%C9%D0%20FR%C1%20H%C1FELLI&textposition=bottom&text=1&clock=1&date=1&overlayimage=0&fps=15&audio=0&videokeyframeinterval=30&videobitrate=250&videobitratepriority=framerate&squarepixel=0&videocodec=h264&rotation=0", item)

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

def addDir(name, action_key, action_value, iconimage='DefaultFolder.png'):
	is_folder = True
	if action_key == 'spila':
		is_folder = False
        u=sys.argv[0]+"?action_key="+urllib.quote_plus(action_key)+"&action_value="+str(action_value)+"&name="+urllib.quote_plus(name)
        liz=xbmcgui.ListItem(name, iconImage=iconimage, thumbnailImage='')
        liz.setInfo(type="Video", infoLabels={ "Title": name } )
        return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=is_folder)
        
              
params=get_params()
try:
        action_key = urllib.unquote_plus(params["action_key"])
        action_value = urllib.unquote_plus(params["action_value"])
        name = urllib.unquote_plus(params["name"])
except:
        pass

print action_key
print action_value
if action_key is None:
	forsida()
elif action_key == 'stod':
        flokkar(int(action_value))
elif action_key == 'flokkur':
	stod, flokkur = action_value.split(';')
        thaettir(int(stod), int(flokkur))
elif action_key == 'thattur':
	upptokur(action_value)
elif action_key == 'spila':
	spila(action_value)
elif action_key == 'nytt':
	nytt(action_value)
elif action_key == 'eldfjall':
	eldfjall(action_value)
        
xbmcplugin.endOfDirectory(int(sys.argv[1]))

