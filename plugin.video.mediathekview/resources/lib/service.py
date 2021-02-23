# -*- coding: utf-8 -*-
"""
The service module

Copyright 2017-2018, Leo Moll and Dominik Schlösser
SPDX-License-Identifier: MIT
"""

# -- Imports ------------------------------------------------
from __future__ import unicode_literals

from resources.lib.kodi.kodiaddon import KodiService
from resources.lib.monitorKodi import MonitorKodi

from resources.lib.notifierKodi import NotifierKodi
from resources.lib.updater import MediathekViewUpdater
import resources.lib.appContext as appContext

# -- Classes ------------------------------------------------


class MediathekViewService(KodiService):
    """ The main service class """

    def __init__(self):
        super(MediathekViewService, self).__init__()
        # self.set_topic('Service')
        self.logger = appContext.MVLOGGER.get_new_logger('MediathekViewService')
        self.settings = appContext.MVSETTINGS
        self.notifier = appContext.MVNOTIFIER
        self.monitor = MonitorKodi()
        appContext.initMonitor(self.monitor)
        self.updater = MediathekViewUpdater()
        self._lastDatabaseType = self.settings.getDatabaseType()

    def __del__(self):
        self.logger = None
        self.settings = None
        self.notifier = None
        self.monitor = None
        self.updater = None

    def init(self):
        """ Initialisation of the service """
        self.logger.debug('init')

    def run(self):
        """ Execution of the service """
        self.logger.debug('Service Startup...')
        # Wait for Kodi to retrieve network
        self.monitor.wait_for_abort(self.settings.getDelayStartupSec())
        # error counter to slow down
        self.errorCount = 0
        #
        while not self.monitor.abort_requested():
            # slow down in case of errors (+1 because 0 is unlimited!)
            delayInSec = (self.errorCount * 60) + 1
            self.monitor.wait_for_abort(delayInSec)
            if delayInSec > 1:
                self.logger.warn('Delayed service agent by {} sec due to error count {}', delayInSec, self.errorCount)
            #
            self.updater = MediathekViewUpdater()
            self.updater.init()
            #
            try:
                # we need this for database change and update variable cache
                if self._lastDatabaseType != self.settings.getDatabaseType():
                    self.logger.debug('database change from {} to {}', self._lastDatabaseType, self.settings.getDatabaseType())
                    self._lastDatabaseType = self.settings.getDatabaseType()
                    self.updater.database.get_status()

                self.updater.doUpdate()
                self.errorCount = 0
            except Exception as err:
                self.logger.error('MediathekViewUpdater {}', err)
                self.updater.exit()
                self.settings.setDatabaseStatus('UNINIT');
                self.errorCount = self.errorCount + 1
            #
            self.updater.exit()
            # Sleep/wait for abort for 60 seconds
            if self.monitor.wait_for_abort(appContext.MVSETTINGS.getUpdateCheckIntervel()):
                # Abort was requested while waiting. We should exit
                break
        self.logger.info('Shutting down Service')

    def exit(self):
        """ Shutdown of the service """
        self.logger.info('Exit Service')
        self.updater.exit()

