"""
    Pitchfork TV
    maruchan
"""
import sys
import xbmcaddon
#import xbmcaddon

#plugin constants
__plugin__ = "Pitchfork TV"
__author__ = "maruchan"
__version__ = "1.1.0"
__settings__ = xbmcaddon.Addon(id='plugin.video.pitchfork')

print "[PLUGIN] '%s: version %s' initialized!" % (__plugin__, __version__)

if __name__ == "__main__":
    from resources.lib import pitchfork_main
    pitchfork_main.Main()

sys.modules.clear()