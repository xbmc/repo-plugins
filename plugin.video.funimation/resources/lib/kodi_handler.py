# -*- coding: utf-8 -*-
import xbmc
import logging


# python log levels to kodis log levels
# everything is sent to notice except errors and warnings
py_to_kodi = {
    logging.DEBUG:    2,
    logging.INFO:     2,
    logging.WARN:     3,
    logging.ERROR:    4,
    logging.CRITICAL: 5,
}


class KodiHandler(logging.Handler):

    def emit(self, record):
        try:
            msg = self.format(record)
            xbmc.log(msg, py_to_kodi[record.levelno])
        except:
            self.handleError(record)
