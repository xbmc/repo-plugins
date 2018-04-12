#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import re
import sys
import urllib
import xbmc
import xbmcgui
import xbmcplugin

import simplejson
from . import Settings

from .helpers import *

def addDirectory(title,banner,backdrop, description,link,mode,pluginhandle):
    parameters = {"link" : link,"title" : title,"banner" : banner, "mode" : mode}
    u = sys.argv[0] + '?' + urllib.urlencode(parameters)
    createListItem(title,banner,description,'','','',u, False,True, backdrop,pluginhandle,None)

def generateAddonVideoUrl(videourl):
    return "plugin://%s/?mode=play&videourl=%s"  % (xbmcaddon.Addon().getAddonInfo('id'),videourl)

    
def createListItem(title,banner,description,duration,date,channel,videourl,playable,folder, backdrop,pluginhandle,subtitles=None,blacklist=False, contextMenuItems = None):
    contextMenuItems = contextMenuItems or []

    liz=xbmcgui.ListItem(title)
    liz.setIconImage(banner)
    liz.setThumbnailImage(banner)
    liz.setInfo( type="Video", infoLabels={ "Title": title } )
    liz.setInfo( type="Video", infoLabels={ "Tvshowtitle": title } )
    liz.setInfo( type="Video", infoLabels={ "Sorttitle": title } )
    liz.setInfo( type="Video", infoLabels={ "Plot": description } )
    liz.setInfo( type="Video", infoLabels={ "Plotoutline": description } )
    liz.setInfo( type="Video", infoLabels={ "Aired": date } )
    liz.setInfo( type="Video", infoLabels={ "Studio": channel } )
    liz.setProperty('fanart_image',backdrop)
    if playable and not folder:
        liz.setProperty('IsPlayable', 'true')
        videourl = "plugin://%s/?mode=play&videourl=%s" % (xbmcaddon.Addon().getAddonInfo('id'),videourl)
        debugLog("Videourl: %s" % videourl,"ListItem")                       

    if not folder:
        liz.setInfo( type="Video", infoLabels={ "mediatype" : 'video'})
        videoStreamInfo = {'codec': 'h264', 'aspect': 1.78}
        try:
            videoStreamInfo.update({'duration': int(duration)})
        except (TypeError, ValueError):
            debugLog("No Duration found in Video",'Info')
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
        if subtitles != None and Settings.subtitles():
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
        match = re.search(r'( - \w\w, \d\d.\d\d.\d\d\d\d)',title)
        if match != None:
            bltitle = title.split(" - ")
            bltitle = bltitle[0].split(": ")

            bl_title = bltitle[0].replace("+"," ").strip()
        else:
            bl_title = title.replace("+"," ").strip()

        blparameters = {"mode" : "blacklistShow", "link": bl_title}
        blurl = sys.argv[0] + '?' + urllib.urlencode(blparameters)
        contextMenuItems.append(('%s %s %s' % (Settings.localizedString(30038).encode("utf-8"), bl_title, Settings.localizedString(30042).encode("utf-8")), 'XBMC.RunPlugin(%s)' % blurl))
        if checkBlacklist(bl_title):
            return

    liz.addContextMenuItems(contextMenuItems)
    xbmcplugin.addDirectoryItem(pluginhandle, url=videourl, listitem=liz, isFolder=folder)
    return liz

def checkBlacklist(title):
    addonUserDataFolder = xbmc.translatePath("special://profile/addon_data/plugin.video.orftvthek");
    bl_json_file = os.path.join(addonUserDataFolder, 'blacklist.json')
    if os.path.exists(bl_json_file):
        if os.path.getsize(bl_json_file) > 0:
            data = getBlacklist(bl_json_file)
            tmp = data;
            for item in tmp:
                if item.encode('UTF-8') == title:
                    return True
    return False


def removeBlacklist(title):
    addonUserDataFolder = xbmc.translatePath("special://profile/addon_data/plugin.video.orftvthek");
    bl_json_file = os.path.join(addonUserDataFolder, 'blacklist.json')
    if os.path.exists(bl_json_file):
        if os.path.getsize(bl_json_file) > 0:
            data = getBlacklist(bl_json_file)
            tmp = data;
            for item in tmp:
                if item.encode('UTF-8') == title:
                    tmp.remove(item)
            setBlacklist(tmp,bl_json_file)

def printBlacklist(banner,backdrop,translation,pluginhandle):
    addonUserDataFolder = xbmc.translatePath("special://profile/addon_data/plugin.video.orftvthek");
    bl_json_file = os.path.join(addonUserDataFolder, 'blacklist.json')
    if os.path.exists(bl_json_file):
        if os.path.getsize(bl_json_file) > 0:
            data = getBlacklist(bl_json_file)
            for item in data:
                item = item.encode('UTF-8')
                description = translation(30040).encode('UTF-8') % item
                createListItem(item, banner, description, None, None, None, sys.argv[0] + '?' + urllib.urlencode({'link': item, 'mode': 'unblacklistShow'}), True, False, backdrop, pluginhandle)


def setBlacklist(data,file):
    with open(file,'w') as data_file:
        data_file.write(simplejson.dumps(data,'utf-8'))
    data_file.close()

def getBlacklist(file):
    data = []
    with open(file,'r') as data_file:
        data = simplejson.load(data_file,'UTF-8')
    return data

def blacklistItem(title):
    addonUserDataFolder = xbmc.translatePath("special://profile/addon_data/plugin.video.orftvthek");
    bl_json_file = os.path.join(addonUserDataFolder, 'blacklist.json')
    title = urllib.unquote(title).replace("+"," ").strip()
    #check if file exists
    if os.path.exists(bl_json_file):
        #check if file already has an entry
        if os.path.getsize(bl_json_file) > 0:
            #append value to JSON File
            if not checkBlacklist(title):
                data = getBlacklist(bl_json_file)
                data.append(title)
                setBlacklist(data,bl_json_file)
        #found empty file - writing first record
        else:
            data = []
            data.append(title)
            setBlacklist(data,bl_json_file)
    #create json file
    else:
        if not os.path.exists(addonUserDataFolder):
            os.makedirs(addonUserDataFolder)
        data = []
        data.append(title)
        setBlacklist(data,bl_json_file)


def unblacklistItem(title):
    title = urllib.unquote(title).replace("+"," ").strip()
    removeBlacklist(title)
