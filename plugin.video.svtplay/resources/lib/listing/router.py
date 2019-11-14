from __future__ import absolute_import,unicode_literals
import re
from resources.lib.listing.common import Common
from resources.lib.api import svt
from resources.lib.api.graphql import GraphQL
from resources.lib import logging
from resources.lib import helper

try:
  # Python 2
  from urllib import quote
except ImportError:
  # Python 3
  from urllib.parse import quote

class Router:
    # List modes
    MODE_LIVE_PROGRAMS = "live"
    MODE_LATEST = "latest"
    MODE_LATEST_NEWS = 'news'
    MODE_POPULAR = "popular"
    MODE_LAST_CHANCE = "last_chance"
    MODE_CHANNELS = "kanaler"
    MODE_A_TO_O = "a-o"
    MODE_SEARCH = "search"
    MODE_CATEGORIES = "categories"
    MODE_LETTER = "letter"
    MODE_CATEGORY = "ti"

    def __init__(self, addon, plugin_url, plugin_handle, default_fanart, settings):
        logging.log("Starting normal listing mode")
        self.graphql = GraphQL()
        self.common = Common(addon, plugin_url, plugin_handle, default_fanart, settings)
        self.localize = addon.getLocalizedString
        self.settings = settings

    def route(self, mode, url, params, page):
        if not mode:
            self.view_start()
        elif mode == self.MODE_A_TO_O:
            if self.settings.alpha_program_listing:
                self.view_alpha_directories()
            else:
                self.view_a_to_z()
        elif mode == self.MODE_CATEGORIES:
            self.view_categories()
        elif mode == self.MODE_CATEGORY:
            self.view_category(url)
        elif mode == self.common.MODE_PROGRAM:
            self.view_episodes(url)
        elif mode == self.common.MODE_CLIPS:
            self.view_clips(url)
        elif mode == self.common.MODE_VIDEO:
            self.start_video(url)
        elif mode == self.MODE_POPULAR or \
            mode == self.MODE_LATEST or \
            mode == self.MODE_LAST_CHANCE or \
            mode == self.MODE_LIVE_PROGRAMS:
            self.view_section(mode, page)
        elif mode == self.MODE_LATEST_NEWS:
            self.view_latest_news()
        elif mode == self.MODE_CHANNELS:
            self.view_channels()
        elif mode == self.MODE_LETTER:
            self.view_programs_by_letter(params.get("letter"))
        elif mode == self.MODE_SEARCH:
            self.view_search()

    def view_start(self):
        self.common.add_directory_item(self.localize(30009), {"mode": self.MODE_POPULAR})
        self.common.add_directory_item(self.localize(30003), {"mode": self.MODE_LATEST})
        self.common.add_directory_item(self.localize(30004), {"mode": self.MODE_LATEST_NEWS})
        self.common.add_directory_item(self.localize(30010), {"mode": self.MODE_LAST_CHANCE})
        self.common.add_directory_item(self.localize(30002), {"mode": self.MODE_LIVE_PROGRAMS})
        self.common.add_directory_item(self.localize(30008), {"mode": self.MODE_CHANNELS})
        self.common.add_directory_item(self.localize(30000), {"mode": self.MODE_A_TO_O})
        self.common.add_directory_item(self.localize(30001), {"mode": self.MODE_CATEGORIES})
        self.common.add_directory_item(self.localize(30006), {"mode": self.MODE_SEARCH})

    def view_a_to_z(self):
        programs = self.graphql.getAtoO()
        self.__program_listing(programs)

    def view_alpha_directories(self):
        letters = svt.getAlphas()
        if not letters:
            return
        for letter in letters:
            self.common.add_directory_item(
                letter, 
                {
                    "mode": self.MODE_LETTER,
                    "letter": letter.encode("utf-8")
                }
            )

    def view_programs_by_letter(self, letter):
        programs = self.graphql.getProgramsByLetter(letter)
        self.__program_listing(programs)

    def __program_listing(self, programs):
        for program in programs:
            if self.common.is_geo_restricted(program):
                logging.log("Not showing {} as it is restricted to Sweden and geo setting is on".format(program["title"]))
                continue
            folder = True
            mode = self.common.MODE_PROGRAM
            if program["type"] == "video":
                mode = self.common.MODE_VIDEO
                folder = False
            self.common.add_directory_item(
                program["title"],
                {
                    "mode": mode,
                    "url": program["url"]
                },
                thumbnail=program["thumbnail"],
                folder=folder
            )

    def view_categories(self):
        categories = self.graphql.getGenres()
        for category in categories:
            self.common.add_directory_item(
                category["title"],
                {
                    "mode": self.MODE_CATEGORY, 
                    "url": category["genre"]
                }
            )

    def view_section(self, section, page):
        (items, more_items) = svt.getItems(section, page)
        if not items:
            return
        for item in items:
            mode = self.common.MODE_VIDEO
            if item["type"] == "program":
                mode = self.common.MODE_PROGRAM
            self.common.create_dir_item(item, mode)
        if more_items:
            self.common.add_next_page_item(page+1, section)

    def view_channels(self):
        channels = svt.getChannels()
        if not channels:
            return
        for channel in channels:
            self.common.create_dir_item(channel, self.common.MODE_VIDEO)

    def view_latest_news(self ):
        items = self.graphql.getLatestNews()
        if not items:
            return
        for item in items:
            self.common.create_dir_item(item, self.common.MODE_VIDEO)

    def view_category(self, genre):
        programs = self.graphql.getProgramsForGenre(genre)
        if not programs:
            return
        for program in programs:
            mode = self.common.MODE_PROGRAM
            if program["type"] == "video":
                mode = self.common.MODE_VIDEO
            self.common.create_dir_item(program, mode)

    def view_episodes(self, url):
        slug = url.split("/")[-1]
        logging.log("View episodes for {}".format(slug))
        episodes = self.graphql.getEpisodes(slug)
        self.common.view_episodes(episodes)

    def view_clips(self, url):
        logging.log("View clips for {}".format(url))
        clips = svt.getClips(url.split("/")[-1])
        self.common.view_clips(clips)

    def view_search(self):
        keyword = helper.getInputFromKeyboard(self.localize(30102))
        if keyword == "" or not keyword:
            self.view_start()
            return
        keyword = quote(keyword)
        logging.log("Search string: " + keyword)
        keyword = re.sub(r" ", "+", keyword)
        keyword = keyword.strip()
        results = self.graphql.getSearchResults(keyword)
        for result in results:
            mode = self.common.MODE_VIDEO
            if result["type"] == "program":
                mode = self.common.MODE_PROGRAM
            self.common.create_dir_item(result, mode)

    def start_video(self, video_url):
        channel_pattern = re.compile(r'^ch\-')
        logging.log("start video for {}".format(video_url))
        if channel_pattern.search(video_url):
            video_json = svt.getVideoJSON(video_url)
        else:
            legacy_id = video_url.split("/")[2]
            svt_id = self.graphql.getSvtIdForlegacyId(legacy_id)
            video_json = svt.getSvtVideoJson(svt_id)
        self.common.start_video(video_json)
        