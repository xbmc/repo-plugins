# ------------------------------------------------------------------------------
#  Copyright (c) 2026 Dimitri Kroon.
#  This file is part of plugin.audio.bbcsounds.
#  SPDX-License-Identifier: GPL-3.0-or-later
#  See LICENSE.txt or https://www.gnu.org/licenses/gpl-3.0.txt
# ------------------------------------------------------------------------------

import time
from datetime import datetime


try:
    # noinspection compatibility
    from zoneinfo import ZoneInfo
except ImportError:
    # python < 3.9
    # noinspection unresolved-references
    from backports.zoneinfo import ZoneInfo


# noinspection shadowing-builtins
def strptime(date_string: str, format: str) -> datetime:
    """A bug-free alternative to `datetime.datetime.strptime(...)`"""
    return datetime(*(time.strptime(date_string, format)[0:6]))
