# SPDX-License-Identifier: CC-BY-NC-SA-4.0

import os
import io
import time

from resources.lib.backtothefuture import unicode
from resources.lib.retroconfig import Config


class SessionHelper(object):
    __TimeOut = 1 * 60 * 60

    def __init__(self):
        # static only
        raise NotImplementedError()

    @staticmethod
    def create_session(logger=None):
        """ Creates a session file in the add-on data folder. This file indicates
        that we passed the channel selection screen. It's main purpose is to be
        able to distinguish between coming back to the channel selection screen
        (in which case a session file was present) or starting the add-on and
        getting to the channel screen. In the latter case we want to show some
        extra data.

        """

        if not SessionHelper.is_session_active() and logger:
            logger.debug("Creating session at '%s'", SessionHelper.__get_session_path())
        elif logger:
            logger.debug("Updating session at '%s'", SessionHelper.__get_session_path())

        if logger:
            with io.open(SessionHelper.__get_session_path(), mode='w', encoding='utf-8') as fd:
                fd.write(unicode(logger.minLogLevel))
        else:
            io.open(SessionHelper.__get_session_path(), 'w', encoding='utf-8').close()

    @staticmethod
    def clear_session(logger=None):
        """ Clears the active session indicator by deleting the file """

        if os.path.isfile(SessionHelper.__get_session_path()):
            if logger:
                logger.warning("Clearing session at '%s'", SessionHelper.__get_session_path())
            os.remove(SessionHelper.__get_session_path())
        elif logger:
            logger.debug("No session to clear")

        return

    @staticmethod
    def is_session_active(logger=None):
        """ Returns True if an active session file is found """

        if logger:
            logger.debug("Checking for active sessions (%.2f minutes / %.2f hours).", SessionHelper.__TimeOut / 60, SessionHelper.__TimeOut / 3600.0)

        if not os.path.isfile(SessionHelper.__get_session_path()):
            if logger:
                logger.debug("No active sessions found.")
            return False

        time_stamp = os.path.getmtime(SessionHelper.__get_session_path())
        now_stamp = time.time()
        modified_in_last_hours = (now_stamp - SessionHelper.__TimeOut) < time_stamp

        log_level = None
        # try to determine whether we have a new loglevel in this session, if so, we reset the session to get all
        # required debug data. But we can only do that with a logger.
        if logger:
            try:
                with io.open(SessionHelper.__get_session_path(), mode='r', encoding='utf-8') as fd:
                    log_level = fd.readline()

                if not log_level == "":
                    # logger.Trace("Found previous loglevel: %s vs current: %s", logLevel, logger.minLogLevel)
                    new_log_level_found = not logger.minLogLevel == int(log_level)
                else:
                    new_log_level_found = False
            except:
                logger.error("Error determining previous loglevel", exc_info=True)
                new_log_level_found = False
        else:
            new_log_level_found = False

        if logger and new_log_level_found:
            logger.debug("Found active session at '%s' with an old loglevel '%s' vs '%s', resetting session",
                         SessionHelper.__get_session_path(), log_level, logger.minLogLevel)
            modified_in_last_hours = False

        elif logger and modified_in_last_hours:
            logger.debug("Found active session at '%s' which was modified %.2f minutes (%.2f hours) ago",
                         SessionHelper.__get_session_path(), (now_stamp - time_stamp) / 60, (now_stamp - time_stamp) / 3600.0)

        elif logger:
            logger.debug("Found expired session at '%s' which was modified %.2f minutes (%.2f hours) ago",
                         SessionHelper.__get_session_path(), (now_stamp - time_stamp) / 60, (now_stamp - time_stamp) / 3600.0)

        return modified_in_last_hours

    @staticmethod
    def __get_session_path():
        """ Returns the session file path """

        return os.path.join(Config.profileDir, "xot.session.lock")
