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

import config
from utils import Logger
from android import AndroidVPNConnector
from vpn import LinuxVPNConnector, OpenElecVPNConnector, RaspBMCVPNConnector, WindowsVPNConnector

class VPNConnectorFactory:

    @classmethod
    def getConnector(cls, countryName = '', cityName = '', serverAddress = '', custom = False):
        Logger.log("Operating System Configured:%s custom:%s Country:%s city:%s server:%s" % (config.getOS(),custom, countryName, cityName, serverAddress) )
        if config.isAndroid():
            Logger.log("Creating AndroidVPNConnector ...")
            return AndroidVPNConnector(countryName, cityName, serverAddress, custom)
        elif config.isLinux():
            Logger.log("Creating LinuxVPNConnector ...")
            return LinuxVPNConnector(countryName, cityName, serverAddress, custom)
        elif config.isWindows():
            Logger.log("Creating windowsVPNConnector ...")
            return WindowsVPNConnector(countryName, cityName, serverAddress, custom)
        elif config.isOpenElec():
            Logger.log("Creating OpenElecVPNConnector ...")
            return OpenElecVPNConnector(countryName, cityName, serverAddress, custom)
        elif config.isRaspBMC():
            Logger.log("Creating RaspBMCVPNConnector ...")
            return RaspBMCVPNConnector(countryName, cityName, serverAddress, custom)
        raise Exception("Platform %s not supported" % config.getOS())

