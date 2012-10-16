"""
Contains constants that we initialize to the correct values at runtime.
"""
__plugin__ = "TED Talks Uninitialized Plugin"
getLS = lambda x: x
__pluginLS__ = __plugin__
__author__ = "XXX"
__version__ = "X.X.X"


def init():
    import xbmcaddon
    addon = xbmcaddon.Addon(id='plugin.video.ted.talks')
    global __plugin__, getLS, __author__, __version__, __pluginLS__
    __plugin__ = addon.getAddonInfo('name')
    getLS = addon.getLocalizedString
    __pluginLS__ = getLS(30000)
    __author__ = addon.getAddonInfo('author')
    __version__ = addon.getAddonInfo('version')
    print "[PLUGIN] '%s: version %s' initialized!" % (__plugin__, __version__)

def report(gnarly_message, friendly_message=None):
    import xbmc
    print "[%s] %s" % (__plugin__, gnarly_message)
    if friendly_message:
        xbmc.executebuiltin('Notification("%s","%s",)' % (__pluginLS__, friendly_message))
