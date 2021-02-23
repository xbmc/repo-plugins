# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT
"""
The base logger module

Copyright 2017-2018, Leo Moll and Dominik Schlösser
"""

import datetime
import sys
import resources.lib.mvutils as mvutils
from resources.lib.loggerInterface import LoggerInterface


class LoggerCommandline(LoggerInterface):
    """ Standalone implementation of the logger class """

    def __init__(self, name, version, topic=None, verbosity=0):
        super(LoggerCommandline, self).__init__(name, version, topic)
        self.verbosity = verbosity

    def get_new_logger(self, topic=None):
        """
        Generates a new logger instance with a specific topic

        Args:
            topic(str, optional): the topic of the new logger.
                Default is the same topic of `self`
        """
        return LoggerCommandline(self.name, self.version, topic, self.verbosity)

    def debug(self, message, *args):
        """ Outputs a debug message """
        self._log(2, message, *args)

    def info(self, message, *args):
        """ Outputs an info message """
        self._log(1, message, *args)

    def warn(self, message, *args):
        """ Outputs a warning message """
        self._log(0, message, *args)

    def error(self, message, *args):
        """ Outputs an error message """
        self._log(-1, message, *args)

    def _log(self, level, message, *args):
        parts = []
        for arg in args:
            part = arg
            if isinstance(arg, str):
                part = mvutils.py2_encode(arg)
            parts.append(part)
        output = '{} {} {}{}'.format(
            datetime.datetime.now(),
            {-1: 'ERROR', 0: 'WARNING', 1: 'INFO', 2: 'DEBUG'}.get(level, 2),
            self.prefix,
            message.format(*parts)
        )

        if level < 0:
            # error
            sys.stderr.write(output + '\n')
            sys.stderr.flush()
        elif self.verbosity >= level:
            # other message
            # pylint: disable=superfluous-parens
            print(output)
