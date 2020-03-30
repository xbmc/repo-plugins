#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# c't uplink - The Audio Podcast Kodi Plug-in
# by Achim Barczok, Heise Medien
#
# Diese Basisversion entspricht dem Beispiel in c't 19/2018
# eine etwas schönere und umfangreiche Version 
# finden Sie unter plugin.audio.ctuplink_audio

import sys
import xbmcgui
import xbmcplugin
import xbmcaddon
import feedparser

def run():
    #Selbst-Referenzierung fürs Plug-in
    addon_handle = int(sys.argv[1])
    
    #Siedle Plug-in in den Bereich Audio
    xbmcplugin.setContent(addon_handle, 'video')
    
    
    #Parse ctuplink-Feed
    d = feedparser.parse('http://www.heise.de/heiseshowhd.rss')
    
    #Liste mit allen Folgen aufbauen
    listing = []
    
    for item in d['entries']:
        title = item['title']
        url = item.enclosures[0].href
        
        #Beschreibung der Folge auslesen, für Audio nicht notwendig, aber für Audio praktisch
        summary = item['description']    
        
        #Einige Folgen haben kein Thumbnailbild, die bekommen ein Standard-Bild verpasst
        try:
            thumb = item['image'].href
        except:
            thumb = "https://heise.cloudimg.io/bound/480x270/q75.png-lossy-75.webp-lossy-75.foil1/_www-heise-de_/ct/imgs/04/1/4/2/6/3/2/5/9cc02d4fe2a3a731.jpeg"
    
        #Baue fürs GUI ein Listenelement
        list_item = xbmcgui.ListItem(label=title, label2=summary)
    
        #Fanart des Plug-ins als Hintergrundbild nutzen
        ctuplink_plugin = xbmcaddon.Addon('plugin.video.heiseshowrss')
        list_item.setArt({'fanart': ctuplink_plugin.getAddonInfo('fanart'), 'thumb': thumb})
        
        list_item.setProperty('IsPlayable', 'true')            
        list_item.setInfo('video', {'plot': summary})
        listing.append((url, list_item, False))    
            
    
    #In diesem Beispiel fügen wir alle Items in einem der Liste hinzu
    xbmcplugin.addDirectoryItems(addon_handle, listing, len(listing))
    
    #Schließe die Liste ab
    xbmcplugin.endOfDirectory(addon_handle, succeeded=True)
