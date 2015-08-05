import os
import xbmcaddon

#
# Constants
# 
__addon__       = "plugin.video.worldstarhiphop"
__settings__    = xbmcaddon.Addon(id=__addon__ )
__language__    = __settings__.getLocalizedString
__images_path__ = os.path.join( xbmcaddon.Addon(id=__addon__ ).getAddonInfo('path'), 'resources', 'images' )
__addon__       = "plugin.video.worldstarhiphop"
__date__        = "05 august 2015"
__version__     = "1.0.2"
