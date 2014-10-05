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
import requests

import traceback
import xbmc


class Logger:

    LOG_DEBUG = xbmc.LOGDEBUG
    LOG_INFO = xbmc.LOGINFO
    LOG_WARNING = xbmc.LOGWARNING
    LOG_ERROR = xbmc.LOGERROR
    LOG_FATAL = xbmc.LOGFATAL

    @classmethod
    def log(cls, msg, level = LOG_INFO, prefix = "Datho VPN"):

        return xbmc.log("%s %s" % (prefix, msg), level)


def GetPublicNetworkInformation():
    
    for i in range(2):
        xbmc.sleep(250)        
        
        data = GetPrimaryPublicNetworkInformation()
        if data:
            return data
            
        xbmc.sleep(250)        
            
        data = GetSecondaryPublicNetworkInformation()
        if data:
            return data

    return None    
    
    

def GetSecondaryPublicNetworkInformation():

    url = 'http://www.ip2location.com/'
    try:
        Logger.log("GetSecondaryPublicNetworkInformation: trying to get information ...", Logger.LOG_DEBUG)
        response = requests.get(url)
        content = response.content
        ipAddressMatch   = re.compile("<td><label>(.+?)</label></td>").findall(content)
        countryMatch   = re.compile("<td><label for=\"chkCountry\">(.+?)</label></td>").findall(content)
        cityMatch   = re.compile("<td><label for=\"chkRegionCity\">(.+?)</label></td>").findall(content)
    
        if len(ipAddressMatch)!=2 or len(countryMatch)!=2 or len(cityMatch)!=2:
            Logger.log("There was an error parsing network data from %s" % url)
            return None
    
        Logger.log("GetSecondaryPublicNetworkInformation: ip:%s country:%s city:%s" % (ipAddressMatch[1], countryMatch[1], cityMatch[1]), Logger.LOG_DEBUG)
        return ipAddressMatch[1], countryMatch[1], cityMatch[1]
    except Exception:
        Logger.log("GetSecondaryPublicNetworkInformation: there was an error getting data...", Logger.LOG_DEBUG)
        traceback.print_exc()
        return None
        
        
def GetPrimaryPublicNetworkInformation():

    url = "http://whatismyipaddress.com/"
    user_agent = {'User-agent': 'Mozilla/5.0'}
    try:
        Logger.log("GetPrimaryPublicNetworkInformation: trying to get information ...", Logger.LOG_DEBUG)

        response = requests.get(url, headers = user_agent)
        content = response.content
        
        ipAddressMatch   = re.compile("<!-- do not script -->\n(.+?)\n<!-- do not script -->").findall(content)
        countryMatch   = re.compile("Country:</th><td style=\"font-size:14px;\">(.+?)</td></tr>").findall(content)
        cityMatch   = re.compile("City:</th><td style=\"font-size:14px;\">(.+?)</td></tr>").findall(content)
    
        if len(ipAddressMatch)!=1 or len(countryMatch)!=1 or len(cityMatch)!=1:
            Logger.log("GetPrimaryPublicNetworkInformation: could not parse data ...", Logger.LOG_DEBUG)
            return None
    
        Logger.log("GetPrimaryPublicNetworkInformation: ip:%s country:%s city:%s" % (ipAddressMatch[0], countryMatch[0], cityMatch[0]), Logger.LOG_DEBUG)
        return ipAddressMatch[0], countryMatch[0], cityMatch[0]
    except Exception:        
        Logger.log("GetPrimaryPublicNetworkInformation: there was an error getting data...", Logger.LOG_DEBUG)
        traceback.print_exc()
        return None