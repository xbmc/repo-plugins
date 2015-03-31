#!/usr/bin/python
# -*- coding: utf-8 -*-
import xbmcplugin,xbmcgui,sys,urllib

def addDirectory(title,banner,backdrop,translation,description,link,mode,pluginhandle):
    parameters = {"link" : link,"title" : title,"banner" : banner,"backdrop" : backdrop, "mode" : mode}
    u = sys.argv[0] + '?' + urllib.urlencode(parameters)
    createListItem(title,banner,description,'','','',u,'false',True,translation,backdrop,pluginhandle,None)

def createListItem(title,banner,description,duration,date,channel,videourl,playable,folder,translation,backdrop,pluginhandle,subtitles=None):
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

    xbmcplugin.addDirectoryItem(handle=pluginhandle, url=videourl, listitem=liz, isFolder=folder)
    return liz
