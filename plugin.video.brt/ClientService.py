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