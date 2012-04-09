# File: tvvn.py
# By:   Binh Nguyen <binh@vnoss.org>
# Date: 25-03-2012
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os, re, sys, urllib, urllib2, xbmcaddon, xbmcplugin, xbmcgui
from string import split, replace, find
from xml.dom.minidom import parseString
import xml.sax.saxutils as saxutils

addon = xbmcaddon.Addon('plugin.video.tvvn')
profile = xbmc.translatePath(addon.getAddonInfo('profile'))
__settings__ = xbmcaddon.Addon(id='plugin.video.tvvn')
home = __settings__.getAddonInfo('path')
fanart = xbmc.translatePath( os.path.join( home, 'fanart.jpg' ) )

# CONFIGURATION
# See here for more IP's http://www.vtc.com.vn/XMLStart.aspx
VTCURLList=[    'rtmp://66.160.142.201/live',
		'rtmp://66.160.142.198/live',
		'rtmp://66.160.142.197/live']
from random import choice
VTCURL=choice(VTCURLList)

# provider_name = [stream url, swf player url, referrer url]
provider_vtc = [VTCURL,'http://vtc.com.vn/player.swf','http://vtc.com.vn/#']
#provider_tv24 = ['rtmp://112.197.2.11:1935/live','http://tv24.vn/WebMedia/mediaplayer/vplayer.swf','http://www.tv24.vn']
provider_tv24 = ['rtmp://112.197.2.11/live','http://tv24.vn/WebMedia/mediaplayer/vplayer.swf','http://www.tv24.vn']

mode=None

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

try:
        stream_name=urllib.unquote_plus(params["stream_name"])
except:
        pass
try:
        ref=urllib.unquote_plus(params["ref"])
except:
        pass
try:
        provider=urllib.unquote_plus(params["provider"])
except:
        pass
try:
        mode=int(params["mode"])
except:
        pass

def addLink(name,provider,stream_name,ref,iconimage):
	ok = True
	give_url = sys.argv[0]+"?mode=1&stream_name="+stream_name+"&ref="+ref+"&provider="+provider
	liz = xbmcgui.ListItem( name, iconImage=xbmc.translatePath(os.path.join(home, iconimage)), thumbnailImage=xbmc.translatePath(os.path.join(home, iconimage)))
	liz.setInfo(type="Video", infoLabels={"Title": name})
	liz.setProperty("Fanart_Image",fanart)
	ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=give_url,listitem=liz)

def addDirectoryLink(name, lmode, iconimage):
	#li = xbmcgui.ListItem(name)
	li = xbmcgui.ListItem( name, iconImage=xbmc.translatePath(os.path.join(home, iconimage)), thumbnailImage=xbmc.translatePath(os.path.join(home, iconimage)))
	li.setInfo(type="Video", infoLabels={"Title": name})
	li.setProperty("Fanart_Image",fanart)
	url = sys.argv[0]+'?mode='+lmode
	return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=li, isFolder=True)

def show_menu_sctv ():
	addLink('SCTV1', 'provider_tv24',  'sctv1.stream',  '',   'sctv.png')
	addLink('SCTV2', 'provider_tv24',  'sctv2.stream',  '',   'sctv.png')
	addLink('SCTV3', 'provider_tv24',  'sctv3.stream',  '',   'sctv.png')
	addLink('SCTV4', 'provider_tv24',  'sctv4.stream',  '',   'sctv.png')
	addLink('SCTV5', 'provider_tv24',  'sctv5.stream',  '',   'sctv.png')
	addLink('SCTV6', 'provider_tv24',  'sctv6.stream',  '',   'sctv.png')
	addLink('SCTV7', 'provider_tv24',  'sctv7.stream',  '',   'sctv.png')
	addLink('SCTV8', 'provider_tv24',  'sctv8.stream',  '',   'sctv.png')
	addLink('SCTV9', 'provider_tv24',  'sctv9.stream',  '',   'sctv.png')
	addLink('SCTV10', 'provider_tv24',  'sctv10.stream',  '',   'sctv.png')
	addLink('SCTV11', 'provider_tv24',  'sctv11.stream',  '',   'sctv.png')
	addLink('SCTV12', 'provider_tv24',  'sctv12.stream',  '',   'sctv.png')
	addLink('SCTV13', 'provider_tv24',  'sctv13.stream',  '',   'sctv.png')
	addLink('SCTV14', 'provider_tv24',  'sctv14.stream',  '',   'sctv.png')
	addLink('SCTV15', 'provider_tv24',  'sctv15.stream',  '',   'sctv.png')
	addLink('SCTV16', 'provider_tv24',  'sctv16.stream',  '',   'sctv.png')
	addLink('SCTV17', 'provider_tv24',  'sctv17.stream',  '',   'sctv.png')
	addLink('SCTVHD', 'provider_tv24',  'sctv18.stream',  '',   'sctv.png')
	xbmcplugin.endOfDirectory(int(sys.argv[1]))

def show_menu_vov ():
	addLink('VOV 1', 'provider_vtc',  'vov1',   'VOV1/29',  'vov1.png')
	addLink('VOV 2', 'provider_vtc',  'vov2',   'VOV2/28',  'vov2.png')
	addLink('VOV 3', 'provider_vtc',  'vov3',   'VOV3/27',  'vov3.png')
	addLink('VOV 5', 'provider_vtc',  'vov5',   'VOV5/25',  'vov5.png')
	xbmcplugin.endOfDirectory(int(sys.argv[1]))

def Init():
	addLink('VTV 1', 'provider_vtc',  'vtv11',  'VTV1/15',  'vtv1.png')
	addLink('VTV 2', 'provider_vtc',  'vtv2',   'VTV2/23',  'vtv2.png')
	addLink('VTV 3', 'provider_vtc',  'vtv31',  'VTV3/3',   'vtv3.png')
	addLink('VTV 4', 'provider_vtc',  'vtv4',   'VTV4/2',   'vtv4.png')
	addLink('VTV 6', 'provider_tv24',  'vtv6.stream',   '',   'vtv6.png')
	addLink('VTV 9', 'provider_tv24',  'vtv9.stream',   '',   'vtv9.png')

	addLink('HTV 7', 'provider_tv24',  'htv7.stream',   '',  'htv7.png')
	addLink('HTV 9', 'provider_tv24',  'htv9.stream',  '',   'htv9.png')

	addLink('VTC 1', 'provider_vtc',  'vtc11',  'VTC1/10',  'vtc1.png')
	addLink('VTC 2', 'provider_vtc',  'vtc21',  'VTC2/11',  'vtc2.png')
	addLink('VTC 10', 'provider_vtc', 'vtc101', 'VTC10/22', 'vtc10.png')

	addDirectoryLink('SCTV Channels', '10', 'sctv.png')
	addDirectoryLink('VOV Stations', '11', 'vov.png')

	xbmcplugin.endOfDirectory(int(sys.argv[1]))

def play_video(provider, stream_name, ref):
	xbmc.executebuiltin( "ActivateWindow(busydialog)" )
	prov=globals()[provider]

	item = xbmcgui.ListItem("TVVN")
	item.setProperty("SWFPlayer", prov[1])
	item.setProperty("IsLive", "true")
	item.setProperty("PageURL", prov[2]+"/"+ref)
	xbmc.executebuiltin( "Dialog.Close(busydialog)" )
	xbmc.Player(xbmc.PLAYER_CORE_DVDPLAYER).play(prov[0]+"/"+stream_name, item)

if mode==None:
	Init()
elif mode==1:
	play_video(provider, stream_name, ref)
elif mode==10:
	show_menu_sctv()
elif mode==11:
	show_menu_vov()
