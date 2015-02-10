# coding: utf-8
import os
import json
import urllib2
# from resources.lib import *
from urlparse import urlsplit, urlunsplit, SplitResult

import xbmcgui
import xbmcplugin
import xbmcaddon
from datetime import date
from datetime import datetime

def load_json(url):
    try:
        req = urllib2.Request(url)
        response = urllib2.urlopen(req)
    except:
        xbmc.log("plugin.audio.sverigesradio: unable to load url: " + url)
        return None, "site"
    jsonStr = response.read()
    response.close()
    try:
        out = json.loads(jsonStr)
    except:
        xbmc.log("plugin.audio.sverigesradio: malformed xml from url: " + url)
        return None, "json"
    return out, None


def load_channels():
    SRAPI_CHANNEL_URL = "http://api.sr.se/api/v2/channels?format=json&pagination=false"
    channels = load_json(SRAPI_CHANNEL_URL)
    return channels


def load_programs(channel_id='', category_id=''):
    SRAPI_PROGRAM_URL = "http://api.sr.se/api/v2/programs/index?format=json&pagination=false&filter=program.hasondemand&filterValue=true"
    url = SRAPI_PROGRAM_URL
    if channel_id:
        url = url + "&channelid=" + channel_id
    if category_id:
        url = url + "&programcategoryid=" + category_id
    programs = load_json(url)
    return programs


def load_program_broadcasts(program_id):
    __settings__ = xbmcaddon.Addon(id='plugin.audio.sverigesradio')
    QUALITIES = ["lo", "normal", "hi"]
    quality = QUALITIES[int(__settings__.getSetting("quality"))]
    SRAPI_BROADCAST_URL = "http://api.sr.se/api/v2/broadcasts?format=json&pagination=false&audioquality={0}&programid={1}"
    url = SRAPI_BROADCAST_URL.format(quality, program_id)
    broadcasts = load_json(url)
    return broadcasts


def load_program_info(program_id):
    SRAPI_PROGRAM_URL = "http://api.sr.se/api/v2/programs/{0}?format=json&pagination=false"
    url = SRAPI_PROGRAM_URL.format(program_id)
    program_info = load_json(url)
    return program_info


def load_categories():
    SRAPI_PROGRAM_CATEGORIES = "http://api.sr.se/api/v2/programcategories?format=json&pagination=false"
    return load_json(SRAPI_PROGRAM_CATEGORIES)


def add_posts(title, url, description='', thumb='', isPlayable='true', isLive='false', isFolder=False, artist='',
              album='', duration='', date_str=''):
    title = title.replace("\n", " ").encode("utf-8")
    description = description.encode("utf-8")
    listitem = xbmcgui.ListItem(title, description, iconImage=thumb)
    if date_str:
        date_object = datetime.fromtimestamp(float(int(date_str[6:-2]) / 1000)).date()
        date_strftime = date_object.strftime("%d.%m.%Y")
        listitem.setInfo(type='music', infoLabels={'title': title, 'duration': duration, 'date': date_strftime, 'artist': artist, 'album': album})
    else:
        listitem.setInfo(type='music', infoLabels={'title': title, 'duration': duration, 'artist': artist, 'album': album})
    listitem.setProperty('IsPlayable', isPlayable)
    listitem.setProperty('IsLive', isLive)
    listitem.setPath(url)
    return xbmcplugin.addDirectoryItem(HANDLE, url=url, listitem=listitem, isFolder=isFolder)


def list_live_channels():
    channels = load_channels()
    for channel in channels[0]['channels']:
        if channel['image']:
            add_posts(channel['name'], channel['liveaudio']['url'], channel['channeltype'], channel['image'],
                      isLive='true', album=channel['name'], artist='Sveriges Radio')
        else:
            add_posts(channel['name'], channel['liveaudio']['url'], channel['channeltype'], isLive='true',
                      album=channel['name'], artist='Sveriges Radio')
    xbmcplugin.endOfDirectory(HANDLE)


def list_channels():
    channel_url = "plugin://plugin.audio.sverigesradio/channel/"
    channels = load_channels()
    for channel in channels[0]['channels']:
        if channel['image']:
            add_posts(channel['name'], channel_url + str(channel['id']), isFolder=True, thumb=channel['image'])
        else:
            add_posts(channel['name'], channel_url + str(channel['id']), isFolder=True)
    xbmcplugin.endOfDirectory(HANDLE)


def list_categories():
    category_url = "plugin://plugin.audio.sverigesradio/category/"
    categories = load_categories()
    for category in categories[0]['programcategories']:
        add_posts(category['name'], category_url + str(category['id']), isFolder=True)
    xbmcplugin.endOfDirectory(HANDLE)


def list_channel_programs(channel_id):
    program_url = "plugin://plugin.audio.sverigesradio/program/"
    programs = load_programs(channel_id=channel_id)
    for program in programs[0]['programs']:
        if program['programimage']:
            add_posts(program['name'], program_url + str(program['id']), program['description'],
                      isFolder=True,
                      thumb=program['programimage'])
        else:
            add_posts(program['name'], program_url + str(program['id']), program['description'],
                      isFolder=True)
    xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_TITLE)
    xbmcplugin.endOfDirectory(HANDLE)


def list_category_programs(category_id):
    program_url = "plugin://plugin.audio.sverigesradio/program/"
    programs = load_programs(category_id=category_id)
    for program in programs[0]['programs']:
        if program['programimage']:
            add_posts(program['name'], program_url + str(program['id']), program['description'],
                      isFolder=True,
                      thumb=program['programimage'])
        else:
            add_posts(program['name'], program_url + str(program['id']), program['description'],
                      isFolder=True)
    xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_TITLE)
    xbmcplugin.endOfDirectory(HANDLE)


def list_all_programs():
    program_url = "plugin://plugin.audio.sverigesradio/program/"
    programs = load_programs()
    for program in programs[0]['programs']:
        if program['programimage']:
            add_posts(program['name'], program_url + str(program['id']), program['description'],
                      isFolder=True,
                      thumb=program['programimage'])
        else:
            add_posts(program['name'], program_url + str(program['id']), program['description'],
                      isFolder=True)
    xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_TITLE)
    xbmcplugin.endOfDirectory(HANDLE)


def list_program(program_id):
    broadcasts = load_program_broadcasts(program_id)
    program_info = load_program_info(program_id)
    program_name = program_info[0]["program"]["name"]
    for broadcast in broadcasts[0]['broadcasts']:
        if broadcast['image']:
            for file in broadcast['broadcastfiles']:
                add_posts(broadcast['title'], file['url'], broadcast['description'],
                      broadcast['image'], isLive='false', album=program_name, artist='Sveriges Radio',
                      duration=file['duration'], date_str=broadcast['broadcastdateutc'])
        else:
            for file in broadcast['broadcastfiles']:
                add_posts(broadcast['title'], file['url'], broadcast['description'],
                          isLive='false', album=program_name, artist='Sveriges Radio',
                          duration=file['duration'], date_str=broadcast['broadcastdateutc'])
    xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_TITLE)
    xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_DATE)
    xbmcplugin.endOfDirectory(HANDLE)


def add_main_menu():
    listitem = xbmcgui.ListItem("Live")
    listitem.setInfo(type='music', infoLabels={'Title': "Live"})
    listitem.setPath('live')
    u = sys.argv[0] + "live/"
    xbmcplugin.addDirectoryItem(HANDLE, url=u, listitem=listitem, isFolder=True)

    listitem = xbmcgui.ListItem("Kanaler")
    listitem.setInfo(type='music', infoLabels={'Title': "Kanaler"})
    listitem.setPath('channel')
    u = sys.argv[0] + "channels/"
    xbmcplugin.addDirectoryItem(HANDLE, url=u, listitem=listitem, isFolder=True)

    listitem = xbmcgui.ListItem("Kategorier")
    listitem.setInfo(type='music', infoLabels={'Title': "Kategorier"})
    listitem.setPath('category')
    u = sys.argv[0] + "categories/"
    xbmcplugin.addDirectoryItem(HANDLE, url=u, listitem=listitem, isFolder=True)

    listitem = xbmcgui.ListItem("Program A-Ö")
    listitem.setInfo(type='music', infoLabels={'Title': "Program A-Ö"})
    listitem.setPath('allprograms')
    u = sys.argv[0] + "allprograms/"
    xbmcplugin.addDirectoryItem(HANDLE, url=u, listitem=listitem, isFolder=True)

    return xbmcplugin.endOfDirectory(HANDLE)


if (__name__ == "__main__" ):
    MODE = sys.argv[0]
    HANDLE = int(sys.argv[1])
    modes = MODE.split('/')
    activemode = modes[len(modes) - 2]
    if activemode == "allprograms":
        list_all_programs()
    elif activemode == "live":
        list_live_channels()
    elif activemode == "channels":
        list_channels()
    elif activemode == "categories":
        list_categories()
    elif activemode == "channel":
        channel_id = modes[len(modes) - 1]
        list_channel_programs(channel_id)
    elif activemode == "category":
        category_id = modes[len(modes) - 1]
        list_category_programs(category_id)
    elif activemode == 'program':
        program_id = modes[len(modes) - 1]
        list_program(program_id)
    else:
        add_main_menu()
