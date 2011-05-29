# -*- coding: utf-8 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para bancodeseries
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#------------------------------------------------------------
import urlparse,urllib2,urllib,re
import os
import sys

try:
    from core import logger
    from core import config
    from core import scrapertools
    from core.item import Item
    from servers import servertools
    from servers import vk
except:
    # En Plex Media server lo anterior no funciona...
    from Code.core import logger
    from Code.core import config
    from Code.core import scrapertools
    from Code.core.item import Item
    from Code.servers import servertools
    from Code.servers import vk

CHANNELNAME = "bancodeseries"
DEBUG = True

def isGeneric():
    return True

def mainlist(item):
    logger.info("[bancodeseries.py] mainlist")

    itemlist = []
    itemlist.append( Item(channel=CHANNELNAME, action="novedades"      , title="Novedades" , url="http://bancodeseries.com/"))
    itemlist.append( Item(channel=CHANNELNAME, action="novedades"      , title="Estrenos" , url="http://bancodeseries.com/taquilla/estrenos/"))
    itemlist.append( Item(channel=CHANNELNAME, action="ListaCat"       , title="Categorias" , url="http://bancodeseries.com/taquilla/estrenos/"))
    itemlist.append( Item(channel=CHANNELNAME, action="FullSeriesList" , title="Listado Completo de Series" , url="http://bancodeseries.com/"))

    return itemlist
    
def novedades(item):
    logger.info("[bancodeseries.py] novedades")

    itemlist = []
    
    # Extrae las entradas
    data = scrapertools.cachePage(item.url)
    patron  = '<div class="galleryitem">[^<]+'
    patron += '<h1>[^<]+</h1>[^<]+'
    patron += '<a href="([^"]+)">[^<]+<img src="([^"]+)" '
    patron += 'alt="([^"]+)"'
    matches = re.compile(patron,re.DOTALL).findall(data)
    if DEBUG: scrapertools.printMatches(matches)

    for match in matches:
        scrapedtitle = match[2]
        scrapedurl = match[0]
        scrapedthumbnail = match[1].replace(" ","%20")
        scrapedplot = ""
        if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")
        try:
            print scrapedtitle
            scrapedtitle = scrapedtitle.replace("ñ","?")
            #scrapedtitle = unicode(scrapedtitle, "utf-8" )
        except:
            pass
        itemlist.append( Item(channel=CHANNELNAME, action="listcapitulos" , title=scrapedtitle , url=scrapedurl, thumbnail=scrapedthumbnail, plot=scrapedplot))

    # Extrae la pagina siguiente
    patron  = 'class="current">[^<]+</span><a href="([^"]+)"'
    matches = re.compile(patron,re.DOTALL).findall(data)
    if DEBUG: scrapertools.printMatches(matches)

    for match in matches:
        scrapedtitle = "!Pagina siguiente"
        scrapedurl = match
        scrapedthumbnail = ""
        scrapedplot = ""
        if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")
        itemlist.append( Item(channel=CHANNELNAME, action="novedades" , title=scrapedtitle , url=scrapedurl, thumbnail=scrapedthumbnail, plot=scrapedplot))

    return itemlist

def FullSeriesList(item):
    logger.info("[bancodeseries.py] FullSeriesList")
    itemlist = []
    
    # Extrae las entradas
    data = scrapertools.cachePage(item.url)
    patronvideos  = "<a href='([^']+)' class='[^']+' title='[^']+' style='[^']+'"          # URL
    patronvideos += ">([^<]+)</a>"                                                         # TITULO
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    if DEBUG: scrapertools.printMatches(matches)

    for match in matches:
        scrapedtitle = match[1]
        scrapedurl = match[0]
        scrapedthumbnail = ""
        scrapedplot = ""
        if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")
        itemlist.append( Item(channel=CHANNELNAME, action="novedades" , title=scrapedtitle , url=scrapedurl, thumbnail=scrapedthumbnail, plot=scrapedplot))

    return itemlist

def ListaCat(item):
    logger.info("[bancodeseries.py] ListaCat")
    itemlist = []
    itemlist.append( Item(channel=CHANNELNAME, action="novedades"      , title="Acción"          , url="http://bancodeseries.com/taquilla/accion"))
    itemlist.append( Item(channel=CHANNELNAME, action="novedades"      , title="Ciencia-Ficción" , url="http://bancodeseries.com/taquilla/ciencia-ficcion"))
    itemlist.append( Item(channel=CHANNELNAME, action="novedades"      , title="Comedia"         , url="http://bancodeseries.com/taquilla/comedia"))
    itemlist.append( Item(channel=CHANNELNAME, action="novedades"      , title="Dibujos"         , url="http://bancodeseries.com/taquilla/dibujos"))
    itemlist.append( Item(channel=CHANNELNAME, action="novedades"      , title="Drama"           , url="http://bancodeseries.com/taquilla/drama"))
    itemlist.append( Item(channel=CHANNELNAME, action="novedades"      , title="Entretenimiento" , url="http://bancodeseries.com/taquilla/entretenimiento"))
    itemlist.append( Item(channel=CHANNELNAME, action="novedades"      , title="Estrenos"        , url="http://bancodeseries.com/taquilla/ultimos-extrenos"))
    itemlist.append( Item(channel=CHANNELNAME, action="novedades"      , title="Fantastico"      , url="http://bancodeseries.com/taquilla/fantastico"))
    itemlist.append( Item(channel=CHANNELNAME, action="novedades"      , title="Misterio"        , url="http://bancodeseries.com/taquilla/misterio"))
    itemlist.append( Item(channel=CHANNELNAME, action="novedades"      , title="Suspenso"        , url="http://bancodeseries.com/taquilla/suspenso"))
    itemlist.append( Item(channel=CHANNELNAME, action="novedades"      , title="Terror"          , url="http://bancodeseries.com/taquilla/terror"))
    itemlist.append( Item(channel=CHANNELNAME, action="novedades"      , title="Thriller"        , url="http://bancodeseries.com/taquilla/thriller"))
    itemlist.append( Item(channel=CHANNELNAME, action="FullSeriesList" , title="Todas las Series" , url="http://bancodeseries.com/"))
    return itemlist

def listcapitulos(item):
    logger.info("[bancodeseries.py] listcapitulos")

    itemlist = []
    thumbnail = item.thumbnail
    # Extrae el argumento
    data = scrapertools.cachePage(item.url)
    patron = '<div class="sinopsis">.*?<p><p>(.*?)</p>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    if len(matches)>0:
        plot = matches[0]
    else:
        plot=""    

    # Patron de las entradas
    patron = 'post_id="([^"]+)'
    matchesid = re.compile(patron,re.DOTALL).findall(data)
    
    '''
    <div class="capitulo" id="Adelanto">
    <h2><a class="title-capitulo">Adelanto Capitulo 1</a></h2>
    <div class="content blank_content"></div>
    </div>
    '''
    patron = '<div class="capitulo" id="([^"]+)">[^<]+'
    patron += '<h2><a class="title-capitulo">([^<]+)</a></h2>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)
    for match in matches:
        # Atributos
        scrapedtitle = match[1]
        #http://bancodeseries.com/capitulo.php?action=load_capitulo&id=Capitulo-1&post_id=1078&_=1285004415408
        scrapedurl = "http://bancodeseries.com/capitulo.php?action=load_capitulo&id=%s&post_id=%s" %(match[0],matchesid[0])
        scrapedthumbnail = thumbnail
        scrapedplot = plot
        if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

        itemlist.append( Item(channel=CHANNELNAME, action="listmirrors" , title=scrapedtitle , url=scrapedurl, thumbnail=scrapedthumbnail, plot=scrapedplot))

    return itemlist

def listmirrors(item):
    logger.info("[bancodeseries.py] listmirrors")
    itemlist = []

    title = item.title
    thumbnail = item.thumbnail
    plot = item.plot

    # Descarga la pagina de detalle
    # http://bancodeseries.com/sorority-row/
    data = scrapertools.cachePage(item.url)
    logger.info(data)
    
    # Extrae el argumento
    '''
    patron = '<div class="sinopsis">.*?<li>(.*?)</li>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    if len(matches)>0:
        plot = matches[0]
    '''
    # Extrae los enlaces a los videos (MV)
    scrapedthumbnail = thumbnail
    scrapedplot = plot
    patron  = '<a href="([^"]+)".+?>([^<]+)</a>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)
    
    for match in matches:
        scrapedtitle = title
        
        if match[0].endswith(".html"):
            if "/vk/" in match[0]:  #http://bancodeseries.com/vk/11223192/674072850/ml3mp2pm9v00nmp2/predators-online.html
                patron = "http\:\/\/bancodeseries.com\/vk\/([^\/]+)\/([^\/]+)\/([^\/]+)\/[^\.]+\.html"
                matchesvk = re.compile(patron).findall(match[0])
                scrapedurl = "http://bancodeseries.com/modulos/embed/vkontakteX.php?oid=%s&id=%s&hash=%s" %(matchesvk[0][0],matchesvk[0][1],matchesvk[0][2])
                server = "Directo"
                itemlist.append( Item(channel=CHANNELNAME, action="play" , server=server , title=scrapedtitle+" - %s [VK]" %match[1] , url=scrapedurl, thumbnail=scrapedthumbnail, plot=scrapedplot, folder=False))

            patron   = "http://bancodeseries.com/([^/]+)/([^/]+)/[^/]+/([^\.]+).html"    #http://bancodeseries.com/playlist/6917/el-equipo-a-online.html
            matches2 = re.compile(patron,re.DOTALL).findall(match[0])
                            
            if matches2[0][0] == "playlist":
                xmlurl = "http://bancodeseries.com/xml/%s.xml" %matches2[0][1]
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
                    itemlist.append( Item(channel=CHANNELNAME, action="play" , server=server , title=scrapedtitle+" - %s [Directo]" %xmlmatch[0] , url=scrapedurl, thumbnail=scrapedthumbnail, plot=scrapedplot, folder=False))

            elif matches2[0][0] == "flash":
                url = "http://bancodeseries.com/megaembed/%s/%s.html" %(matches2[0][1],matches2[0][2])
                data1 = scrapertools.cachePage(url)
                listavideos = servertools.findvideos(data1)

                for video in listavideos:
        
                    videotitle = video[0]
                    url = video[1]
                    server = video[2]
                    
                    from core import downloadtools
                    itemlist.append( Item(channel=CHANNELNAME, action="play" , server=server , title=scrapedtitle + " - " + videotitle , url=url, thumbnail=scrapedthumbnail, plot=downloadtools.limpia_nombre_excepto_1(plot), folder=False))

        elif "vk.php" in match[0]:
            scrapedurl = "http://bancodeseries.com/modulos/embed/vkontakteX.php?%s" %match[0].split("?")[1]
            server = "Directo"
            itemlist.append( Item(channel=CHANNELNAME, action="play" , server=server , title=scrapedtitle+" - %s [VK]" %match[1] , url=scrapedurl, thumbnail=scrapedthumbnail, plot=scrapedplot, folder=False  ))

    return itemlist

def play(item):
    logger.info("[bancodeseries.py] play url="+item.url)
    itemlist = []
    # Busca enlaces de videos para el servidor vkontakte.ru
    #"http://vkontakte.ru/video_ext.php?oid=89710542&id=147003951&hash=28845bd3be717e11&hd=1
    if "vkontakteX.php" in item.url:
        '''
        var video_host = 'http://cs12916.vkontakte.ru/';
        var video_uid = '87155741';
        var video_vtag = 'fc697084d3';
        var video_no_flv = 1;
        var video_max_hd = '1'
        '''
        data = scrapertools.cachePage(item.url)
        patronvideos = '<iframe src="(http://vk[^/]+/video_ext.php[^"]+)"'
        matches = re.compile(patronvideos,re.DOTALL).findall(data)
        if len(matches)>0:
            #print " encontro VKontakte.ru :%s" %matches[0]
            item.server = "Directo"
            item.url = vk.geturl(matches[0])

    itemlist.append( item )
    return itemlist