# -*- coding: utf-8 -*-
# KodiAddon 
#
from resources.lib.scraper import myAddon
import re
import sys
import urlparse

params = dict(urlparse.parse_qsl(sys.argv[2].replace('?','')))
action = params.get('action')

if action == 'rm_db':
    from resources.lib.metahandler import MetaData
    MetaData().remove_database()
else:
    # Start of Module
    addonName = re.search('plugin\://plugin.video.(.+?)/',str(sys.argv[0])).group(1)
    ma = myAddon(addonName)
    ma.processAddonEvent()
