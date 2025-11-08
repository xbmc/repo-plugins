"""
Kodi specific utils
"""

import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin

# read settings
ADDON = xbmcaddon.Addon()


def get_string(string_id):
    """Get a localized string"""
    localized_string = ADDON.getLocalizedString(string_id)

    if len(localized_string) > 0:
        return_string = localized_string
    else:
        # Running under unit test - return a unit test string
        return_string = f"UNIT TEST LOCALIZED STRING {string_id}"

    return return_string


def show_notification(title, message, time_ms=5000):
    """Show a Kodi notification to the user

    Args:
        title (str): Notification title
        message (str): Notification message
        time_ms (int): Display time in milliseconds (default 5000)
    """
    try:
        xbmcgui.Dialog().notification(
            title, message, xbmcgui.NOTIFICATION_INFO, time_ms
        )
    except Exception:
        # Fallback to log if notification fails (e.g., during unit tests)
        xbmc.log(f"Notification: {title} - {message}", xbmc.LOGINFO)


def get_video_info(stream_url=None):
    """Returns video info dict with resolution based on stream URL

    For playback, detects resolution from URL.
    For menu items, defaults to 1080p.

    Args:
        stream_url (str, optional): Stream URL to analyze for resolution.
                                   Only needed for actual playback items.

    Returns:
        dict: A video_info dict with detected resolution
    """
    # Default to 1080p for menu items and upgraded streams
    width = "1920"
    height = "1080"

    if stream_url:
        # Only detect resolution for actual playback URLs
        if "/v1.m3u8" in stream_url:
            # 1080p variant
            width = "1920"
            height = "1080"
        elif "/v2.m3u8" in stream_url or "/v3.m3u8" in stream_url:
            # 720p variants
            width = "1280"
            height = "720"
        elif "/v4.m3u8" in stream_url:
            # 360p variant
            width = "640"
            height = "360"
        elif "/v5.m3u8" in stream_url:
            # 180p variant
            width = "320"
            height = "180"
        elif "o-master.m3u8" in stream_url:
            # 1080p master playlist
            width = "1920"
            height = "1080"
        elif "master.m3u8" in stream_url:
            # 720p master playlist (fallback)
            width = "1280"
            height = "720"

    video_info = {"aspect": "1.78", "width": width, "height": height}
    return video_info


def get_sd_video_info():
    """
    Returns a SD video info array
    """
    video_info = {"aspect": "1.82", "width": "640", "height": "368"}
    return video_info


def set_video_directory_information(plugin_handle, sort_method, content_type="videos"):
    """Sets the metadata like SORT_METHOD on the
    current Kodi directory

    Arguments:
        plugin_handle {int} -- Plugin handle
        sort_method {int} -- xbmcplugin.SORT_METHOD_TITLE
        content_type {str} -- videos, episodes, tvshows, etc.
    """
    # Debug logging
    current_sort_method = xbmc.getInfoLabel("Container.SortMethod")
    xbmc.log(f"Current sort method: {current_sort_method}")
    xbmc.log(f"Requested sort method: {sort_method}")

    # Set sort method
    xbmcplugin.addSortMethod(plugin_handle, sort_method)
    if content_type != "videos":
        # Set the content to a more specific content type than videos
        xbmcplugin.setContent(plugin_handle, content_type)

    # End of Directory
    xbmcplugin.endOfDirectory(plugin_handle, succeeded=True, cacheToDisc=False)


def get_episodelist_title(title, total_episodes):
    """Returns a formatted episode list title
    Arguments:
        title {unicode} -- episode list title
        total_episodes {unicode} -- number of episodes
    Returns:
        {unicode} -- Journeys in Japan - 2 Episodes
    """

    if total_episodes == 1:
        episodelist_title = get_string(30090).format(title, total_episodes)
    else:
        episodelist_title = get_string(30091).format(title, total_episodes)
    return episodelist_title
