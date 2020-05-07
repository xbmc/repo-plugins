#!/usr/bin/python
# -*- coding: utf-8 -*-
import xbmcplugin,xbmcaddon,xbmcgui,os,sys

addon = xbmcaddon.Addon()
addon_path = addon.getAddonInfo('path').decode('utf-8')
xbmcplugin.setContent(handle=int(sys.argv[1]), content='songs')
				
def add_item(url,infolabels,):
    listitem = xbmcgui.ListItem(infolabels['title'])
    listitem.setInfo('audio',infolabels)
    listitem.setProperty('IsPlayable','true')
    xbmcplugin.addDirectoryItem(int(sys.argv[1]),url,listitem)

add_item('https://streams.ilovemusic.de/iloveradio1.mp3',{'title':'I LOVE RADIO'})
add_item('https://streams.ilovemusic.de/iloveradio2.mp3',{'title':'I LOVE 2 DANCE'})
add_item('https://streams.ilovemusic.de/iloveradio23.mp3',{'title':'I LOVE CHILL NATION'})
add_item('https://streams.ilovemusic.de/iloveradio103.mp3',{'title':'I LOVE DANCE FIRST'})
add_item('https://streams.ilovemusic.de/iloveradio6.mp3',{'title':'I LOVE DEUTSCHRAP BESTE'})
add_item('https://streams.ilovemusic.de/iloveradio104.mp3',{'title':'I LOVE DEUTSCHRAP FIRST!'})
add_item('https://streams.ilovemusic.de/iloveradio16.mp3',{'title':'I LOVE GREATEST HITS'})
add_item('https://streams.ilovemusic.de/iloveradio21.mp3',{'title':'I LOVE HARDSTYLE'})
add_item('https://streams.ilovemusic.de/iloveradio3.mp3',{'title':'I LOVE HIP HOP'})
add_item('https://streams.ilovemusic.de/iloveradio109.mp3',{'title':'I LOVE HITS 2020'})
add_item('https://streams.ilovemusic.de/iloveradio12.mp3',{'title':'I LOVE HITS HISTORY'})
add_item('https://streams.ilovemusic.de/iloveradio22.mp3',{'title':'I LOVE MAINSTAGE'})
add_item('https://streams.ilovemusic.de/iloveradio5.mp3',{'title':'I LOVE MASHUP'})
add_item('https://streams.ilovemusic.de/iloveradio10.mp3',{'title':'I LOVE MUSIC AND CHILL'})
add_item('https://streams.ilovemusic.de/iloveradio14.mp3',{'title':'I LOVE PARTY HARD'})
add_item('https://streams.ilovemusic.de/iloveradio11.mp3',{'title':'I LOVE POPSTARS'})
add_item('https://streams.ilovemusic.de/iloveradio18.mp3',{'title':'I LOVE ROBIN SCHULZ'})
add_item('https://streams.ilovemusic.de/iloveradio7.mp3',{'title':'I LOVE THE BEACH'})
add_item('https://streams.ilovemusic.de/iloveradio20.mp3',{'title':'I LOVE THE CLUB'})
add_item('https://streams.ilovemusic.de/iloveradio4.mp3',{'title':'I LOVE THE DJ BY DJ MAG'})
add_item('https://streams.ilovemusic.de/iloveradio15.mp3',{'title':'I LOVE THE SUN'})
add_item('https://streams.ilovemusic.de/iloveradio9.mp3',{'title':'I LOVE TOP 100 CHARTS'})
add_item('https://streams.ilovemusic.de/iloveradio24.mp3',{'title':'I LOVE TRAP NATION'})
add_item('https://streams.ilovemusic.de/iloveradio13.mp3',{'title':'I LOVE US ONLY RAP RADIO'})
add_item('https://streams.ilovemusic.de/iloveradio8.mp3',{'title':'I LOVE X-MAS'})

xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True, updateListing=False, cacheToDisc=False)