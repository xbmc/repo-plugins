# -*- coding: utf-8 -*-
"""

    Copyright (C) 2013-2019 PleXBMC Helper (script.plexbmc.helper)
        by wickning1 (aka Nick Wing), hippojay (Dave Hawes-Johnson)
    Copyright (C) 2019-2020 Composite (plugin.video.composite_for_plex)

    This file is part of Composite (plugin.video.composite_for_plex)

    SPDX-License-Identifier: GPL-2.0-or-later
    See LICENSES/GPL-2.0-or-later.txt for more information.
"""

import socket
import threading
import traceback
from functools import partial

from kodi_six import xbmc  # pylint: disable=import-error
from kodi_six import xbmcgui  # pylint: disable=import-error

from ..addon.constants import CONFIG
from ..addon.logger import Logger
from ..addon.strings import i18n
from .http_persist import RequestManager
from .listener import PlexCompanionHandler
from .listener import ThreadedHTTPServer
from .subscribers import SubscriptionManager


class CompanionReceiverThread(threading.Thread):
    LOG = Logger('CompanionReceiverThread')
    MONITOR = xbmc.Monitor()

    def __init__(self, gdm_client, settings):
        super(CompanionReceiverThread, self).__init__()  # pylint: disable=super-with-arguments
        self._stopped = threading.Event()
        self._ended = threading.Event()
        self._dialog = xbmcgui.Dialog()

        self.settings = settings
        self.client = gdm_client
        self.client_details = self.settings.companion_receiver()
        self.httpd = None
        self.request_manager = None
        self.subscription_manager = None
        self.daemon = True
        self.start()

    def stop(self):
        self.LOG.debug('Stop event set...')
        self._stopped.set()

    def stopped(self):
        return self._stopped.is_set()

    def end(self):
        self.LOG.debug('End event set...')
        self._ended.set()

    def ended(self):
        return self._ended.is_set()

    def _get_httpd(self):
        self.httpd = ThreadedHTTPServer(self.client, self.subscription_manager,
                                        ('', self.client_details['port']),
                                        partial(PlexCompanionHandler, self.settings))
        self.httpd.timeout = 0.95

    def run(self):
        count = 0
        self.request_manager = RequestManager()
        self.subscription_manager = SubscriptionManager(self.settings, self.request_manager)

        while not self.MONITOR.abortRequested():
            try:
                self._get_httpd()
                break
            except:  # pylint: disable=bare-except
                self.LOG.debug('Unable to start receiver. Sleep and Retry...')
                self.settings.set_replacement(True)

            self.MONITOR.waitForAbort(3)

            if count == 3:
                self.LOG.debug('Unable to start web receiver. Giving up.')
                self._dialog.notification(CONFIG['name'],
                                          i18n('Companion receiver is unable to start '
                                               'due to a port conflict'),
                                          CONFIG['icon'], sound=False)
                self.httpd = None
                break

            count += 1

        if self.httpd:
            self.client.start_all()
            self.settings.set_replacement(False)

            count = 0
            running = False

            while (not xbmc.Monitor().abortRequested() and
                   not self.settings.replacement() and
                   not self.stopped()):
                try:

                    self.httpd.handle_request()
                    count += 1

                    if count > 30:
                        if self.client.check_client_registration():
                            self.LOG.debug('Client is still registered')
                        else:
                            self.LOG.debug('Client is no longer registered')
                        self.LOG.debug('Receiver still running on port %s' %
                                       self.client_details['port'])
                        count = 0

                    if not running:
                        self.LOG.debug('Receiver has started')
                        self._dialog.notification(CONFIG['name'],
                                                  i18n('Companion receiver has started'),
                                                  CONFIG['icon'], sound=False)

                    running = True
                    if count % 1 == 0:
                        self.subscription_manager.notify()
                    self.subscription_manager.server_list = self.client.get_server_list()
                except:  # pylint: disable=bare-except
                    self.LOG.debug('Error in loop, continuing anyway')
                    self.LOG.debug(traceback.print_exc())

            self._shutdown()

    def _shutdown(self):
        try:
            self.httpd.socket.shutdown(socket.SHUT_RDWR)
        except:  # pylint: disable=bare-except
            pass
        finally:
            self.httpd.socket.close()

        self.request_manager.dump_connections()
        self.client.stop_all()
        self.end()
        self.LOG.debug('Receiver has been stopped')
        self._dialog.notification(CONFIG['name'], i18n('Companion receiver has been stopped'),
                                  CONFIG['icon'], sound=False)


def shutdown(companion_thread):
    if companion_thread:
        companion_thread.stop()
        companion_thread.join()
