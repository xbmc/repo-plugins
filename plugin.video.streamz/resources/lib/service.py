# -*- coding: utf-8 -*-
""" Background service code """

from __future__ import absolute_import, division, unicode_literals

import logging

from xbmc import Monitor

from resources.lib import kodilogging, kodiutils
from resources.lib.modules.proxy import Proxy

_LOGGER = logging.getLogger(__name__)


class BackgroundService(Monitor):
    """ Background service code """

    def __init__(self):
        Monitor.__init__(self)
        self._proxy_thread = None
        self.update_interval = 24 * 3600  # Every 24 hours
        self.cache_expiry = 30 * 24 * 3600  # One month

    def run(self):
        """ Background loop for maintenance tasks """
        _LOGGER.debug('Service started')

        kodiutils.set_setting('manifest_proxy_port', None)
        if kodiutils.get_setting_bool('manifest_proxy'):
            _LOGGER.debug('Starting Manifest Proxy...')
            self._proxy_thread = Proxy.start()

        while not self.abortRequested():
            # Stop when abort requested
            if self.waitForAbort(60):
                break

        # Wait for the proxy thread to stop
        if self._proxy_thread and self._proxy_thread.is_alive():
            _LOGGER.debug('Stopping Manifest Proxy...')
            Proxy.stop()

        _LOGGER.debug('Service stopped')


def run():
    """ Run the BackgroundService """
    kodilogging.config()
    BackgroundService().run()
