#!/usr/bin/python

########################

import sys
import xbmcgui

from resources.lib.helper import *
from resources.lib.utils import *

########################


class Main:
    def __init__(self):
        self.action = False
        self.params = {}
        self._parse_argv()

        if self.action:
            self.getactions()
        else:
            DIALOG.ok(ADDON.getLocalizedString(32000), ADDON.getLocalizedString(32001))

    def _parse_argv(self):
        args = sys.argv

        for arg in args:
            if arg == ADDON_ID:
                continue
            if arg.startswith('action='):
                self.action = arg[7:].lower()
            else:
                try:
                    self.params[arg.split("=")[0].lower()] = "=".join(arg.split("=")[1:]).strip()
                except Exception:
                    self.params = {}

    def getactions(self):
        util = globals()[self.action]
        util(self.params)
