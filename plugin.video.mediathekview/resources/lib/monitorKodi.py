# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT
"""
The base logger module

Copyright 2020, Mediathekview.de
"""

from resources.lib.monitorInterface import MonitorInterface
import xbmc


class MonitorKodi(MonitorInterface):

    def __init__(self):
        self.xbmcMonitor = xbmc.Monitor()

    """ Returns True if abort has been requested. """

    def abort_requested(self):
        return self.xbmcMonitor.abortRequested()

    """
        True when abort have been requested, 
        False if a timeout is given and the operation times out.
    """

    def wait_for_abort(self, timeout=1):
        return self.xbmcMonitor.waitForAbort(timeout)

