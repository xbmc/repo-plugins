# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para pelispekes
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#------------------------------------------------------------
import urlparse,urllib2,urllib,re
import os
import sys

from core import scrapertools
from core import logger
from core import config
from core.item import Item
from core import xbmctools
from pelisalacarta import buscador

from servers import servertools
from servers import vk

import xbmc
import xbmcgui
import xbmcplugin

CHANNELNAME = "pelispekes"

# Esto permite su ejecución en modo emulado
try:
    pluginhandle = int( sys.argv[ 1 ] )
except:
    pluginhandle = ""

# Traza el inicio del canal
logger.info("[pelispekes.py] init")

DEBUG = True

def mainlist(params,url,category):
    logger.info("[pelispekes.py] mainlist")

    # Añade al listado de XBMC
    xbmctools.addnewfolder( CHANNELNAME , "novedades" , category , "Novedades" ,"http://pelispekes.com/","","")
    xbmctools.addnewfolder( CHANNELNAME , "Listcat" , category , "Categorias" ,"http://pelispekes.com/","","")

    # Cierra el directorio
    xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
    xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

    
def novedades(params,url,category):
    logger.info("[pelispekes.py] novedades")

    # ------------------------------------------------------
    # Descarga la página
    # ------------------------------------------------------
    data = scrapertools.cachePage(url)
    #logger.info(data)

    # ------------------------------------------------------
    # Extrae las películas
    # ------------------------------------------------------
    #patron  = '<div class="thumb">[^<]+<a href="([^"]+)"><img src="([^"]+)".*?alt="([^"]+)"/></a>'
    patron  = '<div class="post-content clearfix">.+?'
    patron += '<a href="([^"]+)">'           #Url
    patron += '<img src="([^"]+)".+?'        #Caratula
    patron += 'alt="([^"]+)"/></a>.+?'          #Titulo
    patron += '<p>([^<]+)</p>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    if DEBUG: scrapertools.printMatches(matches)

    for match in matches:
        scrapedtitle = match[2]
        scrapedurl = match[0]
        scrapedthumbnail = match[1].replace(" ","%20")
        scrapedplot = match[3]
        if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")
        try:
            print scrapedtitle
            scrapedtitle = scrapedtitle
            #scrapedtitle = unicode(scrapedtitle, "utf-8" )
            
        except:
            pass
        # Añade al listado de XBMC
        xbmctools.addnewfolder( CHANNELNAME , "listmirrors" , category , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )

    # ------------------------------------------------------
    # Extrae la página siguiente
    # ------------------------------------------------------
    #patron = '<a href="([^"]+)" >\&raquo\;</a>'
    patron  = "class='current'>[^<]+</span><a href='([^']+)'"
    matches = re.compile(patron,re.DOTALL).findall(data)
    if DEBUG:
        scrapertools.printMatches(matches)

    for match in matches:
        scrapedtitle = "!Pagina siguiente"
        scrapedurl = match
        scrapedthumbnail = ""
        scrapeddescription = ""
        if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

        # Añade al listado de XBMC
        xbmctools.addthumbnailfolder( CHANNELNAME , scrapedtitle , scrapedurl , scrapedthumbnail, "novedades" )

    # Label (top-right)...
    xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
    xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )
    xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def Listcat(params,url,category):
    logger.info("[pelispekes.py] Listcat")

    # Descarga la página
    data = scrapertools.cachePage(url)
    #logger.info(data)

    # Patron de las entradas
    #<li  class="cat-item cat-item-15"><a href="http://pelispekes.com/categoria/accion/" title="Ver todas las entradas archivadas en Accion" class="fadeThis"><span class="entry">Accion <span class="details inline">(39)</span></span></a><a class="rss bubble" href="http://pelispekes.com/categoria/accion/feed/" title="XML"></a>

    patron = '<li  class="[^"]+"><a href="([^"]+)"[^>]+>'
    patron += '<span class="entry">([^<]+)<span class="details inline">([^<]+)</span'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    # Añade las entradas encontradas
    for match in matches:
        # Atributos
        scrapedtitle = match[1]+match[2]
        scrapedurl = match[0]
        scrapedthumbnail = ""
        scrapedplot = ""
        if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

        # Añade al listado de XBMC
        xbmctools.addnewfolder( CHANNELNAME , "novedades" , category , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )

    # Asigna el título, desactiva la ordenación, y cierra el directorio
    xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
    xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )
    xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )
        

def listmirrors(params,url,category):
    logger.info("[pelispekes.py] listmirrors")

    title = unicode( xbmc.getInfoLabel( "ListItem.Title" ), "utf-8" )
    
    thumbnail = urllib.unquote_plus( params.get("thumbnail") )
    plot = unicode( xbmc.getInfoLabel( "ListItem.Plot" ), "utf-8" )
    

    # Descarga la página de detalle
    # http://pelispekes.com/sorority-row/
    data = scrapertools.cachePage(url)
    #logger.info(data)
    
    # Extrae el argumento
    patron = '<div class="sinopsis">.*?<li>(.*?)</li>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    if len(matches)>0:
        plot = matches[0]

    
    

    patron = '<div class="page-navigation">(.*?)</table>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)
    scrapedtitle = title
    scrapedthumbnail = thumbnail
    scrapedplot = plot
    
    if len(matches)>0:
        data = matches[0]
        patron  = '<a href="([^"]+)"[^>]+>([^<]+)</a>'
        matches = re.compile(patron,re.DOTALL).findall(data)
        scrapertools.printMatches(matches)
        
        for match in matches:
            
            
            
            if match[0].endswith(".html"):
                if "/vk/" in match[0]:  #http://pelispekes.com/vk/11223192/674072850/ml3mp2pm9v00nmp2/predators-online.html
                    patron = "http\:\/\/pelispekes.com\/vk\/([^\/]+)\/([^\/]+)\/([^\/]+)\/[^\.]+\.html"
                    matchesvk = re.compile(patron).findall(match[0])
                    scrapedurl = "http://pelispekes.com/modulos/embed/vkontakteX.php?oid=%s&id=%s&hash=%s" %(matchesvk[0][0],matchesvk[0][1],matchesvk[0][2])
                    server = "Directo"
                    xbmctools.addnewvideo( CHANNELNAME , "play" , category ,server, scrapedtitle+" - %s [VK]" %match[1] , scrapedurl , scrapedthumbnail, scrapedplot )
                              
            
            
                patron   = "http://pelispekes.com/([^/]+)/([^/]+)/[^\.]+.html"    #http://pelispekes.com/playlist/6917/el-equipo-a-online.html
                matches2 = re.compile(patron,re.DOTALL).findall(match[0])
                                
                if matches2[0][0] == "playlist":
                    xmlurl = "http://pelispekes.com/xml/%s.xml" %matches2[0][1]
                    xmldata = scrapertools.cachePage(xmlurl)
                    logger.info("xmldata="+xmldata)
                    patronvideos  = '<track>[^<]+'
                    patronvideos += '<creator>([^<]+)</creator>[^<]+'
                    patronvideos += '<location>([^<]+)</location>.*?'
                    patronvideos += '</track>'
                    matchesxml = re.compile(patronvideos,re.DOTALL).findall(xmldata)
                    scrapertools.printMatches(matchesxml)
                    for xmlmatch in matchesxml:
                        scrapedurl = xmlmatch[1]
                        #xbmctools.addnewvideo( CHANNELNAME , "play" , category , server , (title.strip() + " (%d) " + videotitle) % j , url , thumbnail , plot )
                        server = "Directo"
                        xbmctools.addnewvideo( CHANNELNAME , "play" , category ,server, scrapedtitle+" - %s [Directo]" %xmlmatch[0] , scrapedurl , scrapedthumbnail, scrapedplot )
                elif matches2[0][0] == "flash":
                    scrapedurl = matches2[0][1]
                    server = "Megavideo"
                    scrapedtitle = scrapedtitle+" - %s" %match[1]
                    scrapedtitle = scrapedtitle.replace("&ntilde;","ñ")
                    xbmctools.addnewvideo( CHANNELNAME , "play" , category ,server, scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )
            elif "vk.php" in match[0]:
                scrapedurl = "http://pelispekes.com/modulos/vkontakteX.php?%s" %match[0].split("?")[1]
                server = "Directo"
                xbmctools.addnewvideo( CHANNELNAME , "play" , category ,server, scrapedtitle+" - %s [VK]" %match[1] , scrapedurl , scrapedthumbnail, scrapedplot )
    
    patronvideos = '<iframe src="(http://vk[^/]+/video_ext.php[^"]+)"'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    if len(matches)>0:
        print " encontro VKontakte.ru :%s" %matches[0]
        scrapedurl =     vk.geturl(matches[0])    
        server = "Directo"
        xbmctools.addnewvideo( CHANNELNAME , "play" , category ,server, scrapedtitle+" - [VK]" , scrapedurl , scrapedthumbnail, scrapedplot )

    patronvideos = '<iframe src="(http://pelispekes.com/modulos/vkontakteX.php[^"]+)"'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    if len(matches)>0:
        print " encontro VKontakte.ru :%s" %matches[0]
        #scrapedtitle = scrapedtitle.replace("\xf3","ñ")
        scrapedurl =     matches[0]    
        server = "Directo"
        xbmctools.addnewvideo( CHANNELNAME , "play" , category ,server, scrapedtitle+" - [VK]" , scrapedurl , scrapedthumbnail, scrapedplot )    
    # ------------------------------------------------------------------------------------
    # Busca los enlaces a los videos en los servidores habilitados
    # ------------------------------------------------------------------------------------
    listavideos = servertools.findvideos(data)

    for video in listavideos:
        
        videotitle = video[0]
        url = video[1]
        server = video[2]
        from core import downloadtools
        scrapedplot = downloadtools.limpia_nombre_excepto_1(scrapedplot)
        xbmctools.addnewvideo( CHANNELNAME , "play" , category , server , scrapedtitle + " - " + videotitle , url , scrapedthumbnail , scrapedplot )
        
    # Cierra el directorio
    xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
    xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )
    xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def play(params,url,category):
    logger.info("[pelispekes.py] play")
    try:
        title = unicode( xbmc.getInfoLabel( "ListItem.Title" ), "utf-8" )
    except:
        title = urllib.unquote_plus( params.get("title") )
    thumbnail = urllib.unquote_plus( params.get("thumbnail") )
    plot = unicode( xbmc.getInfoLabel( "ListItem.Plot" ), "utf-8" )
    server = params.get("server")

    # Abre dialogo
    dialogWait = xbmcgui.DialogProgress()
    dialogWait.create( 'Accediendo al video...', title , plot )

    # Descarga la página del reproductor
    # http://pelispekes.com/modulos/player.php?url=dmlkZW8uYWsuZmFjZWJvb2suY29tL2Nmcy1hay1hc2gyLzMzMjM2LzY4NS8xMDU1NTcxNDYxNjI3MjNfMzQ5ODk=
    # http://pelispekes.com/modulos/embed/playerembed.php?url=dmlkZW8uYWsuZmFjZWJvb2suY29tL2Nmcy1hay1hc2gyLzMzMjM2LzY4NS8xMDU1NTcxNDYxNjI3MjNfMzQ5ODk=
    logger.info("[pelispekes.py] url="+url)
    
    ## --------------------------------------------------------------------------------------##
    #            Busca enlaces de videos para el servidor vkontakte.ru                        #
    ## --------------------------------------------------------------------------------------##
    #"http://vkontakte.ru/video_ext.php?oid=89710542&id=147003951&hash=28845bd3be717e11&hd=1
    
    
    if "vkontakteX.php" in url:
        data = scrapertools.cachePage(url)
        server = "Directo"
        '''
        var video_host = 'http://cs12916.vkontakte.ru/';
        var video_uid = '87155741';
        var video_vtag = 'fc697084d3';
        var video_no_flv = 1;
        var video_max_hd = '1'
        '''
        patronvideos = '<iframe src="(http://vk[^/]+/video_ext.php[^"]+)"'
        matches = re.compile(patronvideos,re.DOTALL).findall(data)
        if len(matches)>0:
            print " encontro VKontakte.ru :%s" %matches[0]
            url =     vk.geturl(matches[0])
            
    
    # Cierra dialogo
    dialogWait.close()
    del dialogWait

    if len(url)>0:
        
        logger.info("url="+url)
        xbmctools.playvideo(CHANNELNAME,server,url,category,title,thumbnail,plot)
    else:
        xbmctools.alertnodisponible()
