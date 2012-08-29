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
__settings__ = xbmcaddon.Addon(id='plugin.video.animeftw')

print "[PLUGIN] '%s: version initialized!" % (__plugin__)

if __name__ == "__main__":
    from resources.lib import main_ftw2
    main_ftw2.Main()

sys.modules.clear()