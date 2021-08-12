# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, unicode_literals

import logging
from time import time, sleep

from xbmc import Monitor
from yelo_api import YeloApi
from kodiwrapper import KodiWrapper
from helpers.helperclasses import EPG, PluginCache

_LOGGER = logging.getLogger('plugin')


class BackgroundService(Monitor):
    def __init__(self):
        Monitor.__init__(self)
        self.update_interval = 24 * 3600

    def run(self):
        _LOGGER.debug('Service started')

        while not self.abortRequested():
            # Update every `update_interval` after the last update
            if EPG().is_enabled and int(KodiWrapper.get_setting('metadata_last_updated', 0)) \
                    + self.update_interval < time():
                self.cache_channel_epg()

            # Stop when abort requested
            if self.waitForAbort(10):
                break

        _LOGGER.debug('Service stopped')

    @classmethod
    def cache_channel_epg(cls):
        if PluginCache.key_exists("entitlements"):
            _LOGGER.debug('Caching channels..')

            channels = YeloApi.get_channels()

            epg = YeloApi.get_epg(channels)
            EPG.to_cache(epg)

            KodiWrapper.set_setting('metadata_last_updated', str(int(time())))

            sleep(1)
            KodiWrapper.container_refresh()


def refresh_epg():
    KodiWrapper.dialog_ok(KodiWrapper.get_localized_string(40001),
                          KodiWrapper.get_localized_string(40003))
    BackgroundService.cache_channel_epg()
    KodiWrapper.dialog_ok(KodiWrapper.get_localized_string(40001),
                          KodiWrapper.get_localized_string(40002))


def run():
    """ Run the BackgroundService """
    BackgroundService().run()


if __name__ == "__main__":
    run()
