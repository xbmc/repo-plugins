"""
Main plugin code
"""
import random

import routing
import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin

from . import (ataglance, first_run_wizard, kodiutils, news_programs, nhk_api,
               topstories, url, utils, vod)
from .episode import Episode

plugin = routing.Plugin()

# Global variables
ADDON = xbmcaddon.Addon()
NHK_ICON = ADDON.getAddonInfo('icon')
NHK_FANART = ADDON.getAddonInfo('fanart')

# Default value - can be overwritten by settings
MAX_NEWS_DISPLAY_ITEMS = 0
MAX_ATAGLANCE_DISPLAY_ITEMS = 0
USE_CACHE = True
USE_720P = False

# Initialize the plugin with default values and the cache
xbmc.log("Initializing plug-in")
xbmc.log("initialize: Retrieving plug-in setting")
# Getting the add-on settings - these will be 0 under unit test
# Define how many items should be displayed in News
MAX_NEWS_DISPLAY_ITEMS = ADDON.getSettingInt("max_news_items")
# Define how many items should be displayed in At A Glance
MAX_ATAGLANCE_DISPLAY_ITEMS = ADDON.getSettingInt("max_ataglance_items")
# Define if to ise 720P instead of 1080P
USE_720P = ADDON.getSettingBool("use_720P")
xbmc.log(f"initialize: Using 720P instead of 1080p: {USE_720P}")
USE_CACHE = ADDON.getSettingBool("use_backend")
xbmc.log(f"initialize: Use Azure cache: {USE_CACHE}")

if utils.UNIT_TEST:
    MAX_NEWS_DISPLAY_ITEMS = 20
    MAX_ATAGLANCE_DISPLAY_ITEMS = 800
    USE_CACHE = True

#
# Entry point - this is called from main.py
# This function cannot be unit tested
#


def run():
    """ Run the plugin
    """
    if ADDON.getSettingBool("run_wizard"):
        first_run_wizard.show_wizard()
    plugin.run()


@plugin.route('/')
def index():
    """
    Start page of the plug-in
    """
    xbmc.log("Creating Main Menu")
    # Add menus
    add_live_stream_menu_item()
    add_on_demand_menu_item()
    add_live_schedule_menu_item()
    add_topstories_menu_item()
    add_ataglance_menu_item()
    add_news_programs_menu_item()
    # Set-up view
    kodiutils.set_video_directory_information(plugin.handle,
                                              xbmcplugin.SORT_METHOD_UNSORTED,
                                              "tvshows")
    return True


#
# Top Stories
#


#  Menu item
def add_topstories_menu_item():
    """
    Top Stories - Menu item
    """
    xbmc.log("Adding top stories menu item")
    success = False
    menu_item = topstories.get_menu_item()
    # Create the directory item
    if menu_item is not None:
        xbmcplugin.addDirectoryItem(plugin.handle,
                                    plugin.url_for(topstories_index),
                                    menu_item.kodi_list_item, True)
        success = True
    return success


# List
@plugin.route('/topstories/index')
def topstories_index():
    """
    Top Stories - Index
    """
    xbmc.log("Displaying Top Stories Index")
    success = False
    topstories_episodes = topstories.get_episodes(MAX_NEWS_DISPLAY_ITEMS,
                                                  NHK_ICON, NHK_FANART)
    episodes = []

    for episode in topstories_episodes:
        if episode.is_playable:
            episodes.append(
                (plugin.url_for(play_news_item, episode.url, episode.vod_id,
                                "news",
                                episode.title), episode.kodi_list_item, False))
        else:
            # No video attached to it
            episodes.append(
                (plugin.url_for(show_textviewer_dialog_box, episode.title,
                                episode.plot), episode.kodi_list_item, False))

    if len(episodes) > 0:
        xbmcplugin.addDirectoryItems(plugin.handle, episodes, len(episodes))
        kodiutils.set_video_directory_information(
            plugin.handle, xbmcplugin.SORT_METHOD_UNSORTED, "episodes")
        success = True
    return success


#
# At a glance
#


#  Menu item
def add_ataglance_menu_item():
    """
    At a glance - Menu item
    """
    xbmc.log("Adding At a glance menu item")
    success = False
    menu_item = ataglance.get_menu_item()

    if menu_item is not None:
        xbmcplugin.addDirectoryItem(plugin.handle,
                                    plugin.url_for(ataglance_index),
                                    menu_item.kodi_list_item, True)
        success = True
    return success


# Episode list
@plugin.route('/ataglance/index')
def ataglance_index():
    """
    At a glance - Index
    """
    xbmc.log("Displaying At a Glance Index")
    success = False
    ataglance_episodes = ataglance.get_episodes(MAX_ATAGLANCE_DISPLAY_ITEMS)
    episodes = []

    for episode in ataglance_episodes:

        episodes.append(
            (plugin.url_for(play_news_item, episode.url, episode.vod_id,
                            'ataglance',
                            episode.title), episode.kodi_list_item, False))

    if len(episodes) > 0:
        xbmcplugin.addDirectoryItems(plugin.handle, episodes, len(episodes))
        kodiutils.set_video_directory_information(
            plugin.handle, xbmcplugin.SORT_METHOD_UNSORTED, "episodes")
        success = True
    return success


#
# News Programs
#


# Menu item
def add_news_programs_menu_item():
    """
    News Programs - Menu item
    """
    xbmc.log("Displaying News Programs menu item")
    art = {
        'thumb':
        "https://www3.nhk.or.jp/nhkworld/upld/thumbnails/en/news/programs/1001_2.jpg",
        'fanart':
        "https://www3.nhk.or.jp/nhkworld/common/assets/news/images/programs/newsline_2020.jpg"
    }
    list_item = xbmcgui.ListItem(kodiutils.get_string(30080), offscreen=True)
    info_labels = {}
    info_labels['mediatype'] = 'episode'
    info_labels['Plot'] = kodiutils.get_string(30081)
    list_item.setInfo('video', info_labels)
    list_item.addStreamInfo('video', kodiutils.get_sd_video_info())
    list_item.setArt(art)
    xbmcplugin.addDirectoryItem(plugin.handle,
                                plugin.url_for(news_programs_index), list_item,
                                True)
    return True


# News program list
@plugin.route('/news/programs/index')
def news_programs_index():
    """
    News Programs - Index
    """
    xbmc.log("Displaying News Programs Index")
    success = False
    programs = news_programs.get_programs()

    if len(programs) > 0:
        xbmcplugin.addDirectoryItems(plugin.handle, programs, len(programs))
        kodiutils.set_video_directory_information(
            plugin.handle, xbmcplugin.SORT_METHOD_UNSORTED, 'tvshows')
        success = True
    return success


# Add on-demand menu item
def add_on_demand_menu_item():
    """
    On-demand - Menu item
    """
    xbmc.log("Adding on-demand menu item")
    # Getting random on-demand episode to show
    featured_episodes = url.get_json(
        nhk_api.rest_url['homepage_ondemand'])['data']['items']
    no_of_epsisodes = len(featured_episodes)
    pgm_title = None
    try_count = 0
    program_json = []
    episode = Episode()

    # Find a valid random episode to highlight
    while pgm_title is None:
        try_count = try_count + 1
        xbmc.log(
            f"Check if random episode has a valid title. Try count: {try_count}"
        )
        featured_episode = random.randint(0, no_of_epsisodes - 1)
        program_json = featured_episodes[featured_episode]
        pgm_title = program_json['pgm_title_clean']

    if program_json is not None:
        episode.title = kodiutils.get_string(30020)
        episode.plot = kodiutils.get_string(30022).format(
            utils.get_episode_name(pgm_title, program_json['subtitle']))
        episode.thumb = program_json['image_sp']
        episode.fanart = program_json['image_pc']

        # Create the directory item

        episode.video_info = kodiutils.get_video_info(USE_720P)
        xbmcplugin.addDirectoryItem(plugin.handle, plugin.url_for(vod_index),
                                    episode.kodi_list_item, True)

    return episode


# Add live stream menu item
def add_live_stream_menu_item(use_720p=USE_720P):
    """[summary]
        Creates a menu item for the NHK live stream
    Args:
        use_720p ([boolean], optional): Use 720P or 1080p.
        Defaults to USE_720P from add-on settings

    Returns:
        [Episode]: Episode with the live stream
    """
    xbmc.log("Adding live stream menu item")
    program_json = url.get_json(nhk_api.rest_url['get_livestream'],
                                False)['channel']['item']

    # Add live stream text
    episode = Episode()
    episode.title = kodiutils.get_string(30030)

    # Currently playing
    row = program_json[0]

    # Schedule Information
    episode.thumb = row['thumbnail_s']
    episode.fanart = row['thumbnail']
    episode.is_playable = True
    episode.playcount = 0

    # Title and Description
    plot = f"{row['title']}\n\n{row['description']}"
    episode.plot = plot

    if use_720p:
        episode.url = nhk_api.rest_url['live_stream_url_720p']
    else:
        episode.url = nhk_api.rest_url['live_stream_url_1080p']

    episode.video_info = kodiutils.get_video_info(use_720p)
    xbmcplugin.addDirectoryItem(plugin.handle, episode.url,
                                episode.kodi_list_item, False)
    return episode


#
# Live schedule
#


# Menu item
def add_live_schedule_menu_item():
    """
    Live schedule - Menu item
    """
    xbmc.log("Adding live schedule menu item")
    program_json = url.get_json(nhk_api.rest_url['get_livestream'],
                                False)['channel']['item']

    # Featured Episode
    no_of_epsisodes = len(program_json)
    featured_episode = random.randint(1, no_of_epsisodes - 1)
    row = program_json[featured_episode]

    # Add live-schedule text
    episode = Episode()
    episode.title = kodiutils.get_string(30036)

    # Schedule Information
    episode.broadcast_start_date = row['pubDate']
    episode.broadcast_end_date = row['endDate']
    episode.thumb = row['thumbnail_s']
    episode.fanart = row['thumbnail']

    title = utils.get_schedule_title(episode.broadcast_start_date,
                                     episode.broadcast_end_date, row['title'])
    episode.plot = utils.format_plot(
        kodiutils.get_string(30022).format(title), row['description'])

    # Do not show duration
    episode.broadcast_start_date = None
    episode.broadcast_end_date = None

    episode.video_info = kodiutils.get_video_info(USE_720P)
    xbmcplugin.addDirectoryItem(plugin.handle,
                                plugin.url_for(live_schedule_index),
                                episode.kodi_list_item, True)
    return True


#
# List
#


@plugin.route('/live_schedule/index')
def live_schedule_index():
    """
    Live schedule - Index
    """
    xbmc.log('Adding live schedule index')
    program_json = url.get_json(nhk_api.rest_url['get_livestream'],
                                False)['channel']['item']
    row_count = 0
    episodes = []
    success = False
    for row in program_json:
        row_count = row_count + 1

        episode = Episode()
        # Schedule Information
        episode.broadcast_start_date = row['pubDate']
        episode.broadcast_end_date = row['endDate']

        # Live program
        episode.thumb = row['thumbnail_s']
        episode.fanart = row['thumbnail']
        episode_name = utils.get_episode_name(row['title'], row['subtitle'])
        title = utils.get_schedule_title(episode.broadcast_start_date,
                                         episode.broadcast_end_date,
                                         episode_name)

        vod_id = row['vod_id']
        episode.vod_id = vod_id
        if len(vod_id) > 0:
            # Can play on-demand -> Add "Play:" before the title
            # and make it playable
            episode.is_playable = True
            episode.title = kodiutils.get_string(30063).format(title)
        else:
            episode.title = title

        episode.plot = utils.format_plot(episode_name, row['description'])

        if episode.is_playable:
            # Display the playable episode
            episodes.append((add_playable_episode(episode,
                                                  use_cache=USE_CACHE,
                                                  use_720p=USE_720P)))
        else:
            # Simply display text
            episodes.append(
                (plugin.url_for(show_textviewer_dialog_box, episode.title,
                                episode.plot), episode.kodi_list_item, False))

    if row_count > 0:
        xbmcplugin.addDirectoryItems(plugin.handle, episodes, len(episodes))
        xbmcplugin.endOfDirectory(plugin.handle,
                                  succeeded=True,
                                  cacheToDisc=False)
        success = True

    # Used for unit testing
    return success


#
# Video On Demand menu
#


@plugin.route('/vod/index')
def vod_index():
    """
    Video On Demand - Menu item
    """
    xbmc.log("Creating Video On Demand Menu")
    art = {'thumb': NHK_ICON, 'fanart': NHK_FANART}
    # Programs
    list_item = xbmcgui.ListItem(kodiutils.get_string(30040), offscreen=True)
    list_item.setArt(art)
    xbmcplugin.addDirectoryItem(plugin.handle, plugin.url_for(vod_programs),
                                list_item, True)
    # Latest Episodes
    list_item = xbmcgui.ListItem(kodiutils.get_string(30043), offscreen=True)
    list_item.setArt(art)
    xbmcplugin.addDirectoryItem(
        plugin.handle,
        plugin.url_for(vod_episode_list, "get_latest_episodes", "None", 0,
                       xbmcplugin.SORT_METHOD_UNSORTED), list_item, True)

    # Most Watched
    list_item = xbmcgui.ListItem(kodiutils.get_string(30044), offscreen=True)
    list_item.setArt(art)
    xbmcplugin.addDirectoryItem(
        plugin.handle,
        plugin.url_for(vod_episode_list, "get_most_watched_episodes", "None",
                       0, xbmcplugin.SORT_METHOD_UNSORTED), list_item, True)

    # Documentaries
    list_item = xbmcgui.ListItem(kodiutils.get_string(30046), offscreen=True)
    list_item.setArt(art)
    xbmcplugin.addDirectoryItem(
        plugin.handle,
        plugin.url_for(vod_episode_list, "get_categories_episode_list", 15, 0,
                       xbmcplugin.SORT_METHOD_UNSORTED), list_item, True)
    # Categories
    list_item = xbmcgui.ListItem(kodiutils.get_string(30041), offscreen=True)
    list_item.setArt(art)
    xbmcplugin.addDirectoryItem(plugin.handle, plugin.url_for(vod_categories),
                                list_item, True)
    # Playlists
    list_item = xbmcgui.ListItem(kodiutils.get_string(30042), offscreen=True)
    list_item.setArt(art)
    xbmcplugin.addDirectoryItem(plugin.handle, plugin.url_for(vod_playlists),
                                list_item, True)

    # All
    list_item = xbmcgui.ListItem(kodiutils.get_string(30045), offscreen=True)
    list_item.setArt(art)
    xbmcplugin.addDirectoryItem(
        plugin.handle,
        plugin.url_for(vod_episode_list, "get_all_episodes", "None", 0,
                       xbmcplugin.SORT_METHOD_TITLE), list_item, True)

    kodiutils.set_video_directory_information(plugin.handle,
                                              xbmcplugin.SORT_METHOD_NONE,
                                              "videos")

    return True


# By Program (Programs Tab on NHK World Site)
@plugin.route('/vod/programs/')
def vod_programs():
    """VOD Programs (Programs Tab on NHK World Site)
    Returns:
        [str] -- [Last program ID added]
    """
    program_json = url.get_json(
        nhk_api.rest_url['get_programs'])['vod_programs']['programs']
    row_count = 0
    episodes = []
    program_id = None

    for program_id in program_json:
        row = program_json[program_id]
        row_count = row_count + 1
        total_episodes = int(row['total_episode'])
        if total_episodes > 0:
            # Only show programs that have at lease on episode
            episode = Episode()
            episode.title = kodiutils.get_episodelist_title(
                row['title_clean'], total_episodes)
            episode.plot = row['description_clean']
            episode.thumb = row['image']
            episode.fanart = row['image_l']
            episode.video_info = kodiutils.get_video_info(USE_720P)

            # Create the directory item
            episodes.append(
                (plugin.url_for(vod_episode_list, "get_programs_episode_list",
                                program_id, 1,
                                xbmcplugin.SORT_METHOD_UNSORTED),
                 episode.kodi_list_item, True))

    if row_count > 0:
        xbmcplugin.addDirectoryItems(plugin.handle, episodes, len(episodes))
        kodiutils.set_video_directory_information(plugin.handle,
                                                  xbmcplugin.SORT_METHOD_TITLE,
                                                  "episodes")

    # Return last program program Id - useful for unit testing
    return program_id


@plugin.route('/vod/categories/')
def vod_categories():
    """VOD Categories (Categories Tab on NHK World Site)
    Returns:
        [str] -- [Last category ID added]
    """
    api_result_json = url.get_json(nhk_api.rest_url['get_categories'])
    row_count = 0
    episodes = []
    category_id = None
    for row in api_result_json['vod_categories']:
        row_count = row_count + 1
        episode = Episode()

        episode.title = kodiutils.get_episodelist_title(
            row['name'], row['count'])
        episode.absolute_image_url = True
        episode.thumb = row['icon_l']
        episode.fanart = row['icon_l']
        episode.video_info = kodiutils.get_video_info(USE_720P)

        # Create the directory item
        category_id = row['category_id']
        episodes.append(
            (plugin.url_for(vod_episode_list, 'get_categories_episode_list',
                            category_id, 0, xbmcplugin.SORT_METHOD_UNSORTED),
             episode.kodi_list_item, True))

    if row_count > 0:
        xbmcplugin.addDirectoryItems(plugin.handle, episodes, len(episodes))
        kodiutils.set_video_directory_information(plugin.handle,
                                                  xbmcplugin.SORT_METHOD_TITLE,
                                                  'videos')

    # Return last valid category ID - useful useful for unit testing
    return category_id


@plugin.route('/vod/playlists/')
def vod_playlists():
    """VOD Playlists (Playlists Tab on NHK World Site)
    Returns:
        [str] -- [Last playlist ID added]
    """
    api_result_json = url.get_json(nhk_api.rest_url['get_playlists'])
    row_count = 0
    episodes = []
    playlist_id = None
    for row in api_result_json['data']['playlist']:
        row_count = row_count + 1

        episode = Episode()
        episode.title = kodiutils.get_episodelist_title(
            row['title_clean'], row['track_total'])
        episode.thumb = row['image_square']
        episode.fanart = row['image_square']

        playlist_id = row['playlist_id']
        episodes.append(
            (plugin.url_for(vod_episode_list, "get_playlists_episode_list",
                            playlist_id, 0, xbmcplugin.SORT_METHOD_TITLE),
             episode.kodi_list_item, True))

    if row_count > 0:
        xbmcplugin.addDirectoryItems(plugin.handle, episodes, len(episodes))
        kodiutils.set_video_directory_information(
            plugin.handle, xbmcplugin.SORT_METHOD_UNSORTED, "episodes")

    # Return last valid playlist ID - useful for unit testing
    return playlist_id


def add_playable_episode(episode, use_cache, use_720p):
    """ Add a Kodi directory item for a playable episode

    Args:
        episode ([Episode]): The episode
        use_cache ([boolean]): Use Azure episode cache
        use_720p ([boolean]): Use 720P or 1080p.
        Defaults to USE_720P from add-on settings

    Returns:
        [list]: List
    """
    # If the vod_id is in cache and cache is being used,
    # directly add the URL otherwise dynamically resolve it
    # via play_vod_episode()

    # Get episode from cache if cache is enabled
    xbmc.log(
        f"add_playable_episode: Add {episode.vod_id}, use cache: {use_cache}")
    if use_cache:
        return_value = vod.get_episode_from_cache(episode, use_720p)
        if return_value is not None:
            xbmc.log(
                f"add_playable_episode: Added {episode.vod_id} from cache")
            return return_value

    # Don't use cache or episode not in cache - need to be resolve dynamically
    play_url = plugin.url_for(resolve_vod_episode, episode.vod_id)
    xbmc.log(f"add_playable_episode: Resolved Play URL: {play_url}")
    return_value = [play_url, episode.kodi_list_item, False]
    return return_value


@plugin.route(
    '/vod/episode_list/<api_method>/<list_id>/<show_only_subtitle>/<sort_method>/'
)
def vod_episode_list(api_method,
                     list_id,
                     show_only_subtitle,
                     sort_method,
                     unit_test=False):
    """  Video On Demand - Episode List

        Creates a folded with list items based on the requested NHK API Method
        (e.g. Programs, Categories, etc.)

    Args:
        api_method ([str]): The NHK API method to use
        id ([str]): ID to use (optional)
        show_only_subtitle ([bool]): Only show subtitles
        sort_method ([str]): Sort method to use
        unit_test ([bool]): Don't add playable episodes while under unit_test

    Returns:
        [boolean] -- List was created
    """

    success = False
    episodes = vod.get_episode_list(api_method, list_id, show_only_subtitle)

    if len(episodes) > 0:
        playable_episodes = []
        if not unit_test:
            xbmc.log(
                f"vod_episode_list: {len(episodes)} episodes, use_cache: {USE_CACHE}, use_720p: {USE_720P}"
            )
            for episode in episodes:
                # Add the current episode directory item
                playable_episodes.append(
                    (add_playable_episode(episode,
                                          use_cache=USE_CACHE,
                                          use_720p=USE_720P)))

            xbmcplugin.addDirectoryItems(plugin.handle, playable_episodes,
                                         len(playable_episodes))
            sort_method = int(sort_method)
            kodiutils.set_video_directory_information(plugin.handle,
                                                      sort_method, "episodes")
        success = True

    # Used for unit testing
    return success


# Video On Demand - Resolve episode
@plugin.route('/vod/resolve_episode/<vod_id>/')
def resolve_vod_episode(vod_id, use_720p=USE_720P):
    """ Resolve a VOD episode directly from NHK

    Args:
        vod_id ([str]): The VOD Id
        use_720p ([boolean], optional): Use 720P or 1080p.
        Defaults to USE_720P from add-on settings

    Returns:
        [Episode]: The resolved Episode - only used for unit testing
    """

    episode = vod.resolve_vod_episode(vod_id, use_720p)
    if (episode is not None and episode.is_playable):
        xbmcplugin.setResolvedUrl(plugin.handle, True, episode.kodi_list_item)
        return episode


#  Play News or At A Glance Item
@plugin.route(
    '/news/play_news_item/<path:api_url>/<news_id>/<item_type>/<title>/')
def play_news_item(api_url, news_id, item_type, title):
    """ Play a news item
    can either be 'news' or 'ataglance'
    """
    xbmc.log(f"ITEM_TYPE: {item_type}")
    xbmc.log(f"API_URL: {api_url}")
    xbmc.log(f"NEWS_ID: {news_id}")
    xbmc.log(f"TITLE: {title}")

    if item_type == 'news':
        video_xml = url.get_url(api_url).text
        play_path = nhk_api.rest_url['news_video_url'].format(
            utils.get_top_stories_play_path(video_xml))
    elif item_type == 'ataglance':
        video_xml = url.get_url(api_url).text
        play_path = nhk_api.rest_url['ataglance_video_url'].format(
            utils.get_ataglance_play_path(video_xml))
    else:
        return False

    xbmc.log(f"Play Path: {play_path}")
    if play_path is not None:
        episode = Episode()
        episode.vod_id = news_id
        episode.title = title
        episode.url = play_path
        episode.video_info = kodiutils.get_sd_video_info()
        episode.is_playable = True
        xbmcplugin.setResolvedUrl(plugin.handle, True, episode.kodi_list_item)
        return True
    else:
        # Couldn't find video
        xbmc.log(f"Could not find video {api_url}")
        return False


@plugin.route('/dialog/show_textviewer_dialog_box/<title>/<plot>')
def show_textviewer_dialog_box(title: str, plot: str) -> xbmcgui.Dialog:
    """ Shows a Kodi TextViewer Dialog box (used for non playable items)

    Args:
        title (str): Episode title
        plot (str): Episode Plot
    """
    dialog = xbmcgui.Dialog()
    dialog.textviewer(heading=title, text=plot)
    return dialog
