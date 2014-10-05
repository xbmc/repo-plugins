#
#       Copyright (C) 2014 Datho Digital Inc
#       Martin Candurra (martincandurra@dathovpn.com)
#
#  This Program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2, or (at your option)
#  any later version.
#
#  This Program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with XBMC; see the file COPYING.  If not, write to
#  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
#  http://www.gnu.org/copyleft/gpl.html
#

import re
import os
import time
import urllib2

import requests

import config
from utils import Logger
from config import __language__

class NoConnectionError(Exception):
    pass

class VPNContainer():
    def __init__(self, items):
        self.server   = items[0]
        self.capacity = int(items[1])
        self.city     = items[2]
        self.abrv     = items[3]
        self.icon     = os.path.join(config.IMAGES, self.abrv.lower()+'.png') # items[4]
        self.ip       = items[5]
        self.status   = int(items[6])
        self.visible  = items[7] == '1'
        self.country  = self.abrv
        if config.COUNTRIES.has_key(self.country):
                self.country = config.COUNTRIES[self.country]
        self.mustShow = self.status == 1 and self.visible

class VPNServerManager:

    URL      =  'http://www.wlvpn.com/serverList.xml'
    REGEX_STR = 'server name="(.+?)" capacity="(.+?)" city="(.+?)" country="(.+?)" icon="(.+?)" ip="(.+?)" status="(.+?)" visible="(.+?)"'
    REGEX = re.compile(REGEX_STR)
    TIMEOUT = 10 * 60
    _instance = None


    @classmethod
    def getInstance(cls):
        if cls._instance is None:
            cls._instance = VPNServerManager()
            cls._instance._init()
        return cls._instance

    def _isContentOld(self):
        # If the last time the content was grabbed from the web is more than 15 minutes ago
        return (time.time() - self.lastContentUpdateTimestamp > self.TIMEOUT)

    def _getItems(self):
        ret = self._getItemsFromBase()
        if ret:
            return ret

        try:
            html  = GetContentFromUrl(self.URL)
            return re.compile(self.REGEX).findall(html)
        except urllib2.URLError, e:
            Logger.log("There was an error while getting content from remote server")
            raise NoConnectionError(__language__(30042) )

    def getPlainUsername(self, username):
        idx = username.find("@")
        if idx > 0:
            username = username[:idx]
        return username

    def _getItemsFromBase(self):
        self._usingDathoVPNServers = False
        try:
            Logger.log("Trying to retrieve info from base", Logger.LOG_DEBUG)
            quoted_user = urllib2.quote(self.getPlainUsername(config.getUsername()))
            quoted_pass =  urllib2.quote(config.getPassword())
            ret = requests.get("https://www.dathovpn.com/service/addon/servers/%s/%s/" % (quoted_user, quoted_pass))
            result = self.REGEX.findall(ret.text)
            Logger.log("Retrieve from base ok result len:%s" %  len(result), Logger.LOG_DEBUG)
            if "<mode>Datho</mode>" in ret.text:
                self._usingDathoVPNServers = True

            return result
        except urllib2.URLError, e:
            Logger.log("There was an error while getting content from remote server %r" % e, Logger.LOG_INFO)
            return []
        except urllib2.ConnectionError, ce:
            Logger.log("Could not connect the server %r" % ce, Logger.LOG_INFO)
            return []


    def usingDathoVPNServers(self):
        return self._usingDathoVPNServers

    def _init(self):
        self.lastContentUpdateTimestamp = time.time()

        items = self._getItems()

        self.countryMap = {}
        self.cityByCountryMap = {}

        for item in items:
            vpn = VPNContainer(item)
            if vpn.country not in self.countryMap:
                if vpn.mustShow:
                    self.countryMap[vpn.abrv] = [vpn.country, vpn.abrv, vpn.icon]

            if not vpn.mustShow:
                continue

            cities = self.cityByCountryMap.get(vpn.abrv, [] )
            self.cityByCountryMap[vpn.abrv] = cities
            cities.append([vpn.city, vpn.icon, vpn.capacity, vpn.ip])

        self.countries = self.countryMap.values()
        self.countries.sort()


    def getCities(self, countryAbrv):
        if countryAbrv not in self.cityByCountryMap:
            Logger.log("Country %s not in map:%r" % (countryAbrv, self.cityByCountryMap.keys()), Logger.LOG_ERROR)
        l = self.cityByCountryMap[ countryAbrv ]
        l.sort()
        return l

    def getCountries(self):
        if self._instance._isContentOld():
            self._init()
        return self.countries


def GetContentFromUrl(url, agent = ''):
    req = urllib2.Request(url)
    req.add_header('User-Agent', agent)

    response = urllib2.urlopen(req)
    html     = response.read()
    response.close()
    return html