#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys,os,re,urllib,xbmcplugin,xbmcaddon,xbmcgui

addonID = "plugin.video.vidstatsx_com"
addon_work_folder=xbmc.translatePath("special://profile/addon_data/"+addonID)
channelFavsFile=xbmc.translatePath("special://profile/addon_data/"+addonID+"/"+addonID+".favorites")

if not os.path.isdir(addon_work_folder):
  os.mkdir(addon_work_folder)

param=urllib.unquote_plus(sys.argv[1])
mode=param[param.find("###MODE###=")+11:]
mode=mode[:mode.find("###")]
channelEntry=param[param.find("###USER###="):]

if mode=="ADD":
  if os.path.exists(channelFavsFile):
    fh = open(channelFavsFile, 'r')
    content=fh.read()
    fh.close()
    if content.find(channelEntry)==-1:
      fh=open(channelFavsFile, 'a')
      fh.write(channelEntry+"\n")
      fh.close()
  else:
    fh=open(channelFavsFile, 'a')
    fh.write(channelEntry+"\n")
    fh.close()
elif mode=="REMOVE":
  refresh=param[param.find("###REFRESH###=")+14:]
  refresh=refresh[:refresh.find("###USER###=")]
  fh = open(channelFavsFile, 'r')
  content=fh.read()
  fh.close()
  entry=content[content.find(channelEntry):]
  fh=open(channelFavsFile, 'w')
  fh.write(content.replace(channelEntry+"\n",""))
  fh.close()
  if refresh=="TRUE":
    xbmc.executebuiltin("Container.Refresh")
