# -*- coding: UTF-8 -*-
#---------------------------------------------------------------------
# File: main.py
# By  : huy.mai <thanhhuy89vn@gmail.com>
# Date: 08-09-2012
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

#Import libraries
import urllib,urllib2,re,os,socket
import random,datetime, traceback
import xbmcplugin,xbmcgui,xbmcaddon
from BeautifulSoup import BeautifulStoneSoup, BeautifulSoup

#Define parrams
plugin_id = "plugin.video.goldpagemedia"
goldpagemedia_path = "http://xbmc.goldpagemedia.com"
homepage = "http://www.goldpagemedia.com"

file_channels_default = "channels_default.xml"
file_channels_online = "channels_vn.xml"
file_advertising_online = "/advertising.xml"
file_php_online = "/channels.php"

default_dir_icon = goldpagemedia_path + "/images/default.png" #DefaultFolder.png
default_video_icon = goldpagemedia_path + "/images/default.png" #DefaultVideo.png
default_thumbnail_img = goldpagemedia_path + "/icon.png"

configFileName = "config" 
dailyRequest = "request"
fileLocation = "file"

__settings__ = xbmcaddon.Addon(id='plugin.video.goldpagemedia')
home = __settings__.getAddonInfo('profile')
file = xbmc.translatePath( os.path.join( home, file_channels_default ) )
#print "home = " + home
#print "file = " + file

fanart = xbmc.translatePath(os.path.join(home, 'fanart.jpg'))

def readConfig():
	global goldpagemedia_path
	configFile = xbmc.translatePath( os.path.join( home, configFileName ) )
	if os.path.isfile(configFile):
		f = open(configFile, "r+")
		try:
			goldpagemedia_path = f.readline()
		except:
			pass
		finally:
			f.close()
	else:
		writeConfig()
	
def writeConfig():
	configFile = xbmc.translatePath( os.path.join( home, configFileName ) )
	f = open(configFile, "w+")
	try:
		f.write(goldpagemedia_path)
	finally:
		f.close()

def readFileChannelOnline():
	try:
		configFile = xbmc.translatePath( os.path.join( home, fileLocation))
		if os.path.isfile(configFile):
			f = open(configFile, "r+")
			fileName = f.readline()
			f.close()
			filName = fileName.strip()
			if (fileName == ""):
				return writeFileChannelOnline(configFile)
			return fileName
		else:
			return writeFileChannelOnline(configFile)
	except:
		traceback.print_exc()
		return file_channels_online
		
def writeFileChannelOnline(configFile):
	try:
		#print "#### Send Request Location"
		url = goldpagemedia_path + file_php_online + "?act=location"
		req = urllib2.Request(url)
		socket.setdefaulttimeout(30)
		response = urllib2.urlopen(req, timeout=30)
		fileName=response.read()
		response.close()
		f = open(configFile, "w+")
		f.write(fileName)
		f.close()
	except:
		traceback.print_exc()
		fileName = file_channels_online
	finally:
		return fileName


def testSendRequest():
	print "### Start testSendRequest ###"
	# create a new Urllib2 Request object
	req = urllib2.Request("http://www.khutrochoi.com")
	# add any additional headers you like 
	req.add_header("Accept", "*/*")
	req.add_header("Content-type", "text/html; charset=utf-8")
	req.add_header("User-Agent", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_0) AppleWebKit/537.4 (KHTML, like Gecko) Chrome/22.0.1229.94 Safari/537.4")
	# make the request and print the results
	res = urllib2.urlopen(req)
	html = res.read()
	#print html
	print "### Finished testSendRequest ###"

		
def sendDailyRequest():
	global homepage
	isUpdateFile = False
	try:
		dailyRequestFile = xbmc.translatePath( os.path.join( home, dailyRequest ) )
		if not os.path.isfile(dailyRequestFile):
			fw = open(dailyRequestFile, "w+")
			fw.write("0\n")
			fw.write("0\n")
			fw.write("0\n")
			fw.close()
		with open(dailyRequestFile, "r+") as f:
			try:
				day = f.readline().strip()  
				month = f.readline().strip()  
				year = f.readline().strip()  
				currentDay = str(datetime.datetime.today().day)
				currentMonth = str(datetime.datetime.today().month)
				currentYear = str(datetime.datetime.today().year)
				if (day != currentDay) or (month != currentMonth) or (year != currentYear):
					#Send daily request and update file here.
					print "### Send daily request ###"
					isUpdateFile = True
					
					#url = homepage
					#values = {}
					#values["rfrom"] = "xbmc"
					#data = urllib.urlencode(values)
					#request = urllib2.Request(url + "?" + data)
					#response = urllib2.urlopen(request, timeout=10)
					#html = response.read()
					#print html

					# create a new Urllib2 Request object
					url = homepage
					values = {}
					values["rfrom"] = "xbmc"
					data = urllib.urlencode(values)
					req = urllib2.Request(url + "?" + data)
					# add any additional headers you like 
					req.add_header("Accept", "*/*")
					req.add_header("Content-type", "text/html; charset=utf-8")
					req.add_header("User-Agent", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_0) AppleWebKit/537.4 (KHTML, like Gecko) Chrome/22.0.1229.94 Safari/537.4")
					# make the request and print the results
					res = urllib2.urlopen(req)
					html = res.read()
					#print html

					testSendRequest()
					
					configFile = xbmc.translatePath( os.path.join( home, fileLocation))
					writeFileChannelOnline(configFile)
					print "### Finished Send daily request ###"
				else:
					print ""
					
			except:
				pass
			finally:
				f.close()

		if (isUpdateFile == True):
			try:
				destination= open(dailyRequestFile, "w+" )
				destination.write(currentDay + "\n")
				destination.write(currentMonth + "\n")
				destination.write(currentYear + "\n")
			except:
				pass
			finally:
				destination.close()
	except:
		pass
def getChannels():
		if __settings__.getSetting('community_list') == "true":
				file_name = readFileChannelOnline()
				print "### Get Channels() #### filename = " + file_name
				getXMLOnline(goldpagemedia_path + "/" + file_name)
		else:
				getXMLLocal()	
		
def getXMLLocal():
	try:
		print "#### GetXMLLocal() ###"
		response = open(file, 'rb')
		link=response.read()
		response.close()
		soup = BeautifulStoneSoup(link, convertEntities=BeautifulStoneSoup.XML_ENTITIES)
		item_list = soup('item')
		for item in item_list:
			if item.parent.name == "channels":
				name = item('title')[0].string
				url_link = item('link')[0].string	
				#url_link = url_link.replace('{goldpagemedia_path}', goldpagemedia_path)
				thumbnail = item('thumbnail')[0].string
				thumbnail = thumbnail.replace('{goldpagemedia_path}', goldpagemedia_path)
				adv_index = item('adv')[0].string
				desc = item('desc')[0].string
				addLink(url_link,name,thumbnail,adv_index, desc)
		
		
		if len(soup('channels')) > 0:
				channels = soup('channel')
				for channel in channels:
						channelId = channel('channel_id')[0].string
						name = channel('name')[0].string
						thumbnail = channel('thumbnail')[0].string
						thumbnail = thumbnail.replace('{goldpagemedia_path}', goldpagemedia_path)
						url = ''
						addDir(channelId, name,url,1,thumbnail)
	except:
		dialog = xbmcgui.Dialog()
		dialog.ok("Error", "Have an error when get local channels.")
		traceback.print_exc()
		
def getXMLOnline(url):
		print "#### GetXMLOnline(url) ###" + url
		global goldpagemedia_path
		global fanart
		global homepage
		try:
			req = urllib2.Request(url)
			socket.setdefaulttimeout(30)
			response = urllib2.urlopen(req, timeout=30)
			link=response.read()
			response.close()
			soup = BeautifulStoneSoup(link, convertEntities=BeautifulStoneSoup.XML_ENTITIES)
			fanart = soup('fanart_url')[0].string.replace('{goldpagemedia_path}', goldpagemedia_path)
			item_list = soup('item')
			for item in item_list:
				if item.parent.name == "channels":
					name = item('title')[0].string
					url_link = item('link')[0].string	
					thumbnail = item('thumbnail')[0].string.replace('{goldpagemedia_path}', goldpagemedia_path)
					adv_index = item('adv')[0].string
					desc = item('desc')[0].string
					addLink(url_link,name,thumbnail,adv_index, desc)
			if len(soup('channels')) > 0:
					channels = soup('channel')
					for channel in channels:
							channelId = channel('channel_id')[0].string
							name = channel('name')[0].string
							thumbnail = channel('thumbnail')[0].string.replace('{goldpagemedia_path}', goldpagemedia_path)
							addDir(channelId, name, url,3,thumbnail)
					mainPath = soup('mainpath')[0].string
					homepage = soup('homepage')[0].string
					if mainPath != goldpagemedia_path:
						goldpagemedia_path = mainPath
						writeConfig()
		except:
			dialog = xbmcgui.Dialog()
			dialog.ok("Error", "Have an error when get online channels.\nIt will be get local channels")
			getXMLLocal()
			traceback.print_exc()
		finally:
			sendDailyRequest()


def getChannelItems_xml(url,channelId):
	try:
		print "#### I'm in getChannelItems_xml(url,channelId) ###" + url + " ##channelId = " + channelId
		req = urllib2.Request(url)
		response = urllib2.urlopen(req)
		link=response.read()
		response.close()
		soup = BeautifulStoneSoup(link, convertEntities=BeautifulStoneSoup.XML_ENTITIES)
		#channel_list = soup('channel_id', text=channelId)[0].next.next.next.next.next
		channel_id_list = soup('channel_id')
		for id in channel_id_list:
			if channelId == id.text:
				channel = id.parent
				break


		items = channel('item')
		for item in items:
				try:
						name = item('title')[0].string
				except:
						pass
				try:
						if __settings__.getSetting('mirror_link') == "true":
								try:
										url = item('link')[1].string
								except:
										url = item('link')[0].string
						if __settings__.getSetting('mirror_link_low') == "true":
								try:
										url = item('link')[2].string
								except:
										try:
												url = item('link')[1].string
										except:
												url = item('link')[0].string
						else:
								url = item('link')[0].string
				except:
						pass
				try:
						thumbnail = item('thumbnail')[0].string.replace('{goldpagemedia_path}', goldpagemedia_path)
						url_adv = item('adv')[0].string
						desc = item('desc')[0].string
				except:
						pass
				addLink(url,name,thumbnail,url_adv, desc)
	except:
		dialog = xbmcgui.Dialog()
		dialog.ok("Error", "Have an error when get sub online channel.")
		traceback.print_exc()

def getChannelItems(channelId):
	print "#### I'm in getChannelItems(channelId)" + channelId
	try:
		response = open(file, 'rb')
		link=response.read()
		response.close()
		soup = BeautifulStoneSoup(link, convertEntities=BeautifulStoneSoup.XML_ENTITIES)
		channel_id_list = soup('channel_id')
		for id in channel_id_list:
			if channelId == id.text:
				channel = id.parent
				break
		#channel_list = soup('name', text=name)[0].next.next.next.next.next
		items = channel('item')
		for item in items:
				try:
						name = item('title')[0].string
				except:
						pass
				try:
						if __settings__.getSetting('mirror_link') == "true":
								try:
										url = item('link')[1].string
								except:
										url = item('link')[0].string
						if __settings__.getSetting('mirror_link_low') == "true":
								try:
										url = item('link')[2].string
								except:
										try:
												url = item('link')[1].string
										except:
												url = item('link')[0].string
						else:
								url = item('link')[0].string
				except:
						pass
				try:
						#url = url.replace('{goldpagemedia_path}', goldpagemedia_path)
						thumbnail = item('thumbnail')[0].string
						thumbnail = thumbnail.replace('{goldpagemedia_path}', goldpagemedia_path)
						url_adv = item('adv')[0].string
						desc = item('desc')[0].string
				except:
						pass
				addLink(url,name,thumbnail,url_adv, desc)
	except:
		dialog = xbmcgui.Dialog()
		dialog.ok("Error", "Have an error when get sub local channel.")
		traceback.print_exc()
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


def addDir(channelId, name,url,mode,iconimage):
	try:
		global fanart
		u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&channelId="+urllib.quote_plus(channelId)
		ok=True
		liz=xbmcgui.ListItem(name, iconImage=default_dir_icon, thumbnailImage=iconimage)
		liz.setInfo( type="Video", infoLabels={ "Title": name } )
		liz.setProperty("Fanart_Image",fanart)
		ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)
		return ok
	except:
		dialog = xbmcgui.Dialog()
		dialog.ok("Error", "Have an error when add directory.")
		traceback.print_exc()
		
def addLink(url,name,iconimage,adv_index,desc):
	try:
		#print "addLink: " + url
		#print "adv_index: " + adv_index
		ok=True
		
		if url.find("rtmp") != -1:
			url = url.replace(" ", "___")
			url = url.replace("=", "0_0")
			url = url.replace("?", "::::")
			url = url.replace("&", "0::0")
		
		give_url = sys.argv[0]+"?mode=10&url="+url+"&name="+name+"&adv_index="+adv_index
		#fullURL = url;
		#give_url = sys.argv[0]+"?mode=1&stream_name="+stream_name+"&ref="+ref+"&src="+src+"&stream_short_name="+short_name
		liz=xbmcgui.ListItem(name + "    " + desc, iconImage=default_video_icon, thumbnailImage=iconimage)
		liz.setInfo( type="Video", infoLabels={ "Title": name + "    " + desc } )
		liz.setProperty("Fanart_Image",fanart)
		ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=give_url,listitem=liz)
		return ok
	except:
		dialog = xbmcgui.Dialog()
		dialog.ok("Error", "Have an error when add link item.")
		traceback.print_exc()
		
def play_video(url, name, adv_index):

	try:
		if url.find("rtmp") != -1:
			url = url.replace("___", " ")
			url = url.replace("0_0", "=")
			url = url.replace("::::","?")
			url = url.replace("0::0", "&")
			#print "url RTMP replace result: " + url

		listitem = xbmcgui.ListItem(name, thumbnailImage=default_thumbnail_img)
		listitem.setInfo('video', {'Title': name})
		
		pls = xbmc.PlayList( xbmc.PLAYLIST_VIDEO )
		pls.clear()
			
		#Add commercial video in playlist
		isHasCommercial = True
		if __settings__.getSetting('commercial') != "true":
			isHasCommercial = bool(random.getrandbits(1))
			
		if isHasCommercial == True:
			advObject = getAdvertising(adv_index)	
			listitemAds = xbmcgui.ListItem(advObject["adv_title"], thumbnailImage=advObject["adv_thumbnail"])
			listitemAds.setInfo('video', {'Title': advObject["adv_title"]})
			pls.add(advObject["adv_file_path"], listitem=listitemAds)
		
		#Add url of streaming
		vftvWrongStreamName = "urlparams?channel:1005?token:6436488?video:l?audio:l?finished_gops:1"
		vttvRightStreamName = "urlparams?channel:1005?token:6436488?video:L?audio:L?finished_gops:1"
		if url.find(vftvWrongStreamName) != -1:
			url = url.replace(vftvWrongStreamName, vttvRightStreamName)
			url = url.replace("flashver=lnx_11,2,202,233","flashVer=LNX_11,2,202,233")
			#print "After URL = " + url
		pls.add(url, listitem=listitem )
		player.play(pls)
	#	while player.is_active:
	#		player.sleep(1000)
	except:
		dialog = xbmcgui.Dialog()
		dialog.ok("Error", "Have an error when play item.")

def getAdvertising(adv_index):
	try:
		req = urllib2.Request(goldpagemedia_path + file_advertising_online)
		response = urllib2.urlopen(req)
		link=response.read()
		response.close()
		soup = BeautifulStoneSoup(link, convertEntities=BeautifulStoneSoup.XML_ENTITIES)
		adv_num = len(soup('adv'))
		if (adv_index == None) or (adv_index == ""):
			adv_index = random.randrange(0,adv_num)
		else:
			if adv_index > adv_num:
				adv_index = random.randrange(0,adv_num)
			else:
				adv_index = int(adv_index) - 1
			
		print "Cuoi cung thi adv_index = " + str(adv_index)
		adv = soup('adv')[int(adv_index)]
		result = {}
		if adv != None:
			result["adv_title"] = adv('title')[0].string
			result["adv_thumbnail"] = adv('thumbnail')[0].string.replace('{goldpagemedia_path}', goldpagemedia_path)
			result["adv_file_path"] = adv('link')[0].string.replace('{goldpagemedia_path}', goldpagemedia_path)
		return result
	except:
		result["adv_title"] = "Advertisement  default"
		result["adv_thumbnail"] = "{goldpagemedia_path}/images/default.png".string.replace('{goldpagemedia_path}', goldpagemedia_path)
		result["adv_file_path"] = "{goldpagemedia_path}/videos/ads_1210091024.flv".string.replace('{goldpagemedia_path}', goldpagemedia_path)
		return result
		
def checkEmail():
	try:
		correct = 1
		old_email = __settings__.getSetting('email')
		if validateEmail(old_email) != 1:
			correct = 0
		while correct == 0:
			#old_email = __settings__.getSetting('email')
			__settings__.openSettings()
			new_email = __settings__.getSetting('email')
			if "" != new_email:
				if validateEmail(new_email):
					#send request to php here
					sendUserInfoRequest()
					correct = 1
				else:
					dialog = xbmcgui.Dialog()
					dialog.ok("Warning", "Your email is incorrect.")
			else:
				dialog = xbmcgui.Dialog()
				dialog.ok("Warning", "Your email is incorrect.")
	except:
		pass
			
def sendUserInfoRequest():
	try:
		name = __settings__.getSetting('name')
		email = __settings__.getSetting('email')
		url = goldpagemedia_path
		values = {}
		if email != "":
			values["email"] = email
		values["act"] = "track"
		if name != "":
			values["name"] = name
		data = urllib.urlencode(values)
		request = urllib2.Request(url +  file_php_online +"?"+ data)

		response = urllib2.urlopen(request, timeout=1)
	except:
		pass
	
def validateEmail(email):	
	if len(email) > 7:
		if re.match("^.+\\@(\\[?)[a-zA-Z0-9\\-\\.]+\\.([a-zA-Z]{2,3}|[0-9]{1,3})(\\]?)$", email) != None:
			return 1
	return 0

class MyPlayer(xbmc.Player):

	def __init__( self, *args, **kwargs ):
		self.is_active = True
		#print "#XBMCPlayer#"

	def onPlayBackPaused( self ):
		xbmc.log("#Im paused#")

	def onPlayBackResumed( self ):
		xbmc.log("#Im Resumed #")

	def onPlayBackStarted( self ):
		#print "#Playback Started#"
		try:
			print "#Im playing :: " + self.getPlayingFile()
		except:
			print "#I failed get what Im playing#"

	def onPlayBackEnded( self ):
		print "#Playback Ended#"

	def onPlayBackStopped( self ):
		print "## Playback Stopped ##"

	def sleep(self, s):
		xbmc.sleep(s)

	def playnext(self):
		#print "#Play next item in playlist."
		pass
player = MyPlayer(xbmc.PLAYER_CORE_DVDPLAYER)

		
params=get_params()
url=None
name=None
mode=None
adv_index=None
channelId = None
fullURL=None

try:
		url=urllib.unquote_plus(params["url"])
except:
		pass
try:
		name=urllib.unquote_plus(params["name"])
except:
		pass
try:
		adv_index=urllib.unquote_plus(params["adv_index"])
except:
		pass
try:
		channelId=urllib.unquote_plus(params["channelId"])
except:
		pass
try:
		mode=int(params["mode"])
except:
		pass

print "Mode: "+str(mode)
print "URL: "+str(url)
print "Name: "+str(name)

if mode==None:
	try:
		#print "mode None "
		readConfig()
		checkEmail()
		getChannels()
	except:
		dialog = xbmcgui.Dialog()
		dialog.ok("Error", "Have an error mode 0. Please contact admin")
		traceback.print_exc()

elif mode==1:
	try:
		readConfig()
		getChannelItems(channelId)
	except:
		dialog = xbmcgui.Dialog()
		dialog.ok("Error", "Have an error mode 1. Please contact admin")
		traceback.print_exc()

#elif mode==2:
#		print "mode 2 "+url
#		getXML(url)

elif mode==3:
	try:
		readConfig()
		getChannelItems_xml(url,channelId)
	except:
		dialog = xbmcgui.Dialog()
		dialog.ok("Error", "Have an error mode 3. Please contact admin")
		traceback.print_exc()

elif mode==10:
	try:
		readConfig()
		play_video(url, name, adv_index)
	except:
		dialog = xbmcgui.Dialog()
		dialog.ok("Error", "Have an error mode 10. Please contact admin")
		traceback.print_exc()
	

xbmcplugin.endOfDirectory(int(sys.argv[1]))