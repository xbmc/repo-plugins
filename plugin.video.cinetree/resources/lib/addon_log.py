
# ------------------------------------------------------------------------------
#  Copyright (c) 2022-2023 Dimitri Kroon.
#  This file is part of plugin.video.cinetree.
#  SPDX-License-Identifier: GPL-2.0-or-later.
#  See LICENSE.txt
# ------------------------------------------------------------------------------

import logging
from logging.handlers import RotatingFileHandler
import os
import xbmc

from codequick import Script
from codequick.support import addon_data, logger_id


kodi_lvl_map = {
    logging.NOTSET: xbmc.LOGDEBUG,
    logging.DEBUG: xbmc.LOGDEBUG,
    logging.INFO: xbmc.LOGINFO,
    logging.WARNING: xbmc.LOGWARNING,
    logging.ERROR: xbmc.LOGERROR,
    logging.CRITICAL: xbmc.LOGFATAL
}


class KodiLogHandler(logging.Handler):
    def __init__(self):
        super(KodiLogHandler, self).__init__()
        self.setFormatter(logging.Formatter("[%(name)s] [%(levelname)s] %(message)s"))

    def emit(self, record: logging.LogRecord) -> None:
        msg = self.format(record)
        # as per kodi requirements only log at debug level to kodi log
        xbmc.log(msg, xbmc.LOGDEBUG)


class CtFileHandler(RotatingFileHandler):
    def __init__(self):
        logfile = os.path.join(Script.get_info('profile'), logger_id + '.log')
        super(CtFileHandler, self).__init__(filename=logfile, mode='w', maxBytes=1000000, backupCount=2, encoding='utf8')
        self.setFormatter(logging.Formatter('%(asctime)s %(levelname)-8s [%(name)s]: %(message)s'))

    def __del__(self):
        self.close()


class DummyHandler(logging.Handler):
    def __init__(self):
        super(DummyHandler, self).__init__()
        super(DummyHandler, self).setLevel(100)

    def emit(self, record: logging.LogRecord) -> None:
        pass

    def setLevel(self, level) -> None:
        pass


def set_log_handler(handler_class):
    to_be_removed = []
    new_handler_present = False

    for handler in logger.handlers:
        # noinspection PyTypeHints
        if not isinstance(handler, handler_class):
            to_be_removed.append(handler)
        else:
            new_handler_present = True

    # write to the old log
    logger.info("Logging: change handler to: %s, to be removed: %s", handler_class.__name__,
                [type(h).__name__ for h in to_be_removed])

    for handler in to_be_removed:
        logger.removeHandler(handler)
        if isinstance(handler, logging.FileHandler):
            handler.close()

    if new_handler_present:
        logger.info("Logging: kept original handler")
    else:
        logger.addHandler(handler_class())
        # write to the new log
        logger.info("Logging: changed handler to: %s, removed: %s", handler_class.__name__,
                    [type(h).__name__ for h in to_be_removed])


logger = logging.getLogger(logger_id)
logger.propagate = False

# noinspection PyBroadException
try:
    handler_name = addon_data.getSettingString('log-handler').lower()
except:
    handler_name = 'kodi'

if 'kodi' in handler_name:
    logger.addHandler(KodiLogHandler())
elif 'file' in handler_name:
    logger.addHandler(CtFileHandler())
else:
    logger.addHandler(DummyHandler())

# noinspection PyBroadException
try:
    log_lvl_idx = addon_data.getSettingInt('log-level')
    log_lvl = (logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR)[log_lvl_idx]
except:
    logger.warning("setting 'log-level' not present in addon settings")
    log_lvl = logging.DEBUG

logger.setLevel(log_lvl)


def shutdown_log():
    logging.shutdown()
