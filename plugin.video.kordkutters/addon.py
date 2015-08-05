#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
 Author: enen92 

 This program is free software: you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation, either version 3 of the License, or
 (at your option) any later version.

 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with this program.  If not, see <http://www.gnu.org/licenses/>.
 
"""

import urllib,xbmcplugin
import os,sys
from resources.lib.common_variables import *
from resources.lib.directory import *
from resources.lib.youtubewrapper import *
from resources.lib.watched import * 

"""

Addon navigation is below
 
"""	
			
            
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
name=None
mode=None
iconimage=None
page = None
token = None

try: url=urllib.unquote_plus(params["url"])
except: pass
try: name=urllib.unquote_plus(params["name"])
except: pass
try: mode=int(params["mode"])
except:
	try: 
		mode=params["mode"]
	except: pass
try: iconimage=urllib.unquote_plus(params["iconimage"])
except: pass
try: token=urllib.unquote_plus(params["token"])
except: pass
try: page=int(params["page"])
except: page = 1

print ("Mode: "+str(mode))
print ("URL: "+str(url))
print ("Name: "+str(name))
print ("iconimage: "+str(iconimage))
print ("Page: "+str(page))
print ("Token: "+str(token))

if mode==None:
	if show_live_category:
		addDir('[B][I]'+translate(30001)+'[/B][/I]','',10,os.path.join(artfolder,'live.png'),1,1,'')
	if show_uploads_playlist:
		addDir('[B][I]'+translate(30004)+'[/B][/I]','',11,os.path.join(artfolder,'allvideos.png'),1,1,'')
	if show_channel_playlists:
		get_playlists()
	xbmcplugin.setContent(int(sys.argv[1]), 'files')
elif mode==1: return_youtubevideos(name,url,token,page)
elif mode==5: 
	play_youtube_video(url)
elif mode==6: mark_as_watched(url)
elif mode==7: removed_watched(url)
elif mode==8: add_to_bookmarks(url)
elif mode==9: remove_from_bookmarks(url)
elif mode==10: get_live_videos()
elif mode==11: get_all_youtube_uploads()
	
xbmcplugin.endOfDirectory(int(sys.argv[1]))
