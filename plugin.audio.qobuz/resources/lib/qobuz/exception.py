'''
    qobuz.exception
    ~~~~~~~~~~~~~~~

    :part_of: xbmc-qobuz
    :copyright: (c) 2012 by Joachim Basmaison, Cyril Leclerc
    :license: GPLv3, see LICENSE for more details.
'''
import pprint
import traceback


class QobuzXbmcError(Exception):

    def __init__(self, **ka):
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
