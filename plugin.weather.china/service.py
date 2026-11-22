# -*- coding: utf-8 -*-
"""Kodi service entry point for plugin.weather.china.

Keep this file minimal: the refresh loop lives in resources/lib/background.py.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "resources"))

from lib import background  # noqa: E402

if __name__ == "__main__":
    background.run()
