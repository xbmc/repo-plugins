
# ------------------------------------------------------------------------------
#  Copyright (c) 2026 Dimitri Kroon.
#  This file is part of plugin.audio.bbcsounds.
#  SPDX-License-Identifier: GPL-3.0-or-later
#  See LICENSE.txt or https://www.gnu.org/licenses/gpl-3.0.txt
# ------------------------------------------------------------------------------

import xbmc


def log(msg: str, *args, exc_info: bool = False):
    txt = '[BBC Sounds] ' + msg % args
    if exc_info:
        from traceback import format_exc
        txt = '\n'.join((txt, format_exc()))
    xbmc.log(txt, xbmc.LOGDEBUG)


# Python logging compatibles:
debug = log
info = log
warning = log
error = log
critical = log
