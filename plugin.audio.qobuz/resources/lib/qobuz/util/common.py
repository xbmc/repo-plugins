'''
    qobuz.util.common
    ~~~~~~~~~~~~~~~

    :part_of: xbmc-qobuz
    :copyright: (c) 2015 by Joachim Basmaison, Cyril Leclerc
    :license: GPLv3, see LICENSE for more details.
'''


def isEmpty(value):
    if value is None or value == '':
        return True
    return False
