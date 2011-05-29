# -*- coding: utf-8 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para somosmovies
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#------------------------------------------------------------
import urlparse,urllib2,urllib,re
import os, sys

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

CHANNELNAME = "somosmovies"
DEBUG = True

def isGeneric():
    return True

def mainlist(item):
    logger.info("[somosmovies.py] mainlist")

    itemlist = []
    itemlist.append( Item(channel=CHANNELNAME, title="Películas"    , action="listado", url="http://www.somosmovies.com/search/label/Peliculas?max-results=12"))
    itemlist.append( Item(channel=CHANNELNAME, title="Series"       , action="listado", url="http://www.somosmovies.com/search/label/Series?max-results=12"))
    itemlist.append( Item(channel=CHANNELNAME, title="Anime"        , action="listado", url="http://www.somosmovies.com/search/label/Anime?max-results=12"))
    itemlist.append( Item(channel=CHANNELNAME, title="Documentales" , action="listado", url="http://www.somosmovies.com/search/label/Documental?max-results=12"))
    
    return itemlist

def listado(item):
    logger.info("[somosmovies.py] listado")

    # Descarga la página
    data = scrapertools.cachePage(item.url)

    # Extrae las entradas
    '''
    <h3 class='post-title entry-title'>
    <a href='http://www.somosmovies.com/2010/12/dinner-for-schmucks-2010.html'>Dinner for Schmucks (2010)</a>
    </h3>
    <div class='post-header-line-1'></div>
    <div class='post-body entry-content'>
    <a href='http://www.somosmovies.com/2010/12/dinner-for-schmucks-2010.html'><div id='summary2965545734731460603'><center><img border="0" src="http://1.bp.blogspot.com/_IcS2ZFffwuA/TRj6TU_-VXI/AAAAAAAACfE/bVPxAz3dra8/s1600/Dinner+For+Schmuck+%25282010%2529.jpg" style="display: block; height: 350px;"></center><br>
    <br>
    '''
    '''
    <h3 class='post-title entry-title'>
    <a href='http://www.somosmovies.com/2010/12/ticking-clock-2011.html'>Ticking Clock (2011)</a>
    </h3>
    <div class='post-header-line-1'></div>
    <div class='post-body entry-content'>
    <a href='http://www.somosmovies.com/2010/12/ticking-clock-2011.html'><div id='summary4195574178414576162'><div class="separator" style="clear: both; text-align: center;"><a href="http://1.bp.blogspot.com/_0bsG3NIClx0/TRp1mjN4f8I/AAAAAAAAAS0/ZRwtedadMjM/s1600/Caratula.png" imageanchor="1" style="margin-left: 1em; margin-right: 1em;"><img border="0" height="400" src="http://1.bp.blogspot.com/_0bsG3NIClx0/TRp1mjN4f8I/AAAAAAAAAS0/ZRwtedadMjM/s400/Caratula.png" width="315"></a></div><div class="separator" style="clear: both; text-align: center;"><a href="http://2.bp.blogspot.com/_0bsG3NIClx0/TRKLExwYtRI/AAAAAAAAAQE/hIT8HghjdSA/s1600/Caratula.png" imageanchor="1" style="margin-left: 1em; margin-right: 1em;"><span id="goog_956228244"></span><span id="goog_956228245"></span></a></div></div></a><script type='text/javascript'>createSummaryAndThumb("summary4195574178414576162");</script>
    <div style='clear: both;'></div>
    </div>
    '''

    patronvideos  = "<h3 class='post-title entry-title'>[^<]+"
    patronvideos += "<a href='([^']+)'>([^<]+)</a>[^<]+"
    patronvideos += "</h3>[^<]+"
    patronvideos += "<div class='post-header-line-1'></div>[^<]+"
    patronvideos += "<div class='post-body entry-content'>[^<]+"
    patronvideos += "<a href='[^']+'><div id='[^']+'>.*?<img.*?src=\"([^\"]+)\""

    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    if DEBUG: scrapertools.printMatches(matches)

    itemlist = []
    for match in matches:
        scrapedtitle = match[1]
        scrapedplot = ""
        scrapedurl = urlparse.urljoin(item.url,match[0])
        scrapedthumbnail = urlparse.urljoin(item.url,match[2])
        if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

        # Añade al listado de XBMC
        itemlist.append( Item(channel=CHANNELNAME, action="findvideos", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )

    # Extrae el paginador
    patronvideos  = "<a class='blog-pager-older-link' href='([^']+)' id='Blog1_blog-pager-older-link' title='Siguiente'>"
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    if len(matches)>0:
        #http://www.somosmovies.com/search/label/Peliculas?updated-max=2010-12-20T08%3A27%3A00-06%3A00&max-results=12
        scrapedurl = urlparse.urljoin(item.url,matches[0])
        scrapedurl = scrapedurl.replace("%3A",":")
        itemlist.append( Item(channel=CHANNELNAME, action="peliculas", title="!Página siguiente" , url=scrapedurl , folder=True) )

    return itemlist