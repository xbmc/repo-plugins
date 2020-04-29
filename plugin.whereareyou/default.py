from kodi_six import xbmc, xbmcaddon
from resources.lib.whereareyou import Main

addon        = xbmcaddon.Addon()
addonversion = addon.getAddonInfo('version')
preamble     = '[Where Are You]'


if ( __name__ == "__main__" ):
    xbmc.log( '%s script version %s started' % (preamble, addonversion), xbmc.LOGINFO )
    action = Main()
xbmc.log( '%s script stopped' % preamble, xbmc.LOGINFO )
