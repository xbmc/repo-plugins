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

import sys, urllib

class YouTubeScraper():	
	
	urls = {}
	urls['current_trailers'] = "http://www.youtube.com/trailers?s=trit&p=%s&hl=en"
	urls['disco_main'] = "http://www.youtube.com/disco" 
	urls['disco_mix_list'] = "http://www.youtube.com/watch?v=%s&feature=disco&playnext=1&list=%s"
	urls['disco_search'] = "http://www.youtube.com/disco?action_search=1&query=%s"
	urls['game_trailers'] = "http://www.youtube.com/trailers?s=gtcs"
	urls['main'] = "http://www.youtube.com"
	urls['movies'] = "http://www.youtube.com/ytmovies"
	urls['popular_game_trailers'] = "http://www.youtube.com/trailers?s=gtp&p=%s&hl=en"
	urls['popular_trailers'] = "http://www.youtube.com/trailers?s=trp&p=%s&hl=en"
	urls['show_list'] = "http://www.youtube.com/show"
	urls['shows'] = "http://www.youtube.com/shows"
	urls['trailers'] = "http://www.youtube.com/trailers?s=tr"
	urls['latest_trailers'] = "http://www.youtube.com/trailers?s=tr"
	urls['latest_game_trailers'] = "http://www.youtube.com/trailers?s=gtcs"
	urls['upcoming_game_trailers'] = "http://www.youtube.com/trailers?s=gtcs&p=%s&hl=en"
	urls['upcoming_trailers'] = "http://www.youtube.com/trailers?s=tros&p=%s&hl=en"
	urls['liked_videos'] = "http://www.youtube.com/my_liked_videos"
	urls['music'] = "http://www.youtube.com/music"
	urls['artist'] = "http://www.youtube.com/artist?a=%s&feature=artist"
	urls['education'] = "http://www.youtube.com/education"
	urls['education_category'] = "http://www.youtube.com/education?category=%s"
	urls['playlist'] = "http://www.youtube.com/view_play_list?p=%s"
	
	def __init__(self):
		self.settings = sys.modules[ "__main__" ].settings
		self.language = sys.modules[ "__main__" ].language
		self.plugin = sys.modules[ "__main__"].plugin
		self.dbg = sys.modules[ "__main__" ].dbg

		self.utils =  sys.modules[ "__main__" ].utils
		self.core = sys.modules["__main__" ].core
		self.common = sys.modules[ "__main__" ].common
		self.cache = sys.modules[ "__main__" ].cache
		
			
		self.feeds = sys.modules[ "__main__" ].feeds
		self.storage = sys.modules[ "__main__" ].storage
			
#=================================== Trailers ============================================
	def scrapeTrailersListFormat (self, params = {}):
		get = params.get
		self.common.log("")
		
		url = self.createUrl(params)
		result = self.core._fetchPage({"link":url})
		
		trailers = self.common.parseDOM(result["content"], "div", attrs = { "id": "recent-trailers-container"})
		
		items = []
		if (len(trailers) > 0):
			ahref = self.common.parseDOM(trailers, "a", attrs = {"class": " yt-uix-hovercard-target", "id": ".*?" }, ret = "href")
			
			athumbs = self.common.parseDOM(trailers, "img", attrs = { "alt": "Thumbnail" }, ret = "data-thumb")
			
			videos = self.utils.extractVID(ahref)
			
			for index, videoid in enumerate(videos):
				items.append((videoid, athumbs[index]))
				
		self.common.log("Done")
		return (items, result["status"])
		
	def scrapeTrailersGridFormat(self, params = {}):
		get = params.get
		self.common.log("")
		items = []
		next = True
		page = 0 
		
		while next:
			params["page"] = str(page)
			url = self.createUrl(params)
			result = self.core._fetchPage({"link":url})
			
			page += 1
			
			next = False
			if result["status"] == 200:
				pagination = self.common.parseDOM(result["content"], "div", { "class": "yt-uix-pager"})
				if (len(pagination) > 0):
					tmp = str(pagination)
					if (tmp.find("Next") > 0):
						next = True
				
				trailers = self.common.parseDOM(result["content"], "div", attrs = { "id": "popular-column" })
				
				if len(trailers) > 0:
					ahref = self.common.parseDOM(trailers, "a", attrs = { "class": 'ux-thumb-wrap.*?' }, ret = "href")
					
					athumbs = self.common.parseDOM(trailers, "a", attrs = { "class": "ux-thumb-wrap.*?"})
					
					videos = self.utils.extractVID(ahref)
					
					for index, videoid in enumerate(videos):
						thumb = self.common.parseDOM(athumbs[index], "img", attrs = { "alt": "Thumbnail"}, ret = "data-thumb")
						if len(thumb) > 0:
							thumb = thumb[0]
						
						items.append((videoid, thumb))
		
		del params["page"]
		self.common.log("Done")
		return (items, result["status"])
		
#=================================== Music  ============================================
	def scrapeMusicCategories(self, params = {}):
		get = params.get
		self.common.log("")
		
		items = []
		
		url = self.createUrl(params)
		result = self.core._fetchPage({"link": url})
		
		if result["status"] == 200:
			categories = self.common.parseDOM(result["content"], "div", attrs = { "id": "browse-filter-menu"})
			ahref = self.common.parseDOM(categories, "a", ret= "href")
			acontent = self.common.parseDOM(categories, "a")

			if len(acontent) == len(ahref) and len(ahref) > 0:
				for i in range(0 , len(ahref)):
					item = {}
					title = self.common.makeAscii(acontent[i])
					title = self.common.replaceHtmlCodes(title)
					link = ahref[i].replace("/music/","/")
					item["Title"] = title
					item["category"] = urllib.quote_plus(link)
					item["icon"] = "music"
					item["thumbnail"] = "music"
					item["scraper"] = get("scraper")
					if get("scraper") == "music_artists":
						item["folder"] = "true"
						
					items.append(item)

		self.common.log("Done")
		return (items, result["status"]) 

	
	def scrapeArtist(self, params = {}):
		get = params.get
		self.common.log("")
		
		result = {"status":303}
		
		items = []
		
		if get("artist") and get("artist_name"):
			self.storage.saveStoredArtist(params)
		
		if get("artist"):
			url = self.createUrl(params)
			result = self.core._fetchPage({"link": url})
			
			if result["status"] == 200:
				videos = self.common.parseDOM(result["content"], "a", attrs = { "href": ".*feature=artist" }, ret = "href")
				videos = self.utils.extractVID(videos)
		
			for v in videos:
				if v not in items:
					items.append(v)
		
		self.common.log("Done")
		return ( items, result["status"] )
	
	def scrapeSimilarArtists(self, params = {}):
		get = params.get
		self.common.log("")
		
		items = []
		if get("artist"):
			url = self.createUrl(params)
			result = self.core._fetchPage({"link": url})
			
			if result["status"] == 200:
				artists = self.common.parseDOM(result["content"], "div", { "id": "similar-artists"});
				ahref = self.common.parseDOM(artists, "a", ret = "href")
				atitle = self.common.parseDOM(artists, "a")
				if len(ahref) == len(atitle):
					for i in range(0, len(ahref)):
						item = {}
						title = self.common.makeAscii(atitle[i])
						title = self.common.replaceHtmlCodes(title)
						item["Title"] = title
						item["artist_name"] = urllib.quote_plus(title)
						link = ahref[i]
						link = link[link.find("?a=") + 3:link.find("&")]
						item["artist"] = link
						item["icon"] = "music"
						item["scraper"] = "music_artist"
						item["thumbnail"] = "music"
						items.append(item)
		
		self.common.log("Done")
		return ( items, result["status"] )
		
	def scrapeMusicCategoryArtists(self, params={}):
		get = params.get
		self.common.log("")
			
		status = 200
		items = []
		
		if get("category"):
			url = self.createUrl(params) 
			result = self.core._fetchPage({"link":url})
			
			artist_container = self.common.parseDOM(result["content"], "div", attrs = { "id": "artist-recs-container"})
			artists = self.common.parseDOM(artist_container, "div",  { "class": "artist-recommendation .*?"})

			for artist in artists:
				div = self.common.parseDOM(artist, "div", attrs = { "class": "browse-item-content" })
				ahref = self.common.parseDOM(div, "a", ret = "href")[0]
				atitle = self.common.parseDOM(div, "a", ret = "title")[0]
				athumb = self.common.parseDOM(artist, "img", ret = "data-thumb")[0]
				
				item = {}
				title = self.common.makeAscii(atitle)
				title = self.common.replaceHtmlCodes(title)
				item["Title"] = title
				item["scraper"] = "music_artist"
				item["artist_name"] = urllib.quote_plus(title)
				link = ahref
				link = link[link.find("?a=") + 3:link.find("&")]
				item["artist"] = link
				item["icon"] = "music"
				item["thumbnail"] = athumb
				items.append(item)
		
		self.common.log("Done")
		return (items, status)
	
	def scrapeMusicCategoryHits(self, params = {}):
		get = params.get
		self.common.log("")
		
		status = 200
		items = []
		params["batch"] = "true"
		
		if get("category"):
			category = urllib.unquote_plus(get("category"))
			url = self.createUrl(params)
			result = self.core._fetchPage({"link":url})
			
			container = self.common.parseDOM(result["content"], "div", { "id": "music-guide-container"})
			content = self.common.parseDOM(container, "a", attrs = {"class": "ux-thumb-wrap.*?" }, ret = "href")
			items = self.utils.extractVID(content)

		self.common.log("Done")
		return (items, status)
	
	def searchDisco(self, params = {}):
		get = params.get
		self.common.log("")
		
		items = []
		
		url = self.createUrl(params)
		result = self.core._fetchPage({"link": url})
		
		if (result["content"].find("list=") != -1):
			result["content"] = result["content"].replace("\u0026", "&")
			mix_list_id = result["content"][result["content"].find("list=") + 5:]
			if (mix_list_id.find("&") != -1):
				mix_list_id = mix_list_id[:mix_list_id.find("&")]
			elif (mix_list_id.find('"') != -1):
				mix_list_id = mix_list_id[:mix_list_id.find('"')]
			params["mix_list_id"] = mix_list_id
			
			video_id = result["content"][result["content"].find("v=") + 2:]
			params["disco_videoid"] = video_id[:video_id.find("&")]
			
			url = self.createUrl(params)
			result = self.core._fetchPage({"link": url})
			
			mix_list = self.common.parseDOM(result["content"], "div", { "id": "playlist-bar" }, ret = "data-video-ids")
			
			if (len(mix_list) > 0):
				items = mix_list[0].split(",")
		
		self.common.log("Done")
		return ( items, result["status"])
	
	def scrapeDiscoTopArtist(self, params = {}):
		get = params.get
		self.common.log("")
		
		url = self.createUrl(params)
		result = self.core._fetchPage({"link":url})
		
		popular = self.common.parseDOM(result["content"], "div", { "class": "ytg-fl popular-artists"})
		yobjects = []
		if len(popular) > 0:
			artists = self.common.parseDOM(popular, "li", attrs = { "class": "popular-artist-row disco-search" }, ret = "data-artist-name")
			for artist in artists:
				item = {}
				title = self.common.makeAscii(artist)
				item["search"] = title
				item["Title"] = title
				
				params["thumb"] = "true"
				thumb = self.storage.retrieve(params, "thumbnail", item)
				if not thumb:
					item["thumbnail"] = "discoball"
				else:
					item["thumbnail"] = thumb
				
				item["path"] = get("path")
				item["scraper"] = "search_disco"
				yobjects.append(item)
				
		self.common.log("Done : " + repr(yobjects))
		return (yobjects, result["status"])
				
#=================================== Eduction ============================================
	def scrapeEducationCategories(self, params = {}):
		get = params.get
		self.common.log("")

		url = self.createUrl(params)
		result = self.core._fetchPage({"link": url})
		
		categories = self.common.parseDOM(result["content"], "div", { "id": "browse-filter-menu-0"})
		items = []

		if len(categories) > 0:
			ahref = self.common.parseDOM(categories, "a", ret = "href" )
			atitle = self.common.parseDOM(categories, "a" )

			for i in range(0 , len(ahref)):
				item = {}

				item['Title'] = atitle[i]
				show_url = ahref[i]
				show_url = show_url.replace("/education?category=", "")
				show_url = urllib.quote_plus(show_url).replace("%25", "%")
				item['category'] = show_url
				item['icon'] = "feeds"
				item['scraper'] = "education"

				items.append(item)
		
		self.common.log("Done")
		return (items, result["status"])

	def scrapeEducationSubCategories(self, params = {}):
		get = params.get
		self.common.log("")

		url = self.createUrl(params)
		result = self.core._fetchPage({"link": url})
		
		categories = self.common.parseDOM(result["content"], "div", { "id": "browse-filter-menu-1"})
		items = []

		if len(categories) > 0:
			ahref = self.common.parseDOM(categories, "a", ret = "href" )
			atitle = self.common.parseDOM(categories, "a" )
			
			item = {}

			item['Title'] = self.common.replaceHtmlCodes(atitle[0])
			item['Title'] = "Videos"
			show_url = ahref[0]
			show_url = show_url.replace("/education?category=", "")
			show_url = urllib.quote_plus(show_url).replace("%25", "%")
			if show_url == "":
				show_url = get("category")
			item['videos'] = show_url
			item['icon'] = "feeds"
			item['scraper'] = "education"
				
			items.append(item)

			item = {}
			item['Title'] = self.common.replaceHtmlCodes(atitle[0])
			item['Title'] = "Courses"
			show_url = ahref[0]
			show_url = show_url.replace("/education?category=", "")
			show_url = urllib.quote_plus(show_url)
			if show_url == "":
				show_url = get("category")
			item['courses'] = show_url
			item['icon'] = "feeds"
			item['scraper'] = "education"
				
			items.append(item)
			for i in range(1 , len(ahref)):
				item = {}

				item['Title'] = self.common.replaceHtmlCodes(atitle[i])
				show_url = ahref[i]
				show_url = show_url.replace("/education?category=", "")
				show_url = urllib.quote_plus(show_url).replace("%25", "%")
				if show_url.count("%2F") > 1:
					item["courses"] = show_url
				else:
					item['category'] = show_url
				item['icon'] = "feeds"
				item['scraper'] = "education"

				items.append(item)
		
		self.common.log("Done : " + repr(items))
		return (items, result["status"])

	def scrapeEducationCourses(self, params = {}):
		get = params.get
		self.common.log("")
		
		url = self.createUrl(params)
		result = self.core._fetchPage({"link":url})

		next = "false"
		pagination = self.common.parseDOM(result["content"], "div", attrs = { "class": "yt-uix-pager"})

		if (len(pagination) > 0):
			tmp = str(pagination)
			if (tmp.find("Next") > 0):
				next = "true"

		categories = self.common.parseDOM(result["content"], "div", { "class": "playlist-extra-thumb-outer "})
		if len(categories) == 0:
			categories = self.common.parseDOM(result["content"], "div", { "class": "ytg-fl browse-content"})

		items = []
		if len(categories) > 0:
			ahref = self.common.parseDOM(categories, "a", attrs = { "href": "/course.*?", "title": ".*?" }, ret = "href" )
			atitle = self.common.parseDOM(result["content"], "a", attrs = { "href": "/course.*?" }, ret = "title" )
			athumb = self.common.parseDOM(categories, "img", attrs = { "alt": "Thumbnail" }, ret = "data-thumb")

			item = {}

			item['Title'] = "Videos"
			item['videos'] = get("courses")
			item['icon'] = "feeds"
			item['scraper'] = "education"
			
			items.append(item)

			for i in range(1 , len(ahref)):
				item = {}

				item['Title'] = self.common.replaceHtmlCodes(atitle[i])
				show_url = ahref[i]
				show_url = show_url.replace("/education?category=", "")
				if (show_url.find("list=") != -1):
					show_url = show_url[show_url.find("list=") + 5:]
				if (show_url.find("&") > 0):
					show_url = show_url[:show_url.find("&")]
				item['playlist'] = show_url
				item['icon'] = "feeds"
				item['scraper'] = "education"
				item["thumbnail"] = athumb[i]
				if item["thumbnail"].find("//") == 0:
					item["thumbnail"] = "http:" + item["thumbnail"]
				items.append(item)
				
		self.common.log("Done : " + repr(items))
		return (items, result["status"])

	def scrapeEducationVideos(self, params = {}):
		get = params.get
		self.common.log("")
		
		url = self.createUrl(params)
		result = self.core._fetchPage({"link":url})

		next = "false"
		pagination = self.common.parseDOM(result["content"], "div", attrs = { "class": "yt-uix-pager"})

		if (len(pagination) > 0):
			tmp = str(pagination)
			if (tmp.find("Next") > 0):
				next = "true"

		categories = self.common.parseDOM(result["content"], "li", attrs = { "class": " yt-uix-expander"})
		if len(categories) == 0:
			categories = self.common.parseDOM(result["content"], "div", attrs = { "class": "ytg-fl browse-content"})

		if len(categories) == 0:
			categories = self.common.parseDOM(result["content"], "li", attrs = { "class": "video"})
			
		items = []

		if len(categories) > 0:
			ahref = self.common.parseDOM(categories, "a", attrs = { "class": "ux-thumb-wrap contains-addto"}, ret = "href")
			if len(ahref) == 0:
				ahref = self.common.parseDOM(categories, "a", attrs = { "class": "tile-link-block video-tile.*?"}, ret = "href")
			
			links = self.utils.extractVID(ahref)
			items.extend(links)

		self.common.log("Done")
		return (items, result["status"])
				
#=================================== User Scraper ============================================
	
	def scrapeLikedVideos(self, params):
		get = params.get
		self.common.log("")
		
		url = self.createUrl(params)
		
		result = self.core._fetchPage({"link": url, "login": "true"})
		liked = self.common.parseDOM(result["content"], "div", { "id": "vm-video-list-container"})

		items = []
		
		if (len(liked) > 0):
			vidlist = self.common.parseDOM(liked, "li", { "class":" vm-video-item " }, ret = "id")
			for videoid in vidlist:
				videoid = videoid[videoid.rfind("video-") + 6:]
				items.append(videoid)
		
		self.common.log("Done")
		return (items, result["status"])
			
#=================================== Shows ============================================
	def scrapeShowEpisodes(self, params = {}):
		get = params.get
		self.common.log(repr(params))
		
		url = self.createUrl(params)
		result = self.core._fetchPage({"link":url})
		
		videos = self.common.parseDOM(result["content"], "div", attrs = { "class": "show-season-videos" } )
		videos = self.common.parseDOM(videos, "button", ret = "data-video-ids")
		
		nexturl = self.common.parseDOM(result["content"], "button", { "class": " yt-uix-button" }, ret = "data-next-url")
		
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
				result = self.core._fetchPage({"link":url})
				
				if result["status"] == 200:
					result["content"] = result["content"].replace("\\u0026","&")
					result["content"] = result["content"].replace("\\/","/")
					result["content"] = result["content"].replace('\\"','"')
					result["content"] = result["content"].replace("\\u003c","<")
					result["content"] = result["content"].replace("\\u003e",">")
					more_videos = self.common.parseDOM(result["content"], "button", ret = "data-video-ids")
					
					if not more_videos:
						fetch = False
					else:
						videos += more_videos
						start += 20
		
		self.common.log("Done")
		return (videos, result["status"])
		
		# If the show contains more than one season the function will return a list of folder items,
		# otherwise a paginated list of video items is returned

	def scrapeShow(self, params = {}):
		get = params.get
		self.common.log("")
		
		url = self.createUrl(params)
		result = self.core._fetchPage({"link":url})
		
		if ((result["content"].find('class="seasons "') == -1) or get("season")):
			self.common.log("scrapeShow parsing videolist for single season")
			return self.cache.cacheFunction(self.scrapeShowEpisodes, params)
		
		params["folder"] = "true"
		del params["batch"]
		self.common.log("Done")
		return self.cache.cacheFunction(self.scrapeShowSeasons, result["content"], params)
	
	def scrapeShowSeasons(self, html, params = {}): 
		get = params.get
		params["folder"] = "true"
		self.common.log("scrapeShowSeasons : " + repr(params))
		
		yobjects = []
		
		seasons = self.common.parseDOM(html, "div", attrs = {"class": "seasons "})
		if (len(seasons) > 0):
			params["folder"] = "true"
			
			season_list = self.common.parseDOM(seasons, "button", attrs = { "type": "button" }, ret = "data-season-number")
			
			print repr(season_list)
			atitle = self.common.parseDOM(seasons, "button", attrs = { "type": "button" }, ret = "title")

			if len(season_list) == len(atitle) and len(atitle) > 0:
				for i in range(0, len(atitle)):
					item = {}
					
					season_id = season_list[i] 
					title = self.language(30058) % season_id.encode("utf-8")
					title += " - " + atitle[i].encode("utf-8")
					item["Title"] = title
					item["season"] = season_id.encode("utf-8")
					item["thumbnail"] = "shows"
					item["scraper"] = "shows"
					item["icon"] = "shows"
					item["show"] = get("show")
					yobjects.append(item)
		
		if (len(yobjects) > 0):
			self.common.log("Done")
			return ( yobjects, 200 )
		
		self.common.log("Failed")
		return ([], 303)
	
	def scrapeShowsGrid(self, params = {}):
		get = params.get
		self.common.log("")
		
		next = "true"
		items = []
		page = 0
		
		while next == "true":
			next = "false"
			params["page"] = str(page)
			
			url = self.createUrl(params)
			result = self.core._fetchPage({"link":url})
			
			showcont = self.common.parseDOM(result["content"], "ul", { "class": "browse-item-list"})

			showcont = "".join(showcont)
			
			shows = self.common.parseDOM(showcont, "div", { "class": "browse-item show-item.*?" })
			if (len(shows) > 0):
				page += 1
				next = "true"
			
			for show in shows:
				ahref = self.common.parseDOM(show, "a", attrs = { "title": ".*?" }, ret = "href" )
				acont = self.common.parseDOM(show, "a", ret = "title" )
				athumb = self.common.parseDOM(show, "img", attrs = { "alt": "Thumbnail" }, ret = "src")
				acount = self.common.parseDOM(show, "span", { "class": "show-video-counts" })

				#self.common.log("XXX " + str(len(ahref)) + " - " +  str(len(acont)) + " - " + str(len(athumb)) + " - " + str(len(acount)) + repr(show))
				if len(ahref) == len(acont) and len(ahref) == len(acount) and len(ahref) == len(athumb) and len(ahref) > 0:
					for i in range(0, len(ahref)):
						item = {}

						count = self.common.stripTags(acount[i].replace("\n", "").replace(",", ", "))
						title = acont[i] + " (" + count + ")"
						title = self.common.replaceHtmlCodes(title)
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
		
		self.common.log("Done")
		print "funky : " + repr(items)
		return (items, result["status"])


#=================================== Music ============================================

	def scrapeYouTubeTop100(self, params = {}):
		get = params.get
		self.common.log("")
		
		url = self.createUrl(params)
		result = self.core._fetchPage({"link": url})
		
		
		items = []
		if result["status"] == 200:
			videos = self.common.parseDOM(result["content"], "div", attrs = {"id":'weekly-hits'})
			items = self.common.parseDOM(videos, "button", attrs = { "type":"button", "class":"addto-button.*?" }, ret = "data-video-ids")
		self.common.log("Done")
		return (items, result["status"])
		
#=================================== Movies ============================================		

	def scrapeMovieSubCategory(self, params = {}):
		get = params.get
		self.common.log("scrapeMovieSubCategory : " + repr(params))
		
		url = self.createUrl(params)
		result = self.core._fetchPage({"link":url})
		
		ytobjects = []


		dom_pages = self.common.parseDOM(result["content"], "div", { "class": "yt-uix-slider-title"})
		for item in dom_pages:
			ahref = self.common.parseDOM(item, "a", ret = "href" )
			acont = self.common.parseDOM(item, "a")
			if len(ahref) == len(acont) and len(ahref) > 0:
				item = {}
				cat = ahref[0]
				title = acont[0].replace("&raquo;", "").strip()
				item['Title'] = self.common.replaceHtmlCodes(title)
				cat = urllib.quote_plus(cat)
				item['category'] = cat
				item['scraper'] = "movies"
				item["thumbnail"] = "movies"
				ytobjects.append(item)

		self.common.log("Done")
		return (ytobjects, result["status"])

	
	def scrapeMoviesGrid(self, params = {}):
		get = params.get
		self.common.log("")
		
		next = "true"
		items = []
		page = 0
		
		while next == "true":
			next = "false"
			params["page"] = str(page)
			
			url = self.createUrl(params)
			result = self.core._fetchPage({"link":url})
			
			pagination = self.common.parseDOM(result["content"], "div", attrs = { "class": "yt-uix-pager"})

			if (len(pagination) > 0):
				tmp = str(pagination)
				if (tmp.find("Next") > 0):
					next = "true"
						
			videoids = self.common.parseDOM(result["content"], "button", { "class": "addto-button.*?"}, ret = "data-video-ids")
			thumbs = self.common.parseDOM(result["content"], "img", attrs = { "alt": "Thumbnail" }, ret = "data-thumb")
			
			page += 1
			if len(videoids) == len(thumbs) and len(videoids) > 0:
				for i in range(0 , len(videoids)):
					items.append( (videoids[i], thumbs[i]) )
		
		del params["page"]
		print repr(items)
		self.common.log("Done : " + str(len(items)))
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
		if (get("scraper") == "music_top100"):
			function = self.scrapeYouTubeTop100
			params["batch"] = "true"
		if (get("scraper") == "disco_top_artist"):
			function = self.scrapeDiscoTopArtist
			params["folder"] = "true"
		if (get("scraper") == "music_artist"):
			function = self.scrapeArtist
			params["batch"] = "true"
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
		
		if (get("scraper") in ["movies", "shows"] and not get("category")):
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
			if get("subcategory"):
				params["folder"] = "true"
				function = self.scrapeMovieSubCategory
			else:
				params["batch"] = "thumbnails"
				function = self.scrapeMoviesGrid
		
		if get("scraper") == "education":
			params["folder"] = "true"
			function = self.scrapeEducationCategories
			if ( get("category")):
				function = self.scrapeEducationSubCategories
			if ( get("courses") ):
				function = self.scrapeEducationCourses
			if ( get("playlist") or  get("videos") ):
				params["batch"] = "true"
				del params["folder"] 
				function = self.scrapeEducationVideos
				
		if (get("scraper") in ['current_trailers','game_trailers','popular_game_trailers','popular_trailers','trailers','upcoming_game_trailers','upcoming_trailers']):
			params["batch"] = "thumbnails"
			function = self.scrapeTrailersGridFormat
		if (get("scraper") in [ "latest_game_trailers", "latest_trailers"]):
			params["batch"] = "thumbnails"
			function = self.scrapeTrailersListFormat
				
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
		
		if (get("scraper") == "education"):
			url = self.urls["education"]
			if get("category"):
				url = self.urls["education_category"] % get("category")
			if get("subcategory"):
				url = self.urls["education_category"] % get("subcategory")
			if get("videos"):
				url = self.urls["education_category"] % get("videos")
			if get("courses"):
				url = self.urls["education_category"] % get("courses")
			if get("playlist"):
				url = self.urls["playlist"] % get("playlist")
			
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
		
		if get("scraper") in ["music_artists", "music_artist", "similar_artist", "music_hits", "music_top100"]: 
			url = self.urls["music"]
			if get("category"):
				url = self.urls["music"] + urllib.unquote_plus(get("category"))
			
			if get("artist"):
				url = self.urls["artist"] % get("artist")
				
		if (get("scraper") in "search_disco"):
			url = self.urls["disco_search"] % urllib.quote_plus(get("search"))
			if get("mix_list_id") and get("disco_videoid"):
				url = self.urls["disco_mix_list"] % (get("disco_videoid"), get("mix_list_id"))
		if (get("scraper") == "disco_top_artist"):
			url = self.urls["disco_main"]
		
		return url
	
	def scrapeCategoryList(self, params = {}):
		get = params.get
		self.common.log("")
		
		scraper = "movies"
		thumbnail = "explore"
		yobjects = []
		
		if (get("scraper") and get("scraper") != "movies"):
			scraper = get("scraper")
			thumbnail = get("scraper")
		
		url = self.createUrl(params)
		result = self.core._fetchPage({"link":url})
		
		if result["status"] == 200:
			categories = self.common.parseDOM(result["content"], "div", attrs = {"class": "yt-uix-expander-body.*?"})
			if len(categories) == 0:
				categories = self.common.parseDOM(result["content"], "div", attrs = {"id": "browse-filter-menu"})

			if len(categories) == 0: # <- is this needed. Anyways. it breaks. fix that..
				categories = self.common.parseDOM(result["content"], "div", attrs = {"class": "browse-filter-menu.*?"})
			
			for cat in categories:
				self.common.log("scrapeCategoryList : " + cat[0:50])
				ahref = self.common.parseDOM(cat, "a", ret = "href")
				acontent = self.common.parseDOM(cat, "a")
				for i in range(0 , len(ahref)):
					item = {}
					title = acontent[i]
					title = title.replace("&amp;", "&")
					if title == "All Categories" or title == "Education" or title == "":
						continue
					item['Title'] = title
					
					cat = ahref[i].replace("/" + scraper + "/", "")

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
				self.common.log("Failed")
				return (self.language(30601), 303)
		
		self.common.log("Done")
		return (yobjects, result["status"])

	
	def paginator(self, params = {}):
		get = params.get
		
		status = 303
		result = []
		next = 'false'
		page = int(get("page", "0"))
		per_page = ( 10, 15, 20, 25, 30, 40, 50, )[ int( self.settings.getSetting( "perpage" ) ) ]
		
		if get("page"):
			del params["page"]
		
		if get("scraper") == "shows" and get("show"):
			(result, status) = params["new_results_function"](params)
		else:
			(result, status) = self.cache.cacheFunction(params["new_results_function"], params)
		
		self.common.log("paginator new result " + str(repr(len(result[0:50]))))
		
		if len(result) == 0:
			if get("scraper") not in ["music_top100"]:
				return (result, 303)
			result = self.storage.retrieve(params)
			if len(result) > 0:
				status = 200
		elif get("scraper") in ["music_top100"]:
			self.storage.store(params, result)
		
		if not get("folder") or (get("scraper") == "shows" and get("category")):
			if ( per_page * ( page + 1 ) < len(result) ):
				next = 'true'
			
			if (get("fetch_all") != "true"):
				result = result[(per_page * page):(per_page * (page + 1))]
			print " tomomomom " + repr(len(result))
			print " tomomomom2 " + repr(result)
			if len(result) == 0:
				return (result, status)
		
		if get("batch") == "thumbnails":
			(result, status) = self.core.getBatchDetailsThumbnails(result, params)
		elif get("batch"):
			(result, status) = self.core.getBatchDetails(result, params)
		
		if get("batch"):
			del params["batch"]
		if page > 0:
			params["page"] = str(page)
		
		if not get("page") and (get("scraper") == "search_disco" or get("scraper") == "music_artist"):
			thumbnail = result[0].get("thumbnail")
			self.storage.store(params, thumbnail, "thumbnail")
		
		if next == "true":
			self.utils.addNextFolder(result, params)
		
		return (result, status)
	
	def scrape(self, params = {}):
		get = params.get
				
		self.getNewResultsFunction(params)
		
		return self.paginator(params)
	
if __name__ == '__main__':
	sys.exit(0)
