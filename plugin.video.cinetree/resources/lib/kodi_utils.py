
# ------------------------------------------------------------------------------
#  Copyright (c) 2022-2025 Dimitri Kroon.
#  This file is part of plugin.video.cinetree.
#  SPDX-License-Identifier: GPL-2.0-or-later.
#  See LICENSE.txt
# ------------------------------------------------------------------------------

import logging
import time
import sys
from collections.abc import Callable

import xbmcgui
from xbmc import Player, Monitor, executeJSONRPC


from codequick import Script, utils
from codequick.support import addon_data, logger_id, build_path

from resources.lib.ctree.ct_data import FilmItem


logger = logging.getLogger('.'.join((logger_id, __name__)))


TXT_LOG_TARGETS = 30112
TXT_CINETREE_ACCOUNT = 30200

TXT_RENTAL_FILM = 30601
MSG_CREDITS_LOW = 30602
TXT_MORE_INFO = 30604
MSG_MORE_PAYMENT_INFO = 30605
TXT_ACCOUNT_ERROR = 30610
MSG_LOGIN = 30611
MSG_LOGIN_SUCCESS = 30612
MSG_LOGGED_OUT_SUCCESS = 30613

TXT_USERNAME = 30614
TXT_PASSWORD = 30615
TXT_INVALID_USERNAME = 30616
TXT_INVALID_PASSWORD = 30617
TXT_TRY_AGAIN = 30618
TXT_RESUME_FROM = 30619
TXT_PLAY_FROM_START = 30620
TXT_LOGIN_NOW = 30621

TXT_RENT_NOW = 30622
MSG_RENT_NOW_CONFIRM = 30623
TXT_PAY = 30624

BTN_TXT_OK = 30790
BTN_TXT_CANCEL = 30791


class PlayTimeMonitor(Player):
    POLL_PERIOD = 4

    def __init__(self):
        super(PlayTimeMonitor, self).__init__()
        self.total_time = 0
        self._playtime = 0
        self.monitor = Monitor()
        self.is_playing = False

    @property
    def playtime(self):
        """Return the last known playtime"""
        if self._playtime and self.total_time:
            if 0 < self.total_time - self._playtime < self.POLL_PERIOD + 1:
                return self.total_time
        return self._playtime

    def onAVStarted(self) -> None:
        # noinspection PyBroadException
        try:
            self.total_time = self.getTotalTime()
            logger.debug("PlayTimeMonitor: total play time = %s", self.playtime/60)
        except:
            logger.warning("PlayTimeMonitor.onAVStarted: failed to get totalTime.", exc_info=True)
        # noinspection PyBroadException
        try:
            self._playtime = self.getTime()
        except:
            logger.warning("PlayTimeMonitor.onAVStarted: failed to get Time.", exc_info=True)
        self.is_playing = True

    def onPlayBackSeek(self, time: int, seekOffset: int) -> None:
        self._playtime = min(time / 1000, self.total_time)

    def wait_until_playing(self, timeout) -> bool:
        """Wait and return `True` when the player has started playing.
        Return `False` when `timeout` expires, or when playing has been aborted before
        the actual playing started.

        """
        end_t = time.monotonic() + timeout
        while not self.is_playing:
            if time.monotonic() >= end_t:
                return False
            if self.monitor.waitForAbort(0.2):
                logger.debug("wait_until_playing ended: abort requested")
                return False
        return True

    def wait_while_playing(self) -> None:
        """Wait while the player is playing and return when playing has stopped.
        Returns immediately if the player is not playing.
        """
        while not self.monitor.waitForAbort(self.POLL_PERIOD) and self.isPlaying():
            try:
                self._playtime = self.getTime()
            except RuntimeError:  # Player just stopped playing
                break


def ask_credentials(username: str = None, password: str = None):
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
    return result


def show_login_result(success: bool, message: str = None):
    if success:
        icon = Script.NOTIFY_INFO
        if not message:
            message = Script.localize(MSG_LOGIN_SUCCESS)
    else:
        icon = Script.NOTIFY_WARNING

    Script.notify(Script.localize(TXT_CINETREE_ACCOUNT), message, icon)


def ask_login_retry(reason):
    """Show a message that login has failed and ask whether to try again"""

    if reason.lower() == 'invalid username':
        reason = Script.localize(TXT_INVALID_USERNAME)
    elif reason.lower() == 'invalid password':
        reason = Script.localize(TXT_INVALID_PASSWORD)

    msg = '\n\n'.join((reason, Script.localize(TXT_TRY_AGAIN)))

    dlg = xbmcgui.Dialog()

    return dlg.yesno(
            Script.localize(TXT_ACCOUNT_ERROR),
            msg,
            nolabel=Script.localize(BTN_TXT_CANCEL),
            yeslabel=Script.localize(BTN_TXT_OK))


def show_low_credit_msg(price, credit):
    """Show a message with info regarding rental films

    Note that the NO-button acts as an OK button.
    """
    dlg_title = Script.localize(TXT_RENTAL_FILM)

    dlg = xbmcgui.Dialog()
    result = dlg.yesno(
            dlg_title,
            Script.localize(MSG_CREDITS_LOW).format(credit=credit, amount=price),
            nolabel=Script.localize(BTN_TXT_OK),
            yeslabel=Script.localize(TXT_MORE_INFO),
            autoclose=15000)

    if result:
        # Show a message with more detailed info on how to pay for a film.
        dlg.textviewer(dlg_title, Script.localize(MSG_MORE_PAYMENT_INFO))


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


def confirm_rent_from_credit(title, price, credit):
    msg_txt = Script.localize(MSG_RENT_NOW_CONFIRM).format(title=title, amount=price, credit=credit)
    dlg = xbmcgui.Dialog()
    result = dlg.yesno(Script.localize(TXT_RENT_NOW),
                       msg_txt,
                       Script.localize(BTN_TXT_CANCEL),
                       Script.localize(TXT_PAY))
    if not result:
        dlg.textviewer(Script.localize(TXT_RENTAL_FILM), Script.localize(MSG_MORE_PAYMENT_INFO))
    return result


def ok_dialog(msg, heading=None):
    if heading is None:
        heading = 'Cinetree'
    elif isinstance(heading, int):
        heading = Script.localize(heading)

    if isinstance(msg, int):
        msg = Script.localize(msg)
    xbmcgui.Dialog().ok(heading, msg)


def yes_no_dialog(msg, heading=None, autoclose=12000):
    if heading is None:
        heading = 'Cinetree'
    elif isinstance(heading, int):
        heading = Script.localize(heading)

    if isinstance(msg, int):
        msg = Script.localize(msg)
    return xbmcgui.Dialog().yesno(heading, msg, autoclose=autoclose)


def sync_play_state(callback: Callable, film_item: FilmItem):
    """Sync the play state of the film to the Kodi database."""
    params = film_item.data['params']
    full_url = build_path(callback, _title_=params['title'], **params)
    resume_point = film_item.playtime
    if resume_point > 0:
        json_str = '{"jsonrpc": "2.0", "method": "Files.SetFileDetails", "params": {"file":"%s", ' \
                   '"media": "video", "resume": {"position": %s, "total": %s}}, "id": 1}' % (
                   full_url, resume_point, film_item.duration)
    else:
        json_str = '{"jsonrpc": "2.0", "method": "Files.SetFileDetails", "params": {"file":"%s", ' \
                   '"media": "video", "playcount": 1, "resume": {"position": 0, "total": %s}}, "id": 1}' % (
                   full_url, film_item.duration)
    response = executeJSONRPC(json_str)
    logger.debug("sync_play_state of '%s' to %s of %s, JSONRPC response: %s",
                 params['title'], resume_point, film_item.duration, response)
