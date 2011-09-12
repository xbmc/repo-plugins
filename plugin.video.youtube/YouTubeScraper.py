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

import sys, urllib, re
import YouTubeCore, YouTubeUtils

class YouTubeScraper(YouTubeCore.YouTubeCore, YouTubeUtils.YouTubeUtils):	 

	__settings__ = sys.modules[ "__main__" ].__settings__
	__language__ = sys.modules[ "__main__" ].__language__
	__plugin__ = sys.modules[ "__main__"].__plugin__	
	__dbg__ = sys.modules[ "__main__" ].__dbg__
	
	__feeds__ = sys.modules[ "__main__" ].__feeds__
	__storage__ = sys.modules[ "__main__" ].__storage__
	
	def __init__(self):
		self.urls['categories'] = "http://www.youtube.com/videos"
		self.urls['current_trailers'] = "http://www.youtube.com/trailers?s=trit&p=%s&hl=en"
		self.urls['disco_main'] = "http://www.youtube.com/disco" 
		self.urls['disco_mix_list'] = "http://www.youtube.com/watch?v=%s&feature=disco&playnext=1&list=%s"
		self.urls['disco_search'] = "http://www.youtube.com/disco?action_search=1&query=%s"
		self.urls['game_trailers'] = "http://www.youtube.com/trailers?s=gtcs"
		self.urls['live'] = "http://www.youtube.com/live"
		self.urls['main'] = "http://www.youtube.com"
		self.urls['movies'] = "http://www.youtube.com/ytmovies"
		self.urls['popular_game_trailers'] = "http://www.youtube.com/trailers?s=gtp&p=%s&hl=en"
		self.urls['popular_trailers'] = "http://www.youtube.com/trailers?s=trp&p=%s&hl=en"
		self.urls['recommended'] = "http://www.youtube.com/videos?r=1&hl=en"
		self.urls['show_list'] = "http://www.youtube.com/show"
		self.urls['shows'] = "http://www.youtube.com/shows"
		self.urls['trailers'] = "http://www.youtube.com/trailers?s=tr"
		self.urls['latest_trailers'] = "http://www.youtube.com/trailers?s=tr"
		self.urls['latest_game_trailers'] = "http://www.youtube.com/trailers?s=gtcs"
		self.urls['upcoming_game_trailers'] = "http://www.youtube.com/trailers?s=gtcs&p=%s&hl=en"
		self.urls['upcoming_trailers'] = "http://www.youtube.com/trailers?s=tros&p=%s&hl=en"
		self.urls['watch_later'] = "http://www.youtube.com/my_watch_later_list"
		self.urls['liked_videos'] = "http://www.youtube.com/my_liked_videos"
		self.urls['music'] = "http://www.youtube.com/music"
		self.urls['artist'] = "http://www.youtube.com/artist?a=%s&feature=artist"	
		
#=================================== Trailers ============================================
	def scrapeTrailersListFormat (self, params = {}):
		get = params.get
		if self.__dbg__:
			print self.__plugin__ + " scrapeTrailersListFormat"

		yobjects = []
		
		url = self.createUrl(params)
		result = self._fetchPage({"link":url})
		
		#list = SoupStrainer(id="recent-trailers-container", name="div")
		#trailers = BeautifulSoup(result["content"], parseOnlyThese=list)
		trailers = self.parseDOM(result["content"], "div", attrs = { "id": "recent-trailers-container"})
		
		if (len(trailers) > 0):
			items = []
			ahref = self.parseDOM(trailers, "a", attrs = {"class": " yt-uix-hovercard-target", "id": ".*?" }, ret = "href")
			athumb = self.parseDOM(trailers, "img", attrs = { "alt": "Thumbnail" }, ret = "src")
			if len(ahref) == len(athumb):
				for i in range(0, len(ahref)):
					videoid = ahref[i]
				
					if (videoid):
						if (videoid.find("=") > -1):
							videoid = videoid[videoid.find("=")+1:]  
							items.append( (videoid, athumb[i]) )
		
		if (items):
			(yobjects, status) = self.getBatchDetailsThumbnails(items)
			
		if (not yobjects):
			return (yobjects, 500)
		
		if self.__dbg__:
			print self.__plugin__ + " scrapeTrailersListFormat Done"
		return (yobjects, status)
	
#=================================== Categories  ============================================
	def scrapeCategoriesGrid(self, params = {}):
		get = params.get
		if self.__dbg__:
			print self.__plugin__ + " scrapeCategoriesGrid: "
		
		url = self.createUrl(params)
		result = self._fetchPage({"link":url})

		next = "false"
		pagination = self.parseDOM(result["content"], "div", attrs = { "class": "yt-uix-pager"})

		if (len(pagination) > 0):
			tmp = str(pagination)
			if (tmp.find("Next") > 0):
				next = "true"
		
		videos = self.parseDOM(result["content"], "div", { "id": "browse-video-data"})
		if len(videos) == 0:
			videos = self.parseDOM(result["content"], "div", attrs= { "class": "most-viewed-list paginated"})
		
		items = []
		if (len(videos) > 0):
			links = self.parseDOM(videos, "a", attrs = { "class": "ux-thumb-wrap " } , ret = "href")
			if len(links) == 0:
				links = self.parseDOM(videos, "a", ret = "href")
			for link in links:
				if (link.find("/watch?v=") != -1):
					link = link[link.find("=") + 1:]
				if (link.find("&") > 0):
					link = link[:link.find("&")]
				items.append(link)
		if self.__dbg__:
			print self.__plugin__ + " scrapeCategoriesGrid done " 
		return (items, result["status"])
		
#=================================== Music  ============================================
	def scrapeMusicCategories(self, params = {}):
		get = params.get
		if self.__dbg__:
			print self.__plugin__ + " scrapeMusicCategories"
		
		items = []
		url = self.urls["music"]

		result = self._fetchPage({"link": url})
		
		if result["status"] == 200:
			categories = self.parseDOM(result["content"], "div", attrs = { "id": "browse-filter-menu"})
			ahref = self.parseDOM(categories, "a", ret= "href")
			acontent = self.parseDOM(categories, "a")

			if len(acontent) == len(ahref) and len(ahref) > 0:
				for i in range(0 , len(ahref)):
					item = {}
					title = self.makeAscii(acontent[i])
					title = self.replaceHtmlCodes(title)
					link = ahref[i].replace("/music/","/")
					item["Title"] = title
					item["category"] = urllib.quote_plus(link)
					item["icon"] = "music"
					item["thumbnail"] = "music"
					item["scraper"] = get("scraper")
					if get("scraper") == "music_artists":
						item["folder"] = "true"
						
					items.append(item)

		if self.__dbg__:
			print self.__plugin__ + " scrapeMusicCategories done" 
		return (items, result["status"]) 

	
	def scrapeArtist(self, params = {}):
		get = params.get
		if self.__dbg__:
			print self.__plugin__ + " scrapeArtist"

		items = []
		videos = []
		
		if get("artist") and get("artist_name"):
			self.__storage__.saveStoredArtist(params)
		
		if get("artist"):
			url = self.urls["artist"] % get("artist")
			result = self._fetchPage({"link": url})
			
			if result["status"] == 200:
				videos = re.compile('<a href="/watch\?v=(.*)&amp;feature=artist" title="').findall(result["content"]);
			
		for v in videos:
			if v not in items:
				items.append(v)
		
		if self.__dbg__:
			print self.__plugin__ + " scrapeArtist done"
		return ( items, result["status"] )
	
	def scrapeSimilarArtists(self, params = {}):
		get = params.get
		if self.__dbg__:
			print self.__plugin__ + " scrapeSimilarArtists"
		
		items = []
		if get("artist"):
			url = self.urls["artist"] % get("artist")
			result = self._fetchPage({"link": url})
			
			if result["status"] == 200:
				artists = self.parseDOM(result["content"], "div", { "id": "similar-artists"});
				ahref = self.parseDOM(artists, "a", ret = "href")
				atitle = self.parseDOM(artists, "a")
				if len(ahref) == len(atitle):
					for i in range(0, len(ahref)):
						item = {}
						title = self.makeAscii(atitle[i])
						title = self.replaceHtmlCodes(title)
						item["Title"] = title
						item["artist_name"] = urllib.quote_plus(title)
						link = ahref[i]
						link = link[link.find("?a=") + 3:link.find("&")]
						item["artist"] = link
						item["icon"] = "music"
						item["scraper"] = "music_artist"
						item["thumbnail"] = "music"
						items.append(item)
		
		if self.__dbg__:
			print self.__plugin__ + " scrapeSimilarArtists done"
		return ( items, result["status"] )
		
	def scrapeMusicCategoryArtists(self, params={}):
		get = params.get
		if self.__dbg__:
			print self.__plugin__ + " scrapeMusicCategoryArtists"
			
		status = 200
		items = []
		
		if get("category"):
			category = urllib.unquote_plus(get("category"))
			url = self.urls["music"] + category
			result = self._fetchPage({"link":url})

			artists = self.parseDOM(result["content"], "div",  { "id": "artist-recs-container"})
			for artist in artists:
				ahref = self.parseDOM(artist, "a", { "title": ".*?" }, ret = "href")
				atitle = self.parseDOM(artist, "a", ret = "title")
				athumb = self.parseDOM(artist, "img", ret = "data-thumb")
				if len(atitle) == len(ahref) == len(athumb) and len(ahref) > 0:
					for i in range(0 , len(ahref)):
						item = {}
						title = self.makeAscii(atitle[i])
						title = self.replaceHtmlCodes(title)
						item["Title"] = title
						item["scraper"] = "music_artist"
						item["artist_name"] = urllib.quote_plus(title)
						link = ahref[i]
						link = link[link.find("?a=") + 3:link.find("&")]
						item["artist"] = link
						item["icon"] = "music"
						item["thumbnail"] = athumb[i]
						items.append(item)
		
		if self.__dbg__:
			print self.__plugin__ + " scrapeMusicCategoryArtists done"
		return (items, status)
	
	def scrapeMusicCategoryHits(self, params = {}):
		get = params.get
		if self.__dbg__:
			print self.__plugin__ + " scrapeMusicCategoryHits"
		
		status = 200
		items = []
		params["batch"] = "true"
		
		if get("category"):
			category = urllib.unquote_plus(get("category"))
			url = self.urls["music"] + category
			result = self._fetchPage({"link":url})
			
			content = self.parseDOM(result["content"], "li", { "class": "yt-uix-slider-slide-item "})
			
			for video in content:
				videoid = self.parseDOM(video, "a", attrs = {"class": "ux-thumb-wrap " }, ret = "href")
				videoid = videoid[0]
				videoid = videoid[videoid.find("?v=") + 3:videoid.find("&")]
				items.append(videoid)
		
		if self.__dbg__:
			print self.__plugin__ + " scrapeMusicCategoryHits done"		
		return (items, status)
	
	def searchDisco(self, params = {}):
		get = params.get
		if self.__dbg__:
			print self.__plugin__ + " searchDisco"
		
		items = []
		
		url = self.urls["disco_search"] % urllib.quote_plus(get("search"))
		result = self._fetchPage({"link": url})
		
		if (result["content"].find("list=") != -1):
			result["content"] = result["content"].replace("\u0026", "&")
			mix_list_id = result["content"][result["content"].find("list=") + 5:]
			if (mix_list_id.find("&") != -1):
				mix_list_id = mix_list_id[:mix_list_id.find("&")]
			elif (mix_list_id.find('"') != -1):
				mix_list_id = mix_list_id[:mix_list_id.find('"')]
			
			video_id = result["content"][result["content"].find("v=") + 2:]
			video_id = video_id[:video_id.find("&")]
			
			url = self.urls["disco_mix_list"] % (video_id, mix_list_id)
										
			result = self._fetchPage({"link": url})
			
			#list = SoupStrainer(name="div", id ="playlist-bar")
			#mix_list = BeautifulSoup(result["content"], parseOnlyThese=list)
			mix_list = self.parseDOM(result["content"], "div", { "id": "playlist-bar" }, ret = "data-video-ids")

			if (len(mix_list) > 0):
				items = mix_list[0].split(",")
		
		if self.__dbg__:
			print self.__plugin__ + " searchDisco done " 
		return ( items, result["status"])
	
	def scrapeDiscoTop50(self, params = {}):
		get = params.get		
		if self.__dbg__:
			print self.__plugin__ + " scrapeDiscoTop50"
			
		url = self.urls["disco_main"]
		result = self._fetchPage({"link": url})
		
		popular = self.parseDOM(result["content"], "a", { "id": "popular-tracks"})

		items = []		
		if (len(popular) > 0):
			videos = self.urls["main"] + popular[0]
			videos = videos.replace("&quot;",'"').strip()
			#print self.__plugin__ + " scrapeDiscoTop50 def : " + repr(videos)
			if (videos.find('"') > 0):# This never hits as far as i can see.
				#print self.__plugin__ + " scrapeDiscoTop50 def : " + repr(videos)
				videos = videos[videos.find('["')+2:videos.rfind("])")]
				videos = videos.replace('"',"")
				videos = videos.replace(" ","")
				items = videos.split(",")
		
		if self.__dbg__:
			print self.__plugin__ + " scrapeDiscoTop50 done : " + repr(items)
		return ( items, result["status"])
	
	def scrapeDiscoTopArtist(self, params = {}):
		get = params.get
		if self.__dbg__:
			print self.__plugin__ + " scrapeDiscoTopArtist"
		
		url = self.urls["disco_main"]
		result = self._fetchPage({"link":url})
		
		popular = self.parseDOM(result["content"], "div", { "class": "ytg-fl popular-artists"})
		yobjects = []
		if len(popular) > 0:
			artists = self.parseDOM(popular, "li", attrs = { "class": "popular-artist-row disco-search" }, ret = "data-artist-name")
			for artist in artists:
				item = {}
				title = self.makeAscii(artist)
				item["search"] = title
				item["Title"] = title
				
				params["thumb"] = "true"
				thumb = self.__storage__.retrieve(params, "thumbnail", item)
				if not thumb:
					item["thumbnail"] = "discoball"
				else:
					item["thumbnail"] = thumb
				
				item["path"] = get("path")
				item["scraper"] = "search_disco"
				yobjects.append(item)
				
		if self.__dbg__:
			print self.__plugin__ + " scrapeDiscoTopArtist done : " + repr(yobjects)
		return (yobjects, result["status"])

#=================================== Live ============================================
	def scrapeLiveNow(self, params = {}):
		get = params.get
		if self.__dbg__:
			print self.__plugin__ + " scrapeLiveNow"

		url = self.urls[get("scraper")]
		
		result = self._fetchPage({"link": url})
		
		live = self.parseDOM(result["content"], "div", { "id": "live-main"})
		live = self.parseDOM(live, "div", { "class": "browse-item ytg-box"})
		videos = []

		if len(live) > 0:
			live = "".join(live)
			ahref = self.parseDOM(live, "a", attrs = {"class": "live-video-title"}, ret = "href" )
			atitle = self.parseDOM(live, "a", attrs = {"class": "live-video-title"})
			athumb = self.parseDOM(live, "img", attrs = { "alt": "Thumbnail" }, ret = "src")
			astudio = self.parseDOM(live, "a", ret = "title")

			#print self.__plugin__ + " BLA BLA BTEST2 " + str(len(ahref)) +  " - " + str(len(atitle))  + " - " + str(len(athumb)) + " - " + str(len(astudio)) #+  " - " + str(len(result["content"])) + " - " + str(len(live))
			if len(ahref) == len(atitle) and len(ahref) == len(astudio) and len(ahref) == len(athumb):
				for i in range(0 , len(ahref)):
					item = {}
					videoid = ahref[i]
					videoid = videoid[videoid.rfind("/")+1:]
					item["videoid"] = videoid
					item["icon"] = "live"
					#thumbnail = self.urls["thumbnail"] % videoid
					thumbnail = athumb[i]
					thumbnail = thumbnail.replace("default","0")
					item["thumbnail"] = thumbnail
					title = "Unknown Title"

					title = atitle[i]
					item["Studio"] = astudio[i]
					item ["Title"] = title
					videos.append(item)
		
		if self.__dbg__:
			print self.__plugin__ + " scrapeLiveNow Done"
		return (videos, result["status"])
				
#=================================== User Scraper ============================================
	
	def scrapeRecommended(self, params = {}):
		get = params.get
		if self.__dbg__:
			print self.__plugin__ + " scrapeRecommended"
		
		url = self.urls[get("scraper")]
		result = self._fetchPage({"link": url, "login": "true"})
		
		videos = re.compile('<a href="/watch\?v=(.*)&amp;feature=grec_browse" class=').findall(result["content"]);
		
		if len(videos) == 0:
			videos = re.compile('<div id="reco-(.*)" class=').findall(result["content"]);
		
		if self.__dbg__:
			print self.__plugin__ + " scrapeRecommended done"
		return ( videos, result["status"] )

	def scrapeWatchLater(self, params):	
		get = params.get
		if self.__dbg__:
			print self.__plugin__ + " scrapeWatchLater"
		
		url = self.urls[get("scraper")]
		
		result = self._fetchPage({"link": url, "get_redirect":"true", "login": "true"})
		
		if result["status"] == 200:
			if result["content"].find("p=") > 0:
				result["content"] = result["content"][result["content"].find("p=") + 2:]
				playlist_id = result["content"][:result["content"].find("&")]
				params["user_feed"] = "playlist"
				params["login"] = "true"
				params["playlist"] = playlist_id
				if self.__dbg__:
					print self.__plugin__ + " scrapeWatchLater done"
				return self.__feeds__.list(params)
		
		if self.__dbg__:
			print self.__plugin__ + " scrapeWatchLater failed"
		return ([], 303)
	
	def scrapeLikedVideos(self, params):
		get = params.get
		if self.__dbg__:
			print self.__plugin__ + " scrapeLikedVideos"
		
		url = self.urls[get("scraper")]
		
		result = self._fetchPage({"link": url, "login": "true"})
		liked = self.parseDOM(result["content"], "div", { "id": "vm-video-list-container"})

		items = []
		
		if (len(liked) > 0):
			vidlist = self.parseDOM(liked, "li", { "class":" vm-video-item " }, ret = "id")
			for videoid in vidlist:
				videoid = videoid[videoid.rfind("video-") + 6:]
				items.append(videoid)
		
		if self.__dbg__:
			print self.__plugin__ + " scrapeLikedVideos done"
		return (items, result["status"])
			
#=================================== Shows ============================================
	def scrapeShowEpisodes(self, params = {}):
		get = params.get
		if self.__dbg__:
			print self.__plugin__ + " scrapeShowEpisodes: " + repr(params)
		
		url = self.createUrl(params)
		result = self._fetchPage({"link":url})
			
		videos = re.compile('<a href="/watch\?v=(.*)&amp;feature=sh_e_sl&amp;list=SL"').findall(result["content"])
			

		nexturl = self.parseDOM(result["content"], "button", { "class": " yt-uix-button" }, ret = "data-next-url")
		print "smoker "+ repr(nexturl)
		if (len(nexturl) > 0):
			nexturl = nexturl[0]
		else:
			nexturl = ""
		
		if nexturl.find("start=") > 0:
			fetch = True
			start = 20
			nexturl = nexturl.replace("start=20", "start=%s")
			while fetch:
				url = self.urls["main"] + nexturl % start
				result = self._fetchPage({"link":url})
				
				if result["status"] == 200:
					result["content"] = result["content"].replace("\\u0026","&")
					result["content"] = result["content"].replace("\\/","/")
					result["content"] = result["content"].replace('\\"','"')
					result["content"] = result["content"].replace("\\u003c","<")
					result["content"] = result["content"].replace("\\u003e",">")
					more_videos = re.compile('data-video-ids="([^"]*)"').findall(result["content"])
					
					if not more_videos:
						fetch = False
					else:
						videos += more_videos
						start += 20
		
		if self.__dbg__:
			print self.__plugin__ + " scrapeShowEpisodes done"
		return (videos, result["status"])
		
		# If the show contains more than one season the function will return a list of folder items,
		# otherwise a paginated list of video items is returned

	def scrapeShow(self, params = {}):
		get = params.get
		if self.__dbg__:
			print self.__plugin__ + " scrapeShow"
		
		url = self.createUrl(params)
		result = self._fetchPage({"link":url})
		
		if ((result["content"].find('class="seasons"') == -1) or get("season")):
			if self.__dbg__:
				print self.__plugin__ + " scrapeShow parsing videolist for single season"
			return self.scrapeShowEpisodes(params)
		
		params["folder"] = "true"
		del params["batch"]
		if self.__dbg__:
			print self.__plugin__ + " scrapeShow done"
		return self.scrapeShowSeasons(result["content"], params)
	
	def scrapeShowSeasons(self, html, params = {}): 
		get = params.get
		params["folder"] = "true"
		if self.__dbg__:
			print self.__plugin__ + " scrapeShowSeasons : " + repr(params)
		
		yobjects = []

		seasons = self.parseDOM(html, "div", attrs = {"class": "seasons"})
		if (len(seasons) > 0):
			params["folder"] = "true"

			season_list = self.parseDOM(seasons, "span", attrs = {"class": "yt-uix-button-content"})
			atitle = self.parseDOM(seasons, "button", attrs = { "type": "button" }, ret = "title")

			if len(season_list) == len(atitle) and len(atitle) > 0:
				for i in range(0, len(atitle)):
					item = {}
				
					season_id = season_list[i]
					title = self.__language__(30058) % season_id.encode("utf-8")
					title += " - " + atitle[i].encode("utf-8")
					item["Title"] = title
					item["season"] = season_id.encode("utf-8")
					item["thumbnail"] = "shows"
					item["scraper"] = "shows"
					item["icon"] = "shows"
					item["show"] = get("show")
					yobjects.append(item)
		
		if (len(yobjects) > 0):
			if self.__dbg__:
				print self.__plugin__ + " scrapeShowSeasons done"
			return ( yobjects, 200 )
		
		if self.__dbg__:
			print self.__plugin__ + " scrapeShowSeasons failed"
		return ([], 303)
	
	def scrapeShowsGrid(self, params = {}):
		get = params.get
		if self.__dbg__:
			print self.__plugin__ + " scrapeShowsGrid : " 
		
		next = "true"
		items = []
		page = 0
		
		while next == "true":
			next = "false"
			params["page"] = str(page)
			
			url = self.createUrl(params)
			result = self._fetchPage({"link":url})
			
			showcont = self.parseDOM(result["content"], "ul", { "class": "browse-item-list"})

			if (len(showcont) > 0):
				page += 1
				next = "true"
			showcont = "".join(showcont)

			shows = self.parseDOM(showcont, "div", { "class": "browse-item show-item yt-uix-hovercard " })

			for show in shows:
				ahref = self.parseDOM(show, "a", attrs = { "title": ".*?" }, ret = "href" )
				acont = self.parseDOM(show, "a", ret = "title" )
				athumb = self.parseDOM(show, "img", attrs = { "alt": "Thumbnail" }, ret = "src")
				acount = self.parseDOM(show, "span", { "class": "show-video-counts" })

				#print self.__plugin__ + " XXX " + str(len(ahref)) + " - " +  str(len(acont)) + " - " + str(len(athumb)) + " - " + str(len(acount)) + repr(show)
				if len(ahref) == len(acont) and len(ahref) == len(acount) and len(ahref) == len(athumb) and len(ahref) > 0:
					for i in range(0, len(ahref)):
						item = {}

						count = self.stripTags(acount[i].replace("\n", "").replace(",", ", "))
						title = acont[i] + " (" + count + ")"
						title = self.replaceHtmlCodes(title)
						item['Title'] = title
						
						show_url = ahref[i]
						if (show_url.find("?p=") > 0):
							show_url = show_url[show_url.find("?p=") + 1:]
						else :
							show_url = show_url.replace("/show/", "")
						show_url = urllib.quote_plus(show_url)
						item['show'] = show_url
						
						item['icon'] = "shows"
						item['scraper'] = "shows"
						thumbnail = athumb[i]
						if ( thumbnail.find("_thumb.") > 0):
							thumbnail = thumbnail.replace("_thumb.",".")
						else:
							thumbnail = "shows"
						
						item["thumbnail"] = thumbnail						
						items.append(item)
			del params["page"]
		
		if self.__dbg__:
			print self.__plugin__ + " scrapeShowsGrid done : "
		return (items, result["status"])


#=================================== Music ============================================

	def scrapeYouTubeTop100(self, params = {}):
		get = params.get
		if self.__dbg__:
			print self.__plugin__ + " scrapeYouTubeTop100"
		
		url = self.createUrl(params)
		result = self._fetchPage({"link": url})
		
		items = []
		if result["status"] == 200:
			items = re.compile('<a href="/watch\?v=(.*)&amp;feature=musicchart" class=').findall(result["content"]);
		
		if self.__dbg__:
			print self.__plugin__ + " scrapeYouTubeTop100 done"
		return (items, result["status"])
		
#=================================== Movies ============================================		

	def scrapeMovieSubCategory(self, params = {}):
		get = params.get
		if self.__dbg__:
			print self.__plugin__ + " scrapeMovieSubCategory : " + repr(params)
		
		url = self.createUrl(params)
		result = self._fetchPage({"link":url})
		
		ytobjects = []


		dom_pages = self.parseDOM(result["content"], "div", { "class": "yt-uix-slider-title"})
		for item in dom_pages:
			ahref = self.parseDOM(item, "a", ret = "href" )
			acont = self.parseDOM(item, "a")
			if len(ahref) == len(acont) and len(ahref) > 0:
				item = {}
				cat = ahref[0]
				title = acont[0].replace("&raquo;", "").strip()
				item['Title'] = title
				#print self.__plugin__ + " scrapeMovieSubCategory : " + cat
				cat = urllib.quote_plus(cat)
				#print self.__plugin__ + " scrapeMovieSubCategory : " + cat
				item['category'] = cat
				item['scraper'] = "movies"
				item["thumbnail"] = "movies"
				ytobjects.append(item)

		if self.__dbg__:
			print self.__plugin__ + " scrapeMovieSubCategory done"
		return (ytobjects, result["status"])

	
	def scrapeMoviesGrid(self, params = {}):
		get = params.get
		if self.__dbg__:
			print self.__plugin__ + " scrapeMoviesGrid"
		
		params["batch"] = "thumbnails"
		next = "true"
		items = []
		page = 0
		
		while next == "true":
			next = "false"
			params["page"] = str(page)
			
			url = self.createUrl(params)
			result = self._fetchPage({"link":url})
			
			dom_pages = self.parseDOM(result["content"], "div", attrs = {"class": "yt-uix-pager"})
			links = self.parseDOM("".join(dom_pages), "a", attrs = {"class": "yt-uix-pager-link" }, ret = "data-page")
			print self.__plugin__ + " scrapeMoviesGrid " + str(len(dom_pages)) + " - " + str(len(links))
			if len(links) > 0:
				for link in links:
					if int(link) > page:
						if self.__dbg__:
							print self.__plugin__ + " scrapeMoviesGrid - next page ? link: " + str(link) + " > page: " + str(page + 1)
						next = "true"

			dom_list = self.parseDOM(result["content"], "ul", { "class": "browse-item-list"})
			vidids = self.parseDOM(dom_list, "span", ret = "data-video-ids")
			thumbs = self.parseDOM(dom_list, "img", ret = "data-thumb")
			
			page += 1
			if len(vidids) == len(thumbs) and len(vidids) > 0:
				for i in range(0 , len(vidids)):
					items.append( (vidids[i], thumbs[i]) )
				
		del params["page"]
		if self.__dbg__:
			print self.__plugin__ + " scrapeMoviesGrid done : " + str(len(items))
		return (items, result["status"])

	
#================================== Common ============================================
	
	def getNewResultsFunction(self, params = {}):
		get = params.get
		
		function = ""	
		if (get("scraper") == "search_disco"):
			function = self.searchDisco
			params["batch"] = "true"
		if (get("scraper") == "liked_videos"):
			function = self.scrapeLikedVideos
			params["batch"] = "true"
		if (get("scraper") == "disco_top_50"):
			function = self.scrapeDiscoTop50
			params["batch"] = "true"
		if (get("scraper") == "recommended"):
			function = self.scrapeRecommended
			params["batch"] = "true"
		if (get("scraper") == "music_top100"):
			function = self.scrapeYouTubeTop100
			params["batch"] = "true"
		if (get("scraper") == "disco_top_artist"):
			function = self.scrapeDiscoTopArtist
			params["folder"] = "true"
		if (get("scraper") == "music_artist"):
			function = self.scrapeArtist
			params["batch"] = "true"
		if (get("scraper") in [ "latest_game_trailers", "latest_trailers"]):
			function = self.scrapeTrailersListFormat
		if (get("scraper") == "similar_artist"):
			function = self.scrapeSimilarArtists
			params["folder"] = "true"
		if (get("scraper") == "music_hits" or get("scraper") == "music_artists"):
			if get("category") and get("scraper") == "music_hits":
				function = self.scrapeMusicCategoryHits
			elif get("category") and get("scraper") == "music_artists":
				function = self.scrapeMusicCategoryArtists
			else:
				function = self.scrapeMusicCategories
		
		if (get("scraper") in ["categories", "movies", "shows"] and not get("category")):
			function = self.scrapeCategoryList
			params["folder"] = "true"

		if get("scraper") == "shows" and get("category"):
			params["folder"] = "true"
			function = self.scrapeShowsGrid
			
		if get("scraper") == "shows" and get("show"):
			del params["folder"]
			params["batch"] = "true"
			function = self.scrapeShow
			
		if get("scraper") == "movies" and get("category"):
			params["batch"] = "thumbnails"
			function = self.scrapeMoviesGrid		
			if get("subcategory"):
				params["folder"] = "true"
				del params["batch"]
				function = self.scrapeMovieSubCategory
		
		if get("scraper") == "categories" and get("category"):
			params["batch"] = "true"
			function = self.scrapeCategoriesGrid
		
		if (get("scraper") in ['current_trailers','game_trailers','popular_game_trailers','popular_trailers','trailers','upcoming_game_trailers','upcoming_trailers']):
			params["batch"] = "thumbnails"
			function = self.scrapeGridFormat
		
		if function:
			params["new_results_function"] = function
		
		return True
	
	def createUrl(self, params = {}):
		get = params.get
		page = str(int(get("page","0")) + 1)
		url = ""
		
		if (get("scraper") in self.urls):
			url = self.urls[get("scraper")]
			if url.find('%s') > 0:
				url = url % page
			elif url.find('?') > -1:
				url += "&p=" + page
			else:
				url += "?p=" + page
		
		if (get("scraper") == "categories"):
			if (get("category")):
				category = get("category")
				category = urllib.unquote_plus(category)
				category = category.replace("/videos", "")
				if (category.find("/") > -1):
					if category.find("?") > -1:
						url = self.urls["main"] + category + "&hl=en" + "&p=" + page
					else:
						url = self.urls["main"] + category + "?hl=en" + "&p=" + page
				else:
					if category.find("?") > -1:
						url = self.urls["main"] + "/categories" + category + "&hl=en" + "&p=" + page
					else:
						url = self.urls["main"] + "/categories" + category + "?hl=en" + "&p=" + page
			else:
				url = self.urls["categories"] + "?hl=en"
		
		if (get("scraper") == "shows"):
			url = self.urls["shows"] + "?hl=en"
			
			if (get("category")):
				category = get("category")
				category = urllib.unquote_plus(category)
				category = category.replace("/shows/", "")
				category = category.replace("/shows", "")
				url = self.urls["shows"] + "/" + category
				if category.find("?") > -1:
					url += "&p=" + page + "&hl=en"
				else:
					url += "?p=" + page + "&hl=en"
			
			if (get("show")):
				show = urllib.unquote_plus(get("show"))
				if (show.find("p=") < 0):
					url = self.urls["show_list"] + "/" + show + "?hl=en"
				else:
					url = self.urls["show_list"] + "?" + show + "&hl=en"
				if (get("season")):
					url = url + "&s=" + get("season")
				
		if (get("scraper") == "movies"):
			if (get("category")):
				category = get("category")
				category = urllib.unquote_plus(category)
				category = category.replace("/movies/", "") # indian
				category = category.replace("/movies", "") # Foreign
				if get("subcategory"):
					url = self.urls["main"] + "/movies/" + category + "?hl=en"
				else:
					if category.find("?") > -1:
						url = self.urls["main"] + "/movies/" + category + "&p=" + page + "&hl=en"
					else:
						url = self.urls["main"] + "/movies/" + category + "?p=" + page + "&hl=en"

			else:
				url = self.urls["movies"] + "?hl=en"
		
		if(get("scraper") == "music_top100"):
			url = self.urls["music"]
		
		return url
	
	def scrapeGridFormat(self, params = {}):
		get = params.get
		if self.__dbg__:
			print self.__plugin__ + " scrapeGridFormat"
		items = []
		next = "false"
		
		url = self.createUrl(params)
		result = self._fetchPage({"link":url})
		
		if result["status"] == 200:
			pagination = self.parseDOM(result["content"], "div", { "class": "yt-uix-pager"})
	
			if (len(pagination) > 0):
				tmp = str(pagination)
				if (tmp.find("Next") > 0):
					next = "true"
			
			
			trailers = self.parseDOM(result["content"], "div", attrs = { "id": "popular-column" })
			
			if len(trailers) > 0:
				ahref = self.parseDOM(result["content"], "a", attrs = { "class": "ux-thumb-wrap " }, ret = "href")
				if len(ahref) == 0:
					ahref = self.parseDOM(trailers, "a", attrs = { "class": "ux-thumb-wrap contains-addto" }, ret = "href")
				
				athumbs = self.parseDOM(trailers, "a", attrs = { "class": "ux-thumb-wrap "})
				if len(athumbs) == 0:
					athumbs = self.parseDOM(trailers, "a", attrs = { "class": "ux-thumb-wrap contains-addto"})
				for i in range(0 , len(ahref)):
					videoid = ahref[i] 
						
					if (videoid):
						if (videoid.find("=") > -1):
							videoid = videoid[videoid.find("=")+1:]
					thumb = self.parseDOM(athumbs[i], "img", attrs = { "alt": "Thumbnail"}, ret = "src")
					if len(thumb) > 0:
						thumb = thumb[0]
					items.append((videoid, thumb))
		
		if self.__dbg__:
			print self.__plugin__ + " scrapeGridFormat done " 
		return (items, result["status"]) 
	
	def scrapeCategoryList(self, params = {}):
		get = params.get
		if self.__dbg__:
			print self.__plugin__ + " scrapeCategoryList : "
		
		scraper = "categories"
		thumbnail = "explore"
		yobjects = []
		
		if (get("scraper") != "categories"):
			scraper = get("scraper")
			thumbnail = get("scraper")
		
		url = self.createUrl(params)
		result = self._fetchPage({"link":url})
		
		if result["status"] == 200:
			categories = self.parseDOM(result["content"], "div", attrs = {"class": "yt-uix-expander-body.*?"})
			if len(categories) == 0:
				categories = self.parseDOM(result["content"], "div", attrs = {"id": "browse-filter-menu"})

			if len(categories) == 0: # <- is this needed. Anyways. it breaks. fix that..
				categories = self.parseDOM(result["content"], "div", attrs = {"class": "browse-filter-menu.*?"})
			
			for cat in categories:
				print self.__plugin__ + " scrapeCategoryList : " + cat[0:50]
				ahref = self.parseDOM(cat, "a", ret = "href")
				acontent = self.parseDOM(cat, "a")
				for i in range(0 , len(ahref)):
					item = {}
					title = acontent[i]
					title = title.replace("&amp;", "&")
					if title == "All Categories" or title == "Education" or title == "":
						continue
					item['Title'] = title

					cat = ahref[i].replace("/" + scraper + "/", "")

					if get("scraper") == "categories":
						if title == "Music":
							continue
						if cat.find("comedy") > 0:
							cat = "?c=23"
						if cat.find("gaming") > 0:
							cat = "?c=20"
						if cat.find("education") > 0:
							item["subcategory"] = "true"

					if get("scraper") == "movies":
						if cat.find("pt=nr") > 0:
							continue
						elif cat.find("indian-cinema") > -1 or cat.find("foreign-film") > -1:
							item["subcategory"] = "true"	
						
					cat = urllib.quote_plus(cat)
					item['category'] = cat
					item['scraper'] = scraper
					item["thumbnail"] = thumbnail
					yobjects.append(item)
		
			if (not yobjects):
				if self.__dbg__:
					print self.__plugin__ + " scrapeCategoryList failed"
				return (self.__language__(30601), 303)
		
		if self.__dbg__:
			print self.__plugin__ + " scrapeCategoryList done"
		return (yobjects, result["status"])

	
	def paginator(self, params = {}):
		get = params.get
		
		status = 303
		result = []
		next = 'false'
		page = int(get("page", "0"))
		per_page = ( 10, 15, 20, 25, 30, 40, 50, )[ int( self.__settings__.getSetting( "perpage" ) ) ]
				
		if not get("page"):
			(result, status) = params["new_results_function"](params)
			
			if self.__dbg__:
				print self.__plugin__ + " paginator new result " + str(repr(result))[0:50]
			
			if len(result) == 0:
				if get("scraper") not in ["music_top100"]:
					return (result, 303)
				result = self.__storage__.retrieve(params)
			else:
				self.__storage__.store(params, result)
		else:
			result = self.__storage__.retrieve(params)
			if len(result) > 0:
				status = 200
		
		if not get("folder") or (get("scraper") == "shows" and get("category")):
			if ( per_page * ( page + 1 ) < len(result) ):
				next = 'true'
			
			if (get("fetch_all") != "true"):
				result = result[(per_page * page):(per_page * (page + 1))]
			if len(result) == 0:
				return (result, status)
		
		if get("batch") == "thumbnails":
			(result, status) = self.getBatchDetailsThumbnails(result, params)
		elif get("batch"):
			(result, status) = self.getBatchDetails(result, params)
		
		if get("batch"):
			del params["batch"]
		
		if not get("page") and (get("scraper") == "search_disco" or get("scraper") == "music_artist"):
			thumbnail = result[0].get("thumbnail")
			self.__storage__.store(params, thumbnail, "thumbnail")
		
		if next == "true":
			self.addNextFolder(result, params)
		
		return (result, status)
	
	def scrape(self, params = {}):
		get = params.get
		
		if (get("scraper") == "watch_later"):
			return self.scrapeWatchLater(params)
		
		self.getNewResultsFunction(params)
		
		return self.paginator(params)
	
if __name__ == '__main__':
	sys.exit(0)
