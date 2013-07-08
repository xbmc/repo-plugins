import os
import xbmcaddon

#
# Constants
# 
__addon__       = "plugin.video.nlhardwareinfo"
__settings__    = xbmcaddon.Addon(id=__addon__ )
__language__    = __settings__.getLocalizedString
__images_path__ = os.path.join( xbmcaddon.Addon(id=__addon__ ).getAddonInfo('path'), 'resources', 'images' )
__date__        = "3 july 2013"
__version__     = "1.0.2"