# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para sesionvip
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#------------------------------------------------------------
import urlparse,urllib2,urllib,re
import os
import sys
import xbmc
import xbmcgui
import xbmcplugin
import scrapertools
import megavideo
import servertools
import binascii
import xbmctools
import config
import logger

CHANNELNAME = "sesionvip"

# Esto permite su ejecución en modo emulado
try:
    pluginhandle = int( sys.argv[ 1 ] )
except:
    pluginhandle = ""

# Traza el inicio del canal
logger.info("[sesionvip.py] init")

DEBUG = True

def mainlist(params,url,category):
    logger.info("[sesionvip.py] mainlist")

    xbmctools.addnewfolder( CHANNELNAME , "newlist" , category , "Novedades","http://www.sesionvip.com/","","")
    xbmctools.addnewfolder( CHANNELNAME , "search"  , category , "Buscar","","","")

    # Label (top-right)...
    xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )
        
    # Disable sorting...
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )

    # End of directory...
    xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

def newlist(params,url,category):
    logger.info("[sesionvip.py] newlist")

    # Descarga la página
    data = scrapertools.cachePage(url)
    #logger.info(data)

    '''
    <div class="entry"><!-- Entry -->
    <h3 class="post-title">
    <a href="http://www.sesionvip.com/ver-online-millennium-2-la-chica-que-sonaba-con-una-cerilla-y-un-bidon-de-gasolina-en-alta-calidad" rel="bookmark">ver online millennium 2 La Chica Que Soñaba Con Una Cerilla Y Un Bidón De Gasolina en alta calidad</a>
    </h3>
    <p style="text-align: center;">YA DISPONIBLE &#8211; CALIDAD TS-SCREENER ALTO</p>
    <p style="text-align: center;"><img class="aligncenter size-medium wp-image-9125" title="peliculas online" src="http://www.sesionvip.com/wp-content/uploads/2009/08/1843318212-222x300.jpg" alt="peliculas online" width="222" height="300" /></p>
    <p style="text-align: left;"> <a href="http://www.sesionvip.com/ver-online-millennium-2-la-chica-que-sonaba-con-una-cerilla-y-un-bidon-de-gasolina-en-alta-calidad#more-9124" class="more-link">PULSA AQUI PARA <strong>Ver la pelicula online</strong></a></p>
    <div id="postmeta" class="postmetabox">
    Categoria: <a href="http://www.sesionvip.com/category/estrenos-online" title="Ver todas las entradas en Estrenos Online" rel="category tag">Estrenos Online</a>                                                <br/><a href="http://www.sesionvip.com/ver-online-millennium-2-la-chica-que-sonaba-con-una-cerilla-y-un-bidon-de-gasolina-en-alta-calidad#comments" title="Comentarios en ver online millennium 2 La Chica Que Soñaba Con Una Cerilla Y Un Bidón De Gasolina en alta calidad"><strong>Comments (3)</strong></a>
    </div>
    </div><!--/entry-->
    '''
    # Extrae las entradas (carpetas)
    
    patronvideos  = '<div class="entry"><!-- Entry -->(.*?)<!--/entry-->'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)
    for match in matches:
        logger.info("match="+match)
        nuevopatron = '<a href="([^"]+)" rel="bookmark">([^<]+)</a>'#<img.*?src="([^"]+)"'
        nuevomatches = re.compile(nuevopatron,re.DOTALL).findall(match)
        logger.info("len(nuevomatches)=%d" % len(nuevomatches))
        scrapertools.printMatches(nuevomatches)

        # Titulo
        scrapedtitle = nuevomatches[0][1]
        if not scrapedtitle.startswith("Descargar"):
            #Elimina todos los prefijos SEO
            scrapedtitle = xbmctools.unseo(scrapedtitle)
            # URL
            scrapedurl = urlparse.urljoin(url,nuevomatches[0][0])
            # Thumbnail
            scrapedthumbnail = ""#urlparse.urljoin(url,nuevomatches[2])
            # Argumento
            scrapedplot = ""

            # Depuracion
            if (DEBUG):
                logger.info("scrapedtitle="+scrapedtitle)
                logger.info("scrapedurl="+scrapedurl)
                logger.info("scrapedthumbnail="+scrapedthumbnail)

            # Añade al listado de XBMC
            xbmctools.addthumbnailfolder( CHANNELNAME , scrapedtitle , scrapedurl , scrapedthumbnail, "listmirrors" )

    # Página siguiente
    patronvideos  = '<div class="back"><a href="([^"]+)"'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for match in matches:
        # Titulo
        scrapedtitle = "Página siguiente"
        # URL
        scrapedurl = urlparse.urljoin(url,match)
        # Thumbnail
        scrapedthumbnail = ""
        # Argumento
        scrapedplot = ""

        # Depuracion
        if (DEBUG):
            logger.info("scrapedtitle="+scrapedtitle)
            logger.info("scrapedurl="+scrapedurl)
            logger.info("scrapedthumbnail="+scrapedthumbnail)

        # Añade al listado de XBMC
        xbmctools.addthumbnailfolder( CHANNELNAME , scrapedtitle , scrapedurl , scrapedthumbnail, "newlist" )

    # Label (top-right)...
    xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )

    # Disable sorting...
    xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )

    # End of directory...
    xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def listmirrors(params,url,category):
    logger.info("[sesionvip.py] detail")

    title = params.get("title")
    thumbnail = params.get("thumbnail")
    logger.info("[sesionvip.py] title="+title)
    logger.info("[sesionvip.py] thumbnail="+thumbnail)

    '''
    # Descarga la página y extrae el enlace a la siguiente pagina
    data = scrapertools.cachePage(url)
    patronvideos  = '<p style="text-align: center;">.*?<a href\="(http\://www.sesionvip.com/[^"]+)"'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)
    #logger.info(data)

    if len(matches)==0:
        xbmctools.alertnodisponible()
        return

    # Descarga la siguiente página y extrae el enlace a los mirrors
    url = matches[0]
    '''
    data = scrapertools.cachePage(url)

    # ------------------------------------------------------------------------------------
    # Busca los enlaces a los videos
    # ------------------------------------------------------------------------------------
    listavideos = servertools.findvideos(data)

    for video in listavideos:
        xbmctools.addvideo( CHANNELNAME , video[0] , video[1] , category , video[2] )
    # ------------------------------------------------------------------------------------

    # Label (top-right)...
    xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
        
    # Disable sorting...
    xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )

    # End of directory...
    xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def search(params,url,category):
    logger.info("[sesionvip.py] search")

    keyboard = xbmc.Keyboard('')
    keyboard.doModal()
    if (keyboard.isConfirmed()):
        tecleado = keyboard.getText()
        if len(tecleado)>0:
            #convert to HTML
            tecleado = tecleado.replace(" ", "+")
            searchUrl = "http://www.sesionvip.com/?s="+tecleado
            searchresults(params,searchUrl,category)

def performsearch(texto):
    logger.info("[sesionvip.py] performsearch")
    url = "http://www.sesionvip.com/?s="+texto

    # Descarga la página
    data = scrapertools.cachePage(url)

    # Extrae las entradas (carpetas)
    patronvideos  = '<div class="entry">.*?'
    patronvideos += '<a href="([^"]+)" rel="bookmark">([^<]+)</a>'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)
    
    resultados = []

    for match in matches:
        # Titulo
        scrapedtitle = match[1]
        if not scrapedtitle.startswith("Descargar"):
            scrapedtitle = xbmctools.unseo(scrapedtitle)
            scrapedurl = urlparse.urljoin(url,match[0])
            scrapedthumbnail = ""
            scrapedplot = ""

        if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

        # Añade al listado de XBMC
        resultados.append( [CHANNELNAME , "listmirrors" , "buscador" , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot ] )
        


    return resultados

def searchresults(params,url,category):
    logger.info("[sesionvip.py] searchresults")

    # Descarga la página
    data = scrapertools.cachePage(url)
    patronvideos  = '<div class="entry">.*?'
    patronvideos += '<a href="([^"]+)" rel="bookmark">([^<]+)</a>'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for match in matches:
        # Titulo
        scrapedtitle = match[1]
        if not scrapedtitle.startswith("Descargar"):
            #Elimina todos los prefijos SEO
            scrapedtitle = xbmctools.unseo(scrapedtitle)
            # URL
            scrapedurl = urlparse.urljoin(url,match[0])
            # Thumbnail
            scrapedthumbnail = ""
            # Argumento
            scrapedplot = ""

            # Depuracion
            if (DEBUG):
                logger.info("scrapedtitle="+scrapedtitle)
                logger.info("scrapedurl="+scrapedurl)
                logger.info("scrapedthumbnail="+scrapedthumbnail)

            # Añade al listado de XBMC
            xbmctools.addthumbnailfolder( CHANNELNAME , scrapedtitle , scrapedurl , scrapedthumbnail, "listmirrors" )

    # Label (top-right)...
    xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )

    # Disable sorting...
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )

    # End of directory...
    xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )


def play(params,url,category):
    logger.info("[sesionvip.py] play")

    title = unicode( xbmc.getInfoLabel( "ListItem.Title" ), "utf-8" )
    thumbnail = xbmc.getInfoImage( "ListItem.Thumb" )
    plot = unicode( xbmc.getInfoLabel( "ListItem.Plot" ), "utf-8" )
    server = params["server"]
    logger.info("[sesionvip.py] thumbnail="+thumbnail)
    logger.info("[sesionvip.py] server="+server)
    
    xbmctools.playvideo(CHANNELNAME,server,url,category,title,thumbnail,plot)
