# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para cine15
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#------------------------------------------------------------
# Nota: Esta web sigue existiendo, pero ha dejado de actualizarse. Se elimina el canal.
import urlparse,urllib2,urllib,re

try:
    from core import logger
    from core import config
    from core import scrapertools
    from core.item import Item
    from servers import servertools
except:
    # En Plex Media server lo anterior no funciona...
    from Code.core import logger
    from Code.core import config
    from Code.core import scrapertools
    from Code.core.item import Item

CHANNELNAME = "cine15"
DEBUG = True

def isGeneric():
    return True

def mainlist(item):
    logger.info("[cine15.py] mainlist")

    itemlist = []
    itemlist.append( Item(channel=CHANNELNAME, action="listvideos" , title="Películas - Novedades"            ,url="http://www.cine15.com/"))
    itemlist.append( Item(channel=CHANNELNAME, action="peliscat"   , title="Películas - Lista por categorías" ,url="http://www.cine15.com/"))
    #itemlist.append( Item(channel=CHANNELNAME, action=""search"     , category , "Buscar"                           ,"","","")

    return itemlist

def search(item):
    from pelisalacarta import buscador
    buscador.listar_busquedas(params,url,category)

def searchresults(item):
    logger.info("[cine15.py] search")

    from pelisalacarta import buscador
    buscador.salvar_busquedas(params,url,category)
    tecleado = url.replace(" ", "+")
    searchUrl = "http://www.cine15.com/?s="+tecleado+"&x=0&y=0"
    listvideos(params,searchUrl,category)

def performsearch(texto):
    logger.info("[cine15.py] performsearch")
    url = "http://www.cine15.com/?s="+texto+"&x=0&y=0"

    # Descarga la página
    data = scrapertools.cachePage(url)

    # Extrae las entradas (carpetas)
    patronvideos  = '<div class="videoitem">[^<]+'
    patronvideos += '<div class="ratings">[^<]+'
    patronvideos += '<div id="post-ratings[^>]+><img[^>]+><img[^>]+><img[^>]+><img[^>]+><img[^>]+></div>[^<]+'
    patronvideos += '<div id="post-ratings[^>]+><img[^>]+>&nbsp;Loading ...</div>[^<]+'
    patronvideos += '</div>[^<]+'
    patronvideos += '<div class="comments">[^<]+</div>[^<]+'
    patronvideos += '<div class="thumbnail">[^<]+'
    patronvideos += '<a href="([^"]+)" title="([^"]+)"><img style="background: url\(([^\)]+)\)" [^>]+></a>[^<]+'
    patronvideos += '</div>[^<]+'
    patronvideos += '<h2 class="itemtitle"><a[^>]+>[^<]+</a></h2>[^<]+'
    patronvideos += '<p class="itemdesc">([^<]+)</p>[^<]+'
    patronvideos += '<small class="gallerydate">([^<]+)</small>'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    resultados = []

    for match in matches:
        scrapedtitle = match[1]
        scrapedurl = urlparse.urljoin(url,match[0])
        scrapedthumbnail = urlparse.urljoin(url,match[2])
        scrapedplot = match[3]

        if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

        # Añade al listado de XBMC
        resultados.append( [CHANNELNAME , "detail" , "buscador" , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot ] )
        
    return resultados

def peliscat(item):
    logger.info("[cine15.py] peliscat")

    # Descarga la página
    data = scrapertools.cachePage(item.url)

    # Extrae las entradas (carpetas)
    patronvideos  = '<li class="cat-item cat-item[^"]+"><a href="([^"]+)" title="[^"]+">([^<]+)</a>'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    itemlist = []
    for match in matches:
        scrapedtitle = match[1]
        scrapedurl = urlparse.urljoin(item.url,match[0])
        scrapedthumbnail = ""
        scrapedplot = ""
        if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

        itemlist.append( Item(channel=CHANNELNAME, action="listvideos", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )

    return itemlist

def listvideos(item):
    logger.info("[cine15.py] listvideos")

    # Descarga la página
    data = scrapertools.cachePage(item.url)
    #logger.info(data)

    # Extrae las entradas (carpetas)
    '''
    <div class="thumbnail-div">
    <a href="http://www.cine15.com/peliculas/accion/zombieland/" title="Zombieland">  <img src="http://www.cine15.com/wp-content/themes/cine2.00/timthumb.php?src=http://www.cine15.com/wp-content/uploads/2010/05/x14z.jpg&amp;h=225&amp;w=141&amp;q=80&amp;zc=1" alt=""  style="border: none;" />   </a>
    <div  id="play">
    <ul class="playimg">
    <li><a href="http://www.cine15.com/peliculas/accion/zombieland/" class="boton"  ></a></li>
    </ul></div>
    <div class="post-info2">
    <h2><a href="http://www.cine15.com/peliculas/accion/zombieland/" class="post-info-title" title="Permanent Link to Zombieland">
    Zombieland...                        </a></h2>
    <p class="itemdesc">TÍTULO ORIGINAL:  Zombieland
    AÑO: 2009     Ver trailer externo
    DURACIÓN: ...</p>
    '''
    patronvideos  = '<div class="thumbnail-div">[^<]+'
    patronvideos += '<a href="([^"]+)" title="([^"]+)">  <img src="([^"]+)"'
    
    matches = re.compile(patronvideos,re.DOTALL).findall(data)

    scrapertools.printMatches(matches)

    itemlist = []
    for match in matches:
        scrapedtitle = match[1]
        scrapedurl = urlparse.urljoin(item.url,match[0])
        scrapedthumbnail = urlparse.urljoin(item.url,match[2])
        scrapedplot = ""
        if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

        # Añade al listado de XBMC
        itemlist.append( Item(channel=CHANNELNAME, action="detail", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )

    # Extrae la marca de siguiente página
    patronvideos = "<span class='current'>[^<]+</span><a href='([^']+)' class='page'>"
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    if len(matches)>0:
        scrapedtitle = "Página siguiente"
        scrapedurl = urlparse.urljoin(item.url,matches[0])
        scrapedthumbnail = ""
        scrapedplot = ""
        itemlist.append( Item(channel=CHANNELNAME, action="listvideos", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )

    return itemlist

def detail(item):
    logger.info("[cine15.py] detail")

    title = item.title
    thumbnail = item.thumbnail
    plot = item.plot

    # Descarga la página
    data = scrapertools.cachePage(item.url)
    #logger.info(data)

    # ------------------------------------------------------------------------------------
    # Busca los enlaces a videos no megavideo (playlist xml)
    # ------------------------------------------------------------------------------------
    patronvideos  = 'flashvars[^f]+file=([^\&]+)\&amp'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)
    
    itemlist = []
    if len(matches)>0:
        if ("xml" in matches[0]):
            data2 = scrapertools.cachePage(matches[0])
            logger.info("data2="+data2)
            patronvideos  = '<track>[^<]+'
            patronvideos += '<title>([^<]+)</title>[^<]+'
            patronvideos += '<location>([^<]+)</location>[^<]+'
            patronvideos += '</track>'
            matches = re.compile(patronvideos,re.DOTALL).findall(data2)
            scrapertools.printMatches(matches)

            for match in matches:
                scrapedtitle = match[0]
                scrapedurl = match[1].strip()
                scrapedthumbnail = thumbnail
                scrapedplot = plot
                if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

                itemlist.append( Item(channel=CHANNELNAME, action="play" , title=scrapedtitle + " [Directo]" , url=scrapedurl, thumbnail=scrapedthumbnail, plot=scrapedplot, server="Directo", folder=False))

        else:
            itemlist.append( Item(channel=CHANNELNAME, action="play" , title=title + " [Directo]" , url=matches[0], thumbnail=thumbnail, plot=plot, server="Directo", folder=False))
            
    # ------------------------------------------------------------------------------------
    # Busca los enlaces a los videos
    # ------------------------------------------------------------------------------------
    listavideos = servertools.findvideos(data)

    for video in listavideos:
        videotitle = video[0]
        url = video[1]
        server = video[2]
        itemlist.append( Item(channel=CHANNELNAME, action="play" , title=title.strip() + " - " + videotitle , url=url, thumbnail=thumbnail, plot=plot, server=server, folder=False))
    # ------------------------------------------------------------------------------------

    return itemlist
