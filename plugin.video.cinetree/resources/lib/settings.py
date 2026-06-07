
# ------------------------------------------------------------------------------
#  Copyright (c) 2022-2025 Dimitri Kroon.
#  This file is part of plugin.video.cinetree.
#  SPDX-License-Identifier: GPL-2.0-or-later.
#  See LICENSE.txt
# ------------------------------------------------------------------------------

import logging

import xbmc
import xbmcgui
import xbmcplugin
from codequick import Script
from codequick.support import addon_data, logger_id

from resources.lib.ctree import ct_account
from resources.lib.ctree import ct_api
from resources.lib import kodi_utils
from resources.lib import addon_log as ct_logging

logger = logging.getLogger('.'.join((logger_id, __name__)))


@Script.register()
def login(_):
    if ct_account.session().login():
        ct_api.favourites = None


@Script.register()
def logout(_):
    # just to provide a route for settings' log out
    if ct_account.session().log_out():
        Script.notify(Script.localize(kodi_utils.TXT_CINETREE_ACCOUNT),
                      Script.localize(kodi_utils.MSG_LOGGED_OUT_SUCCESS),
                      Script.NOTIFY_INFO)
        ct_api.favourites = None


@Script.register()
def change_logger(_):
    """Callback for settings->general->log_to.
    Let the user choose between logging to kodi log, to our own file, or no logging at all.

    """
    handlers = (ct_logging.KodiLogHandler, ct_logging.CtFileHandler, ct_logging.DummyHandler)

    try:
        curr_hndlr_idx = handlers.index(type(ct_logging.logger.handlers[0]))
    except (ValueError, IndexError):
        curr_hndlr_idx = 0

    new_hndlr_idx, handler_name = kodi_utils.ask_log_handler(curr_hndlr_idx)
    handler_type = handlers[new_hndlr_idx]

    ct_logging.set_log_handler(handler_type)
    addon_data.setSettingString('log-handler', handler_name)


@Script.register()
def genre_sort_method(_):
    """Change the settings for genre sorting.

    Handler for the context menu item 'Sort by' on items in genre listings.

    Offer a context menu where the user can select from several sort methods
    and sort directions, and set the addon's settings accordingly.

    """
    ASCENDING = 0
    DESCENDING = 1
    TXT_ASC = Script.localize(584)
    TXT_DESC = Script.localize(585)
    sort_methods = [
        (Script.localize(571), xbmcplugin.SORT_METHOD_UNSORTED, ASCENDING),
        (' - '.join((Script.localize(556), TXT_ASC)), xbmcplugin.SORT_METHOD_TITLE, ASCENDING),
        (' - '.join((Script.localize(556), TXT_DESC)), xbmcplugin.SORT_METHOD_TITLE, DESCENDING),
        (' - '.join((Script.localize(570), TXT_ASC)), xbmcplugin.SORT_METHOD_DATEADDED, ASCENDING),
        (' - '.join((Script.localize(570), TXT_DESC)), xbmcplugin.SORT_METHOD_DATEADDED, DESCENDING),
        (' - '.join((Script.localize(180), TXT_ASC)), xbmcplugin.SORT_METHOD_DURATION, ASCENDING),
        (' - '.join((Script.localize(180), TXT_DESC)), xbmcplugin.SORT_METHOD_DURATION, DESCENDING),
        (' - '.join((Script.localize(562), TXT_ASC)), xbmcplugin.SORT_METHOD_VIDEO_YEAR, ASCENDING),
        (' - '.join((Script.localize(562), TXT_DESC)), xbmcplugin.SORT_METHOD_VIDEO_YEAR, DESCENDING)
    ]
    dlg = xbmcgui.Dialog()
    result = dlg.contextmenu([m[0] for m in sort_methods])
    if result < 0:
        return
    addon_data.setSettingInt('genre-sort-method', sort_methods[result][1])
    addon_data.setSettingInt('genre-sort-order', sort_methods[result][2])
    xbmc.executebuiltin('Container.Refresh')
