
# ------------------------------------------------------------------------------
#  Copyright (c) 2022 Dimitri Kroon
#
#  SPDX-License-Identifier: GPL-2.0-or-later
#  This file is part of plugin.video.cinetree
#
# ------------------------------------------------------------------------------

from codequick.script import Script


class FetchError(IOError):
    pass


class AccessRestrictedError(FetchError):
    """Raised on HTTP errors 'Not Allowed' or 'Not Authenticated' while successfully logged in."""
    def __init__(self, msg=None):
        super(AccessRestrictedError, self).__init__(
            msg or Script.localize(30901))


class NoSubscriptionError(AccessRestrictedError):
    pass


class NotPaidError(AccessRestrictedError):
    pass


class AuthenticationError(FetchError):
    def __init__(self, msg=None):
        super(AuthenticationError, self).__init__(
            msg or Script.localize(30902))


class GeoRestrictedError(FetchError):
    def __init__(self, msg=None):
        super(GeoRestrictedError, self).__init__(
            msg or Script.localize(30904))


class HttpError(FetchError):
    def __init__(self, code, reason):
        self.code = code
        self.reason = reason
        super(HttpError, self).__init__(Script.localize(30905).format(reason))


class ParseError(FetchError):
    def __init__(self, msg=None):
        super(ParseError, self).__init__(
            msg or Script.localize(30906))
