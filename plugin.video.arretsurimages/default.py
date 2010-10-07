"""
    Arret Sur Images
    beenje

    based on TED Talks by rwparris2
"""
import sys
import xbmcaddon
import urllib

# plugin constants
__plugin__ = "Arret Sur Images"
__author__ = "beenje"
__url__ = "http://github.com/beenje/plugin.video.arretsurimages"
__version__ = "1.0.0"
__settings__ = xbmcaddon.Addon(id='plugin.video.arretsurimages')

print "[PLUGIN] '%s: version %s' initialized!" % (__plugin__, __version__)

if __name__ == "__main__":
    import resources.lib.asi as asi

    if not __settings__.getSetting('alreadyrun'):
        __settings__.openSettings()
        __settings__.setSetting('alreadyrun', '1')

    if not sys.argv[2]:
        asi.Main()
    elif sys.argv[2].startswith('?download'):
        asi.Main(checkMode=False).downloadVideo(urllib.unquote_plus(sys.argv[2].split('=')[-1]))
    else:
        asi.Main()

sys.modules.clear()
