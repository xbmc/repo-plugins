# -*- coding: utf-8 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para seriespepito
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#------------------------------------------------------------
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

CHANNELNAME = "seriespepito"
DEBUG = True

def isGeneric():
    return True

def mainlist(item):
    logger.info("[seriespepito.py] mainlist")

    itemlist = []
    itemlist.append( Item(channel=CHANNELNAME, action="listalfabetico"   , title="Listado alfabético"))
    #itemlist.append( Item(channel=CHANNELNAME, action="allserieslist"    , title="Listado completo",    url="http://www.seriespepito.com/"))

    return itemlist

def listalfabetico(item):
    
    itemlist = []
    itemlist.append( Item(channel=CHANNELNAME, action="alphaserieslist" , title="0-9",url="http://www.seriespepito.com/lista-series-num/"))
    itemlist.append( Item(channel=CHANNELNAME, action="alphaserieslist" , title="A",url="http://www.seriespepito.com/lista-series-a/"))
    itemlist.append( Item(channel=CHANNELNAME, action="alphaserieslist" , title="B",url="http://www.seriespepito.com/lista-series-b/"))
    itemlist.append( Item(channel=CHANNELNAME, action="alphaserieslist" , title="C",url="http://www.seriespepito.com/lista-series-c/"))
    itemlist.append( Item(channel=CHANNELNAME, action="alphaserieslist" , title="D",url="http://www.seriespepito.com/lista-series-d/"))
    itemlist.append( Item(channel=CHANNELNAME, action="alphaserieslist" , title="E",url="http://www.seriespepito.com/lista-series-e/"))
    itemlist.append( Item(channel=CHANNELNAME, action="alphaserieslist" , title="F",url="http://www.seriespepito.com/lista-series-f/"))
    itemlist.append( Item(channel=CHANNELNAME, action="alphaserieslist" , title="G",url="http://www.seriespepito.com/lista-series-g/"))
    itemlist.append( Item(channel=CHANNELNAME, action="alphaserieslist" , title="H",url="http://www.seriespepito.com/lista-series-h/"))
    itemlist.append( Item(channel=CHANNELNAME, action="alphaserieslist" , title="I",url="http://www.seriespepito.com/lista-series-i/"))
    itemlist.append( Item(channel=CHANNELNAME, action="alphaserieslist" , title="J",url="http://www.seriespepito.com/lista-series-j/"))
    itemlist.append( Item(channel=CHANNELNAME, action="alphaserieslist" , title="K",url="http://www.seriespepito.com/lista-series-k/"))
    itemlist.append( Item(channel=CHANNELNAME, action="alphaserieslist" , title="L",url="http://www.seriespepito.com/lista-series-l/"))
    itemlist.append( Item(channel=CHANNELNAME, action="alphaserieslist" , title="M",url="http://www.seriespepito.com/lista-series-m/"))
    itemlist.append( Item(channel=CHANNELNAME, action="alphaserieslist" , title="N",url="http://www.seriespepito.com/lista-series-n/"))
    itemlist.append( Item(channel=CHANNELNAME, action="alphaserieslist" , title="O",url="http://www.seriespepito.com/lista-series-o/"))
    itemlist.append( Item(channel=CHANNELNAME, action="alphaserieslist" , title="P",url="http://www.seriespepito.com/lista-series-p/"))
    itemlist.append( Item(channel=CHANNELNAME, action="alphaserieslist" , title="Q",url="http://www.seriespepito.com/lista-series-q/"))
    itemlist.append( Item(channel=CHANNELNAME, action="alphaserieslist" , title="R",url="http://www.seriespepito.com/lista-series-r/"))
    itemlist.append( Item(channel=CHANNELNAME, action="alphaserieslist" , title="S",url="http://www.seriespepito.com/lista-series-s/"))
    itemlist.append( Item(channel=CHANNELNAME, action="alphaserieslist" , title="T",url="http://www.seriespepito.com/lista-series-t/"))
    itemlist.append( Item(channel=CHANNELNAME, action="alphaserieslist" , title="U",url="http://www.seriespepito.com/lista-series-u/"))
    itemlist.append( Item(channel=CHANNELNAME, action="alphaserieslist" , title="V",url="http://www.seriespepito.com/lista-series-v/"))
    itemlist.append( Item(channel=CHANNELNAME, action="alphaserieslist" , title="W",url="http://www.seriespepito.com/lista-series-w/"))
    itemlist.append( Item(channel=CHANNELNAME, action="alphaserieslist" , title="X",url="http://www.seriespepito.com/lista-series-x/"))
    itemlist.append( Item(channel=CHANNELNAME, action="alphaserieslist" , title="Y",url="http://www.seriespepito.com/lista-series-y/"))
    itemlist.append( Item(channel=CHANNELNAME, action="alphaserieslist" , title="Z",url="http://www.seriespepito.com/lista-series-z/"))

    return itemlist

def alphaserieslist(item):
    logger.info("[seriespepito.py] alphaserieslist")

    # Descarga la página
    data = scrapertools.cachePage(item.url)
    #logger.info(data)

    # Extrae las entradas (carpetas)
    '''
    <div class='lista-series'>    
    <div class="imagen">
    <a href="http://abducidos.seriespepito.com" title="Abducidos online">
    <img src='http://www.midatacenter.com/seriespepito/imagenes-serie/abducidos498.jpg' width='90' height='124' border='0' alt='Abducidos online'   />                  </a>
    </div>
    <div class="nombre">
    <a href="http://abducidos.seriespepito.com" title="Abducidos online">Abducidos</a>
    </div>
    <div class="sinopsis">
    Abducidos es una Mini-Serie Estadounidense que consta de 10 capítulos, los cuales los podrás ver online o descargar en SeriesPepito.
    Es una miniserie de ciencia ficción emitida por primera vez en el ...                  </div>
    <div class="enlace">
    '''
    patron  = "<div class='lista-series'>[^<]+"
    patron += '<div class="imagen">[^<]+'
    patron += '<a href="([^"]+)"[^<]+'
    patron += "<img src='([^']+)'[^<]+</a>[^<]+"
    patron += '</div>[^<]+'
    patron += '<div class="nombre">[^<]+'
    patron += '<a[^>]+>([^<]+)</a>[^<]+'
    patron += '</div>[^<]+'
    patron += '<div class="sinopsis">(.*?)</div>[^<]+'
    patron += '<div class="enlace">'


    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    itemlist = []
    for match in matches:
        scrapedtitle = match[2]
        scrapedurl = match[0]
        scrapedthumbnail = match[1]
        scrapedplot = match[3]
        if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

        # Ajusta el encoding a UTF-8
        scrapedtitle = unicode( scrapedtitle, "iso-8859-1" , errors="replace" ).encode("utf-8")

        itemlist.append( Item(channel=CHANNELNAME, action="episodelist" , title=scrapedtitle , url=scrapedurl, thumbnail=scrapedthumbnail, plot=scrapedplot, show=scrapedtitle))

    return itemlist

def episodelist(item):
    logger.info("[seriespepito.py] list")

    # Descarga la página
    data = scrapertools.cachePage(item.url)
    #logger.info(data)

    # Extrae los capítulos
    patron  = "<li><a  href='(http://.*?.seriespepito.com.*?)'[^>]+><span>([^<]+)</span></a>"
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    itemlist = []
    for match in matches:
        scrapedtitle = match[1]
        scrapedurl = match[0]
        scrapedthumbnail = item.thumbnail
        scrapedplot = item.plot
        if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

        itemlist.append( Item(channel=CHANNELNAME, action="findvideos" , title=scrapedtitle , url=scrapedurl, thumbnail=scrapedthumbnail, plot=scrapedplot, show=item.show))

    return itemlist
