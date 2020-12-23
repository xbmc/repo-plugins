# coding: utf-8
from __future__ import print_function, division, absolute_import

try:
    import xbmcgui
except ImportError:
    import warnings
    warnings.warn('Not running under Kodi, GUI will not work!')
    xbmcgui = None


class Fakexbmc(object):
    NOTIFICATION_ERROR = "ERR"
    NOTIFICATION_INFO = "INFO"

    class Dialog(object):
        def notification(self, title, msg, level, timeout):
            warnings.warn("%s: %s" % (level, msg))


if not xbmcgui:
    xbmcgui = Fakexbmc()


def err(text):
    msg(text, xbmcgui.NOTIFICATION_ERROR, 30)


def info(text):
    msg(text, xbmcgui.NOTIFICATION_INFO)


def msg(text, level, time=15):
    xbmcgui.Dialog().notification('media.ccc.de', text, level, time * 1000)
