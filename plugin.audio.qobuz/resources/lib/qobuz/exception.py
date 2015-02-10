#     Copyright 2011 Joachim Basmaison, Cyril Leclerc
#
#     This file is part of xbmc-qobuz.
#
#     xbmc-qobuz is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     xbmc-qobuz is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.   See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with xbmc-qobuz.   If not, see <http://www.gnu.org/licenses/>.
import pprint
import traceback


class QobuzXbmcError(Exception):

    def __init__(self, **ka):
#        exc_type, exc_value, exc_traceback = sys.exc_info()
        if not 'additional' in ka or ka['additional'] is None:
            ka['additional'] = ''
        if (not 'who' in ka) or (not 'what' in ka):
            raise Exception(
                'QobuzXbmcError', 'Missing constructor arguments (who|what)')
        nl = "\n"
        msg = "[QobuzXbmcError]" + nl
        msg += " - who        : " + pprint.pformat(ka['who']) + nl
        msg += " - what       : " + ka['what'] + nl
        msg += " - additional : " + repr(ka['additional']) + nl
#        msg += " - type       : " + self.exc_type + nl
#        msg += " - value      : " + self.exc_value + nl
        msg += " - Stack      : " + nl
        print msg
        print traceback.print_exc(10)
