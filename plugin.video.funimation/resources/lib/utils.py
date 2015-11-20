# -*- coding: utf-8 -*-
import sys
import logging
import xbmc
import xbmcaddon
from urllib import urlencode
from urlparse import parse_qsl

__all__ = ['show_message', 'show_error_message', 'get_string',
           'get_user_input', 'build_url', 'get_params']

STRINGMAP = {
    'browse_shows': 30010,
    'browse_latest': 30011,
    'browse_simulcasts': 30012,
    'browse_featured': 30013,
    'browse_genre': 30014,
    'browse_alpha': 30015,
    'search': 30016,

    # messages
    'error':            30600,
    'unknown_error':    30601,
    'no_results':       30603,
}

_log = logging.getLogger('funimation')


def show_message(msg, title=None, icon=None):
    addon = xbmcaddon.Addon()
    if title is None:
        title = addon.getAddonInfo('name')
    if icon is None:
        icon = addon.getAddonInfo('icon')

    xbmc.executebuiltin(
        'Notification({title}, {msg}, 3000, {icon})'.format(**locals()))


def show_error_message(result=None, title=None):
    if title is None:
        title = get_string('error')
    if result is None:
        result = get_string('unknown_error')
    show_message(result, title)


def get_string(string_key):
    if string_key in STRINGMAP:
        string_id = STRINGMAP[string_key]
        string = xbmcaddon.Addon().getLocalizedString(string_id).encode('utf8')
        _log.debug('"%s" translates to "%s"', string_id, string)
        return string
    else:
        _log.debug('String is missing: "%s"', string_key)
        return string_key


def get_user_input(title, default=None, hidden=False):
    if default is None:
        default = u''

    result = None
    keyboard = xbmc.Keyboard(default, title)
    keyboard.setHiddenInput(hidden)
    keyboard.doModal()

    if keyboard.isConfirmed():
        result = keyboard.getText()

    return result


def build_url(d):
    return sys.argv[0] + '?' + urlencode(d)


def get_params():
    return dict(parse_qsl(sys.argv[2][1:]))
