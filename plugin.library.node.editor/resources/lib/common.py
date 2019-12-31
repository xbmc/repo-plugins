
import sys
import os
import xbmc, xbmcaddon

PY3 = sys.version_info.major >= 3


ADDON        = xbmcaddon.Addon()
ADDONID      = ADDON.getAddonInfo('id') if PY3 else ADDON.getAddonInfo('id').decode( 'utf-8' )
ADDONVERSION = ADDON.getAddonInfo('version')
LANGUAGE     = ADDON.getLocalizedString
CWD          = ADDON.getAddonInfo('path') if PY3 else  ADDON.getAddonInfo('path').decode("utf-8")
ADDONNAME    = ADDON.getAddonInfo('name') if PY3 else  ADDON.getAddonInfo('name').decode("utf-8")
DATAPATH     = xbmc.translatePath(xbmcaddon.Addon().getAddonInfo('profile')) if PY3 else xbmc.translatePath(xbmcaddon.Addon().getAddonInfo('profile')).decode('utf-8')
DEFAULTPATH  = os.path.join( CWD, 'resources' )

def log(txt):
    if isinstance (txt,str):
        if not PY3:
            txt = txt.decode('utf-8')
    message = u'%s: %s' % (ADDONID, txt)
    xbmc.log(msg=message if PY3 else message.encode("utf-8"), level=xbmc.LOGDEBUG)

def six_decoder(item):
    if PY3:
        return item
    return item.decode("utf-8")