"""Orange TV France exceptions."""


class StreamRequestException(IOError):
    """There was an exception while handling stream request."""

    def __init__(self, *args, **kwargs):
        """Initialise StreamRequestException."""
        super().__init__(*args, **kwargs)


class AuthenticationRequired(StreamRequestException):
    """Authentication is required in order to request stream."""


class StreamNotIncluded(StreamRequestException):
    """Requested stream is not included in subscription."""


class StreamDataDecodeError(StreamRequestException):
    """Stream data can't be read."""
