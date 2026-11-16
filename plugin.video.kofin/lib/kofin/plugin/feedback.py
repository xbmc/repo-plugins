"""What a plugin route tells the viewer when a request fails.

One spelling for every route: the session refused (the way back in is the
Account tab), a server that answered badly (its answer), or a server that
could not be reached.
"""

from kofin.core import settings, toast
from kofin.core.http import HttpError, JellyfinError, Unauthorized


def message(error: Exception) -> str:
    if isinstance(error, Unauthorized):
        return settings.localized(30022)
    if isinstance(error, HttpError):
        return settings.localized(30821) % error
    return settings.localized(30018)


def failed(error: Exception, time_ms: int = 4000) -> None:
    """Toast the failure. ``error`` is what the request raised."""
    toast.show(message(error), toast.ERROR, time_ms=time_ms)


__all__ = ["JellyfinError", "failed", "message"]
