''' 
   YouTube plugin for XBMC
    Copyright (C) 2010-2011 Tobias Ussing And Henrik Mosgaard Jensen

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

import sys, urllib, re, os.path, datetime, time, string
import simplejson as json
import xbmc, xbmcgui, xbmcplugin
import YouTubeCore
from xml.dom.minidom import parseString

core = YouTubeCore.YouTubeCore()

class YouTubePlayer:
	__settings__ = sys.modules[ "__main__" ].__settings__
	__language__ = sys.modules[ "__main__" ].__language__
	__plugin__ = sys.modules[ "__main__" ].__plugin__ 
	__dbg__ = sys.modules[ "__main__" ].__dbg__
	VALID_CHARS = "-_.() %s%s" % (string.ascii_letters, string.digits)
	USERAGENT = "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-GB; rv:1.9.2.8) Gecko/20100722 Firefox/3.6.8"
	urls = {}
	
	def __init__(self):
		# YouTube Playback Feeds
		self.urls['video_stream'] = "http://www.youtube.com/watch?v=%s&safeSearch=none"
		self.urls['embed_stream'] = "http://www.youtube.com/get_video_info?video_id=%s"
		self.urls['timed_text_index'] = "http://www.youtube.com/api/timedtext?type=list&v=%s"
		self.urls['video_info'] = "http://gdata.youtube.com/feeds/api/videos/%s"
		self.urls['close_caption_url'] = "http://www.youtube.com/api/timedtext?type=track&v=%s&name=%s&lang=%s"
		self.urls['transcription_url'] = "http://www.youtube.com/api/timedtext?sparams=asr_langs,caps,expire,v&asr_langs=en,ja&caps=asr&expire=%s&key=yttt1&signature=%s&hl=en&type=trackformat=1&lang=en&kind=asr&name=&v=%s&tlang=en"
		self.urls['annotation_url'] = "http://www.youtube.com/api/reviews/y/read2?video_id=%s"
		self.urls['remove_watch_later'] = "http://www.youtube.com/addto_ajax?action_delete_from_playlist=1"
	
	# ================================ Video Playback ====================================
	
	def playVideo(self, params = {}):
		get = params.get
		
		(video, status) = self.getVideoObject(params);
		
		if status != 200:
			if self.__dbg__ : 
				print self.__plugin__ + " construct video url failed contents of video item " + repr(video)
			self.showErrorMessage(self.__language__(30603), video["apierror"], status)
			return False
		
		listitem=xbmcgui.ListItem(label=video['Title'], iconImage=video['thumbnail'], thumbnailImage=video['thumbnail'], path=video['video_url']);		
		listitem.setInfo(type='Video', infoLabels=video)
		
		if self.__dbg__:
			print self.__plugin__ + " - Playing video: " + self.makeAscii(video['Title']) + " - " + get('videoid') + " - " + video['video_url']
		
		xbmcplugin.setResolvedUrl(handle=int(sys.argv[1]), succeeded=True, listitem=listitem)
					
		self.__settings__.setSetting( "vidstatus-" + video['videoid'], "7" )

	def getVideoUrlMap(self, pl_obj, video = {}):
		if self.__dbg__:
			print self.__plugin__ + " getVideoUrlMap: " 
		links = {}
		video["url_map"] = "true"
					
		html = ""
		if pl_obj["args"].has_key("fmt_stream_map"):
			html = pl_obj["args"]["fmt_stream_map"]

		if len(html) == 0 and pl_obj["args"].has_key("url_encoded_fmt_stream_map"):
			html = urllib.unquote(pl_obj["args"]["url_encoded_fmt_stream_map"])

		if len(html) == 0 and pl_obj["args"].has_key("fmt_url_map"):
			html = pl_obj["args"]["fmt_url_map"]

		html = urllib.unquote_plus(html)

		if pl_obj["args"].has_key("liveplayback_module"):
			video["live_play"] = "true"

		fmt_url_map = [html]
		if html.find("|") > -1:
			fmt_url_map = html.split('|')
		elif html.find(",url=") > -1:
			fmt_url_map = html.split(',url=')
		elif html.find("&conn=") > -1:
			video["stream_map"] = "true"
			fmt_url_map = html.split('&conn=')
		
		print self.__plugin__ + " getVideoUrlMap Searching for fmt_url_map 2: "  + repr(fmt_url_map)
		
		if len(fmt_url_map) > 0:
			for index, fmt_url in enumerate(fmt_url_map):
				if (len(fmt_url) > 7 and fmt_url.find("&") > 7):
					quality = "5"
					final_url = fmt_url.replace(" ", "%20").replace("url=", "")
					
					if (final_url.rfind(';') > 0):
						final_url = final_url[:final_url.rfind(';')]
					
					if (final_url.rfind(',') > final_url.rfind('&id=')): 
						final_url = final_url[:final_url.rfind(',')]
					elif (final_url.rfind(',') > final_url.rfind('/id/') and final_url.rfind('/id/') > 0):
						final_url = final_url[:final_url.rfind('/')]

					if (final_url.rfind('itag=') > 0):
						quality = final_url[final_url.rfind('itag=') + 5:]
						if quality.find('&') > -1:
							quality = quality[:quality.find('&')]
						if quality.find(',') > -1:
							quality = quality[:quality.find(',')]
					elif (final_url.rfind('/itag/') > 0):
						quality = final_url[final_url.rfind('/itag/') + 6:]
					
					if final_url.find("&type") > 0:
						final_url = final_url[:final_url.find("&type")]
					
					if self.__settings__.getSetting("preferred") == "true":
						pos = final_url.find("://")
						fpos = final_url.find("fallback_host")
						if pos > -1 and fpos > -1:
							host = final_url[pos + 3:]
							if host.find("/") > -1:
								host = host[:host.find("/")]
							fmt_fallback = final_url[fpos + 14:]
							if fmt_fallback.find("&") > -1:
								fmt_fallback = fmt_fallback[:fmt_fallback.find("&")]
							#print self.__plugin__ + " Swapping cached host [%s] and fallback host [%s] " % ( host, fmt_fallback )
							final_url = final_url.replace(host, fmt_fallback)
							final_url = final_url.replace("fallback_host=" + fmt_fallback, "fallback_host=" + host)

					if final_url.find("rtmp") > -1 and index > 0:
						if pl_obj.has_key("url") or True:
							final_url += " swfurl=" + pl_obj["url"] + " swfvfy=1"

						playpath = False
						if final_url.find("stream=") > -1:
							playpath = final_url[final_url.find("stream=")+7:]
							if playpath.find("&") > -1:
								playpath = playpath[:playpath.find("&")]
						else:
							playpath = fmt_url_map[index - 1]

						if playpath:
							if pl_obj["args"].has_key("ptk") and pl_obj["args"].has_key("ptchn"):
								final_url += " playpath=" + playpath + "?ptchn=" + pl_obj["args"]["ptchn"] + "&ptk=" + pl_obj["args"]["ptk"] 

					links[int(quality)] = final_url.replace('\/','/')
		
		if self.__dbg__:
			print self.__plugin__ + " getVideoUrlMap done " + repr(links)
		return links 
			
	def getInfo(self, params):
		get = params.get
		video = {}
		
		(result, status) = core._fetchPage(link = self.urls["video_info"] % get("videoid"), api=True)

		if status == 200:
			video = core._getvideoinfo(result)
		
			if len(result) == 0:
				if self.__dbg__:
					print self.__plugin__ + " Couldn't parse API output, YouTube doesn't seem to know this video id?"
				video["apierror"] = self.__language__(30603)
				return (video, 303)
		else:
			if self.__dbg__:
				print self.__plugin__ + " Got API Error from YouTube!"
			video["apierror"] = result
			
			return (video,303)
		video = video[0]
		return (video, status)
	
	def selectVideoQuality(self, links, params):
		get = params.get
		link = links.get
		video_url = ""

		if self.__dbg__:
			print self.__plugin__ + " selectVideoQuality : " #+ repr(links)
		
		if get("action") == "download":
			hd_quality = int(self.__settings__.getSetting( "hd_videos_download" ))
			if ( hd_quality == 0 ):
				hd_quality = int(self.__settings__.getSetting( "hd_videos" ))
			else:
				hd_quality -= 1
		else:
			if (not get("quality")):
				hd_quality = int(self.__settings__.getSetting( "hd_videos" ))
			else:
				if (get("quality") == "1080p"):
					hd_quality = 2
				elif (get("quality") == "720p"):
					hd_quality = 1
				else: 
					hd_quality = 0
		
			# SD videos are default, but we go for the highest res
		if (link(35)):
			video_url = link(35)
		elif (link(34)):
			video_url = link(34)
		elif (link(59)): #<-- 480 for rtmpe
			video_url = link(59)
		elif (link(78)): #<-- seems to be around 400 for rtmpe
			video_url = link(78)
		elif (link(18)):
			video_url = link(18)
		elif (link(5)):
			video_url = link(5)
		
		if (hd_quality > 0): #<-- 720p
			if (link(22)):
				video_url = link(22)
		if (hd_quality > 1): #<-- 1080p
			if (link(37)):
				video_url = link(37)
				
		if not len(video_url) > 0:
			if self.__dbg__:
				print self.__plugin__ + " selectVideoQuality - construct_video_url failed, video_url not set"
			return video_url
		
		if get("action") != "download":
			video_url += " | " + self.USERAGENT

		if self.__dbg__:
			print self.__plugin__ + " selectVideoQuality done"			
		return video_url
	
	def getVideoObject(self, params):
		get = params.get
		video = {}
		links = []
				
		(video, status) = self.getInfo(params)
		(links, video) = self._getVideoLinks(video, params)
		
		if links:
			video["video_url"] = self.selectVideoQuality(links, params)
			if video["video_url"] == "":
				video['apierror'] = self.__language__(30618)
				status = 303
		else:
			status = 303
			vget = video.get
			if vget("live_play"):
				video['apierror'] = self.__language__(30612)
			elif vget("stream_map"):
				video['apierror'] = self.__language__(30620)
			else:
				video['apierror'] = self.__language__(30618)
		
		return (video, status)

	def _convertFlashVars(self, html):
		#print self.__plugin__ + " _convertFlashVars : " + repr(html)
		obj = { "PLAYER_CONFIG": { "args": {} } }
		temp = html.split("&")
		print self.__plugin__ + " _convertFlashVars : " + str(len(temp))
		for item in temp:
			it = item.split("=")
			obj["PLAYER_CONFIG"]["args"][it[0]] = urllib.unquote_plus(it[1])
		#print self.__plugin__ + " _convertFlashVars done : " + repr(obj)
		return obj

	def _getVideoLinks(self, video, params):
		get = params.get
		vget = video.get
		player_object = {}
		links = []

		if self.__dbg__:
			print self.__plugin__ + " _getVideoLinks trying website"

		(result, status) = core._fetchPage(link = self.urls["video_stream"] % get("videoid"))

		if status == 200:
			data = result.find("PLAYER_CONFIG")
			if data > -1:
				data = result.rfind("yt.setConfig", 0, data)
				data = re.compile('yt.setConfig\((.*?PLAYER_CONFIG.*?)\)').findall(result[data:].replace("\n", ""))
				if len(data) > 0:
					player_object = json.loads(data[0].replace('\'PLAYER_CONFIG\'', '"PLAYER_CONFIG"'))
			else:
				data = result
				data = data[data.find('flashvars'):].replace("\n", "").replace("&amp;", "&")
				data = re.findall('="(ttsurl=.*?)"', data)
				if len(data) > 0:
					player_object = self._convertFlashVars(data[0])

		else:
			# Default error reporting.
			if status == 403:
				video['apierror'] = self.__language__(30617)
			elif status != 200:
				if not vget('apierror'):
					video['apierror'] = self.__language__(30617)

			if self.__dbg__:
				print self.__plugin__ + " _getVideoLinks Falling back to embed"

			(result, status) = core._fetchPage(link = self.urls["embed_stream"] % get("videoid"))
		
			# Fallback error reporting
			if result.find("status=fail") > -1:
				status = 303
				video["apierror"] = re.compile('reason=(.*)%3Cbr').findall(content)[0]

			if status == 200:
				player_object = self._convertFlashVars(result)

		# Find playback URI
		if player_object.has_key("PLAYER_CONFIG"):
			if player_object["PLAYER_CONFIG"].has_key("args"):
				if player_object["PLAYER_CONFIG"]["args"].has_key("ttsurl"):
					video["ttsurl"] = player_object["PLAYER_CONFIG"]["args"]["ttsurl"]

				links = self.getVideoUrlMap(player_object["PLAYER_CONFIG"], video)

				if len(links) == 0:
					if self.__dbg__:
						print self.__plugin__ + " _getVideoLinks Couldn't find url map or stream map."

		return (links, video)
	
	def makeAscii(self, str):
		try:
			return str.encode('ascii')
		except:
			if self.__dbg__:
				print self.__plugin__ + " makeAscii hit except on : " + repr(str)
			s = ""
			for i in str:
				try:
					i.encode("ascii")
				except:
					continue
				else:
					s += i
			return s

	# Standardised error handler
	def showErrorMessage(self, title = "", result = "", status = 500):
		if title == "":
			title = self.__language__(30600)
		if result == "":
			result = self.__language__(30617)
			
		if ( status == 303):
			self.showMessage(title, result)
		else :
			self.showMessage(title, self.__language__(30617))
