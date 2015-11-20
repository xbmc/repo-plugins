# -*- coding: utf-8 -*-
import sys
import logging
import xbmcaddon
from resources.lib.kodi_handler import KodiHandler

addon = xbmcaddon.Addon()


def setup_logging():
    log_level = (int(addon.getSetting('loglvl')) + 1) * 10
    logger = logging.getLogger('funimation')
    logger.setLevel(log_level)
    formatter = logging.Formatter(
        '[{0}] %(funcName)s : %(message)s'.format(addon.getAddonInfo('id')))
    kh = KodiHandler()
    kh.setLevel(log_level)
    kh.setFormatter(formatter)
    logger.addHandler(kh)
    return logger


def main():
    log = setup_logging()
    log.debug('ARGV: %s', sys.argv)

    import resources.lib.nav as nav
    nav.list_menu()


if __name__ == '__main__':
    main()
