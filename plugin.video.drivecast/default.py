'''
	DriveCast plugin for XBMC
	Copyright (C) 2011 Francesco Alisetta

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
'''

# -*- coding: utf-8 -*-

import sys, xbmc, xbmcaddon, xbmcplugin, xbmcgui, urllib, urllib2, unicodedata, httplib, threading
from simplejson import load, loads
from base64 import b64encode, b64decode
from xml.dom.minidom import parseString

# plugin constants
__url__ = 'https://drivecast.eu/'
__api_version__ = "api/2.0/"
__api_key__ = "QXz8eEdSeKDoBvg4CzX4gU3n6MnliMZ9"
__device__ = "&name=XBMC&dev_type=boxee"
__settings__ = xbmcaddon.Addon(id='plugin.video.drivecast')
__language__ = __settings__.getLocalizedString
__thumbnails__ = __settings__.getAddonInfo('path')+"/thumbnails/"
__rss__= __settings__.getSetting("rss")

#========================================================================================
#	LOG MENU																	<<<OK>>>>
#========================================================================================
def log_menu():
	trying= xbmcgui.ListItem(__language__(30011),iconImage=__thumbnails__+"guest.png", thumbnailImage=__thumbnails__+"guest.png")
	xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=sys.argv[0]+"?guest",listitem=trying, isFolder=True)
	log_form= xbmcgui.ListItem(__language__(30013),iconImage=__thumbnails__+"user.png", thumbnailImage=__thumbnails__+"user.png")
	xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=sys.argv[0]+"?form",listitem=log_form,isFolder=True)
	qr= qrcode_post()
	qr_menu= xbmcgui.ListItem(__language__(30010), iconImage=qr, thumbnailImage=qr)
	xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=sys.argv[0]+"?qrcode",listitem=qr_menu, isFolder=True)
	xbmcplugin.endOfDirectory(int(sys.argv[1]))

#========================================================================================
#	QRCODE																		<<<OK>>>>
#========================================================================================
def qrcode_post():
	conn = httplib.HTTPSConnection("drivecast.eu:443")
	conn.request("POST", "/"+__api_version__+"pair/AppleTV/AppleTV")
	response = conn.getresponse()
	data= loads(response.read())
	conn.close()
	__settings__.setSetting("qr",str(data["paircode"]))
	return str(data["QRcode"])+".png"

def qrcode_click():
	qr= __settings__.getSetting("qr")
	try:
		get= read_resource("","pair/AppleTV/AppleTV/AppleTV/"+qr)
		up= str(get["Authorization"])
		us = b64decode(up).split(":")[0]
		__settings__.setSetting("login_name",us)
		log(str(get["Authorization"]))
	except:
		xbmc.executebuiltin("Notification("+__language__(30006)+","+__language__(30012)+")")

#========================================================================================
#	LOG FUNCTION																<<<OK>>>>
#========================================================================================
def login_form():
	__settings__.openSettings()
	username = __settings__.getSetting("login_name")	#USERNAME
	password = __settings__.getSetting("login_pass")	#PASSWORD
	aut = b64encode(username+':'+password)	#AUTENTICAZIONE IN BASE64
	try:
		log(aut)
	except:
		xbmc.executebuiltin("Notification("+__language__(30006)+","+__language__(30007)+")")
		xbmc.executebuiltin("Container.Refresh")

def log(up):
	rssURL= read_resource(up, "feed")
	__settings__.setSetting("up",up)
	__settings__.setSetting("rss", str(rssURL["feedURL"]))
	xbmc.executebuiltin("Notification("+__language__(30005)+","+__language__(30007)+")")
	xbmc.executebuiltin("Container.Refresh")

def logout():
	__settings__.setSetting("login_name",'')	#USERNAME
	__settings__.setSetting("login_pass",'')	#PASSWORD
	__settings__.setSetting("rss",'')			#RSS
	__settings__.setSetting("up","")			#USER:PASS
	xbmc.executebuiltin("Container.Update("+sys.argv[0]+")")

#========================================================================================
#	ELENCO PLAYLISTS															<<<OK>>>>
#========================================================================================
def playlists():
	playl= read_resource(__settings__.getSetting("up"), "playlist/XBMC?type=device")
	fu= xbmcgui.ListItem(label="Library", thumbnailImage=__thumbnails__+"library.png", path=sys.argv[0]+"??")
	xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=sys.argv[0]+"??", listitem=fu, isFolder=True)
	for pl in playl["elements"]:
		u=sys.argv[0]+"??"+pl["name"]
		item= xbmcgui.ListItem(label=pl["name"], thumbnailImage=__thumbnails__+"playlist.png", path=u)
		xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=item, isFolder=True)
	lo= xbmcgui.ListItem(label="Logout...", thumbnailImage=__thumbnails__+"user.png", path=sys.argv[0]+"?logout")
	xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=sys.argv[0]+"?logout", listitem=lo, isFolder=True)
	xbmcplugin.endOfDirectory(int(sys.argv[1]))

#========================================================================================
#	ELENCO ITEMS																<<<OK>>>>
#========================================================================================
def manage_RSS(playlist):
	feed= read_RSS()
	empty= True
	for item in feed.getElementsByTagName('item'):
		playl=item.getElementsByTagName('carcast:playlists_string')
		if playl:
			pl= playl[0].firstChild.data.encode('utf-8')
		else:
			pl= ""
		if(pl==playlist or pl.endswith(","+playlist) or pl.startswith(playlist+",") or pl.find(","+playlist+",")!=-1 or playlist==""):
			item_url = item.getElementsByTagName('guid')[0].firstChild.data.encode('utf-8')					#path
			item_title = item.getElementsByTagName("title")[0].firstChild.data.encode('utf-8')				#label
			item_author = item.getElementsByTagName("author")[0].firstChild.data.encode('utf-8')			#label2
			item_thumb = item.getElementsByTagName("carcast:thumbnail")[0].firstChild.data.encode('utf-8')	#thumbnailimage
			item_type = item.getElementsByTagName("carcast:element_type")[0].firstChild.data.encode('utf-8')
			elem= xbmcgui.ListItem(label=item_title, label2=item_author, thumbnailImage=item_thumb, path=item_url)
			if item_type==("video"):
				elem.setInfo(type="Video", infoLabels={"Title": item_title})
			elif item_type==("audio"):
				elem.setInfo(type="Music", infoLabels={"Title": item_title})
			else:
				elem.setInfo(type="Music", infoLabels={"Title": item_title})
			xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=item_url, listitem=elem, isFolder=False)
			empty= False
	if empty:
		xbmc.executebuiltin("Notification("+__language__(30008)+","+__language__(30009)+")")
	else:
		xbmcplugin.endOfDirectory(int(sys.argv[1]))

#========================================================================================
#	GUEST USER																	<<<OK>>>>
#========================================================================================
def guest():
	params= urllib.urlencode({'username': 'guest', 'type': 'drivecast', 'useragent': 'Boxee', 'device_type' : 'boxee', 'device_name' : 'boxee'})
	header= {"Content-type": "application/x-www-form-urlencoded"}
	conn = httplib.HTTPConnection("widgets.inrete.it:80")
	conn.request("POST", "/widget-boxee.php", params, header)
	response = conn.getresponse()
	res= response.read()
	data= parseString(res.split("?>")[1])
	conn.close()
	for item in data.getElementsByTagName('item'):
		playl=item.getElementsByTagName('carcast:playlists_string')
		item_url = item.getElementsByTagName('url')[0].firstChild.data.encode('utf-8')
		item_title = item.getElementsByTagName("title")[0].firstChild.data.encode('utf-8')
		item_author = item.getElementsByTagName("author")[0].firstChild.data.encode('utf-8')
		item_thumb = item.getElementsByTagName("thumbnail")[0].firstChild.data.encode('utf-8')
		item_type = item.getElementsByTagName("type")[0].firstChild.data.encode('utf-8')
		elem= xbmcgui.ListItem(label=item_title, label2=item_author, thumbnailImage=item_thumb, path=item_url)
		if item_type==("video"):
			elem.setInfo(type="Video", infoLabels={"Title": item_title})
		elif item_type==("audio"):
			elem.setInfo(type="Music", infoLabels={"Title": item_title})
		else:
			elem.setInfo(type="Music", infoLabels={"Title": item_title})
		xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=item_url, listitem=elem)
	xbmcplugin.endOfDirectory(int(sys.argv[1]))

#========================================================================================
#	API																			<<<OK>>>>
#========================================================================================
def read_resource(aut, resource):
	try:
		request = urllib2.Request(__url__+""+__api_version__+""+resource)
		opener = urllib2.build_opener()
		request.add_header('User-Agent','DriveCast apikey='+__api_key__)					# aggiungo apikey all'header
		if aut != "":
			request.add_header('Authorization','Basic '+aut)									# aggiungo dati login utente all'header
		src = load(opener.open(request))
		if (src['statusdesc']=='OK' and src['statuscode']=='200'):						# 'OK' se la richiesta è andata a buon fine
			return src
	except urllib2.HTTPError, e:
		print " ---API HTTP ERROR--- : " + str(e.code)
		raise
	except urllib2.URLError, e:
		print " ---API URL ERROR--- : " + str(e.reason)
		raise

def read_RSS():
	try:
		request = urllib2.Request(__rss__+""+__device__)#__settings__.GetSetting("rss")+""+__device__)
		opener = urllib2.urlopen(request).read()
		return parseString(opener)
	except urllib2.HTTPError, e:
		print " ---RSS HTTP ERROR--- : " + str(e.code)
	except urllib2.URLError, e:
		print " ---RSS URL ERROR--- : " + str(e.reason)

#========================================================================================
#	MAIN																		<<<OK>>>>
#========================================================================================
mode= sys.argv[2][1:]

if __rss__ == "":
	if  mode=="":
		log_menu()
	elif mode=="guest":
		guest()
	elif mode=="form":
		login_form()
	elif mode=="qrcode":
		qrcode_click()
else:
	if mode == "logout":
		logout()
	elif mode == "":
		playlists()
	else:
		manage_RSS(mode[1:])
