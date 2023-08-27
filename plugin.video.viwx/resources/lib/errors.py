
# ----------------------------------------------------------------------------------------------------------------------
#  Copyright (c) 2022-2023 Dimitri Kroon.
#  This file is part of plugin.video.viwx.
#  SPDX-License-Identifier: GPL-2.0-or-later
#  See LICENSE.txt
# ----------------------------------------------------------------------------------------------------------------------


class FetchError(IOError):
    pass


class AccountError(Exception):
    def __init__(self, descr):
        super(AccountError, self).__init__(descr)


class AuthenticationError(FetchError):
    def __init__(self, msg=None):
        super(AuthenticationError, self).__init__(
            msg or 'Login required')


class GeoRestrictedError(FetchError):
    def __init__(self, msg=None):
        super(GeoRestrictedError, self).__init__(
            msg or 'Service is not available in this area')


class AccessRestrictedError(FetchError):
    def __init__(self, msg=None):
        super(AccessRestrictedError, self).__init__(
            msg or 'Access not allowed')


class HttpError(FetchError):
    def __init__(self, code, reason):
        self.code = code
        self.reason = reason
        super(HttpError, self).__init__(u'Connection error: {}'.format(reason))


class ParseError(FetchError):
    def __init__(self, msg=None):
        super(ParseError, self).__init__(
            msg or u'Error parsing data')
