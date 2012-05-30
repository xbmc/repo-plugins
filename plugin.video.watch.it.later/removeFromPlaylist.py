#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys,os,re,urllib,xbmcplugin,xbmcaddon,xbmcgui

addonID = "plugin.video.watch.it.later"
myPlaylist=xbmc.translatePath("special://profile/addon_data/"+addonID+"/playlist")

playlistEntry=urllib.unquote_plus(sys.argv[1])
fh = open(myPlaylist, 'r')
content=fh.read()
fh.close()
fh=open(myPlaylist, 'w')
fh.write(content.replace(playlistEntry+"\n",""))
fh.close()
xbmc.executebuiltin("Container.Refresh")