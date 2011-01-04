# -*- coding: utf-8 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para letmewatchthis
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#------------------------------------------------------------
import urlparse,urllib2,urllib,re
import os, sys

import scrapertools
import servertools
import logger
import buscador
from item import Item

CHANNELNAME = "letmewatchthis"
DEBUG = True

def isGeneric():
    return True

def mainlist(item):
    logger.info("[letmewatchthis.py] mainlist")

    itemlist = []
    itemlist.append( Item(channel=CHANNELNAME, action="peliculas" , title="Movies"   ,url="http://www.letmewatchthis.com/"))
    itemlist.append( Item(channel=CHANNELNAME, action="series"    , title="TV Shows" ,url="http://www.letmewatchthis.com/?tv"))
    #itemlist.append( Item(channel=CHANNELNAME, action=""search"     , category , "Buscar"                           ,"","","")

    return itemlist

def peliculas(item):
    logger.info("[letmewatchthis.py] peliculas")

    return listaconcaratulas(item,"listmirrors")

def series(item):
    logger.info("[letmewatchthis.py] peliculas")

    return listaconcaratulas(item,"listepisodes")

def listaconcaratulas(item,action):

    itemlist = []

    # Descarga la página
    data = scrapertools.cachePage(item.url)
    #logger.info(data)

    '''
    <div class="index_item index_item_ie"><a href="/watch-356059-Here-Come-the-Co-eds" title="Watch Here Come the Co-eds (1945) - 37 views"><img src="http://images.letmewatchthis.com/thumbs/356059_Here_Come_the_Co_eds_1945.jpg" border="0" alt="Watch Here Come the Co-eds"><h2>Here Come the Co-.. (1945)</h2></a><div class="index_ratings">
    <div id="unit_long356059">
    <ul style="width: 100px;" class="unit-rating">
    <li style="width: 60px;" class="current-rating">Current rating.</li> <li class="r1-unit"></li>
    <li class="r2-unit"></li>
    <li class="r3-unit"></li>
    <li class="r4-unit"></li>
    <li class="r5-unit"></li>
    </ul>
    </div>
    </div><div class="item_categories"><a href="/?genre=Comedy">Comedy</a> <a href="/?genre=Musical">Musical</a> </div></div>
    '''
    patronvideos  = '<div class="index_item index_item_ie"><a href="([^"]+)" title="([^"]+)"><img src="([^"]+)"'

    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    if DEBUG: scrapertools.printMatches(matches)

    for match in matches:
        # Titulo
        scrapedtitle = match[1]
        scrapedplot = ""
        scrapedurl = urlparse.urljoin(item.url,match[0])
        scrapedthumbnail = match[2]
        if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

        # Añade al listado de XBMC
        itemlist.append( Item(channel=CHANNELNAME, action=action, title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )

    # Extrae el paginador
    #<span class=current>1</span> <a href="/index.php?page=2">2</a>
    patronvideos  = '<span class=current>[^<]+</span> <a href="([^"]+)">'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    if len(matches)>0:
        scrapedurl = urlparse.urljoin(item.url,matches[0])
        itemlist.append( Item(channel=CHANNELNAME, action="peliculas", title="!Next page" , url=scrapedurl , folder=True) )
    
    return itemlist

def listepisodes(item):
    logger.info("[letmewatchthis.py] listepisodes")
    itemlist = []

    # Descarga la página
    data = scrapertools.cachePage(item.url)
    #logger.info(data)
    '''
    <div class="tv_episode_item"> <a href="/tv-11033-Storm-Chasers/season-1-episode-1">Episode 1                                <span class="tv_episode_name"> - Episode 1</span>
    </a> </div>
    '''
    patronvideos  = '<div class="tv_episode_item"> <a href="([^"]+)">([^<]+)<span class="tv_episode_name">([^<]+)</span>'

    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    if DEBUG: scrapertools.printMatches(matches)

    for match in matches:
        scrapedtitle = match[1].strip()+" "+match[2].strip()
        scrapedplot = ""
        scrapedurl = urlparse.urljoin(item.url,match[0])
        scrapedthumbnail = item.thumbnail
        if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")
        itemlist.append( Item(channel=CHANNELNAME, action="listmirrors", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )

    return itemlist

def listmirrors(item):
    logger.info("[letmewatchthis.py] listmirrors")
    itemlist = []

    # Descarga la página
    data = scrapertools.cachePage(item.url)
    #logger.info(data)
    '''
    <a href="/external.php?title=Tangled&url=aHR0cDovL3d3dy5zb2Nrc2hhcmUuY29tL2ZpbGUvNlBKODNDMjA1UU84V0tX&domain=c29ja3NoYXJlLmNvbQ==&loggedin=0" onClick="return  addHit('1886628137', '1')" rel="nofollow" target="_blank"> Watch Version 3</a>
    </span></td>
    <td align="center" width="115" valign="middle"><span class="version_host"><img src=/images/host_45.gif></span>
    '''

    patronvideos  = '<a href="(/external.php[^"]+)"[^>]+>(.*?)</a>.*?'
    patronvideos += '<span class="version_host">(.*?)</span>'

    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    if DEBUG: scrapertools.printMatches(matches)

    for match in matches:
        # Servidor
        servidor = match[2]
        servidor = servidor.replace('<script type="text/javascript">document.writeln(','')
        servidor = servidor.replace(");</script>","")
        servidor = servidor.replace("<img src=/images/","")
        servidor = servidor.replace(">","")
        servidor = servidor.strip()
        # Titulo
        scrapedtitle = match[1]+" ("+servidor+")"
        scrapedplot = ""
        scrapedurl = urlparse.urljoin(item.url,match[0])
        scrapedthumbnail = item.thumbnail
        if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")
        itemlist.append( Item(channel=CHANNELNAME, action="findvideos", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )

    return itemlist
