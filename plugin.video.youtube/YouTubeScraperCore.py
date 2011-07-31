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
from BeautifulSoup import BeautifulSoup, SoupStrainer

class YouTubeScraperCore:	 

	__settings__ = sys.modules[ "__main__" ].__settings__
	__language__ = sys.modules[ "__main__" ].__language__
	__plugin__ = sys.modules[ "__main__"].__plugin__	
	__dbg__ = sys.modules[ "__main__" ].__dbg__
	
	__utils__ = sys.modules[ "__main__" ].__utils__
	__core__ = sys.modules[ "__main__" ].__core__
	__storage__ = sys.modules [ "__main__" ].__storage__
	
	simple_scrapers = ["search_disco","liked_videos","live","recommended","music_top100", "disco_top_artist", "music_hits", "music_artists","music_artist", "similar_artist"]
	
	urls = {}
	urls['categories'] = "http://www.youtube.com/videos"
	urls['current_trailers'] = "http://www.youtube.com/trailers?s=trit&p=%s&hl=en"
	urls['disco_main'] = "http://www.youtube.com/disco" 
	urls['disco_mix_list'] = "http://www.youtube.com/watch?v=%s&feature=disco&playnext=1&list=%s"
	urls['disco_search'] = "http://www.youtube.com/disco?action_search=1&query=%s"
	urls['game_trailers'] = "http://www.youtube.com/trailers?s=gtcs"
	urls['live'] = "http://www.youtube.com/live"
	urls['main'] = "http://www.youtube.com"
	urls['movies'] = "http://www.youtube.com/ytmovies"
	urls['popular_game_trailers'] = "http://www.youtube.com/trailers?s=gtp&p=%s&hl=en"
	urls['popular_trailers'] = "http://www.youtube.com/trailers?s=trp&p=%s&hl=en"
	urls['recommended'] = "http://www.youtube.com/videos?r=1&hl=en"
	urls['show_list'] = "http://www.youtube.com/show"
	urls['shows'] = "http://www.youtube.com/shows"
	urls['trailers'] = "http://www.youtube.com/trailers?s=tr"
	urls['upcoming_game_trailers'] = "http://www.youtube.com/trailers?s=gtcs&p=%s&hl=en"
	urls['upcoming_trailers'] = "http://www.youtube.com/trailers?s=tros&p=%s&hl=en"
	urls['watch_later'] = "http://www.youtube.com/my_watch_later_list"
	urls['liked_videos'] = "http://www.youtube.com/my_liked_videos"
	urls['music'] = "http://www.youtube.com/music"
	urls['artist'] = "http://www.youtube.com/artist?a=%s&feature=artist"

#=================================== Trailers ============================================
	def scrapeTrailersListFormat (self, page, params = {}):
		get = params.get		 
		yobjects = []
		
		list = SoupStrainer(id="recent-trailers-container", name="div")
		trailers = BeautifulSoup(page, parseOnlyThese=list)
		
		if (len(trailers) > 0):
			trailer = trailers.div.div
			items = []
			
			while (trailer != None):
				videoid = trailer.div.div.a['href']

				if (videoid):
					if (videoid.find("=") > -1):
						videoid = videoid[videoid.find("=")+1:]  
						items.append( (videoid, trailer.div.div.a.span.img['src']) )
				
				trailer = trailer.findNextSibling(name="div")
			
		if (items):
			(yobjects, status) = self.__core__.getBatchDetailsThumbnails(items)
			
		if (not yobjects):
			return (yobjects, 500)
		
		return (yobjects, status)
	
#=================================== Categories  ============================================
	def scrapeCategoriesGrid(self, html, params = {}):
		get = params.get
		if self.__dbg__:
			print self.__plugin__ + " scrapeCategoriesGrid"
		
		next = "false"
		pager = SoupStrainer(name="div", attrs = {'class':"yt-uix-pager"})
		pagination = BeautifulSoup(html, parseOnlyThese=pager)

		if (len(pagination) > 0):
			tmp = str(pagination)
			if (tmp.find("Next") > 0):
				next = "true"
		
		list = SoupStrainer(name="div", id="browse-video-data")
		videos = BeautifulSoup(html, parseOnlyThese=list)
		
		items = []
		if (len(videos) > 0):
			video = videos.div.div
			while (video != None):
				id = video.div.a["href"]
				if (id.find("/watch?v=") != -1):
					id = id[id.find("=") + 1:id.find("&")]
					items.append(id)
				video = video.findNextSibling(name="div", attrs = {'class':"video-cell *vl"})
		else:
			list = SoupStrainer(name="div", attrs = {'class':"most-viewed-list paginated"})
			videos = BeautifulSoup(html, parseOnlyThese=list)
			if (len(videos) > 0):
				video = videos.div.div.findNextSibling(name="div", attrs={'class':"video-cell"})
				while (video != None):
					id = video.div.a["href"]
					if (id.find("/watch?v=") != -1):
						id = id[id.find("=") + 1:]
					if (id.find("&") > 0):
						id = id[:id.find("&")]
					items.append(id)
					video = video.findNextSibling(name="div", attrs = {'class':"video-cell"})
		
		if (items):
			(results, status) = self.__core__.getBatchDetails(items)
			if (status == 200):
				results[len(results) -1]["next"] = next
			return (results, status)
		
		return ([], 303)
		
#=================================== Music  ============================================
	def scrapeMusicCategories(self, params = {}):
		get = params.get
		if self.__dbg__:
			print self.__plugin__ + " scrapeMusicCategories"
		
		items = []
		url = self.urls["music"]
		(html, status) = self.__core__._fetchPage({"link": url})
		
		if status == 200:
			list = SoupStrainer(name="div", id="browse-filter-menu")
			content = BeautifulSoup(html, parseOnlyThese=list)
			if (len(content) > 0):
				cat_list = content.ul
				while cat_list != None:
					category = cat_list.li
					if (category.a == None):
						category = category.findNextSibling()
					while category != None:
						item = {}
						title = self.__utils__.makeAscii(category.a.contents[0])
						title = self.__utils__.replaceHtmlCodes(title)
						id = category.a["href"].replace("/music/","/")
						item["Title"] = title
						item["category"] = urllib.quote_plus(id)
						item["icon"] = "music"
						item["scraper"] = get("scraper")
						if get("scraper") == "music_artists":
							item["folder"] = "true"
						
						items.append(item)
						category = category.findNextSibling()
					cat_list = cat_list.findNextSibling()
		return (items, status) 

	
	def scrapeArtist(self, params = {}):
		get = params.get
		items = []
		videos = []
		if self.__dbg__:
			print self.__plugin__ + " scrapeArtist"
		
		if get("artist"):
			url = self.urls["artist"] % get("artist")
			(html, status) = self.__core__._fetchPage({"link": url})
			
			if status == 200:
				videos = re.compile('<a href="/watch\?v=(.*)&amp;feature=artist" title="').findall(html);
				
		for v in videos:
			if v not in items:
				items.append(v)
		
		return ( items, status )
	
	def scrapeSimilarArtists(self, params = {}):
		get = params.get
		items = []
		
		if self.__dbg__:
			print self.__plugin__ + " scrapeSimilarArtist"
		
		if get("artist"):
			url = self.urls["artist"] % get("artist")
			(html, status) = self.__core__._fetchPage({"link": url})
			
			if status == 200:
				list = SoupStrainer(name="div", id ="similar-artists")
				content = BeautifulSoup(html, parseOnlyThese=list)
				artists = content.findAll(name = "div", attrs = {"class":"similar-artist"})
				for artist in artists:
					item = {}
					title = self.__utils__.makeAscii(artist.a.contents[0])
					title = self.__utils__.replaceHtmlCodes(title)
					item["Title"] = title
					
					id = artist.a["href"]
					id = id[id.find("?a=") + 3:id.find("&")]
					item["artist"] = id
					item["icon"] = "music"
					item["scraper"] = "music_artist"
					item["thumbnail"] = "music"
					items.append(item)
		
		return ( items, status )
		
	def scrapeMusicCategoryArtists(self, params={}):
		get = params.get
		status = 200
		items = []
		
		if get("category"):
			category = urllib.unquote_plus(get("category"))
			url = self.urls["music"] + category
			(html, status) = self.__core__._fetchPage({"link":url})
			
			list = SoupStrainer(name="div", attrs = {"class":"ytg-fl browse-content"})
			content = BeautifulSoup(html, parseOnlyThese=list)
			
			if (len(content) > 0):
				artists = content.findAll(name="div", attrs = {"class":"browse-item artist-item"}, recursive=True)
				for artist in artists:
					item = {}
					title = self.__utils__.makeAscii(artist.div.h3.a.contents[0])
					title = self.__utils__.replaceHtmlCodes(title)
					item["Title"] = title
					item["scraper"] = "music_artist"
					
					id = artist.a["href"]
					id = id[id.find("?a=") + 3:id.find("&")]
					item["artist"] = id
					item["icon"] = "music"
					item["thumbnail"] = artist.a.span.span.span.img["data-thumb"]
					items.append(item)
		
		return (items, status)
	
	def scrapeMusicCategoryHits(self, params = {}):
		get = params.get
		status = 200
		items = []
		
		if get("category"):
			category = urllib.unquote_plus(get("category"))
			url = self.urls["music"] + category
			(html, status) = self.__core__._fetchPage({"link":url})
			
			list = SoupStrainer(name="div", attrs = {"class":"ytg-fl browse-content"})
			content = BeautifulSoup(html, parseOnlyThese=list)
			
			if (len(content) > 0):
				videos = content.findAll(name="div", attrs = {"class":"browse-item music-item "}, recursive=True)
				for video in videos: 
					id = video.a["href"]
					id = id[id.find("?v=") + 3:id.find("&")]
					items.append(id)
		
		return (items, status)
	

	def searchDisco(self, params = {}):
		get = params.get
		if self.__dbg__:
			print self.__plugin__ + " searchDisco"
		
		items = []
		if get("search"):
			url = self.urls["disco_search"] % urllib.quote_plus(get("search"))
						
			(page, status) = self.__core__._fetchPage({"link": url})
			
			if (page.find("list=") != -1):
				page = page.replace("\u0026", "&")
				mix_list_id = page[page.find("list=") + 5:]
				if (mix_list_id.find("&") != -1):
					mix_list_id = mix_list_id[:mix_list_id.find("&")]
				elif (mix_list_id.find('"') != -1):
					mix_list_id = mix_list_id[:mix_list_id.find('"')]
				
				video_id = page[page.find("v=") + 2:]
				video_id = video_id[:video_id.find("&")]
				
				url = self.urls["disco_mix_list"] % (video_id, mix_list_id)
											
				(page, status) = self.__core__._fetchPage({"link": url})
				
				list = SoupStrainer(name="div", id ="playlist-bar")
				mix_list = BeautifulSoup(page, parseOnlyThese=list)
				if (len(mix_list) > 0):
					items = mix_list.div["data-video-ids"].split(",")
		
		return ( items, 200)
		
	def scrapeDiscoTopArtist(self, params = {}):
		get = params.get
		url = self.urls["disco_main"]
		status = 303
		yobjects = []
		(page, status) = self.__core__._fetchPage({"link":url})
		list = SoupStrainer(name="div", attrs = {"class":"ytg-fl popular-artists"})
		popular = BeautifulSoup(page, parseOnlyThese=list)
		if (len(popular)):
			status = 200
			artists = popular.findAll(name="li")
			for artist in artists:
				item = {}
				title = self.__utils__.makeAscii(artist.contents[0])
				item["search"] = title
				item["Title"] = title
				
				params["thumb"] = "true"
				thumb = self.__storage__.retrieve(params)
				if not thumb:
					item["thumbnail"] = "discoball"
				else:
					item["thumbnail"] = thumb
				
				item["path"] = get("path")
				item["scraper"] = "search_disco"
				yobjects.append(item)
				
		return (yobjects, status)

#=================================== Live ============================================
	def scrapeLiveNow(self, params = {}):
		get = params.get
		if self.__dbg__:
			print self.__plugin__ + " scrapeLiveNow"

		url = self.urls[get("scraper")]
		
		(response , status) = self.__core__._fetchPage({"link": url})
		
		list = SoupStrainer(name="div", id='live-now-list-container')
		live = BeautifulSoup(response, parseOnlyThese=list)
		videos = []
		if (len(live) > 0):
			video = live.div.div
			while (video != None):
				item = {}
				videoid = video.div.a["href"]
				videoid = videoid[videoid.rfind("/")+1:]
				item["videoid"] = videoid
				item["icon"] = "live"
				thumbnail = video.div.a.span.span.img["src"]
				thumbnail = thumbnail.replace("default","0")
				item["thumbnail"] = thumbnail
				title = "Unknown Title"
				
				info = video.div.findNextSibling(name="div", attrs = {'class':"live-browse-info"})
				if len(info) > 0: 
					title = info.a.contents[0]
				item["Studio"] = info.span.a["title"]
				item ["Title"] = title
				videos.append(item)
				video = video.findNextSibling(name="div", attrs= {"class":"video-cell"})
		
		return (videos, status)	
				
#=================================== User Scraper ============================================
	
	def scrapeRecommended(self, params = {}):
		get = params.get
				
		url = self.urls[get("scraper")]
		(result, status) = self.__core__._fetchPage({"link": url, "login": "true"})
		
		videos = re.compile('<a href="/watch\?v=(.*)&amp;feature=grec_browse" class=').findall(result);
		
		if len(videos) == 0:
			videos = re.compile('<div id="reco-(.*)" class=').findall(result);
		
		return ( videos, 200 )

	def scrapeWatchLater(self, params):	
		get = params.get
		if self.__dbg__:
			print self.__plugin__ + " scrapeWatchLater"
		
		url = self.urls[get("scraper")]
		
		(response , status) = self.__core__._fetchPage({"link": url, "get_redirect":"true", "login": "true"})
		
		if status == 200:
			if response.find("p=") > 0:
				response = response[response.find("p=") + 2:]
				playlist_id = response[:response.find("&")]
				params["user_feed"] = "playlist"
				params["login"] = "true"
				params["playlist"] = playlist_id
				return self.__core__.list(params)
		
		return ([], 303)
	
	def scrapeLikedVideos(self, params):
		get = params.get
		if self.__dbg__:
			print self.__plugin__ + " scrapeLikedVideos"
		
		url = self.urls[get("scraper")]
		
		(response, status) = self.__core__._fetchPage({"link": url, "login": "true"})
		
		list = SoupStrainer(name="div", id="vm-video-list-container")
		liked = BeautifulSoup(response, parseOnlyThese=list)
		items = []
		
		if (len(liked) > 0):
			video = liked.ol.li
			while video:
				videoid = video["id"]
				videoid = videoid[videoid.rfind("video-") + 6:]
				items.append(videoid)
				video = video.findNextSibling()
		
		return (items, status)
			
#=================================== Shows ============================================
	def scrapeShowEpisodes(self, html, params = {}):
		get = params.get
		if self.__dbg__:
			print self.__plugin__ + " scrapeShowEpisodes"
		
		page = int(get("page", "0"))
		per_page = ( 10, 15, 20, 25, 30, 40, 50, )[ int( self.__settings__.getSetting( "perpage" ) ) ]
		
		oldVideos = self.__settings__.getSetting("show_" + get("show") + "_season_" + get("season","0") )
		
		if ( page == 0 or not oldVideos):
			videos = re.compile('<a href="/watch\?v=(.*)&amp;feature=sh_e_sl&amp;list=SL"').findall(html)
			
			list = SoupStrainer(name="div", attrs = {'class':"show-more-ctrl"})
			nexturl = BeautifulSoup(html, parseOnlyThese=list)
			if (len(nexturl) > 0):
				nexturl = nexturl.find(name="div", attrs = {'class':"button-container"})
				if (nexturl.button):
					nexturl = nexturl.button["data-next-url"]
				else:
					nexturl = ""
			
			if nexturl.find("start=") > 0:
				fetch = True
				start = 20
				nexturl = nexturl.replace("start=20", "start=%s")
				while fetch:
					url = self.urls["main"] + nexturl % start
					(html, status) = self.__core__._fetchPage({"link":url})
					
					if status == 200:
						html = html.replace("\\u0026","&")
						html = html.replace("\\/","/")
						html = html.replace('\\"','"')
						html = html.replace("\\u003c","<")
						html = html.replace("\\u003e",">")
						more_videos = re.compile('data-video-ids="([^"]*)"').findall(html)
						
						if not more_videos:
							fetch = False
						else:
							videos += more_videos
							start += 20
			if self.__dbg__:
				print self.__plugin__ + "found " + str(len(videos)) + " videos: " + repr(videos)
			
			self.__settings__.setSetting("show_" + get("show") + "_season_" + get("season","0"), self.__utils__.arrayToPipeDelimitedString(videos))
		else:
			videos = oldVideos.split("|")
		
		if ( per_page * ( page + 1 ) < len(videos) ):
			next = 'true'
		else:
			next = 'false'
		
		subitems = videos[(per_page * page):(per_page * (page + 1))]
		
		( ytobjects, status ) = self.__core__.getBatchDetails(subitems)
		
		if (next == "true"):
			self.__storage__.addNextFolder(ytobjects, params)
				
		return (ytobjects, status)
		
		# If the show contains more than one season the function will return a list of folder items,
		# otherwise a paginated list of video items is returned
	def scrapeShow(self, html, params = {}):
		get = params.get
		if self.__dbg__:
			print self.__plugin__ + " scrapeShow"

		
		if ((html.find('class="seasons"') == -1) or get("season")):
			if self.__dbg__:
				print self.__plugin__ + " parsing videolist for single season"
			return self.scrapeShowEpisodes(html, params)
		
		return self.scrapeShowSeasons(html, params)
	
	def scrapeShowSeasons(self, html, params = {}):
		get = params.get
		yobjects = []
		
		if self.__dbg__:
			print self.__plugin__ + " scrapeShowSeasons"
		
		list = SoupStrainer(name="div", attrs = {'class':"seasons"})
		seasons = BeautifulSoup(html, parseOnlyThese=list)
		if (len(seasons) > 0):
			params["folder"] = "true"
			season = seasons.div.div.span.button
			
			while (season != None):
				item = {}
				
				season_id = season.span.contents[0]
				title = self.__language__(30058) % season_id.encode("utf-8")
				title += " - " + season["title"].encode("utf-8")
				item["Title"] = title
				item["season"] = season_id.encode("utf-8")
				item["thumbnail"] = "shows"
				item["scraper"] = "show"
				item["icon"] = "shows"
				item["show"] = get("show")
				yobjects.append(item)
				season = season.findNextSibling()			
		
		if (len(yobjects) > 0):
			return ( yobjects, 200 )
		
		return ([], 303)
	
	def scrapeShowsGrid(self, html, params = {}):
		get = params.get
		params["folder"] = "true"
		if self.__dbg__:
			print self.__plugin__ + " scrapeShowsGrid"
		
		next = "false"
		pager = SoupStrainer(name="div", attrs = {'class':"yt-uix-pager"})
		pagination = BeautifulSoup(html, parseOnlyThese=pager)

		if (len(pagination) > 0):
			tmp = str(pagination)
			if (tmp.find("Next") > 0):
				next = "true"
		
		#Now look for the shows in the list.
		list = SoupStrainer(name="div", attrs = {"class":"popular-show-list"})
		shows = BeautifulSoup(html, parseOnlyThese=list)
		
		yobjects = []
		status = 200
		
		if (len(shows) > 0):
			
			show = shows.div.div
			
			while (show != None):
				
				if (show.a):
					item = {}
					episodes = show.find(name = "div", attrs= {'class':"show-extrainfo"})
					title = show.div.h3.contents[0]
					if (episodes and episodes.span):
						title = title + " (" + episodes.span.contents[0].lstrip().rstrip() + ")"
					
					title = title.replace("&amp;", "&")
					item['Title'] = title
					
					show_url = show.a["href"]
					if (show_url.find("?p=") > 0):
						show_url = show_url[show_url.find("?p=") + 1:]
					else :
						show_url = show_url.replace("/show/", "")
					
					show_url = urllib.quote_plus(show_url)
					item['show'] = show_url
					item['icon'] = "shows"
					item['scraper'] = "show"
					thumbnail = show.a.span.img['src']
					if ( thumbnail.find("_thumb.") > 0):
						thumbnail = thumbnail.replace("_thumb.",".")
					else:
						thumbnail = "shows"
					
					item["thumbnail"] = thumbnail
					
					if self.__dbg__:
						print self.__plugin__ + " adding show " + repr(item['Title']) + ", url: " + repr(item['show'])
					
					yobjects.append(item)
				
				show = show.findNextSibling(name="div", attrs = { 'class':re.compile("show-cell .") })
			
		if (not yobjects):
			return (self.__language__(30601), 303)
		
		yobjects[len(yobjects) -1]["next"] = next
			
		return (yobjects, status)

#=================================== Music ============================================

	def scrapeYouTubeTop100(self, params = {}):
		get = params.get
		items = []
		
		url = self.createUrl(params)
		
		(html, status) = self.__core__._fetchPage({"link": url})
		
		if status == 200:
			items = re.compile('<a href="/watch\?v=(.*)&amp;feature=musicchart" class=').findall(html);
		
		return (items, status)
		
#=================================== Movies ============================================		

	def scrapeMovieSubCategory(self, html, params = {}):
		get = params.get
		ytobjects = []
		
		list = SoupStrainer(name="div", attrs = {'class':"ytg-fl browse-content"})
		categories = BeautifulSoup(html, parseOnlyThese=list)
		if len(categories):
			categorylist = categories.findAll(name="div", attrs = {'class':"yt-uix-slider-head"})
			for category in categorylist:
				item = {}
				cat = category.div.button["href"]
				title = category.div.findNextSibling(name="div")
				title = title.h2.contents[0].strip()
				item['Title'] = title
				cat = cat.replace("/movies/", "")												
				cat = urllib.quote_plus(cat)
				item['category'] = cat
				item['scraper'] = "movies"
				item["thumbnail"] = "movies"
				ytobjects.append(item)
		
		params["folder"] = "true"
		return (ytobjects, 200)
	
	def scrapeMoviesGrid(self, html, params = {}):
		get = params.get
		yobjects = []
		next = "false"
		
		pager = SoupStrainer(name="div", attrs = {'class':"yt-uix-pager"})
		pagination = BeautifulSoup(html, parseOnlyThese=pager)

		if (len(pagination) > 0):
			tmp = str(pagination)
			if (tmp.find("Next") > 0):
				next = "true"
			
		list = SoupStrainer(name="ul", attrs = {'class':"browse-item-list"})
		movies = BeautifulSoup(html, parseOnlyThese=list)
		
		if (len(movies) > 0):
			movie = movies.li
						
			item = []
			while ( movie != None ):
				videoid = ""
				video_info = movie.div.a.span.findNextSibling(name="span")
				if video_info:
					videoid = video_info['data-video-ids']
						
				if (videoid):					
					item.append( (videoid, movie.div.a.span.img["data-thumb"]) )
				
				movie = movie.findNextSibling(name="li")
			
			(yobjects, result ) = self.__core__.getBatchDetailsThumbnails(item);
			
			if result != 200:
				return (yobjects, result)

		if (not yobjects):
			return (yobjects, 500)
		
		yobjects[len(yobjects)-1]['next'] = next

		return (yobjects, 200)

#=================================== Common ============================================
	
	def simplePaginator(self, params = {}):
		get = params.get

		page = int(get("page", "0"))
		per_page = ( 10, 15, 20, 25, 30, 40, 50, )[ int( self.__settings__.getSetting( "perpage" ) ) ]
		
		videos = []
		status = 200
		stored = self.__storage__.retrieve(params)
		
		if page == 0 or not videos:
			
			if (get("scraper") == "search_disco"):
				(videos, result ) = self.searchDisco(params)
			if (get("scraper") == "liked_videos"):
				(videos, result ) = self.scrapeLikedVideos(params)
			if (get("scraper") == "live"):
				(videos, result ) = self.scrapeLiveNow(params)
				params["no_batch"] = "true"
			if (get("scraper") == "recommended"):
				(videos, result ) = self.scrapeRecommended(params)
			if (get("scraper") == "music_top100"):
				(videos, result ) = self.scrapeYouTubeTop100(params)
			if (get("scraper") == "disco_top_artist"):
				(videos, result ) = self.scrapeDiscoTopArtist(params)
			if (get("scraper") == "music_artist"):
				(videos, result ) = self.scrapeArtist(params)
			if (get("scraper") == "similar_artist"):
				(videos, result ) = self.scrapeSimilarArtists(params)
			if (get("scraper") == "music_hits" or get("scraper") == "music_artists"):
				if get("category") and get("scraper") == "music_hits":
					(videos, result ) = self.scrapeMusicCategoryHits(params)
				elif get("category") and get("scraper") == "music_artists":
					(videos, result ) = self.scrapeMusicCategoryArtists(params)
				else:
					(videos, result ) = self.scrapeMusicCategories(params)
			
			if result == 200:
				self.__storage__.store(params, videos)
		
		if not videos and get("scraper") == "music_top100":
			videos = stored
		
		if not get("folder"): 
			if ( per_page * ( page + 1 ) < len(videos) ):
				next = 'true'
			else:
				next = 'false'
			
			subitems = videos[(per_page * page):(per_page * (page + 1))]
			
			if (get("fetch_all") == "true"):
				subitems = videos
			
			if len(subitems) == 0:
				return (subitems, 303)
			
			if get("batch_thumbnails"):
				( ytobjects, status ) = self.__core__.getBatchDetailsThumbnails(subitems)
			elif not get("no_batch"):
				( ytobjects, status ) = self.__core__.getBatchDetails(subitems)
			else:
				ytobjects = videos
			
			if (len(ytobjects) > 0):
				if get("scraper") == "search_disco":
					thumbnail = ytobjects[0].get("thumbnail","")
					if thumbnail:
						self.__settings__.setSetting("disco_search_" + urllib.unquote_plus(get("search")) + "_thumb", thumbnail)
				if (next == "true"):
					self.__storage__.addNextFolder(ytobjects, params)
		else:
			ytobjects = videos
			
		return (ytobjects, status)
	
	def advancedPageinator(self, params = {}):
		get = params.get
		original_page = int(get("page","0"))
		scraper_per_page = 0
		result = []

		if ( get("scraper") == "categories" and get("category")):
			if urllib.unquote_plus(get("category")).find("/") > 0:
				scraper_per_page = 23
			else:
				scraper_per_page = 36
		elif ( get("scraper") == "shows" and get("category")):
			scraper_per_page = 44
		elif ( get("scraper") == "movies" and get("category") and not get("subcategory")):
			scraper_per_page = 60		
		elif (get("scraper") != "shows" and 
			get("scraper") != "show" and 
			get("scraper") != "categories" and 
			get("scraper") != "movies" and 
			get("scraper") in self.urls):
			scraper_per_page = 40
		
		if (self.__dbg__):
			print self.__plugin__ + " scraper per page " + str(scraper_per_page) 
		
		if (scraper_per_page > 0):
			# begin dark magic
			request_page = int(get("page", "0"))
			page_count = request_page
			per_page = ( 10, 15, 20, 25, 30, 40, 50, )[ int( self.__settings__.getSetting( "perpage" ) ) ]
			xbmc_index = page_count * per_page 
			
			begin_page = (xbmc_index / scraper_per_page) + 1
			begin_index = (xbmc_index % scraper_per_page)
			
			params["page"] = str(begin_page)
			url = self.createUrl(params)
			if (self.__dbg__):
				print "fetching url " + url
			(html, status) = self.__core__._fetchPage({"link": url})

			if (get("scraper") == "categories"):
				(result, status) = self.scrapeCategoriesGrid(html, params)
			elif (get("scraper") == "shows"):
				(result, status) = self.scrapeShowsGrid(html, params)	
			elif (get("scraper") == "movies" and get("category")):
				(result, status) = self.scrapeMoviesGrid(html, params)
			else:
				(result, status) = self.scrapeGridFormat(html, params)
			
			next = "false"
			if (result):
				next = result[len(result) -1]["next"]
				result[len(result) -1]["next"] = ""
				result = result[begin_index:]
			
				page_count = begin_page + 1
				params["page"] = str(page_count)
				
				i = 1
				while (len(result) <  per_page and next == "true"):
					url = self.createUrl(params)
					if (self.__dbg__):
						print "fetching url: " + url
					(html, status) = self.__core__._fetchPage({"link": url})
	
					if (get("scraper") == "categories"):
						(new_result, status) = self.scrapeCategoriesGrid(html, params)
					elif (get("scraper") == "shows"):
						(new_result, status) = self.scrapeShowsGrid(html, params)
					elif (get("scraper") == "movies" and get("category")):
						(new_result, status) = self.scrapeMoviesGrid(html, params)
					else:
						(new_result, status) = self.scrapeGridFormat(html, params)
					
					if (new_result):
						next = new_result[len(new_result) - 1]["next"]
						new_result[len(new_result) -1]["next"] = ""
					else: 
						next = "false"
					
					result = result + new_result 
					page_count = page_count + 1
					params["page"] = str(page_count)
					
					i = i+1
					if (i > 9):	
						if (self.__dbg__):
							print self.__plugin__ + " Scraper pagination failed, requested more than 10 pages which should never happen."
						return False
				
				if (next == "false" and len(result) > per_page):
					next = "true"
				
				params["page"] = str(original_page)
				result = result[:per_page]
				
				if (next == "true"):
					self.__storage__.addNextFolder(result, params)
				
				return (result, status)
			else:
				return ([], 303)
		else:
			url = self.createUrl(params)
			
			if self.__dbg__:
				print self.__plugin__ + " fetching url: " + url 
				
			(html,status) = self.__core__._fetchPage({"link": url})
			if (get("scraper") == "categories" ):
				if (get("category")):
					return self.scrapeCategoriesGrid(html, params)
				else:
					return self.scrapeCategoryList(html, params)
				
			elif (get("show")):
				return self.scrapeShow(html, params)
			elif (get("scraper") == "shows"):
				if (get("category")):
					return self.scrapeShowsGrid(html, params)
				else:
					return self.scrapeCategoryList(html, params, "shows")
			elif (get("scraper") == "movies"):
				if (get("category")):
					if get("subcategory"):
						return self.scrapeMovieSubCategory(html, params)
					else:
						return self.scrapeGridFormat(html, params)
				else: 
					return self.scrapeCategoryList(html, params, "movies")
			else:
				return self.scrapeTrailersListFormat(html, params)
	
	def createUrl(self, params = {}):
		get = params.get
		page = get("page")
		
		if (get("scraper") == "categories"):
			if (get("category")):
				category = get("category")
				category = urllib.unquote_plus(category)  
				if (category.find("/") != -1):
					url = self.urls["main"] + category + "?hl=en" + "&p=" + page
				else:
					url = self.urls["main"] + "/categories" + category + "&hl=en" + "&p=" + page
			else:
				url = self.urls["categories"] + "?hl=en"
		
		elif (get("scraper") == "shows"):
			if (get("category")):
				category = get("category")
				category = urllib.unquote_plus(category)
				url = self.urls["shows"] + "/" + category
				if url.find("?") < 0:
					url += "?p=" + page + "&hl=en"
				else:
					url += "&p=" + page + "&hl=en"
			else:
				url = self.urls["shows"] + "?hl=en"
				
		elif (get("scraper") == "movies"):
			if (get("category")):
				category = get("category")
				category = urllib.unquote_plus(category)
				if get("subcategory"):
					url = self.urls["main"] + "/movies/" + category + "?hl=en"
				else:
					url = self.urls["main"] + "/movies/" + category + "?p=" + page + "&hl=en"
			else:
				url = self.urls["movies"] + "?hl=en"
		elif(get("scraper") == "music_top100"):
			url = self.urls["music"]
		elif (get("show")):
			show = urllib.unquote_plus(get("show"))
			if (show.find("p=") < 0):
				url = self.urls["show_list"] + "/" + show + "?hl=en"
			else:
				url = self.urls["show_list"] + "?" + show + "&hl=en"
			if (get("season")):
				url = url + "&s=" + get("season")
		else:
			if (get("scraper") in self.urls):
				url = self.urls[get("scraper")]
				url = url % page
			else :
				if (get("scraper") == "latest_trailers"):					
					url = self.urls["trailers"]
				else:
					url = self.urls["game_trailers"]
		
				
		return url
	
	def scrapeGridFormat(self, html, params = {}):
		get = params.get
		yobjects = []
		next = "false"
		
		pager = SoupStrainer(name="div", attrs = {'class':"yt-uix-pager"})
		pagination = BeautifulSoup(html, parseOnlyThese=pager)

		if (len(pagination) > 0):
			tmp = str(pagination)
			if (tmp.find("Next") > 0):
				next = "true"
			
		list = SoupStrainer(id="popular-column", name="div")
		trailers = BeautifulSoup(html, parseOnlyThese=list)
		
		if (len(trailers) > 0):
			trailer = trailers.div.div
			if (get("scraper") == "movies"):
				trailer = trailers.div.div.div
			
			cell = "trailer-cell *vl"
			if (get("scraper") == "categories"):
				cell = "video-cell"
			
			item = []
			while ( trailer != None ):
				videoid = trailer.div.a['href']
						
				if (videoid):
					if (videoid.find("=") > -1):
						videoid = videoid[videoid.find("=")+1:]
					
					item.append( (videoid, trailer.div.a.span.img['src']) )
				
				trailer = trailer.findNextSibling(name="div", attrs = { 'class':cell })
			
			(yobjects, result ) = self.__core__.getBatchDetailsThumbnails(item);
			
			if result != 200:
				return (yobjects, result)

		if (not yobjects):
			return (yobjects, 500)
		
		yobjects[len(yobjects)-1]['next'] = next

		return (yobjects, 200)
	
	def scrapeCategoryList(self, html = "", params = {}, tag = ""):
		get = params.get
		if self.__dbg__:
			print self.__plugin__ + " scrapeCategories " 
		scraper = "categories"
		thumbnail = "explore"
		
		if (tag):
			scraper = tag
			thumbnail = tag
		
		list = SoupStrainer(name="div", attrs = {"class":"yt-uix-expander-body"})
		categories = BeautifulSoup(html, parseOnlyThese=list)
		
		if len(categories) == 0:
			list = SoupStrainer(name="div", id = "browse-filter-menu")
			categories = BeautifulSoup(html, parseOnlyThese=list)
		
		yobjects = []
		status = 200
		
		if (len(categories) > 0):
			ul = categories.ul
			while (ul != None):
				category = ul.li
				while (category != None):
					if (category.a):
						item = {}
						title = category.a.contents[0]
						title = title.replace("&amp;", "&")
						item['Title'] = title
						cat = category.a["href"].replace("/" + tag + "/", "")
						if get("scraper") == "categories":
							if title == "Music":
								category = category.findNextSibling(name = "li")
								continue
							if cat.find("?") != -1:
								cat = cat[cat.find("?"):]
							if cat.find("comedy") > 0:
								cat = "?c=23"
							if cat.find("gaming") > 0:
								cat = "?c=20"
						if get("scraper") == "movies":
							if cat.find("pt=nr") > 0:
								category = category.findNextSibling(name = "li")
								continue
							elif cat == "indian-cinema":
								item["subcategory"] = "true"
						
						cat = urllib.quote_plus(cat)
						item['category'] = cat
						item['scraper'] = scraper
						item["thumbnail"] = thumbnail
						if self.__dbg__:
							print self.__plugin__ + "adding item: " + repr(item['Title']) + ", url: " + item['category']
						yobjects.append(item)
					
					category = category.findNextSibling(name = "li")
				ul = ul.findNextSibling(name = "ul")
		
		if (not yobjects):
			return (self.__language__(30601), 303)
		
		return (yobjects, status)
		
	def scrape(self, params = {}):
		get = params.get
		
		if get("scraper") in self.simple_scrapers:
			return self.simplePaginator(params)
		if (get("scraper") == "watch_later"):
			return self.scrapeWatchLater(params)
		
		return self.advancedPageinator(params)
	
if __name__ == '__main__':
	sys.exit(0);
