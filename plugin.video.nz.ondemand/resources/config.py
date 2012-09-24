import sys, xbmc, xbmcaddon

__name__ = 'plugin.video.nz.ondemand'
__settings__ = xbmcaddon.Addon(id = __name__)
__cache__ = xbmc.translatePath('special://temp/%s' % __name__)
__data__ = xbmc.translatePath('special://profile/addon_data/%s' % __name__)
__language__ = __settings__.getLocalizedString
__id__ = int(sys.argv[1])
__path__ = __settings__.getAddonInfo('path')
