"""Utility classes and methods"""
from __future__ import absolute_import, division, unicode_literals
import xbmc
import xbmcgui
import xbmcaddon

__addon__ = xbmcaddon.Addon()


def ask_for_input(category):
    """Input dialog box"""
    return xbmcgui.Dialog().input(
        defaultt='',
        heading='Search in ' + category,
        type=xbmcgui.INPUT_ALPHANUM) or None


class Logger:
    """Logger class"""
    @staticmethod
    def log(message, level=xbmc.LOGDEBUG):
        """Generic log method defaults to debug"""
        xbmc.log('{0}: {1}'.format(__addon__.getAddonInfo('id'), message), level)

    @staticmethod
    def info(message):
        """Info log method"""
        Logger.log(message, xbmc.LOGINFO)

    @staticmethod
    def error(message):
        """Error log method"""
        Logger.log(message, xbmc.LOGERROR)

    @staticmethod
    def warn(message):
        """Warn log method"""
        Logger.log(message, xbmc.LOGWARNING)

    @staticmethod
    def debug(message):
        """Debug log method"""
        Logger.log(message, xbmc.LOGDEBUG)
