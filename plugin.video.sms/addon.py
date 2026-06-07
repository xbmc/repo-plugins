"""
    Copyright (C) 2020 Scott Ware
    This file is part of Scoot Media Streamer (plugin.video.sms)
    SPDX-License-Identifier: GPL-3.0-only
    See LICENSE.txt for more information
"""

################################################################################################

from operator import itemgetter
import os
import sys
import urllib
import time
import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin
import xbmcvfs

################################################################################################

addon = xbmcaddon.Addon('plugin.video.sms')
addon_path = addon.getAddonInfo('path')
libs = xbmcvfs.translatePath(os.path.join(addon_path, 'resources', 'lib'))
sys.path.append(libs)

################################################################################################

import client
import service_client
import player
import utils

################################################################################################

#
# Helper Functions
#
def buildUrl(query):
    return baseUrl + '?' + urllib.parse.urlencode(query)

def getMediaFolderType(type):
    if type is None:
        return -1
    elif type[0] == 'audio':
        return 1
    elif type[0] == 'video':
        return 2
        
def getMediaElementType(type):
    if type is None:
        return -1
    elif type[0] == 'audio':
        return 1
    elif type[0] == 'video':
        return 2


def mainMenu():
    # Music
    url = buildUrl({'content_type': 'audio'})
    item = xbmcgui.ListItem(addon.getLocalizedString(30200))
    item.setArt({ 'icon' : 'DefaultAudio.png' })
    xbmcplugin.addDirectoryItem(handle=addonHandle,
                                url=url,
                                listitem=item,
                                isFolder=True)

    # Videos
    url = buildUrl({'content_type': 'video'})
    item = xbmcgui.ListItem(addon.getLocalizedString(30201))
    item.setArt({ 'icon' : 'DefaultVideo.png' })
    xbmcplugin.addDirectoryItem(handle=addonHandle,
                                url=url,
                                listitem=item,
                                isFolder=True)

    
    
def videoMenu():
    # Media Browser
    url = buildUrl({'mode': 'media_browser', 'content_type': contentType[0]})
    item = xbmcgui.ListItem(addon.getLocalizedString(30202))
    item.setArt({ 'icon' : 'DefaultFolder.png' })
    xbmcplugin.addDirectoryItem(handle=addonHandle,
                                url=url,
                                listitem=item,
                                isFolder=True)

    # Recently Played
    url = buildUrl({'mode': 'recently_played', 'content_type': contentType[0]})
    item = xbmcgui.ListItem(addon.getLocalizedString(30203))
    item.setArt({ 'icon' : 'DefaultFolder.png' })
    xbmcplugin.addDirectoryItem(handle=addonHandle,
                                url=url,
                                listitem=item,
                                isFolder=True)

    # Recently Added
    url = buildUrl({'mode': 'recently_added', 'content_type': contentType[0]})
    item = xbmcgui.ListItem(addon.getLocalizedString(30204))
    item.setArt({ 'icon' : 'DefaultFolder.png' })
    xbmcplugin.addDirectoryItem(handle=addonHandle,
                                url=url,
                                listitem=item,
                                isFolder=True)

    xbmcplugin.endOfDirectory(addonHandle)

def audioMenu():
    # Media Browser
    url = buildUrl({'mode': 'media_browser', 'content_type': contentType[0]})
    item = xbmcgui.ListItem(addon.getLocalizedString(30202))
    item.setArt({ 'icon' : 'DefaultFolder.png' })
    xbmcplugin.addDirectoryItem(handle=addonHandle,
                                url=url,
                                listitem=item,
                                isFolder=True)

    # Recently Played
    url = buildUrl({'mode': 'recently_played', 'content_type': contentType[0]})
    item = xbmcgui.ListItem(addon.getLocalizedString(30203))
    item.setArt({ 'icon' : 'DefaultFolder.png' })
    xbmcplugin.addDirectoryItem(handle=addonHandle,
                                url=url,
                                listitem=item,
                                isFolder=True)

    # Recently Added
    url = buildUrl({'mode': 'recently_added', 'content_type': contentType[0]})
    item = xbmcgui.ListItem(addon.getLocalizedString(30204))
    item.setArt({ 'icon' : 'DefaultFolder.png' })
    xbmcplugin.addDirectoryItem(handle=addonHandle,
                                url=url,
                                listitem=item,
                                isFolder=True)
                                
    # Playlists
    url = buildUrl({'mode': 'playlists', 'content_type': contentType[0]})
    item = xbmcgui.ListItem(addon.getLocalizedString(30205))
    item.setArt({ 'icon' : 'DefaultPlaylist.png' })
    xbmcplugin.addDirectoryItem(handle=addonHandle,
                                url=url,
                                listitem=item,
                                isFolder=True)

    xbmcplugin.endOfDirectory(addonHandle)

def mediaFolders():
    folders = sms_client.getMediaFolders()
    total = len(folders)

    for folder in folders:
        if folder['type'] == mediaFolderType:
            url = buildUrl({'content_type': contentType[0], 'mode': 'media_folder', 'id': folder['id']})
            item = xbmcgui.ListItem(folder['name'])
            item.setArt({ 'icon' : 'DefaultFolder.png' })
            xbmcplugin.addDirectoryItem(handle=addonHandle,
                                        url=url,
                                        listitem=item,
                                        isFolder=True)

    xbmcplugin.endOfDirectory(addonHandle)

def recentlyPlayedList():
    elements = sms_client.getRecentlyPlayedElements(mediaElementType)
    parseMediaElements(elements, True)

def recentlyAddedList():
    elements = sms_client.getRecentlyAddedElements(mediaElementType)
    parseMediaElements(elements, True)
    
def playlists():
    playlists = sms_client.getPlaylists()
    
    for playlist in playlists:
        url = buildUrl({'content_type': contentType[0], 'mode': 'playlist', 'id': playlist['id']})
        item = xbmcgui.ListItem(playlist['name'])
        item.setArt({ 'icon' : 'DefaultPlaylist.png' })
        xbmcplugin.addDirectoryItem(handle=addonHandle,
                                    url=url,
                                    listitem=item,
                                    isFolder=True)
                                    
    xbmcplugin.endOfDirectory(addonHandle)
    
def playlistContents():
    elements = sms_client.getPlaylistContents(arguments.get('id', None)[0])
    parseMediaElements(elements, False)

def mediaFolderContents():
    elements = sms_client.getMediaFolderContents(arguments.get('id', None)[0])
    parseMediaElements(elements, False)
    
def directoryElementContents():
    elements = sms_client.getDirectoryElementContents(arguments.get('id', None)[0])
    parseMediaElements(elements, False)
    
def parseMediaElements(elements, altTitle):
    if elements is None:
        return
        
    if len(elements) == 0:
        return

    total = len(elements)

    for element in elements:
        elementType = element['type']

        # Process Title
        title = element['title']

        # Video Mode
        if contentType[0] == 'video':
            if altTitle and 'collection' in element:
                if not element['collection'] in element['title']:
                    title = element['collection'] + ' - ' + element['title']
                
            if elementType == 2:
                url = buildUrl({'content_type': contentType[0], 'mode': 'video_element','id': element['id']})
                item = xbmcgui.ListItem(title)
                item.setContentLookup(0)
                item.setProperty("IsPlayable", "true")
                item.setInfo('video', { 'title': element['title'] })
                    
                if 'rating' in element:
                    item.setInfo('video', { 'rating': element['rating'] })

                if 'tagline' in element:
                    item.setInfo('video', { 'tagline': element['tagline'] })

                if 'description' in element:
                    item.setInfo('video', { 'plot': element['description'] })
                    
                if 'certificate' in element:
                    item.setInfo('video', { 'mpaa': element['certificate'] })

                if 'year' in element:
                    item.setInfo('video', { 'year': element['year'] })

                if 'genre' in element:
                    item.setInfo('video', { 'genre': element['genre'] })

                if 'collection' in element:
                    item.setInfo('video', { 'set': element['collection'] })
            
                if 'duration' in element:
                    if utils.getVersion() < 15:
                        item.setInfo('video', { 'duration': element['duration'] // 60})
                    else:
                        item.setInfo('video', { 'duration': element['duration'] })

                item.setArt({ 'icon' : 'DefaultVideo.png', 'thumb': sms_settings['serverUrl'] + ':' + str(sms_settings['serverPort']) + '/image/' + element['id'] + '/thumbnail', 'poster': sms_settings['serverUrl'] + ':' + str(sms_settings['serverPort']) + '/image/' + element['id'] + '/cover', 'fanart' : sms_settings['serverUrl'] + ':' + str(sms_settings['serverPort']) + '/image/' + element['id'] + '/fanart?scale=' + str(xbmcgui.Window().getWidth()) })

                xbmcplugin.addDirectoryItem(handle=addonHandle,
                                            url=url,
                                            listitem=item)

            elif elementType == 4:
                if 'directoryType' in element:
                    directoryType = element['directoryType']
                else:
                    directoryType = 0

                # Ignore audio directories
                if directoryType == 1:
                    continue
                    
                url = buildUrl({'content_type': contentType[0], 'mode': 'directory_element','id': element['id']})
                item = xbmcgui.ListItem(title)
                item.setProperty("IsPlayable", "false")
                item.setInfo('video', { 'title': element['title'] })
                    
                if directoryType == 2:
                    if 'year' in element:
                        item.setInfo('video', { 'year': str(element['year']) })
            
                    if 'rating' in element:
                        item.setInfo('video', { 'rating': element['rating'] })

                    if 'tagline' in element:
                        item.setInfo('video', { 'tagline': element['tagline'] })

                    if 'description' in element:
                        item.setInfo('video', { 'plot': element['description'] })

                    if 'certificate' in element:
                        item.setInfo('video', { 'mpaa': element['certificate'] })

                    if 'genre' in element:
                        item.setInfo('video', { 'genre': element['genre'] })

                    if 'collection' in element:
                        item.setInfo('video', { 'set': element['collection'] })

                item.setArt({ 'icon' : 'DefaultFolder.png', 'thumb': sms_settings['serverUrl'] + ':' + str(sms_settings['serverPort']) + '/image/' + element['id'] + '/cover', 'poster': sms_settings['serverUrl'] + ':' + str(sms_settings['serverPort']) + '/image/' + element['id'] + '/cover', 'fanart' : sms_settings['serverUrl'] + ':' + str(sms_settings['serverPort']) + '/image/' + element['id'] + '/fanart?scale=' + str(xbmcgui.Window().getWidth()) })

                xbmcplugin.addDirectoryItem(handle=addonHandle,
                                            url=url,
                                            listitem=item,
                                            isFolder=True)

        # Audio Mode
        elif contentType[0] == 'audio':
            if altTitle and 'artist' in element:
                title = element['artist'] + ' - ' + element['title']

            if elementType == 1:
                url = buildUrl({'content_type': contentType[0], 'mode': 'audio_element','id': element['id']})
                item = xbmcgui.ListItem(title)
                item.setContentLookup(0)
                item.setProperty("IsPlayable", "true")
                item.setInfo('music', { 'title': element['title'] })
            
                if 'trackNumber' in element:
                    item.setInfo('music', { 'tracknumber': element['trackNumber'] })

                if 'discNumber' in element:
                    item.setInfo('music', { 'discnumber': element['discNumber'] })

                if 'artist' in element:
                    item.setInfo('music', { 'artist': element['artist'] })
                
                if 'album' in element:
                    item.setInfo('music', { 'album': element['album'] })

                if 'year' in element:
                    item.setInfo('music', { 'year': element['year'] })

                if 'genre' in element:
                    item.setInfo('music', { 'genre': element['genre'] })

                if 'duration' in element:
                    item.setInfo('music', { 'duration': element['duration'] })

                if 'description' in element:
                    item.setInfo('music', { 'comment': element['description'] })

                item.setArt({ 'icon' : 'DefaultAudio.png', 'thumb': sms_settings['serverUrl'] + ':' + str(sms_settings['serverPort']) + '/image/' + element['id'] + '/cover', 'poster': sms_settings['serverUrl'] + ':' + str(sms_settings['serverPort']) + '/image/' + element['id'] + '/cover', 'fanart' : sms_settings['serverUrl'] + ':' + str(sms_settings['serverPort']) + '/image/' + element['id'] + '/fanart?scale=' + str(xbmcgui.Window().getWidth()) })

                xbmcplugin.addDirectoryItem(handle=addonHandle,
                                            url=url,
                                            listitem=item)

            elif elementType == 4:
                if 'directoryType' in element:
                    directoryType = element['directoryType']
                else:
                    directoryType = 0

                # Ignore video directories
                if directoryType == 2:
                    continue
                    
                item = xbmcgui.ListItem(title)
                item.setProperty("IsPlayable", "false")
                url = buildUrl({'content_type': contentType[0], 'mode': 'directory_element','id': element['id']})

                if directoryType == 1:
                    item.setInfo('music', { 'title': element['title'] })

                    if 'artist' in element:
                        item.setInfo('music', { 'artist': element['artist'] })

                    if 'year' in element:
                        item.setInfo('music', { 'year': str(element['year']) })
                
                item.setArt({ 'icon' : 'DefaultFolder.png', 'thumb': sms_settings['serverUrl'] + ':' + str(sms_settings['serverPort']) + '/image/' + element['id'] + '/cover', 'poster': sms_settings['serverUrl'] + ':' + str(sms_settings['serverPort']) + '/image/' + element['id'] + '/cover', 'fanart' : sms_settings['serverUrl'] + ':' + str(sms_settings['serverPort']) + '/image/' + element['id'] + '/fanart?scale=' + str(xbmcgui.Window().getWidth()) })

                xbmcplugin.addDirectoryItem(handle=addonHandle,
                                            url=url,
                                            listitem=item,
                                            isFolder=True)

    xbmcplugin.endOfDirectory(addonHandle)

def playVideo():
    id = arguments.get('id', None)[0]
    element = sms_client.getMediaElement(id)
    url = sms_settings['serverUrl'] + ':' + str(sms_settings['serverPort']) + '/stream/' + str(session) + '/' + str(id)

    item = xbmcgui.ListItem(element['title'], path=url)
    item.setArt({ 'icon' : 'DefaultVideo.png', 'thumb': sms_settings['serverUrl'] + ':' + str(sms_settings['serverPort']) + '/image/' + element['id'] + '/thumbnail', 'poster': sms_settings['serverUrl'] + ':' + str(sms_settings['serverPort']) + '/image/' + element['id'] + '/cover', 'fanart' : sms_settings['serverUrl'] + ':' + str(sms_settings['serverPort']) + '/image/' + element['id'] + '/fanart?scale=' + str(xbmcgui.Window().getWidth()) })
    item.setInfo('video', { 'title': element['title'] })

    if 'rating' in element:
        item.setInfo('video', { 'rating': element['rating'] })

    if 'tagline' in element:
        item.setInfo('video', { 'tagline': element['tagline'] })

    if 'description' in element:
        item.setInfo('video', { 'plot': element['description'] })
        
    if 'certificate' in element:
        item.setInfo('video', { 'mpaa': element['certificate'] })

    if 'year' in element:
        item.setInfo('video', { 'year': element['year'] })

    if 'genre' in element:
        item.setInfo('video', { 'genre': element['genre'] })

    if 'collection' in element:
        item.setInfo('video', { 'set': element['collection'] })

    if 'duration' in element:
        if utils.getVersion() < 15:
            item.setInfo('video', { 'duration': element['duration'] // 60})
        else:
            item.setInfo('video', { 'duration': element['duration'] })

        xbmcplugin.setResolvedUrl(handle=addonHandle, succeeded=True, listitem=item)

    # Blocking call to monitor playback
    player.monitorPlayback(url, addonUrl)

    # End job
    sms_client.endJob(session, id)

    return

def playAudio():
    id = arguments.get('id', None)[0]
    element = sms_client.getMediaElement(id)
    url = sms_settings['serverUrl'] + ':' + str(sms_settings['serverPort']) + '/stream/' + str(session) + '/' + str(id)
    
    item = xbmcgui.ListItem(element['title'], path=url)
    item.setInfo('music', { 'title': element['title'] })
    item.setArt({ 'icon' : 'DefaultAudio.png', 'thumb': sms_settings['serverUrl'] + ':' + str(sms_settings['serverPort']) + '/image/' + str(id) + '/cover', 'fanart' : sms_settings['serverUrl'] + ':' + str(sms_settings['serverPort']) + '/image/' + element['id'] + '/fanart?scale=' + str(xbmcgui.Window().getWidth()) })
        
    if 'trackNumber' in element:
        item.setInfo('music', { 'tracknumber': element['trackNumber'] })

    if 'discNumber' in element:
        item.setInfo('music', { 'discnumber': element['discNumber'] })

    if 'artist' in element:
        item.setInfo('music', { 'artist': element['artist'] })
        
    if 'album' in element:
        item.setInfo('music', { 'album': element['album'] })

    if 'year' in element:
        item.setInfo('music', { 'year': element['year'] })

    if 'genre' in element:
        item.setInfo('music', { 'genre': element['genre'] })

    if 'duration' in element:
        item.setInfo('music', { 'duration': element['duration'] })

    if 'description' in element:
           item.setInfo('music', { 'comment': element['description'] })

    xbmcplugin.setResolvedUrl(handle=addonHandle, succeeded=True, listitem=item)

    # Blocking call to monitor playback
    player.monitorPlayback(url, addonUrl)

    # End job
    sms_client.endJob(session, id)

    return

#
# Main Plugin Navigation
#

if __name__ == '__main__':
        # Settings
    sms_settings = {'serverUrl': addon.getSettingString('serverUrl'), \
                    'serverPort': addon.getSettingInt('serverPort'), \
                    'username': addon.getSettingString('username'), \
                    'password': addon.getSettingString('password'), \
                    'audioQuality': addon.getSettingInt('audioQuality'), \
                    'videoQuality': addon.getSettingInt('videoQuality'), \
                    'maxSampleRate': addon.getSettingString('maxSampleRate'), \
                    'multichannel': addon.getSettingBool('multichannel'), \
                    'directPlay': addon.getSettingBool('directPlay'),
                    'servicePort': addon.getSettingInt('servicePort')}

    # XBMC Plugin URLs
    addonUrl = sys.argv[0] + sys.argv[2]
    baseUrl = sys.argv[0]
    addonHandle = int(sys.argv[1])
    arguments = urllib.parse.parse_qs(sys.argv[2][1:])

    # Server Client
    sms_client = client.RESTClient(sms_settings)

    # Service Client
    serviceClient = service_client.ServiceClient(sms_settings)

    # Test connection with server
    if not sms_client.testConnection():
        dialog = xbmcgui.Dialog().ok('Scoot Media Streamer', 'Unable to connect to server. Please check that the plugin settings are correct.')
    
        if dialog:
            addon.openSettings()
            sys.exit("Settings incorrect.")
        else:
            sys.exit("Settings incorrect.")

    # Session ID
    session = serviceClient.getSession()
    
    # Sync client settings with server
    serviceClient.update()

    # Addon Routing
    contentType = arguments.get('content_type', None)
    mediaFolderType = getMediaFolderType(contentType)
    mediaElementType = getMediaElementType(contentType)
    mode = arguments.get('mode', None)

    if mode is None:
        if contentType is None:
            mainMenu()
        elif contentType[0] == 'audio':
            audioMenu()
        elif contentType[0] == 'video':
            videoMenu()
    elif mode[0] == 'media_browser':
        mediaFolders()
    elif mode[0] == 'recently_played':
        recentlyPlayedList()
    elif mode[0] == 'recently_added':
        recentlyAddedList()
    elif mode[0] == 'playlists':
        playlists()
    elif mode[0] == 'playlist':
        playlistContents()
    elif mode[0] == 'media_folder':
        mediaFolderContents()
    elif mode[0] == 'directory_element':
        directoryElementContents()
    elif mode[0] == 'video_element':
        playVideo()
    elif mode[0] == 'audio_element':
        playAudio()
