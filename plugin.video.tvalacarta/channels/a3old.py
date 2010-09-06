# -*- coding: iso-8859-1 -*-

import sys
import urllib

import xbmctools
import logger
import a3parser as channel
from item import Item

try:
    pluginhandle = int( sys.argv[ 1 ] )
except:
    pluginhandle = ""

DEBUG = True
CHANNELNAME = "a3"

def mainlist(params,url,category):
    logger.info("[a3.py] mainlist")
    
    itemlist = channel.mainlist()
    xbmctools.renderItems(itemlist, params, url, category)

def losmasvistos(params,url,category):
    logger.info("[a3.py] losmasvistos")
    
    title = urllib.unquote_plus( params.get("title") )
    thumbnail = urllib.unquote_plus( params.get("thumbnail") )
    plot = urllib.unquote_plus( params.get("plot") )
    server = "directo"

    item = Item(channel=CHANNELNAME, title=title , url=url, thumbnail=thumbnail , plot=plot , server=server , folder=True)
    itemlist = channel.losmasvistos( item )
    xbmctools.renderItems(itemlist, params, url, category)

def ultimosvideos(params,url,category):
    logger.info("[a3.py] ultimosvideos")
    
    title = urllib.unquote_plus( params.get("title") )
    thumbnail = urllib.unquote_plus( params.get("thumbnail") )
    plot = urllib.unquote_plus( params.get("plot") )
    server = "directo"

    item = Item(channel=CHANNELNAME, title=title , url=url, thumbnail=thumbnail , plot=plot , server=server , folder=True)
    itemlist = channel.ultimosvideos( item )
    xbmctools.renderItems(itemlist, params, url, category)

def ultimasemana(params,url,category):
    logger.info("[a3.py] ultimasemana")
    
    title = urllib.unquote_plus( params.get("title") )
    thumbnail = urllib.unquote_plus( params.get("thumbnail") )
    plot = urllib.unquote_plus( params.get("plot") )
    server = "directo"

    item = Item(channel=CHANNELNAME, title=title , url=url, thumbnail=thumbnail , plot=plot , server=server , folder=True)
    itemlist = channel.ultimasemana( item )
    xbmctools.renderItems(itemlist, params, url, category)

def series(params,url,category):
    logger.info("[a3.py] series")
    
    title = urllib.unquote_plus( params.get("title") )
    thumbnail = urllib.unquote_plus( params.get("thumbnail") )
    plot = urllib.unquote_plus( params.get("plot") )
    server = "directo"

    item = Item(channel=CHANNELNAME, title=title , url=url, thumbnail=thumbnail , plot=plot , server=server , folder=True)
    itemlist = channel.series( item )
    xbmctools.renderItems(itemlist, params, url, category)

def capitulos(params,url,category):
    logger.info("[a3.py] capitulos")
    
    title = urllib.unquote_plus( params.get("title") )
    thumbnail = urllib.unquote_plus( params.get("thumbnail") )
    plot = urllib.unquote_plus( params.get("plot") )
    server = "directo"

    item = Item(channel=CHANNELNAME, title=title , url=url, thumbnail=thumbnail , plot=plot , server=server , folder=True)
    itemlist = channel.capitulos( item )
    xbmctools.renderItems(itemlist, params, url, category)

def programas(params,url,category):
    logger.info("[a3.py] programas")
    
    title = urllib.unquote_plus( params.get("title") )
    thumbnail = urllib.unquote_plus( params.get("thumbnail") )
    plot = urllib.unquote_plus( params.get("plot") )
    server = "directo"

    item = Item(channel=CHANNELNAME, title=title , url=url, thumbnail=thumbnail , plot=plot , server=server , folder=True)
    itemlist = channel.programas( item )
    xbmctools.renderItems(itemlist, params, url, category)

def detalle(params,url,category):
    logger.info("[a3.py] detalle")
    
    title = urllib.unquote_plus( params.get("title") )
    thumbnail = urllib.unquote_plus( params.get("thumbnail") )
    plot = urllib.unquote_plus( params.get("plot") )
    server = "directo"

    item = Item(channel=CHANNELNAME, title=title , url=url, thumbnail=thumbnail , plot=plot , server=server , folder=True)
    itemlist = channel.detalle( item )
    xbmctools.renderItems(itemlist, params, url, category)

def play(params,url,category):
    logger.info("[a3.py] play")
    
    title = urllib.unquote_plus( params.get("title") )
    thumbnail = urllib.unquote_plus( params.get("thumbnail") )
    plot = urllib.unquote_plus( params.get("plot") )
    server = "directo"

    xbmctools.playvideo(CHANNELNAME,server,url,category,title,thumbnail,plot)

    '''
    flvstreamer -V -r "rtmp://antena3tvfs.fplive.net/antena3mediateca/mp_seriesh2/2010/07/21/00004/001.mp4" -o out.mp4
    FLVStreamer v1.9
    (c) 2009 Andrej Stepanchuk, Howard Chu, The Flvstreamer Team; license: GPL
    DEBUG: Parsing...
    DEBUG: Parsed protocol: 0
    DEBUG: Parsed host    : antena3tvfs.fplive.net
    DEBUG: Parsed app     : antena3mediateca/mp_seriesh2
    DEBUG: Protocol : RTMP
    DEBUG: Hostname : antena3tvfs.fplive.net
    DEBUG: Port     : 1935
    DEBUG: Playpath : mp4:2010/07/21/00004/001.mp4
    DEBUG: tcUrl    : rtmp://antena3tvfs.fplive.net:1935/antena3mediateca/mp_seriesh2
    DEBUG: app      : antena3mediateca/mp_seriesh2
    DEBUG: flashVer : LNX 10,0,22,87
    DEBUG: live     : no
    DEBUG: timeout  : 120 sec
    '''
    '''
    #url="http://desprogresiva.antena3.com/mp_seriesh2/2010/07/21/00004/000.mp4"
    #url=rtmp://antena3tvfs.fplive.net/antena3mediateca/mp_seriesh2/2010/07/21/00004/001.mp4
    #url=http://desprogresiva.antena3.com/mp_seriesh2/2010/08/19/00003/000.mp4
    hostname = "antena3tvfs.fplive.net"
    logger.info("[a3.py] hostname="+hostname)
    portnumber = "1935"
    logger.info("[a3.py] portnumber="+portnumber)
    tcurl = "rtmp://antena3tvfs.fplive.net/antena3mediateca"
    logger.info("[a3.py] tcurl="+tcurl)
    #playpath = "mp_seriesh2/2010/07/21/00004/001.mp4"
    playpath = url[33:]
    logger.info("[a3.py] playpath="+playpath)
    app = "antena3mediateca"
    logger.info("[a3.py] app="+app)
    swfplayer = "http://www.antena3.com/static/swf/A3Player.swf"
    logger.info("[a3.py] swfplayer="+swfplayer)

    #url = "rtmp://antena3tvfs.fplive.net/antena3mediateca/"+playpath
    #logger.info("[a3.py] url="+url)
    url="http://desprogresiva.antena3.com/mp_seriesh2/2010/07/21/00004/000.mp4"
    
    import xbmcgui
    listitem = xbmcgui.ListItem( title, iconImage="DefaultVideo.png", thumbnailImage=thumbnail )
    listitem.setInfo( "video", { "Title": title, "Plot" : plot , "Studio" : CHANNELNAME , "Genre" : category } )
    listitem.setProperty("SWFPlayer", swfplayer)
    listitem.setProperty("Hostname",hostname)
    listitem.setProperty("Port",portnumber)
    listitem.setProperty("tcUrl",tcurl)
    listitem.setProperty("Playpath",playpath)
    listitem.setProperty("app",app)
    listitem.setProperty("flashVer","LNX 10,1,82,76")
    listitem.setProperty("pageUrl","http://www.antena3.com/videos/el-internado/temporada-7/capitulo-8.html")

    # Playlist vacia
    import xbmc
    playlist = xbmc.PlayList( xbmc.PLAYLIST_VIDEO )
    playlist.clear()
    playlist.add( url, listitem )

    # Reproduce
    xbmcPlayer = xbmc.Player( xbmc.PLAYER_CORE_AUTO )
    xbmcPlayer.play(playlist)   
    '''