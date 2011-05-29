# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para delatv
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#------------------------------------------------------------
import urlparse,urllib2,urllib,re
import os
import sys
import xbmc
import xbmcgui
import xbmcplugin

from core import scrapertools
from core import config
from core import logger
from core import xbmctools
from core.item import Item
from servers import servertools
from servers import vk

CHANNELNAME = "delatv"

# Traza el inicio del canal
logger.info("[delatv.py] init")

DEBUG = True

def mainlist(params,url,category):
    logger.info("[cinegratis.py] mainlist")

    # Añade al listado de XBMC
    xbmctools.addnewfolder( CHANNELNAME , "novedades" , category , "Novedades" ,"http://delatv.com/","","")
    xbmctools.addnewfolder( CHANNELNAME , "novedades" , category , "Estrenos" ,"http://delatv.com/categoria/estrenos","","")
    xbmctools.addnewfolder( CHANNELNAME , "CategoryList" , category , "Categorias" ,"http://delatv.com/","","")


    # Cierra el directorio
    xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
    xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

    
def novedades(params,url,category):
    logger.info("[delatv.py] novedades")

    # ------------------------------------------------------
    # Descarga la página
    # ------------------------------------------------------
    data = scrapertools.cachePage(url)
    #logger.info(data)

    # ------------------------------------------------------
    # Extrae las películas
    # ------------------------------------------------------
    #patron  = '<div class="thumb">[^<]+<a href="([^"]+)"><img src="([^"]+)".*?alt="([^"]+)"/></a>'
    patron  = '<div class="imagen">'
    patron += '<a title="([^"]+)"'
    patron += ' href="([^"]+)"><img.+?src="([^"]+)" /></a>.*?'
    patron += '<div class="sinopsis">[^<]+<p><p>(.+?)</p>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    if DEBUG: scrapertools.printMatches(matches)

    for match in matches:
        scrapedtitle = match[0]
        scrapedurl = match[1]
        scrapedthumbnail = match[2].replace(" ","%20")
        scrapedplot = match[3]
        if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")
        try:
            print scrapedtitle
            scrapedtitle = scrapedtitle.replace("Ã±","ñ")
            #scrapedtitle = unicode(scrapedtitle, "utf-8" )
            
        except:
            pass
        # Añade al listado de XBMC
        xbmctools.addnewfolder( CHANNELNAME , "listmirrors" , category , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )

    # ------------------------------------------------------
    # Extrae la página siguiente
    # ------------------------------------------------------
    #patron = '<a href="([^"]+)" >\&raquo\;</a>'
    patron  = "<span class='current'>[^<]+</span><a href='([^']+)'"
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
    xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
    xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

def CategoryList(params,url,category):
    logger.info("[delatv.py] CategoryList")

    # Descarga la página
    data = scrapertools.cachePage(url)
    #logger.info(data)

    patronvideos = '<div class="titulo">Generos</div>(.*?)</div>'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)
        
    # Patron de las entradas
    patronvideos  = '<a href="([^"]+)"[^>]+'          # URL
    patronvideos += ">(.+?)<"                                                         # TITULO
      
    matches = re.compile(patronvideos,re.DOTALL).findall(matches[0])
    scrapertools.printMatches(matches)

    # Añade las entradas encontradas
    for match in matches:
        # Atributos
        scrapedtitle = match[1]
        scrapedurl = urlparse.urljoin(url,match[0])
        scrapedthumbnail = ""
        scrapedplot = ""
        if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

        # Añade al listado de XBMC
        xbmctools.addnewfolder( CHANNELNAME , "novedades" , category , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )


    # Asigna el título, desactiva la ordenación, y cierra el directorio
    xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
    xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )


def listmirrors(params,url,category):
    logger.info("[delatv.py] listmirrors")

    title = urllib.unquote_plus( params.get("title") )
    title = title.replace("ñ","Ã±").decode("utf-8")
    thumbnail = urllib.unquote_plus( params.get("thumbnail") )
    plot = unicode( xbmc.getInfoLabel( "ListItem.Plot" ), "utf-8" )

    # Descarga la página de detalle
    # http://delatv.com/sorority-row/
    data = scrapertools.cachePage(url)
    #logger.info(data)
    
    # Extrae el argumento
    patron = '<div class="sinopsis">.*?<li>(.*?)</li>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    if len(matches)>0:
        plot = matches[0]

    # Extrae los enlaces a los vídeos (Megavídeo)
    '''
    <div class="div-servidores">
    <div class="servidores-titulo">Lista de servidores</div>
    <div class="servidores-fondo">
    <div class="boton-ver-pelicula">         <a href="http://delatv.com/modulos/player.php?url=dmlkZW8uYWsuZmFjZWJvb2suY29tL2Nmcy1hay1zbmM0LzMzMjU4LzI3Ny8xMDU1NTcwMzk0OTYwNjdfMjA5NzY=" target="_blank" class="boton-azul">Audio Latino - Parte 1</a>
    <a href="http://delatv.com/modulos/player.php?url=dmlkZW8uYWsuZmFjZWJvb2suY29tL2Nmcy1hay1hc2gyLzMzMjM2LzY4NS8xMDU1NTcxNDYxNjI3MjNfMzQ5ODk=" target="_blank" class="boton-azul">Audio Latino - Parte 2</a>
    <a href="http://delatv.com/modulos/player.php?url=dmlkZW8uYWsuZmFjZWJvb2suY29tL2Nmcy1hay1hc2gyLzMzMTU2LzcwLzEwNTU1NzE5NjE2MjcxOF8yOTA3MQ==" target="_blank" class="boton-azul">Audio Latino - Parte 3</a>
    <a href="http://delatv.com/modulos/player.php?url=dmlkZW8uYWsuZmFjZWJvb2suY29tL2Nmcy1hay1zbmM0LzMzMTE4LzcxNi8xMDU1NTcyMzI4MjkzODFfMjI0OTM=" target="_blank" class="boton-azul">Audio Latino - Parte 4</a>
    <a href="http://delatv.com/modulos/player.php?url=dmlkZW8uYWsuZmFjZWJvb2suY29tL2Nmcy1hay1hc2gyLzMzMzA4Lzk2Ni8xMDU1NTcyOTYxNjI3MDhfMzU3ODg=" target="_blank" class="boton-azul">Audio Latino - Parte 5</a>
    <a href="http://delatv.com/modulos/player.php?url=dmlkZW8uYWsuZmFjZWJvb2suY29tL2Nmcy1hay1zbmM0LzMzMjE2LzE3NS8xMDU1Njg0NTk0OTQ5MjVfNDE5NDE=" target="_blank" class="boton-azul">Audio Latino - Parte 6</a>
    <a href="http://delatv.com/modulos/player.php?url=dmlkZW8uYWsuZmFjZWJvb2suY29tL2Nmcy1hay1hc2gyLzMzMzA2LzgwNi8xMDU1NTc0OTYxNjI2ODhfNDcxNjc=" target="_blank" class="boton-azul">Audio Latino - Parte 7</a>
    <a href="http://delatv.com/modulos/player.php?url=dmlkZW8uYWsuZmFjZWJvb2suY29tL2Nmcy1hay1zbmM0LzMzMzI4Lzc2MS8xNTE5MzAzMTAyNjkzXzk2NDA=" target="_blank" class="boton-rojo">Subtitulado - Parte 1</a>
    <a href="http://delatv.com/modulos/player.php?url=dmlkZW8uYWsuZmFjZWJvb2suY29tL2Nmcy1hay1zbmM0LzMzMzI4LzY0MS8xNTE5MzAzMjIyNjk2XzQ4NzQw" target="_blank" class="boton-rojo">Subtitulado - Parte 2</a>
    <a href="http://delatv.com/modulos/player.php?url=dmlkZW8uYWsuZmFjZWJvb2suY29tL2Nmcy1hay1zbmM0LzMzMzI4LzgyNC8xNTE5MzAzNDIyNzAxXzI1MjQ0" target="_blank" class="boton-rojo">Subtitulado - Parte 3</a>
    <a href="http://delatv.com/modulos/player.php?url=dmlkZW8uYWsuZmFjZWJvb2suY29tL2Nmcy1hay1zbmM0LzMzMzI4Lzk4Ni8xNTE5MzAzNTAyNzAzXzUyMjQx" target="_blank" class="boton-rojo">Subtitulado - Parte 4</a>
    <a href="http://delatv.com/modulos/player.php?url=dmlkZW8uYWsuZmFjZWJvb2suY29tL2Nmcy1hay1hc2gyLzMzMzI4LzEwLzE1MTkzMDM3NDI3MDlfNjI5MjU=" target="_blank" class="boton-rojo">Subtitulado - Parte 5</a>
    <a href="http://delatv.com/modulos/player.php?url=dmlkZW8uYWsuZmFjZWJvb2suY29tL2Nmcy1hay1hc2gyLzMzMzI4LzQ3Ni8xNTE5MzA1MzQyNzQ5XzM2OQ==" target="_blank" class="boton-rojo">Subtitulado - Parte 6</a>
    <a href="http://delatv.com/modulos/player.php?url=dmlkZW8uYWsuZmFjZWJvb2suY29tL2Nmcy1hay1hc2gyLzMzMzI4LzUyLzE1MTkzMDU1MDI3NTNfNTAzNDk=" target="_blank" class="boton-rojo">Subtitulado - Parte 7</a>
    </div>
    '''

    patron = '<div class="titulo-servidores">Lista de Servidores</div>(.*?)</div>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)
    scrapedtitle = title
    scrapedthumbnail = thumbnail
    from core import downloadtools
    scrapedplot = downloadtools.limpia_nombre_excepto_1(plot)
    
    if len(matches)>0:
        data = matches[0]
        patron  = '<a href="([^"]+)"[^>]+>([^<]+)</a>'
        matches = re.compile(patron,re.DOTALL).findall(data)
        scrapertools.printMatches(matches)
        
        for match in matches:
            
            
            
            if match[0].strip().endswith(".html"):
                if "/vk/" in match[0]:  #http://delatv.com/vk/11223192/674072850/ml3mp2pm9v00nmp2/predators-online.html
                    #patron = "http\:\/\/delatv.com\/vk\/([^\/]+)\/([^\/]+)\/([^\/]+)\/[^\.]+\.html"
                    #matchesvk = re.compile(patron).findall(match[0].strip())
                    scrapedurl = match[0].strip() #"http://delatv.com/modulos/embed/vkontakteX.php?oid=%s&id=%s&hash=%s" %(matchesvk[0][0],matchesvk[0][1],matchesvk[0][2])
                    print "scrapedurl=["+scrapedplot+"]"
                    server = "Directo"
                    xbmctools.addnewvideo( CHANNELNAME , "play" , category ,server, scrapedtitle+" - %s [VK]" %match[1] , scrapedurl , scrapedthumbnail, scrapedplot )
            
                patron   = "http://delatv.com/([^/]+)/([^/]+)/[^\.]+.html"    #http://delatv.com/playlist/6917/el-equipo-a-online.html
                matches2 = re.compile(patron,re.DOTALL).findall(match[0].strip())
                                
                if matches2[0][0] == "playlist":
                    xmlurl = "http://delatv.com/xml/%s.xml" %matches2[0][1]
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
            elif "vk.php" in match[0].strip():
                scrapedurl = "http://delatv.com/modulos/embed/vkontakteX.php?%s" %match[0].split("?")[1]
                server = "Directo"
                xbmctools.addnewvideo( CHANNELNAME , "play" , category ,server, scrapedtitle+" - %s [VK]" %match[1] , scrapedurl.strip() , scrapedthumbnail, scrapedplot )

    # Cierra el directorio
    xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
    xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

def play(params,url,category):
    logger.info("[delatv.py] play")
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
    # http://delatv.com/modulos/player.php?url=dmlkZW8uYWsuZmFjZWJvb2suY29tL2Nmcy1hay1hc2gyLzMzMjM2LzY4NS8xMDU1NTcxNDYxNjI3MjNfMzQ5ODk=
    # http://delatv.com/modulos/embed/playerembed.php?url=dmlkZW8uYWsuZmFjZWJvb2suY29tL2Nmcy1hay1hc2gyLzMzMjM2LzY4NS8xMDU1NTcxNDYxNjI3MjNfMzQ5ODk=
    logger.info("[delatv.py] url="+url)
    
    ## --------------------------------------------------------------------------------------##
    #            Busca enlaces de videos para el servidor vkontakte.ru                        #
    ## --------------------------------------------------------------------------------------##
    #"http://vkontakte.ru/video_ext.php?oid=89710542&id=147003951&hash=28845bd3be717e11&hd=1
    
    
    if "vkontakteX.php" or "/vk/" in url:
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
            
            
            '''
            data2 = scrapertools.cachePage(matches[0])
            print data2
            patron  = "var video_host = '([^']+)'.*?"
            patron += "var video_uid = '([^']+)'.*?"
            patron += "var video_vtag = '([^']+)'.*?"
            patron += "var video_no_flv = ([^;]+);.*?"
            patron += "var video_max_hd = '([^']+)'"
            matches2 = re.compile(patron,re.DOTALL).findall(data2)
            if len(matches2)>0:    #http://cs12385.vkontakte.ru/u88260894/video/d09802a95b.360.mp4
                for match in matches2:
                    if match[3].strip() == "0":
                        tipo = "flv"
                        url = "%su%s/video/%s.%s" % (match[0],match[1],match[2],tipo)
                    
                    else:
                        tipo = "360.mp4"
                        url = "%su%s/video/%s.%s" % (match[0],match[1],match[2],tipo)
                        
            '''
    
    
    # Cierra dialogo
    dialogWait.close()
    del dialogWait

    if len(url)>0:
        
        logger.info("url="+url)
        xbmctools.playvideo(CHANNELNAME,server,url,category,title,thumbnail,plot)
    else:
        xbmctools.alertnodisponible()
