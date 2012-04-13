# coding=utf-8
#
# <BestRussianTV plugin for XBMC>
# Copyright (C) <2011>  <BestRussianTV>
#
#       This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
import Content, Config
import httplib
from BeautifulSoup import BeautifulSoup


req = '<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/"><s:Body>{BODY}</s:Body></s:Envelope>'
host = 'ivsmedia.iptv-distribution.net'
proxy = 'ivsmedia.iptv-distribution.net'#'ivsmedia.iptv-distribution.net'
port = 80


def SetSett(sess):
    try:
        # new XBMC 10.05 addons:
        import xbmcaddon
    except ImportError:
        # old XBMC - create fake xbmcaddon module with same interface as new XBMC 10.05
        class xbmcaddon:
            """ fake xbmcaddon module """
            __version__ = "(old XBMC)"
            class Addon:
                """ fake xbmcaddon.Addon class """
                def __init__(self, id):
                    self.id = id
    
                def getSetting(self, key):
                    return xbmcplugin.getSetting(key)
    
                def openSettings(self):
                    xbmc.openSettings()
                def setSetting(self, key, value):
                    return xbmcplugin.setSetting(key, value)
    
    addon = xbmcaddon.Addon("plugin.video.brt")
    quality = ['HQ', 'SQ']
    q = int(addon.getSetting('quality'))
    region = ['EU_RST', 'NA_PST', 'NA_EST','AU_EST']
    r = int(addon.getSetting('region'))
    server = ['1','7']
    s = int(addon.getSetting('server'))
    req = '<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/"><s:Body>' \
          '<SetSettings xmlns="http://ivsmedia.iptv-distribution.net"><sessionID>' + sess + '</sessionID>' \
          '<cs xmlns:d4p1="http://schemas.datacontract.org/2004/07/IVS.Media.Client" xmlns:i="http://www.w3.org/2001/XMLSchema-instance">' \
          '<d4p1:adultEnabled>false</d4p1:adultEnabled><d4p1:clientServices /><d4p1:language>rus</d4p1:language>' \
          '<d4p1:playerType xmlns:d5p1="http://schemas.datacontract.org/2004/07/IVS.Common" i:nil="true" /><d4p1:streamPreference xmlns:d5p1="http://schemas.datacontract.org/2004/07/IVS.Common.Server">' \
          '<d5p1:balancingArea i:nil="true" /><d5p1:cdn><d5p1:id>' + server[s] + '</d5p1:id><d5p1:name i:nil="true" /></d5p1:cdn>' \
          '<d5p1:qualityPreset>' + quality[q] + '</d5p1:qualityPreset><d5p1:shiftTimeZoneName>' + region[r] + '</d5p1:shiftTimeZoneName></d4p1:streamPreference>' \
          '<d4p1:timeZoneName>' + region[r] + '</d4p1:timeZoneName></cs></SetSettings></s:Body></s:Envelope>'
    Request(req, 'SetSettings')

def Login(Username = '',Password = ''):
    x = Content.Application().ClientAppSettings
    x.clientCredential.UserLogin = Username
    x.clientCredential.UserPassword = Password
    x.appSettings.appName ='XBMC'
    temp = req.replace('{BODY}', '<Login xmlns="http://ivsmedia.iptv-distribution.net">' + x.get() + '</Login>')
    soup = BeautifulSoup(Request(temp, 'Login'))
    try:
        x.appSettings.sessionID = soup("b:sessionid")[0].text
    except:
        x.appSettings.sessionID = ""
    return x
    

def Request(str, action):
    conn = httplib.HTTPConnection(proxy, port)
    conn.request('POST', Config.ClientService, str, {
           'Host': host,
           'SOAPAction': 'http://' + host + '/ClientService/' + action,
           'Content-Type': 'text/xml; charset=utf-8'
          
           })                                            
    response = conn.getresponse()
    data = response.read()
    return data