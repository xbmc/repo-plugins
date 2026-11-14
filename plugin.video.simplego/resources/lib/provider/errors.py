"""The client's errors: what the provider refused, each with the message key the user sees (kind)."""


class ApiError(Exception):
    """The provider refused a call or could not be reached; base of the client's errors.

    kind: the user-facing message key (see playmessages.ERRORS).

    :param code: the provider's error code, if it gave one
    :param status: the HTTP status, if the call got that far
    """

    kind = None
    # Something else to watch, set by the view that caught it (see plugin.tell).
    offer = None

    def __init__(self, message="", code=None, status=None):
        Exception.__init__(self, message)
        self.code = code
        self.status = status


class AuthError(ApiError):
    """The stored login is missing or no longer accepted; a new login is needed."""

    kind = "auth"


class GeoBlockedError(ApiError):
    """The provider refused playback from this address."""

    kind = "geo"


class NotSubscribedError(ApiError):
    """The channel is in the channel map but not in the subscription."""

    kind = "subscription"


class LicenceRefusedError(ApiError):
    """The licence server refuses this device's Widevine module; retrying is futile.

    :param code: the server's refusal code; None when the caller knows it would be refused and never asked
    """

    kind = "licence"

    def __init__(self, code=None):
        ApiError.__init__(self, "licence refused (%s)" % (code or "not asked"), code=code)


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
