# -*- coding: utf-8 -*-
# Copyright: (c) 2016, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import numbers
import time


def old_div(a, b):
    """Python 2 and 3 Integer division cheat (https://python-future.org/compatible_idioms.html#division)

    """
    if isinstance(a, numbers.Integral) and isinstance(b, numbers.Integral):
        return a // b

    return a / b


def current_timestamp():
    """Get current timestamp (Unix time, the same given here https://timestamp.online)

    Returns:
        float: Current timestamp
    """
    return time.time()
