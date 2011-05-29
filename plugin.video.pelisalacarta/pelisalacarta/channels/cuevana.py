# -*- coding: utf-8 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para cuevana
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#------------------------------------------------------------
import urlparse,urllib2,urllib,re
import os, sys
import xbmcgui
import xbmc

try:
    from core import logger
    from core import config
    from core import scrapertools
    from core.item import Item
    from servers import servertools
    from core import library
    from core import xbmctools
except:
    # En Plex Media server lo anterior no funciona...
    from Code.core import logger
    from Code.core import config
    from Code.core import scrapertools
    from Code.core.item import Item
    from Code.core import library
    from Code.core import xbmctools

CHANNELNAME = "cuevana"
DEBUG = True

def isGeneric():
    return True

def mainlist(item):
    logger.info("[cuevana.py] mainlist")

    itemlist = []
    itemlist.append( Item(channel=CHANNELNAME, title="Películas"  , action="peliculas", url="http://www.cuevana.tv/peliculas/"))
    itemlist.append( Item(channel=CHANNELNAME, title="Series"     , action="series",    url="http://www.cuevana.tv/series/"))
    itemlist.append( Item(channel=CHANNELNAME, title="Buscar", action="search") )
    
    return itemlist

def peliculas(item):
    logger.info("[cuevana.py] peliculas")
    itemlist = []
    itemlist.append( Item(channel=CHANNELNAME, title="Novedades"  , action="novedades", url="http://www.cuevana.tv/peliculas/"))
    itemlist.append( Item(channel=CHANNELNAME, title="M�s Populares"  , action="novedades", url="http://www.cuevana.tv/peliculas/populares/"))
    itemlist.append( Item(channel=CHANNELNAME, title="Mejor Puntuadas"  , action="novedades", url="http://www.cuevana.tv/peliculas/mejorpuntuadas/"))
    itemlist.append( Item(channel=CHANNELNAME, title="Listado Alfabético"     , action="listadoAlfabetico",    url="http://www.cuevana.tv/peliculas/lista/"))

    return itemlist

def listadoAlfabetico(item):
    itemlist = []
    itemlist.append( Item(channel=CHANNELNAME , action="novedades" , title="0-9",url="http://www.cuevana.tv/peliculas/lista/letra=num"))
    itemlist.append( Item(channel=CHANNELNAME , action="novedades" , title="A",url="http://www.cuevana.tv/peliculas/lista/letra=a"))
    itemlist.append( Item(channel=CHANNELNAME , action="novedades" , title="B",url="http://www.cuevana.tv/peliculas/lista/letra=b"))
    itemlist.append( Item(channel=CHANNELNAME , action="novedades" , title="C",url="http://www.cuevana.tv/peliculas/lista/letra=c"))
    itemlist.append( Item(channel=CHANNELNAME , action="novedades" , title="D",url="http://www.cuevana.tv/peliculas/lista/letra=d"))
    itemlist.append( Item(channel=CHANNELNAME , action="novedades" , title="E",url="http://www.cuevana.tv/peliculas/lista/letra=e"))
    itemlist.append( Item(channel=CHANNELNAME , action="novedades" , title="F",url="http://www.cuevana.tv/peliculas/lista/letra=f"))
    itemlist.append( Item(channel=CHANNELNAME , action="novedades" , title="G",url="http://www.cuevana.tv/peliculas/lista/letra=g"))
    itemlist.append( Item(channel=CHANNELNAME , action="novedades" , title="H",url="http://www.cuevana.tv/peliculas/lista/letra=h"))
    itemlist.append( Item(channel=CHANNELNAME , action="novedades" , title="I",url="http://www.cuevana.tv/peliculas/lista/letra=i"))
    itemlist.append( Item(channel=CHANNELNAME , action="novedades" , title="J",url="http://www.cuevana.tv/peliculas/lista/letra=j"))
    itemlist.append( Item(channel=CHANNELNAME , action="novedades" , title="K",url="http://www.cuevana.tv/peliculas/lista/letra=k"))
    itemlist.append( Item(channel=CHANNELNAME , action="novedades" , title="L",url="http://www.cuevana.tv/peliculas/lista/letra=l"))
    itemlist.append( Item(channel=CHANNELNAME , action="novedades" , title="M",url="http://www.cuevana.tv/peliculas/lista/letra=m"))
    itemlist.append( Item(channel=CHANNELNAME , action="novedades" , title="N",url="http://www.cuevana.tv/peliculas/lista/letra=n"))
    itemlist.append( Item(channel=CHANNELNAME , action="novedades" , title="O",url="http://www.cuevana.tv/peliculas/lista/letra=o"))
    itemlist.append( Item(channel=CHANNELNAME , action="novedades" , title="P",url="http://www.cuevana.tv/peliculas/lista/letra=p"))
    itemlist.append( Item(channel=CHANNELNAME , action="novedades" , title="Q",url="http://www.cuevana.tv/peliculas/lista/letra=q"))
    itemlist.append( Item(channel=CHANNELNAME , action="novedades" , title="R",url="http://www.cuevana.tv/peliculas/lista/letra=r"))
    itemlist.append( Item(channel=CHANNELNAME , action="novedades" , title="S",url="http://www.cuevana.tv/peliculas/lista/letra=s"))
    itemlist.append( Item(channel=CHANNELNAME , action="novedades" , title="T",url="http://www.cuevana.tv/peliculas/lista/letra=t"))
    itemlist.append( Item(channel=CHANNELNAME , action="novedades" , title="U",url="http://www.cuevana.tv/peliculas/lista/letra=u"))
    itemlist.append( Item(channel=CHANNELNAME , action="novedades" , title="V",url="http://www.cuevana.tv/peliculas/lista/letra=v"))
    itemlist.append( Item(channel=CHANNELNAME , action="novedades" , title="W",url="http://www.cuevana.tv/peliculas/lista/letra=w"))
    itemlist.append( Item(channel=CHANNELNAME , action="novedades" , title="X",url="http://www.cuevana.tv/peliculas/lista/letra=x"))
    itemlist.append( Item(channel=CHANNELNAME , action="novedades" , title="Y",url="http://www.cuevana.tv/peliculas/lista/letra=y"))
    itemlist.append( Item(channel=CHANNELNAME , action="novedades" , title="Z",url="http://www.cuevana.tv/peliculas/lista/letra=z"))

    return itemlist

def novedades(item):
    if (DEBUG): logger.info("[cuevana.py] novedades login")
    p = urllib.urlencode({'usuario' : 'pelisalacarta','password' : 'pelisalacarta','recordarme':'si','ingresar':'true'})
    data = scrapertools.downloadpage("http://www.cuevana.tv/login_get.php",p)
    data = scrapertools.downloadpagewithcookies(item.url)

    # Extrae las entradas
    '''
    <tr class='row2'>
    <td valign='top'><a href='/peliculas/2933/alpha-and-omega/'><img src='/box/2933.jpg' border='0' height='90' /></a></td>
    <td valign='top'><div class='tit'><a href='/peliculas/2933/alpha-and-omega/'>Alpha and Omega</a></div>
    <div class='font11'>Dos pequeños carrochos de lobo se ven obligados a convivir por determinadas circunstancias.
    <div class='reparto'><b>Reparto:</b> <a href='/buscar/?q=Animación&cat=actor'>Animación</a></div>
    </div></td>
    '''
    patronvideos  = "<tr class='row[^<]+"
    patronvideos += "<td valign='top'><a href='([^']+)'><img src='([^']+)'[^>]+></a></td>[^<]+"
    patronvideos += "<td valign='top'><div class='tit'><a[^>]+>([^<]+)</a></div>[^<]+"
    patronvideos += "<div class='font11'>([^<]+)<"

    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    if DEBUG: scrapertools.printMatches(matches)

    itemlist = []
    for match in matches:
        scrapedtitle = match[2]
        scrapedplot = match[3]
        scrapedurl = urlparse.urljoin(item.url,match[0])
        scrapedthumbnail = urlparse.urljoin(item.url,match[1])
        if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

        # Añade al listado de XBMC
        itemlist.append( Item(channel=CHANNELNAME, action="findvideos", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )

    # Extrae el paginador
    patronvideos  = "<a class='next' href='([^']+)' title='Siguiente'>"
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    if len(matches)>0:
        scrapedurl = urlparse.urljoin(item.url,matches[0])
        itemlist.append( Item(channel=CHANNELNAME, action="novedades", title="Página siguiente" , url=scrapedurl , folder=True) )

    return itemlist

def series(item):
    logger.info("[cuevana.py] series")
    
    # Descarga la página
    data = scrapertools.cachePage(item.url)

    # Extrae las entradas
    patron  = 'serieslist.push\(\{id\:([0-9]+),nombre\:"([^"]+)"\}\);'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)
    itemlist = []
    for match in matches:
        scrapedtitle = match[1]
        scrapedplot = ""
        code = match[0]
        scrapedurl = "http://www.cuevana.tv/list_search_id.php?serie="+code
        scrapedthumbnail = "http://www.cuevana.tv/box/"+code+".jpg"
        if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

        itemlist.append( Item(channel=CHANNELNAME, action="temporadas", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , show=item.title , folder=True, extra=scrapedtitle) )

    return itemlist

def temporadas(item):
    logger.info("[cuevana.py] temporadas")

    # Descarga la página
    data = scrapertools.cachePage(item.url)

    # Extrae las entradas
    patron  = '<li onclick=\'listSeries\(2,"([^"]+)"\)\'>([^<]+)</li>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)
    itemlist = []
    for match in matches:
        scrapedtitle = match[1]
        temporada = scrapedtitle.replace("Temporada ","")
        scrapedplot = ""
        code = match[0]
        scrapedurl = "http://www.cuevana.tv/list_search_id.php?temporada="+code
        scrapedthumbnail = item.thumbnail
        if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"], temporada=["+temporada+"]")

        itemlist.append( Item(channel=CHANNELNAME, action="episodios", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , show=item.show + " - " + item.title , folder=True, extra=item.extra + "|" + temporada) )

    return itemlist

def episodios(item):
    logger.info("[cuevana.py] episodios")

    # Descarga la página
    data = scrapertools.cachePage(item.url)

    # Extrae las entradas
    #<li onclick='listSeries(3,"5099")'><span class='nume'>1</span> Truth Be Told</li>
    patron  = '<li onclick=\'listSeries\(3,"([^"]+)"\)\'><span class=\'nume\'>([^<]+)</span>([^<]+)</li>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)
    itemlist = []
    logger.info("[cuevana.py] agregar todos los episodios a la biblioteca")
    # A�ade "Agregar todos a la librer�a"
    itemlist.append( Item(channel=CHANNELNAME, action="addlist2Library", title="A�ADIR TODOS LOS EPISODIOS A LA BIBLIOTECA", url=item.url, thumbnail="", show = item.show , folder=True, extra=item.extra, plot="") )

    for match in matches:
        code = match[0]
        scrapedtitle = match[1]+" "+match[2].strip()
        scrapedplot = ""
        scrapedurl = "http://www.cuevana.tv/list_search_info.php?episodio="+code
        scrapedthumbnail = item.thumbnail
        if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

        itemlist.append( Item(channel=CHANNELNAME, action="findvideos", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , show = item.show , folder=True) )

    return itemlist

def findvideos(item):
    logger.info("[cuevana.py] findvideos")

    # True es Serie, False es Pelicula
    serieOpelicula = True
    code =""
    if (item.url.startswith("http://www.cuevana.tv/list_search_info.php")):
        data = scrapertools.cachePage(item.url)
        #logger.info("data="+data)
        patron = "window.location\='/series/([0-9]+)/"
        matches = re.compile(patron,re.DOTALL).findall(data)
        if len(matches)>0:
            code = matches[0]
        logger.info("code="+code)
        url = "http://www.cuevana.tv/player/source?id=%s&subs=,ES&onstart=yes&tipo=s&sub_pre=ES" % matches[0]
        serieOpelicula = True
    else:
        # http://www.cuevana.tv/peliculas/2553/la-cienaga/
        logger.info("url1="+item.url)
        patron = "http://www.cuevana.tv/peliculas/([0-9]+)/"
        matches = re.compile(patron,re.DOTALL).findall(item.url)
        if len(matches)>0:
            code = matches[0]
        logger.info("code="+code)
        url = "http://www.cuevana.tv/player/source?id=%s&subs=,ES&onstart=yes&sub_pre=ES#" % code
        serieOpelicula = False
    
    logger.info("url2="+url)
    data = scrapertools.cachePage(url)
    #logger.info("data="+data)

    # goSource('ee5533f50eab1ef355661eef3b9b90ec','megaupload')
    patron = "goSource\('([^']+)','megaupload'\)"
    matches = re.compile(patron,re.DOTALL).findall(data)
    if len(matches)>0:
        data = scrapertools.cachePagePost("http://www.cuevana.tv/player/source_get","key=%s&host=megaupload&vars=&id=2933&subs=,ES&tipo=&amp;sub_pre=ES" % matches[0])
    logger.info("data="+data)

    # Subtitulos
    if serieOpelicula:
	    suburl = "http://www.cuevana.tv/files/s/sub/"+code+"_ES.srt"
    else:
            suburl = "http://www.cuevana.tv/files/sub/"+code+"_ES.srt"
    logger.info("suburl="+suburl)
    
    # Elimina el archivo subtitulo.srt de alguna reproduccion anterior
    ficherosubtitulo = os.path.join( config.get_data_path(), 'subtitulo.srt' )
    if os.path.exists(ficherosubtitulo):
        try:
          os.remove(ficherosubtitulo)
        except IOError:
          xbmc.output("Error al eliminar el archivo subtitulo.srt "+ficherosubtitulo)
          raise

    listavideos = servertools.findvideos(data)
    
    itemlist = []
    
    for video in listavideos:
        server = video[2]
        scrapedtitle = item.title + " [" + server + "]"
        scrapedurl = video[1]
        
        itemlist.append( Item(channel=CHANNELNAME, action="play" , title=scrapedtitle , url=scrapedurl, thumbnail=item.thumbnail, plot=item.plot, server=server, subtitle=suburl, folder=False))

    return itemlist

def search(item):
    logger.info("[cuevana.py] search")
    itemlist = []
    itemlist.append( Item(channel=CHANNELNAME, title="Titulo"  , action="search2"))
    itemlist.append( Item(channel=CHANNELNAME, title="Episodio"     , action="search2"))
    itemlist.append( Item(channel=CHANNELNAME, title="Actor"  , action="search2"))
    itemlist.append( Item(channel=CHANNELNAME, title="Director"     , action="search2"))
    
    return itemlist
	
def search2(item):
	logger.info("[cuevana.py] search2")
    
	if config.get_platform()=="xbmc" or config.get_platform()=="xbmcdharma":
		from pelisalacarta import buscador
		texto = buscador.teclado()
		texto = texto.replace(' ','+')
		item.extra = texto
		title= item.title
		title = title.lower()

	itemlist = searchresults(item,title)

	return itemlist
    
def searchresults(item,title):
    logger.info("[cuevana.py] searchresults")
    
    teclado = item.extra.replace(" ", "+")
    logger.info("[newhd.py] " + teclado)
    item.url = "http://www.cuevana.tv/buscar/?q="+ teclado+ "&cat=" + title

    return listar(item)

def listar(item):
    logger.info("[cuevana.py] listar")

    # Descarga la página
    data = scrapertools.cachePage(item.url)

    patronvideos  = "<div class='result'>[^<]+"
    patronvideos += "<div class='right'><div class='tit'><a href='([^']+)'>([^<]+)</a>"
    patronvideos += ".*?<div class='txt'>([^<]+)<div class='reparto'>.*?"
    patronvideos += "<div class='img'>.*?<img src='([^']+)'[^>]+></a>"


    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    if DEBUG: scrapertools.printMatches(matches)

    itemlist = []
    for match in matches:
        scrapedtitle = match[1]
        scrapedplot = match[2]
        scrapedurl = urlparse.urljoin("http://www.cuevana.tv/peliculas/",match[0])
        scrapedthumbnail = urlparse.urljoin("http://www.cuevana.tv/peliculas/",match[3])
        if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

        # Añade al listado de XBMC
        itemlist.append( Item(channel=CHANNELNAME, action="findvideos", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )

    # Extrae el paginador
    patronvideos  = "<a class='next' href='([^']+)' title='Siguiente'>"
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    if len(matches)>0:
        scrapedurl = urlparse.urljoin(item.url,matches[0])
        itemlist.append( Item(channel=CHANNELNAME, action="listar", title="Página siguiente" , url=scrapedurl , folder=True) )

    return itemlist

def strm_detail(item):
    logger.info("[cuevana.py] strm_detail")
    code =""
    if (item.url.startswith("http://www.cuevana.tv/list_search_info.php")):
        data = scrapertools.cachePage(item.url)
        patron = "window.location\='/series/([0-9]+)/"
        matches = re.compile(patron,re.DOTALL).findall(data)
        if len(matches)>0:
            code = matches[0]
        logger.info("code="+code)
        url = "http://www.cuevana.tv/player/source?id=%s&subs=,ES&onstart=yes&tipo=s&sub_pre=ES" % matches[0]
        serieOpelicula = True
    else:
        logger.info("url1="+item.url)
        patron = "http://www.cuevana.tv/peliculas/([0-9]+)/"
        matches = re.compile(patron,re.DOTALL).findall(item.url)
        if len(matches)>0:
            code = matches[0]
        logger.info("code="+code)
        url = "http://www.cuevana.tv/player/source?id=%s&subs=,ES&onstart=yes&sub_pre=ES#" % code
        serieOpelicula = False
    
    logger.info("url2="+url)
    data = scrapertools.cachePage(url)

    # goSource('ee5533f50eab1ef355661eef3b9b90ec','megaupload')
    patron = "goSource\('([^']+)','megaupload'\)"
    matches = re.compile(patron,re.DOTALL).findall(data)
    if len(matches)>0:
        data = scrapertools.cachePagePost("http://www.cuevana.tv/player/source_get","key=%s&host=megaupload&vars=&id=2933&subs=,ES&tipo=&amp;sub_pre=ES" % matches[0])
    logger.info("data="+data)

    # Subtitulos
    if serieOpelicula:
        suburl = "http://www.cuevana.tv/files/s/sub/"+code+"_ES.srt"
    else:
        suburl = "http://www.cuevana.tv/files/sub/"+code+"_ES.srt"
    logger.info("suburl="+suburl)
    
    # Elimina el archivo subtitulo.srt de alguna reproduccion anterior
    ficherosubtitulo = os.path.join( config.get_data_path(), 'subtitulo.srt' )
    if os.path.exists(ficherosubtitulo):
        try:
          os.remove(ficherosubtitulo)
        except IOError:
          xbmc.output("Error al eliminar el archivo subtitulo.srt "+ficherosubtitulo)
          raise

    from core import downloadtools
    downloadtools.downloadfile(suburl, ficherosubtitulo )
    config.set_setting("subtitulo","true")

    listavideos = servertools.findvideos(data)
    
    for video in listavideos:
        server = video[2]
        if server == "Megaupload":
          scrapedtitle = item.title + " [" + server + "]"
          scrapedurl = video[1]
          thumbnail = urllib.unquote_plus( item.thumbnail )
          plot = unicode( xbmc.getInfoLabel( "ListItem.Plot" ), "utf-8" )
          # xbmctools.playvideo("cuevana","megaupload","G0NMCIXJ","Series","24","","",strmfile=True)
          xbmctools.playvideo(CHANNELNAME,server,scrapedurl,"Series",scrapedtitle,item.thumbnail,item.plot,strmfile=True,subtitle=suburl)
          exit
    logger.info("[cuevana.py] strm_detail fin")
    return

def addlist2Library(item):
    logger.info("[cuevana.py] addlist2Library")
    itemlist = []
    # Descarga la p�gina
    data = scrapertools.cachePage(item.url)
    extra = item.extra.split("|")

    # Extrae las entradas (carpetas)
    patronvideos  = '<li onclick=\'listSeries\(3,"([^"]+)"\)\'><span class=\'nume\'>([^<]+)</span>([^<]+)</li>'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    pDialog = xbmcgui.DialogProgress()
    ret = pDialog.create('pelisalacarta', 'A�adiendo episodios...')
    pDialog.update(0, 'A�adiendo episodio...')
    totalepisodes = len(matches)
    logger.info ("[cuevana.py - addlist2Library] Total Episodios:"+str(totalepisodes))
    i = 0
    errores = 0
    nuevos = 0
    for match in matches:
        scrapedtitle = "S"+extra[1]+"E"+match[1]+" "+match[2].strip()
        Serie = extra[0]
        server = "Megaupload"
        i = i + 1
        pDialog.update(i*100/totalepisodes, 'A�adiendo episodio...',scrapedtitle)
        if (pDialog.iscanceled()):
            return
        url = "http://www.cuevana.tv/list_search_info.php?episodio="+match[0]
        scrapedthumbnail = ""
        scrapedplot = ""
        if (DEBUG):
            logger.info("scrapedtitle="+scrapedtitle)
            logger.info("url="+url) #OPCION 2.
            logger.info("scrapedthumbnail="+scrapedthumbnail)
            logger.info("Episodio "+str(i)+" de "+str(totalepisodes)+"("+str(i*100/totalepisodes)+"%)")
        try:
            nuevos = nuevos + library.savelibrary(scrapedtitle,url,scrapedthumbnail,server,scrapedplot,canal=CHANNELNAME,category="Series",Serie=Serie,verbose=False,accion="strm_detail",pedirnombre=False)
        except IOError:
            logger.info("Error al grabar el archivo "+scrapedtitle)
            errores = errores + 1
    if errores > 0:
        logger.info ("[cuevana.py - addlist2Library] No se pudo a�adir "+str(errores)+" episodios") 
    library.update(totalepisodes,errores,nuevos)
