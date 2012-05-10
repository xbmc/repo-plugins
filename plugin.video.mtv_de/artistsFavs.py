#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys,os,re,urllib,xbmcplugin,xbmcaddon,xbmcgui

addonID = "plugin.video.mtv_de"
addon_work_folder=xbmc.translatePath("special://profile/addon_data/"+addonID)
artistsFavsFile=xbmc.translatePath("special://profile/addon_data/"+addonID+"/"+addonID+".artistsFavs")

if not os.path.isdir(addon_work_folder):
  os.mkdir(addon_work_folder)

param=urllib.unquote_plus(sys.argv[1])
mode=param[param.find("###MODE###=")+11:]
mode=mode[:mode.find("###")]
playlistEntry=param[param.find("###URL###="):]

if mode=="ADD":
  if os.path.exists(artistsFavsFile):
    fh = open(artistsFavsFile, 'r')
    content=fh.read()
    fh.close()
    if content.find(playlistEntry)==-1:
      fh=open(artistsFavsFile, 'a')
      fh.write(playlistEntry+"\n")
      fh.close()
  else:
    fh=open(artistsFavsFile, 'a')
    fh.write(playlistEntry+"\n")
    fh.close()
elif mode=="REMOVE":
  refresh=param[param.find("###REFRESH###=")+14:]
  refresh=refresh[:refresh.find("###URL###=")]
  fh = open(artistsFavsFile, 'r')
  content=fh.read()
  fh.close()
  entry=content[content.find(playlistEntry):]
  fh=open(artistsFavsFile, 'w')
  fh.write(content.replace(playlistEntry+"\n",""))
  fh.close()
  if refresh=="TRUE":
    xbmc.executebuiltin("Container.Refresh")
