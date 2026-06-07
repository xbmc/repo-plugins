# ----------------------------------------------------------------------------------------------------------------------
#  Copyright (c) 2022-2025 Dimitri Kroon.
#  This file is part of plugin.video.viwx.
#  SPDX-License-Identifier: GPL-2.0-or-later
#  See LICENSE.txt
# ----------------------------------------------------------------------------------------------------------------------
from __future__ import annotations
import json
import logging

import xbmc
import xbmcgui

from codequick import Script, utils
from codequick.support import addon_data, logger_id

from . utils import addon_info, ZoneInfo

logger = logging.getLogger(logger_id + '.kodi_utils')


TXT_LOG_TARGETS = 30112
TXT_ITV_ACCOUNT = 30200

TXT_MORE_INFO = 30604

TXT_ACCOUNT_ERROR = 30610
MSG_LOGIN = 30611
MSG_LOGGED_OUT_SUCCESS = 30613

TXT_USERNAME = 30614
TXT_PASSWORD = 30615
TXT_TRY_AGAIN = 30618
TXT_RESUME_FROM = 30619
TXT_PLAY_FROM_START = 30620
TXT_LOGIN_NOW = 30621

BTN_TXT_OK = 30790
BTN_TXT_CANCEL = 30791


def ask_credentials(username: str | None = None, password: str | None = None):
    """Ask the user to enter his username and password.
    Return a tuple of (username, password). Each or both can be empty when the
    user has canceled the operation.

    The optional parameters `username` and `password` will be used as the
    default values for the on-screen keyboard.

    """
    new_username = utils.keyboard(Script.localize(TXT_USERNAME), username or '')
    if new_username:
        hide_characters = not addon_data.getSettingBool('show_password_chars')
        new_password = utils.keyboard(Script.localize(TXT_PASSWORD), password or '', hidden=hide_characters)
    else:
        new_password = ''
    return new_username, new_password


def show_msg_not_logged_in():
    """Show a message to inform the user is not logged in and
    ask whether to login now.

    """
    dlg = xbmcgui.Dialog()
    result = dlg.yesno(
            Script.localize(TXT_ACCOUNT_ERROR),
            Script.localize(MSG_LOGIN),
            nolabel=Script.localize(BTN_TXT_CANCEL),
            yeslabel=Script.localize(TXT_LOGIN_NOW))
    logger.debug("Dialog 'Open settings to login' result: {}".format('YES' if result else 'NO'))
    return result


def ask_login_retry(reason):
    """Show a message that login has failed and ask whether to try again."""

    msg = '\n\n'.join((reason, Script.localize(TXT_TRY_AGAIN)))

    dlg = xbmcgui.Dialog()

    return dlg.yesno(
            Script.localize(TXT_ACCOUNT_ERROR),
            msg,
            nolabel=Script.localize(BTN_TXT_CANCEL),
            yeslabel=Script.localize(BTN_TXT_OK))


def ask_log_handler(default):
    options = Script.localize(TXT_LOG_TARGETS).split(',')
    dlg = xbmcgui.Dialog()
    result = dlg.contextmenu(options)
    if result == -1:
        result = default
    try:
        return result, options[result]
    except IndexError:
        # default value is not necessarily a valid index.
        return result, ''


def ask_play_from_start(title=None):
    if not isinstance(title, (type(None), str)):
        logger.error("Invalid argument passed to ask_lay_from_start: '%s'", title)
        raise ValueError('Parameter title must be of type string')

    dlg = xbmcgui.Dialog()
    return dlg.yesno(
            title or addon_info.name,
            Script.localize(TXT_PLAY_FROM_START))


def msg_dlg(msg, title=None, **kwargs):
    if not isinstance(msg, (str, int)) or not isinstance(title, (type(None), str, int)):
        logger.error("Invalid argument passed to message dialog: '%s', '%s'", msg, title)
        raise ValueError('Arguments must be of type string or int')

    if isinstance(msg, int):
        msg = Script.localize(msg)
    if kwargs:
        msg = msg.format(**kwargs)

    if isinstance(title, int):
        title = Script.localize(title)

    dlg = xbmcgui.Dialog()
    if title is None:
        title = addon_info.name
    dlg.ok(title, msg)


def get_system_setting(setting_id):
    json_str = ('{{"jsonrpc": "2.0", "method": "Settings.GetSettingValue", "params": ["{}"], "id": 1}}'.
                format(setting_id))
    response = xbmc.executeJSONRPC(json_str)
    data = json.loads(response)
    try:
        return data['result']['value']
    except KeyError:
        msg = data.get('message') or "Failed to get setting"
        logger.error("get_system_setting failed for setting_id '%s': '%s'", setting_id, msg)
        raise ValueError('system setting error: {}'.format(msg))


_local_timezone = None


def local_timezone() -> ZoneInfo:
    global _local_timezone
    if not _local_timezone:
        try:
            _local_timezone = ZoneInfo(get_system_setting('locale.timezone'))
        except ValueError:
            # To be Matrix compatible
            from tzlocal import get_localzone
            _local_timezone = get_localzone()
    return _local_timezone
