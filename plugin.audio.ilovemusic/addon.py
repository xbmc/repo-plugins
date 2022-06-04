#!/usr/bin/python
# -*- coding: utf-8 -*-
import xbmcplugin,xbmcaddon,xbmcgui,os,sys,requests

addon = xbmcaddon.Addon()
addon_path = addon.getAddonInfo('path').decode('utf-8')
senderliste = os.path.join(addon_path,'resources','senderliste.txt')
xbmcplugin.setContent(handle=int(sys.argv[1]), content='songs')
enable_senderupdate = addon.getSetting('senderupdate')

def sender_update():
    addon_path = addon.getAddonInfo('path').decode('utf-8')
    icons_path = os.path.join(addon_path,'resources','senderlogos')
    senderliste = os.path.join(addon_path,'resources','senderliste.txt')
    url = 'https://raw.githubusercontent.com/adiko01/plugin.audio.ilovemusic/Daten/Senderlisten/Senderliste-Stabel.txt'
    r = requests.get(url, allow_redirects=True)
    open(senderliste, 'wb').write(r.content)
				
def add_item(url,infolabels,img=''):
    listitem = xbmcgui.ListItem(infolabels['title'])
    listitem.setInfo('audio',infolabels)
    listitem.setArt({ 'thumb': img , 'icon' : img })
    listitem.setProperty('IsPlayable','true')
    xbmcplugin.addDirectoryItem(int(sys.argv[1]),url,listitem)    

if enable_senderupdate == 'true':
    sender_update()

datei = open(senderliste,'r')
for zeile in datei:
    sender2 = zeile.split(',')
    add_item(sender2[0],{'title':sender2[1]},sender2[2])

xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True, updateListing=False, cacheToDisc=True)
