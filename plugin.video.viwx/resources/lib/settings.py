
# ----------------------------------------------------------------------------------------------------------------------
#  Copyright (c) 2022-2023 Dimitri Kroon.
#  This file is part of plugin.video.viwx.
#  SPDX-License-Identifier: GPL-2.0-or-later
#  See LICENSE.txt
# ----------------------------------------------------------------------------------------------------------------------

import logging

from codequick import Script
from codequick.support import addon_data, logger_id

from resources.lib import itv_account
from resources.lib import kodi_utils
from resources.lib import addon_log
from resources.lib import errors

logger = logging.getLogger('.'.join((logger_id, __name__)))


@Script.register()
def login(_=None):
    """Ask the user to enter credentials and try to sign in to ITVX.

    On failure ask to retry and continue to do so until signin succeeds,
    or the user selects cancel.
    """
    uname = None
    passw = None

    while True:
        uname, passw = kodi_utils.ask_credentials(uname, passw)
        if not all((uname, passw)):
            logger.info("Entering login credentials canceled by user")
            return
        try:
            itv_account.itv_session().login(uname, passw)
            kodi_utils.show_login_result(success=True)
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
