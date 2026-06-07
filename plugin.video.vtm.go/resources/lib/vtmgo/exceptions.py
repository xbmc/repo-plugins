# -*- coding: utf-8 -*-
""" Exceptions """

from __future__ import absolute_import, division, unicode_literals


class NoLoginException(Exception):
    """ Is thrown when the user need to follow the authorization flow. """


class InvalidTokenException(Exception):
    """ Is thrown when the token is invalid. """


class InvalidLoginException(Exception):
    """ Is thrown when the credentials are invalid. """


class UnavailableException(Exception):
    """ Is thrown when an item is unavailable. """


class StreamGeoblockedException(Exception):
    """ Is thrown when a geoblocked item is played. """


class StreamUnavailableException(Exception):
    """ Is thrown when an unavailable item is played. """


class LimitReachedException(Exception):
    """ Is thrown when the limit is reached to play an stream. """
