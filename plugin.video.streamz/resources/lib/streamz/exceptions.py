# -*- coding: utf-8 -*-
""" Exceptions """

from __future__ import absolute_import, division, unicode_literals


class NoLoginException(Exception):
    """ Is thrown when the user need to follow the authorization flow. """


class InvalidTokenException(Exception):
    """ Is thrown when the token is invalid. """


class NoStreamzSubscriptionException(Exception):
    """ Is thrown when you don't have an subscription with Streamz. """


class NoTelenetSubscriptionException(Exception):
    """ Is thrown when you don't have an subscription with Telenet. """


class LoginErrorException(Exception):
    """ Is thrown when we could not login. """

    def __init__(self, code):
        super(LoginErrorException, self).__init__()
        self.code = code


class UnavailableException(Exception):
    """ Is thrown when an item is unavailable. """


class LimitReachedException(Exception):
    """ Is thrown when the limit is reached to play an stream. """
