
# ----------------------------------------------------------------------------------------------------------------------
#  Copyright (c) 2022-2025 Dimitri Kroon.
#  This file is part of plugin.video.viwx.
#  SPDX-License-Identifier: GPL-2.0-or-later
#  See LICENSE.txt
# ----------------------------------------------------------------------------------------------------------------------

import logging
import json

import xbmcgui
import xbmcvfs
from codequick import Script
from codequick.support import addon_data, logger_id

from resources.lib import itv_account
from resources.lib import kodi_utils
from resources.lib import addon_log
from resources.lib import errors

logger = logging.getLogger('.'.join((logger_id, __name__)))

TXT_LOGIN_SUCCESS = 30612
TXT_EXPORT_NOT_SINGED_IN = 30623
TXT_EXPORT_SUCCESS = 30624
TXT_EXPORT_FAIL = 30625
TXT_IMPORT_SUCCESS = 30626
TXT_IMPORT_INVALID_DATA = 30627
TXT_IMPORT_FAILED_REFRESH = 30268


@Script.register()
def login(_=None):
    """Ask the user to enter credentials and try to sign in to ITVX.

    On failure ask to retry and continue to do so until signin succeeds,
    or the user selects cancel.
    """
    uname = None
    passw = None

    logger.debug("Starting Login...")
    while True:
        uname, passw = kodi_utils.ask_credentials(uname, passw)
        if not all((uname, passw)):
            logger.info("Entering login credentials canceled by user")
            return
        try:
            session = itv_account.itv_session()
            session.login(uname, passw)
            kodi_utils.msg_dlg(TXT_LOGIN_SUCCESS, nickname=session.user_nickname)
            from resources.lib import cache
            import xbmc
            cache.my_list_programmes = None
            xbmc.executebuiltin('Container.Refresh')
            return
        except errors.AuthenticationError as e:
            if not kodi_utils.ask_login_retry(str(e)):
                logger.info("Login retry canceled by user")
                return


@Script.register()
def logout(_):
    # just to provide a route for settings' log out
    if itv_account.itv_session().log_out():
        Script.notify(Script.localize(kodi_utils.TXT_ITV_ACCOUNT),
                      Script.localize(kodi_utils.MSG_LOGGED_OUT_SUCCESS),
                      Script.NOTIFY_INFO)
        from resources.lib import cache
        import xbmc
        cache.my_list_programmes = False
        xbmc.executebuiltin('Container.Refresh')


@Script.register()
def import_tokens(_):
    """Import authentication tokens from a web browser or an existing viwx session file.

    """
    file_path = xbmcgui.Dialog().browseSingle(1, 'Open token file', 'files')
    if not file_path:
        logger.info("Importing auth tokens canceled.")
        return

    logger.info("Importing auth tokens from %s.", file_path)
    with xbmcvfs.File(file_path, 'r') as f:
        raw_data = f.read()
    check_token_data(raw_data)


def check_token_data(raw_data: str):
    data_type = "Unknown"
    data = raw_data.strip()
    # Just in case some editor has inserted hard wraps.
    data = data.replace('\n', '')
    data = data.replace('\r', '')
    try:
        if '.Session:"{' in data[:16]:
            data_type = "Firefox cookie"
            if not data.startswith('Itv'):
                raise errors.ParseError("Firefox cookie data should start with 'ITV.Session'.")
            if not data.endswith('"'):
                raise errors.ParseError('Firefox cookie data should end with a double quote (").')
            token_data = _parse_cookie(data[13:-1])
        elif 'tokens":' in data[:11]:
            data_type = "Chromium cookie"
            if not data.startswith('{'):
                raise errors.ParseError("Chromium cookie data should start with a '{'.")
            if not data.endswith('}'):
                raise errors.ParseError("Chromium cookie data should end with a '}'.")
            token_data = _parse_cookie(data)
        elif '"vers": 2' in data:
            data_type = "viwX export"
            try:
                token_data = json.loads(data)['itv_session']
            except (json.JSONDecodeError, KeyError):
                raise errors.ParseError("This is not a valid viwX token export file.")
        else:
            raise errors.ParseError("Unknown file format.\n"
                                    "Ensure to copy all data exactly as is.")
    except errors.ParseError as err:
        logger.error("Invalid token data\n\t\tFile format: %s\n\t\tstart: '%s'\n\t\tend: '%s'\n",
                     data_type, raw_data[:20], raw_data[-20:], exc_info=True)
        kodi_utils.msg_dlg('\n'.join((Script.localize(TXT_IMPORT_INVALID_DATA), str(err))))
        return

    try:
        # Just to check its presence
        _ = token_data['refresh_token']
    except KeyError:
        logger.error("Failed to import' refresh token not present.")
        kodi_utils.msg_dlg('\n'.join((
            Script.localize(TXT_IMPORT_INVALID_DATA),
            "Missing token.Are you sure you were signed in when copying the cookie?"))
        )
        return

    logger.debug('Successfully read auth tokens file.')
    session = itv_account.itv_session()
    session.account_data['itv_session'] = token_data
    session.account_data['cookies'] = {}
    if session.refresh():
        kodi_utils.msg_dlg(TXT_IMPORT_SUCCESS, nickname=session.user_nickname)
    else:
        kodi_utils.msg_dlg(TXT_IMPORT_FAILED_REFRESH)


def _parse_cookie(data: str) -> dict:
    """Read tokens from cookie data and try to show an informative message on failure."""
    try:
        tokens = json.loads(data)['tokens']['content']
        return tokens
    except (json.JSONDecodeError, TypeError):
        logger.error("Error importing tokens from cookie:\n", exc_info=True)
        raise errors.ParseError('Invalid, or a incomplete authentication cookie.')
    except KeyError:
        logger.error("Error importing tokens from cookie:\n", exc_info=True)
        raise errors.ParseError('The cookie data is invalid, or incomplete.\n'
                                'Are you sure you were signed in when copying the cookie?')


@Script.register()
def export_tokens(_):
    import datetime
    import os
    from resources.lib import utils

    # Check if a user is logged in
    user_id = itv_account.itv_session().user_id
    if not user_id:
        logger.info("Nothing to export, user_id = '%s'.", user_id)
        kodi_utils.msg_dlg(TXT_EXPORT_NOT_SINGED_IN)
        return

    session_file = os.path.join(utils.addon_info.profile, "itv_session")
    dest_dir = xbmcgui.Dialog().browseSingle(0, 'Choose directory', 'files')
    if not dest_dir:
        return
    filename = datetime.datetime.now().strftime('viwx_tokens_%Y-%m-%d_%H-%M-%S.txt')
    logger.info("Selected destination directory: %s", dest_dir)
    sep = '' if dest_dir[-1] in ('/', '\\') else '/'
    dest_path = sep.join((dest_dir, filename))
    logger.info("Exporting session data to '%s'.", dest_path)
    xbmcvfs.copy(session_file, dest_path)

    # Both copy() and File.write() return True when writing to an un-writable destination
    # Check if the file exists to ensure copy succeeded.
    if xbmcvfs.exists(dest_path):
        kodi_utils.msg_dlg(TXT_EXPORT_SUCCESS, file_path=dest_path)
    else:
        kodi_utils.msg_dlg(TXT_EXPORT_FAIL)
    return


@Script.register()
def change_logger(_):
    """Callback for settings->generic->log_to.
    Let the user choose between logging to kodi log, to our own file, or no logging at all.

    """
    handlers = (addon_log.KodiLogHandler, addon_log.CtFileHandler, addon_log.DummyHandler)

    try:
        curr_hndlr_idx = handlers.index(type(addon_log.logger.handlers[0]))
    except (ValueError, IndexError):
        curr_hndlr_idx = 0

    new_hndlr_idx, handler_name = kodi_utils.ask_log_handler(curr_hndlr_idx)
    handler_type = handlers[new_hndlr_idx]

    addon_log.set_log_handler(handler_type)
    addon_data.setSettingString('log-handler', handler_name)
