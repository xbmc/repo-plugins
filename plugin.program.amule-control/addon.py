"""
    Plugin for Launching programs
"""

# -*- coding: UTF-8 -*-
# main imports
import sys
import os
import xbmc
import xbmcgui
import xbmcaddon

# plugin constants
__plugin__ = "amule-control"
__author__ = "RPiola"
__url__ = "http://pi.ilpiola.it/amulecontrol/"
__git_url__ = ""
__credits__ = "aMule"
__version__ = "1.1.1"

running = os.popen("pgrep -c amuled").read()
dialog = xbmcgui.Dialog()
addon = xbmcaddon.Addon(id='plugin.program.amule-control')
tostart = False
tostop = False
if running == "0\n":
  installed = os.popen("ls -l /etc/init.d/amule-daemon 2>/dev/null | wc -l").read()
  if installed == "0\n":
    dialog.ok(addon.getLocalizedString(id=30000 ), addon.getLocalizedString(id=30028),addon.getLocalizedString(id=30029))
  else:
    tostart = dialog.yesno(addon.getLocalizedString(id=30000 ), addon.getLocalizedString(id=30020 ), '',addon.getLocalizedString(id=30022 ),addon.getLocalizedString(id=30024 ),addon.getLocalizedString(id=30025))
else:
  tostop = dialog.yesno(addon.getLocalizedString(id=30000 ), addon.getLocalizedString(id=30021 ), '',addon.getLocalizedString(id=30023 ),addon.getLocalizedString(id=30024 ),addon.getLocalizedString(id=30025))
  if (not tostop):
    title="amulecmd -P \"******\" -c \"statistics\""
    cmd="amulecmd -P \"" + addon.getSetting("password") + "\" -c \"statistics\" | egrep \"(Uploaded|Downloaded) Data\" | cut -c7-"
    stream=os.popen(cmd)
    line1=''
    line2=''
    line1=stream.readline()
    line2=stream.readline()
    if((line1=='') and (line2=='')):
      dialog.ok(title,addon.getLocalizedString(id=30030),addon.getLocalizedString(id=30031),addon.getLocalizedString(id=30032))
    else:
      dialog.ok(title,line1,line2)
if (tostart):
  output=os.popen("sudo /etc/init.d/amule-daemon start").read()
  dialog.ok(addon.getLocalizedString(id=30026 ),output)
  print output
if (tostop):
  output=os.popen("sudo /etc/init.d/amule-daemon stop").read()
  dialog.ok(addon.getLocalizedString(id=30027 ),output)
  print output
