# -*- coding: utf-8 -*-
"""
    Copyright (C) 2020 Tubed (plugin.video.tubed)

    This file is part of plugin.video.tubed

    SPDX-License-Identifier: GPL-2.0-only
    See LICENSES/GPL-2.0-only.txt for more information.
"""

import datetime
import time


def strptime(timestamp, timestamp_format):
    import _strptime  # pylint: disable=import-outside-toplevel
    try:
        time.strptime('01 01 2012', '%d %m %Y')
    finally:
        return time.strptime(timestamp, timestamp_format)  # pylint: disable=lost-exception


def now():
    # now that always has microseconds
    _now = datetime.datetime.now()

    try:
        _ = datetime.datetime(*(strptime(_now.strftime('%Y-%m-%d %H:%M:%S.%f'),
                                         '%Y-%m-%d %H:%M:%S.%f')[0:6]))
        return _now
    except:  # pylint: disable=bare-except
        return _now + datetime.timedelta(microseconds=1)


def timestamp_diff(timestamp=None):
    if not timestamp:
        return 86400

    try:
        then = datetime.datetime(*(strptime(timestamp, '%Y-%m-%d %H:%M:%S.%f')[0:6]))
    except ValueError:
        then = datetime.datetime(*(strptime(timestamp, '%Y-%m-%d %H:%M:%S')[0:6]))
    except TypeError:
        return 604800

    delta = now() - then

    return delta.total_seconds()


def iso8601_duration_to_seconds(duration):
    macro_string = ''
    micro_string = duration

    years = 0
    months = 0
    weeks = 0
    days = 0
    hours = 0
    minutes = 0
    seconds = 0

    string = duration.split('P')[-1]

    if 'T' in string:
        macro_string, micro_string = string.split('T')

    if macro_string:
        years, macro_string = _iso8601_duration_token(macro_string, 'Y')
        months, macro_string = _iso8601_duration_token(macro_string, 'M')
        weeks, macro_string = _iso8601_duration_token(macro_string, 'W')
        days, macro_string = _iso8601_duration_token(macro_string, 'D')

    if micro_string:
        hours, micro_string = _iso8601_duration_token(micro_string, 'H')
        minutes, micro_string = _iso8601_duration_token(micro_string, 'M')
        seconds, micro_string = _iso8601_duration_token(micro_string, 'S')

    # add weeks, months and years to days, assume 30 day month and 365 day year for simplicity
    days = int(days) + (7 * int(weeks)) + (30 * int(months)) + (365 * int(years))

    time_delta = datetime.timedelta(
        days=int(days),
        hours=int(hours),
        minutes=int(minutes),
        seconds=int(seconds)
    )

    return int(time_delta.total_seconds())


def _iso8601_duration_token(string, token):
    payload = 0

    if token in string:
        payload, string = string.split(token)

    return payload, string
