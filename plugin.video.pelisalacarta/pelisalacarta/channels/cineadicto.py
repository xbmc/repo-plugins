# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para cine-adicto.com by Bandavi
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

from pelisalacarta import buscador

CHANNELNAME = "cineadicto"

# Esto permite su ejecución en modo emulado
try:
    pluginhandle = int( sys.argv[ 1 ] )
except:
    pluginhandle = ""

# Traza el inicio del canal
logger.info("[cineadicto.py] init")

DEBUG = True
def isGeneric():
    return True

def mainlist(item):
    logger.info("[cineadicto.py] mainlist")

    itemlist = []
    itemlist.append( Item(channel=CHANNELNAME , action="listvideos"        , title="Ultimas Películas Añadidas"    , url="http://www.cine-adicto.com/"))
    itemlist.append( Item(channel=CHANNELNAME , action="ListaCat"          , title="Listado por Genero"            , url="http://www.cine-adicto.com/"))
    itemlist.append( Item(channel=CHANNELNAME , action="ListaAlfa"         , title="Listado Alfanumerico"          , url="http://www.cine-adicto.com/" ))
    itemlist.append( Item(channel=CHANNELNAME , action="ListvideosMirror"  , title="Estrenos"                      , url="http://www.cine-adicto.com/category/2010/" ))
    itemlist.append( Item(channel=CHANNELNAME , action="listvideos"        , title="Documentales"                  , url="http://www.cine-adicto.com/category/documentales/" ))
    #itemlist.append( Item(channel=CHANNELNAME , action="listvideos"        , title="Peliculas en HD"              , url="http://www.cine-adicto.com/category/peliculas-hd-categorias" ))
    itemlist.append( Item(channel=CHANNELNAME , action="search"            , title="Buscar"                        , url="http://www.cine-adicto.com/" , category = "Buscador_Generico"))

    return itemlist
    
def search(item):
    logger.info("[cineadicto.py] search")

    return buscador.listar_busquedas(item)

def searchresults(item):
    logger.info("[cineadicto.py] searchresults")

    buscador.salvar_busquedas(item)

    #convert to HTML
    tecleado = item.url.replace(" ", "+")
    item.url = "http://www.cine-adicto.com/?s="+tecleado
    itemlist = searchresults2(item)
    return itemlist

def searchresults2(item):
    logger.info("[cineadicto.py] SearchResult")
    
    
    # Descarga la página
    data = scrapertools.cachePage(item.url)
    #print data
    # Extrae las entradas (carpetas)
    patronvideos  = '<div class="poster">[^<]+<a href="([^"]+)"'                          # URL
    patronvideos += '><img src="([^"]+)" width=[^\/]+\/>'                                 # TUMBNAIL
    patronvideos += '</a>[^<]+<[^>]+>[^<]+<[^>]+>[^<]+<a href="[^"]+">([^<]+)</a>'        # TITULO 
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)
    
    itemlist = []
    for match in matches:
        # Atributos
        scrapedurl = match[0]
        
        scrapedtitle =match[2]
        scrapedtitle = scrapedtitle.replace("&#8211;","-")
        scrapedtitle = scrapedtitle.replace("&nbsp;"," ")
        scrapedthumbnail = match[1]
        scrapedplot = ""
        if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

        # Añade al listado de XBMC
        itemlist.append( Item(channel=CHANNELNAME , action="detail"  , title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail, plot=scrapedplot ))

    
    return itemlist

def ListaCat(item):
    logger.info("[cineadicto.py] ListaCat")

    
    
    # Descarga la página
    data = scrapertools.cachePage(item.url)
    #print data
    # Extrae las entradas (carpetas)
    patronvideos  = '<a href="([^"]+)" title="[^<]+" class="generos">([^<]+)</a>'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)

    scrapertools.printMatches(matches)

    itemlist = []
    for match in matches:
        # Atributos
        scrapedurl = match[0]
        
        scrapedtitle =match[1]
        scrapedthumbnail = ""
        scrapedplot = ""
        if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

        # Añade al listado de XBMC
        itemlist.append( Item(channel=CHANNELNAME , action="listvideos"   , title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail, plot=scrapedplot ))
    
    return itemlist
    
 

def ListaAlfa(item):

    itemlist = []
    itemlist.append( Item(channel=CHANNELNAME , action="listvideos" , title="0-9",url="http://www.cine-adicto.com/alphabet/9/"))
    itemlist.append( Item(channel=CHANNELNAME , action="listvideos" , title="A",url="http://www.cine-adicto.com/alphabet/a/"))
    itemlist.append( Item(channel=CHANNELNAME , action="listvideos" , title="B",url="http://www.cine-adicto.com/alphabet/b/"))
    itemlist.append( Item(channel=CHANNELNAME , action="listvideos" , title="C",url="http://www.cine-adicto.com/alphabet/c/"))
    itemlist.append( Item(channel=CHANNELNAME , action="listvideos" , title="D",url="http://www.cine-adicto.com/alphabet/d/"))
    itemlist.append( Item(channel=CHANNELNAME , action="listvideos" , title="E",url="http://www.cine-adicto.com/alphabet/e/"))
    itemlist.append( Item(channel=CHANNELNAME , action="listvideos" , title="F",url="http://www.cine-adicto.com/alphabet/f/"))
    itemlist.append( Item(channel=CHANNELNAME , action="listvideos" , title="G",url="http://www.cine-adicto.com/alphabet/g/"))
    itemlist.append( Item(channel=CHANNELNAME , action="listvideos" , title="H",url="http://www.cine-adicto.com/alphabet/h/"))
    itemlist.append( Item(channel=CHANNELNAME , action="listvideos" , title="I",url="http://www.cine-adicto.com/alphabet/i/"))
    itemlist.append( Item(channel=CHANNELNAME , action="listvideos" , title="J",url="http://www.cine-adicto.com/alphabet/j/"))
    itemlist.append( Item(channel=CHANNELNAME , action="listvideos" , title="K",url="http://www.cine-adicto.com/alphabet/k/"))
    itemlist.append( Item(channel=CHANNELNAME , action="listvideos" , title="L",url="http://www.cine-adicto.com/alphabet/l/"))
    itemlist.append( Item(channel=CHANNELNAME , action="listvideos" , title="M",url="http://www.cine-adicto.com/alphabet/m/"))
    itemlist.append( Item(channel=CHANNELNAME , action="listvideos" , title="N",url="http://www.cine-adicto.com/alphabet/n/"))
    itemlist.append( Item(channel=CHANNELNAME , action="listvideos" , title="O",url="http://www.cine-adicto.com/alphabet/o/"))
    itemlist.append( Item(channel=CHANNELNAME , action="listvideos" , title="P",url="http://www.cine-adicto.com/alphabet/p/"))
    itemlist.append( Item(channel=CHANNELNAME , action="listvideos" , title="Q",url="http://www.cine-adicto.com/alphabet/q/"))
    itemlist.append( Item(channel=CHANNELNAME , action="listvideos" , title="R",url="http://www.cine-adicto.com/alphabet/r/"))
    itemlist.append( Item(channel=CHANNELNAME , action="listvideos" , title="S",url="http://www.cine-adicto.com/alphabet/s/"))
    itemlist.append( Item(channel=CHANNELNAME , action="listvideos" , title="T",url="http://www.cine-adicto.com/alphabet/t/"))
    itemlist.append( Item(channel=CHANNELNAME , action="listvideos" , title="U",url="http://www.cine-adicto.com/alphabet/u/"))
    itemlist.append( Item(channel=CHANNELNAME , action="listvideos" , title="V",url="http://www.cine-adicto.com/alphabet/v/"))
    itemlist.append( Item(channel=CHANNELNAME , action="listvideos" , title="W",url="http://www.cine-adicto.com/alphabet/w/"))
    itemlist.append( Item(channel=CHANNELNAME , action="listvideos" , title="X",url="http://www.cine-adicto.com/alphabet/x/"))
    itemlist.append( Item(channel=CHANNELNAME , action="listvideos" , title="Y",url="http://www.cine-adicto.com/alphabet/y/"))
    itemlist.append( Item(channel=CHANNELNAME , action="listvideos" , title="Z",url="http://www.cine-adicto.com/alphabet/z/"))

    return itemlist


        
def ListvideosMirror(item):
    logger.info("[cineadicto.py] ListvideosMirror")

    # Descarga la página
    data = scrapertools.cachePage(item.url)
    #logger.info(data)


    # Patron de las entradas
    #<!-- empieza pelicula-left --> <div class="pelicula-left"> <div class="box-pelicula-titulo"></div> <div class="box-pelicula-contenido">

#<div class="imagen"><a title="Resident Evil Afterlife (Resident Evil 4)" href="http://www.cine-adicto.com/resident-evil-afterlife.html"><img alt="imagen de Resident Evil Afterlife (Resident Evil 4)"  src="http://www.cine-adicto.com/images/Resident-Evil-Afterlife-Resident-Evil-4.jpg" width="166" height="250" alt="Resident Evil Afterlife (Resident Evil 4)" /></a></div>

#    <div class="tituloh1"><h1><a title="Resident Evil Afterlife (Resident Evil 4)" href="http://www.cine-adicto.com/resident-evil-afterlife.html">Resident Evil Afterlife (Resident Evil 4)</a></h1></div>
#<div class="sinopsis"><p>
    patronvideos  = '<div class="pelicula-left">.*?<div class="imagen"><a title="([^"]+)"'           # TITULO
    patronvideos += ' href="([^"]+)"'                                                             # URL
    patronvideos += '><img alt="[^"]+"  src="([^"]+)" width=[^\/]+\/>.*?'                            # TUMBNAIL
    patronvideos += '<div class="sinopsis"><p>([^<]+)</p>'                                           # SINOPSIS
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    itemlist = []
    for match in matches:
        # Atributos
        scrapedtitle = match[0]
        scrapedurl = match[1]
        scrapedthumbnail = match[2]
        scrapedplot = match[3]
        if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

        # Añade al listado de XBMC
        itemlist.append( Item(channel=CHANNELNAME , action="detail"  , title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail, plot=scrapedplot ))

    #Extrae la marca de siguiente página
    patronvideos  = '<span class="current">[^<]+</span>[^<]+<a title="[^"]+" href="([^"]+)"'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    if len(matches)>0:
        scrapedtitle = "Página siguiente"
        scrapedurl = matches[0]
        scrapedthumbnail = ""
        scrapedplot = ""
        itemlist.append( Item(channel=CHANNELNAME , action="ListvideosMirror"  , title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail, plot=scrapedplot ))

    return itemlist
        

def listvideos(item):
    logger.info("[cineadicto.py] listvideos")

    url = item.url
    if url=="":
        url = "http://www.cine-adicto.com/"
                
    data = scrapertools.cachePage(url)

    # Extrae las entradas (carpetas)
    '''
    <div class="box-pelicula-contenido">
    <div class="imagen"><a title="Frankie & Alice" href="http://www.cine-adicto.com/frankie-alice.html"><img alt="imagen de Frankie & Alice"  src="http://www.cine-adicto.com/images/Frankie_and_Alice.jpg" width="166" height="250" alt="Frankie & Alice" /></a></div>
    <div class="tituloh1"><h1><a title="Frankie & Alice" href="http://www.cine-adicto.com/frankie-alice.html">Frankie & Alice</a></h1></div>
    
    <div class="sinopsis"><p>Drama centrado en la vida de una mujer (Halle Berry) que lucha contra el  trastorno de personalidad múltiple, una enfermedad en la que su propio  ser es invadido por una mente racista que se está apoderando de ella,  alterando su personalidad como Frankie y como Alice.</p></div>
    <a class="boton-pelicula linkFader" title="Frankie & Alice" href="http://www.cine-adicto.com/frankie-alice.html"></a> </div> <div class="box-pelicula-abajo">
    '''
    patron = '<div class="box-pelicula-contenido">(.*?)<div class="box-pelicula-abajo">'
    matches = re.compile(patron,re.DOTALL).findall(data)
    logger.info("hay %d matches" % len(matches))

    itemlist = []
    for match in matches:
        data2 = match
        patron  = '<div class="imagen"><a.*?href="([^"]+)"><img.*?src="([^"]+)".*?'
        patron += '<div class="tituloh1"><h1><a[^>]+>([^<]+)</a></h1></div>.*?'
        patron += '<div class="sinopsis">(.*?)</div>'
        matches2 = re.compile(patron,re.DOTALL).findall(data2)
        logger.info("hay %d matches2" % len(matches2))

        for match2 in matches2:
            scrapedtitle = match2[2]
            scrapedurl = match2[0]
            scrapedthumbnail = match2[1]
            scrapedplot = match2[3]
            
            itemlist.append( Item(channel=CHANNELNAME , action="detail"  , title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail, plot=scrapedplot , fanart=scrapedthumbnail ))

    #Extrae la marca de siguiente página
    patronvideos  = '<span class="current">[^<]+</span>[^<]+<a title="[^"]+" href="([^"]+)"' #"</span><a href='(http://www.cine-adicto.com/page/[^']+)'"
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    if len(matches)>0:
        scrapedtitle = "Página siguiente"
        scrapedurl = urlparse.urljoin(url,matches[0])#matches[0]
        scrapedthumbnail = ""
        scrapedplot = ""
        itemlist.append( Item(channel=CHANNELNAME , action="listvideos"  , title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail, plot=scrapedplot ))

    return itemlist
    
def detail(item):
    logger.info("[cineadicto.py] detail")

    title = item.title
    thumbnail = item.thumbnail
    plot = item.plot
    scrapedurl = ""
    url = item.url
    # Descarga la página
    data = scrapertools.cachePage(url)
    #logger.info(data)
    patronvideos = 'name="Pelicula" src="([^"]+)"'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    if len(matches)>0:
        data = scrapertools.cachePage(matches[0])
    # Extrae el argumento
    patronarg = '</p><p>.*?<strong>([^<]+</strong> <strong>.*?)<p></p>'
    matches   = re.compile(patronarg,re.DOTALL).findall(data)
    if len(matches)>0:
        plot  = re.sub("<[^>]+>"," ",matches[0])
  
    # ------------------------------------------------------------------------------------
    # Busca los enlaces a los videos en los servidores habilitados
    # ------------------------------------------------------------------------------------

   
            
    ## --------------------------------------------------------------------------------------##
    #               Busca enlaces a videos .flv o (.mp4 dentro de un xml)                     #
    ## --------------------------------------------------------------------------------------##
    patronvideos = 'file=(http\:\/\/[^\&]+)\&'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)
    playWithSubt = "play"
    c = 0
    itemlist = []
    if len(matches)>0:
        for match in matches:
            subtitle = "[FLV-Directo]"
            c += 1
            if ("playlist" in match):
                data2 = scrapertools.cachePage(match)
                logger.info("data2="+data2)
                patronvideos  = '<track>.*?'
                patronvideos += '<title>([^<]+)</title>[^<]+'
                patronvideos += '<location>([^<]+)</location>(?:[^<]+'
                patronvideos += '<meta rel="type">video</meta>[^<]+|[^<]+'
                patronvideos += '<meta rel="captions">([^<]+)</meta>[^<]+)'
                patronvideos += '</track>'
                matches2 = re.compile(patronvideos,re.DOTALL).findall(data2)
                scrapertools.printMatches(matches)
                
                for match2 in matches2:
                    sub = ""
                    if match2[2].endswith(".xml"): # Subtitulos con formato xml son incompatibles con XBMC
                        sub = "[Subtitulo incompatible con xbmc]"
                        playWithSubt = "play"
                    if ".mp4" in match2[1]:
                        subtitle = "[MP4-Directo]"
                    scrapedtitle = '%s (castellano) - %s  %s' %(title,match2[0],subtitle)
                    
                    scrapedurl = match2[1].strip()
                    scrapedthumbnail = thumbnail
                    scrapedplot = plot
                    if ("cast.xml" or "mirror.xml") not in match:
                        scrapedtitle = '%s (V.O.S) - %s  %s %s' %(title,match2[0],subtitle,sub)
                        if not match2[2].endswith("cine-adicto2.srt") and (sub == ""): 
                            scrapedurl = scrapedurl + "|" + match2[2]
                            playWithSubt = "play2"
                            
                    if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")
                            
                    # Añade al listado de XBMC
                    itemlist.append( Item(channel=CHANNELNAME , action=playWithSubt  , title=scrapedtitle, url=scrapedurl , thumbnail=scrapedthumbnail, plot=scrapedplot, server= "Directo" , folder = False ))
                
            else:
                c +=1
                scrapedurl = match
                if match.endswith(".srt") and not (((c / 2) * 2 - c) == 0) :
                    scrapedurl = scrapedurl + "|" + match 
                    itemlist.append( Item(channel=CHANNELNAME , action="play2"  , server="Directo" , title=title + " (V.O.S) - "+subtitle, url=scrapedurl , thumbnail=thumbnail , plot=plot , folder=False))
                elif     match.endswith(".xml") and not (((c / 2) * 2 - c) == 0):
                    sub = "[Subtitulo incompatible con xbmc]"
                    itemlist.append( Item(channel=CHANNELNAME , action="play"  , server="Directo" , title=title + " (V.O) - %s %s" %(subtitle,sub), url=scrapedurl , thumbnail=thumbnail , plot=plot , folder=False ))
                elif not match.endswith("srt" or "xml") :
                    itemlist.append( Item(channel=CHANNELNAME , action="play"  , server="Directo" , title=title + " - [Directo]" , url=scrapedurl , thumbnail=thumbnail , plot=plot , folder=False ))
                
                print scrapedurl
    
    try:
        matches = url.split("/")
        url2 = "http://www.cine-adicto.com/tab/"+matches[3]
        data2 = scrapertools.cachePage(url2)
    
        
        listavideos = servertools.findvideos(data2)
        c = 0
        for video in listavideos:
            if "stagevu.com/embed" not in video[1]:
                videotitle = video[0]
                url = video[1]
                server = video[2]
                if "facebook" in url:
                    c += 1
                    itemlist.append( Item(channel=CHANNELNAME , action="play"   , server=server , title=title.strip() + " - Parte %d %s" %(c,videotitle) , url=url , thumbnail=thumbnail , plot=plot , folder=False))
                else:
                    itemlist.append( Item(channel=CHANNELNAME , action="play"   , server=server , title=title.strip() + " - " + videotitle , url=url , thumbnail=thumbnail , plot=plot , folder=False ))
    except:
        pass


    ## --------------------------------------------------------------------------------------##
    #            Busca enlaces de videos para el servidor vk.com                             #
    ## --------------------------------------------------------------------------------------##
    '''
    var video_host = '447.gt3.vkadre.ru';
    var video_uid = '0';
    var video_vtag = '2638f17ddd39-';
    var video_no_flv = 0;
    var video_max_hd = '0';
    var video_title = 'newCine.NET+-+neWG.Es+%7C+Chicken+Little';

    '''
    patronvideos = '<iframe src="(http://[^\/]+\/video_ext.php[^"]+)"'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    if len(matches)>0:
        print " encontro VK.COM :%s" %matches[0]
        videourl = vk.geturl(matches[0])
        itemlist.append( Item(channel=CHANNELNAME , action="play"  , server="Directo" , title=title + " - "+"[VK]", url=videourl , thumbnail=thumbnail , plot=plot , folder=False ))

    patronvideos = '(http://cine-adicto.com/(?:(?:vk|vb)|(?:mg|bb))?/[^\.]+.html)'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    if len(matches)>0:
        for match in matches:
            
            listavideos = servertools.findvideos(scrapertools.cachePage(match))
            for video in listavideos:
                if "stagevu.com/embed" not in video[1]:
                    videotitle = video[0]
                    url = video[1]
                    server = video[2]
                if "facebook" in url:
                    c += 1
                    itemlist.append( Item(channel=CHANNELNAME , action="play"  , server=server , title=title.strip() + " - Parte %d %s" %(c,videotitle) , url=url , thumbnail=thumbnail , plot=plot , folder=False ))
                else:
                    itemlist.append( Item(channel=CHANNELNAME , action="play"  , server=server , title=title.strip() + " - " + videotitle , url=url , thumbnail=thumbnail , plot=plot , folder=False ))
 
    listavideos = servertools.findvideos(data)
    for video in listavideos:
        if "stagevu.com/embed" not in video[1]:
            videotitle = video[0]
            url = video[1]
            server = video[2]
            if "facebook" in url:
                c += 1
                itemlist.append( Item(channel=CHANNELNAME , action="play"  , server=server , title=title.strip() + " - Parte %d %s" %(c,videotitle) , url=url , thumbnail=thumbnail , plot=plot , folder=False ))
            else:
                itemlist.append( Item(channel=CHANNELNAME , action="play"  , server=server , title=title.strip() + " - " + videotitle , url=url , thumbnail=thumbnail , plot=plot ,folder=False ))
 
    return itemlist

def play(params,url,category):
    logger.info("[cineadicto.py] play")

    title = unicode( xbmc.getInfoLabel( "ListItem.Title" ), "utf-8" )
    thumbnail = urllib.unquote_plus( params.get("thumbnail") )
    plot = unicode( xbmc.getInfoLabel( "ListItem.Plot" ), "utf-8" )
    server = params["server"]

    xbmctools.playvideo(CHANNELNAME,server,url,category,title,thumbnail,plot)

def play2(params,url,category):
    logger.info("[cineadicto.py] play2")
    url1 = url
    if "|" in url:
        urlsplited = url.split("|")
        url1 = urlsplited[0]
        urlsubtit = urlsplited[1]
        subt_ok = "0"
        while subt_ok == "0":
            subt_ok = downloadstr(urlsubtit)
            print "subtitulo subt_ok = %s" % str(subt_ok)
            if subt_ok is None: # si es None la descarga del subtitulo esta ok
                config.set_setting("subtitulo", "true")
                break
    play(params,url1,category)


def acentos(title):
    title = title.replace("Ã‚Â", "")
    title = title.replace("ÃƒÂ©","é")
    title = title.replace("ÃƒÂ¡","á")
    title = title.replace("ÃƒÂ³","ó")
    title = title.replace("ÃƒÂº","ú")
    title = title.replace("ÃƒÂ­","í")
    title = title.replace("ÃƒÂ±","ñ")
    title = title.replace("Ã¢â‚¬Â", "")
    title = title.replace("Ã¢â‚¬Å“Ã‚Â", "")
    title = title.replace("Ã¢â‚¬Å“","")
    title = title.replace("Ã©","é")
    title = title.replace("Ã¡","á")
    title = title.replace("Ã³","ó")
    title = title.replace("Ãº","ú")
    title = title.replace("Ã­","í")
    title = title.replace("Ã±","ñ")
    title = title.replace("Ãƒâ€œ","Ó")
    return(title)
        
def downloadstr(urlsub):
    
    import downloadtools
    
    fullpath = os.path.join( config.DATA_PATH, 'subtitulo.srt' )
    if os.path.exists(fullpath):
        try:
            subtitfile = open(fullpath,"w")
            subtitfile.close()
        except IOError:
            logger.info("Error al limpiar el archivo subtitulo.srt "+fullpath)
            raise
    try:        
        ok = downloadtools.downloadfile(urlsub,fullpath)
    except IOError:
        logger.info("Error al descargar el subtitulo "+urlsub)
        return -1
    return ok

def getpost(url,values): # Descarga la pagina con envio de un Form
    
    #url=url
    try:
        data = urllib.urlencode(values)          
        req = urllib2.Request(url, data)
        response = urllib2.urlopen(req)
        the_page = response.read() 
        return the_page 
    except Exception: 
        return "Err "     
