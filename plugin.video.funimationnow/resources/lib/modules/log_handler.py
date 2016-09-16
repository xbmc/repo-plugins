# -*- coding: utf-8 -*-

'''
    Funimation|Now Add-on
    Copyright (C) 2016 Funimation|Now

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''


import xbmc;
import logging;


# python log levels to kodis log levels
# everything is sent to notice except errors and warnings

py_to_kodi = {
    logging.DEBUG:    2,
    logging.INFO:     2,
    logging.WARN:     3,
    logging.ERROR:    4,
    logging.CRITICAL: 5,
}


class LogHandler(logging.Handler):

    def emit(self, record):

        try:

            msg = self.format(record);
            xbmc.log(msg, py_to_kodi[record.levelno]);

        except:
            self.handleError(record);
