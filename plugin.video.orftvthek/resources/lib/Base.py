#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import re

import simplejson as json
from kodi_six import xbmcplugin, xbmcgui, xbmcvfs
from kodi_six.utils import py2_encode, py2_decode
from . import Settings
from .Helpers import *


def showDialog(title, description):
    xbmcgui.Dialog().notification(title, description, xbmcaddon.Addon().getAddonInfo('icon'))


def addDirectory(title, banner, backdrop, description, link, mode, pluginhandle):
    parameters = {"link": link, "mode": mode}
    u = build_kodi_url(parameters)
    createListItem(title, banner, description, '', '', '', u, False, True, backdrop, pluginhandle, None)


def generateAddonVideoUrl(videourl):
    videourl = buildLink(videourl)
    return "plugin://%s/?mode=play&link=%s" % (xbmcaddon.Addon().getAddonInfo('id'), videourl)


def generateDRMVideoUrl(videourl, drm_lic_url):
    parameters = {"link": videourl, "mode": "playDRM", "lic_url": drm_lic_url}
    return build_kodi_url(parameters)


def buildLink(link):
    link = link.replace("https://apasfpd.apa.at", "https://apasfpd.sf.apa.at")
    if link:
        return "%s|User-Agent=%s" % (link, Settings.userAgent())
    else:
        return link


def createPlayAllItem(name, pluginhandle, stream_info=False):
    play_all_parameters = {"mode": "playlist"}
    play_all_url = build_kodi_url(play_all_parameters)
    play_all_item = xbmcgui.ListItem(label=name, offscreen=True)
    if stream_info:
        description = stream_info['description']
        play_all_item.setArt({'thumb': stream_info['teaser_image'], 'poster': stream_info['teaser_image']})
    else:
        description = ""
    play_all_item.setInfo(type="Video", infoLabels={"Title": name, "Plot": description})
    xbmcplugin.addDirectoryItem(pluginhandle, play_all_url, play_all_item, isFolder=False, totalItems=-1)


def createListItem(title, banner, description, duration, date, channel, videourl, playable, folder, backdrop, pluginhandle, subtitles=None, blacklist=False, contextMenuItems=None):
    contextMenuItems = contextMenuItems or []

    liz = xbmcgui.ListItem(label=title, label2=channel, offscreen=True)
    liz.setInfo(type="Video", infoLabels={"Title": title})
    liz.setInfo(type="Video", infoLabels={"Tvshowtitle": title})
    liz.setInfo(type="Video", infoLabels={"Sorttitle": title})
    liz.setInfo(type="Video", infoLabels={"Plot": description})
    liz.setInfo(type="Video", infoLabels={"Plotoutline": description})
    liz.setInfo(type="Video", infoLabels={"Aired": date})
    liz.setInfo(type="Video", infoLabels={"Studio": channel})
    liz.setProperty('fanart_image', backdrop)
    liz.setProperty('IsPlayable', str(playable and not folder))
    liz.setArt({'thumb': banner, 'poster': banner, 'fanart': backdrop, "icon": banner})

    if not folder:
        liz.setInfo(type="Video", infoLabels={"mediatype": 'video'})
        videoStreamInfo = {'codec': 'h264', 'aspect': 1.78}
        try:
            videoStreamInfo.update({'duration': int(duration)})
        except (TypeError, ValueError):
            debugLog("No Duration found in Video")
        if videourl.lower().endswith('_qxb.mp4') or '_qxb' in videourl.lower():
            videoStreamInfo.update({'width': 1280, 'height': 720})
        if videourl.lower().endswith('_q8c.mp4') or '_q8c' in videourl.lower():
            videoStreamInfo.update({'width': 1280, 'height': 720})
        elif videourl.lower().endswith('_q6a.mp4') or '_q6a' in videourl.lower():
            videoStreamInfo.update({'width': 960, 'height': 540})
        elif videourl.lower().endswith('_q4a.mp4') or '_q4a' in videourl.lower():
            videoStreamInfo.update({'width': 640, 'height': 360})
        else:
            videoStreamInfo.update({'width': 320, 'height': 180})
        liz.addStreamInfo('video', videoStreamInfo)

        liz.addStreamInfo('audio', {"codec": "aac", "language": "de", "channels": 2})
        if subtitles is not None and Settings.subtitles():
            if len(subtitles) > 0 and subtitles[0].endswith('.srt'):
                subtitles.pop(0)
            liz.addStreamInfo('subtitle', {"language": "de"})
            try:
                liz.setSubtitles(subtitles)
            except AttributeError:
                # setSubtitles was introduced in Helix (v14)
                # catch the error in Gotham (v13)
                pass

    if blacklist:
        match = re.search(r'( - \w\w, \d\d.\d\d.\d\d\d\d)', title)
        if match is not None:
            bltitle = title.split(" - ")
            bltitle = bltitle[0].split(": ")

            bl_title = bltitle[0].replace("+", " ").strip()
        else:
            bl_title = title.replace("+", " ").strip()

        blparameters = {"mode": "blacklistShow", "link": bl_title}
        blurl = build_kodi_url(blparameters)
        contextMenuItems.append(('%s %s %s' % (Settings.localizedString(30038).encode("utf-8"), bl_title, Settings.localizedString(30042).encode("utf-8")), 'XBMC.RunPlugin(%s)' % blurl))
        if checkBlacklist(bl_title):
            return

    liz.addContextMenuItems(contextMenuItems)
    xbmcplugin.addDirectoryItem(pluginhandle, url=videourl, listitem=liz, isFolder=folder)
    return liz


def checkBlacklist(title):
    addonUserDataFolder = xbmcvfs.translatePath("special://profile/addon_data/plugin.video.orftvthek")
    bl_json_file = os.path.join(addonUserDataFolder, 'blacklist.json')
    if os.path.exists(bl_json_file):
        if os.path.getsize(bl_json_file) > 0:
            data = getJsonFile(bl_json_file)
            tmp = data
            for item in tmp:
                if py2_decode(item) == py2_decode(title):
                    return True
    return False


def removeBlacklist(title):
    addonUserDataFolder = xbmcvfs.translatePath("special://profile/addon_data/plugin.video.orftvthek")
    bl_json_file = os.path.join(addonUserDataFolder, 'blacklist.json')
    if os.path.exists(bl_json_file):
        if os.path.getsize(bl_json_file) > 0:
            data = getJsonFile(bl_json_file)
            tmp = data
            for item in tmp:
                if item.encode('UTF-8') == title:
                    tmp.remove(item)
            saveJsonFile(tmp, bl_json_file)


def printBlacklist(banner, backdrop, translation, pluginhandle):
    addonUserDataFolder = xbmcvfs.translatePath("special://profile/addon_data/plugin.video.orftvthek")
    bl_json_file = os.path.join(addonUserDataFolder, 'blacklist.json')
    if os.path.exists(bl_json_file):
        if os.path.getsize(bl_json_file) > 0:
            data = getJsonFile(bl_json_file)
            for item in data:
                item = item.encode('UTF-8')
                description = translation(30040).encode('UTF-8') % item
                parameters = {'link': item, 'mode': 'unblacklistShow'}
                url = build_kodi_url(parameters)
                createListItem(item, banner, description, None, None, None, url, False, False, backdrop, pluginhandle)


def saveJsonFile(data, file):
    with open(file, 'w') as data_file:
        data_file.write(json.dumps(data, 'utf-8'))
    data_file.close()


def getJsonFile(file):
    with open(file, 'r') as data_file:
        data = json.load(data_file, 'UTF-8')
    return data


def blacklistItem(title):
    addonUserDataFolder = xbmcvfs.translatePath("special://profile/addon_data/plugin.video.orftvthek")
    bl_json_file = os.path.join(addonUserDataFolder, 'blacklist.json')
    title = unqoute_url(title)
    title = title.replace("+", " ").strip()
    # check if file exists
    if os.path.exists(bl_json_file):
        # check if file already has an entry
        if os.path.getsize(bl_json_file) > 0:
            # append value to JSON File
            if not checkBlacklist(title):
                data = getJsonFile(bl_json_file)
                data.append(title)
                saveJsonFile(data, bl_json_file)
        # found empty file - writing first record
        else:
            data = []
            data.append(title)
            saveJsonFile(data, bl_json_file)
    # create json file
    else:
        if not os.path.exists(addonUserDataFolder):
            os.makedirs(addonUserDataFolder)
        data = []
        data.append(title)
        saveJsonFile(data, bl_json_file)


def unblacklistItem(title):
    title = unqoute_url(title)
    title = title.replace("+", " ").strip()
    removeBlacklist(title)


def isBlacklisted(title):
    title = unqoute_url(title)
    title = py2_decode(title.replace("+", " ").strip())
    return checkBlacklist(title)


def searchHistoryPush(title):
    addonUserDataFolder = xbmcvfs.translatePath("special://profile/addon_data/plugin.video.orftvthek")
    json_file = os.path.join(addonUserDataFolder, 'searchhistory.json')
    title = unqoute_url(title)
    title = title.replace("+", " ").strip()
    # check if file exists
    if os.path.exists(json_file):
        # check if file already has an entry
        if os.path.getsize(json_file) > 0:
            # append value to JSON File
            data = getJsonFile(json_file)
            data.append(title)
            saveJsonFile(data, json_file)
        # found empty file - writing first record
        else:
            data = []
            data.append(title)
            saveJsonFile(data, json_file)
    # create json file
    else:
        if not os.path.exists(addonUserDataFolder):
            os.makedirs(addonUserDataFolder)
        data = []
        data.append(title)
        saveJsonFile(data, json_file)

def searchHistoryGet():
    addonUserDataFolder = xbmcvfs.translatePath("special://profile/addon_data/plugin.video.orftvthek")
    json_file = os.path.join(addonUserDataFolder, 'searchhistory.json')
    if os.path.exists(json_file):
        if os.path.getsize(json_file) > 0:
            data = getJsonFile(json_file)
            return data
    return []