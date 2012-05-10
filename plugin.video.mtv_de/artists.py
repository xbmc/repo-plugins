#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys,os,urllib,xbmcplugin,xbmcaddon

addonID = "plugin.video.mtv_de"
addon_work_folder=xbmc.translatePath("special://profile/addon_data/"+addonID)
artists=xbmc.translatePath("special://profile/addon_data/"+addonID+"/"+addonID+".artists")

if not os.path.isdir(addon_work_folder):
  os.mkdir(addon_work_folder)

artistEntrys=urllib.unquote_plus(sys.argv[1])

fh=open(artists, 'a')
spl=artistEntrys.split("###URL###=")
for i in range(1,len(spl),1):
  fh.write("###URL###="+spl[i]+"\n")
fh.close()
