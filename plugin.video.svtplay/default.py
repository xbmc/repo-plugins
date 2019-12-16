# -*- coding: utf-8 -*-
from __future__ import absolute_import,unicode_literals
from sys import argv
from resources.lib.svtplay import SvtPlay

# plugin setup
PLUGIN_HANDLE = int(argv[1])
PLUGIN_URL = argv[0]
PLUGIN_PARAMS = argv[2]

svt_play = SvtPlay(PLUGIN_HANDLE, PLUGIN_URL)
svt_play.run(PLUGIN_PARAMS)
