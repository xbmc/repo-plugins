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
import xbmc
import xbmcgui

class YouTubePlaylistControl:
	__settings__ = sys.modules[ "__main__" ].__settings__
	__language__ = sys.modules[ "__main__" ].__language__
	__plugin__ = sys.modules[ "__main__"].__plugin__	
	__dbg__ = sys.modules[ "__main__" ].__dbg__

	__core__ = sys.modules[ "__main__" ].__core__
	__scraper__ = sys.modules[ "__main__" ].__scraper__
	__utils__ = sys.modules[ "__main__" ].__utils__	
	
	def playAll(self, params={}):
		get = params.get
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
		elif get("user_feed") == "newsubscriptions":
			result = self.getNewSubscriptions(params)
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
	
	def getPlayList(self, params = {}):
		get = params.get
		
		if not get("playlist"):
			return False
		params["user_feed"] = "playlist" 
		return self.__core__.listAll(params)
	
	def getDiscoSearch(self, params = {}):
		(result, status) = self.__scraper__.searchDisco(params)
		
		if status == 200:
			(result, status) = self.__core__.getBatchDetails(result, params)
		
		return result
	
	def getFavorites(self, params = {}):
		get = params.get
		
		if not get("contact"):
			return False
		
		params["user_feed"] = "favorites"
		return self.__core__.listAll(params)
	
	def getNewSubscriptions(self, params = {}):
		get = params.get
		
		if not get("contact"):
			return False
		params["user_feed"] = "newsubscriptions"
		return self.__core__.listAll(params)
	
	def addToPlaylist(self, params = {}):
		get = params.get
		
		result = []
		if (not get("playlist")):
			params["user_feed"] = "playlists"
			params["login"] = "true"
			params["folder"] = "true"
			result = self.__core__.listAll(params)
		
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
				result = self.__core__.listAll(params)
				for item in result:
					if get("title") == item["Title"]:
						params["playlist"] = item["playlist"]
						break
		elif selected > 0:
			params["playlist"] = result[selected - 1].get("playlist")
		
		if get("playlist"):
			self.__core__.add_to_playlist(params)
			return True
		
		return False
	
	def createPlayList(self, params = {}):
		get = params.get
		
		input = self.__utils__.getUserInput(self.__language__(30529))
		if input:
			params["title"] = input
			self.__core__.add_playlist(params)
			return True
		return False
				
	def removeFromPlaylist(self, params = {}):
		get = params.get
		
		if get("playlist") and get("playlist_entry_id"):
			(message, status) = self.__core__.remove_from_playlist(params)
			
			if (status != 200):
				self.__utils__.showErrorMessage(self.__language__(30600), message, status)
				return False
			xbmc.executebuiltin( "Container.Refresh" )
		return True

	def deletePlaylist(self, params):
		get = params.get
		if get("playlist"):
			(message, status) = self.__core__.del_playlist(params)
			
			if status != 200:
				self.__utils__.showErrorMessage(self.__language__(30600), message, status)
				return False
			xbmc.executebuiltin( "Container.Refresh" )
		return True
