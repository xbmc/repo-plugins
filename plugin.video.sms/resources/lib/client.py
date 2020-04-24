"""
    Copyright (C) 2020 Scott Ware
    This file is part of Scoot Media Streamer (plugin.video.sms)
    SPDX-License-Identifier: GPL-3.0-only
    See LICENSE.txt for more information
"""

import requests
import xbmcaddon
import xbmcgui

class RESTClient(object):
    addon = None
    settings = None

    def __init__(self, settings):
        self.addon = xbmcaddon.Addon()
        self.settings = settings

    def testConnection(self):
        if testUrl(self.settings):
            return True

        return False

    def getRecentlyAddedElements(self, type):
        try:
            response = requests.get(self.settings['serverUrl'] + ':' + str(self.settings['serverPort']) + '/media/recentlyadded/50?type=' + str(type), auth=(self.settings['username'], self.settings['password']))
            response.raise_for_status()
            data = response.json()
            return data
        except requests.exceptions.RequestException:
            xbmcgui.Dialog().notification(self.addon.getLocalizedString(30100), self.addon.getLocalizedString(30101), xbmcgui.NOTIFICATION_ERROR, 5000)

    def getRecentlyPlayedElements(self, type):
        try:
            response = requests.get(self.settings['serverUrl'] + ':' + str(self.settings['serverPort']) + '/media/recentlyplayed/50?type=' + str(type), auth=(self.settings['username'], self.settings['password']))
            response.raise_for_status()
            data = response.json()
            return data
        except requests.exceptions.RequestException:
            xbmcgui.Dialog().notification(self.addon.getLocalizedString(30100), self.addon.getLocalizedString(30102), xbmcgui.NOTIFICATION_ERROR, 5000)

    def getMediaFolders(self):
        try:
            response = requests.get(self.settings['serverUrl'] + ':' + str(self.settings['serverPort']) + '/media/folder', auth=(self.settings['username'], self.settings['password']))
            response.raise_for_status()
            data = response.json()
            return data
        except requests.exceptions.RequestException:
            xbmcgui.Dialog().notification(self.addon.getLocalizedString(30100), self.addon.getLocalizedString(30103), xbmcgui.NOTIFICATION_ERROR, 5000)

    def getMediaFolderContents(self, id):
        try:
            response = requests.get(self.settings['serverUrl'] + ':' + str(self.settings['serverPort']) + '/media/folder/' + str(id) + '/contents', auth=(self.settings['username'], self.settings['password']))
            response.raise_for_status()
            data = response.json()
            return data
        except requests.exceptions.RequestException:
            xbmcgui.Dialog().notification(self.addon.getLocalizedString(30100), self.addon.getLocalizedString(30104), xbmcgui.NOTIFICATION_ERROR, 5000)

    def getDirectoryElementContents(self, id):
        try:
            response = requests.get(self.settings['serverUrl'] + ':' + str(self.settings['serverPort']) + '/media/' + str(id) + '/contents', auth=(self.settings['username'], self.settings['password']))
            response.raise_for_status()
            data = response.json()
            return data
        except requests.exceptions.RequestException:
            xbmcgui.Dialog().notification(self.addon.getLocalizedString(30100), self.addon.getLocalizedString(30104), xbmcgui.NOTIFICATION_ERROR, 5000)

    def getMediaElement(self, id):
        try:
            response = requests.get(self.settings['serverUrl'] + ':' + str(self.settings['serverPort']) + '/media/' + str(id), auth=(self.settings['username'], self.settings['password']))
            response.raise_for_status()
            data = response.json()
            return data
        except requests.exceptions.RequestException:
            xbmcgui.Dialog().notification(self.addon.getLocalizedString(30100), self.addon.getLocalizedString(30104), xbmcgui.NOTIFICATION_ERROR, 5000)

    def getPlaylists(self):
        try:
            response = requests.get(self.settings['serverUrl'] + ':' + str(self.settings['serverPort']) + '/playlist', auth=(self.settings['username'], self.settings['password']))
            response.raise_for_status()
            data = response.json()
            return data
        except requests.exceptions.RequestException:
            xbmcgui.Dialog().notification(self.addon.getLocalizedString(30100), self.addon.getLocalizedString(30105), xbmcgui.NOTIFICATION_ERROR, 5000)
            
    def getPlaylistContents(self, id):
        try:
            response = requests.get(self.settings['serverUrl'] + ':' + str(self.settings['serverPort']) + '/playlist/' + str(id) + '/contents', auth=(self.settings['username'], self.settings['password']))
            response.raise_for_status()
            data = response.json()
            return data
        except requests.exceptions.RequestException:
            xbmcgui.Dialog().notification(self.addon.getLocalizedString(30100), self.addon.getLocalizedString(30104), xbmcgui.NOTIFICATION_ERROR, 5000)
    
    def endJob(self, sid, id):
        response = requests.delete(self.settings['serverUrl'] + ':' + str(self.settings['serverPort']) + '/session/end/' + str(sid) + '/' + str(id), auth=(self.settings['username'], self.settings['password']))

    def addSession(self, id, profile):
        try:
            response = requests.post(self.settings['serverUrl'] + ':' + str(self.settings['serverPort']) + '/session/add?id=' + str(id), json=profile, auth=(self.settings['username'], self.settings['password']))
            response.raise_for_status()
        except requests.exceptions.RequestException:
            xbmcgui.Dialog().notification(self.addon.getLocalizedString(30100), self.addon.getLocalizedString(30106), xbmcgui.NOTIFICATION_ERROR, 5000)
            
    def updateClientProfile(self, id, profile):
        try:
            response = requests.post(self.settings['serverUrl'] + ':' + str(self.settings['serverPort']) + '/session/update/' + str(id), json=profile, auth=(self.settings['username'], self.settings['password']))
            response.raise_for_status()
        except requests.exceptions.RequestException:
            xbmcgui.Dialog().notification(self.addon.getLocalizedString(30100), self.addon.getLocalizedString(30107), xbmcgui.NOTIFICATION_ERROR, 5000)

    def endSession(self, id):
        response = requests.delete(self.settings['serverUrl'] + ':' + str(self.settings['serverPort']) + '/session/end/' + str(id), auth=(self.settings['username'], self.settings['password']))

def testUrl(settings):
    try:
        response = requests.get(settings['serverUrl'] + ':' + str(settings['serverPort']) + '/settings/version', auth=(settings['username'], settings['password']), timeout=2.0)
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException:
        return False
