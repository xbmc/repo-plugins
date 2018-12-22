# -*- coding: utf-8 -*-
"""Various date and time conversions.

relative_day_resid and day_resid are for nice display, because "Yesterday"
looks more human than "03-08-2017".

The ones with "kodi" in their name should be kept carefully the same:
they return the formats that Kodi expects and parses. Kodi will silently
ignore unknown date and time formats.
"""
import datetime

from resources.lib import pypo


def relative_day_resid(days_ago, date):
    """Return the resource ID for a day in the past week, using words like "Yesterday". """
    if days_ago == 0:
        return pypo.strings.today
    if days_ago == 1:
        return pypo.strings.yesterday
    if days_ago == 2:
        return pypo.strings.day_before_yesterday
    return day_resid(date)


def day_resid(date):
    """Return the resource ID for the day name of a date, e.g. "Wednesday"."""
    weekday = int(date.strftime("%w"))
    if weekday == 0:
        return pypo.strings.sunday
    elif weekday == 1:
        return pypo.strings.monday
    elif weekday == 2:
        return pypo.strings.tuesday
    elif weekday == 3:
        return pypo.strings.wednesday
    elif weekday == 4:
        return pypo.strings.thursday
    elif weekday == 5:
        return pypo.strings.friday
    elif weekday == 6:
        return pypo.strings.saturday
    else:
        return -1


def time2kodi_datetime(time):
    """Convert a timestamp into a Kodi date + time string, like "2017-08-04 17:12:59"."""
    return date2kodi_datetime(datetime.datetime.fromtimestamp(time))


def time2kodi_date(time):
    """Convert a timestamp into a Kodi date string, like "04-08-2017"."""
    return date2kodi_date(datetime.datetime.fromtimestamp(time))


def date2kodi_date(date):
    """Convert a datetime into a Kodi date string, like "04-08-2017"."""
    return date.strftime("%d-%m-%Y")


def date2kodi_datetime(date):
    """Convert a datetime into a Kodi date + time string, like "2017-08-04 17:12:59"."""
    return date.strftime("%Y-%m-%d %H:%M:%S")


def time2kodi_time(time):
    """Convert a timestamp into a Kodi time string, like "17:12"."""
    return datetime.datetime.fromtimestamp(time).strftime("%H:%M")
