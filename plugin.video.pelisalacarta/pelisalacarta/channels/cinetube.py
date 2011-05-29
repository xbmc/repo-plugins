# -*- coding: utf-8 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para cinetube
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

CHANNELNAME = "cinetube"
DEBUG = True

def isGeneric():
    return True

def mainlist(item):
    logger.info("[cinetube.py] getmainlist")

    itemlist = []
    itemlist.append( Item(channel=CHANNELNAME, title="Películas - Novedades (con carátula)"  , action="peliculas"      , url="http://www.cinetube.es/peliculas/"))
    itemlist.append( Item(channel=CHANNELNAME, title="Películas - Todas A-Z (con carátula)"  , action="listalfabetico" , url="peliculas"))

    itemlist.append( Item(channel=CHANNELNAME, title="Series - Novedades (con carátula)"    , action="series" , url="http://www.cinetube.es/series/"))
    itemlist.append( Item(channel=CHANNELNAME, title="Series - Todas A-Z (con carátula)"    , action="listalfabetico" , url="series"))

    itemlist.append( Item(channel=CHANNELNAME, title="Documentales - Novedades" , action="documentales" , url="http://www.cinetube.es/documentales/"))
    itemlist.append( Item(channel=CHANNELNAME, title="Documentales - Todos A-Z" , action="listalfabetico", url="documentales"))

    itemlist.append( Item(channel=CHANNELNAME, title="Series anime - Novedades"    , action="series" , url="http://www.cinetube.es/series-anime/"))
    itemlist.append( Item(channel=CHANNELNAME, title="Series anime - Todas A-Z"    , action="listalfabetico" , url="series-anime" ))
                     
    itemlist.append( Item(channel=CHANNELNAME, title="Películas Anime - Novedades" , action="documentales" , url="http://www.cinetube.es/peliculas-anime/") )
    itemlist.append( Item(channel=CHANNELNAME, title="Películas Anime - Todas A-Z" , action="listalfabetico" , url="peliculas-anime" ))

    itemlist.append( Item(channel=CHANNELNAME, title="Buscar", action="search") )
    
    return itemlist

def search(item):
    logger.info("[cinetube.py] search")
    
    if config.get_platform()=="xbmc" or config.get_platform()=="xbmcdharma":
        from pelisalacarta import buscador
        texto = buscador.teclado()
        item.extra = texto

    itemlist = searchresults(item)
    
    return itemlist
    
def searchresults(item):
    logger.info("[cinetube.py] searchresults")
    
    #buscador.salvar_busquedas(params,tecleado,category)
    tecleado = item.extra.replace(" ", "+")
    item.url = "http://www.cinetube.es/buscar/peliculas/?palabra="+tecleado+"&categoria=&valoracion="

    return peliculas(item)
    
def peliculas(item):
    logger.info("[cinetube.py] peliculas")

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
    '''
    <!--PELICULA-->
    <div class="peli_item textcenter"><a href="/documentales/otros/ver-documental-tu-cerebro-inmortal.html">
    <div class="pelicula_img">
    <img src="http://caratulas.cinetube.es/docus/9570.jpg" alt="Tu Cerebro Inmortal" />
    </div>
    <p class="white"><a class="white" href="/documentales/otros/ver-documental-tu-cerebro-inmortal.html" title="Ver documental Tu Cerebro Inmortal">Tu Cerebro Inmortal</a></p></a>
    <div class="icos_lg"><img src="http://caratulas.cinetube.es/img/cont/espanol.png" alt="" /><img src="http://caratulas.cinetube.es/img/cont/megavideo.png" alt="" /><img src="http://caratulas.cinetube.es/img/cont/ddirecta.png" alt="descarga directa" /> </div>                                    </div>
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
        scrapedtitle = scrapedtitle.replace("megavideo/megavideo","megavideo")
        scrapedtitle = scrapedtitle.replace("megavideo/megavideo","megavideo")
        scrapedtitle = scrapedtitle.replace("descarga directa","DD")

        # Convierte desde UTF-8 y quita entidades HTML
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
        itemlist.append( Item(channel=CHANNELNAME, action="peliculas", title="!Página siguiente" , url=scrapedurl , folder=True) )

    return itemlist

def documentales(item):
    logger.info("[cinetube.py] documentales")

    # Descarga la página
    data = scrapertools.cachePage(item.url)

    # Extrae las entradas
    '''
    <!--PELICULA-->
    <div class="peli_item textcenter"><a href="/documentales/otros/ver-documental-tu-cerebro-inmortal.html">
    <div class="pelicula_img">
    <img src="http://caratulas.cinetube.es/docus/9570.jpg" alt="Tu Cerebro Inmortal" />
    </div>
    <p class="white"><a class="white" href="/documentales/otros/ver-documental-tu-cerebro-inmortal.html" title="Ver documental Tu Cerebro Inmortal">Tu Cerebro Inmortal</a></p></a>
    <div class="icos_lg"><img src="http://caratulas.cinetube.es/img/cont/espanol.png" alt="" /><img src="http://caratulas.cinetube.es/img/cont/megavideo.png" alt="" /><img src="http://caratulas.cinetube.es/img/cont/ddirecta.png" alt="descarga directa" /> </div>                                    </div>
    <!--FIN PELICULA-->
    '''
    patronvideos  = '<!--PELICULA-->[^<]+'
    patronvideos += '<div class="peli_item textcenter"><a href="([^"]+)">[^<]+'
    patronvideos += '<div class="pelicula_img">[^<]+'
    patronvideos += '<img src="([^"]+)" alt="([^"]+)"'
    
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    if DEBUG: scrapertools.printMatches(matches)

    itemlist = []
    for match in matches:
        scrapedtitle = match[2]
        scrapedplot = ""
        scrapedurl = urlparse.urljoin(item.url,match[0])
        scrapedthumbnail = urlparse.urljoin(item.url,match[1])
        if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

        # Añade al listado
        if match[0].startswith("/documentales/serie-documental"):
            itemlist.append( Item(channel=CHANNELNAME, action="episodios", title=scrapedtitle+" (serie)" , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )
        else:
            itemlist.append( Item(channel=CHANNELNAME, action="findvideos", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )

    # Extrae el paginador
    #<li class="navs"><a class="pag_next" href="/peliculas-todas/2.html"></a></li>
    patronvideos  = '<li class="navs"><a class="pag_next" href="([^"]+)"></a></li>'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    if len(matches)>0:
        scrapedurl = urlparse.urljoin(item.url,matches[0])
        itemlist.append( Item(channel=CHANNELNAME, action="documentales", title="!Página siguiente" , url=scrapedurl , folder=True) )

    return itemlist

def listalfabetico(item):
    logger.info("[cinetube.py] listalfabetico("+item.url+")")
    
    action = item.url
    if item.url=="series-anime":
        action="series"
    if item.url=="peliculas-anime":
        action="documentales"
    
    baseurl = "http://www.cinetube.es/"+item.url+"/"
    
    itemlist = []
    itemlist.append( Item(channel=CHANNELNAME, action=action , title="0-9", url=baseurl+"0-9/"))
    itemlist.append( Item(channel=CHANNELNAME, action=action , title="A"  , url=baseurl+"A/"))
    itemlist.append( Item(channel=CHANNELNAME, action=action , title="B"  , url=baseurl+"B/"))
    itemlist.append( Item(channel=CHANNELNAME, action=action , title="C"  , url=baseurl+"C/"))
    itemlist.append( Item(channel=CHANNELNAME, action=action , title="D"  , url=baseurl+"D/"))
    itemlist.append( Item(channel=CHANNELNAME, action=action , title="E"  , url=baseurl+"E/"))
    itemlist.append( Item(channel=CHANNELNAME, action=action , title="F"  , url=baseurl+"F/"))
    itemlist.append( Item(channel=CHANNELNAME, action=action , title="G"  , url=baseurl+"G/"))
    itemlist.append( Item(channel=CHANNELNAME, action=action , title="H"  , url=baseurl+"H/"))
    itemlist.append( Item(channel=CHANNELNAME, action=action , title="I"  , url=baseurl+"I/"))
    itemlist.append( Item(channel=CHANNELNAME, action=action , title="J"  , url=baseurl+"J/"))
    itemlist.append( Item(channel=CHANNELNAME, action=action , title="K"  , url=baseurl+"K/"))
    itemlist.append( Item(channel=CHANNELNAME, action=action , title="L"  , url=baseurl+"L/"))
    itemlist.append( Item(channel=CHANNELNAME, action=action , title="M"  , url=baseurl+"M/"))
    itemlist.append( Item(channel=CHANNELNAME, action=action , title="N"  , url=baseurl+"N/"))
    itemlist.append( Item(channel=CHANNELNAME, action=action , title="O"  , url=baseurl+"O/"))
    itemlist.append( Item(channel=CHANNELNAME, action=action , title="P"  , url=baseurl+"P/"))
    itemlist.append( Item(channel=CHANNELNAME, action=action , title="Q"  , url=baseurl+"Q/"))
    itemlist.append( Item(channel=CHANNELNAME, action=action , title="R"  , url=baseurl+"R/"))
    itemlist.append( Item(channel=CHANNELNAME, action=action , title="S"  , url=baseurl+"S/"))
    itemlist.append( Item(channel=CHANNELNAME, action=action , title="T"  , url=baseurl+"T/"))
    itemlist.append( Item(channel=CHANNELNAME, action=action , title="U"  , url=baseurl+"U/"))
    itemlist.append( Item(channel=CHANNELNAME, action=action , title="V"  , url=baseurl+"V/"))
    itemlist.append( Item(channel=CHANNELNAME, action=action , title="W"  , url=baseurl+"W/"))
    itemlist.append( Item(channel=CHANNELNAME, action=action , title="X"  , url=baseurl+"X/"))
    itemlist.append( Item(channel=CHANNELNAME, action=action , title="Y"  , url=baseurl+"Y/"))
    itemlist.append( Item(channel=CHANNELNAME, action=action , title="Z"  , url=baseurl+"Z/"))

    return itemlist

def series(item):
    logger.info("[cinetube.py] series")
    itemlist = []

    # Descarga la página
    data = scrapertools.cachePage(item.url)
    logger.info("Pagina de %d caracteres" % len(data))

    # Extrae las entradas
    '''
    <li>
    <a href="/series/en-tierra-de-lobos/temporada-1/capitulo-12/"><img src="http://caratulas.cinetube.es/series/8912.jpg" alt="peli" /></a>
    <div class="icos_lg"><img src="http://caratulas.cinetube.es/img/cont/espanol.png" alt="espanol" /> <img src="http://caratulas.cinetube.es/img/cont/megavideo.png" alt="megavideo.png" /> <img src="http://caratulas.cinetube.es/img/cont/ddirecta.png" alt="descarga directa" /> <p><span class="rosa"></span></p></div>
    <p class="tit_ficha"><a class="tit_ficha" title="Ver serie Tierra de lobos" href="/series/en-tierra-de-lobos/temporada-1/capitulo-12/">Tierra de lobos </a></p>
    <p class="tem_fich">1a Temporada - Cap 12</p>
    </li>
    '''
    '''
    <li>
    <a href="/series/gabriel-un-amor-inmortal/"><img src="http://caratulas.cinetube.es/series/7952.jpg" alt="peli" /></a>
    <div class="icos_lg"><img src="http://caratulas.cinetube.es/img/cont/latino.png" alt="" /><img src="http://caratulas.cinetube.es/img/cont/megavideo.png" alt="" /><img src="http://caratulas.cinetube.es/img/cont/ddirecta.png" alt="descarga directa" /> </div>                                        
    <p class="tit_ficha">Gabriel, un amor inmortal </p>
    </li>
    '''
    '''
    <li>
    <a href="/series-anime/star-driver-kagayaki-no-takuto/temporada-1/capitulo-13/"><img src="http://caratulas.cinetube.es/seriesa/9009.jpg" alt="peli" /></a>
    <div class="icos_lg"><img src="http://caratulas.cinetube.es/img/cont/sub.png" alt="sub" /> <img src="http://caratulas.cinetube.es/img/cont/megavideo.png" alt="megavideo.png" /> <img src="http://caratulas.cinetube.es/img/cont/ddirecta.png" alt="descarga directa" /> <p><span class="rosa"></span></p></div>
    <p class="tit_ficha"><a class="tit_ficha" title="Ver serie Star Driver Kagayaki no Takuto" href="/series-anime/star-driver-kagayaki-no-takuto/temporada-1/capitulo-13/">Star Driver Kagayaki no Takuto </a></p>
    <p class="tem_fich">1a Temporada - Cap 13</p>
    </li>
    '''
    patronvideos  = '<li>[^<]+'
    patronvideos += '<a href="([^"]+)"><img src="([^"]+)"[^>]*></a>[^<]+'
    patronvideos += '<div class="icos_lg">(.*?)</div>[^<]+'
    patronvideos += '<p class="tit_ficha">(.*?)</p>[^<]+'
    patronvideos += '(?:<p class="tem_fich">([^<]+)</p>)?'

    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    if DEBUG: scrapertools.printMatches(matches)

    for match in matches:
        # Titulo
        scrapedtitle = match[3].strip()
        if len(match)>=5:
            scrapedtitle = scrapedtitle+" "+match[4]
        matchesconectores = re.compile('<img.*?alt="([^"]*)"',re.DOTALL).findall(match[2])
        conectores = ""
        for matchconector in matchesconectores:
            logger.info("matchconector="+matchconector)
            if matchconector=="":
                matchconector = "megavideo"
            conectores = conectores + matchconector + "/"
        if len(matchesconectores)>0:
            scrapedtitle = scrapedtitle + " (" + conectores[:-1] + ")"
        scrapedtitle = scrapedtitle.replace("megavideo/megavideo","megavideo")
        scrapedtitle = scrapedtitle.replace("megavideo/megavideo","megavideo")
        scrapedtitle = scrapedtitle.replace("megavideo/megavideo","megavideo")
        scrapedtitle = scrapedtitle.replace("descarga directa","DD")

        scrapedtitle = scrapertools.htmlclean(scrapedtitle)
        scrapedtitle = scrapertools.entityunescape(scrapedtitle)

        scrapedplot = ""
        scrapedurl = urlparse.urljoin(item.url,match[0])
        scrapedthumbnail = match[1]
        if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

        itemlist.append( Item(channel=CHANNELNAME, action="temporadas", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )

    # Paginador
    #<li class="navs"><a class="pag_next" href="/peliculas-todas/2.html"></a></li>
    patronvideos  = '<li class="navs"><a class="pag_next" href="([^"]+)"></a></li>'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    if len(matches)>0:
        scrapedurl = urlparse.urljoin(item.url,matches[0])
        itemlist.append( Item(channel=CHANNELNAME, action="series", title="!Página siguiente" , url=scrapedurl , folder=True) )

    return itemlist

def temporadas(item):
    logger.info("[cinetube.py] temporadas")
    itemlist = []

    # Descarga la página
    data = scrapertools.cachePage(item.url)

    # Busca el argumento
    patronvideos  = '<div class="ficha_des des_move">(.*?)</div>'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    if len(matches)>0:
        data = matches[0]
        scrapedplot = scrapertools.htmlclean(matches[0])
        logger.info("plot actualizado en detalle");
    else:
        logger.info("plot no actualizado en detalle");

    # Busca las temporadas
    patronvideos  = '<li><h2><a href="([^"]+)">([^<]+)<'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    if DEBUG: scrapertools.printMatches(matches)

    for match in matches:
        scrapedtitle = match[1].strip()
        scrapedurl = urlparse.urljoin(item.url,match[0])
        scrapedthumbnail = item.thumbnail
        if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

        itemlist.append( Item(channel=CHANNELNAME, action="episodios", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail, plot=scrapedplot) )

    # Una trampa, si la serie enlaza no con la temporada sino con la lista de episodios, se resuelve aquí
    if len(itemlist)==0:
        itemlist = episodios(item)
        
    # Si la serie lleva directamente a la página de detalle de un episodio (suele pasar en novedades) se detecta aquí
    if len(itemlist)==0:
        itemlist.extend(findvideos(item))

    return itemlist

def episodios(item):
    '''
    <div class="title"> <a class="bold" href="/series/geronimo-stilton/temporada-1/capitulo-5/">Geronimo Stilton 1x05 </a></div>
    '''
    logger.info("[cinetube.py] episodios")
    itemlist = []

    # Descarga la página
    data = scrapertools.cachePage(item.url)

    # Busca los episodios
    patronvideos  = '<div class="title"> <a class="bold" href="([^"]+)">([^<]+)</a></div>'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    if DEBUG: scrapertools.printMatches(matches)

    for match in matches:
        scrapedtitle = match[1].strip()
        scrapedurl = urlparse.urljoin(item.url,match[0])
        scrapedthumbnail = item.thumbnail
        scrapedplot = item.plot
        if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

        itemlist.append( Item(channel=CHANNELNAME, action="findvideos", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail, plot=scrapedplot) )

    return itemlist

def findvideos(item):
    logger.info("[cinetube.py] findvideos")

    url = item.url
    title = item.title
    thumbnail = item.thumbnail
    plot = item.plot

    # Descarga la pagina
    data = scrapertools.cachePage(url)
    #logger.info(data)
    
    # Busca el argumento
    patronvideos  = '<div class="ficha_des">(.*?)</div>'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    if len(matches)>0:
        plot = scrapertools.htmlclean(matches[0])
        logger.info("plot actualizado en detalle");
    else:
        logger.info("plot no actualizado en detalle");
    
    # Busca el thumbnail
    patronvideos  = '<div class="ficha_img pelicula_img">[^<]+'
    patronvideos += '<img src="([^"]+)"'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    if len(matches)>0:
        thumbnail = matches[0]
        logger.info("thumb actualizado en detalle");
    else:
        logger.info("thumb no actualizado en detalle");

    # Busca los enlaces a los mirrors, o a los capitulos de las series...
    '''
    FORMATO EN SERIES
    <div class="tit_opts"><a href="/series/hawai-five/temporada-1/capitulo-13/212498.html">
    <p>Opción 1: Ver online en Megavideo <span class="bold"></span></p>
    <p><span>IDIOMA: SUB</span></p>
    <p class="v_ico"><img src="http://caratulas.cinetube.es/img/cont/megavideo.png" alt="Megavideo" /></p>
    '''
    patronvideos = '<div class="tit_opts"><a href="([^"]+)"[^>]*>[^<]+'
    patronvideos += '<p>(.*?)</p>[^<]+'
    patronvideos += '<p><span>(.*?)</span>'
    '''
    patronvideos = '<div class="tit_opts"><a href="([^"]+)".*?>[^<]+'
    patronvideos += '<p>([^<]+)</p>[^<]+'
    patronvideos += '<p><span>(.*?)</span>'
    '''
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
            scrapedtitle = scrapertools.htmlclean(scrapedtitle)
            scrapedurl = video[1]
            server = video[2]
            
            itemlist.append( Item(channel=CHANNELNAME, action="play" , title=scrapedtitle , url=scrapedurl, thumbnail=item.thumbnail, plot=item.plot, server=server, folder=False))

    return itemlist