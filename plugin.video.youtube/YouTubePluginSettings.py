'''
   YouTube plugin for XBMC
    Copyright (C) 2010-2012 Tobias Ussing And Henrik Mosgaard Jensen

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

class YouTubePluginSettings():

    def __init__(self):
        self.settings = sys.modules["__main__"].settings
        self.dbg = sys.modules["__main__"].dbg

    def itemsPerPage(self):
        return (10, 15, 20, 25, 30, 40, 50)[int(self.settings.getSetting("perpage"))]

    def currentRegion(self):
        return ('', 'AU', 'BR', 'CA', 'CZ', 'FR', 'DE', 'GB', 'NL', 'HK', 'IN', 'IE', 'IL', 'IT', 'JP', 'MX', 'NZ', 'PL', 'RU', 'KR', 'ES', 'SE', 'TW', 'US', 'ZA')[int(self.settings.getSetting("region_id"))]

    def safeSearchLevel(self):
        return ("none", "moderate", "strict")[int(self.settings.getSetting("safe_search"))]

    def requestTimeout(self):
        return [5, 10, 15, 20, 25][int(self.settings.getSetting("timeout"))]

    def userHasProvidedValidCredentials(self):
        return (self.settings.getSetting("username") != "" and self.settings.getSetting("oauth2_access_token"))

    def userName(self):
        return self.settings.getSetting("username")

    def userPassword(self):
        return self.settings.getSetting("user_password")

    def debugModeIsEnabled(self):
        return self.settings.getSetting("debug") == "true"

    def authenticationRefreshRoken(self):
        return self.settings.getSetting("oauth2_refresh_token")
