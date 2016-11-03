#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys,os,re,urllib,xbmcplugin,xbmcaddon,xbmcgui

addonID = "plugin.video.mtv_de"
addon_work_folder=xbmc.translatePath("special://profile/addon_data/"+addonID)
playlist=xbmc.translatePath("special://profile/addon_data/"+addonID+"/"+addonID+".playlists")
settings = xbmcaddon.Addon(id=addonID)

playlistsTemp=[]
for i in range(0,9,1):
  playlistsTemp.append(settings.getSetting("pl"+str(i)))
playlists=[]
for pl in playlistsTemp:
  if pl!="":
    playlists.append(pl)

if not os.path.isdir(addon_work_folder):
  os.mkdir(addon_work_folder)

param=urllib.unquote_plus(sys.argv[1])
mode=param[param.find("###MODE###=")+11:]
mode=mode[:mode.find("###")]
playlistEntry=param[param.find("###URL###="):]

if mode=="ADD":
  if len(playlists)==1:
    pl = playlists[0]
  else:
    dialog = xbmcgui.Dialog()
    pl = playlists[dialog.select('Playlist wählen', playlists)]
  if type(pl)==type(str()):
    playlistEntry=playlistEntry+"PLAYLIST###="+pl+"###PLEND###"
    if os.path.exists(playlist):
      fh = open(playlist, 'r')
      content=fh.read()
      fh.close()
      if content.find(playlistEntry)==-1:
        fh=open(playlist, 'a')
        fh.write(playlistEntry+"\n")
        fh.close()
    else:
      fh=open(playlist, 'a')
      fh.write(playlistEntry+"\n")
      fh.close()
elif mode=="REMOVE":
  refresh=param[param.find("###REFRESH###=")+14:]
  refresh=refresh[:refresh.find("###URL###=")]
  fh = open(playlist, 'r')
  content=fh.read()
  fh.close()
  fh=open(playlist, 'w')
  fh.write(content.replace(playlistEntry+"\n",""))
  fh.close()
  if refresh=="TRUE":
    xbmc.executebuiltin("Container.Refresh")
