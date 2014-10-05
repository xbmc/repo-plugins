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


import urllib
import xbmcplugin
import gui
from lib import common
from lib.vpnconnectorfactory import VPNConnectorFactory
from lib.vpnmanager import VPNServerManager, NoConnectionError

import config
from config import __language__


_SETTINGS  = 100
_KILL      = 200
_SEPARATOR = 300
_COUNTRY   = 400
_VPN       = 500
_CUSTOM_CONNECT = 600


arguments = sys.argv




def Main():
    common.CheckVersion()
    common.CheckUsername()

    if config.isVPNCustom():
        connectToCustomServer()
        return

    gui.addDir(arguments, __language__(30001), _SETTINGS,  isFolder=False)
    gui.addDir(arguments, __language__(30002),   _KILL,      isFolder=False)
    gui.addDir(arguments, ' ',             _SEPARATOR, isFolder=False)

    try:
        for country in VPNServerManager.getInstance().getCountries():
            gui.addDir(arguments, country[0], _COUNTRY, abrv=country[1], thumbnail=country[2])
    except NoConnectionError:
        gui.DialogOK( __language__(30003),  __language__(30004), __language__(30005))


def addCitiesForCountry(countryName):
    try:
        cities = VPNServerManager.getInstance().getCities(countryName)
        for city in cities:
            label = '%s (%d)' % (city[0], city[2])
            gui.addDir(arguments, label, _VPN, thumbnail=city[1], server=city[3], isFolder=False, countryName = countryName)
    except NoConnectionError:
        gui.DialogOK(__language__(30003), __language__(30004), __language__(30005))


def connectToCustomServer():
    server = config.getConfiguredServerAddress()
    if not server:
        gui.addDir(arguments, __language__(30001), _SETTINGS,  isFolder=False)
    else:
        gui.addDir(arguments, __language__(30053), _CUSTOM_CONNECT,  isFolder=False)
        gui.addDir(arguments, __language__(30002),   _KILL,      isFolder=False)











def get_params():
    param=[]
    paramstring=arguments[2]
    if len(paramstring)>=2:
        params=arguments[2]
        cleanedparams=params.replace('?','')
        if (params[len(params)-1]=='/'):
           params=params[0:len(params)-2]
        pairsofparams=cleanedparams.split('&')
        param={}
        for i in range(len(pairsofparams)):
            splitparams={}
            splitparams=pairsofparams[i].split('=')
            if (len(splitparams))==2:
                param[splitparams[0]]=splitparams[1]
    return param



params = get_params()
mode     = -1

try:    mode = int(params['mode'])
except: pass




if mode == _COUNTRY:
    label = urllib.unquote_plus(params['label'])
    abrv  = urllib.unquote_plus(params['abrv'])
    countrySelected = abrv
    addCitiesForCountry(abrv)

elif mode == _VPN:
    label  = urllib.unquote_plus(params['label'])
    abrv   = urllib.unquote_plus(params['abrv'])
    server = urllib.unquote_plus(params['server'])
    country = urllib.unquote_plus(params['country'])

    city = label.rsplit(' (', 1)[0]
    vpnConnector = VPNConnectorFactory.getConnector(country, city, server)
    vpnConnector.connectToVPNServer()

elif mode == _SETTINGS:
    gui.ShowSettings()

elif mode == _KILL:
    vpnConnector = VPNConnectorFactory.getConnector()
    ret = vpnConnector.kill(showBusy=True)
    if ret:
        gui.DialogOK(__language__(30006))
    else:
        gui.DialogOK(__language__(30007), __language__(30008))

elif mode == _CUSTOM_CONNECT:
    server = config.getConfiguredServerAddress()
    gui.DialogOK( __language__(30045),  __language__(30046) % server, "")
    vpnConnector = VPNConnectorFactory.getConnector(serverAddress = server, custom=True)
    vpnConnector.connectToVPNServer()


elif mode == _SEPARATOR:
    pass

else:
    Main()

xbmcplugin.endOfDirectory(int(arguments[1]))

