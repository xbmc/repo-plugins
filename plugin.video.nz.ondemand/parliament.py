# http://inthehouse.co.nz/

import os, sys, tools, xbmcaddon
from datetime import date
addon = xbmcaddon.Addon(id = sys.argv[0][9:-1])

def RESOLVE(channel, count):
 info = tools.defaultinfo(0)
 info["Title"] = 'Parliament TV (Live Stream)'
 info["Thumb"] = os.path.join(addon.getAddonInfo('path'), "resources/images/%s.png" % channel)
 info["Plot"] = "Parliament TV provides live broadcasts from the House of Representatives. Question time is replayed each day at 6pm and 10pm."
 info["Date"] = date.today().strftime("%d.%m.%Y")
 quality = '384'
 if addon.getSetting('%s_stream' % channel) == "Apple Quicktime":
  quality = '512'
 if addon.getSetting('%s_quality' % channel) == "Low":
  quality = '56'
 elif addon.getSetting('%s_quality' % channel) == "Medium":
  quality = '128'
 info["FileName"] = "%s%s" % ("mms://wms-parliament.harmonycdn.net/parlserv-house", quality)
 if addon.getSetting('%s_stream' % channel) == "Apple Quicktime":
  info["FileName"] = "%s%s%s" % ("rtsp://Qts1.ptv.parliament.nz/ptv-", quality, ".sdp")
 tools.addlistitem(int(sys.argv[1]), info, "resources/images/%s.jpg" % channel, 0, count)