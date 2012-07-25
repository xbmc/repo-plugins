# -*- coding: UTF-8 -*-
#---------------------------------------------------------------------
# File: tvvn.py
# By:   Binh Nguyen <binh@vnoss.org>
# Date: 25-07-2012
#---------------------------------------------------------------------
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
#---------------------------------------------------------------------

import os, re, sys, urllib, urllib2, xbmcaddon, xbmcplugin, xbmcgui
from random import choice

addon = xbmcaddon.Addon('plugin.video.tvvn')
profile = xbmc.translatePath(addon.getAddonInfo('profile'))
mysettings = xbmcaddon.Addon(id='plugin.video.tvvn')
home = mysettings.getAddonInfo('path')
fanart = xbmc.translatePath(os.path.join(home, 'fanart.jpg'))

#---------------------------------------------------------------------
# CONFIGURATION STARTS
#---------------------------------------------------------------------
# src_name = [stream url, swf player url, referrer url, app name]

# vtc.com.vn
# See here for more IP's http://www.vtc.com.vn/XMLStart.aspx
VTCURLList = 	['rtmp://66.160.142.201/live',
				 'rtmp://66.160.142.198/live',
				 'rtmp://66.160.142.197/live']
VTCURL = choice(VTCURLList)
src_vtc =   	[VTCURL,
				 'http://vtc.com.vn/player.swf',
				 'http://vtc.com.vn/#',
				 '']

# tv24.vn
TV24URLList = 	['rtmp://112.197.2.16:1935/live',
			     'rtmp://112.197.2.11:1935/live']
TV24URL = choice(TV24URLList)
src_tv24 =  	[TV24URL,
				 'http://tv24.vn/jwplayer/player.swf',
				 'http://www.tv24.vn',
				 '']

# xunghe.vn
src_trt  =  	['rtmp://118.69.176.149/live',
				 'http://tv.xunghe.vn/player.swf',
				 'http://tv.xunghe.vn/?tab=Truyen-Hinh&xem=trt1-hue',
				 '']

# vietfacetv.com
VFTVURLList = 	['rtmp://119.18.184.129:1935/streams',
				 'rtmp://64.71.151.49/streams']
VFTVURL = choice(VFTVURLList)
src_vietface = 	[VFTVURL,
				 'http://vietpho.com/ext/js/playerPro.swf',
			 	 'http://vietpho.com/online-channels.php?id=42&gID=0&page=1',
				 '']

# van tv
src_vantv = 	['rtmp://flash67.ustream.tv:1935/ustreamVideo/3097098',
			 	 'http://static-cdn1.ustream.tv/swf/live/viewer.rsl:194.swf',
			 	 'http://www.552vantv.com',
				 '']

src_lsgtv = 	['rtmp://stream.s15.cpanelservices.com/lstvlive',
		  		 'http://vietpho.com/ext/js/5.1/player-licensed.swf',
			 	 'http://vietpho.com/online-channels.php?id=2&gID=0&page=1',
				 'lstvlive']

src_sgtv = 		['rtmp://74.63.219.101:1935/sgtv',
				 'http://vietpho.com/ext/js/3/mediaplayer.swf',
				 'http://vietpho.com/online-channels.php?id=41&gID=0&page=1',
				 'sgtv']

src_globaltv = 	['rtmp://unirtmp.tulix.tv:1935/globaltv',
				 'http://vietpho.com/ext/js/3/mediaplayer.swf',
				 'http://vietpho.com/online-channels.php?id=5&gID=0&page=1',
				 'globaltv']

src_vbstv = 	['rtmp://74.63.219.101:1935/vbstele',
				 'http://vietpho.com/ext/js/3/mediaplayer.swf',
				 'http://vietpho.com/online-channels.php?id=6&gID=0&page=1',
				 'vbstele']

#---------------------------------------------------------------------
# CONFIGURATION ENDS
#---------------------------------------------------------------------

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
	stream_short_name=urllib.unquote_plus(params["stream_short_name"])
except:
	pass
try:
	stream_name=urllib.unquote_plus(params["stream_name"])
except:
	pass
try:
	ref=urllib.unquote_plus(params["ref"])
except:
	pass
try:
	src=urllib.unquote_plus(params["src"])
except:
	pass
try:
	mode=int(params["mode"])
except:
	pass

def add_link(name,src,stream_name,ref,iconimage,desc):
	ok = True
	short_name=name
	if (mysettings.getSetting('descriptions')=='true' and desc != ''):
		if mysettings.getSetting('descriptions_on_right') == 'false':
			name = desc+"    "+name
		else:
			name = name+"    "+desc
	give_url = sys.argv[0]+"?mode=1&stream_name="+stream_name+"&ref="+ref+"&src="+src+"&stream_short_name="+short_name
	liz = xbmcgui.ListItem( name, iconImage=xbmc.translatePath(os.path.join(home, 'resources', 'logos', iconimage)), thumbnailImage=xbmc.translatePath(os.path.join(home, 'resources', 'logos', iconimage)))
	liz.setInfo(type="Video", infoLabels={"Title": name})
	liz.setProperty("Fanart_Image",fanart)
	ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=give_url,listitem=liz)

def add_directory_link(name, lmode, iconimage,desc):
	name = "["+name+"]"
	if (mysettings.getSetting('descriptions')=='true' and desc != ''):
		if mysettings.getSetting('descriptions_on_right') == 'false':
			name = desc+"    "+name
		else:
			name = name+"    "+desc
	li = xbmcgui.ListItem( name, iconImage=xbmc.translatePath(os.path.join(home, 'resources', 'logos', iconimage)), thumbnailImage=xbmc.translatePath(os.path.join(home, 'resources', 'logos', iconimage)))
	li.setInfo(type="Video", infoLabels={"Title": name})
	li.setProperty("Fanart_Image",fanart)
	url = sys.argv[0]+'?mode='+lmode
	return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=li, isFolder=True)

def show_menu_sctv():
	add_link('SCTV1', 'src_tv24',  'SDsctv1.stream',  '',   'sctv.png', 'Hài')
	add_link('SCTV2', 'src_tv24',  'SDsctv2.stream',  '',   'sctv.png', 'Yan TV: Âm nhạc quốc tế')
	add_link('SCTV3', 'src_tv24',  'SDsctv3.stream',  '',   'sctv.png', 'Sao TV: Thiếu nhi')
	add_link('SCTV4', 'src_tv24',  'SDsctv4.stream',  '',   'sctv.png', 'Giải trí tổng hợp')
	add_link('SCTV5', 'src_tv24',  'SDsctv5.stream',  '',   'sctv.png', 'Shopping TV: Mua sắm SCJ ')
	add_link('SCTV6', 'src_tv24',  'SDsctv6.stream',  '',   'sctv.png', 'Sóng nhạc')
	add_link('SCTV7', 'src_tv24',  'SDsctv7.stream',  '',   'sctv.png', 'Sân khấu, Văn nghệ tổng hợp')
	add_link('SCTV8', 'src_tv24',  'SDsctv8.stream',  '',   'sctv.png', 'Thông tin Kinh tế, Thị trường')
	add_link('SCTV9', 'src_tv24',  'SDsctv9.stream',  '',   'sctv.png', 'Phim châu Á')
	add_link('SCTV10', 'src_tv24',  'SDsctv10.stream',  '',   'sctv.png', 'Home Shopping Network: Mua sắm')
	add_link('SCTV11', 'src_tv24',  'SDsctv11.stream',  '',   'sctv.png', 'Hát trên truyền hình')
	add_link('SCTV12', 'src_tv24',  'SDsctv12.stream',  '',   'sctv.png', 'Du lịch, Khám phá')
	add_link('SCTV13', 'src_tv24',  'SDsctv13.stream',  '',   'sctv.png', 'Phụ nữ và Gia đình')
	add_link('SCTV14', 'src_tv24',  'SDsctv14.stream',  '',   'sctv.png', 'Phim Việt')
	add_link('SCTV15', 'src_tv24',  'SDsctv15.stream',  '',   'sctv.png', 'Thể thao')
	add_link('SCTV16', 'src_tv24',  'SDsctv16.stream',  '',   'sctv.png', 'Phim truyện nước ngoài')
	add_link('SCTV17', 'src_tv24',  'SDsctv17.stream',  '',   'sctv.png', 'Phim tổng hợp')
	add_link('SCTVHD', 'src_tv24',  'SDsctv18.stream',  '',   'sctv.png', 'Thể thao')
	xbmcplugin.endOfDirectory(int(sys.argv[1]))

def show_menu_local():
	add_link('HN1', 'src_tv24',  'hn1.stream',  '',   'default.png', 'Hà Nội 1')
	add_link('TRT1', 'src_trt',  'trt',  '',   'default.png', 'Thừa Thiên Huế')
	add_link('LA34', 'src_tv24',  'la34.stream',  '',   'default.png', 'Long An')
	add_link('THVL1', 'src_tv24',  'thvl1.stream',  '',   'default.png', 'Vĩnh Long')
	add_link('ĐN1', 'src_tv24',  'dn1.stream',  '',   'default.png', 'Đồng Nai 1')
	add_link('HGV', 'src_tv24',  'thhg.stream',  '',   'default.png', 'Hậu Giang')
	add_link('STV', 'src_tv24',  'thst.stream',  '',   'default.png', 'Sóc Trăng')
	add_link('THTG', 'src_tv24',  'thtg.stream',  '',   'default.png', 'Tiền Giang')
	add_link('QRT', 'src_tv24',  'qrt.stream',  '',   'default.png', 'Quảng Nam')
	add_link('BTV', 'src_tv24',  'bthtv.stream',  '',   'default.png', 'Bình Thuận')
	add_link('THĐT', 'src_tv24',  'thdt.stream',  '',   'default.png', 'Đồng Tháp')
	xbmcplugin.endOfDirectory(int(sys.argv[1]))
 
def show_menu_overseas():
	add_link('Vietface', 'src_vietface',  'urlparams_qm_channel:1005_qm_token:6436488',   '',  'vietfacetv.png', 'Vietface Media Group')
	add_link('SaigonTV', 'src_sgtv',  'myStream.sdp',   '',  'saigontv.png', 'Saigon TV')
	add_link('GlobalTV', 'src_globaltv',  'myStream.sdp',   '',  'globaltv.png', 'Global Television')
	add_link('VAN-TV', 'src_vantv',  'streams/live_1',   '',  'vantv.png', 'Vietnamese American Network TV')
	add_link('VBSTV', 'src_vbstv',  'myStream.sdp',   '',  'vbstv.png', 'Vietnamese Broadcasting Services')
	add_link('LSTV', 'src_lsgtv',  'livestream',   '',  'lsaigontv.png', 'Little Saigon TV')
	xbmcplugin.endOfDirectory(int(sys.argv[1]))
 
def show_menu_vov():
	add_link('VOV1', 'src_vtc',  'vov1',   'VOV1/29',  'vov1.png', 'Thời sự, Chính trị, Tổng hợp')
	add_link('VOV2', 'src_vtc',  'vov2',   'VOV2/28',  'vov2.png', 'Văn hóa, Đời sống, Khoa giáo')
	add_link('VOV3', 'src_vtc',  'vov3',   'VOV3/27',  'vov3.png', 'Âm nhạc, Giải trí')
	add_link('VOV5', 'src_vtc',  'vov5',   'VOV5/25',  'vov5.png', 'Phát thanh đối ngoại')
	xbmcplugin.endOfDirectory(int(sys.argv[1]))

def Init():
	#add_link('VTV1', 'src_vtc',  'vtv11',  'VTV1/15',  'vtv1.png', 'Thông tin tổng hợp')
	#add_link('VTV2', 'src_vtc',  'vtv2',   'VTV2/23',  'vtv2.png', 'Khoa học & Giáo dục')
	#add_link('VTV3', 'src_vtc',  'vtv31',  'VTV3/3',   'vtv3.png', 'Thể thao, Giải trí & Thông tin kinh tế')
	#add_link('VTV4', 'src_vtc',  'vtv4',   'VTV4/2',   'vtv4.png', 'Kênh cho người Việt Nam ở nước ngoài')
	#add_link('HTV7', 'src_vtc',  'htv7',   '',  'htv7.png', 'Thông tin - Giải trí - Thể thao')
	#add_link('HTV9', 'src_vtc',  'htv91',  '',   'htv9.png', 'Chính trị - Xã hội - Văn hóa')
	add_link('VTV1', 'src_tv24',  'vtv1.stream',  '',  'vtv1.png', 'Thông tin tổng hợp')
	add_link('VTV2', 'src_tv24',  'vtv2.stream',  '',  'vtv2.png', 'Khoa học, Giáo dục')
	add_link('VTV3', 'src_tv24',  'vtv3.stream',  '',  'vtv3.png', 'Thể thao, Giải trí, Thông tin Kinh tế')
	add_link('VTV4', 'src_tv24',  'vtv4.stream',  '',  'vtv4.png', 'Kênh cho người Việt Nam ở nước ngoài')
	add_link('VTV6', 'src_tv24',  'vtv6.stream',  '',  'vtv6.png', 'Kênh cho Thanh, thiếu niên')
	add_link('VTV9', 'src_tv24',  'vtv9.stream',  '',  'vtv9.png', 'Kênh cho Khán giả miền Nam')
	add_link('ANTV', 'src_tv24',  'antv.stream',  '',  'antv.png', 'An ninh TV')
	add_link('HTV7', 'src_tv24',  'htv7.stream',  '',  'htv7.png', 'Thông tin, Giải trí, Thể thao')
	add_link('HTV9', 'src_tv24',  'htv9.stream',  '',  'htv9.png', 'Chính trị, Xã hội, Văn hóa')
	add_link('VTC1', 'src_vtc',  'vtc11',  'VTC1/10',  'vtc1.png', 'Thời sự tổng hợp')
	add_link('VTC2', 'src_vtc',  'vtc21',  'VTC2/11',  'vtc2.png', 'Khoa học, Công nghệ')
	add_link('VTC10', 'src_vtc', 'vtc101', 'VTC10/22', 'vtc10.png', 'Kênh Văn hóa Việt')
	add_directory_link('SCTV Channels', '10', 'sctv.png', 'SCTV hợp tác và sản xuất')
	add_directory_link('VOV Radio', '11', 'vov.png', 'Đài Tiếng nói Việt Nam')
	add_directory_link('Local Stations', '12', 'default.png', 'Truyền hình Địa phương')
	add_directory_link('Oversea Stations', '13', 'default.png', 'Truyền hình Hải ngoại')

	xbmcplugin.endOfDirectory(int(sys.argv[1]))

def play_video(src, name, stream_name, ref):
	prov = globals()[src]
	item = xbmcgui.ListItem(name)

	stream_name=stream_name.replace('_qm_','?')

	if (ref != ''):
		pageUrl=prov[2]+"/"+ref
	else:
		pageUrl=prov[2]

	if (stream_name != ''):
		videoUrl=prov[0]+"/"+stream_name
	else:
		videoUrl=prov[0]
	swfUrl=prov[1]
	flashVer='LNX_11,2,202,233'

	fullURL=videoUrl+' swfVfy=1 live=1 playpath='+stream_name+' flashVer='+flashVer+' pageUrl='+pageUrl+' tcUrl='+videoUrl+' swfUrl='+swfUrl 
	if (prov[3] != ''):
		fullURL=fullURL+' app='+prov[3]
	if (src == "src_tv24" and mysettings.getSetting('tv24_http') == 'true'):
		fullURL=prov[0].replace("rtmp://","http://")+"/"+stream_name+"/playlist.m3u8"
	xbmc.Player(xbmc.PLAYER_CORE_DVDPLAYER).play(fullURL, item)

if mode==None:
	Init()
elif mode==1:
	play_video(src, stream_short_name, stream_name, ref)
elif mode==10:
	show_menu_sctv()
elif mode==11:
	show_menu_vov()
elif mode==12:
	show_menu_local()
elif mode==13:
	show_menu_overseas()
