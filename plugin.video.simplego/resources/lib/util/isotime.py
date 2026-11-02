"""The provider's UTC time format, e.g. "2026-10-29T07:00:00Z"."""

import time

FORMAT = "%Y-%m-%dT%H:%M:%SZ"


def iso(when=None):
    """Return the time `when` (Unix seconds; now if None) as the provider writes it."""
    return time.strftime(FORMAT, time.gmtime(when))


def stamp(text):
    """Return the Unix time of a time written as the provider does.

    :raises ValueError: not written so
    """
    # Lazy: calendar pulls in datetime and locale, a fifth of a live channel switch's imports.
    import calendar

    return calendar.timegm(time.strptime(text, FORMAT))
