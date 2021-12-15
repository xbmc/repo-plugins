import os
import shutil
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin
import xbmcvfs
from xbmcgui import ListItem
from xbmcplugin import SORT_METHOD_GENRE, SORT_METHOD_LISTENERS, SORT_METHOD_UNSORTED

from resources.lib.channel import Channel

CHANNELS_FILE_NAME = "channels.xml"

__addon__ = "SomaFM"
__addonid__ = "plugin.audio.somafm"
__version__ = "2.0.0"

__ms_per_day__ = 24 * 60 * 60 * 1000


def log(msg):
    xbmc.log(str(msg), level=xbmc.LOGDEBUG)


log(sys.argv)

rootURL = "https://somafm.com/"
tempdir = xbmcvfs.translatePath("special://home/userdata/addon_data/%s" % __addonid__)
xbmcvfs.mkdirs(tempdir)

LOCAL_CHANNELS_FILE_PATH = os.path.join(tempdir, CHANNELS_FILE_NAME)

try:
    plugin_url = sys.argv[0]
    handle = int(sys.argv[1])
    query = sys.argv[2]
except Exception as e:
    xbmc.log(f"Initialization Failed: {e}", level=xbmc.LOGERROR)
    plugin_url = "plugin://" + __addonid__
    handle = 0
    query = ""


def fetch_remote_channel_data():
    with urllib.request.urlopen(rootURL + CHANNELS_FILE_NAME) as response:
        channel_data = response.read()
        with open(LOCAL_CHANNELS_FILE_PATH, "w") as local_channels_xml:
            local_channels_xml.write(channel_data.decode("utf-8"))
        return channel_data


def fetch_local_channel_data():
    with open(LOCAL_CHANNELS_FILE_PATH) as local_channels_file:
        return local_channels_file.read()


def fetch_cached_channel_data():
    if os.path.getmtime(LOCAL_CHANNELS_FILE_PATH) + cache_ttl_in_ms() > time.time():
        return fetch_local_channel_data()
    # don't delete the cached file so we can still use it as a fallback
    # if something goes wrong fetching the channel data from server


def fetch_channel_data(*strategies):
    for strategy in strategies:
        try:
            result = strategy()
            if result is not None:
                return result
        except Exception as e:
            xbmc.log(f"fetch_channel_data Failed: {e}", level=xbmc.LOGERROR)


def build_directory():
    channel_data = fetch_channel_data(
        fetch_cached_channel_data, fetch_remote_channel_data, fetch_local_channel_data
    )
    xml_data = ET.fromstring(channel_data)

    stations = xml_data.findall(".//channel")
    for station in stations:
        channel = Channel(handle, tempdir, station)
        li = xbmcgui.ListItem(
            channel.get_simple_element("title"),
            channel.get_simple_element("description"),
            plugin_url + channel.getid(),
        )

        li.setArt(
            {
                "icon": channel.geticon(),
                "thumb": channel.getthumbnail(),
                "fanart": xbmcvfs.translatePath(
                    "special://home/addons/%s/fanart.jpg" % __addonid__
                ),
            }
        )

        li.setProperty("IsPlayable", "true")

        for element, info in [
            ("listeners", "listeners"),
            ("genre", "genre"),
            ("dj", "artist"),
            ("description", "comment"),
            ("title", "title"),
        ]:
            value = channel.get_simple_element(element)
            li.setInfo("Music", {info: value})

        xbmcplugin.addDirectoryItem(
            handle=handle,
            url=plugin_url + channel.getid(),
            listitem=li,
            totalItems=len(stations),
        )
    xbmcplugin.addSortMethod(handle, SORT_METHOD_UNSORTED)
    xbmcplugin.addSortMethod(handle, SORT_METHOD_LISTENERS)
    xbmcplugin.addSortMethod(handle, SORT_METHOD_GENRE)


def format_priority():
    setting = xbmcplugin.getSetting(handle, "priority_format")
    result = [
        ["mp3"],
        ["mp3", "aac"],
        ["aac", "mp3"],
        ["aac"],
    ][int(setting)]
    xbmc.log(
        f"Format setting is {setting}, using priority {result}", level=xbmc.LOGDEBUG
    )
    return result


def quality_priority():
    setting = xbmcplugin.getSetting(handle, "priority_quality")
    result = [
        [
            "slowpls",
            "fastpls",
            "highestpls",
        ],
        [
            "fastpls",
            "slowpls",
            "highestpls",
        ],
        [
            "fastpls",
            "highestpls",
            "slowpls",
        ],
        [
            "highestpls",
            "fastpls",
            "slowpls",
        ],
    ][int(setting)]
    xbmc.log(
        f"Quality setting is {setting}, using priority {result}", level=xbmc.LOGDEBUG
    )
    return result


def cache_ttl_in_ms():
    setting = xbmcplugin.getSetting(handle, "cache_ttl")
    result = [0, __ms_per_day__, 7 * __ms_per_day__, 30 * __ms_per_day__][int(setting)]
    xbmc.log(f"Cache setting is {setting}, using ttl of {result}", level=xbmc.LOGDEBUG)
    return result


def play(item_to_play):
    channel_data = fetch_channel_data(
        fetch_local_channel_data, fetch_remote_channel_data
    )
    xml_data = ET.fromstring(channel_data)
    try:
        channel_data = xml_data.find(".//channel[@id='" + item_to_play + "']")
        channel = Channel(
            handle, tempdir, channel_data, quality_priority(), format_priority()
        )
    except:
        for element in xml_data.findall(".//channel"):
            channel = Channel(
                handle, tempdir, element, quality_priority(), format_priority()
            )
            if channel.getid() == item_to_play:
                break

    list_item = ListItem(
        channel.get_simple_element("title"),
        channel.get_simple_element("description"),
        channel.get_content_url(),
    )

    list_item.setArt(
        {
            "icon": channel.geticon(),
            "thumb": channel.getthumbnail(),
            "fanart": xbmcvfs.translatePath(
                "special://home/addons/%s/fanart.jpg" % __addonid__
            ),
        }
    )

    xbmcplugin.setResolvedUrl(handle, True, list_item)


def clearcache():
    shutil.rmtree(tempdir, True)
    addon = xbmcaddon.Addon(id=__addonid__)
    heading = addon.getLocalizedString(32004)
    message = addon.getLocalizedString(32005)
    xbmcgui.Dialog().notification(heading, message, xbmcgui.NOTIFICATION_INFO, 1000)


def run():
    if handle == 0:
        if query == "clearcache":
            clearcache()
        else:
            xbmc.log(f"Unexpected query supplied: {query}", level=xbmc.LOGDEBUG)
    else:
        path = urllib.parse.urlparse(plugin_url).path
        item_to_play = os.path.basename(path)

        if item_to_play:
            play(item_to_play)
        else:
            build_directory()

        xbmcplugin.endOfDirectory(handle)
