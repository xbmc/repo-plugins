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
import Config
import httplib
from BeautifulSoup import BeautifulSoup


host = 'ivsmedia.iptv-distribution.net'
proxy = 'ivsmedia.iptv-distribution.net'
port = 80



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



def MediaImageUrlTemplate():
    req = '<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/">' \
          '<s:Body>' \
          '<MediaImageUrlTemplate xmlns="http://ivsmedia.iptv-distribution.net">' \
          '<siteID>0</siteID>' \
          '</MediaImageUrlTemplate>' \
          '</s:Body>' \
          '</s:Envelope>'
    soup = BeautifulSoup(Request(req, 'MediaImageUrlTemplate'))
    try:
        imageUrl = soup("mediaimageurltemplateresult")[0].text
    except:
        imageUrl = ''
    return imageUrl


def GetClientStreamUri(sessionID, cType, Id ):
    quality = ['HQ', 'SQ']
    q = int(addon.getSetting('quality'))
    region = ['EU_RST', 'NA_PST', 'NA_EST','AU_EST']
    r = int(addon.getSetting('region'))
    server = ['1','7']
    s = int(addon.getSetting('server'))
    
    req = '<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/">' \
          '<s:Body>' \
          '<GetClientStreamUri xmlns="http://ivsmedia.iptv-distribution.net">' \
          '<sessionID>' + sessionID + '</sessionID>' \
          '<mediaRequest xmlns:d4p1="http://schemas.datacontract.org/2004/07/IVS.Content.Media" xmlns:i="http://www.w3.org/2001/XMLSchema-instance">' \
          '<d4p1:clientSidePlaylist>false</d4p1:clientSidePlaylist>' \
          '<d4p1:item xmlns:d5p1="http://schemas.datacontract.org/2004/07/IVS.Content.Data">' \
          '<d5p1:contentType>' + cType + '</d5p1:contentType>' \
          '<d5p1:id>' + Id + '</d5p1:id>' \
          '</d4p1:item>' \
          '<d4p1:mediaFormat i:nil="true" />' \
          '<d4p1:startOffset>0</d4p1:startOffset>' \
          '<d4p1:streamSettings xmlns:d5p1="http://schemas.datacontract.org/2004/07/IVS.Common.Server">' \
          '<d5p1:balancingArea>' \
          '<d5p1:id>13</d5p1:id>' \
          '<d5p1:name i:nil="true" />' \
          '</d5p1:balancingArea>' \
          '<d5p1:cdn>' \
          '<d5p1:id>' + server[s] + '</d5p1:id>' \
          '<d5p1:name i:nil="true" />' \
          '</d5p1:cdn>' \
          '<d5p1:qualityPreset>' + quality[q] + '</d5p1:qualityPreset>' \
          '<d5p1:shiftTimeZoneName>' + region[r] + '</d5p1:shiftTimeZoneName>' \
          '</d4p1:streamSettings>' \
          '</mediaRequest>' \
          '</GetClientStreamUri>' \
          '</s:Body>' \
          '</s:Envelope>'
    soup = BeautifulSoup(Request(req, 'GetClientStreamUri'))
    try:
        StreamUrl = soup("a:url")[0].text
    except:
        StreamUrl = ''
    return StreamUrl



def GetArcStreamUri(sessionID, Id ):
    quality = ['HQ', 'SQ']
    q = int(addon.getSetting('quality'))
    region = ['EU_RST', 'NA_PST', 'NA_EST','AU_EST']
    r = int(addon.getSetting('region'))
    server = ['1','7']
    s = int(addon.getSetting('server'))
    
    req = '<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/">' \
          '<s:Body>' \
          '<GetClientStreamUri xmlns="http://ivsmedia.iptv-distribution.net">' \
          '<sessionID>' + sessionID + '</sessionID>' \
          '<mediaRequest xmlns:d4p1="http://schemas.datacontract.org/2004/07/IVS.Content.Media" xmlns:i="http://www.w3.org/2001/XMLSchema-instance">' \
          '<d4p1:clientSidePlaylist>true</d4p1:clientSidePlaylist>' \
          '<d4p1:item xmlns:d5p1="http://schemas.datacontract.org/2004/07/IVS.Content.Data">' \
          '<d5p1:contentType>DVR</d5p1:contentType>' \
          '<d5p1:id>' + Id + '</d5p1:id>' \
          '</d4p1:item>' \
          '<d4p1:mediaFormat i:nil="true" />' \
          '<d4p1:startOffset>0</d4p1:startOffset>' \
          '<d4p1:streamSettings xmlns:d5p1="http://schemas.datacontract.org/2004/07/IVS.Common.Server">' \
          '<d5p1:balancingArea>' \
          '<d5p1:id>13</d5p1:id>' \
          '<d5p1:name i:nil="true" />' \
          '</d5p1:balancingArea>' \
          '<d5p1:cdn>' \
          '<d5p1:id>' + server[s] + '</d5p1:id>' \
          '<d5p1:name i:nil="true" />' \
          '</d5p1:cdn>' \
          '<d5p1:qualityPreset>' + quality[q] + '</d5p1:qualityPreset>' \
          '<d5p1:shiftTimeZoneName>' + region[r] + '</d5p1:shiftTimeZoneName>' \
          '</d4p1:streamSettings>' \
          '</mediaRequest>' \
          '</GetClientStreamUri>' \
          '</s:Body>' \
          '</s:Envelope>'
          
    soup = BeautifulSoup(Request(req, 'GetClientStreamUri'))
    
    try:
        StreamUrl = soup("a:playlist")[0].text
        StreamUrl = StreamUrl.replace('&lt;', '<').replace('&gt;', '>')
    except:
        StreamUrl = ''
    return StreamUrl





def Request(str, action):
    conn = httplib.HTTPConnection(proxy, port)
    conn.request('POST', Config.MediaService, str, {
           'Host': host,
           'SOAPAction': 'http://' + host + '/MediaService/' + action,
           'Content-Type': 'text/xml; charset=utf-8'
          
           })                                            
    response = conn.getresponse()
    data = response.read()
    return data