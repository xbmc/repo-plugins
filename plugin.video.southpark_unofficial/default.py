#!/usr/bin/python
# -*- coding: utf-8 -*-
import socket
import sys
import southpark

socket.setdefaulttimeout(30)
plugin = southpark.SouthParkAddon(argv=sys.argv, last_season=23)
plugin.handle()
plugin = None
