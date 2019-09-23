from __future__ import absolute_import,unicode_literals
import xbmcgui # pylint: disable=import-error
import re
from resources.lib.mode.common import Common
from resources.lib.playback import Playback
from resources.lib import svt
from resources.lib import logging
from resources.lib import helper

try:
  # Python 2
  from urllib import quote
except ImportError:
  # Python 3
  from urllib.parse import quote

class NormalList:
    # Settings
    S_USE_ALPHA_CATEGORIES = "alpha"
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
    MODE_CLIPS = "clips"

    def __init__(self, addon, plugin_url, plugin_handle, default_fanart):
        self.common = Common(addon, plugin_url, plugin_handle, default_fanart)
        self.playback = Playback(plugin_handle)
        self.localize = addon.getLocalizedString

    def route(self, mode, url, params, page):
        if not mode:
            self.view_start()
        elif mode == self.MODE_A_TO_O:
            if helper.getSetting(self.S_USE_ALPHA_CATEGORIES):
                self.view_alpha_directories()
            else:
                self.view_a_to_z()
        elif mode == self.MODE_CATEGORIES:
            self.view_categories()
        elif mode == self.MODE_CATEGORY:
            self.view_category(url)
        elif mode == self.common.MODE_PROGRAM:
            self.view_episodes(url)
            self.__add_clip_dir_item(url)
        elif mode == self.MODE_CLIPS:
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
        programs = svt.getAtoO()
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
        programs = svt.getProgramsByLetter(letter)
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
        categories = svt.getCategories()
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
        items = svt.getLatestNews()
        if not items:
            return
        for item in items:
            self.common.create_dir_item(item, self.common.MODE_VIDEO)

    def view_category(self, genre):
        programs = svt.getProgramsForGenre(genre)
        if not programs:
            return
        for program in programs:
            mode = self.common.MODE_PROGRAM
            if program["type"] == "video":
                mode = self.common.MODE_VIDEO
            self.common.create_dir_item(program, mode)

    def view_episodes(self, url):
        """
        Displays the episodes for a program
        """
        logging.log("View episodes for {}".format(url))
        episodes = svt.getEpisodes(url.split("/")[-1])
        if episodes is None:
            logging.log("No episodes found")
            return
        for episode in episodes:
            self.common.create_dir_item(episode, self.common.MODE_VIDEO)

    def __add_clip_dir_item(self, url):
        """
        Adds the "Clips" directory item to a program listing.
        """
        params = {}
        params["mode"] = self.MODE_CLIPS
        params["url"] = url
        self.common.add_directory_item(self.localize(30108), params)

    def view_clips(self, url):
        """
        Displays the latest clips for a program
        """
        logging.log("View clips for {}".format(url))
        clips = svt.getClips(url.split("/")[-1])
        if not clips:
            logging.log("No clips found")
            return
        for clip in clips:
            self.common.create_dir_item(clip, self.common.MODE_VIDEO)

    def view_search(self):
        keyword = helper.getInputFromKeyboard(self.localize(30102))
        if keyword == "" or not keyword:
            self.view_start()
            return
        keyword = quote(keyword)
        logging.log("Search string: " + keyword)
        keyword = re.sub(r" ", "+", keyword)
        keyword = keyword.strip()
        results = svt.getSearchResults(keyword)
        for result in results:
            mode = self.common.MODE_VIDEO
            if result["type"] == "program":
                mode = self.common.MODE_PROGRAM
            self.common.create_dir_item(result["item"], mode)

    def start_video(self, video_id):
        video_json = svt.getVideoJSON(video_id)
        if video_json is None:
            logging.log("ERROR: Could not get video JSON")
            return
        try:
            show_obj = helper.resolveShowJSON(video_json)
        except ValueError:
            logging.log("Could not decode JSON for "+video_id)
            return
        if show_obj["videoUrl"]:
            self.playback.play_video(show_obj["videoUrl"], show_obj.get("subtitleUrl", None))
        else:
            dialog = xbmcgui.Dialog()
            dialog.ok("SVT Play", self.localize(30100))