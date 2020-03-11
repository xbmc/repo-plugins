# -*- coding: utf-8 -*-

'''
@author: jackyNIX

Copyright (C) 2011-2020 jackyNIX

This file is part of KODI Mixcloud Plugin.

KODI Mixcloud Plugin is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

KODI Mixcloud Plugin is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with KODI Mixcloud Plugin.  If not, see <http://www.gnu.org/licenses/>.
'''



import sys
import xbmc
import xbmcgui
import xbmcplugin
from datetime import datetime
from .mixcloud import MixcloudInterface
from .utils import Utils
from .history import History
from .resolver import ResolverBuilder
from .base import BaseBuilder, BaseListBuilder, QueryListBuilder, BaseList, BuildResult
from .lang import Lang



# main menu
class MainBuilder(BaseListBuilder):

    def buildItems(self):
        Utils.log('MainBuilder.buildItems()')
        if MixcloudInterface().profileLoggedIn():
            self.addFolderItem({'title' : Lang.FOLLOWINGS}, {'mode' : 'playlists', 'key' : '/me/following/'}, Utils.getIcon('nav/kodi_highlight.png'))
            self.addFolderItem({'title' : Lang.FOLLOWERS}, {'mode' : 'playlists', 'key' : '/me/followers/'}, Utils.getIcon('nav/kodi_highlight.png'))
            self.addFolderItem({'title' : Lang.FAVORITES}, {'mode' : 'cloudcasts', 'key' : '/me/favorites/'}, Utils.getIcon('nav/kodi_favorites.png'))
            self.addFolderItem({'title' : Lang.UPLOADS}, {'mode' : 'cloudcasts', 'key' : '/me/cloudcasts/'}, Utils.getIcon('nav/kodi_uploads.png'))
            self.addFolderItem({'title' : Lang.PLAYLISTS}, {'mode' : 'playlists', 'key' : '/me/playlists/'}, Utils.getIcon('nav/kodi_playlists.png'))
            self.addFolderItem({'title' : Lang.LISTEN_LATER}, {'mode' : 'cloudcasts', 'key' : '/me/listen-later/'}, Utils.getIcon('nav/kodi_listenlater.png'))
        else:
            self.addFolderItem({'title' : Lang.PROFILE}, {'mode' : 'profile', 'key' : 'login'}, Utils.getIcon('nav/kodi_profile.png'))
        self.addFolderItem({'title' : Lang.CATEGORIES}, {'mode' : 'playlists', 'key' : '/categories/'}, Utils.getIcon('nav/kodi_categories.png'))
        self.addFolderItem({'title' : Lang.HISTORY}, {'mode' : 'playhistory', 'offset' : 0, 'offsetex' : 0}, Utils.getIcon('nav/kodi_history.png'))
        self.addFolderItem({'title' : Lang.SEARCH}, {'mode' : 'search'}, Utils.getIcon('nav/kodi_search.png'))
        return 0



# cloudcasts menu
class CloudcastsBuilder(BaseListBuilder):

    def buildItems(self):
        Utils.log('CloudcastsBuilder.buildItems()')
        xbmcplugin.setContent(self.plugin_handle, 'songs')
        cloudcasts = MixcloudInterface().getList(self.key, {'offset' : self.offset})
        mon = xbmc.Monitor()            
        for cloudcast in cloudcasts.items:
            # user aborted
            if mon.abortRequested():
                break
                
            contextMenuItems = self.buildContextMenuItems(cloudcast)
            self.addAudioItem(cloudcast.infolabels, {'mode' : 'resolve', 'key' : cloudcast.key, 'user' : cloudcast.user}, cloudcast.image, contextMenuItems, len(cloudcasts.items))
        return cloudcasts.nextOffset



# playlists menu
class PlaylistsBuilder(BaseListBuilder):

    def buildItems(self):
        Utils.log('PlaylistsBuilder.buildItems()')
        playlists = MixcloudInterface().getList(self.key, {'offset' : self.offset})
        mon = xbmc.Monitor()            
        for playlist in playlists.items:
            # user aborted
            if mon.abortRequested():
                break
                
            if playlist.image:
                image = playlist.image
            elif self.key == '/categories/':
                image = Utils.getIcon('nav/kodi_categories.png')
            elif self.key == '/me/playlists/':
                image = Utils.getIcon('nav/kodi_playlists.png')
            else:
                image = ''
            contextMenuItems = self.buildContextMenuItems(playlist)
            self.addFolderItem(playlist.infolabels, {'mode' : 'cloudcasts', 'key' : playlist.key + 'cloudcasts/'}, image, contextMenuItems)
        return playlists.nextOffset
    


# play history menu (with profile listens)
class PlayHistoryBuilder(BaseListBuilder):

    def buildItems(self):
        Utils.log('PlayHistoryBuilder.buildItems()')
        xbmcplugin.setContent(self.plugin_handle, 'songs')

        cloudcasts = []
        playHistory = History.getHistory('play_history')
        if playHistory:
            cloudcasts.append(MixcloudInterface().getCloudcasts(playHistory.data, {'offset' : self.offset[0]}))
        else:
            cloudcasts.append(BaseList())
        if MixcloudInterface().profileLoggedIn():
            cloudcasts.append(MixcloudInterface().getList('/me/listens/', {'offset' : self.offset[1]}))
        else:
            cloudcasts.append(BaseList())

        mergedCloudcasts = BaseList()
        mergedCloudcasts.merge(cloudcasts)
        mergedCloudcasts.initTrackNumbers(self.offset[0] + self.offset[1])
        if (cloudcasts[0].nextOffset + cloudcasts[1].nextOffset) > 0:
            mergedCloudcasts.nextOffset[0] = self.offset[0] + mergedCloudcasts.nextOffset[0]
            mergedCloudcasts.nextOffset[1] = self.offset[1] + mergedCloudcasts.nextOffset[1]
        else:
            mergedCloudcasts.nextOffset = [0, 0]

        mon = xbmc.Monitor()            
        for cloudcast in mergedCloudcasts.items:
            # user aborted
            if mon.abortRequested():
                break
                
            contextMenuItems = self.buildContextMenuItems(cloudcast)
            self.addAudioItem(cloudcast.infolabels, {'mode' : 'resolve', 'key' : cloudcast.key, 'user' : cloudcast.user}, cloudcast.image, contextMenuItems, len(mergedCloudcasts.items))

        return mergedCloudcasts.nextOffset



# search menu
class SearchBuilder(BaseListBuilder):

    def buildItems(self):
        self.addFolderItem({'title' : Lang.SEARCH_FOR_CLOUDCASTS}, {'mode' : 'searchcloudcast'}, Utils.getIcon('nav/kodi_search.png'))
        self.addFolderItem({'title' : Lang.SEARCH_FOR_USERS}, {'mode' : 'searchuser'}, Utils.getIcon('nav/kodi_search.png'))
        searchHistory = History.getHistory('search_history')
        if searchHistory:
            index = 0
            mon = xbmc.Monitor()            
            for keyitem in searchHistory.data:
                # user aborted
                if mon.abortRequested():
                    break
                
                index += 1
                if index > self.offset:
                    if index <= self.offset + 10:
                        if keyitem['key'] == 'cloudcast':
                            self.addFolderItem({'title' : keyitem['value']}, {'mode' : 'searchcloudcast', 'key' : keyitem['value']}, Utils.getIcon('nav/kodi_playlists.png'))
                        elif keyitem['key'] == 'user':
                            self.addFolderItem({'title' : keyitem['value']}, {'mode' : 'searchuser', 'key' : keyitem['value']}, Utils.getIcon('nav/kodi_profile.png'))
                    else:
                        break
            if index < len(searchHistory.data):
                return index
        return 0



# search cloudcast menu
class SearchCloudcastBuilder(QueryListBuilder):

    def buildQueryItems(self, query):
        xbmcplugin.setContent(self.plugin_handle, 'songs')
        cloudcasts = MixcloudInterface().getList('/search/', {'q' : query, 'type' : 'cloudcast', 'offset' : self.offset})
        mon = xbmc.Monitor()            
        for cloudcast in cloudcasts.items:
            # user aborted
            if mon.abortRequested():
                break
                
            contextMenuItems = self.buildContextMenuItems(cloudcast)
            self.addAudioItem(cloudcast.infolabels, {'mode' : 'resolve', 'key' : cloudcast.key, 'user' : cloudcast.user}, cloudcast.image, contextMenuItems, len(cloudcasts.items))
        if not self.key:
            searchHistory = History.getHistory('search_history')
            if searchHistory:
                searchHistory.add({'key' : 'cloudcast', 'value' : query})
        return cloudcasts.nextOffset



# search user menu
class SearchUserBuilder(QueryListBuilder):

    def buildQueryItems(self, query):
        users = MixcloudInterface().getList('/search/', {'q' : query, 'type' : 'user', 'offset' : self.offset})
        mon = xbmc.Monitor()            
        for user in users.items:
            # user aborted
            if mon.abortRequested():
                break
                
            contextMenuItems = self.buildContextMenuItems(user)
            self.addFolderItem(user.infolabels, {'mode' : 'cloudcasts', 'key' : user.key + 'cloudcasts/'}, user.image, contextMenuItems)
        if not self.key:
            searchHistory = History.getHistory('search_history')
            if searchHistory:
                searchHistory.add({'key' : 'user', 'value' : query})
        return users.nextOffset



# mixcloud profile builder
class MixcloudProfileBuilder(BaseBuilder):

    def build(self):
        if (self.key == 'login') and (MixcloudInterface().profileLogin()):
            return MainBuilder().build()
        elif self.key == 'logout':
            MixcloudInterface().profileLogout()
            xbmc.executebuiltin('Container.Refresh')
            return BuildResult.ENDOFDIRECTORY_DONOTHING
        else:
            return BuildResult.ENDOFDIRECTORY_FAILED



# mixcloud post or delete builder
class MixcloudProfileActionBuilder(BaseBuilder):

    def build(self):
        MixcloudInterface().profileAction(self.mode.upper(), self.key)
        xbmc.executebuiltin('Container.Refresh')
        return BuildResult.ENDOFDIRECTORY_DONOTHING



# mixcloud post or delete builder
class ClearHistoryBuilder(BaseBuilder):

    def build(self):
        if xbmcgui.Dialog().yesno('Mixcloud', Lang.ASK_CLEAR_HISTORY):
            playHistory = History.getHistory('play_history')
            playHistory.clear()
            playHistory.writeFile()

            searchHistory = History.getHistory('search_history')
            searchHistory.clear()
            searchHistory.writeFile()

        xbmc.executebuiltin('Container.Refresh')
        return BuildResult.ENDOFDIRECTORY_DONOTHING



# mode/class switches
BUILDERS = {
    '' : MainBuilder,
    'cloudcasts' : CloudcastsBuilder,
    'playlists' : PlaylistsBuilder,
    'playhistory' : PlayHistoryBuilder,
    'search' : SearchBuilder,
    'searchcloudcast' : SearchCloudcastBuilder,
    'searchuser' : SearchUserBuilder,
    'resolve' : ResolverBuilder,
    'profile' : MixcloudProfileBuilder,
    'post' : MixcloudProfileActionBuilder,
    'delete' : MixcloudProfileActionBuilder,
    'history' : ClearHistoryBuilder
}

# main entry
def run():
    starttime = datetime.now()
    Utils.log('##############################################################################################################################')
    plugin_args = Utils.getArguments()
    Utils.log('args: ' + str(plugin_args))

    try:
        BUILDERS.get(plugin_args.get('mode', ''), MainBuilder)().execute()
    except Exception as e:
        Utils.log('builder execute failed', e)

    elapsedtime = datetime.now() - starttime
    Utils.log('executed in ' + str(elapsedtime.seconds) + '.' + str(elapsedtime.microseconds) + ' seconds')

    # version check
    currentVersion = Utils.getVersion()
    lastCheckedVersion = Utils.getSetting('last_checked_version')
    if currentVersion != lastCheckedVersion:
        xbmcgui.Dialog().ok('Mixcloud', Utils.getChangeLog())
    Utils.setSetting('last_checked_version', currentVersion)