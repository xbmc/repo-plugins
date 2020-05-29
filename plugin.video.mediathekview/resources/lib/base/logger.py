# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT
"""
The base logger module

Copyright 2017-2018, Leo Moll and Dominik Schlösser
"""


class Logger(object):
    """
    The logger base class

    Args:
        name(str): Name of the logger

        version(str): Version string of the application

        topic(str, optional): Topic string displayed in messages
            from this logger. Default is `None`
    """

    def __init__(self, name, version, topic=None):
        self.name = name
        self.version = version
        self.prefix = None
        self.set_topic(topic)

    def get_new_logger(self, topic=None):
        """
        Generates a new logger instance with a specific topic

        Args:
            topic(str, optional): the topic of the new logger.
                Default is the same topic of `self`
        """
        pass

    def set_topic(self, topic=None):
        """
        Changes the topic of the logger

        Args:
            topic(str, optional): the new topic of the logger.
                If not specified or `None`, the logger will have
                no topic. Default is `None`
        """
        if topic is None:
            self.prefix = '[%s-%s]: ' % (self.name, self.version)
        else:
            self.prefix = '[%s-%s:%s]: ' % (self.name, self.version, topic)

    def debug(self, message, *args):
        """ Outputs a debug message """
        pass

    def info(self, message, *args):
        """ Outputs an info message """
        pass

    def warn(self, message, *args):
        """ Outputs a warning message """
        pass

    def error(self, message, *args):
        """ Outputs an error message """
        pass
