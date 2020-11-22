# -*- coding: utf-8 -*-
"""
The Kodi logger module

Copyright 2017-2018, Leo Moll and Dominik Schlösser
SPDX-License-Identifier: MIT
"""

# pylint: disable=import-error
import xbmc

from resources.lib.base.logger import Logger
import resources.lib.mvutils as mvutils

class KodiLogger(Logger):
    """
    The Kodi logger class

    Args:
        name(str): Name of the logger

        version(str): Version string of the application

        topic(str, optional): Topic string displayed in messages
            from this logger. Default is `None`
    """

    def get_new_logger(self, topic=None):
        """
        Generates a new logger instance with a specific topic

        Args:
            topic(str, optional): the topic of the new logger.
                Default is the same topic of `self`
        """
        return KodiLogger(self.name, self.version, topic)

    def debug(self, message, *args):
        """ Outputs a debug message """
        self._log(xbmc.LOGDEBUG, message, *args)

    def info(self, message, *args):
        """ Outputs an info message """
        self._log(xbmc.LOGINFO, message, *args)

    def warn(self, message, *args):
        """ Outputs a warning message """
        self._log(xbmc.LOGWARNING, message, *args)

    def error(self, message, *args):
        """ Outputs an error message """
        self._log(xbmc.LOGERROR, message, *args)

    def _log(self, level, message, *args):
        parts = []
        for arg in args:
            part = arg
            if isinstance(arg, str):
                part = mvutils.py2_encode(arg)
            parts.append(part)
        xbmc.log(self.prefix + message.format(*parts), level=level)
