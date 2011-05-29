# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para SOFACINE
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

CHANNELNAME = "sofacine"
DEBUG = True

def isGeneric():
    return True

def mainlist(item):
    logger.info("[sofacine.py] mainlist")

    itemlist = []
    itemlist.append( Item(channel=CHANNELNAME, action="listvideos" , title="Películas - Novedades"            , url="http://www.sofacine.com/index.php"))
   #itemlist.append( Item(channel=CHANNELNAME, action="search"     , title="Buscar"))

    return itemlist

def pelisalfa(item):
    logger.info("[sofacine.py] mainlist")

    itemlist = []
    itemlist.append( Item(channel=CHANNELNAME, action="listsimple", title="0-9", url="http://www.sofacine.com/index.php?module=peliculaslist&init="))
    itemlist.append( Item(channel=CHANNELNAME, action="listsimple", title="A", url="http://www.sofacine.com/index.php?module=peliculaslist&init=a"))
    itemlist.append( Item(channel=CHANNELNAME, action="listsimple", title="B", url="http://www.sofacine.com/index.php?module=peliculaslist&init=b"))
    itemlist.append( Item(channel=CHANNELNAME, action="listsimple", title="C", url="http://www.sofacine.com/index.php?module=peliculaslist&init=c"))
    itemlist.append( Item(channel=CHANNELNAME, action="listsimple", title="D", url="http://www.sofacine.com/index.php?module=peliculaslist&init=d"))
    itemlist.append( Item(channel=CHANNELNAME, action="listsimple", title="E", url="http://www.sofacine.com/index.php?module=peliculaslist&init=e"))
    itemlist.append( Item(channel=CHANNELNAME, action="listsimple", title="F", url="http://www.sofacine.com/index.php?module=peliculaslist&init=f"))
    itemlist.append( Item(channel=CHANNELNAME, action="listsimple", title="G", url="http://www.sofacine.com/index.php?module=peliculaslist&init=g"))
    itemlist.append( Item(channel=CHANNELNAME, action="listsimple", title="H", url="http://www.sofacine.com/index.php?module=peliculaslist&init=h"))
    itemlist.append( Item(channel=CHANNELNAME, action="listsimple", title="I", url="http://www.sofacine.com/index.php?module=peliculaslist&init=i"))
    itemlist.append( Item(channel=CHANNELNAME, action="listsimple", title="J", url="http://www.sofacine.com/index.php?module=peliculaslist&init=j"))
    itemlist.append( Item(channel=CHANNELNAME, action="listsimple", title="K", url="http://www.sofacine.com/index.php?module=peliculaslist&init=k"))
    itemlist.append( Item(channel=CHANNELNAME, action="listsimple", title="L", url="http://www.sofacine.com/index.php?module=peliculaslist&init=l"))
    itemlist.append( Item(channel=CHANNELNAME, action="listsimple", title="M", url="http://www.sofacine.com/index.php?module=peliculaslist&init=m"))
    itemlist.append( Item(channel=CHANNELNAME, action="listsimple", title="N", url="http://www.sofacine.com/index.php?module=peliculaslist&init=n"))
    itemlist.append( Item(channel=CHANNELNAME, action="listsimple", title="O", url="http://www.sofacine.com/index.php?module=peliculaslist&init=o"))
    itemlist.append( Item(channel=CHANNELNAME, action="listsimple", title="P", url="http://www.sofacine.com/index.php?module=peliculaslist&init=p"))
    itemlist.append( Item(channel=CHANNELNAME, action="listsimple", title="Q", url="http://www.sofacine.com/index.php?module=peliculaslist&init=q"))
    itemlist.append( Item(channel=CHANNELNAME, action="listsimple", title="R", url="http://www.sofacine.com/index.php?module=peliculaslist&init=r"))
    itemlist.append( Item(channel=CHANNELNAME, action="listsimple", title="S", url="http://www.sofacine.com/index.php?module=peliculaslist&init=s"))
    itemlist.append( Item(channel=CHANNELNAME, action="listsimple", title="T", url="http://www.sofacine.com/index.php?module=peliculaslist&init=t"))
    itemlist.append( Item(channel=CHANNELNAME, action="listsimple", title="U", url="http://www.sofacine.com/index.php?module=peliculaslist&init=u"))
    itemlist.append( Item(channel=CHANNELNAME, action="listsimple", title="V", url="http://www.sofacine.com/index.php?module=peliculaslist&init=v"))
    itemlist.append( Item(channel=CHANNELNAME, action="listsimple", title="W", url="http://www.sofacine.com/index.php?module=peliculaslist&init=w"))
    itemlist.append( Item(channel=CHANNELNAME, action="listsimple", title="X", url="http://www.sofacine.com/index.php?module=peliculaslist&init=x"))
    itemlist.append( Item(channel=CHANNELNAME, action="listsimple", title="Y", url="http://www.sofacine.com/index.php?module=peliculaslist&init=y"))
    itemlist.append( Item(channel=CHANNELNAME, action="listsimple", title="Z", url="http://www.sofacine.com/index.php?module=peliculaslist&init=z"))

    return itemlist

# TODO: La búsqueda no funciona en canales genéricos aún
def search(params,url,category):
    logger.info("[sofacine.py] search")

    from pelisalacarta import buscador
    buscador.listar_busquedas(params,url,category)

# TODO: La búsqueda no funciona en canales genéricos aún
def searchresults(params,tecleado,category):
    logger.info("[sofacine.py] search")

    from pelisalacarta import buscador
    buscador.salvar_busquedas(params,tecleado,category)
    tecleado = tecleado.replace(" ", "+")
    searchUrl = "http://www.sofacine.com/index.php?module=search&title="+tecleado
    listsimple(params,searchUrl,category)

# TODO: La búsqueda no funciona en canales genéricos aún
def performsearch(texto):
    logger.info("[sofacine.py] performsearch")
    url = "http://www.sofacine.com/index.php?module=search&title="+texto

    # Descarga la página
    data = scrapertools.cachePage(url)

    # Extrae los items
    patronvideos  = "<a href='(index.php\?module\=player[^']+)'[^>]*>(.*?)</a>"
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)
    
    resultados = []

    for match in matches:
        # Atributos
        scrapedtitle = match[1]
        scrapedtitle = scrapedtitle.replace("<span class='style4'>","")
        scrapedtitle = scrapedtitle.replace("</span>","")
        scrapedurl = urlparse.urljoin(url,match[0])
        scrapedthumbnail = ""
        scrapedplot = ""

        if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

        # Añade al listado de XBMC
        resultados.append( [CHANNELNAME , "findvideos" , "buscador" , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot ] )
        
    return resultados

def peliscat(item):
    logger.info("[sofacine.py] peliscat")

    url = item.url

    itemlist = []
    itemlist.append( Item(channel=CHANNELNAME, action="listsimple" , title="Versión original" , url="http://www.sofacine.com/index.php?module=search&title=subtitulado"))
    itemlist.append( Item(channel=CHANNELNAME, action="listsimple" , title="Versión latina"   , url="http://www.sofacine.com/index.php?module=search&title=latino"))

    # Descarga la página
    data = scrapertools.cachePage(url)

    # Extrae los items
    patronvideos  = "<td align='left'><a href='([^']+)'><img src='([^']+)' border='0'></a></td>"
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for match in matches:
        # Atributos
        patron2 = "genero/([A-Za-z\-]+)/"
        matches2 = re.compile(patron2,re.DOTALL).findall(match[0])
        scrapertools.printMatches(matches2)
        
        scrapedtitle = matches2[0]
        scrapedurl = urlparse.urljoin(url,match[0])
        scrapedthumbnail = urlparse.urljoin(url,match[1])
        scrapedplot = ""
        if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

        itemlist.append( Item(channel=CHANNELNAME, action="listvideos" , title=scrapedtitle , url=scrapedurl, thumbnail=scrapedthumbnail, plot=scrapedplot))

    return itemlist

def listsimple(item):
    logger.info("[sofacine.py] listsimple")

    url = item.url

    # Descarga la página
    data = scrapertools.cachePage(url)

    # Extrae los items
    patronvideos  = "<a href='(index.php\?module\=player[^']+)'[^>]*>(.*?)</a>"
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    itemlist = []
    for match in matches:
        # Atributos
        scrapedtitle = match[1]
        scrapedtitle = scrapedtitle.replace("<span class='style4'>","")
        scrapedtitle = scrapedtitle.replace("</span>","")
        scrapedurl = urlparse.urljoin(url,match[0])
        scrapedthumbnail = ""
        scrapedplot = ""
        if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

        itemlist.append( Item(channel=CHANNELNAME, action="findvideos" , title=scrapedtitle , url=scrapedurl, thumbnail=scrapedthumbnail, plot=scrapedplot))

    return itemlist

def listvideos(item):
    logger.info("[sofacine.py] listvideos")

    url = item.url

    # Descarga la página
    data = scrapertools.cachePage(url)
    #logger.info(data)

    # Extrae los items
    '''
    <h2 class="contentheading">
    <span>
    <a href="/peliculas/pequenas-mentiras-sin-importancia-2.html" class="contentpagetitle">PEQUEÑAS MENTIRAS SIN IMPORTANCIA (BR-Scr)</a>
    </span>
    </h2>
    <div class="article-tools clearfix">
    <div class="article-meta">
    <a class="comments" href="/peliculas/pequenas-mentiras-sin-importancia-2.html#comments">0 Comentarios</a>
    <span class="article-section">
    <a href="/peliculas">						Peliculas Español							</a>											 - 					</span>
    <span class="article-section">
    <a href="/peliculas-4.html">						Comedia							</a>					</span>
    </div>
    </div>
    <div class="article-content">
    <p><a href="peliculas/pequenas-mentiras-sin-importancia.html"><img src="images/stories/PELICULAS/pequenas-mentiras-sin-importancia.jpg"
    '''
    #patronvideos  = "<table.*?<td.*?>([^<]+)<span class='style1'>\(Visto.*?"
    #patronvideos += "<div align='justify'>(.*?)</div>.*?"
    #patronvideos += "<a href='(.*?)'.*?"
    #patronvideos += "<img src='(.*?)'"
    
    patronvideos  = '<h2 class="contentheading">[^<]+'
    patronvideos += '<span>[^<]+'
    patronvideos += '<a href="([^"]+)" class="contentpagetitle">([^<]+)</a>.*?'
    patronvideos += '<img src="([^"]+)"'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    itemlist = []
    for match in matches:
        scrapedtitle = match[1]
        scrapedurl = urlparse.urljoin(url,match[0])
        scrapedthumbnail = urlparse.urljoin(url,match[2])
        scrapedplot = ""
        if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

        itemlist.append( Item(channel=CHANNELNAME, action="findvideos" , title=scrapedtitle , url=scrapedurl, thumbnail=scrapedthumbnail, plot=scrapedplot))

    # Extrae la marca de siguiente página
    #patronvideos  = "<a href='[^']+'><u>[^<]+</u></a> <a href='([^']+)'>"
    patron = '<a href="([^"]+)" title="Siguiente">Siguiente'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    if len(matches)>0:
        scrapedtitle = "Página siguiente"
        scrapedurl = urlparse.urljoin(url,matches[0])
        scrapedthumbnail = ""
        scrapedplot = ""
        itemlist.append( Item(channel=CHANNELNAME, action="listvideos" , title=scrapedtitle , url=scrapedurl, thumbnail=scrapedthumbnail, plot=scrapedplot))

    return itemlist

def listseries(item):
    logger.info("[sofacine.py] listvideos")

    url = item.url
    
    # Descarga la página
    data = scrapertools.cachePage(url)

    # Extrae los items
    patronvideos  = "<table width='785'[^>]+><tr><td[^>]+>([^<]+)<.*?"
    patronvideos += "<div align='justify'>(.*?)</div>.*?"
    patronvideos += "<a href='(.*?)'.*?"
    patronvideos += "<img src='(.*?)'"
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    itemlist = []
    for match in matches:
        scrapedtitle = match[0]
        scrapedurl = urlparse.urljoin(url,match[2])
        scrapedthumbnail = urlparse.urljoin(url,match[3])
        scrapedplot = match[1]
        if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

        itemlist.append( Item(channel=CHANNELNAME, action="findvideos" , title=scrapedtitle , url=scrapedurl, thumbnail=scrapedthumbnail, plot=scrapedplot))

    # Extrae la marca de siguiente página
    patronvideos  = "<a href='[^']+'><u>[^<]+</u></a> <a href='([^']+)'>"
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    if len(matches)>0:
        scrapedtitle = "Página siguiente"
        scrapedurl = urlparse.urljoin(url,matches[0])
        scrapedthumbnail = ""
        scrapedplot = ""
        itemlist.append( Item(channel=CHANNELNAME, action="listseries" , title=scrapedtitle , url=scrapedurl, thumbnail=scrapedthumbnail, plot=scrapedplot))

    return itemlist
