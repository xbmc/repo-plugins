# -*- coding: utf-8 -*-
import xbmc
from logging import Handler


# python log levels to kodis log levels
# everything is sent to notice except errors and warnings
py_to_kodi = {
    10: 2,
    20: 2,
    30: 3,
    40: 4,
    50: 5,
}


class KodiHandler(Handler):

    def emit(self, record):
        try:
            msg = self.format(record)
            xbmc.log(msg.decode('utf8'), py_to_kodi[record.levelno])
        except:
            self.handleError(record)
