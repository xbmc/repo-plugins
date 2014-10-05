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


import xbmcaddon
import xbmc

import os

ADDONID  = 'plugin.program.datho.vpn'
ADDON    =  xbmcaddon.Addon(ADDONID)
HOME     =  ADDON.getAddonInfo('path')
PROFILE  =  xbmc.translatePath(ADDON.getAddonInfo('profile'))
EXTERNAL = 0
TITLE    = 'Datho-Digital VPN'
VERSION  = '0.9.17'

COUNTRIES = {'AT' : 'Austria', 'AU':'Australia', 'BE':'Belguim', 'BR':'Brazil', 'CH':'Switzerland', 'DK':'Denmark', 'DE':'Germany', 'ES':'Spain', 'FR':'France', 'HU':'Hungary',  'JP':'Japan', 'KR':'South Korea', 'NL':'Netherlands', 'PL':'Poland', 'SE':'Sweden', 'SG':'Singapore', 'UK':'United Kingdom', 'US':'United  States'}
OpenVPNLogFilePath =  os.path.join(PROFILE, 'openvpn.log')
StdErrLogFilePath =  os.path.join(PROFILE, 'stderr.log')
IMAGES   =  os.path.join(HOME, 'resources', 'images')
ICON     =  os.path.join(HOME, 'icon.png')
FANART   =  os.path.join(HOME, 'fanart.jpg')
URL      =  'http://www.wlvpn.com/serverList.xml'

__language__ = ADDON.getLocalizedString

def getOS():
    return ADDON.getSetting('OS')

def isWindows():
    return getOS() == 'Windows'

def isLinux():
    return getOS() == 'Linux'

def isAndroid():
    return getOS() == 'Android'

def isOpenElec():
    return getOS() == 'OpenElec'

def isRaspBMC():
    return getOS() == 'RaspBMC'

def getSudo():
    if isWindows():
        return None, None

    sudopwd = None
    sudo    = ADDON.getSetting('SUDO') == 'true'

    if sudo:
        sudopwd = ADDON.getSetting('SUDOPASS')

    return sudo, sudopwd

def getUsername():
    baseUsername = ADDON.getSetting('USER')
    return baseUsername

def getPassword():
    return ADDON.getSetting('PASS')

def getPaidServersPostFix():
    return "@dathodigital"

# Return True if User and Password are not empty
def CheckCredentialsEmpty():
    user = ADDON.getSetting('USER')
    pwd  = getPassword()
    return user is '' or pwd is ''

def getSetting(name, defaultValue ):
    try:
        return ADDON.getSetting('PASS')
    except Exception:
        return defaultValue

def getIntSetting(name, defaultValue ):
    value = int(defaultValue)
    try:
        value = ADDON.getSetting(name)
    except Exception:
        pass

    return int(value)

def getTimeout():
    return getIntSetting('TIMEOUT', 1800)

def getPort():
    return ADDON.getSetting('PORT')


def _getConfigDirPath():
    return os.path.join(HOME, 'resources', 'configs')

def _getCustomConfigDirPath():
    return os.path.join( _getConfigDirPath(), 'custom')


def getCertFilePath():
    """
    Returns the Path containing the Certificate used by OpenVPN
    :return:
    """
    root    = _getConfigDirPath()
    return os.path.join(root, 'vpn.crt')

def getDathoCertFilePath():
    """
    Returns the Path containing the Certificate used by OpenVPN
    :return:
    """
    root    = _getConfigDirPath()
    return os.path.join(root, 'datho.crt')

def getCustomCertFilePath():
    """
    Returns the Path containing the Certificate used by OpenVPN
    :return:
    """
    customPath    = _getCustomConfigDirPath()
    return os.path.join(customPath, 'ca.crt')

def getCustomCrlFilePath():
    """
    Returns the Path containing the Certificate used by OpenVPN
    :return:
    """
    customPath    = _getCustomConfigDirPath()
    return os.path.join(customPath, 'crl.pem')

def getOpenVPNTemplateConfigFilePath():
    """
        Returns the Template file path containing the default configuration parameters for OpenVPN
        this file should always keep unchanged
    :return:s
    """
    root    = _getConfigDirPath()
    return os.path.join(root, 'cfg.opvn')

def getOpenVPNCustomTemplateConfigFilePath():
    """
        Returns the Template file path containing the default configuration parameters for OpenVPN
        this file should always keep unchanged
    :return:s
    """
    root    = _getCustomConfigDirPath()
    return os.path.join(root, 'cfg.opvn')


def getOpenVPNRealConfigFilePath():
    """
    Returns the file path where the configuration file containing the OpenVPN Parameters is
    :return:aaa
    """
    return os.path.join(PROFILE, 'cfg.opvn')


def getActionUrl():
    return "http://www.dathovpn.com/service/addon/action/"

def getVPNType():
    return ADDON.getSetting('VPNTYPE')

def isVPNCustom():
    return getVPNType()=="Custom"

def getConfiguredServerAddress():
    return ADDON.getSetting("SERVER_ADDRESS")

