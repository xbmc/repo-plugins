'''
   Vimeo plugin for XBMC
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

import sys, urllib2, string

class VimeoScraperCore(object):
	
	def __init__(self):
		self.soup = sys.modules["__main__"].soup
		self.settings = sys.modules[ "__main__" ].settings
		self.language = sys.modules[ "__main__" ].language
		self.plugin = sys.modules[ "__main__" ].plugin
		self.dbg = sys.modules[ "__main__" ].dbg
		self.hq_thumbs = self.settings.getSetting( "high_quality_thumbs" ) == "true"
		
		self.USERAGENT = "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-GB; rv:1.9.2.8) Gecko/20100722 Firefox/3.6.8"
		self.LOGINURL = "http://www.vimeo.com/log_in"

	def scrapeChannels(self, page, params = {}):
		get = params.get
		vobjects = []
		
		if (not get('featured')):
			featured = {}
			featured["thumbnail"] = "featured"
			featured["Title"] = "Featured Channels"
			featured["scraper"] = "channels"
			featured["featured"] = "true"
				
			vobjects = self._scrapeCloud(page, params)
		
			if (vobjects):
				vobjects.insert(0, featured)
				return vobjects
		else :
			vobjects = self._scrapeChannelBadgeFormat(page, params)
			
		
		if (not vobjects):
			vobjects = self._scrapeDetailFormat(page, params) 
		
		return vobjects
	
	def scrapeGroups(self, page, params = {}):
		get = params.get
		vobjects = []				
		
		vobjects = self._scrapeCloud(page, params)
		
		if (not vobjects):
			vobjects = self._scrapeDetailFormat(page, params)
		
		return vobjects
	
	def scrapeCategories(self, page, params = {}):
		get = params.get
		vobjects = []
		
		vobjects = self._scrapeCategoryBrowser(page, params)
				
		if (not vobjects):
			vobjects = self._scrapeThumbnailFormat(page, params)
						
		return vobjects
	
	def _scrapeCloud(self, page, params = {}):
		get = params.get
		vobjects = []
		
		list = self.soup.SoupStrainer(id="cloud", name="div")
		cloud = self.soup.BeautifulSoup(page, parseOnlyThese=list)
		
		if (len(cloud) > 0):
			li = cloud.ul.li
			
			while (li != None):
				item ={}
				title = li.a.contents
				if (title):
					item["Title"] = string.capwords(title[0].strip())
					if (len(title[0]) < 3):
						item["Title"] = title[0].upper()
					item["Title"] = item["Title"].replace("Diy", "DIY")
					
					category = li.a['href']
					if (category.rfind(":") > 0):
						category = category[category.rfind(":")+1:]
					item["category"] = category
					
					item["scraper"] = get("scraper")
					item["thumbnail"] = "explore"
					vobjects.append(item)
				li = li.findNextSibling(name="li")
				
		return vobjects
	
	def _scrapeThumbnailFormat(self, page, params = {}):
		get = params.get
		vobjects = []
		
		list = self.soup.SoupStrainer(name="div", attrs = {"class":"thumbnail_format"})
		videos = self.soup.BeautifulSoup(page, parseOnlyThese=list)
		
		if (len(videos) > 0):
			
			next = "false"
			limiter = self.soup.SoupStrainer(name="div", attrs = {"class":"pagination"})
			pagination = self.soup.BeautifulSoup(page, parseOnlyThese=limiter)
			if (len(pagination) > 0):
				li = pagination.ul.li.findNextSibling(name="li", attrs = {"class":"arrow"})
				if (li != None):
					next = "true"

			row = videos.div.div
			
			while (row != None):
				video = row.div
				while (video != None):
					if (video["class"] != "clear"): 
						item ={}
						title = video.div.a.contents
						if (title):
							item["Title"] = title[0].strip()
							videoid = video.a['href']
							if (videoid.find("/") > -1):
								videoid = videoid[videoid.find("/")+1:]
								
							item["videoid"] = videoid 
							thumbnail = video.a.img['src']
							if (self.hq_thumbs):
								if thumbnail.rfind("_200"):
									thumbnail = thumbnail.replace("_200", "_640")

							overlay = self.settings.getSetting( "vidstatus-" + item['videoid'] )
							
							if overlay:
								item['Overlay'] = int(overlay)
								
							item["thumbnail"] = thumbnail
							item["next"] = next
							vobjects.append(item)
						
					video = video.findNextSibling(name="div")
				row = row.findNextSibling(name="div", attrs = { 'class':"row" })
				
		return vobjects
		
	def _fetchPage(self, feed, params = {}):
		url = urllib2.Request(feed)
		url.add_header('User-Agent', self.USERAGENT);
		
		con = urllib2.urlopen(url);
		page = con.read()
		con.close()
		return page
	
	def _scrapeChannelBadgeFormat(self, page, params = {}):
		get = params.get
		vobjects = []
		list = self.soup.SoupStrainer(id ="featured", name="div")
		featured = self.soup.BeautifulSoup(page, parseOnlyThese=list)
		if (len(featured) > 0):
			li = featured.ul.li
			
			while (li != None):
				item = {}
				item["Title"] =li.a['title'].strip()
				channel = li.a['href']
				item["channel"] = channel[channel.rfind("/")+1:]
				image = li.div['style']
				image = image[image.find("('")+2:]
				image = image[:image.rfind("')")]
				if (self.hq_thumbs):
					if (image.rfind("_200")):
						image = image.replace("_200", "_600")
				item["thumbnail"] = image
				vobjects.append(item)
				li = li.findNextSibling(name="li")
		return vobjects
	
	def _scrapeCategoryBrowser(self, page, params = {}):
		get = params.get
		vobjects = []
		
		list = self.soup.SoupStrainer(id="cat_browse", name="div")
		categories = self.soup.BeautifulSoup(page, parseOnlyThese=list)
		if (len(categories) > 0):
			li = categories.ul.li
			
			while (li != None):
				item ={}
				title = li.h3.a.contents
				if (title):
					category = li.h3.a['href']
					if (category.rfind("/") > 0):
						category = category[category.rfind("/")+1:]
					item["category"] = category 
					item["Title"] = title[0].strip()
					item["thumbnail"] = "explore"
					item["scraper"] = get("scraper")
					vobjects.append(item)
				li = li.findNextSibling(name="li")
		
		return vobjects		 
	
	def _scrapeDetailFormat(self, page, params = {}):
		get = params.get
		vobjects = []
		
		list = self.soup.SoupStrainer(name="div", attrs={"class":"detail_format"})
		details = self.soup.BeautifulSoup(page, parseOnlyThese=list)
		if (len(details) > 0):

			next = "false"
			limiter = self.soup.SoupStrainer(name="div", attrs = {"class":"pagination"})
			pagination = self.soup.BeautifulSoup(page, parseOnlyThese=limiter)
			if (len(pagination) > 0):
				
				li = pagination.ul.li.findNextSibling(name="li", attrs = {"class":"arrow"})
				if (li != None):
					next = "true"
			
			row = details.div.div
			
			while (row != None):				
				item ={}
				detail = row.div.div.findNextSibling(name="div", attrs = { 'class':"detail" })
				if (len(detail) > 0):
					title = detail.div.a.contents
					if (title):
						title[0] = title[0].replace("&hellip;", "...")
						title[0] = title[0].replace("&quot;", '"')
						title[0] = title[0].replace("&amp;", '&')
						item["Title"] = title[0].strip()
						
						cog = row.div.div.a['href']
						cog = cog[cog.rfind('/')+1:]
						if (get("scraper") == "groups"):
							item["group"] = cog
						else: 
							item["channel"] = cog
													
						thumbnail = row.div.div.a.img['src']
						if (self.hq_thumbs):
							if thumbnail.rfind("_200"):
								thumbnail = thumbnail.replace("_200", "_640")

						item["thumbnail"] = thumbnail
						item["next"] = next
						description = detail.div.findNextSibling(name="div", attrs = {'class':"description"})						
						if (description):
							desc = description.contents
							if (desc):
								desc[0] = desc[0].replace("&hellip;", "...")
								desc[0] = desc[0].replace("&quot;", '"')
								desc[0] = desc[0].replace("&amp;", '&')
								item["Description"] = desc[0]
						
						vobjects.append(item)
				row = row.findNextSibling(name="div", attrs = { 'class':"row" })
				
		return vobjects
		
		# main scraper function guards pagination, be warned, dark voodoo magic protects these lands :D
	def scrape(self, feed, params = {}):
		get = params.get
		result = [] 
		
		scraper_per_page = 0
		
		if (get("scraper") == "categories" and get("category")):
			scraper_per_page = 12
		elif (get("category")):
			scraper_per_page = 15
		
		if (scraper_per_page > 0):
			# begin dark magic
			request_page = int(get("page", "0"))
			page_count = request_page
			per_page = ( 10, 15, 20, 25, 30, 40, 50, )[ int( self.settings.getSetting( "perpage" ) ) ]
			xbmc_index = page_count * per_page 
			
			begin_page = (xbmc_index / scraper_per_page) + 1
			begin_index = (xbmc_index % scraper_per_page)
			
			params["page"] = str(begin_page)
			
			url = self.createUrl(feed,params)
			
			if (self.dbg):
				print self.plugin + " requesting url: " + url
			html = self._fetchPage(url, params)
			result = self.parsePage(html, params)
			result = result[begin_index:]
			page_count = begin_page + 1
			params["page"] = str(page_count)
			
			i = 1
			while (len(result) <  per_page):
				url = self.createUrl(feed,params)
				if (self.dbg):
					print self.plugin + " requesting url: " + url
				html = self._fetchPage(url, params)
				result = result + self.parsePage(html, params)
				page_count = page_count + 1
				params["page"] = str(page_count)
				
				i = i+1
				if (i > 9):
					if (self.dbg):
						print self.plugin + " Scraper pagination failed, requested more than 10 pages which should never happen."
					return False
				
			if (result):
				result = result[:per_page]
			
			params["page"] = request_page
		else :
			if (get("category")):
				page = int(get("page","0"))
				params["page"] = str(page + 1)
			url = self.createUrl(feed, params)
			html = self._fetchPage(url, params)	
			result = self.parsePage(html, params)		
		
		return (result, 200)
	
	def parsePage(self, page, params = {}):
		get = params.get
		if (get('category') or get('scraper') == 'categories'):
			result = self.scrapeCategories(page, params)
		
		if (get('scraper') == 'channels'):
			result = self.scrapeChannels(page, params)
		
		if (get('scraper') == 'groups'):
			result = self.scrapeGroups(page, params)
		
		return result
		
	def createUrl(self, feed, params = {}):
		get = params.get 
				
		if (get("category")):
			if (get("scraper") == "categories"):
				feed += "/" + get("category") + "/videos"
			else:
				feed += "/all"
				if (get("page")):
					feed += "/page:" + get("page")
				feed += "/category:" + get("category")			
		
		if (get("page") and get("scraper") == "categories"):
			feed += "/page:" + get("page")
			
		if (get("sort")):
			feed += "/sort:" + get("sort")
		
		return feed

