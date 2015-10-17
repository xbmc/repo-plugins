'''
    qobuz.constants
    ~~~~~~~~~~~~~~~

    :part_of: xbmc-qobuz
    :copyright: (c) 2012 by Joachim Basmaison, Cyril Leclerc
    :license: GPLv3, see LICENSE for more details.
'''

__debugging__ = 0


class ModeEnum(object):
    VIEW = 0x1
    PLAY = 0x2
    SCAN = 0x3
    VIEW_BIG_DIR = 0x4

    @classmethod
    def to_s(cls, mode):
        if mode == cls.VIEW:
            return "view"
        elif mode == cls.PLAY:
            return "play"
        elif mode == cls.SCAN:
            return "scan"
        elif mode == cls.VIEW_BIG_DIR:
            return "view big dir"
        else:
            return "Unknow mode: " + str(mode)

Mode = ModeEnum
