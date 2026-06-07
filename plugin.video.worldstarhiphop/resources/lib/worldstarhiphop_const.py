#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import sys
import os
import xbmc
import xbmcgui
import xbmcaddon
import urllib.parse
from bs4 import BeautifulSoup

#
# Constants
#
ADDON = "plugin.video.worldstarhiphop"
SETTINGS = xbmcaddon.Addon()
LANGUAGE = SETTINGS.getLocalizedString
BASE_URL_WSHH = "https://worldstarhiphop.com"
INITIAL_API_VIDEO_URL = "https://api-mobile.worldstar.com/video/feed?daysSize=2&heroVideosSize=3&clean=false&pageCursor="
INITIAL_API_SEARCH_URL = "https://api-mobile.worldstar.com/search/suggestion?searchTerm=<search_string>&pageSize=40&filter=newest&clean=false"
IMAGES_PATH = os.path.join(xbmcaddon.Addon().getAddonInfo('path'), 'resources')
HEADERS = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}
DATE = "2025-07-01"
VERSION = "1.0.16"


if sys.version_info[0] > 2:
    unicode = str


def convertToUnicodeString(s, encoding='utf-8'):
    """Safe decode byte strings to Unicode"""
    if isinstance(s, bytes):  # This works in Python 2.7 and 3+
        s = s.decode(encoding)
    return s


def convertToByteString(s, encoding='utf-8'):
    """Safe encode Unicode strings to bytes"""
    if isinstance(s, unicode):
        s = s.encode(encoding)
    return s


def log(name_object, object):
    try:
        xbmc.log(f"[ADDON] {ADDON} v{VERSION} ({DATE}) debug mode, {name_object} = {convertToUnicodeString(object)}", xbmc.LOGDEBUG)
    except:
        xbmc.log(f"[ADDON] {ADDON} v{VERSION} ({DATE}) debug mode, {name_object} = Unable to log the object due to an error while converting it to an unicode string", xbmc.LOGDEBUG)


def getSoup(html, default_parser="html5lib"):
    soup = BeautifulSoup(html, default_parser)
    return soup


def create_video_list_item(video_data, addon_name, images_path, log):
    """
    Creates and configures an xbmcgui.ListItem for a video.

    Args:
        video_data (dict): Dictionary containing video information.
        addon_name (str): The name of the addon.
        images_path (str): Path to the addon's images.
        log (function): The logging function to use.

    Returns:
        xbmcgui.ListItem: The configured list item, or None if data is malformed.
    """
    try:
        title = video_data.get('title', '')
        title_highlight = video_data.get('titleHighlight', '')
        description = video_data.get('description', '')
        duration = video_data.get('duration', 0)
        thumbnail_url = video_data.get('imageUrl', '')
    except KeyError as e:
        log("ERROR", f"Missing key in video data: {e}")
        return None  # Return None if data is malformed

    log("title", title)
    log("title_highlight", title_highlight)
    log("description", description)
    log("duration", duration)
    log("thumbnail_url", thumbnail_url)

    if title_highlight == "":
        plot = description
    else:
        plot = title_highlight

    log("plot", plot)

    list_item = xbmcgui.ListItem(title)
    list_item.setInfo("video", {
        "title": title,
        "studio": addon_name,
        "plot": plot,
        "duration": duration
    })
    list_item.setArt({
        'thumb': thumbnail_url,
        'icon': thumbnail_url,
        'fanart': os.path.join(images_path, 'fanart-blur.jpg')
    })
    list_item.setProperty('IsPlayable', 'true')

    # Add refresh option to context menu
    list_item.addContextMenuItems([('Refresh', 'Container.Refresh')])

    return list_item

def add_video_to_listing(video_data, plugin_url, listing, addon_name, images_path, log):
    """
    Processes a video dictionary, creates a list item, and appends it to the listing.

    Args:
        video_data (dict): Dictionary containing video information.
        plugin_url (str): The base plugin URL.
        listing (list): The list to append the new list item to.
        addon_name (str): The name of the addon.
        images_path (str): Path to the addon's images.
        log (function): The logging function to use.
    """
    list_item = create_video_list_item(video_data, addon_name, images_path, log)
    # Skip if list item creation failed
    if list_item is None:
        return

    video_url = video_data.get('videoUrl', '')

    log("video_url", video_url)

    parameters = {"action": "play", "video_page_url": video_url}
    url = f"{plugin_url}?{urllib.parse.urlencode(parameters)}"
    is_folder = False

    # Add our item to the listing as a 3-element tuple.
    listing.append((url, list_item, is_folder))