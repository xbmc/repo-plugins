# -*- coding: utf-8 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para cinetube
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#------------------------------------------------------------
import urlparse,urllib2,urllib,re
import os, sys

import scrapertools
import servertools
import logger
import buscador
from item import Item

CHANNELNAME = "cinetube"
DEBUG = True

def isGeneric():
    return True

def mainlist(item):
    logger.info("[cinetube.py] getmainlist")

    itemlist = []
    itemlist.append( Item(channel=CHANNELNAME, title="Películas - Novedades (con carátula)"  , action="listpeliconcaratula", url="http://www.cinetube.es/peliculas/"))
    #itemlist.append( Item(channel=CHANNELNAME, title="Películas - Todas (sin carátula)"      , action="listpelisincaratula", url="http://www.cinetube.es/peliculas-todas/", folder=True) )
    itemlist.append( Item(channel=CHANNELNAME, title="Películas - Todas A-Z (con carátula)" , action="listalfabetico"      , url=""))

    itemlist.append( Item(channel=CHANNELNAME, title="Series - Novedades (con carátula)"    , action="listtemporadacaratula" , url="http://www.cinetube.es/series/"))
    itemlist.append( Item(channel=CHANNELNAME, title="Series - Todas A-Z (con carátula)"    , action="listalfabetico"      , url=""))

    itemlist.append( Item(channel=CHANNELNAME, title="Documentales - Novedades" , action="listpeliconcaratula" , url="http://www.cinetube.es/documentales/"))
    itemlist.append( Item(channel=CHANNELNAME, title="Documentales - Todos A-Z" , action="listalfabetico"      , url=""))

    itemlist.append( Item(channel=CHANNELNAME, title="Anime - Series"    , action="list" , url="http://www.cinetube.es/series-anime/") )
    itemlist.append( Item(channel=CHANNELNAME, title="Anime - Películas" , action="list" , url="http://www.cinetube.es/peliculas-anime/") )

    #itemlist.append( Item(channel=CHANNELNAME, title="Buscar"                                , action="search"             , url=""                                       , folder=True) )
    
    return itemlist

# TODO: No compatible con canal genérico aún
def search(params,url,category):
    logger.info("[cinetube.py] search")

    buscador.listar_busquedas(params,url,category)

# TODO: No compatible con canal genérico aún
def searchresults(params,tecleado,category):
    logger.info("[cinetube.py] searchresults")
    
    buscador.salvar_busquedas(params,tecleado,category)
    tecleado = tecleado.replace(" ", "+")
    url = "http://www.cinetube.es/buscar/peliculas/?palabra="+tecleado+"&categoria=&valoracion="
    itemlist = getsearchresults(params,url,category)
    xbmctools.renderItems(itemlist, params, url, category)

# TODO: No compatible con canal genérico aún
def getsearchresults(params,url,category):
    logger.info("[cinetube.py] getsearchresults")

    if (not url.startswith("http://")):
        url = "http://www.cinetube.es/buscar/peliculas/?palabra="+url+"&categoria=&valoracion="

    return getlistpeliconcaratula(params,url,category)

def listpeliconcaratula(item):
    logger.info("[cinetube.py] listpeliconcaratula")

    url = item.url

    # Descarga la página
    data = scrapertools.cachePage(url)

    # Extrae las entradas
    '''
    <!--PELICULA-->
    <div class="peli_item textcenter">
    <div class="pelicula_img"><a href='/peliculas/thriller/ver-pelicula-un-segundo-despues-2.html' >
    <img src="http://caratulas.cinetube.es/pelis/7058.jpg" alt="Un segundo despu&eacute;s 2" /></a>
    </div><a href="/peliculas/thriller/ver-pelicula-un-segundo-despues-2.html" ><div class="dvdrip"></div></a><a href='/peliculas/thriller/ver-pelicula-un-segundo-despues-2.html' ><p class="white">Un segundo despu&eacute;s 2</p></a><p><span class="rosa">DVD-RIP</span></p><div class="icos_lg"><img src="http://caratulas.cinetube.es/img/cont/espanol.png" alt="espanol" /><img src="http://caratulas.cinetube.es/img/cont/megavideo.png" alt="" /><img src="http://caratulas.cinetube.es/img/cont/ddirecta.png" alt="descarga directa" /> </div>
    </div>
    <!--FIN PELICULA-->
    '''
    # listado alfabetico
    '''
    <!--PELICULA-->
    <div class="peli_item textcenter">
    <div class="pelicula_img"><a href="/peliculas/musical/ver-pelicula-a-chorus-line.html">
    <img src="http://caratulas.cinetube.es/pelis/246.jpg" alt="A Chorus Line" /></a>
    </div>
    <a href="/peliculas/musical/ver-pelicula-a-chorus-line.html"><p class="white">A Chorus Line</p></a>
    <p><span class="rosa">DVD-RIP</span></p><div class="icos_lg"><img src="http://caratulas.cinetube.es/img/cont/espanol.png" alt="espanol" /><img src="http://caratulas.cinetube.es/img/cont/megavideo.png" alt="" /><img src="http://caratulas.cinetube.es/img/cont/ddirecta.png" alt="descarga directa" /> </div>                                    </div>
    <!--FIN PELICULA-->
    '''
    patronvideos  = '<!--PELICULA-->[^<]+'
    patronvideos += '<div class="peli_item textcenter">[^<]+'
    patronvideos += '<div class="pelicula_img"><a[^<]+'
    patronvideos += '<img src=["|\']([^"]+?)["|\'][^<]+</a>[^<]+'
    patronvideos += '</div[^<]+<a href=["|\']([^"]+?)["|\'].*?<p class="white">([^<]+)</p>.*?<p><span class="rosa">([^>]+)</span></p><div class="icos_lg">(.*?)</div>'

    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    if DEBUG: scrapertools.printMatches(matches)

    itemlist = []
    for match in matches:
        scrapedtitle = match[2] + " [" + match[3] + "]"
        matchesconectores = re.compile('<img.*?alt="([^"]*)"',re.DOTALL).findall(match[4])
        conectores = ""
        for matchconector in matchesconectores:
            logger.info("matchconector="+matchconector)
            if matchconector=="":
                matchconector = "megavideo"
            conectores = conectores + matchconector + "/"
        if len(matchesconectores)>0:
            scrapedtitle = scrapedtitle + " (" + conectores[:-1] + ")"
        scrapedtitle = scrapedtitle.replace("megavideo/megavideo","megavideo")
        scrapedtitle = scrapedtitle.replace("descarga directa","DD")

        # Convierte desde UTF-8 y quita entidades HTML
        try:
            scrapedtitle = unicode( scrapedtitle, "utf-8" ).encode("iso-8859-1")
        except:
            pass
        scrapedtitle = scrapertools.entityunescape(scrapedtitle)

        # procesa el resto
        scrapedplot = ""

        scrapedurl = urlparse.urljoin("http://www.cinetube.es/",match[1])
        scrapedthumbnail = match[0]
        if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

        # Añade al listado de XBMC
        itemlist.append( Item(channel=CHANNELNAME, action="findvideos", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )

    # Extrae el paginador
    #<li class="navs"><a class="pag_next" href="/peliculas-todas/2.html"></a></li>
    patronvideos  = '<li class="navs"><a class="pag_next" href="([^"]+)"></a></li>'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    if len(matches)>0:
        scrapedurl = urlparse.urljoin(url,matches[0])
        itemlist.append( Item(channel=CHANNELNAME, action="listpeliconcaratula", title="!Página siguiente" , url=scrapedurl , folder=True) )

    return itemlist

def listpelisincaratula(item):
    logger.info("[cinetube.py] listpelisincaratula")

    url = item.url
    
    # ------------------------------------------------------
    # Descarga la página
    # ------------------------------------------------------
    data = scrapertools.cachePage(url)
    #logger.info(data)

    # ------------------------------------------------------
    # Extrae las entradas
    # ------------------------------------------------------
    '''
    <!--SERIE-->
    <div class="pelicula_bar_border">
    <div class="pelicula_bar series iframe3">
    <ul class="tabs-nav" id="video-1687">
    <li><span style="cursor:pointer;" class="peli_ico_1 bold" onclick="location.href='/peliculas/drama/ver-pelicula-belleza-robada.html'">Belleza robada </a></span></li>
    <li><a class="peli_ico_3" style="margin-left:10px;" href="/peliculas/drama/ver-pelicula-belleza-robada.html"><span>&nbsp;Ver ficha</span></a></li>
    </ul>
    </div>
    <div id="p_ver1" class="peli_bg1" style="display:none;">
    &nbsp;
    </div>
    </div>
    '''
    '''
    <!--SERIE-->
    <div class="pelicula_bar_border">
    <div class="pelicula_bar series iframe3">
    <ul class="tabs-nav" id="video-1692">
    <li><span style="cursor:pointer;" class="peli_ico_1 bold" onclick="location.href='/peliculas/terror/ver-pelicula-bendicion-mortal.html'">Bendici&oacute;n mortal </a></span></li>
    <li><a class="peli_ico_3" style="margin-left:10px;" href="/peliculas/terror/ver-pelicula-bendicion-mortal.html"><span>&nbsp;Ver ficha</span></a></li>
    </ul>
    </div>
    <div id="p_ver1" class="peli_bg1" style="display:none;">
    &nbsp;
    </div>
    </div>
    '''
    patronvideos  = '<!--SERIE-->[^<]+'
    patronvideos += '<div class="pelicula_bar_border">[^<]+'
    patronvideos += '<div class="pelicula_bar series iframe3">[^<]+'
    patronvideos += '<ul class="tabs-nav" id="([^"]+)">[^<]+'
    patronvideos += '<li><span[^>]+?>.+?<a[^>]+?>([^<]+)</a></span></li>[^<]+'
    patronvideos += '<li><a.*?href="([^"]+)"'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)
    itemlist = []
    for match in matches:
        try:
            scrapedtitle = unicode( match[1], "utf-8" ).encode("iso-8859-1")
        except:
            scrapedtitle = match[1]
        scrapedtitle = scrapertools.entityunescape(scrapedtitle)
        scrapedplot = ""
        scrapedurl = urlparse.urljoin("http://www.cinetube.es/",match[2])
        scrapedthumbnail = ""
        if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

        itemlist.append( Item(channel=CHANNELNAME, action="findvideos", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )

    # ------------------------------------------------------
    # Extrae el paginador
    # ------------------------------------------------------
    #<li class="navs"><a class="pag_next" href="/peliculas-todas/2.html"></a></li>
    patronvideos  = '<li class="navs"><a class="pag_next" href="([^"]+)"></a></li>'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    if len(matches)>0:
        scrapedurl = urlparse.urljoin(url,matches[0])
        itemlist.append( Item(channel=CHANNELNAME, action="listpelisincaratula", title="!Página siguiente" , url=scrapedurl , folder=True) )

    return itemlist

def listalfabetico(item):
    logger.info("[cinetube.py] listalfabetico")
    
    itemlist = []
    itemlist.append( Item(channel=CHANNELNAME, action="listpeliconcaratula" , title="0-9", url="http://www.cinetube.es/peliculas/0-9/"))
    itemlist.append( Item(channel=CHANNELNAME, action="listpeliconcaratula" , title="A"  , url="http://www.cinetube.es/peliculas/A/"))
    itemlist.append( Item(channel=CHANNELNAME, action="listpeliconcaratula" , title="B"  , url="http://www.cinetube.es/peliculas/B/"))
    itemlist.append( Item(channel=CHANNELNAME, action="listpeliconcaratula" , title="C"  , url="http://www.cinetube.es/peliculas/C/"))
    itemlist.append( Item(channel=CHANNELNAME, action="listpeliconcaratula" , title="D"  , url="http://www.cinetube.es/peliculas/D/"))
    itemlist.append( Item(channel=CHANNELNAME, action="listpeliconcaratula" , title="E"  , url="http://www.cinetube.es/peliculas/E/"))
    itemlist.append( Item(channel=CHANNELNAME, action="listpeliconcaratula" , title="F"  , url="http://www.cinetube.es/peliculas/F/"))
    itemlist.append( Item(channel=CHANNELNAME, action="listpeliconcaratula" , title="G"  , url="http://www.cinetube.es/peliculas/G/"))
    itemlist.append( Item(channel=CHANNELNAME, action="listpeliconcaratula" , title="H"  , url="http://www.cinetube.es/peliculas/H/"))
    itemlist.append( Item(channel=CHANNELNAME, action="listpeliconcaratula" , title="I"  , url="http://www.cinetube.es/peliculas/I/"))
    itemlist.append( Item(channel=CHANNELNAME, action="listpeliconcaratula" , title="J"  , url="http://www.cinetube.es/peliculas/J/"))
    itemlist.append( Item(channel=CHANNELNAME, action="listpeliconcaratula" , title="K"  , url="http://www.cinetube.es/peliculas/K/"))
    itemlist.append( Item(channel=CHANNELNAME, action="listpeliconcaratula" , title="L"  , url="http://www.cinetube.es/peliculas/L/"))
    itemlist.append( Item(channel=CHANNELNAME, action="listpeliconcaratula" , title="M"  , url="http://www.cinetube.es/peliculas/M/"))
    itemlist.append( Item(channel=CHANNELNAME, action="listpeliconcaratula" , title="N"  , url="http://www.cinetube.es/peliculas/N/"))
    itemlist.append( Item(channel=CHANNELNAME, action="listpeliconcaratula" , title="O"  , url="http://www.cinetube.es/peliculas/O/"))
    itemlist.append( Item(channel=CHANNELNAME, action="listpeliconcaratula" , title="P"  , url="http://www.cinetube.es/peliculas/P/"))
    itemlist.append( Item(channel=CHANNELNAME, action="listpeliconcaratula" , title="Q"  , url="http://www.cinetube.es/peliculas/Q/"))
    itemlist.append( Item(channel=CHANNELNAME, action="listpeliconcaratula" , title="R"  , url="http://www.cinetube.es/peliculas/R/"))
    itemlist.append( Item(channel=CHANNELNAME, action="listpeliconcaratula" , title="S"  , url="http://www.cinetube.es/peliculas/S/"))
    itemlist.append( Item(channel=CHANNELNAME, action="listpeliconcaratula" , title="T"  , url="http://www.cinetube.es/peliculas/T/"))
    itemlist.append( Item(channel=CHANNELNAME, action="listpeliconcaratula" , title="U"  , url="http://www.cinetube.es/peliculas/U/"))
    itemlist.append( Item(channel=CHANNELNAME, action="listpeliconcaratula" , title="V"  , url="http://www.cinetube.es/peliculas/V/"))
    itemlist.append( Item(channel=CHANNELNAME, action="listpeliconcaratula" , title="W"  , url="http://www.cinetube.es/peliculas/W/"))
    itemlist.append( Item(channel=CHANNELNAME, action="listpeliconcaratula" , title="X"  , url="http://www.cinetube.es/peliculas/X/"))
    itemlist.append( Item(channel=CHANNELNAME, action="listpeliconcaratula" , title="Y"  , url="http://www.cinetube.es/peliculas/Y/"))
    itemlist.append( Item(channel=CHANNELNAME, action="listpeliconcaratula" , title="Z"  , url="http://www.cinetube.es/peliculas/Z/"))

    return itemlist
    
def listalfabeticoseries(item):

    xbmctools.addnewfolder( CHANNELNAME , "listserieconcaratula" , category , "0-9"  ,"http://www.cinetube.es/series/0-9/","","")
    xbmctools.addnewfolder( CHANNELNAME , "listserieconcaratula" , category , "A"  ,"http://www.cinetube.es/series/A/","","")
    xbmctools.addnewfolder( CHANNELNAME , "listserieconcaratula" , category , "B"  ,"http://www.cinetube.es/series/B/","","")
    xbmctools.addnewfolder( CHANNELNAME , "listserieconcaratula" , category , "C"  ,"http://www.cinetube.es/series/C/","","")
    xbmctools.addnewfolder( CHANNELNAME , "listserieconcaratula" , category , "D"  ,"http://www.cinetube.es/series/D/","","")
    xbmctools.addnewfolder( CHANNELNAME , "listserieconcaratula" , category , "E"  ,"http://www.cinetube.es/series/E/","","")
    xbmctools.addnewfolder( CHANNELNAME , "listserieconcaratula" , category , "F"  ,"http://www.cinetube.es/series/F/","","")
    xbmctools.addnewfolder( CHANNELNAME , "listserieconcaratula" , category , "G"  ,"http://www.cinetube.es/series/G/","","")
    xbmctools.addnewfolder( CHANNELNAME , "listserieconcaratula" , category , "H"  ,"http://www.cinetube.es/series/H/","","")
    xbmctools.addnewfolder( CHANNELNAME , "listserieconcaratula" , category , "I"  ,"http://www.cinetube.es/series/I/","","")
    xbmctools.addnewfolder( CHANNELNAME , "listserieconcaratula" , category , "J"  ,"http://www.cinetube.es/series/J/","","")
    xbmctools.addnewfolder( CHANNELNAME , "listserieconcaratula" , category , "K"  ,"http://www.cinetube.es/series/K/","","")
    xbmctools.addnewfolder( CHANNELNAME , "listserieconcaratula" , category , "L"  ,"http://www.cinetube.es/series/L/","","")
    xbmctools.addnewfolder( CHANNELNAME , "listserieconcaratula" , category , "M"  ,"http://www.cinetube.es/series/M/","","")
    xbmctools.addnewfolder( CHANNELNAME , "listserieconcaratula" , category , "N"  ,"http://www.cinetube.es/series/N/","","")
    xbmctools.addnewfolder( CHANNELNAME , "listserieconcaratula" , category , "O"  ,"http://www.cinetube.es/series/O/","","")
    xbmctools.addnewfolder( CHANNELNAME , "listserieconcaratula" , category , "P"  ,"http://www.cinetube.es/series/P/","","")
    xbmctools.addnewfolder( CHANNELNAME , "listserieconcaratula" , category , "Q"  ,"http://www.cinetube.es/series/Q/","","")
    xbmctools.addnewfolder( CHANNELNAME , "listserieconcaratula" , category , "R"  ,"http://www.cinetube.es/series/R/","","")
    xbmctools.addnewfolder( CHANNELNAME , "listserieconcaratula" , category , "S"  ,"http://www.cinetube.es/series/S/","","")
    xbmctools.addnewfolder( CHANNELNAME , "listserieconcaratula" , category , "T"  ,"http://www.cinetube.es/series/T/","","")
    xbmctools.addnewfolder( CHANNELNAME , "listserieconcaratula" , category , "U"  ,"http://www.cinetube.es/series/U/","","")
    xbmctools.addnewfolder( CHANNELNAME , "listserieconcaratula" , category , "V"  ,"http://www.cinetube.es/series/V/","","")
    xbmctools.addnewfolder( CHANNELNAME , "listserieconcaratula" , category , "W"  ,"http://www.cinetube.es/series/W/","","")
    xbmctools.addnewfolder( CHANNELNAME , "listserieconcaratula" , category , "X"  ,"http://www.cinetube.es/series/X/","","")
    xbmctools.addnewfolder( CHANNELNAME , "listserieconcaratula" , category , "Y"  ,"http://www.cinetube.es/series/Y/","","")
    xbmctools.addnewfolder( CHANNELNAME , "listserieconcaratula" , category , "Z"  ,"http://www.cinetube.es/series/Z/","","")

    # Cierra el directorio
    xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
    xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

def listtemporadacaratula(item):
    logger.info("[cinetube.py] listtemporadacaratula")
    itemlist = []

    # Descarga la página
    data = scrapertools.cachePage(item.url)

    # Extrae las entradas
    '''
    <li>
    <a href="/series/en-tierra-de-lobos/temporada-1/capitulo-12/"><img src="http://caratulas.cinetube.es/series/8912.jpg" alt="peli" /></a>
    <div class="icos_lg"><img src="http://caratulas.cinetube.es/img/cont/espanol.png" alt="espanol" /> <img src="http://caratulas.cinetube.es/img/cont/megavideo.png" alt="megavideo.png" /> <img src="http://caratulas.cinetube.es/img/cont/ddirecta.png" alt="descarga directa" /> <p><span class="rosa"></span></p></div>
    <p class="tit_ficha"><a class="tit_ficha" title="Ver serie Tierra de lobos" href="/series/en-tierra-de-lobos/temporada-1/capitulo-12/">Tierra de lobos </a></p>
    <p class="tem_fich">1a Temporada - Cap 12</p>
    </li>
    '''
    patronvideos  = '<li>[^<]+'
    patronvideos += '<a href="([^"]+)"><img src="([^"]+)"[^>]+></a>[^>]+'
    patronvideos += '<div class="icos_lg">(.*?)</div>.*?'
    patronvideos += '<p class="tit_ficha"><a[^>]+>([^<]+)</a></p>[^<]+'
    patronvideos += '<p class="tem_fich">([^<]+)</p>'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    if DEBUG: scrapertools.printMatches(matches)

    for match in matches:
        # Titulo
        scrapedtitle = match[3].strip()+" - "+match[4].strip()
        matchesconectores = re.compile('<img.*?alt="([^"]*)"',re.DOTALL).findall(match[2])
        conectores = ""
        for matchconector in matchesconectores:
            logger.info("matchconector="+matchconector)
            if matchconector=="":
                matchconector = "megavideo"
            conectores = conectores + matchconector + "/"
        if len(matchesconectores)>0:
            scrapedtitle = scrapedtitle + " (" + conectores[:-1] + ")"

        scrapedtitle = scrapertools.entityunescape(scrapedtitle)

        scrapedplot = ""
        scrapedurl = urlparse.urljoin(item.url,match[0])
        scrapedthumbnail = match[1]
        if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

        itemlist.append( Item(channel=CHANNELNAME, action="findvideos", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )

    return itemlist

def listserieconcaratula(params,url,category):
    logger.info("[cinetube.py] listserieconcaratula")

    # Descarga la página
    data = scrapertools.cachePage(url)
    #logger.info(data)

    # Extrae las entradas
    '''
    <li>
    <a href="/series/las-reglas-del-juego-leverage/temporada-3/capitulo-15/"><img src="http://caratulas.cinetube.es/series/166.jpg" alt="peli" /></a>
    <div class="icos_lg"><img src="http://caratulas.cinetube.es/img/cont/sub.png" alt="sub" /> <img src="http://caratulas.cinetube.es/img/cont/megavideo.png" alt="megavideo.png" /> <img src="http://caratulas.cinetube.es/img/cont/ddirecta.png" alt="descarga directa" /> <p><span class="rosa"></span></p></div>                                        <p class="tit_ficha"><a class="tit_ficha" title="Ver serie Las reglas del juego (Leverage)" href="/series/las-reglas-del-juego-leverage/temporada-3/capitulo-15/">Las reglas del juego (Leverage) </a></p>
    <p class="tem_fich">3a Temporada - Cap 15</p>
    </li>
    '''
    patronvideos  = '<li>[^<]+'
    patronvideos += '<a href="([^"]+)"><img src="([^"]+)"[^>]+></a>.*?'
    patronvideos += '<div class="icos_lg">(.*?)</div>[^<]+'
    patronvideos += '<p class="tem_ficha">([^<]+)</p>[^<]+'
    patronvideos += '</li>'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    if DEBUG:
        scrapertools.printMatches(matches)

    for match in matches:
        # Titulo
        scrapedtitle = match[3].strip()
        matchesconectores = re.compile('<img.*?alt="([^"]*)"',re.DOTALL).findall(match[2])
        conectores = ""
        for matchconector in matchesconectores:
            logger.info("matchconector="+matchconector)
            if matchconector=="":
                matchconector = "megavideo"
            conectores = conectores + matchconector + "/"
        if len(matchesconectores)>0:
            scrapedtitle = scrapedtitle + " (" + conectores[:-1] + ")"

        # Convierte desde UTF-8 y quita entidades HTML
        try:
            scrapedtitle = unicode( scrapedtitle, "utf-8" ).encode("iso-8859-1")
        except:
            pass
        scrapedtitle = scrapertools.entityunescape(scrapedtitle)


        # procesa el resto
        scrapedplot = ""

        scrapedurl = urlparse.urljoin(url,match[0])
        scrapedthumbnail = match[1]
        if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

        # Añade al listado de XBMC
        xbmctools.addnewfolder( CHANNELNAME , "findvideos" , category , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )

    # ------------------------------------------------------
    # Extrae el paginador
    # ------------------------------------------------------
    #<li class="navs"><a class="pag_next" href="/peliculas-todas/2.html"></a></li>
    patronvideos  = '<li class="navs"><a class="pag_next" href="([^"]+)"></a></li>'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    if len(matches)>0:
        xbmctools.addnewfolder( CHANNELNAME , "listserieconcaratula" , category , "!Página siguiente" , urlparse.urljoin(url,matches[0]) , "", "" )

    # Label (top-right)...
    xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
    xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

def listseriesincaratula(params,url,category):
    logger.info("[cinetube.py] listseriesincaratula")
    # ------------------------------------------------------
    # Descarga la página
    # ------------------------------------------------------
    data = scrapertools.cachePage(url)
    #logger.info(data)

    # ------------------------------------------------------
    # Extrae las entradas
    # ------------------------------------------------------
    '''
    <!--SERIE-->
    <div class="pelicula_bar_border">
    <div class="pelicula_bar series iframe3">
    <ul class="tabs-nav" id="video-1687">
    <li><span style="cursor:pointer;" class="peli_ico_1 bold" onclick="location.href='/peliculas/drama/ver-pelicula-belleza-robada.html'">Belleza robada </a></span></li>
    <li><a class="peli_ico_3" style="margin-left:10px;" href="/peliculas/drama/ver-pelicula-belleza-robada.html"><span>&nbsp;Ver ficha</span></a></li>
    </ul>
    </div>
    <div id="p_ver1" class="peli_bg1" style="display:none;">
    &nbsp;
    </div>
    </div>
    '''
    '''
    <!--SERIE-->
    <div class="pelicula_bar_border">
    <div class="pelicula_bar series iframe3">
    <ul class="tabs-nav" id="video-1692">
    <li><span style="cursor:pointer;" class="peli_ico_1 bold" onclick="location.href='/peliculas/terror/ver-pelicula-bendicion-mortal.html'">Bendici&oacute;n mortal </a></span></li>
    <li><a class="peli_ico_3" style="margin-left:10px;" href="/peliculas/terror/ver-pelicula-bendicion-mortal.html"><span>&nbsp;Ver ficha</span></a></li>
    </ul>
    </div>
    <div id="p_ver1" class="peli_bg1" style="display:none;">
    &nbsp;
    </div>
    </div>
    '''
    patronvideos  = '<!--SERIE-->[^<]+'
    patronvideos += '<div class="pelicula_bar_border">[^<]+'
    patronvideos += '<div class="pelicula_bar series iframe3">[^<]+'
    patronvideos += '<ul class="tabs-nav" id="([^"]+)">[^<]+'
    patronvideos += '<li><span[^>]+>([^<]+)</a></span></li>[^<]+'
    patronvideos += '<li><a.*?href="([^"]+)"'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for match in matches:
        # Titulo
        try:
            scrapedtitle = unicode( match[1], "utf-8" ).encode("iso-8859-1")
        except:
            scrapedtitle = match[1]
        scrapedtitle = scrapertools.entityunescape(scrapedtitle)
        scrapedplot = ""
        scrapedurl = urlparse.urljoin(url,match[2])
        scrapedthumbnail = ""
        if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

        # Añade al listado de XBMC
        xbmctools.addnewfolder( CHANNELNAME , "findvideos" , category , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )

    # ------------------------------------------------------
    # Extrae el paginador
    # ------------------------------------------------------
    #<li class="navs"><a class="pag_next" href="/peliculas-todas/2.html"></a></li>
    patronvideos  = '<li class="navs"><a class="pag_next" href="([^"]+)"></a></li>'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    if len(matches)>0:
        xbmctools.addnewfolder( CHANNELNAME , "listseriesincaratula" , category , "!Página siguiente" , urlparse.urljoin(url,matches[0]) , "", "" )

    # Label (top-right)...
    xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_TITLE )
    xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

def listalfabeticodocumentales(params, url, category):
    addfolder("0-9","http://www.cinetube.es/subindices/idocumentalesnumero.html","list")
    addfolder("A","http://www.cinetube.es/subindices/idocumentalesa.html","list")
    addfolder("B","http://www.cinetube.es/subindices/idocumentalesb.html","list")
    addfolder("C","http://www.cinetube.es/subindices/idocumentalesc.html","list")
    addfolder("D","http://www.cinetube.es/subindices/idocumentalesd.html","list")
    addfolder("E","http://www.cinetube.es/subindices/idocumentalese.html","list")
    addfolder("F","http://www.cinetube.es/subindices/idocumentalesf.html","list")
    addfolder("G","http://www.cinetube.es/subindices/idocumentalesg.html","list")
    addfolder("H","http://www.cinetube.es/subindices/idocumentalesh.html","list")
    addfolder("I","http://www.cinetube.es/subindices/idocumentalesi.html","list")
    addfolder("J","http://www.cinetube.es/subindices/idocumentalesj.html","list")
    addfolder("K","http://www.cinetube.es/subindices/idocumentalesk.html","list")
    addfolder("L","http://www.cinetube.es/subindices/idocumentalesl.html","list")
    addfolder("M","http://www.cinetube.es/subindices/idocumentalesm.html","list")
    addfolder("N","http://www.cinetube.es/subindices/idocumentalesn.html","list")
    addfolder("O","http://www.cinetube.es/subindices/idocumentaleso.html","list")
    addfolder("P","http://www.cinetube.es/subindices/idocumentalesp.html","list")
    addfolder("Q","http://www.cinetube.es/subindices/idocumentalesq.html","list")
    addfolder("R","http://www.cinetube.es/subindices/idocumentalesr.html","list")
    addfolder("S","http://www.cinetube.es/subindices/idocumentaless.html","list")
    addfolder("T","http://www.cinetube.es/subindices/idocumentalest.html","list")
    addfolder("U","http://www.cinetube.es/subindices/idocumentalesu.html","list")
    addfolder("V","http://www.cinetube.es/subindices/idocumentalesv.html","list")
    addfolder("W","http://www.cinetube.es/subindices/idocumentalesw.html","list")
    addfolder("X","http://www.cinetube.es/subindices/idocumentalesx.html","list")
    addfolder("Y","http://www.cinetube.es/subindices/idocumentalesy.html","list")
    addfolder("Z","http://www.cinetube.es/subindices/idocumentalesz.html","list")

    # Cierra el directorio
    xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
    xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

def findvideos(item):
    logger.info("[cinetube.py] findvideos")

    url = item.url
    title = item.title
    thumbnail = item.thumbnail
    plot = item.plot

    # ------------------------------------------------------------------------------------
    # Descarga la pagina
    # ------------------------------------------------------------------------------------
    data = scrapertools.cachePage(url)
    #logger.info(data)
    
    # ------------------------------------------------------------------------------------
    # Busca el argumento
    # ------------------------------------------------------------------------------------
    patronvideos  = '<div class="ficha_des">(.*?)</div>'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    if len(matches)>0:
        plot = scrapertools.htmlclean(matches[0])
        logger.info("plot actualizado en detalle");
    else:
        logger.info("plot no actualizado en detalle");
    
    # ------------------------------------------------------------------------------------
    # Busca el thumbnail
    # ------------------------------------------------------------------------------------
    patronvideos  = '<div class="ficha_img pelicula_img">[^<]+'
    patronvideos += '<img src="([^"]+)"'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    if len(matches)>0:
        thumbnail = matches[0]
        logger.info("thumb actualizado en detalle");
    else:
        logger.info("thumb no actualizado en detalle");

    # ------------------------------------------------------------------------------------
    # Busca los enlaces a los mirrors, o a los capitulos de las series...
    # ------------------------------------------------------------------------------------
    #    url = "http://www.cinetube.es/inc/mostrar_contenido.php?sec=pelis_ficha&zona=online&id=video-4637"
    #patronvideos  = '<div class="ver_des_peli iframe2">[^<]+'
    #patronvideos += '<ul class="tabs-nav" id="([^"]+)">'
    #matches = re.compile(patronvideos,re.DOTALL).findall(data)
    #data = scrapertools.cachePage("http://www.cinetube.es/inc/mostrar_contenido.php?sec=pelis_ficha&zona=online&id="+matches[0])
    
    '''
    <div id="ficha_ver_peli">
    <div class="v_online">
    <h2>Ver online <span>El destino de Nunik</span></h2>
    <div class="opstions_pelicula_list">
    <div class="tit_opts" style="cursor:pointer;" onclick="location.href='http://www.cinetube.es/peliculas/drama/el-destino-de-nunik_espanol-dvd-rip-megavideo-6026.html'">
    <p>Mirror 1: Megavideo</p>
    <p><span>CALIDAD: DVD-RIP | IDIOMA: ESPA&Ntilde;OL</span></p>
    <p class="v_ico"><img src="http://caratulas.cinetube.es/img/cont/megavideo.png" alt="Megavideo" /></p>
    </div>
    <div class="tit_opts" style="cursor:pointer;" onclick="location.href='http://www.cinetube.es/peliculas/drama/el-destino-de-nunik_espanol-dvd-rip-megavideo-6027.html'">
    <p>Mirror 2: Megavideo</p>
    <p><span>CALIDAD: DVD-RIP | IDIOMA: ESPA&Ntilde;OL</span></p>
    <p class="v_ico"><img src="http://caratulas.cinetube.es/img/cont/megavideo.png" alt="Megavideo" /></p>
    </div>
    </div>
    </div>
    </div> 
    '''
    '''
    <div class="v_online">
    <h2>Ver online <span>Cantajuego 6</span></h2>
    <div class="opstions_pelicula_list"><div class="tit_opts"><a href="/peliculas/animacion-e-infantil/cantajuego-6_espanol-dvd-rip-megavideo-73371.html">
    <p>Mirror 1: Megavideo</p>
    <p><span>CALIDAD: DVD-RIP | IDIOMA: ESPA&Ntilde;OL</span></p>
    <p class="v_ico"><img src="http://caratulas.cinetube.es/img/cont/megavideo.png" alt="Megavideo" /></p>
    </a></div>                </div>
    </div>
    </div><br/><div id="ficha_desc_peli">
    <div class="v_online">
    <h2 class="ico_fuego">Descargar <span>Cantajuego 6</span></h2>
    <div class="opstions_pelicula_list"><div class="tit_opts"><a href="/peliculas/animacion-e-infantil/descargar-cantajuego-6_espanol-dvd-rip-megaupload-73372.html" target="_blank">
    <p>Mirror 1: Megaupload </p>
    <p><span>CALIDAD: DVD-RIP | IDIOMA: ESPA&Ntilde;OL </span></p>
    <p class="v_ico"><img src="http://caratulas.cinetube.es/img/cont/megaupload.png" alt="Megaupload" /></p>
    </a></div>
    </div>
    </div>
    </div>
    '''
    #patronvideos  = '<div class="tit_opts"><a href="([^"]+)">[^<]+'
    patronvideos = '<div class="tit_opts"><a href="([^"]+)".*?>[^<]+'
    patronvideos += '<p>([^<]+)</p>[^<]+'
    patronvideos += '<p><span>([^<]+)</span>'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)

    itemlist = []
    for match in matches:
        logger.info("Encontrado iframe mirrors "+match[0])
        # Lee el iframe
        mirror = urlparse.urljoin(url,match[0].replace(" ","%20"))
        req = urllib2.Request(mirror)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
        response = urllib2.urlopen(req)
        data=response.read()
        response.close()
        
        listavideos = servertools.findvideos(data)
        
        for video in listavideos:
            scrapedtitle = title.strip() + " " + match[1] + " " + match[2] + " " + video[0]
            scrapedurl = video[1]
            server = video[2]
            
            itemlist.append( Item(channel=CHANNELNAME, action="play" , title=scrapedtitle , url=scrapedurl, thumbnail=item.thumbnail, plot=item.plot, server=server, folder=False))

    return itemlist