#!/usr/bin/python
# -*- coding: utf-8 -*-
import xbmc,xbmcplugin,xbmcgui,sys,urllib,re,os
import simplejson

def addDirectory(title,banner,backdrop,translation,description,link,mode,pluginhandle):
    parameters = {"link" : link,"title" : title,"banner" : banner,"backdrop" : backdrop, "mode" : mode}
    u = sys.argv[0] + '?' + urllib.urlencode(parameters)
    createListItem(title,banner,description,'','','',u,'false',True,translation,backdrop,pluginhandle,None)

def createListItem(title,banner,description,duration,date,channel,videourl,playable,folder,translation,backdrop,pluginhandle,subtitles=None,blacklist=False):
    if description == '':
        description = (translation(30008)).encode("utf-8")
    liz=xbmcgui.ListItem(title, iconImage=banner, thumbnailImage=banner)
    liz.setInfo( type="Video", infoLabels={ "Title": title } )
    liz.setInfo( type="Video", infoLabels={ "Tvshowtitle": title } )
    liz.setInfo( type="Video", infoLabels={ "Sorttitle": title } )
    liz.setInfo( type="Video", infoLabels={ "Plot": description } )
    liz.setInfo( type="Video", infoLabels={ "Plotoutline": description } )
    liz.setInfo( type="Video", infoLabels={ "Aired": date } )
    liz.setInfo( type="Video", infoLabels={ "Studio": channel } )
    liz.setProperty('fanart_image',backdrop)
    liz.setProperty('IsPlayable', playable)
    
    if not folder:
        try:
            liz.addStreamInfo('video', { 'codec': 'h264','duration':int(duration) ,"aspect": 1.78, "width": 640, "height": 360})
        except:
            liz.addStreamInfo('video', { 'codec': 'h264',"aspect": 1.78, "width": 640, "height": 360})
        liz.addStreamInfo('audio', {"codec": "aac", "language": "de", "channels": 2})
        if subtitles != None:
            if subtitles[0].endswith('.srt'):
                subtitles.pop(0)
            liz.addStreamInfo('subtitle', {"language": "de"})
            liz.setSubtitles(subtitles)   
    
    if blacklist:
        match = re.search(r'( - \w\w, \d\d.\d\d.\d\d\d\d)',title)
        if match != None:
            bltitle = title.split(" - ")
            bltitle = bltitle[0].split(": ")
            
            bl_title = bltitle[0].replace("+"," ").strip()
        else:
            bl_title = title.replace("+"," ").strip()
        
        
        blparameters = {"mode" : "blacklistShow", "title": bl_title}
        blurl = sys.argv[0] + '?' + urllib.urlencode(blparameters)
        commands = []
        commands.append(( '%s %s %s' % (translation(30038).encode("utf-8"),bl_title,translation(30042).encode("utf-8")), 'XBMC.RunPlugin(%s)' % blurl ))
        liz.addContextMenuItems( commands )
        if not checkBlacklist(bl_title):
            xbmcplugin.addDirectoryItem(handle=pluginhandle, url=videourl, listitem=liz, isFolder=folder)
            return liz
    else:
        xbmcplugin.addDirectoryItem(handle=pluginhandle, url=videourl, listitem=liz, isFolder=folder)
        return liz

def checkBlacklist(title):
    addonUserDataFolder = xbmc.translatePath("special://profile/addon_data/plugin.video.orftvthek");
    bl_json_file = os.path.join(addonUserDataFolder, 'blacklist.json')
    if os.path.exists(bl_json_file):
        if os.path.getsize(bl_json_file) > 0:
            data = getBlacklist(bl_json_file)
            tmp = data;
            for item in tmp:
                if item.encode('UTF-8') == title:
                    return True
    return False
    
    
def removeBlacklist(title):
    addonUserDataFolder = xbmc.translatePath("special://profile/addon_data/plugin.video.orftvthek");
    bl_json_file = os.path.join(addonUserDataFolder, 'blacklist.json')
    if os.path.exists(bl_json_file):
        if os.path.getsize(bl_json_file) > 0:
            data = getBlacklist(bl_json_file)
            tmp = data;
            for item in tmp:
                if item.encode('UTF-8') == title:
                    tmp.remove(item)
            setBlacklist(tmp,bl_json_file)
    
def printBlacklist(banner,backdrop,translation,pluginhandle):
    addonUserDataFolder = xbmc.translatePath("special://profile/addon_data/plugin.video.orftvthek");
    bl_json_file = os.path.join(addonUserDataFolder, 'blacklist.json')
    if os.path.exists(bl_json_file):
        if os.path.getsize(bl_json_file) > 0:
            data = getBlacklist(bl_json_file)
            for item in data:
                item = item.encode('UTF-8')
                description = "%s %s %s" % ((translation(30040)).encode("utf-8"),item,(translation(30041)).encode("utf-8"))
                link = item
                mode = "unblacklistShow"
                addDirectory(item,banner,backdrop,translation,description,link,mode,pluginhandle)


def setBlacklist(data,file):
    with open(file,'w') as data_file:
        data_file.write(simplejson.dumps(data,'utf-8'))
    data_file.close()
    
def getBlacklist(file):
    data = []
    with open(file,'r') as data_file:
        data = simplejson.load(data_file,'UTF-8')
    return data
            
def blacklistItem(title):
    addonUserDataFolder = xbmc.translatePath("special://profile/addon_data/plugin.video.orftvthek");
    bl_json_file = os.path.join(addonUserDataFolder, 'blacklist.json')
    title = urllib.unquote(title).replace("+"," ").strip()
    #check if file exists
    if os.path.exists(bl_json_file):
        #check if file already has an entry
        if os.path.getsize(bl_json_file) > 0:
            #append value to JSON File
            if not checkBlacklist(title):
                data = getBlacklist(bl_json_file)
                data.append(title)
                setBlacklist(data,bl_json_file)
        #found empty file - writing first record
        else:
            data = []
            data.append(title)
            setBlacklist(data,bl_json_file)
    #create json file
    else:
        os.makedirs(addonUserDataFolder)
        data = []
        data.append(title)
        setBlacklist(data,bl_json_file)
        
        
def unblacklistItem(title):
    addonUserDataFolder = xbmc.translatePath("special://profile/addon_data/plugin.video.orftvthek");
    bl_json_file = os.path.join(addonUserDataFolder, 'blacklist.json')
    title = urllib.unquote(title).replace("+"," ").strip()
    removeBlacklist(title)