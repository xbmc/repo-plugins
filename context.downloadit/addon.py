#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import xbmc
import xbmcaddon
import xbmcgui,xbmcvfs
import YDStreamUtils
import YDStreamExtractor
import time

addon = xbmcaddon.Addon()    
translation = addon.getLocalizedString
folder=addon.getSetting("folder")
ffmpgfile=addon.getSetting("ffmpgfile")
warning=addon.getSetting("warning")



def debug(content):
    log(content, xbmc.LOGDEBUG)
    
def notice(content):
    log(content, xbmc.LOGNOTICE)

def log(msg, level=xbmc.LOGNOTICE):
    addon = xbmcaddon.Addon()
    addonID = addon.getAddonInfo('id')
    xbmc.log('%s: %s' % (addonID, msg), level) 

def downloadyoutube(file,ffdir=""):
 debug("Start downloadyoutube")
 # If FFMPEG ist definied us it also in youtube-dl
 if not ffdir=="": 
    YDStreamExtractor.overrideParam('ffmpeg_location',ffdir)
 
 # Download Video
 YDStreamExtractor.overrideParam('preferedformat',"avi")  
 vid = YDStreamExtractor.getVideoInfo(file,quality=2)  
 with YDStreamUtils.DownloadProgress() as prog: #This gives a progress dialog interface ready to use
    try:
        YDStreamExtractor.setOutputCallback(prog)
        result = YDStreamExtractor.downloadVideo(vid,folder)
        if result:            
            full_path_to_file = result.filepath
        elif result.status != 'canceled':            
            error_message = result.message
    finally:
        YDStreamExtractor.setOutputCallback(None)
        
def downloadffmpg(file,name):    
    debug("Start downloadffmpg")
    import ffmpy
    import subprocess
    name=name.replace(" ","_").replace(":","")
    name=name[0:50]+".mp4"  
    name=os.path.join(folder,name)   
    ff = ffmpy.FFmpeg(executable=ffmpgfile, inputs={file: None},outputs={name: '-codec copy'})    
    erg=ff.cmd
    debug(erg)
    try:
        dialog=xbmcgui.DialogProgress()
        # Download started
        dialog.create(translation(30002))        
        ret=ff.run(stdout=subprocess.PIPE)
        dialog.close()
        dialog2 = xbmcgui.Dialog()                
        nr=dialog2.ok(translation(30003), translation(30004))
    except:
      dialog.close()
      dialog = xbmcgui.Dialog()
      nr=dialog.ok(translation(30005), translation(30006))
      kodi_player.play(path,listitem)
      time.sleep(5)
      ffdir,fffile=os.path.split(ffmpgfile)
      debug("FFDIR :"+ffdir)
      downloadyoutube(file,ffdir=ffdir)  
    
#MAIN    
# Waring about Abuse
if warning=="false":
    dialog = xbmcgui.Dialog()
    erg=dialog.yesno(translation(30007), translation(30008),translation(30009),translation(30010))
    if erg==1:
       addon.setSetting("warning","true")
    else:
      quit()    

# Read Selected Infolabel      
path = xbmc.getInfoLabel('ListItem.FileNameAndPath')
title = xbmc.getInfoLabel('ListItem.Title')
listitem = xbmcgui.ListItem(path=path)
listitem.setInfo(type="Video", infoLabels={"Title": title})

#Start Video
kodi_player = xbmc.Player()
kodi_player.play(path,listitem)
time.sleep(10) 
videoda=0

#Until the First file is playdread file
while videoda==0 :
    try:
        file=kodi_player.getPlayingFile()
        debug("-----> "+file)
        if not file=="":
            videoda=1
    except:
        pass 
# Kill Header Fields        
file=file.split("|")[0]      

# User FFMPEG or youtube-dl
if not ffmpgfile=="":
   kodi_player.stop()
   downloadffmpg(file,title)  
else:
   downloadyoutube(file)
