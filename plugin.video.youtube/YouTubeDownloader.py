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

import sys, urllib2, os
import DialogDownloadProgress

class YouTubeDownloader():
	
	dialog = ""
	
	def __init__(self):
		self.xbmc = sys.modules["__main__"].xbmc
		self.xbmcvfs = sys.modules["__main__"].xbmcvfs

		self.settings = sys.modules[ "__main__" ].settings
		self.language = sys.modules[ "__main__" ].language
		self.plugin = sys.modules[ "__main__"].plugin
		self.dbg = sys.modules[ "__main__" ].dbg
		self.utils =  sys.modules[ "__main__" ].utils
		self.player = sys.modules["__main__" ].player
		self.storage = sys.modules[ "__main__" ].storage
		self.common = sys.modules[ "__main__" ].common
		self.cache = sys.modules[ "__main__" ].cache
	
	def downloadVideo(self, params = {}):
		self.common.log("")
		get = params.get
		
		path = self.settings.getSetting( "downloadPath" )
		if (not path):
			self.utils.showMessage(self.language(30600), self.language(30611))
			self.settings.openSettings()
			self.dbg = self.settings.getSetting("debug") == "true"
			path = self.settings.getSetting( "downloadPath" )

		if self.cache.lock("YouTubeDownloadLock"):
			params["silent"] = "true"
			self.common.log("Downloader not active, initializing downloader.")
			
			self.storage.addVideoToDownloadQueue(params)
			self.processQueue(params)
			self.cache.unlock("YouTubeDownloadLock")
		else:
			self.common.log("Downloader is active, Queueing video.")
			self.storage.addVideoToDownloadQueue(params)

	def processQueue(self, params = {}):
		self.common.log("")
		videoid = self.storage.getNextVideoFromDownloadQueue()
		self.common.log("res: " + videoid)
		
		if videoid:
			if not self.dialog:
				self.dialog = DialogDownloadProgress.DownloadProgress()
	
			while videoid:
				params["videoid"] = videoid
				( video, status ) = self.player.getVideoObject(params)
				if status != 200:
					self.utils.showMessage(self.language(30625), video["apierror"])
					self.storage.removeVideoFromDownloadQueue(videoid)
					videoid = self.storage.getNextVideoFromDownloadQueue()
					continue
				item = video.get
				if item("stream_map"):
					self.utils.showMessage(self.language(30607), self.language(30619))
					self.storage.removeVideoFromDownloadQueue(videoid)
					videoid = self.storage.getNextVideoFromDownloadQueue()
					continue
				
				( video, status ) = self.downloadVideoURL(video)
				self.storage.removeVideoFromDownloadQueue(videoid)
				videoid = self.storage.getNextVideoFromDownloadQueue()

			self.common.log("Finished download queue.")
			self.dialog.close()
			self.dialog = ""
			
	def downloadVideoURL(self, video, params = {}):
		self.common.log(video['Title'])
		
		if video["video_url"].find("swfurl") > 0:
			self.utils.showMessage(self.language( 30625 ), self.language(30619))
			return ([], 303)
		
		video["downloadPath"] = self.settings.getSetting( "downloadPath" )
		self.player.downloadSubtitle(video) 
		url = urllib2.Request(video['video_url'])
		url.add_header('User-Agent', self.common.USERAGENT);
		filename = "%s-[%s].mp4" % ( ''.join(c for c in video['Title'].decode("utf-8") if c not in self.utils.INVALID_CHARS), video["videoid"] )
		filename_incomplete = os.path.join(self.xbmc.translatePath( "special://temp" ).decode("utf-8"), filename )
		filename_complete = os.path.join(self.settings.getSetting("downloadPath").decode("utf-8"), filename)

		if self.xbmcvfs.exists(filename_complete):
			self.xbmcvfs.delete(filename_complete)

		file = self.storage.openFile(filename_incomplete, "wb")
		con = urllib2.urlopen(url);

		total_size = 8192 * 25
		chunk_size = 8192
		
		if con.info().getheader('Content-Length').strip():			
			total_size = int(con.info().getheader('Content-Length').strip())	
			chunk_size = int(total_size / 200) # We only want 200 updates of the status bar.
		try:
			bytes_so_far = 0
			
			videos = []
			while 1:
				chunk = con.read(chunk_size)
				bytes_so_far += len(chunk)
				percent = int(float(bytes_so_far) / float(total_size) * 100)
				file.write(chunk)
				
				queue = self.cache.get("YouTubeDownloadQueue")

				if queue:
					try:
						videos = eval(queue)
					except:
						videos = []
				else:
					videos = []
				
				heading = "[%s] %s - %s%%" % ( str(len(videos)), self.language(30624), str(percent))
				self.dialog.update(percent=percent, heading = heading, label=video["Title"])

				if not chunk:
					break
			
			con.close()
			file.close()
		except:
			try:
				con.close()
				file.close()
			except:
				self.common.log("Failed to close download stream and file handle")
		
		self.xbmcvfs.rename(filename_incomplete, filename_complete)
		self.dialog.update(heading = self.language(30604), label=video["Title"])
		self.storage.storeValue( "vidstatus-" + video['videoid'], "1" )
		return ( video, 200 )
