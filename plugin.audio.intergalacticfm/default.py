import os
import shutil
import sys
import urllib2
import urlparse
import xml.etree.ElementTree as ET
import time

from lib.channel import Channel
import xbmcaddon
from xbmcgui import ListItem
import xbmcplugin
import xbmcgui
import xbmc
from xbmcplugin import SORT_METHOD_LISTENERS, SORT_METHOD_UNSORTED, SORT_METHOD_GENRE
import xbmcvfs


CHANNELS_FILE_NAME = "channels.xml"

__addon__ = "Intergalactic FM"
__addonid__ = "plugin.audio.intergalacticfm"

__ms_per_day__ = 24 * 60 * 60 * 1000


def log(msg):
    xbmc.log(str(msg), level=xbmc.LOGDEBUG)


log(sys.argv)

#rootURL = "https://intergalactic.fm/"
rootURL = "http://intergalacticfm.net/"
tempdir = xbmc.translatePath("special://home/userdata/addon_data/%s" % __addonid__)
xbmcvfs.mkdirs(tempdir)

LOCAL_CHANNELS_FILE_PATH = os.path.join(tempdir, CHANNELS_FILE_NAME)

try:
    plugin_url = sys.argv[0]
    handle = int(sys.argv[1])
    query = sys.argv[2]
except:
    plugin_url = "plugin://" + __addonid__
    handle = 0
    query = ""


def fetch_remote_channel_data():
    response = urllib2.urlopen(rootURL + CHANNELS_FILE_NAME)
#    response = urllib2.urlopen('https://raw.githubusercontent.com/intergalacticfm/online-radio-channels/master/examples/intergalacticfm.xml')
    channel_data = response.read()
    response.close()
    with open(LOCAL_CHANNELS_FILE_PATH, 'w') as local_channels_xml:
        local_channels_xml.write(channel_data)
    return channel_data


def fetch_local_channel_data():
    with open(LOCAL_CHANNELS_FILE_PATH) as local_channels_file:
        return local_channels_file.read()


def fetch_cached_channel_data():
    if os.path.getmtime(LOCAL_CHANNELS_FILE_PATH) + cache_ttl_in_ms() > time.time():
        print("Using cached channel.xml")
        return fetch_local_channel_data()
    # don't delete the cached file so we can still use it as a fallback
    # if something goes wrong fetching the channel data from server


def fetch_channel_data(*strategies):
    for strategy in strategies:
        try:
            result = strategy()
            if result is not None:
                return result
        except:
            pass


def build_directory():
    channel_data = fetch_channel_data(fetch_cached_channel_data, fetch_remote_channel_data, fetch_local_channel_data)
    xml_data = ET.fromstring(channel_data)

    stations = xml_data.findall(".//channel")
    for station in stations:
        channel = Channel(handle, tempdir, station)
        li = xbmcgui.ListItem(
            channel.get_simple_element('title'),
            channel.get_simple_element('description'),
            channel.geticon(),
            channel.getthumbnail(),
            plugin_url + channel.getid())
        li.setArt({"fanart": xbmc.translatePath("special://home/addons/%s/fanart.jpg" % __addonid__)})

        li.setProperty("IsPlayable", "true")

        for element, info in [('listeners', 'listeners'),
                              ('genre', 'genre'),
                              ('dj', 'artist'),
                              ('description', 'comment'),
                              ('title', 'title')]:
            value = channel.get_simple_element(element)
            li.setInfo("Music", {info: value})

        xbmcplugin.addDirectoryItem(
            handle=handle,
            url=plugin_url + channel.getid(),
            listitem=li,
            totalItems=len(stations))
    xbmcplugin.addSortMethod(handle, SORT_METHOD_UNSORTED)
    xbmcplugin.addSortMethod(handle, SORT_METHOD_LISTENERS)
    xbmcplugin.addSortMethod(handle, SORT_METHOD_GENRE)


def format_priority():
    setting = xbmcplugin.getSetting(handle, "priority_format")
    result = [["mp3"], ["mp3", "aac"], ["aac", "mp3"], ["aac"], ][int(setting)]
    print("Format setting is %s, using priority %s" % (setting, str(result)))
    return result


def quality_priority():
    setting = xbmcplugin.getSetting(handle, "priority_quality")
    result = [['slowpls', 'fastpls', 'highestpls', ],
              ['fastpls', 'slowpls', 'highestpls', ],
              ['fastpls', 'highestpls', 'slowpls', ],
              ['highestpls', 'fastpls', 'slowpls', ], ][int(setting)]
    print("Quality setting is %s, using priority %s" % (setting, str(result)))
    return result


def cache_ttl_in_ms():
    setting = xbmcplugin.getSetting(handle, "cache_ttl")
    result = [0, __ms_per_day__, 7 * __ms_per_day__, 30 * __ms_per_day__][int(setting)]
    print("Cache setting is %s, using ttl of %dms" % (setting, result))
    return result


def play(item_to_play):
    channel_data = fetch_channel_data(fetch_local_channel_data, fetch_remote_channel_data)
    xml_data = ET.fromstring(channel_data)
    try:
        channel_data = xml_data.find(".//channel[@id='" + item_to_play + "']")
        channel = Channel(handle, tempdir, channel_data, quality_priority(), format_priority())
    except:
        for element in xml_data.findall(".//channel"):
            channel = Channel(handle, tempdir, element, quality_priority(), format_priority())
            if channel.getid() == item_to_play:
                break

    list_item = ListItem(channel.get_simple_element('title'),
                         channel.get_simple_element('description'),
                         channel.geticon(),
                         channel.getthumbnail(),
                         channel.get_content_url())
    list_item.setArt({"fanart": xbmc.translatePath("special://home/addons/%s/fanart.jpg" % __addonid__)})
    xbmcplugin.setResolvedUrl(handle, True, list_item)


def clearcache():
    shutil.rmtree(tempdir, True)
    addon = xbmcaddon.Addon(id=__addonid__)
    heading = addon.getLocalizedString(32004)
    message = addon.getLocalizedString(32005)
    xbmcgui.Dialog().notification(
        heading, message, xbmcgui.NOTIFICATION_INFO, 1000)


if handle == 0:
    if query == "clearcache":
        clearcache()
    else:
        print(query)
else:
    path = urlparse.urlparse(plugin_url).path
    item_to_play = os.path.basename(path)

    if item_to_play:
        play(item_to_play)
    else:
        build_directory()

    xbmcplugin.endOfDirectory(handle)
