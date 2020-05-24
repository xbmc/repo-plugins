#!/usr/bin/python
# -*- coding: utf-8 -*-
import xbmcplugin,xbmcaddon,xbmcgui,os,sys

addon = xbmcaddon.Addon()
addon_path = addon.getAddonInfo('path').decode('utf-8')
icons_path = os.path.join(addon_path,'resources','senderlogos')
xbmcplugin.setContent(handle=int(sys.argv[1]), content='songs')
				
def add_item(url,infolabels,img=''):
    listitem = xbmcgui.ListItem(infolabels['title'],iconImage=img,thumbnailImage=img)
    listitem.setInfo('audio',infolabels)
    listitem.setProperty('IsPlayable','true')
    xbmcplugin.addDirectoryItem(int(sys.argv[1]),url,listitem)

add_item('https://streams.ilovemusic.de/iloveradio1.mp3',{'title':'I LOVE RADIO'},os.path.join(icons_path,'i_love_radio.png'))
add_item('https://streams.ilovemusic.de/iloveradio2.mp3',{'title':'I LOVE 2 DANCE'},os.path.join(icons_path,'i_love_2_dance.png'))
add_item('https://streams.ilovemusic.de/iloveradio23.mp3',{'title':'I LOVE CHILL NATION'},os.path.join(icons_path,'i_love_chill_nation.png'))
add_item('https://streams.ilovemusic.de/iloveradio103.mp3',{'title':'I LOVE DANCE FIRST'},os.path.join(icons_path,'i_love_dance_first.png'))
add_item('https://streams.ilovemusic.de/iloveradio6.mp3',{'title':'I LOVE DEUTSCHRAP BESTE'},os.path.join(icons_path,'i_love_deutschrap_beste.png'))
add_item('https://streams.ilovemusic.de/iloveradio104.mp3',{'title':'I LOVE DEUTSCHRAP FIRST!'},os.path.join(icons_path,'i_love_deutschrap_first.png'))
add_item('https://streams.ilovemusic.de/iloveradio16.mp3',{'title':'I LOVE GREATEST HITS'},os.path.join(icons_path,'i_love_greatest_hits.png'))
add_item('https://streams.ilovemusic.de/iloveradio21.mp3',{'title':'I LOVE HARDSTYLE'},os.path.join(icons_path,'i_love_hardstyle.png'))
add_item('https://streams.ilovemusic.de/iloveradio3.mp3',{'title':'I LOVE HIP HOP'},os.path.join(icons_path,'i_love_hip_hop.png'))
add_item('https://streams.ilovemusic.de/iloveradio109.mp3',{'title':'I LOVE HITS 2020'},os.path.join(icons_path,'i_love_hits_2020.png'))
add_item('https://streams.ilovemusic.de/iloveradio12.mp3',{'title':'I LOVE HITS HISTORY'},os.path.join(icons_path,'i_love_hits_history.png'))
add_item('https://streams.ilovemusic.de/iloveradio22.mp3',{'title':'I LOVE MAINSTAGE'},os.path.join(icons_path,'i_love_mainstage.png'))
add_item('https://streams.ilovemusic.de/iloveradio5.mp3',{'title':'I LOVE MASHUP'},os.path.join(icons_path,'i_love_mashup.png'))
add_item('https://streams.ilovemusic.de/iloveradio10.mp3',{'title':'I LOVE MUSIC AND CHILL'},os.path.join(icons_path,'i_love_music_and_chill.png'))
add_item('https://streams.ilovemusic.de/iloveradio14.mp3',{'title':'I LOVE PARTY HARD'},os.path.join(icons_path,'i_love_party_hard.png'))
add_item('https://streams.ilovemusic.de/iloveradio11.mp3',{'title':'I LOVE POPSTARS'},os.path.join(icons_path,'i_love_popstars.png'))
add_item('https://streams.ilovemusic.de/iloveradio18.mp3',{'title':'I LOVE ROBIN SCHULZ'},os.path.join(icons_path,'i_love_robin_schulz.png'))
add_item('https://streams.ilovemusic.de/iloveradio7.mp3',{'title':'I LOVE THE BEACH'},os.path.join(icons_path,'i_love_the_beach.png'))
add_item('https://streams.ilovemusic.de/iloveradio20.mp3',{'title':'I LOVE THE CLUB'},os.path.join(icons_path,'i_love_the_club.png'))
add_item('https://streams.ilovemusic.de/iloveradio4.mp3',{'title':'I LOVE THE DJ BY DJ MAG'},os.path.join(icons_path,'i_love_the_dj_by_dj_mag.png'))
add_item('https://streams.ilovemusic.de/iloveradio15.mp3',{'title':'I LOVE THE SUN'},os.path.join(icons_path,'i_love_the_sun.png'))
add_item('https://streams.ilovemusic.de/iloveradio9.mp3',{'title':'I LOVE TOP 100 CHARTS'},os.path.join(icons_path,'i_love_the_top_100_charts.png'))
add_item('https://streams.ilovemusic.de/iloveradio24.mp3',{'title':'I LOVE TRAP NATION'},os.path.join(icons_path,'i_love_trap_nation.png'))
add_item('https://streams.ilovemusic.de/iloveradio13.mp3',{'title':'I LOVE US ONLY RAP RADIO'},os.path.join(icons_path,'i_love_us_only_rap_radio.png'))
add_item('https://streams.ilovemusic.de/iloveradio8.mp3',{'title':'I LOVE X-MAS'},os.path.join(icons_path,'i_love_X-Mas.png'))

xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True, updateListing=False, cacheToDisc=True)