import os
import xbmcaddon

#
# Constants
# 
__settings__    = xbmcaddon.Addon(id='plugin.video.gamegurumania')
__language__    = __settings__.getLocalizedString
__images_path__ = os.path.join( xbmcaddon.Addon(id='plugin.video.gamegurumania').getAddonInfo('path'), 'resources', 'images' )
__addon__       = "plugin.video.gamegurumania"
__plugin__      = "GameGuruMania"
__author__      = "Skipmode A1"
__url__         = ""
__date__        = "02 oktober 2014"
__version__     = "1.0.2"