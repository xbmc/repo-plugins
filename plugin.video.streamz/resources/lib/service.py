# -*- coding: utf-8 -*-
""" Background service code """

from __future__ import absolute_import, division, unicode_literals

import logging
from time import time

from xbmc import Monitor

from resources.lib import kodilogging, kodiutils
from resources.lib.modules.proxy import Proxy
from resources.lib.streamz.exceptions import NoLoginException

kodilogging.config()
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
            # Update every `update_interval` after the last update
            if kodiutils.get_setting_bool('metadata_update') and int(kodiutils.get_setting('metadata_last_updated', 0)) + self.update_interval < time():
                self._update_metadata()

            # Stop when abort requested
            if self.waitForAbort(60):
                break

        # Wait for the proxy thread to stop
        if self._proxy_thread and self._proxy_thread.is_alive():
            _LOGGER.debug('Stopping Manifest Proxy...')
            Proxy.stop()

        _LOGGER.debug('Service stopped')

    def _update_metadata(self):
        """ Update the metadata for the listings """
        from resources.lib.modules.metadata import Metadata

        # Clear outdated metadata
        kodiutils.invalidate_cache(self.cache_expiry)

        def update_status(_i, _total):
            """ Allow to cancel the background job """
            return self.abortRequested() or not kodiutils.get_setting_bool('metadata_update')

        try:
            success = Metadata().fetch_metadata(callback=update_status)
        except NoLoginException:
            # We have no login yet, but that's okay, we will retry later
            _LOGGER.debug('Skipping background updating since we have no credentials.')
            return

        except Exception as exc:  # pylint: disable=broad-except
            _LOGGER.debug('Skipping background updating since we got an error')
            _LOGGER.exception(exc)
            return

        # Update metadata_last_updated
        if success:
            kodiutils.set_setting('metadata_last_updated', str(int(time())))


def run():
    """ Run the BackgroundService """
    BackgroundService().run()
