"""
    AnimeFTW
    maruchan
"""
import sys
import xbmcaddon
#import xbmcaddon

#plugin constants
__plugin__ = "AnimeFTW"
__author__ = "maruchan"
__version__ = "1.5.5"
__settings__ = xbmcaddon.Addon(id='plugin.video.animeftw')

print "[PLUGIN] '%s: version %s' initialized!" % (__plugin__, __version__)

if __name__ == "__main__":
    from resources.lib import main_ftw
    main_ftw.Main()

sys.modules.clear()