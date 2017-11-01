'''
    OneDrive for Kodi
    Copyright (C) 2015 - Carlos Guzman

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License along
    with this program; if not, write to the Free Software Foundation, Inc.,
    51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

    Created on Mar 1, 2015
    @author: Carlos Guzman (cguZZman) carlosguzmang@hotmail.com
'''

from ConfigParser import ConfigParser
import os

from resources.lib.api import utils
from resources.lib.api.onedrive import OneDrive, AccountNotFoundException
import xbmc
import xbmcaddon


class AccountManager:
    monitor = xbmc.Monitor()
    config = ConfigParser()
    addon = xbmcaddon.Addon()
    addonname = addon.getAddonInfo('name')
    addon_data_path = utils.Utils.unicode(xbmc.translatePath(addon.getAddonInfo('profile')))
    config_file = 'onedrive.ini'
    config_path = os.path.join(addon_data_path, config_file)
    accounts = None
    
    def __init__(self):
        if not os.path.exists(self.addon_data_path):
            try:
                os.makedirs(self.addon_data_path)
            except:
                self.monitor.waitForAbort(3)
                os.makedirs(self.addon_data_path)
        self.config.read(self.config_path)

    def reload(self):
        self.config.read(self.config_path)
        self.accounts = None

    def map(self):
        if not self.accounts:
            self.accounts = {}
            for driveid in self.config.sections():
                onedrive = OneDrive(self.addon.getSetting('client_id_oauth2'))
                onedrive.driveid = driveid
                onedrive.event_listener = self.event_listener
                onedrive.name = self.config.get(driveid, 'name')
                onedrive.access_token = self.config.get(driveid, 'access_token')
                onedrive.refresh_token = self.config.get(driveid, 'refresh_token')
                self.accounts[driveid] = onedrive
        return self.accounts
    
    def get(self, driveid):
        onedrives = self.map()
        if driveid in onedrives:
            return onedrives[driveid]
        raise AccountNotFoundException()
    
    def event_listener(self, onedrive, event, obj):
        if event == 'login_success':
            self.save(onedrive)

    def save(self, onedrive):
        onedrives = self.map()
        if onedrive.driveid not in onedrives:
            self.config.add_section(onedrive.driveid)
        
        self.config.set(onedrive.driveid, 'name', onedrive.name)
        self.config.set(onedrive.driveid, 'access_token', onedrive.access_token)
        self.config.set(onedrive.driveid, 'refresh_token', onedrive.refresh_token)
        
        with open(self.config_path, 'wb') as configfile:
            self.config.write(configfile)

    def remove(self, driveid):
        onedrives = self.map()
        if driveid in onedrives:
            self.config.remove_section(driveid)
            with open(self.config_path, 'wb') as configfile:
                self.config.write(configfile)
    