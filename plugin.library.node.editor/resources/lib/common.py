
import sys
import os
import xbmc, xbmcaddon

ADDON        = xbmcaddon.Addon()
ADDONID      = ADDON.getAddonInfo('id')
ADDONVERSION = ADDON.getAddonInfo('version')
LANGUAGE     = ADDON.getLocalizedString
CWD          = ADDON.getAddonInfo('path')
ADDONNAME    = ADDON.getAddonInfo('name')
DATAPATH     = xbmc.translatePath(xbmcaddon.Addon().getAddonInfo('profile'))
DEFAULTPATH  = os.path.join( CWD, 'resources' )

def log(txt):
    message = u'%s: %s' % (ADDONID, txt)
    xbmc.log(msg=message, level=xbmc.LOGDEBUG)