#!/usr/bin/python
# -*- coding: utf-8 -*-

import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin

from .app_common import log, defaultbanner, addon_handle, addon_url, translate, showNotification, kodiVersion, installAddon

from .utils import cleanText, encodeUrl

_itemsToAdd = []


def get_InputStreamHelper(drm):
    streamHelper = None

    if kodiVersion >= 17:
        try:
            import inputstreamhelper
        except:
            installAddon('script.module.inputstreamhelper')
            return streamHelper

    try:
        streamHelper = inputstreamhelper.Helper('mpd', drm=drm)
    except Exception as ex:
        if ex == 'UnsupportedDRMScheme' and drm == 'com.microsoft.playready':
            streamHelper = inputstreamhelper.Helper('mpd', drm=None)
            pass
        else:
            showNotification(translate(30018).format(drm), notificationType='ERROR')

    if streamHelper and not streamHelper._has_inputstream():
        # install inputstream
        xbmc.executebuiltin(
            'InstallAddon(' + streamHelper.inputstream_addon + ')', True)

    return streamHelper


def addElement(title, fanart, icon, description, link, mode, channel='', duration=None, date='', isFolder=True,
               subtitles=None, width=768, height=432, showID=None):
    if fanart == '':
        fanart = defaultbanner
    if icon == '':
        icon = defaultbanner
    if description == '':
        description = (translate(30004))

    description = cleanText(description)
    title = cleanText(title)

    list_item = xbmcgui.ListItem(title)
    list_item.setInfo('video', {'title': title,
                                'Tvshowtitle': title,
                                'Sorttitle': title,
                                'Plot': description,
                                'Plotoutline': description,
                                'Aired': date,
                                'Studio': channel})

    list_item.setArt({'thumb': icon, 'icon': icon, 'fanart': fanart})
    list_item.setProperty('IsPlayable', str(not isFolder))

    if not duration:
        duration = 0
    if not isFolder:
        list_item.setInfo(type='Video', infoLabels={'mediatype': 'video'})
        list_item.addStreamInfo('video', {'codec': 'h264', 'duration': int(
            duration), 'aspect': 1.78, 'width': width, 'height': height})
        list_item.addStreamInfo(
            'audio', {'codec': 'aac', 'language': 'de', 'channels': 2})
        if subtitles != None:
            list_item.addStreamInfo('subtitle', {'language': 'de'})

    parameters = {'link': link, 'mode': mode, 'showID': showID}
    url = addon_url + '?' + encodeUrl(parameters)

    global _itemsToAdd
    _itemsToAdd.append((url, list_item, isFolder))


def addItemsToKodi(sort):
    xbmcplugin.setPluginCategory(addon_handle, 'Show')
    xbmcplugin.setContent(addon_handle, 'videos')
    xbmcplugin.addDirectoryItems(addon_handle, _itemsToAdd, len(_itemsToAdd))
    if sort:
        xbmcplugin.addSortMethod(
            addon_handle, xbmcplugin.SORT_METHOD_VIDEO_TITLE)
    xbmcplugin.endOfDirectory(addon_handle)
    log('callback done')


def play_video(url):
    play_item = xbmcgui.ListItem(path=url)
    xbmcplugin.setResolvedUrl(addon_handle, True, listitem=play_item)
    log('callback done')


def play_liveStream(path, addon, drm, tkn):
    play_item = xbmcgui.ListItem(path=path)
    play_item.setProperty('inputstreamaddon', addon)
    play_item.setProperty('inputstream.adaptive.manifest_type', 'mpd')
    play_item.setProperty('inputstream.adaptive.license_type', drm)
    play_item.setProperty(
        'inputstream.adaptive.manifest_update_parameter', 'full')
    play_item.setProperty('inputstream.adaptive.license_key', tkn)
    xbmcplugin.setResolvedUrl(addon_handle, True, listitem=play_item)
    log('callback done')
