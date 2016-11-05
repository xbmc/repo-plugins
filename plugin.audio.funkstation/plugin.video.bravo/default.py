# -*- coding: utf-8 -*-
# KodiAddon (Bravo TV)
#
from resources.lib.scraper import myAddon
import re
import sys

# Start of Module

addonName = re.search('plugin\://plugin.video.(.+?)/',str(sys.argv[0])).group(1)
ma = myAddon(addonName)
ma.processAddonEvent()

