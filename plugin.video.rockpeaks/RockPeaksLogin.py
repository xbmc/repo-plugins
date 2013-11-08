'''
    RockPeaks plugin for XBMC
    Copyright 2013 Artem Matsak

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

import sys

class RockPeaksLogin():
    def __init__(self, plugin, api):
        self.plugin = plugin
        self.api = api

    def login(self, silent=False):
        if not silent:
            self.plugin.open_settings()

        self.plugin.set_setting('sessid', '')

        data = self.api.request('user.login', {
            'username': self.plugin.get_setting('username'),
            'password': self.plugin.get_setting('user_password'),
        })
        
        if 'error' not in data:
            self.plugin.set_setting('sessid', data['sessid'])
        elif not silent:
            self.plugin.notify(msg=self.plugin.get_string(30601))
