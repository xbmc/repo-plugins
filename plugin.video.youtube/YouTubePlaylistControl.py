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

import sys
import xbmc, xbmcgui
import YouTubeCore, YouTubeUtils

class YouTubePlaylistControl(YouTubeCore.YouTubeCore, YouTubeUtils.YouTubeUtils):
	__settings__ = sys.modules[ "__main__" ].__settings__
	__language__ = sys.modules[ "__main__" ].__language__
	__plugin__ = sys.modules[ "__main__"].__plugin__	
	__dbg__ = sys.modules[ "__main__" ].__dbg__

	__feeds__ = sys.modules[ "__main__" ].__feeds__
	__scraper__ = sys.modules[ "__main__" ].__scraper__
	__player__ = sys.modules[ "__main__" ].__player__
	
	def playAll(self, params={}):
		get = params.get
		if self.__dbg__:
			print self.__plugin__ + " playAll"

		params["fetch_all"] = "true"
		result = []
		# fetch the video entries
		if get("playlist"):
			result = self.getPlayList(params)
		elif get("search_disco"):
			params["search"] = params["search_disco"]
			result = self.getDiscoSearch(params)
		elif get("user_feed") == "favorites":
			result = self.getFavorites(params)
		elif get("scraper") == "watch_later":
			result = self.getWatchLater(params)
		elif get("scraper") == "liked_videos":
			result = self.getLikedVideos(params)
		elif get("scraper") == "music_artists":
			result = self.getArtist(params)
		elif get("scraper") == "recommended":
			result = self.getRecommended(params)
		elif get("user_feed") == "newsubscriptions":
			result = self.getNewSubscriptions(params)
		elif get("video_list", False) :
			result = []
			video_list = get("video_list", "").split(",")
			for videoid in video_list:
				(video, status) = self.__player__.getVideoObject({ "videoid": videoid})
				result.append(video)
		else:
			return
		
		if len(result) == 0:
			return
		
		if self.__dbg__:
			print self.__plugin__ + " " + repr(len(result)) + " video results "
		
		if get("videoid"):
			video_index = -1
			for index, video in enumerate(result):
				vget = video.get
				if vget("videoid") == get("videoid"):
					video_index = index
			if video_index >= 0:
				result = result[video_index:]
		
		player = xbmc.Player()
		if (player.isPlaying()):
			player.stop()
		
		playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
		playlist.clear()
		
		video_url = "%s?path=/root&action=play_video&videoid=%s"  
		# queue all entries
		for entry in result:
			video = entry.get
			listitem=xbmcgui.ListItem(label=video("Title"), iconImage=video("thumbnail"), thumbnailImage=video("thumbnail"))
			listitem.setProperty('IsPlayable', 'true')
			listitem.setProperty( "Video", "true" )
			listitem.setInfo(type='Video', infoLabels=entry)
			playlist.add(video_url % (sys.argv[0], video("videoid") ), listitem)
		
		if (get("shuffle")):
			playlist.shuffle()

		xbmc.executebuiltin('playlist.playoffset(video , 0)')
		
	def queueVideo(self, params = {}):
		get = params.get
		if self.__dbg__:
			print self.__plugin__ + " - Queuing videos: " + get("videoid")
		
		items =[]
		videoids = get("videoid")
		
		if videoids.find(','):
			items = videoids.split(',')
		else:
			items.append(videoids)
		
		(video, status) = self.__core__.getBatchDetails(items, params);

		if status != 200:
			if self.__dbg__ :
				print self.__plugin__ + " construct video url failed contents of video item " + repr(video)
				
			self.showErrorMessage(self.__language__(30603), video["apierror"], status)
			return False

		listitem=xbmcgui.ListItem(label=video['Title'], iconImage=video['thumbnail'], thumbnailImage=video['thumbnail'], path=video['video_url']);
		listitem.setProperty('IsPlayable', 'true')
		listitem.setInfo(type='Video', infoLabels=video)

		if self.__dbg__:
			print self.__plugin__ + " - Queuing video: " + self.makeAscii(video['Title']) + " - " + get('videoid') + " - " + video['video_url']

		playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
		playlist.add("%s?path=/root&action=play_video&videoid=%s" % (sys.argv[0], video["videoid"] ), listitem)

	def getPlayList(self, params = {}):
		get = params.get
		
		if not get("playlist"):
			return False
		params["user_feed"] = "playlist" 
		return self.__feeds__.listAll(params)
	
	def getWatchLater(self, params = {}):
		(result, status ) = self.__scraper__.scrapeWatchLater(params)
		return result

	def getDiscoSearch(self, params = {}):
		(result, status) = self.__scraper__.searchDisco(params)
		
		if status == 200:
			(result, status) = self.getBatchDetails(result, params)
		
		return result
	
	def getFavorites(self, params = {}):
		get = params.get
		
		if not get("contact"):
			return False
		
		params["user_feed"] = "favorites"
		return self.__feeds__.listAll(params)
	
	def getNewSubscriptions(self, params = {}):
		get = params.get
		
		if not get("contact"):
			return False
		params["user_feed"] = "newsubscriptions"
		return self.__feeds__.listAll(params)
	
	def getRecommended(self, params = {}):
		get = params.get
		
		if not get("scraper") or not get("login"):
			return False
		
		(result, status) = self.__scraper__.scrapeRecommended(params)
		
		if status == 200:
			(result, status) = self.getBatchDetails(result, params)
		
		return result
	
	def getArtist(self, params = {}):
		get = params.get
		
		if not get("artist"):
			return False
		
		(result, status) = self.__scraper__.scrapeArtist(params)
		
		if status == 200:
			(result, status) = self.getBatchDetails(result, params)
		
		return result
	
	def getLikedVideos(self, params = {}):
		get = params.get
		if not get("scraper") or not get("login"):
			return False
		
		(result, status) = self.__scraper__.scrapeLikedVideos(params)
		print " liked videos "  + repr(result)
		if status == 200:
			(result, status) = self.getBatchDetails(result, params)
			
		return result
		
	def addToPlaylist(self, params = {}):
		get = params.get
		
		result = []
		if (not get("playlist")):
			params["user_feed"] = "playlists"
			params["login"] = "true"
			params["folder"] = "true"
			result = self.__feeds__.listAll(params)
		
		selected = -1
		if result:
			list = []
			list.append(self.__language__(30529))
			for item in result:
				list.append(item["Title"])
			dialog = xbmcgui.Dialog()
			selected = dialog.select(self.__language__(30528), list)
			
		if selected == 0:
			self.createPlayList(params)
			if get("title"):
				result = self.__feeds__.listAll(params)
				for item in result:
					if get("title") == item["Title"]:
						params["playlist"] = item["playlist"]
						break
		elif selected > 0:
			params["playlist"] = result[selected - 1].get("playlist")
		
		if get("playlist"):
			self.add_to_playlist(params)
			return True
		
		return False
	
	def createPlayList(self, params = {}):
		get = params.get
		
		input = self.getUserInput(self.__language__(30529))
		if input:
			params["title"] = input
			self.add_playlist(params)
			return True
		return False
				
	def removeFromPlaylist(self, params = {}):
		get = params.get
		
		if get("playlist") and get("playlist_entry_id"):
			(message, status) = self.remove_from_playlist(params)
			
			if (status != 200):
				self.showErrorMessage(self.__language__(30600), message, status)
				return False
			xbmc.executebuiltin( "Container.Refresh" )
		return True
	
	def deletePlaylist(self, params):
		get = params.get
		if get("playlist"):
			(message, status) = self.del_playlist(params)
			
			if status != 200:
				self.showErrorMessage(self.__language__(30600), message, status)
				return False
			xbmc.executebuiltin( "Container.Refresh" )
		return True
