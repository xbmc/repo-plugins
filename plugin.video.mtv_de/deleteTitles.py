#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys,os,urllib,xbmcplugin,xbmcaddon,xbmcgui

addonID = "plugin.video.mtv_de"
settings = xbmcaddon.Addon(id=addonID)
translation = settings.getLocalizedString
addon_work_folder=xbmc.translatePath("special://profile/addon_data/"+addonID)
titles=xbmc.translatePath("special://profile/addon_data/"+addonID+"/"+addonID+".titles")

dialog = xbmcgui.Dialog()
ok = dialog.ok('Info:', translation(30208))
if ok==True:
  fh=open(titles, 'w')
  fh.write("")
  fh.close()
  xbmc.executebuiltin("Container.Refresh")
