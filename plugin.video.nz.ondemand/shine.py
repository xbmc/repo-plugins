import os, sys, tools, xbmcaddon
from datetime import date
addon = xbmcaddon.Addon(id = sys.argv[0][9:-1])

def RESOLVE(channel, count):
 info = tools.defaultinfo(0)
 info["Title"] = 'Shine TV (Live Stream)'
 info["Thumb"] = os.path.join(addon.getAddonInfo('path'), "resources/images/%s.png" % channel)
 info["Plot"] = "Shine TV is a television network of the Rhema Broadcasting Group Inc - New Zealand's largest Christian media organisation. On-air since December 2002, Shine broadcasts 24 hours nationwide on the SKY digital and Freeview Satellite platforms, with regional channels in Canterbury, Nelson and Wellington."
 info["Date"] = date.today().strftime("%d.%m.%Y")
 quality = 'fast'
 if addon.getSetting('%s_quality' % channel) == "Low":
  quality = 'mobile'
 elif addon.getSetting('%s_quality' % channel) == "Medium":
  quality = 'slow'
 info["FileName"] = "%s%s" % ("mms://wnss1.streaming.net.nz/rbg-shinetv-", quality)
 tools.addlistitem(int(sys.argv[1]), info, "resources/images/%s.jpg" % channel, 0, count)