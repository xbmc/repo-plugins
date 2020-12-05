# -*- coding: utf-8 -*-
"""
    Copyright (C) 2020 Tubed (plugin.video.tubed)

    This file is part of plugin.video.tubed

    SPDX-License-Identifier: GPL-2.0-only
    See LICENSES/GPL-2.0-only.txt for more information.
"""

import re
from urllib.parse import parse_qs
from urllib.parse import unquote as uquote
from urllib.parse import urlencode

from ..constants import ADDON_ID
from ..constants import MODES
from ..constants import SCRIPT_MODES


def parse_query(query):
    payload = {
        'mode': str(MODES.MAIN)
    }

    args = parse_qs(query.lstrip('?'))

    for arg in args:
        if len(args[arg]) == 1:
            payload[arg] = args[arg][0]

        else:
            payload[arg] = args[arg]

    return payload


def parse_script_query(argv):
    payload = {
        'mode': str(SCRIPT_MODES.MAIN)
    }

    argv = argv.split('&')

    args = [arg.split('=') for arg in argv if len(arg.split('=')) == 2]

    for arg in args:
        payload[arg[0].lower()] = arg[1]

    return payload


def create_addon_path(parameters):
    return '?'.join(['plugin://%s/' % ADDON_ID, urlencode(parameters)])


def unquote(string):
    try:
        return uquote(string)
    except:  # pylint: disable=bare-except
        return string


def extract_urls(string):
    compiled = re.compile(r'(https?://[^\s]+)')
    matches = compiled.findall(string)

    result = matches or []
    return result
