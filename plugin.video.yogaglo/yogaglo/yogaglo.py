from xbmc import log, LOGDEBUG
from xbmcaddon import Addon
from xbmc_util import (addDirs, eod, yoga_class_list_item,
                       form_plugin_url, yoga_category_menu_list_item,
                       yoga_glo_index_menu_item, yoga_class_play_video, setViewMode)

from http import openUrl
from soup_crawler import SoupCrawler
import authentication

"""
YogaGlo takes care of the main proceessing, delegating to the HTML crawling logic
and the xbmc results from that.

"""
class YogaGlo:
    """
    YogaGlo encapsulates this xbmc plugin, its handle, and its plugin parameters.
    Additionally, logs on to yogaglo.com and creates the HTML crawler delegate.

    """
    plugin_name = "plugin.video.yogaglo"
    yoga_glo_base_url = "http://www.yogaglo.com"

    def __init__(self, plugin, handle, plugin_params):
        log("YogaGlo -- args are %s, %s, %s" %
            (plugin, handle, plugin_params), LOGDEBUG)
        self.xbmc_plugin = plugin
        self.xbmc_handle = handle
        self.addon = Addon(id=self.plugin_name)
        self.yoga_glo_plugin_parameters = plugin_params
        self.yoga_glo_logged_in = authentication.yg_authenticate(self.addon)
        self.crawler = SoupCrawler(self.yoga_glo_base_url)

    # Build plugins index page, with category selection and yoga of the day

    def index(self):
	"""
	Builds the index page for the plugin containing the 5 top level categories
	- Teacher
	- Style
	- Duration
	- Level
	- Yoga Of The Day -> homepage is crawled for this information
	to down select from.
	
	"""
        yoga_glo_categories = {'Teacher': 2, 'Style': 3, 'Duration': 5,
                               'Level': 4, 'Yoga Of The Day': 1 }
        itemList = []
        for category in yoga_glo_categories:
            log("yogaglo -> building index for category '%s'" % (category), LOGDEBUG)
            # processing for yoga of the day!
            if yoga_glo_categories[category] == 1:
                yotd = self.crawler.get_yoga_of_the_day_title_and_info()
                title = yotd['title']
                description = yotd['information']
                plugin_query = {'yogaCategory' : yoga_glo_categories[category],
                                'yogagloUrl' : self.yoga_glo_base_url }
                li = yoga_glo_index_menu_item(title, description)
                plugin_url = form_plugin_url(self.xbmc_plugin, plugin_query)
                itemList.append((plugin_url, li, True))
                continue

            title = category
            description = "Select A" + title
            plugin_query = {'yogaCategory' : yoga_glo_categories[category]}
            li = yoga_glo_index_menu_item(title, description)
            plugin_url = form_plugin_url(self.xbmc_plugin, plugin_query)
            # list item is a folder, per se
            itemList.append((plugin_url, li, True))

        addDirs(self.xbmc_handle, itemList)
        eod(self.xbmc_handle)

    def category_menu(self):
	"""
	Lists the items for the category selected from the index page.  Loads of
	a sub menu, that unless the category is "Yoga Of The Day", requires one
	more down select before a video can be selected.

	Delegates to crawler to gather category information.
	
	"""
        log("yogaglo -> selecting category %s" %
            (self.yoga_glo_plugin_parameters['yogaCategory']), LOGDEBUG)
        itemList = []
        yoga_category = self.yoga_glo_plugin_parameters['yogaCategory']
        menu = self.crawler.get_yoga_glo_navigation_information(yoga_category)
        for item in menu:
            url = item['url']
            # using get() passes None instead of an error
            li = yoga_category_menu_list_item(item['title'], url,
                                              item.get('image_url'))
            plugin_query = { 'yogaCategory' : yoga_category,
                             'yogagloUrl' : url }
            plugin_url = form_plugin_url(self.xbmc_plugin, plugin_query)
            # list item is a folder, per se
            itemList.append((plugin_url, li, True))

        addDirs(self.xbmc_handle, itemList)
        eod(self.xbmc_handle)

    def classes_menu(self):
	"""
	Lists the classes available to play for this particular menu selection.
	Selecting a list item here plays the video.

	Delegates to crawler to gather information for these yoga classes.
	
	"""
        log("yogaglo -> getting classes for category '%s' at url '%s'" %
            (self.yoga_glo_plugin_parameters['yogaCategory'],
             self.yoga_glo_plugin_parameters['yogagloUrl']), LOGDEBUG)
        #list of items for xbmc to handle (you get a progress bar with this!)
        itemList = []
        yoga_category = self.yoga_glo_plugin_parameters['yogaCategory']
        classesInformation = self.crawler.get_classes(
            self.yoga_glo_plugin_parameters['yogagloUrl'])

        for classInformation in classesInformation:
            class_url = classInformation['url']
            li = yoga_class_list_item(classInformation)
            plugin_query = { 'yogaCategory' : yoga_category,
                             'yogagloUrl' : class_url, 'play': 1}
            plugin_url = form_plugin_url(self.xbmc_plugin, plugin_query)
            # list item is not a folder
            itemList.append((plugin_url, li, False))

        addDirs(self.xbmc_handle, itemList)
        setViewMode(self.xbmc_handle, self.addon, "503")
        eod(self.xbmc_handle)

    def play_class_video(self):
	"""
	Plays the video associated with the list item selected.
	If not logged on to yogaglo.com, will play a 5 minute preview clip.
	Logged on gets the full length video at the highest quality.

	Delegates to crawler to class video rtmp information.
	
	"""
        log("yogaglo -> play class at url '%s'" %
            (self.yoga_glo_plugin_parameters['yogagloUrl']), LOGDEBUG)
        yogaglo_url = self.yoga_glo_plugin_parameters['yogagloUrl']

        #logged in, get full video at highest resolution
        if self.yoga_glo_logged_in:
            video_info = self.crawler.get_yogaglo_video_information(
                yogaglo_url, authentication.get_cookie_path())
            yoga_class_play_video(video_info['rtmp_url'],
                                  video_info['play_path'],
                                  video_info['swf_url'], self.xbmc_handle)
            return
            
        #not logged in, 5-minute preview clip
        video_info = self.crawler.get_yogaglo_preview_video_information(
            yogaglo_url)
        yoga_class_play_video(video_info['rtmp_url'],
                              video_info['play_path'],
                              video_info['swf_url'], self.xbmc_handle)
        return

    def processParameters(self):
	"""
	Processes the parameters passed into the plugin.  Parameters are a map.
	Any parameter set with 'play' as a key, will play a yoga class.
	If 'play' isn't present and 'yogagloUrl' is, the yoga classes will be
	crawled and listed.
	If 'yogagloUrl' isn't present and 'yogaCategory' is, the list of
	sub-categories for a selected category will be crawled and listed.
	If no keys are present, the index page is generated.
	
	"""
        if 'play' in self.yoga_glo_plugin_parameters:
            self.play_class_video()
            return

        if 'yogagloUrl' in self.yoga_glo_plugin_parameters:
            self.classes_menu()
            return

        if 'yogaCategory' in self.yoga_glo_plugin_parameters:
            self.category_menu()
            return

        self.index()
