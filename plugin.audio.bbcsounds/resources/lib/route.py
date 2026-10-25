# ------------------------------------------------------------------------------
#  Copyright (c) 2026 Dimitri Kroon.
#  This file is part of plugin.audio.bbcsounds.
#  SPDX-License-Identifier: GPL-3.0-or-later
#  See LICENSE.txt or https://www.gnu.org/licenses/gpl-3.0.txt
# ------------------------------------------------------------------------------

from __future__ import annotations
import os
import importlib

from functools import wraps
from collections.abc import Callable, Generator
from urllib.parse import parse_qsl, urlencode

from resources.lib.log import log


CONTENT = 'content'
RESOLVER = 'resolver'
SCRIPT = 'script'
ADDON_ID = 'plugin.audio.bbcsounds'


def content(func: Callable):
    @wraps(func)
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        if isinstance(result, Generator):
            result = list(result)
        return result
    wrapper.expose = CONTENT
    return wrapper


def resolve(func: Callable):
    func.expose = RESOLVER
    return func


def script(func: Callable):
    func.expose = SCRIPT
    return func


def build_callback(path: str, **kwargs):
    qs = urlencode(kwargs)
    return f'plugin://{ADDON_ID}/{path}?{qs}'


def route(callb_path: str, querystr: str):
    params = dict(parse_qsl(querystr))      # strip leading '?'
    if callb_path:
        path_parts = callb_path.split('/')
        callb_name = path_parts[-1]
        module_path = os.path.normpath('.'.join(path_parts[:-1]))
        if module_path.startswith('..'):
            raise ValueError(f'Invalid callback path "{callb_path}"')
        module_path = 'resources.lib.' + module_path
    else:
        callb_name = 'main_menu'
        module_path = 'resources.lib.menu'

    mod = importlib.import_module(module_path)
    callback = getattr(mod, callb_name)
    callb_type = getattr(callback, 'expose', None)
    if callb_type not in (CONTENT, RESOLVER, SCRIPT):
        log('Invalid route: "%s.%s"', module_path, callb_name)
        raise RuntimeError('Invalid route')
    if isinstance(callback, type):
        callback = callback()
    log("running '%s.%s'  with params %s.", module_path, callb_name, params)
    return callback, callb_type, params
