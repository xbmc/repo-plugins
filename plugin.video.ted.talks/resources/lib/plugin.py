"""
Contains constants that we initialize to the correct values at runtime.
"""
__plugin__ = "TED Talks Uninitialized Plugin"
__author__ = "XXX"
__version__ = "X.X.X"


def init():
    import xbmcaddon
    addon = xbmcaddon.Addon(id='plugin.video.ted.talks')
    global __plugin__, __author__, __version__
    __plugin__ = addon.getAddonInfo('name')
    __author__ = addon.getAddonInfo('author')
    __version__ = addon.getAddonInfo('version')
    print "[PLUGIN] '%s: version %s' initialized!" % (__plugin__, __version__)

def log(message):
    print "[%s] %s" % (__plugin__, message)