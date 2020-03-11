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



from .utils import Utils
from .lang import Lang
import sys
import xbmc
import xbmcplugin
import xbmcgui
from enum import Enum



class BuildResult(Enum):
    ENDOFDIRECTORY_DONOTHING = 0
    ENDOFDIRECTORY_FAILED = 1
    ENDOFDIRECTORY_SUCCESS = 2



# super class
class BaseBuilder:

    def __init__(self):
        plugin_args = Utils.getArguments()
        self.plugin_handle = int(sys.argv[1])
        self.mode = plugin_args.get('mode', '')
        self.key = plugin_args.get('key', '')
        if plugin_args.get('offsetex', ''):
            self.offset = [int(plugin_args.get('offset', '0')), int(plugin_args.get('offsetex', '0'))]
        else:
            self.offset = int(plugin_args.get('offset', '0'))
        Utils.log('BaseBuilder.__init__(self = ' + self.__class__.__name__ + ', plugin_handle = ' + str(self.plugin_handle) + ', mode = ' + self.mode + ', key = ' + self.key + ', offset = ' + str(self.offset) + ')')

    def execute(self):
        Utils.log('BaseBuilder.execute()')
        ret = self.build()
        if ret is not BuildResult.ENDOFDIRECTORY_DONOTHING:
            xbmcplugin.endOfDirectory(handle = self.plugin_handle, succeeded = (ret is BuildResult.ENDOFDIRECTORY_SUCCESS))

    # returns BuildResult
    def build(self):
        Utils.log('BaseBuilder.build()')
        return BuildResult.ENDOFDIRECTORY_SUCCESS



# super class for lists
class BaseListBuilder(BaseBuilder):

    def build(self):
        Utils.log('BaseListBuilder.build()')
        nextOffset = self.buildItems()
        Utils.log('next offset: ' + str(nextOffset))
        nextOffsetEx = None
        if isinstance(nextOffset, list):
            nextOffsetEx = nextOffset[1]
            nextOffset = nextOffset[0]
        if (nextOffset and (nextOffset > 0)) or ((nextOffsetEx is not None) and (nextOffsetEx > 0)):
            parameters = {'mode' : self.mode, 'key' : self.key, 'offset' : nextOffset}
            if nextOffsetEx is not None:
                parameters['offsetex'] = nextOffsetEx
            self.addFolderItem({'title' : Lang.MORE}, parameters)
        if nextOffset != -1:
            return BuildResult.ENDOFDIRECTORY_SUCCESS
        else:
            return BuildResult.ENDOFDIRECTORY_FAILED

    # returns offset
    def buildItems(self):
        Utils.log('BaseListBuilder.buildItems()')
        return 0

    def addFolderItem(self, infolabels = {}, parameters = {}, img = '', contextmenuitems = []):
        Utils.log('BaseListBuilder.addFolderItem(infolabels = ' + str(infolabels) + ', parameters = ' + str(parameters) + ', img = ' + img + ', contextmenuitems = ' + str(contextmenuitems) + ')')

        listitem = xbmcgui.ListItem(infolabels['title'], infolabels['title'])
        listitem.setArt({'icon' : img, 'thumb' : img})
        listitem.setInfo('music', infolabels)

        if contextmenuitems:
            listitem.addContextMenuItems(contextmenuitems)

        return xbmcplugin.addDirectoryItem(handle = self.plugin_handle, url = Utils.encodeArguments(parameters), listitem = listitem, isFolder = True)

    def addAudioItem(self, infolabels = {}, parameters = {}, img = '', contextmenuitems = [], total = 0):
        Utils.log('BaseListBuilder.addAudioItem(infolabels = ' + str(infolabels) + ', parameters = ' + str(parameters) + ', img = ' + img + ', contextmenuitems = ' + str(contextmenuitems) + ', total = ' + str(total) + ')')

        listitem = xbmcgui.ListItem(infolabels['title'], infolabels['artist'])
        listitem.setArt({'icon' : img, 'thumb' : img})
        listitem.setInfo('music', infolabels)
        listitem.setProperty('IsPlayable', 'true')

        if contextmenuitems:
            listitem.addContextMenuItems(contextmenuitems)

        xbmcplugin.addDirectoryItem(handle = self.plugin_handle, url = Utils.encodeArguments(parameters), listitem = listitem, isFolder = False, totalItems = total)

    def buildContextMenuItems(self, item):
        contextMenuItems = []

        if item.favorited == False:
            contextMenuItems.append((Lang.ADD_TO_FAVORITES, 'XBMC.RunPlugin(' + Utils.encodeArguments({'mode' : 'post', 'key' : item.key + 'favorite/'}) + ')'))
        elif item.favorited == True:
            contextMenuItems.append((Lang.REMOVE_FROM_FAVORITES, 'XBMC.RunPlugin(' + Utils.encodeArguments({'mode' : 'delete', 'key' : item.key + 'favorite/'}) + ')'))

        if item.listenlater == False:
            contextMenuItems.append((Lang.ADD_TO_LISTEN_LATER, 'XBMC.RunPlugin(' + Utils.encodeArguments({'mode' : 'post', 'key' : item.key + 'listen-later/'}) + ')'))
        elif item.listenlater == True:
            contextMenuItems.append((Lang.REMOVE_FROM_LISTEN_LATER, 'XBMC.RunPlugin(' + Utils.encodeArguments({'mode' : 'delete', 'key' : item.key + 'listen-later/'}) + ')'))

        userKey = item.user
        if not userKey:
            userKey = item.key

        if item.following == False:
            contextMenuItems.append((Lang.ADD_TO_FOLLOWINGS, 'XBMC.RunPlugin(' + Utils.encodeArguments({'mode' : 'post', 'key' : userKey + 'follow/'}) + ')'))
        elif item.following == True:
            contextMenuItems.append((Lang.REMOVE_FROM_FOLLOWINGS, 'XBMC.RunPlugin(' + Utils.encodeArguments({'mode' : 'delete', 'key' : userKey + 'follow/'}) + ')'))

        # fake menu separator
        # I do hope one day kodi will support menu separators
        if len(contextMenuItems) > 0:
            contextMenuItems.append(('----------------------------------------', ''))

        return contextMenuItems



# super class for user queries
class QueryListBuilder(BaseListBuilder):

    def buildItems(self):
        query = self.key
        if not query:
            keyboard = xbmc.Keyboard(query)
            keyboard.doModal()
            if keyboard.isConfirmed():
                query = keyboard.getText()
        if query:
            return self.buildQueryItems(query)
        return -1
    
    def buildQueryItems(self, query):
        Utils.log('QueryListBuilder.buildQueryItems(' + query + ')')
        return 0



# class for list data
class BaseList:

    def __init__(self):
        self.items = []
        self.nextOffset = 0

    def initTrackNumbers(self, offset):
        index = offset
        for item in self.items:
            index += 1
            item.infolabels['tracknumber'] = index
            item.infolabels['count'] = index

    def merge(self, baseLists = []):
        listCount = len(baseLists)
        Utils.log('merge lists: ' + str(listCount))
        maxItems = int(Utils.getSetting('page_limit'))
        index = []
        count = []
        curItems = []
        for baseList in baseLists:
            index.append(0)
            count.append(len(baseList.items))
            curItems.append(None)

        mon = xbmc.Monitor()            
        for iMerged in range(maxItems):
            # user aborted
            if mon.abortRequested():
                break
                
            for iList in range(listCount):
                if index[iList] < count[iList]:
                    curItems[iList] = baseLists[iList].items[index[iList]]
                else:
                    curItems[iList] = None

            iAdd = -1
            for iList in range(listCount):
                if curItems[iList]:
                    if (iAdd == -1) or ((not curItems[iAdd].timestamp) and (curItems[iList])) or ((curItems[iAdd].timestamp) and (curItems[iList].timestamp) and (curItems[iList].timestamp > curItems[iAdd].timestamp)):
                        iAdd = iList
                    
            if iAdd != -1:
                Utils.log('merge: ' + str(iMerged) + ' from ' + str(iAdd) + ' - ' + str(curItems[iAdd]))
                self.items.append(curItems[iAdd])
                index[iAdd] = index[iAdd] + 1
            else:
                break

        Utils.log('merged result: ' + str(len(self.items)))
        Utils.log('nextoffset: ' + str(index))
        self.nextOffset = index

    # limit list
    def trim(self):
        maxItems = int(Utils.getSetting('page_limit'))
        while len(self.items) > maxItems:
            self.items.pop()



class BaseListItem:

    def __init__(self):
        self.key = None
        self.user = None
        self.image = None
        self.timestamp = None
        self.favorited = None
        self.listenlater = None
        self.following = None
        self.infolabels = {}

    def setKey(self, sourceData, sourceKey):
        if sourceKey in sourceData and sourceData[sourceKey]:
            self.key = sourceData[sourceKey]
        else:
            self.key = None
        return self.key

    def setUser(self, sourceData, sourceKey):
        if sourceKey in sourceData and sourceData[sourceKey]:
            self.user = sourceData[sourceKey]
        else:
            self.user = None
        return self.user

    def setImage(self, sourceData, sourceKey):
        if sourceKey in sourceData and sourceData[sourceKey]:
            self.image = sourceData[sourceKey]
        else:
            self.image = None
        return self.image

    def setTimestamp(self, sourceData, sourceKey):
        if sourceKey in sourceData and sourceData[sourceKey]:
            self.timestamp = sourceData[sourceKey]
        else:
            self.timestamp = None
        return self.timestamp

    def setFavorited(self, sourceData, sourceKey):
        if sourceKey in sourceData:
            self.favorited = sourceData[sourceKey]
        else:
            self.favorited = None
        return self.favorited

    def setListenLater(self, sourceData, sourceKey):
        if sourceKey in sourceData:
            self.listenlater = sourceData[sourceKey]
        else:
            self.listenlater = None
        return self.listenlater

    def setFollowing(self, sourceData, sourceKey):
        if sourceKey in sourceData:
            self.following = sourceData[sourceKey]
        else:
            self.following = None
        return self.following

    def __repr__(self):
        return  'BaseListItem(key: ' + str(self.key) + ', user: ' + str(self.user) + ', image: ' + str(self.image) + ', timestamp: ' + str(self.timestamp) + ', favorited: ' + str(self.favorited) + ', listen-later: ' + str(self.listenlater) + ', following: ' + str(self.following) + ', infolabels: ' + str(self.infolabels) + ')'