# -*- coding: utf-8 -*-
""" Exceptions """

from __future__ import absolute_import, division, unicode_literals


class NoLoginException(Exception):
    """ Is thrown when the user has no credentials. """


class InvalidTokenException(Exception):
    """ Is thrown when the token is invalid. """


class InvalidLoginException(Exception):
    """ Is thrown when the credentials are invalid. """


class NoStreamzSubscriptionException(Exception):
    """ Is thrown when you don't have an subscription. """


class NoTelenetSubscriptionException(Exception):
    """ Is thrown when you don't have an subscription. """


class LoginErrorException(Exception):
    """ Is thrown when we could not login. """

    def __init__(self, code):
        super(LoginErrorException, self).__init__()
        self.code = code


class UnavailableException(Exception):
    """ Is thrown when an item is unavailable. """


class StreamGeoblockedException(Exception):
    """ Is thrown when a geoblocked item is played. """


class StreamUnavailableException(Exception):
    """ Is thrown when an unavailable item is played. """
