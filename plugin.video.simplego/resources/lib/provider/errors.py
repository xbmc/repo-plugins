"""The client's errors: what the provider refused, each with the message key the user sees (kind)."""


class ApiError(Exception):
    """The provider refused a call or could not be reached; base of the client's errors.

    kind: the user-facing message key (see service.quickplay.ERRORS).
    """

    kind = None


class AuthError(ApiError):
    """The stored login is missing or no longer accepted; a new login is needed."""

    kind = "auth"


class GeoBlockedError(ApiError):
    """The provider refused playback from outside Hungary (7027, "out of country blocked")."""

    kind = "geo"


class NotSubscribedError(ApiError):
    """The channel is in the channel map but not in the subscription."""

    kind = "subscription"


class LicenceRefusedError(ApiError):
    """The licence server refused this device's Widevine module before (3099); retrying is futile."""

    kind = "licence"

    def __init__(self, code):
        ApiError.__init__(self, "licence refused before (%s)" % code)
        self.code = code


class RestartNotAllowedError(ApiError):
    """The programme on air may not be watched from its beginning (its "rn" flag)."""

    kind = "restart"


class ArchiveUnavailableError(ApiError):
    """The programme cannot be watched back (no "ct" flag, or the server's 2401)."""

    kind = "archive"


class CatchupExpiredError(ArchiveUnavailableError):
    """The programme's catch-up time is over (the server's 2425): it was on catch-up, but not any more."""

    kind = "expired"


class ParentalLockError(ApiError):
    """The parental lock holds the programme and no right PIN was given for it."""

    kind = "parental"


class CancelledError(ApiError):
    """The user cancelled a pre-play question (where to resume)."""

    kind = "cancelled"
