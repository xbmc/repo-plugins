# -*- coding: utf-8 -*-
# TVS Player for Kodi — entry point (Kodi runs this file for every menu and action).
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources", "lib"))

from tvsplayer.plugin import run  # noqa: E402

run(sys.argv)
