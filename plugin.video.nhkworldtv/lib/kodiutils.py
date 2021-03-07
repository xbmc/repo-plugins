from __future__ import (absolute_import, unicode_literals)
from kodi_six import xbmc, xbmcaddon, xbmcplugin

# read settings
ADDON = xbmcaddon.Addon()


def get_string(string_id):
    localized_string = ADDON.getLocalizedString(string_id)
    if len(localized_string) > 0:
        return localized_string
    else:
        # Running under unit test - return a unit test string
        returnString = 'UNIT TEST LOCALIZED STRING {0}'.format(string_id)
        return returnString


def get_video_info(use_720p):
    """ Returns a list item video info

    Args:
        use720p ([boolean]): Use 720P or 1080p.

    Returns:
        [dict]: A video_info dict
    """
    if (use_720p):
        return (__get_720_HD_video_info())
    else:
        return (__get_1080_HD_video_info())


# Returns a Full-HD (1080p) video info array
def __get_1080_HD_video_info():
    video_info = {'aspect': '1.78', 'width': '1920', 'height': '1080'}
    return (video_info)


# Returns a HD (720p) video info array
def __get_720_HD_video_info():
    video_info = {'aspect': '1.78', 'width': '1280', 'height': '720'}
    return (video_info)


# Returns a SD video info array
def get_SD_video_info():
    video_info = {'aspect': '1.82', 'width': '640', 'height': '368'}
    return (video_info)


def set_video_directory_information(plugin_handle,
                                    sort_method,
                                    content_type='videos'):
    """Sets the metadate like SORT_METHOD on the
    current Kodi directory

    Arguments:
        plugin_handle {int} -- Plugin handle
        sort_method {int} -- xbmcplugin.SORT_METHOD_TITLE
        content_type {str} -- videos, episodes, tvshows, etc.
    """
    # Debug logging
    current_sort_method = xbmc.getInfoLabel('Container.SortMethod')
    xbmc.log('Current sort method: {0}'.format(current_sort_method))
    xbmc.log('Requested sort method: {0}'.format(sort_method))

    # Set sort method
    xbmcplugin.addSortMethod(plugin_handle, sort_method)
    if (content_type != 'videos'):
        # Set the content to a more specific content type than videos
        xbmcplugin.setContent(plugin_handle, content_type)

    # End of Directory
    xbmcplugin.endOfDirectory(plugin_handle, succeeded=True, cacheToDisc=False)


def get_episodelist_title(title, total_episodes):
    """Returns a formated episode list title
    Arguments:
        title {unicode} -- episode list title
        total_episodes {unicode} -- number of episodes
    Returns:
        {unicode} -- Journeys in Japan - 2 Episodes
    """

    if (total_episodes == 1):
        episodelist_title = get_string(30090).format(title, total_episodes)
    else:
        episodelist_title = get_string(30091).format(title, total_episodes)
    return (episodelist_title)
