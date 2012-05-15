#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys,os,urllib,xbmcplugin,xbmcaddon

addonID = "plugin.video.mtv_de"
addon_work_folder=xbmc.translatePath("special://profile/addon_data/"+addonID)
blacklist=xbmc.translatePath("special://profile/addon_data/"+addonID+"/"+addonID+".blacklist")

if not os.path.isdir(addon_work_folder):
  os.mkdir(addon_work_folder)

param=urllib.unquote_plus(sys.argv[1])
playlistEntry=param[param.find("###URL###="):]

if os.path.exists(blacklist):
  fh = open(blacklist, 'r')
  content=fh.read()
  fh.close()
  if content.find(playlistEntry)==-1:
    fh=open(blacklist, 'a')
    fh.write(playlistEntry+"\n")
    fh.close()
else:
  fh=open(blacklist, 'a')
  fh.write(playlistEntry+"\n")
  fh.close()
xbmc.executebuiltin("Container.Refresh")