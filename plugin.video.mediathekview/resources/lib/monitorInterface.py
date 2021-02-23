# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT
"""
The base logger module

Copyright 2020, Mediathekview.de
"""
import time


class MonitorInterface(object):

    def abort_requested(self):
        return False

    def wait_for_abort(self, timeout=1):
        time.sleep(timeout)
        return False
