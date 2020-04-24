#!/usr/bin/python
# -*- coding: utf-8 -*-
import datetime
from .common import *

from .base import *
from .Scraper import *


class htmlScraper(Scraper):
	__urlBase = 'https://tvthek.orf.at'
	__urlLive = __urlBase + '/live'
	__urlMostViewed = __urlBase + '/most-viewed'
	__urlNewest = __urlBase + '/newest'
	__urlSchedule = __urlBase + '/schedule'
	__urlSearch = __urlBase + '/search'
	__urlShows = __urlBase + '/profiles'
	__urlTips = __urlBase + '/tips'
	__urlFocus = __urlBase + '/in-focus'
	__urlTopics = __urlBase + '/topics'
	__urlTopicLane = __urlBase + '/lane/topic/'
	__urlArchive = __urlBase + '/history'
	__urlTrailer = __urlBase + '/coming-soon'

	def __init__(self, xbmc, settings, pluginhandle, quality, protocol, delivery, defaultbanner, defaultbackdrop, usePlayAllPlaylist):
		self.translation = settings.getLocalizedString
		self.xbmc = xbmc
		self.videoQuality = quality
		self.videoDelivery = delivery
		self.videoProtocol = protocol
		self.pluginhandle = pluginhandle
		self.defaultbanner = defaultbanner
		self.defaultbackdrop = defaultbackdrop
		self.enableBlacklist = settings.getSetting("enableBlacklist") == "true"
		self.usePlayAllPlaylist = usePlayAllPlaylist
		debugLog('HTML Scraper - Init done')

	def getMostViewed(self):
		self.getTeaserList(self.__urlMostViewed, "b-teasers-list")

	def getNewest(self):
		self.getTeaserList(self.__urlNewest, "b-teasers-list")

	def getTips(self):
		self.getTeaserList(self.__urlTips, "b-teasers-list")

	# Parses the Frontpage Carousel
	def getHighlights(self):
		self.getTeaserSlideshow(self.__urlBase)
		self.getTeaserList(self.__urlBase, "stage-subteaser-list")

	def getTrailers(self):
		self.getTeaserList(self.__urlTrailer, "b-teasers-list")

	def getFocus(self):
		self.getLaneTopicOverview(self.__urlFocus)

	# Extracts VideoURL from JSON String
	def getVideoUrl(self, sources):
		for source in sources:
			if source["protocol"].lower() == self.videoProtocol.lower():
				if source["delivery"].lower() == self.videoDelivery.lower():
					if source["quality"].lower() == self.videoQuality.lower():
						return generateAddonVideoUrl(source["src"])
		return False

	# Parses teaser lists
	def getTeaserList(self, url, list_class, list_type="ul"):
		url = unqoute_url(url)
		html = fetchPage({'link': url})
		container = parseDOM(html.get("content"), name='main', attrs={'class': "main"}, ret=False)
		teasers = parseDOM(container, name=list_type, attrs={'class': list_class}, ret=False)
		items = parseDOM(teasers, name='article', attrs={'class': "b-teaser"}, ret=False)

		for item in items:
			subtitle = parseDOM(item, name='h4', attrs={'class': "profile"}, ret=False)
			subtitle = replaceHTMLCodes(subtitle[0])

			title = parseDOM(item, name='h5', attrs={'class': "teaser-title.*?"}, ret=False)
			title = replaceHTMLCodes(title[0])

			desc = parseDOM(item, name='p', attrs={'class': "description.*?"}, ret=False)
			if len(desc):
				desc = replaceHTMLCodes(desc[0])
			else:
				desc = ""

			channel = parseDOM(item, name='p', attrs={'class': "channel"}, ret=False)
			if len(channel):
				channel = replaceHTMLCodes(channel[0])
			else:
				channel = ""
			date = parseDOM(item, name='span', attrs={'class': 'date'}, ret=False)
			date = date[0]

			time = parseDOM(item, name='span', attrs={'class': 'time'}, ret=False)
			time = time[0]

			figure = parseDOM(item, name='figure', attrs={'class': 'teaser-img'}, ret=False)
			image = parseDOM(figure, name='img', attrs={}, ret='data-src')
			image = replaceHTMLCodes(image[0])

			link = parseDOM(item, name='a', attrs={'class': 'teaser-link.*?'}, ret='href')
			link = link[0]

			desc = self.formatDescription(title, channel, subtitle, desc, date, time)

			parameters = {"link": link, "banner": image, "mode": "openSeries"}
			url = build_kodi_url(parameters)
			self.html2ListItem(title, image, "", desc, "", "", "", url)

	def getLaneTopicOverview(self, url):
		html = fetchPage({'link': url})
		container = parseDOM(html.get("content"), name='section', attrs={'class': "b-list-container"}, ret=False)

		items = parseDOM(container, name='div', attrs={'class': "b-lane.*?"}, ret=False)

		for item in items:
			title_link = parseDOM(item, name='h3', attrs={'class': "title"}, ret=False)

			title = parseDOM(title_link, name='a', attrs={}, ret=False)
			title = replaceHTMLCodes(title[0])

			link = parseDOM(title_link, name='a', attrs={}, ret='href')
			link = link[0]
			link = "%s%s" % (self.__urlBase, link)

			desc = ""
			desc = self.formatDescription(title, "", "", desc, "", "")

			figure = parseDOM(item, name='figure', attrs={'class': 'teaser-img'}, ret=False)
			image = parseDOM(figure, name='img', attrs={}, ret='src')
			image = replaceHTMLCodes(image[0])

			parameters = {"link": link, "banner": image, "mode": "getArchiveDetail"}

			url = build_kodi_url(parameters)
			self.html2ListItem(title, image, "", desc, "", "", "", url)

	def formatDescription(self, title, channel, subtitle, desc, date, time):
		date_prefix = self.translation(30009)

		# Reformat Title
		if subtitle != title:
			if len(subtitle):
				title = "%s | %s" % (title, subtitle)
		if date != "":
			title = "%s - %s" % (title, date)

		# Reformat
		if len(subtitle):
			subtitle = re.sub("\s\s+", " ", str(subtitle))
			if subtitle == title:
				subtitle = ""
			else:
				if len(channel):
					subtitle = " | [LIGHT]%s[/LIGHT]" % subtitle
				else:
					subtitle = "[LIGHT]%s[/LIGHT]" % subtitle
		else:
			subtitle = ""

		if len(desc):
			desc = "[CR]%s" % desc
		else:
			desc = ""

		if len(channel):
			channel = "[B]%s[/B]" % channel
		else:
			channel = ""

		if len(date):
			return "%s%s[CR]%s[CR][I]%s %s - %s[/I]" % (channel, subtitle, desc, date_prefix, date, time)
		else:
			return "%s%s[CR]%s" % (channel, subtitle, desc)

	# Parses the frontpage teaser slider
	def getTeaserSlideshow(self, url):
		url = unqoute_url(url)
		html = fetchPage({'link': url})
		container = parseDOM(html.get("content"), name='main', attrs={'class': "main"}, ret=False)
		teasers = parseDOM(container, name='div', attrs={'class': "stage-item-list.*?"}, ret=False)
		items = parseDOM(teasers, name='a', attrs={'class': "stage-item.*?"}, ret=False)
		items_href = parseDOM(teasers, name='a', attrs={'class': "stage-item.*?"}, ret='href')
		current = 0
		for item in items:
			subtitle = parseDOM(item, name='h2', attrs={'class': "stage-item-profile-title"}, ret=False)
			subtitle = replaceHTMLCodes(subtitle[0])

			title = parseDOM(item, name='h3', attrs={'class': "stage-item-teaser-title"}, ret=False)
			title = replaceHTMLCodes(title[0])

			figure = parseDOM(item, name='figure', attrs={'class': 'stage-item-img'}, ret=False)
			image = parseDOM(figure, name='img', attrs={'class': "lazyload"}, ret='data-src')

			image = replaceHTMLCodes(image[0])

			link = items_href[current]
			link = link

			# Reformat Title
			if subtitle != title:
				title = "%s | %s" % (subtitle, title)

			parameters = {"link": link, "banner": image, "mode": "openSeries"}

			url = build_kodi_url(parameters)
			self.html2ListItem(title, image, "", "", "", "", "", url)
			current += 1

	# Scrapes the detail page for a schedule day selection (missed a show)
	def openArchiv(self, url):
		url = unqoute_url(url)
		html = fetchPage({'link': url})
		container = parseDOM(html.get("content"), name='main', attrs={'class': "main"}, ret=False)
		teasers = parseDOM(container, name='div', attrs={'class': "b-schedule-list"}, ret=False)
		items = parseDOM(teasers, name='article', attrs={'class': "b-schedule-episode.*?"}, ret=False)

		date = parseDOM(teasers, name='h2', attrs={'class': 'day-title.*?'}, ret=False)
		if len(date):
			date = date[0]
		else:
			date = ""

		for item in items:
			title = parseDOM(item, name='h4', attrs={'class': "item-title.*?"}, ret=False)
			title = replaceHTMLCodes(title[0])

			desc = parseDOM(item, name='div', attrs={'class': "item-description.*?"}, ret=False)
			if len(desc):
				desc = replaceHTMLCodes(desc[0])
				desc = stripTags(desc)
			else:
				desc = ""

			channel = parseDOM(item, name='span', attrs={'class': "small-information.meta.meta-channel-name"}, ret=False)
			if len(channel):
				channel = replaceHTMLCodes(channel[0])
			else:
				channel = ""

			time = parseDOM(item, name='span', attrs={'class': 'meta.meta-time'}, ret=False)
			time = time[0]

			title = "[%s] %s" % (time, title)

			subtitle = time

			image = parseDOM(item, name='img', attrs={}, ret='src')
			if len(image):
				image = replaceHTMLCodes(image[0])
			else:
				image = ""

			link = parseDOM(item, name='a', attrs={'class': 'episode-content'}, ret='href')
			link = link[0]

			desc = self.formatDescription(title, channel, subtitle, desc, date, time)

			parameters = {"link": link, "banner": image, "mode": "openSeries"}

			url = build_kodi_url(parameters)
			self.html2ListItem(title, image, "", desc, "", "", "", url)

	# Parses the Frontpage Show Overview Carousel
	def getCategories(self):
		html = fetchPage({'link': self.__urlShows})
		container = parseDOM(html.get("content"), name='main', attrs={'class': "main"}, ret=False)
		teasers = parseDOM(container, name='div', attrs={'class': "b-profile-results-container.*?"}, ret=False)
		items = parseDOM(teasers, name='article', attrs={'class': "b-teaser"}, ret=False)

		for item in items:
			subtitle = parseDOM(item, name='h4', attrs={'class': "profile"}, ret=False)
			subtitle = replaceHTMLCodes(subtitle[0])

			title = parseDOM(item, name='h5', attrs={'class': "teaser-title.*?"}, ret=False)
			title = replaceHTMLCodes(title[0])

			desc = parseDOM(item, name='p', attrs={'class': "description.*?"}, ret=False)
			if len(desc):
				desc = replaceHTMLCodes(desc[0])
			else:
				desc = ""

			channel = parseDOM(item, name='p', attrs={'class': "channel"}, ret=False)
			if len(channel):
				channel = replaceHTMLCodes(channel[0])
			else:
				channel = ""
			date = parseDOM(item, name='span', attrs={'class': 'date'}, ret=False)
			date = date[0]

			time = parseDOM(item, name='span', attrs={'class': 'time'}, ret=False)
			time = time[0]

			figure = parseDOM(item, name='figure', attrs={'class': 'teaser-img'}, ret=False)
			image = parseDOM(figure, name='img', attrs={}, ret='src')
			image = replaceHTMLCodes(image[0])

			link = parseDOM(item, name='a', attrs={'class': 'teaser-link.*?'}, ret='href')
			link = link[0]

			try:
				regex = r"https://tvthek.orf.at/profile/(.*)/(.*)/(.*)/(.*)"
				matches = re.search(regex, link)
				name_path = matches.group(1)
				id_path = matches.group(2)
				link = "%s/%s/%s/%s" % (self.__urlBase, "profile", name_path, id_path)
			except IndexError:
				debugLog("Not a standard show link. Using default url: %s" % link)

			desc = self.formatDescription(title, channel, subtitle, desc, date, time)
			debugLog("Link: %s" % link)
			parameters = {"link": link, "banner": image, "mode": "getSendungenDetail"}
			url = build_kodi_url(parameters)
			self.html2ListItem(title, image, "", desc, "", "", "", url)

	# Parses Details for the selected Show
	def getCategoriesDetail(self, category, banner):
		url = unqoute_url(category)
		banner = unqoute_url(banner)
		html = fetchPage({'link': url})
		container = parseDOM(html.get("content"), name='main', attrs={'class': "main"}, ret=False)

		# Main Episode
		main_episode_container = parseDOM(container, name='section', attrs={'class': "b-video-details.*?"}, ret=False)

		title = parseDOM(main_episode_container, name='h2', attrs={'class': "description-title.*?"}, ret=False)
		title = replaceHTMLCodes(title[0])

		subtitle = parseDOM(main_episode_container, name='span', attrs={'class': "js-subheadline"}, ret=False)
		if len(subtitle):
			subtitle = replaceHTMLCodes(subtitle[0])
		else:
			subtitle = ""

		desc = parseDOM(main_episode_container, name='p', attrs={'class': "description-text.*?"}, ret=False)
		if len(desc):
			desc = replaceHTMLCodes(desc[0])
		else:
			desc = ""

		channel = parseDOM(main_episode_container, name='span', attrs={'class': "channel.*?"}, ret="aria-label")
		if len(channel):
			channel = replaceHTMLCodes(channel[0])
		else:
			channel = ""

		date = parseDOM(main_episode_container, name='span', attrs={'class': 'date'}, ret=False)
		date = date[0]

		time = parseDOM(main_episode_container, name='span', attrs={'class': 'time'}, ret=False)
		time = time[0]

		image = banner

		if date != "":
			title = "%s - %s" % (title, date)

		desc = self.formatDescription(title, channel, subtitle, desc, date, time)

		parameters = {"link": url, "banner": image, "mode": "openSeries"}
		url = build_kodi_url(parameters)
		self.html2ListItem(title, image, "", desc, "", "", "", url)

		# More Episodes
		more_episode_container = parseDOM(container, name='section', attrs={'class': "related-videos"}, ret=False)
		more_episode_json = parseDOM(more_episode_container, name="div", attrs={'class': 'more-episodes.*?'}, ret='data-jsb')
		if len(more_episode_json):
			more_episode_json_raw = replaceHTMLCodes(more_episode_json[0])
			more_episode_json_data = json.loads(more_episode_json_raw)
			more_episodes_url = "%s%s" % (self.__urlBase, more_episode_json_data.get('url'))

			additional_html = fetchPage({'link': more_episodes_url})

			items = parseDOM(additional_html.get("content"), name='article', attrs={'class': "b-teaser"}, ret=False)

			for item in items:
				subtitle = parseDOM(item, name='h4', attrs={'class': "profile"}, ret=False)
				subtitle = replaceHTMLCodes(subtitle[0])

				title = parseDOM(item, name='h5', attrs={'class': "teaser-title.*?"}, ret=False)
				title = replaceHTMLCodes(title[0])

				desc = parseDOM(item, name='p', attrs={'class': "description.*?"}, ret=False)
				if len(desc):
					desc = replaceHTMLCodes(desc[0])
				else:
					desc = ""

				channel = parseDOM(item, name='p', attrs={'class': "channel"}, ret=False)
				if len(channel):
					channel = replaceHTMLCodes(channel[0])
				else:
					channel = ""
				date = parseDOM(item, name='span', attrs={'class': 'date'}, ret=False)
				date = date[0]

				time = parseDOM(item, name='span', attrs={'class': 'time'}, ret=False)
				time = time[0]

				figure = parseDOM(item, name='figure', attrs={'class': 'teaser-img'}, ret=False)
				image = parseDOM(figure, name='img', attrs={}, ret='src')
				image = replaceHTMLCodes(image[0])

				link = parseDOM(item, name='a', attrs={'class': 'teaser-link.*?'}, ret='href')
				link = link[0]

				if date != "":
					title = "%s - %s" % (title, date)

				desc = self.formatDescription(title, channel, subtitle, desc, date, time)

				parameters = {"link": link, "banner": image, "mode": "openSeries"}
				url = build_kodi_url(parameters)
				self.html2ListItem(title, image, "", desc, "", "", "", url)

	def getLaneTeasers(self, html):
		items = parseDOM(html.get("content"), name='article', attrs={'class': "b-topic-teaser"}, ret=False)

		lane_title = parseDOM(html.get("content"), name='h3', attrs={'class': "title"}, ret=False)
		lane_title = replaceHTMLCodes(lane_title[0])
		lane_title = stripTags(lane_title)

		for item in items:
			title = parseDOM(item, name='h5', attrs={'class': "teaser-title.*?"}, ret=False)
			title = replaceHTMLCodes(title[0])
			title = "[%s] %s" % (lane_title, title)

			video_count = parseDOM(item, name='p', attrs={'class': "topic-video-count"}, ret=False)
			desc = replaceHTMLCodes(video_count[0])

			figure = parseDOM(item, name='figure', attrs={'class': 'teaser-img'}, ret=False)
			image = parseDOM(figure, name='img', attrs={}, ret='src')
			image = replaceHTMLCodes(image[0])

			link = parseDOM(item, name='a', ret='href')
			link = link[0]
			link = "%s%s" % (self.__urlBase, link)

			desc = self.formatDescription(title, "", "", desc, "", "")

			parameters = {"link": link, "banner": image, "mode": "getArchiveDetail"}

			url = build_kodi_url(parameters)
			self.html2ListItem(title, image, "", desc, "", "", "", url)

	# Parses Teaserblock Titles and returns links for every category
	def getLaneItems(self, url):
		html = fetchPage({'link': url})
		items = parseDOM(html.get("content"), name='article', attrs={'class': "b-teaser"}, ret=False)

		if len(items) < 1:
			self.getLaneTeasers(html)
		else:
			lane_title = parseDOM(html.get("content"), name='h3', attrs={'class': "title"}, ret=False)
			lane_title = replaceHTMLCodes(lane_title[0])
			lane_title = stripTags(lane_title)
			for item in items:
				subtitle = parseDOM(item, name='h4', attrs={'class': "profile"}, ret=False)
				subtitle = replaceHTMLCodes(subtitle[0])

				title = parseDOM(item, name='h5', attrs={'class': "teaser-title.*?"}, ret=False)
				title = replaceHTMLCodes(title[0])
				title = "[%s] %s" % (lane_title, title)

				desc = parseDOM(item, name='p', attrs={'class': "description.*?"}, ret=False)
				if len(desc):
					desc = replaceHTMLCodes(desc[0])
				else:
					desc = ""

				channel = parseDOM(item, name='p', attrs={'class': "channel"}, ret=False)
				if len(channel):
					channel = replaceHTMLCodes(channel[0])
				else:
					channel = ""
				date = parseDOM(item, name='span', attrs={'class': 'date'}, ret=False)
				date = date[0]

				time = parseDOM(item, name='span', attrs={'class': 'time'}, ret=False)
				time = time[0]

				figure = parseDOM(item, name='figure', attrs={'class': 'teaser-img'}, ret=False)
				image = parseDOM(figure, name='img', attrs={}, ret='src')
				image = replaceHTMLCodes(image[0])

				link = parseDOM(item, name='a', attrs={'class': 'teaser-link.*?'}, ret='href')
				link = link[0]

				if date != "":
					title = "%s - %s" % (title, date)

				desc = self.formatDescription(title, channel, subtitle, desc, date, time)

				parameters = {"link": link, "banner": image, "mode": "openSeries"}
				url = build_kodi_url(parameters)
				self.html2ListItem(title, image, "", desc, "", "", "", url)

	# Parses "Sendung verpasst?" Date Listing
	def getSchedule(self):
		html = fetchPage({'link': self.__urlSchedule})
		container = parseDOM(html.get("content"), name='div', attrs={'class': 'b-select-box.*?'})
		list_container = parseDOM(container, name='select', attrs={'class': 'select-box-list.*?'})
		items = parseDOM(list_container, name='option', attrs={'class': 'select-box-item.*?'})
		data_items = parseDOM(list_container, name='option', attrs={'class': 'select-box-item.*?'}, ret="data-custom-properties")
		i = 0
		for item in items:
			title = replaceHTMLCodes(item)
			link = replaceHTMLCodes(data_items[i])
			link = "%s%s" % (self.__urlBase, link)

			parameters = {"link": link, "mode": "getScheduleDetail"}
			url = build_kodi_url(parameters)
			self.html2ListItem(title, "", "", "", "", "", "", url)
			i += 1

	def getArchiv(self):
		html = fetchPage({'link': self.__urlArchive})
		html_content = html.get("content")

		wrapper = parseDOM(html_content, name='main', attrs={'class': 'main'})
		items = parseDOM(wrapper, name='article', attrs={'class': 'b-topic-teaser.*?'})

		for item in items:
			subtitle = parseDOM(item, name='h4', attrs={'class': "sub-headline"}, ret=False)
			subtitle = replaceHTMLCodes(subtitle[0])

			title = parseDOM(item, name='h5', attrs={'class': "teaser-title.*?"}, ret=False)
			title = replaceHTMLCodes(title[0])

			video_count = parseDOM(item, name='p', attrs={'class': "topic-video-count"}, ret=False)
			desc = replaceHTMLCodes(video_count[0])

			figure = parseDOM(item, name='figure', attrs={'class': 'teaser-img'}, ret=False)
			image = parseDOM(figure, name='img', attrs={}, ret='src')
			image = replaceHTMLCodes(image[0])

			link = parseDOM(item, name='a', ret='href')
			link = link[0]

			desc = self.formatDescription(title, "", subtitle, desc, "", "")

			parameters = {"link": link, "banner": image, "mode": "getArchiveDetail"}

			url = build_kodi_url(parameters)
			self.html2ListItem(title, image, "", desc, "", "", "", url)

	# Creates a XBMC List Item
	def html2ListItem(self, title, banner, backdrop, description, duration, date, channel, videourl, subtitles=None, folder=True, playable=False, contextMenuItems=None):
		if banner == '':
			banner = self.defaultbanner
		if backdrop == '':
			backdrop = self.defaultbackdrop
		params = parameters_string_to_dict(videourl)
		mode = params.get('mode')
		if not mode:
			mode = "player"

		blacklist = False
		if self.enableBlacklist:
			if mode == 'openSeries' or mode == 'getSendungenDetail':
				blacklist = True
		debugLog("Adding List Item")
		debugLog("Mode: %s" % mode)
		debugLog("Videourl: %s" % videourl)
		debugLog("Duration: %s" % duration)
		debugLog("Banner: %s" % banner)
		debugLog("Backdrop: %s" % backdrop)
		debugLog("Playable: %s" % playable)

		return createListItem(title, banner, description, duration, date, channel, videourl, playable, folder, backdrop, self.pluginhandle, subtitles, blacklist, contextMenuItems)

	def getMainStreamInfos(self, html, data_json, banner):
		stream_info = {}
		try:
			html_data = parseDOM(html.get("content"), name='section', attrs={'class': "b-video-details.*?"}, ret=False)
			playlist_json = data_json.get('playlist')

			current_channel = parseDOM(html_data, name='span', attrs={'class': "channel.*?"}, ret='aria-label')
			if len(current_channel):
				stream_info['channel'] = replaceHTMLCodes(current_channel[0])
			else:
				stream_info['channel'] = ""

			current_date = parseDOM(html_data, name='span', attrs={'class': 'date'}, ret=False)
			stream_info['date'] = current_date[0]

			current_time = parseDOM(html_data, name='span', attrs={'class': 'time'}, ret=False)
			if len(current_time):
				stream_info['time'] = current_time[0]
			else:
				stream_info['time'] = ""

			stream_info['second_headline'] = ""
			current_subtitle = parseDOM(html_data, name='p', attrs={'class': "profile.*?"}, ret=False)
			current_subheadline = parseDOM(current_subtitle, name='span', attrs={'class': "js-subheadline"}, ret=False)
			if len(current_subheadline):
				stream_info['second_headline'] = stripTags(replaceHTMLCodes(current_subheadline[0]))
			else:
				if len(current_subtitle):
					stream_info['second_headline'] = stripTags(replaceHTMLCodes(current_subtitle[0]))

			if len(html_data):
				html_desc = parseDOM(html_data, name='p', attrs={'class': "description-text.*?"}, ret=False)
				stream_info['description'] = stripTags(replaceHTMLCodes(html_desc[0]))

			stream_info['main_title'] = playlist_json['title']
			if "preview_image_url" in playlist_json:
				stream_info['teaser_image'] = playlist_json['preview_image_url']
			else:
				stream_info['teaser_image'] = banner

			stream_info['title'] = data_json.get("selected_video")["title"]
			stream_info['full_description'] = self.formatDescription(stream_info['title'], stream_info['channel'], stream_info['second_headline'], stream_info['description'], stream_info['date'], stream_info['time'])

			if data_json.get("selected_video")["description"]:
				stream_info['description'] = data_json.get("selected_video")["description"]

			if data_json.get("selected_video")["duration"]:
				tmp_duration = float(data_json.get("selected_video")["duration"])
				stream_info['duration'] = int(tmp_duration / 1000)

			if "subtitles" in data_json.get("selected_video"):
				main_subtitles = []
				for sub in data_json.get("selected_video")["subtitles"]:
					main_subtitles.append(sub.get(u'src'))
				stream_info['subtitles'] = main_subtitles
			else:
				stream_info['subtitles'] = None
			stream_info['main_videourl'] = self.getVideoUrl(data_json.get("selected_video")["sources"])
		except:
			debugLog("Error fetching stream infos from html")
		return stream_info

	# Parses a Video Page and extracts the Playlist/Description/...
	def getLinks(self, url, banner, playlist):
		url = unqoute_url(url)
		debugLog("Loading Videos from %s" % url)
		if banner is not None:
			banner = unqoute_url(banner)

		stream_infos = {}
		playlist_json = {}
		video_items = []
		html = fetchPage({'link': url})
		data = parseDOM(html.get("content"), name='div', attrs={'class': "jsb_ jsb_VideoPlaylist"}, ret='data-jsb')

		if len(data):
			try:
				data = data[0]
				data = replaceHTMLCodes(data)
				data_json = json.loads(data)
				playlist_json = data_json.get('playlist')
				stream_infos = self.getMainStreamInfos(html, data_json, banner)
				video_items = playlist_json["videos"]
			except Exception as e:
				debugLog("Error Loading Episode from %s" % url)

			# Add the gapless video if available
			try:
				if "is_gapless" in playlist_json:
					gapless_subtitles = []
					gapless_name = '-- %s --' % self.translation(30059)
					if playlist_json['is_gapless']:
						gapless_videourl = self.getVideoUrl(playlist_json['gapless_video']['sources'])
						if gapless_videourl:
							if "subtitles" in playlist_json['gapless_video']:
								for sub in playlist_json['gapless_video']["subtitles"]:
									gapless_subtitles.append(sub.get(u'src'))
							else:
								global_subtitles = None
							if "duration_in_seconds" in playlist_json:
								gapless_duration = playlist_json["duration_in_seconds"]
							else:
								gapless_duration = ""
							liz = self.html2ListItem(gapless_name, stream_infos['teaser_image'], "", stream_infos['full_description'], gapless_duration, '', '', gapless_videourl, gapless_subtitles, False, True)
			except IndexError as e:
				debugLog("No gapless video added for %s" % url)


			# Multiple chapters available
			if len(video_items) > 1:
				play_all_name = '-- %s --' % self.translation(30060)
				debugLog("Found Video Playlist with %d Items" % len(video_items))
				if self.usePlayAllPlaylist:
					createPlayAllItem(play_all_name, self.pluginhandle, stream_infos)
				for video_item in video_items:
					try:
						title = video_item["title"]
						if video_item["description"]:
							desc = video_item["description"]
						else:
							debugLog("No Video Description for %s" % title)
							desc = ""

						if video_item["duration"]:
							duration = float(video_item["duration"])
							duration = int(duration / 1000)
						else:
							duration = 0

						preview_img = video_item["preview_image_url"]
						sources = video_item["sources"]
						if "subtitles" in video_item:
							debugLog("Found Subtitles for %s" % title)
							subtitles = []
							for sub in video_item["subtitles"]:
								subtitles.append(sub.get(u'src'))
						else:
							subtitles = None
						videourl = self.getVideoUrl(sources)
						liz = self.html2ListItem(title, preview_img, "", desc, duration, '', '', videourl, subtitles, False, True)
						playlist.add(videourl, liz)
					except Exception as e:
						debugLog(str(e), self.xbmc.LOGERROR)
						continue
				return playlist
			else:
				debugLog("No Playlist Items found for %s. Setting up single video view." % stream_infos['title'])
				liz = self.html2ListItem(stream_infos['title'], stream_infos['teaser_image'], "", stream_infos['full_description'], stream_infos['duration'], '', '', stream_infos['main_videourl'], stream_infos['subtitles'], False, True)
				playlist.add(stream_infos['main_videourl'], liz)
				return playlist
		else:
			showDialog((self.translation(30052)))
			sys.exit()

	# Returns Live Stream Listing
	def getLiveStreams(self):
		html = fetchPage({'link': self.__urlBase})
		wrapper = parseDOM(html.get("content"), name='main', attrs={'class': 'main'})
		section = parseDOM(wrapper, name='section', attrs={'class': 'b-live-program.*?'})
		items = parseDOM(section, name='li', attrs={'class': 'channel orf.*?'})

		for item in items:
			channel = parseDOM(item, name='img', attrs={'class': 'channel-logo'}, ret="alt")
			channel = replaceHTMLCodes(channel[0])

			bundesland_article = parseDOM(item, name='li', attrs={'class': '.*?is-bundesland-heute.*?'}, ret='data-jsb')
			article = parseDOM(item, name='article', attrs={'class': 'b-livestream-teaser is-live.*?'})
			if not len(bundesland_article) and len(article):
				figure = parseDOM(article, name='figure', attrs={'class': 'teaser-img'}, ret=False)
				image = parseDOM(figure, name='img', attrs={}, ret='data-src')
				image = replaceHTMLCodes(image[0])

				time = parseDOM(article, name='h4', attrs={'class': 'time'}, ret=False)
				time = replaceHTMLCodes(time[0])
				time = stripTags(time)

				title = parseDOM(article, name='h4', attrs={'class': 'livestream-title.*?'})
				title = replaceHTMLCodes(title[0])

				link = parseDOM(item, name='a', attrs={'class': 'js-link-box'}, ret="href")
				link = replaceHTMLCodes(link[0])

				online = parseDOM(article, name='span', attrs={'class': 'status-online'})
				if len(online):
					online = True
				else:
					online = False

				restart = parseDOM(article, name='span', attrs={'class': 'is-restartable'})
				if len(restart):
					restart = True
				else:
					restart = False

				self.buildLivestream(title, link, time, restart, channel, image, online)
			elif len(bundesland_article):
				bundesland_data = replaceHTMLCodes(bundesland_article[0])
				bundesland_data = json.loads(bundesland_data)
				for bundesland_item_key in bundesland_data:
					bundesland_item = bundesland_data.get(bundesland_item_key)
					if bundesland_item and bundesland_item is not True and len(bundesland_item):
						bundesland_title = bundesland_item.get('title')
						bundesland_image = bundesland_item.get('img')
						bundesland_link = bundesland_item.get('url')

						self.buildLivestream(bundesland_title, bundesland_link, "", True, channel, bundesland_image, True)

	def buildLivestream(self, title, link, time, restart, channel, banner, online):
		html = fetchPage({'link': link})
		container = parseDOM(html.get("content"), name='div', attrs={'class': "player_viewport.*?"})
		if len(container):
			data = parseDOM(container[0], name='div', attrs={}, ret="data-jsb")

			if online:
				state = (self.translation(30019))
			else:
				state = (self.translation(30020))

			if time:
				time_str = " (%s)" % time
			else:
				time_str = ""

			try:
				xbmcaddon.Addon('inputstream.adaptive')
				inputstreamAdaptive = True
			except RuntimeError:
				inputstreamAdaptive = False

			if channel:
				channel = "[%s]" % channel
			else:
				channel = "LIVE"

			uhd_streaming_url = self.getLivestreamUrl(data, 'uhdbrowser')
			if uhd_streaming_url:
				debugLog("Adding UHD Livestream")
				uhdContextMenuItems = []
				if inputstreamAdaptive and restart and online:
					uhdContextMenuItems.append(('Restart', 'RunPlugin(plugin://%s/?mode=liveStreamRestart&link=%s)' % (
						xbmcaddon.Addon().getAddonInfo('id'), link)))
					uhd_final_title = "[Restart]%s[UHD] - %s%s" % (channel, title, time_str)
				else:
					uhd_final_title = "%s[UHD] - %s%s" % (channel, title, time_str)
				self.html2ListItem(uhd_final_title, banner, "", state, time, channel, channel, generateAddonVideoUrl(uhd_streaming_url), None, False, True, uhdContextMenuItems)

			streaming_url = self.getLivestreamUrl(data, self.videoQuality)
			contextMenuItems = []
			if inputstreamAdaptive and restart and online:
				contextMenuItems.append(('Restart', 'RunPlugin(plugin://%s/?mode=liveStreamRestart&link=%s)' % (
					xbmcaddon.Addon().getAddonInfo('id'), link)))
				final_title = "[Restart]%s - %s%s" % (channel, title, time_str)
			else:
				final_title = "%s - %s%s" % (channel, title, time_str)
			self.html2ListItem(final_title, banner, "", state, time, channel, channel, generateAddonVideoUrl(streaming_url), None, False, True, contextMenuItems)

	def liveStreamRestart(self, link):
		try:
			xbmcaddon.Addon('inputstream.adaptive')
		except RuntimeError:
			return

		html = fetchPage({'link': link})
		bitmovinStreamId = self.getLivestreamBitmovinID(html)
		stream_info = self.getLivestreamInformation(html)

		if bitmovinStreamId:
			title = stream_info['title']
			image = stream_info['image']
			description = stream_info['description']
			duration = stream_info['duration']
			date = stream_info['date']
			channel = stream_info['channel']

			ApiKey = '2e9f11608ede41f1826488f1e23c4a8d'
			response = url_get_request('https://playerapi-restarttv.ors.at/livestreams/%s/sections/?state=active&X-Api-Key=%s' % (bitmovinStreamId, ApiKey))
			try:
				charset = response.headers.get_content_charset()
				response_raw = response.read().decode(charset)
			except AttributeError:
				response_raw = response.read().decode('utf-8')

			section = json.loads(response_raw)
			if len(section):
				section = section[0]
				streamingURL = 'https://playerapi-restarttv.ors.at/livestreams/%s/sections/%s/manifests/hls/?startTime=%s&X-Api-Key=%s' % (bitmovinStreamId, section.get('id'), section.get('metaData').get('timestamp'), ApiKey)

				listItem = createListItem(title, image, description, duration, date, channel, streamingURL, True, False, self.defaultbackdrop, self.pluginhandle)
				listItem.setProperty('inputstreamaddon', 'inputstream.adaptive')
				listItem.setProperty('inputstream.adaptive.manifest_type', 'hls')
				self.xbmc.Player().play(streamingURL, listItem)

	@staticmethod
	def getLivestreamUrl(data_sets, quality):
		for data in data_sets:
			try:
				data = replaceHTMLCodes(data)
				data = json.loads(data)
				if 'playlist' in data:
					if 'videos' in data['playlist']:
						for video_items in data['playlist']['videos']:
							for video_sources in video_items['sources']:
								if video_sources['quality'].lower() == quality.lower() and video_sources[
									'protocol'].lower() == "http" and video_sources['delivery'].lower() == 'hls':
									return video_sources['src']
			except Exception as e:
				debugLog("Error getting Livestream")

	@staticmethod
	def getLivestreamBitmovinID(html):
		container = parseDOM(html.get("content"), name='div', attrs={'class': "player_viewport.*?"})
		if len(container):
			data_sets = parseDOM(container[0], name='div', attrs={}, ret="data-jsb")
			if len(data_sets):
				for data in data_sets:
					try:
						data = replaceHTMLCodes(data)
						data = json.loads(data)

						if 'restart_url' in data:
							bitmovin_id = data['restart_url'].replace("https://playerapi-restarttv.ors.at/livestreams/","").replace("/sections/", "")
							return bitmovin_id.split("?")[0]
					except Exception as e:
						debugLog("Error getting Livestream Bitmovin ID")
						return False
		return False

	@staticmethod
	def getLivestreamInformation(html):
		container = parseDOM(html.get("content"), name='div', attrs={'class': "player_viewport.*?"})
		data_sets = parseDOM(container[0], name='div', attrs={}, ret="data-jsb")
		title = "Titel"
		image = ""
		description = "Beschreibung"
		duration = ""
		date = ""
		channel = ""

		for data in data_sets:
			try:
				data = replaceHTMLCodes(data)
				data = json.loads(data)

				if 'playlist' in data:
					time_str = False
					time_str_end = False
					if 'title' in data['playlist']:
						title = data['playlist']['title']
					if 'preview_image_url' in data['playlist']:
						image = data['playlist']['preview_image_url']
					if 'livestream_start' in data['playlist']:
						date = data['playlist']['livestream_start']
						time_str = datetime.datetime.fromtimestamp(int(date)).strftime('%H:%M')
					if 'livestream_end' in data['playlist']:
						date = data['playlist']['livestream_end']
						time_str_end = datetime.datetime.fromtimestamp(int(date)).strftime('%H:%M')
					if 'videos' in data['playlist']:
						if 'description' in data['playlist']['videos']:
							description = data['playlist']['videos']['description']
					if time_str and time_str_end:
						return {"title": "%s (%s - %s)" % (title, time_str, time_str_end), "image": image, "description": description, "date": date, "duration": duration, "channel": channel}
					else:
						return {"title": title, "image": image, "description": description, "date": date, "duration": duration, "channel": channel}
			except Exception as e:
				debugLog("Error getting Livestream Infos")

	# Parses the Topic Overview Page
	def getThemen(self):
		html = fetchPage({'link': self.__urlTopics})
		html_content = html.get("content")

		content = parseDOM(html_content, name='section', attrs={})

		for topic in content:
			title = parseDOM(topic, name='h3', attrs={'class': 'item_wrapper_headline.subheadline'})
			if title:
				title = replaceHTMLCodes(title[0])

				link = parseDOM(topic, name='a', attrs={'class': 'more.service_link.service_link_more'}, ret="href")
				link = replaceHTMLCodes(link[0])

				image = parseDOM(topic, name='img', ret="src")
				image = replaceHTMLCodes(image[0]).replace("width=395", "width=500").replace("height=209.07070707071", "height=265")

				descs = parseDOM(topic, name='h4', attrs={'class': 'item_title'})
				description = ""
				for desc in descs:
					description += "* %s \n" % replaceHTMLCodes(desc)

				parameters = {"link": link, "mode": "getThemenDetail"}
				url = build_kodi_url(parameters)
				self.html2ListItem(title, image, "", description, "", "", "", url)

	# Parses the Archive Detail Page
	def getArchiveDetail(self, url):
		url = unqoute_url(url)
		html = fetchPage({'link': url})
		html_content = html.get("content")

		wrapper = parseDOM(html_content, name='main', attrs={'class': 'main'})
		items = parseDOM(wrapper, name='article', attrs={'class': 'b-teaser.*?'})

		for item in items:
			subtitle = parseDOM(item, name='h4', attrs={'class': "profile"}, ret=False)
			subtitle = replaceHTMLCodes(subtitle[0])

			title = parseDOM(item, name='h5', attrs={'class': "teaser-title.*?"}, ret=False)
			title = replaceHTMLCodes(title[0])

			desc = parseDOM(item, name='p', attrs={'class': "description.*?"}, ret=False)
			desc = replaceHTMLCodes(desc[0])

			figure = parseDOM(item, name='figure', attrs={'class': 'teaser-img'}, ret=False)
			image = parseDOM(figure, name='img', attrs={}, ret='src')
			image = replaceHTMLCodes(image[0])

			link = parseDOM(item, name='a', ret='href')
			link = link[0]

			channel = parseDOM(item, name='p', attrs={'class': "channel"}, ret=False)
			if len(channel):
				channel = replaceHTMLCodes(channel[0])
			else:
				channel = ""

			date = parseDOM(item, name='span', attrs={'class': 'date'}, ret=False)
			date = date[0]

			time = parseDOM(item, name='span', attrs={'class': 'time'}, ret=False)
			time = time[0]

			desc = self.formatDescription(title, channel, subtitle, desc, date, time)

			parameters = {"link": link, "banner": image, "mode": "openSeries"}
			url = build_kodi_url(parameters)
			self.html2ListItem(title, image, "", desc, "", "", "", url)

	def getSearchHistory(self):
		parameters = {'mode': 'getSearchResults'}
		u = build_kodi_url(parameters)
		createListItem((self.translation(30007)) + " ...", self.defaultbanner, "", "", "", '', u, False, True, self.defaultbackdrop, self.pluginhandle)

		history = searchHistoryGet()
		for str_val in reversed(history):
			if str_val.strip() != '':
				parameters = {'mode': 'getSearchResults', 'link': str_val.replace(" ", "+")}
				u = build_kodi_url(parameters)
				createListItem(str_val, self.defaultbanner, "", "", "", '', u, False, True, self.defaultbackdrop, self.pluginhandle)

	@staticmethod
	def removeUmlauts(str_val):
		return str_val.replace("Ö", "O").replace("ö", "o").replace("Ü", "U").replace("ü", "u").replace("Ä", "A").replace("ä","a")

	def getSearchResults(self, link):
		keyboard = self.xbmc.Keyboard(link)
		keyboard.doModal()
		if keyboard.isConfirmed():
			keyboard_in = keyboard.getText()
			if keyboard_in != link:
				searchHistoryPush(keyboard_in)
			searchurl = "%s?q=%s" % (self.__urlSearch, keyboard_in.replace(" ", "+"))
			self.getTeaserList(searchurl, 'b-search-results', 'section')
		else:
			parameters = {'mode': 'getSearchHistory'}
			u = build_kodi_url(parameters)
			createListItem((self.translation(30014)) + " ...", self.defaultbanner, "", "", "", '', u, False, True, self.defaultbackdrop, self.pluginhandle)
