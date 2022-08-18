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



import os
import sys
import json
from datetime import datetime
import xbmc
import xbmcaddon
from .utils import Utils 



# variables
__addon__ = xbmcaddon.Addon('plugin.audio.mixcloud')
CACHED_HISTORY = {}



class History:

    def __init__(self, name):
        self.name = name
        self.data = []
        self.readFile()

    def readFile(self):
        starttime = datetime.now()
        self.data = []
        filepath = xbmc.translatePath(__addon__.getAddonInfo('profile')) + self.name + '.json'
        Utils.log('reading json file: ' + filepath)
        try:
            # read file
            if os.path.exists(filepath):
                with open(filepath, 'r') as text_file:
                    self.data = json.loads(text_file.read())
                self.trim()
            elif __addon__.getSetting(self.name+'_list'):
                # convert old 2.4.x settings
                list_data = __addon__.getSetting(self.name + '_list').split(', ')
                for list_entry in list_data:
                    json_entry = {}
                    list_fields = list_entry.split('=')
                    for list_field in list_fields:
                        if len(json_entry) == 0:
                            json_entry['key'] = list_field
                        elif len(json_entry) == 1:
                            json_entry['value'] = list_field
                    self.data.append(json_entry)
                    self.trim()
                Utils.log('convert old 2.4.x settings: ' + self.name + ' -> ' + json.dumps(self.data))
                self.writeFile()
                __addon__.setSetting(self.name + '_list', None)

        except Exception as e:
            Utils.log('unable to read json file: ' + filepath, e)
        elapsedtime = datetime.now() - starttime
        Utils.log('read ' + str(len(self.data)) + ' items in ' + str(elapsedtime.seconds) + '.' + str(elapsedtime.microseconds) + ' seconds')
        return self.data
        
    def writeFile(self):
        filepath = xbmc.translatePath(__addon__.getAddonInfo('profile')) + self.name + '.json'
        try:
            with open(filepath, 'w+') as text_file:
                text_file.write(json.dumps(self.data, indent = 4 * ' '))
        except Exception as e:
            Utils.log('unable to write json file: ' + filepath, e)

    # add data and write file
    def add(self, json_entry = {}):
        try:
            json_entry['timestamp'] = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
            self.data.insert(0, json_entry)
            self.trim()
            self.writeFile()
        except Exception as e:
            Utils.log('unable to add to json', e)

    # limit list
    def trim(self):
        json_max = 1
        if __addon__.getSetting(self.name + '_max'):
            json_max = int(__addon__.getSetting(self.name + '_max'))
        mon = xbmc.Monitor()            
        while len(self.data) > json_max:
            # user aborted
            if mon.abortRequested():
                break
                
            self.data.pop()

    # clear list
    def clear(self):
        Utils.log('clear json sfile')
        self.data = []

    @staticmethod
    def getHistory(name):
        history = CACHED_HISTORY.get(name)
        if not history:
            history = History(name)
            CACHED_HISTORY[name] = history
        return history