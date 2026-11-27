"""Local dates and times as Kodi's region setting writes them, with Kodi's own day and month names."""

import re
import time

import xbmc

from resources.lib import kodiutil
from resources.lib.util import isotime

# Kodi's string ids of the day and month names: a day's is its base plus its weekday (Monday 0),
# a month's its base plus its number (January 1).
WEEKDAY_NAMES = 11
WEEKDAY_ABBREVS = 41
MONTH_NAMES = 20
MONTH_ABBREVS = 50

_REGION = {}  # Kodi's region formats, asked once per call of the add-on (see region)

# Kodi writes a number without its leading zero as "%-d" ("%#d" on Windows), which Android's
# strftime prints as it is ("október -d."): such numbers are filled in before it formats.
_CODE = re.compile(r"%(%|[-#][dmHIMSjy]|.)")


def region(what):
    """Return one of Kodi's region formats (xbmc.getRegion), asked once: a list's rows ask it again and again."""
    if what not in _REGION:
        _REGION[what] = xbmc.getRegion(what)
    return _REGION[what]


def local_date(stamp):
    """Format a timestamp's local date as Kodi's region setting's short date says.

    Day and month names are Kodi's (in its language): strftime's would be the C locale's English ones.
    """
    moment = time.localtime(stamp)
    names = {
        "%A": kodiutil.kodi_string(WEEKDAY_NAMES + moment.tm_wday),
        "%a": kodiutil.kodi_string(WEEKDAY_ABBREVS + moment.tm_wday),
        "%B": kodiutil.kodi_string(MONTH_NAMES + moment.tm_mon),
        "%b": kodiutil.kodi_string(MONTH_ABBREVS + moment.tm_mon),
    }
    form = region("dateshort")
    for code, name in names.items():
        form = form.replace(code, name.replace("%", "%%"))
    return _strftime(form, moment)


def local_clock(stamp):
    """Format a timestamp's local time of day as Kodi's region setting says, without seconds."""
    return _strftime(region("time").replace(":%S", ""), time.localtime(stamp))


def local_time(iso, date=True):
    """Format an ISO UTC time ("2026-10-26T22:00:00Z") as Kodi's short date and time (or the time only), in local time."""
    stamp = isotime.stamp(iso)
    return "%s %s" % (local_date(stamp), local_clock(stamp)) if date else local_clock(stamp)


def _strftime(form, moment):
    """Return time.strftime(form, moment) with Kodi's unpadded numbers ("%-d", "%#d") filled in."""

    def unpadded(m):
        code = m.group(1)
        if len(code) == 2:
            return str(int(time.strftime("%" + code[1], moment)))
        return m.group(0)

    return time.strftime(_CODE.sub(unpadded, form), moment)
