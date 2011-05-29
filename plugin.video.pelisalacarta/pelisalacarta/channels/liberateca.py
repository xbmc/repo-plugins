# -*- coding: utf-8 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para liberateca
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#------------------------------------------------------------
import urlparse,urllib2,urllib,re
import os, sys
import base64

from core import logger
from core import config
from core import scrapertools
from core.item import Item
from servers import servertools

CHANNELNAME = "liberateca"
DEBUG = True
SESION = config.get_setting("session","liberateca")
LOGIN = config.get_setting("login","liberateca")
PASSWORD = config.get_setting("password","liberateca")

def isGeneric():
    return True

def mainlist(item):
    logger.info("[liberateca.py] mainlist")

    itemlist = []

    itemlist.append( Item(channel=CHANNELNAME, title="Todas las series", action="series", url="http://liberateca.net/api/v1/series"))

    if SESION=="true":
        itemlist.append( Item(channel=CHANNELNAME, title="Cerrar sesion ("+LOGIN+")", action="logout"))
    else:
        itemlist.append( Item(channel=CHANNELNAME, title="Iniciar sesion", action="login"))

    return itemlist

def logout(item):
    nombre_fichero_config_canal = os.path.join( config.get_data_path() , CHANNELNAME+".xml" )
    config_canal = open( nombre_fichero_config_canal , "w" )
    config_canal.write("<settings>\n<session>false</session>\n<login></login>\n<password></password>\n</settings>")
    config_canal.close();

    itemlist = []
    itemlist.append( Item(channel=CHANNELNAME, title="Sesión finalizada", action="mainlist"))
    return itemlist

def login(item):
    import xbmc
    keyboard = xbmc.Keyboard("","Login")
    keyboard.doModal()
    if (keyboard.isConfirmed()):
        login = keyboard.getText()

    keyboard = xbmc.Keyboard("","Password")
    keyboard.doModal()
    if (keyboard.isConfirmed()):
        password = keyboard.getText()

    nombre_fichero_config_canal = os.path.join( config.get_data_path() , CHANNELNAME+".xml" )
    config_canal = open( nombre_fichero_config_canal , "w" )
    config_canal.write("<settings>\n<session>true</session>\n<login>"+login+"</login>\n<password>"+password+"</password>\n</settings>")
    config_canal.close();

    itemlist = []
    itemlist.append( Item(channel=CHANNELNAME, title="Sesión iniciada", action="mainlist"))
    return itemlist

def series(item):
    logger.info("[liberateca.py] series")

    # Descarga la página
    authStr = base64.encodestring('%s:%s' % (LOGIN, PASSWORD))[:-1]
    data = scrapertools.cachePage(item.url,headers=[["Authorization", "Basic %s" % authStr]])
    
    # Extrae las entradas
    patronvideos  = '"url": "([^"]+)",[^"]+'
    patronvideos += '"name": "([^"]+)"'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    if DEBUG: scrapertools.printMatches(matches)

    itemlist = []
    for match in matches:
        scrapedtitle = match[1]
        scrapedplot = ""
        scrapedurl = urlparse.urljoin(item.url,match[0])+"/seasons"
        scrapedthumbnail = ""
        if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")
        itemlist.append( Item(channel=CHANNELNAME, action="temporadas", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )

    return itemlist

def temporadas(item):
    logger.info("[liberateca.py] temporadas")

    # Descarga la página
    authStr = base64.encodestring('%s:%s' % (LOGIN, PASSWORD))[:-1]
    data = scrapertools.cachePage(item.url,headers=[["Authorization", "Basic %s" % authStr]])

    # Extrae las entradas
    patronvideos  = '"url": "([^"]+)"'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    if DEBUG: scrapertools.printMatches(matches)

    itemlist = []
    for match in matches:
        scrapedurl = urlparse.urljoin(item.url,match)
        scrapedtitle = "Temporada "+scrapedurl.split("/")[-2]
        scrapedplot = ""
        scrapedthumbnail = ""
        if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")
        itemlist.append( Item(channel=CHANNELNAME, action="episodios", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )

    return itemlist

def episodios(item):
    logger.info("[liberateca.py] episodios")

    # Descarga la página
    authStr = base64.encodestring('%s:%s' % (LOGIN, PASSWORD))[:-1]
    data = scrapertools.cachePage(item.url,headers=[["Authorization", "Basic %s" % authStr]])

    # Extrae las entradas
    patronvideos  = '"url": "([^"]+)",[^"]+'
    patronvideos += '"title": "([^"]+)",[^"]+'
    patronvideos += '"episode": (\d+)'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    if DEBUG: scrapertools.printMatches(matches)

    itemlist = []
    for match in matches:
        scrapedurl = urlparse.urljoin(item.url,match[0])
        scrapedtitle = match[2]+" "+match[1]
        scrapedplot = ""
        scrapedthumbnail = ""
        if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")
        itemlist.append( Item(channel=CHANNELNAME, action="videos", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )

    return itemlist

def videos(item): 
    logger.info("[liberateca.py] videos")

    # Descarga la página
    authStr = base64.encodestring('%s:%s' % (LOGIN, PASSWORD))[:-1]
    data = scrapertools.cachePage(item.url,headers=[["Authorization", "Basic %s" % authStr]])
    print data

    # Extrae las entradas
    patronvideos  = '"url": "([^"]+)",[^"]+'
    patronvideos += '"audio": "([^"]+)"'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    if DEBUG: scrapertools.printMatches(matches)

    itemlist = []
    for match in matches:
        scrapedurl = urlparse.urljoin(item.url,match[0])
        scrapedtitle = "Audio "+match[1]
        scrapedplot = ""
        scrapedthumbnail = ""
        if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

        videos = servertools.findvideos(scrapedurl)
        if len(videos)>0:
            print videos
            server = videos[0][2]
            scrapedurl = videos[0][1]
            itemlist.append( Item(channel=CHANNELNAME, action="play", title=scrapedtitle+" ["+server+"]" , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot, server=server, folder=False) )

    return itemlist
