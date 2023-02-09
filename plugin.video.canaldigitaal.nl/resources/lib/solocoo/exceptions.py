# -*- coding: utf-8 -*-
""" Exceptions """

from __future__ import absolute_import, division, unicode_literals


class NotAvailableInOfferException(Exception):
    """ Is thrown when the requested item isn't available in your offer. """


class UnavailableException(Exception):
    """ Is thrown when an item is unavailable. """


class InvalidTokenException(Exception):
    """ Is thrown when the token is invalid. """


class InvalidLoginException(Exception):
    """ Is thrown when the credentials are invalid. """
