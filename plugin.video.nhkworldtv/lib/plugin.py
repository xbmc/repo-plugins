"""
Main plugin code
"""

import random

import routing
import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin
import xbmcvfs

from . import ataglance, kodiutils, nhk_api, topstories, url, utils, vod
from .episode import Episode

plugin = routing.Plugin()

# Global variables
ADDON = xbmcaddon.Addon()
NHK_ICON = ADDON.getAddonInfo("icon")
NHK_FANART = ADDON.getAddonInfo("fanart")

# Schedule menu images - convert relative paths to full paths for Kodi
# Use xbmcvfs.translatePath to get proper filesystem paths
ADDON_PATH = xbmcvfs.translatePath(ADDON.getAddonInfo("path"))
SCHEDULE_TODAY_THUMB = f"{ADDON_PATH}/resources/media/thumb_schedule_today.png"
SCHEDULE_TODAY_FANART = f"{ADDON_PATH}/resources/media/fanart_schedule_today.png"
SCHEDULE_PAST_THUMB = f"{ADDON_PATH}/resources/media/thumb_schedule_past.png"
SCHEDULE_PAST_FANART = f"{ADDON_PATH}/resources/media/fanart_schedule_past.png"
SCHEDULE_UPCOMING_THUMB = f"{ADDON_PATH}/resources/media/thumb_schedule_upcoming.png"
SCHEDULE_UPCOMING_FANART = f"{ADDON_PATH}/resources/media/fanart_schedule_upcoming.png"

# Default value - can be overwritten by settings
MAX_NEWS_DISPLAY_ITEMS = 0
MAX_ATAGLANCE_DISPLAY_ITEMS = 0

# Initialize the plugin with default values
xbmc.log("Initializing plug-in")
xbmc.log("initialize: Retrieving plug-in setting")
# Getting the add-on settings - these will be 0 under unit test
# Define how many items should be displayed in News
MAX_NEWS_DISPLAY_ITEMS = ADDON.getSettingInt("max_news_items")
# Define how many items should be displayed in At A Glance
MAX_ATAGLANCE_DISPLAY_ITEMS = ADDON.getSettingInt("max_ataglance_items")

if utils.UNIT_TEST:
    MAX_NEWS_DISPLAY_ITEMS = 20
    MAX_ATAGLANCE_DISPLAY_ITEMS = 800

#
# Entry point - this is called from main.py
# This function cannot be unit tested
#


def run():
    """Run the plugin"""
    plugin.run()


@plugin.route("/")
def index():
    """
    Start page of the plug-in
    """
    xbmc.log("Creating Main Menu")
    # Add menus
    add_live_stream_menu_item()
    add_on_demand_menu_item()
    add_schedule_today_menu_item()
    add_schedule_past_menu_item()
    add_schedule_upcoming_menu_item()
    add_topstories_menu_item()
    add_ataglance_menu_item()
    # Set-up view
    kodiutils.set_video_directory_information(
        plugin.handle, xbmcplugin.SORT_METHOD_UNSORTED, "tvshows"
    )
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
        xbmcplugin.addDirectoryItem(
            plugin.handle,
            plugin.url_for(topstories_index),
            menu_item.kodi_list_item,
            True,
        )
        success = True
    return success


# List
@plugin.route("/topstories/index")
def topstories_index():
    """
    Top Stories - Index
    """
    xbmc.log("Displaying Top Stories Index")
    success = False
    topstories_episodes = topstories.get_episodes(
        MAX_NEWS_DISPLAY_ITEMS, NHK_ICON, NHK_FANART
    )
    episodes = []

    for episode in topstories_episodes:
        if episode.is_playable:
            episodes.append(
                (
                    plugin.url_for(
                        play_news_item,
                        episode.url,
                        episode.vod_id,
                        "news",
                        episode.title,
                    ),
                    episode.kodi_list_item,
                    False,
                )
            )
        else:
            # No video attached to it
            episodes.append(
                (
                    plugin.url_for(
                        show_textviewer_dialog_box, episode.title, episode.plot
                    ),
                    episode.kodi_list_item,
                    False,
                )
            )

    if len(episodes) > 0:
        xbmcplugin.addDirectoryItems(plugin.handle, episodes, len(episodes))
        kodiutils.set_video_directory_information(
            plugin.handle, xbmcplugin.SORT_METHOD_UNSORTED, "episodes"
        )
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
        xbmcplugin.addDirectoryItem(
            plugin.handle,
            plugin.url_for(ataglance_index),
            menu_item.kodi_list_item,
            True,
        )
        success = True
    return success


# Episode list
@plugin.route("/ataglance/index")
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
            (
                plugin.url_for(
                    play_news_item,
                    episode.url,
                    episode.vod_id,
                    "ataglance",
                    episode.title,
                ),
                episode.kodi_list_item,
                False,
            )
        )

    if len(episodes) > 0:
        xbmcplugin.addDirectoryItems(plugin.handle, episodes, len(episodes))
        kodiutils.set_video_directory_information(
            plugin.handle, xbmcplugin.SORT_METHOD_UNSORTED, "episodes"
        )
        success = True
    return success


#
# News Programs
#


# Add on-demand menu item
def add_on_demand_menu_item():
    """Adds a single on-demand menu item to the Kodi interface

    Returns:
        Episode or None if API call fails
    """
    xbmc.log("Adding on-demand menu item")
    # Getting random on-demand episode to show
    api_result = url.get_json(nhk_api.rest_url["homepage_ondemand"])

    if api_result is None or "items" not in api_result:
        xbmc.log(
            "plugin.add_on_demand_menu_item: Failed to load on-demand data",
            xbmc.LOGERROR,
        )
        kodiutils.show_notification("NHK World TV", "Unable to load on-demand menu.")
        return None

    featured_episodes = api_result["items"]
    no_of_episodes = len(featured_episodes)

    if no_of_episodes == 0:
        xbmc.log("plugin.add_on_demand_menu_item: No episodes available", xbmc.LOGERROR)
        return None

    pgm_title = None
    try_count = 0
    program_json = {}
    episode = Episode()

    # Find a valid random episode to highlight
    while pgm_title is None and try_count < 10:  # Prevent infinite loop
        try_count = try_count + 1
        xbmc.log(f"Check if random episode has a valid title. Try count: {try_count}")
        featured_episode = random.randint(0, no_of_episodes - 1)
        program_json = featured_episodes[featured_episode]

        pgm_title = program_json.get("title")

    if pgm_title:
        episode.title = kodiutils.get_string(30020)

        sub_title = program_json.get("subtitle", "")
        episode.plot = kodiutils.get_string(30022).format(
            utils.get_episode_name(pgm_title, sub_title)
        )

        # Get images from API structure
        images_obj = program_json.get("images", {})
        if isinstance(images_obj, dict):
            images = images_obj.get("landscape", [])
            if images:
                episode.thumb = images[0].get("url", "")
                if len(images) > 1:
                    episode.fanart = images[-1].get("url", "")
                else:
                    episode.fanart = episode.thumb
            else:
                episode.thumb = ""
                episode.fanart = ""
        elif isinstance(images_obj, list) and images_obj:
            # Some endpoints return images as array directly
            episode.thumb = images_obj[0].get("url", "") if images_obj[0] else ""
            episode.fanart = (
                images_obj[-1].get("url", "") if len(images_obj) > 1 else episode.thumb
            )
        else:
            episode.thumb = ""
            episode.fanart = ""

        # Create the directory item

        episode.video_info = kodiutils.get_video_info()
        xbmcplugin.addDirectoryItem(
            plugin.handle, plugin.url_for(vod_index), episode.kodi_list_item, True
        )
    else:
        xbmc.log(
            "plugin.add_on_demand_menu_item: Could not find valid episode",
            xbmc.LOGWARNING,
        )

    return episode


# Add live stream menu item
def add_live_stream_menu_item():
    """Creates a menu item for the NHK live stream

    Returns:
        [Episode]: Episode with the live stream, or None if creation fails
    """
    xbmc.log("Adding live stream menu item")

    # Create basic live stream menu item
    episode = Episode()
    episode.title = kodiutils.get_string(30030)  # "NHK World TV Live"
    episode.plot = "Watch NHK World TV live stream"
    episode.is_playable = True
    episode.playcount = 0

    # Get live stream URL with automatic quality upgrade to 1080p
    base_url = nhk_api.rest_url["live_stream_url"]
    episode.url = url.upgrade_to_1080p(base_url)
    xbmc.log(f"Live stream URL: {episode.url}", xbmc.LOGINFO)

    # Try to get currently playing program info (optional - non-critical)
    try:
        # EPG URL requires current date in YYYYMMDD format
        from datetime import datetime

        today = datetime.now().strftime("%Y%m%d")
        epg_url = f"{nhk_api.rest_url['get_livestream']}{today}.json"
        api_result = url.get_json(epg_url, False)

        xbmc.log(f"[NHK] EPG URL: {epg_url}", xbmc.LOGINFO)
        if api_result and "data" in api_result and len(api_result["data"]) > 0:
            # Find first program with a valid thumbnail (news may not have one)
            current_program = None
            thumbnail_url = ""

            for prog in api_result["data"]:
                thumb = prog.get("episodeThumbnailURL") or prog.get("thumbnail", "")
                xbmc.log(
                    f"[NHK] Checking program: {prog.get('title', '')} thumb={thumb}",
                    xbmc.LOGINFO,
                )
                if thumb and thumb.strip():
                    current_program = prog
                    thumbnail_url = thumb
                    break

            # If we found a program with thumbnail, use it
            if current_program and thumbnail_url:
                xbmc.log(
                    f"[NHK] Using thumbnail for live: {thumbnail_url}", xbmc.LOGINFO
                )
                episode.thumb = thumbnail_url
                episode.fanart = thumbnail_url

                # Enhanced plot with current program info
                title = current_program.get("title", "")
                episode_title = current_program.get("episodeTitle", "")
                description = current_program.get("description", "")

                program_name = f"{title}: {episode_title}" if episode_title else title
                if program_name or description:
                    episode.plot = (
                        f"NOW PLAYING: {program_name}\n\n{description}"
                        if program_name and description
                        else f"NOW PLAYING: {program_name or description}"
                    )
            else:
                xbmc.log("[NHK] No valid thumbnail found for live stream", xbmc.LOGINFO)
    except Exception as e:
        # Schedule info is optional, log but continue
        xbmc.log(
            f"Could not load live stream schedule (non-critical): {e}",
            xbmc.LOGINFO,
        )

    episode.video_info = kodiutils.get_video_info(episode.url)
    xbmcplugin.addDirectoryItem(
        plugin.handle, episode.url, episode.kodi_list_item, False
    )
    return episode


#
# Schedule - Today, Past, Upcoming
#


def add_schedule_today_menu_item():
    """
    Today's Schedule - Menu item

    Returns:
        bool: True if successful, False otherwise
    """
    xbmc.log("Adding today's schedule menu item")
    episode = Episode()
    episode.title = kodiutils.get_string(30036)  # "Today's Schedule"
    # "View today's programming schedule"
    episode.plot = kodiutils.get_string(30037)
    episode.thumb = SCHEDULE_TODAY_THUMB
    episode.fanart = SCHEDULE_TODAY_FANART
    episode.video_info = kodiutils.get_video_info()

    xbmcplugin.addDirectoryItem(
        plugin.handle,
        plugin.url_for(schedule_today_index),
        episode.kodi_list_item,
        True,
    )
    return True


def add_schedule_past_menu_item():
    """
    Past Schedule - Menu item

    Returns:
        bool: True if successful, False otherwise
    """
    xbmc.log("Adding past schedule menu item")
    episode = Episode()
    episode.title = kodiutils.get_string(30038)  # "Past Schedule"
    # "View previously aired programs"
    episode.plot = kodiutils.get_string(30039)
    episode.thumb = SCHEDULE_PAST_THUMB
    episode.fanart = SCHEDULE_PAST_FANART
    episode.video_info = kodiutils.get_video_info()

    xbmcplugin.addDirectoryItem(
        plugin.handle,
        plugin.url_for(schedule_past_index),
        episode.kodi_list_item,
        True,
    )
    return True


def add_schedule_upcoming_menu_item():
    """
    Upcoming Schedule - Menu item

    Returns:
        bool: True if successful, False otherwise
    """
    xbmc.log("Adding upcoming schedule menu item")
    episode = Episode()
    episode.title = kodiutils.get_string(30040)  # "Upcoming Schedule"
    episode.plot = kodiutils.get_string(30041)  # "View upcoming programs"
    episode.thumb = SCHEDULE_UPCOMING_THUMB
    episode.fanart = SCHEDULE_UPCOMING_FANART
    episode.video_info = kodiutils.get_video_info()

    xbmcplugin.addDirectoryItem(
        plugin.handle,
        plugin.url_for(schedule_upcoming_index),
        episode.kodi_list_item,
        True,
    )
    return True


def _get_schedule_episodes(time_filter="all"):
    """
    Helper function to get schedule episodes with optional time filtering

    Args:
        time_filter (str): "past", "today", "upcoming", or "all"

    Returns:
        list: List of episode tuples for xbmcplugin.addDirectoryItems
    """
    from datetime import datetime, timezone

    # EPG URL requires current date in YYYYMMDD format
    today_str = datetime.now().strftime("%Y%m%d")
    epg_url = f"{nhk_api.rest_url['get_livestream']}{today_str}.json"

    api_result = url.get_json(epg_url, False)

    if api_result is None or "data" not in api_result:
        xbmc.log(
            f"plugin._get_schedule_episodes: Failed to load EPG ({time_filter})",
            xbmc.LOGERROR,
        )
        kodiutils.show_notification("NHK World TV", "Unable to load schedule.")
        return []

    program_json = api_result["data"]
    episodes = []
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = now.replace(hour=23, minute=59, second=59, microsecond=999999)

    for row in program_json:
        try:
            start_time_str = row.get("startTime")
            if not start_time_str:
                continue

            # Parse the broadcast start time (ISO 8601 with timezone)
            broadcast_start = datetime.fromisoformat(start_time_str)

            # Apply time filter
            if time_filter == "past" and broadcast_start >= now:
                continue
            elif time_filter == "today":
                if broadcast_start < today_start or broadcast_start > today_end:
                    continue
            elif time_filter == "upcoming" and broadcast_start <= now:
                continue

            episode = Episode()
            # Schedule Information
            episode.broadcast_start_date = row.get("startTime")
            episode.broadcast_end_date = row.get("endTime")

            # Program information
            # EPG uses different field names than VOD API
            episode.thumb = row.get("episodeThumbnailURL") or row.get("thumbnail", "")
            episode.fanart = row.get("thumbnail", "")

            # Combine title and episodeTitle
            title = row.get("title", "")
            episode_title = row.get("episodeTitle", "")
            episode_name = utils.get_episode_name(title, episode_title)

            title = utils.get_schedule_title(
                episode.broadcast_start_date, episode.broadcast_end_date, episode_name
            )

            # Check if VOD is available
            vod_flag = row.get("vodFlag", 0)
            episode_id = row.get("episodeId", "")
            episode.vod_id = episode_id
            if vod_flag == 1 and len(episode_id) > 0:
                # Can play on-demand -> Add "PLAY:" and make playable
                episode.is_playable = True
                episode.title = kodiutils.get_string(30063).format(title)
            else:
                episode.title = title

            episode.plot = utils.format_plot(episode_name, row.get("description", ""))

            if episode.is_playable:
                # Display the playable episode
                episodes.append(add_playable_episode(episode))
            else:
                # Simply display text
                episodes.append(
                    (
                        plugin.url_for(
                            show_textviewer_dialog_box, episode.title, episode.plot
                        ),
                        episode.kodi_list_item,
                        False,
                    )
                )
        except Exception as e:
            xbmc.log(
                f"plugin._get_schedule_episodes: Error processing episode: {str(e)}",
                xbmc.LOGERROR,
            )
            continue

    return episodes


@plugin.route("/schedule/today")
def schedule_today_index():
    """
    Today's Schedule - Index
    """
    xbmc.log("Displaying today's schedule")
    episodes = _get_schedule_episodes("today")

    if len(episodes) > 0:
        xbmcplugin.addDirectoryItems(plugin.handle, episodes, len(episodes))
        xbmcplugin.endOfDirectory(plugin.handle, succeeded=True, cacheToDisc=False)
        return True
    else:
        kodiutils.show_notification("NHK World TV", "No programs found for today.")
        xbmcplugin.endOfDirectory(plugin.handle, succeeded=False)
        return False


@plugin.route("/schedule/past")
def schedule_past_index():
    """
    Past Schedule - Index
    """
    xbmc.log("Displaying past schedule")
    episodes = _get_schedule_episodes("past")

    if len(episodes) > 0:
        xbmcplugin.addDirectoryItems(plugin.handle, episodes, len(episodes))
        xbmcplugin.endOfDirectory(plugin.handle, succeeded=True, cacheToDisc=False)
        return True
    else:
        kodiutils.show_notification("NHK World TV", "No past programs found.")
        xbmcplugin.endOfDirectory(plugin.handle, succeeded=False)
        return False


@plugin.route("/schedule/upcoming")
def schedule_upcoming_index():
    """
    Upcoming Schedule - Index
    """
    xbmc.log("Displaying upcoming schedule")
    episodes = _get_schedule_episodes("upcoming")

    if len(episodes) > 0:
        xbmcplugin.addDirectoryItems(plugin.handle, episodes, len(episodes))
        xbmcplugin.endOfDirectory(plugin.handle, succeeded=True, cacheToDisc=False)
        return True
    else:
        kodiutils.show_notification("NHK World TV", "No upcoming programs found.")
        xbmcplugin.endOfDirectory(plugin.handle, succeeded=False)
        return False


#
# Video On Demand menu
#


@plugin.route("/vod/index")
def vod_index():
    """
    Video On Demand - Menu item
    """
    xbmc.log("Creating Video On Demand Menu")
    art = {"thumb": NHK_ICON, "fanart": NHK_FANART}
    # Programs
    list_item = xbmcgui.ListItem(kodiutils.get_string(30042), offscreen=True)
    list_item.setArt(art)
    xbmcplugin.addDirectoryItem(
        plugin.handle, plugin.url_for(vod_programs), list_item, True
    )
    # Latest Episodes
    list_item = xbmcgui.ListItem(kodiutils.get_string(30044), offscreen=True)
    list_item.setArt(art)
    xbmcplugin.addDirectoryItem(
        plugin.handle,
        plugin.url_for(
            vod_episode_list,
            "get_latest_episodes",
            "None",
            0,
            xbmcplugin.SORT_METHOD_UNSORTED,
        ),
        list_item,
        True,
    )

    # Most Watched
    list_item = xbmcgui.ListItem(kodiutils.get_string(30045), offscreen=True)
    list_item.setArt(art)
    xbmcplugin.addDirectoryItem(
        plugin.handle,
        plugin.url_for(
            vod_episode_list,
            "get_most_watched_episodes",
            "None",
            0,
            xbmcplugin.SORT_METHOD_UNSORTED,
        ),
        list_item,
        True,
    )

    # Documentaries
    list_item = xbmcgui.ListItem(kodiutils.get_string(30047), offscreen=True)
    list_item.setArt(art)
    xbmcplugin.addDirectoryItem(
        plugin.handle,
        plugin.url_for(
            vod_episode_list,
            "get_categories_episode_list",
            15,
            0,
            xbmcplugin.SORT_METHOD_UNSORTED,
        ),
        list_item,
        True,
    )
    # Categories
    list_item = xbmcgui.ListItem(kodiutils.get_string(30043), offscreen=True)
    list_item.setArt(art)
    xbmcplugin.addDirectoryItem(
        plugin.handle, plugin.url_for(vod_categories), list_item, True
    )

    # All
    list_item = xbmcgui.ListItem(kodiutils.get_string(30046), offscreen=True)
    list_item.setArt(art)
    xbmcplugin.addDirectoryItem(
        plugin.handle,
        plugin.url_for(
            vod_episode_list,
            "get_all_episodes",
            "None",
            0,
            xbmcplugin.SORT_METHOD_TITLE,
        ),
        list_item,
        True,
    )

    kodiutils.set_video_directory_information(
        plugin.handle, xbmcplugin.SORT_METHOD_NONE, "videos"
    )

    return True


# By Program (Programs Tab on NHK World Site)
@plugin.route("/vod/programs/")
def vod_programs():
    """VOD Programs (Programs Tab on NHK World Site)
    Returns:
        [str] -- [Last program ID added]
    """
    api_result = url.get_json(nhk_api.rest_url["get_programs"])
    if api_result is None or "items" not in api_result:
        xbmc.log("VOD Programs API call failed", xbmc.LOGERROR)
        kodiutils.show_notification(
            "Error", "Unable to load programs. Please try again later."
        )
        return None

    program_json = api_result["items"]
    row_count = 0
    episodes = []
    program_id = None

    # API returns list of program objects
    for row in program_json:
        program_id = row.get("id")
        if not program_id:
            continue

        total_episodes = row.get("video_episodes", {}).get("total", 0)
        title = row.get("title", "").strip()

        # Skip programs with no episodes or no title
        if total_episodes > 0 and title:
            row_count += 1
            episode = Episode()
            episode.title = kodiutils.get_episodelist_title(title, total_episodes)
            episode.plot = row.get("description", "")

            # Get image from API structure
            images = row.get("images", {}).get("landscape", [])
            if images:
                episode.thumb = images[0].get("url", "")
                if len(images) > 1:
                    episode.fanart = images[-1].get("url", "")
                else:
                    episode.fanart = episode.thumb
            else:
                episode.thumb = ""
                episode.fanart = ""

            episode.video_info = kodiutils.get_video_info()

            episodes.append(
                (
                    plugin.url_for(
                        vod_episode_list,
                        "get_programs_episode_list",
                        program_id,
                        1,
                        xbmcplugin.SORT_METHOD_UNSORTED,
                    ),
                    episode.kodi_list_item,
                    True,
                )
            )

    if row_count > 0:
        xbmcplugin.addDirectoryItems(plugin.handle, episodes, len(episodes))
        kodiutils.set_video_directory_information(
            plugin.handle, xbmcplugin.SORT_METHOD_TITLE, "episodes"
        )

    # Return last program program Id - useful for unit testing
    return program_id


@plugin.route("/vod/categories/")
def vod_categories():
    """VOD Categories (Categories Tab on NHK World Site)
    Returns:
        [str] -- [Last category ID added]
    """
    api_result_json = url.get_json(nhk_api.rest_url["get_categories"])
    if api_result_json is None or "items" not in api_result_json:
        xbmc.log("VOD Categories API call failed", xbmc.LOGERROR)
        kodiutils.show_notification(
            "Error", "Unable to load categories. Please try again later."
        )
        return None

    categories = api_result_json["items"]
    row_count = 0
    episodes = []
    category_id = None

    for row in categories:
        row_count = row_count + 1
        episode = Episode()

        category_id = row["id"]
        total_episodes = row.get("video_episodes", {}).get("total", 0)
        episode.title = kodiutils.get_episodelist_title(row["name"], total_episodes)
        # No icon in API, use empty string
        episode.absolute_image_url = True
        episode.thumb = ""
        episode.fanart = ""

        episode.video_info = kodiutils.get_video_info()

        # Create the directory item
        episodes.append(
            (
                plugin.url_for(
                    vod_episode_list,
                    "get_categories_episode_list",
                    category_id,
                    0,
                    xbmcplugin.SORT_METHOD_UNSORTED,
                ),
                episode.kodi_list_item,
                True,
            )
        )

    if row_count > 0:
        xbmcplugin.addDirectoryItems(plugin.handle, episodes, len(episodes))
        kodiutils.set_video_directory_information(
            plugin.handle, xbmcplugin.SORT_METHOD_TITLE, "videos"
        )

    # Return last valid category ID - useful useful for unit testing
    return category_id


def add_playable_episode(episode):
    """Add a Kodi directory item for a playable episode (720p only)

    Args:
        episode ([Episode]): The episode

    Returns:
        [list]: List
    """
    # Episode needs to be resolved dynamically via play_vod_episode
    play_url = plugin.url_for(resolve_vod_episode, episode.vod_id)
    xbmc.log(f"add_playable_episode: Resolved Play URL: {play_url}")
    return_value = [play_url, episode.kodi_list_item, False]
    return return_value


@plugin.route(
    "/vod/episode_list/<api_method>/<list_id>/<show_only_subtitle>/<sort_method>/"
)
def vod_episode_list(
    api_method, list_id, show_only_subtitle, sort_method, unit_test=False
):
    """Video On Demand - Episode List

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
            xbmc.log(f"vod_episode_list: {len(episodes)} episodes")
            for episode in episodes:
                # Add the current episode directory item
                playable_episodes.append(add_playable_episode(episode))

            xbmcplugin.addDirectoryItems(
                plugin.handle, playable_episodes, len(playable_episodes)
            )
            sort_method = int(sort_method)
            kodiutils.set_video_directory_information(
                plugin.handle, sort_method, "episodes"
            )
        success = True

    # Used for unit testing
    return success


# Video On Demand - Resolve episode
@plugin.route("/vod/resolve_episode/<vod_id>/")
def resolve_vod_episode(vod_id):
    """Resolve a VOD episode directly from NHK (720p only)

    Args:
        vod_id ([str]): The VOD Id

    Returns:
        [Episode]: The resolved Episode - only used for unit testing
    """

    episode = vod.resolve_vod_episode(vod_id)
    if episode is not None and episode.is_playable:
        xbmcplugin.setResolvedUrl(plugin.handle, True, episode.kodi_list_item)
        return episode


#  Play News or At A Glance Item
@plugin.route("/news/play_news_item/<path:api_url>/<news_id>/<item_type>/<title>/")
def play_news_item(api_url, news_id, item_type, title):
    """Play a news item
    can either be 'news' or 'ataglance'
    """
    xbmc.log(f"ITEM_TYPE: {item_type}")
    xbmc.log(f"API_URL: {api_url}")
    xbmc.log(f"NEWS_ID: {news_id}")
    xbmc.log(f"TITLE: {title}")

    if item_type == "news":
        video_xml = url.get_url(api_url).text
        play_path = nhk_api.rest_url["news_video_url"].format(
            utils.get_top_stories_play_path(video_xml)
        )
    elif item_type == "ataglance":
        video_xml = url.get_url(api_url).text
        play_path = nhk_api.rest_url["ataglance_video_url"].format(
            utils.get_ataglance_play_path(video_xml)
        )
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


@plugin.route("/dialog/show_textviewer_dialog_box/<title>/<plot>")
def show_textviewer_dialog_box(title: str, plot: str) -> xbmcgui.Dialog:
    """Shows a Kodi TextViewer Dialog box (used for non playable items)

    Args:
        title (str): Episode title
        plot (str): Episode Plot
    """
    dialog = xbmcgui.Dialog()
    dialog.textviewer(heading=title, text=plot)
    return dialog
