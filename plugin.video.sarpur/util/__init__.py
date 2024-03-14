#!/usr/bin/env python
# encoding: UTF-8
from __future__ import absolute_import

import time
from datetime import datetime


def strptime(date_string, format):
    """
    Wrapper for datetime.strptime() because of an odd bug.
    See: http://forum.kodi.tv/showthread.php?tid=112916

    :param date_string: A string representing a date
    :param format: The format of the date
    :return: A datetime object
    """
    try:
        return datetime.strptime(date_string, format)
    except TypeError:
        return datetime(*(time.strptime(date_string, format)[0:6]))
