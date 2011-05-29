# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para programastv
# Autor: blablableble
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

from HTMLParser import HTMLParser
import htmllib, formatter
 
class LinksExtractor(htmllib.HTMLParser): # derive new HTML parser
    def __init__(self, formatter) :        # class constructor
        htmllib.HTMLParser.__init__(self, formatter)  # base class constructor
        self.links = []        # create an empty list for storing hyperlinks
 
    def start_a(self, attrs):  # override handler of <A ...>...</A> tags
        if len(attrs) > 0 :
            print "The raw tuple data is:", attrs
            for attr in attrs:
 
                if attr[0] == "href": 
                    self.links.append(attr[1]) # save the link info in the list
 
    def get_links(self) :     # return the list of extracted links
        return self.links
 
 
 
import htmllib
import formatter
import string
 
class MyParser(htmllib.HTMLParser):
    # return a dictionary mapping anchor texts to lists
    # of associated hyperlinks
 
    def __init__(self, verbose=0):
        self.anchors = {}
        f = formatter.NullFormatter()
        htmllib.HTMLParser.__init__(self, f, verbose)
 
    def anchor_bgn(self, href, name, type):
        self.save_bgn()
        self.anchor = href
 
    def anchor_end(self):
        text = string.strip(self.save_end())
        if self.anchor and text:
            self.anchors[text] = self.anchors.get(text, []) + [self.anchor]
 
CHANNELNAME = "programastv"
 
# Esto permite su ejecución en modo emulado
try:
    pluginhandle = int( sys.argv[ 1 ] )
except:
    pluginhandle = ""
 
# Traza el inicio del canal
logger.info("[programastv.py] init")
 
DEBUG = True
 
def mainlist(params,url,category):
    logger.info("[programastv.py] mainlist")
 
    itemlist = getmainlist(params,url,category)
    xbmctools.renderItems(itemlist, params, url, category)
 
def getmainlist(params,url,category):
    logger.info("[programastv.py] getmainlist")
 
    itemlist = []
    itemlist.append( Item(channel=CHANNELNAME, title="Secciones"  , action="secciones", url="http://programastvonline.blogspot.com/"      , folder=True) )
    itemlist.append( Item(channel=CHANNELNAME, title="Novedades"      , action="parsear", url="http://programastvonline.blogspot.com/", folder=True) )
    itemlist.append( Item(channel=CHANNELNAME, title="Buscar"                                , action="search"             , url=""                                       , folder=True) )
 
 
    return itemlist
 
def search(params,url,category):
    logger.info("[programastv.py] search")
 
    keyboard = xbmc.Keyboard('')
    keyboard.doModal()
    if (keyboard.isConfirmed()):
        tecleado = keyboard.getText()
        if len(tecleado)>0:
            #convert to HTML
            tecleado = tecleado.replace(" ", "+")
            searchUrl = "http://programastvonline.blogspot.com/search?q="+tecleado
            itemlist=[]
            itemlist.append( Item(channel=CHANNELNAME, title=tecleado      , action="parsear", url="http://programastvonline.blogspot.com/search?q="+tecleado, folder=True) )
 
            #searchresults(params,searchUrl,category)
    xbmctools.renderItems(itemlist, params, url, category)
    xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )
 
    # Disable sorting...
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
 
    # End of directory...
    xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )
 
def searchresults(params,url,category):
    logger.info("[programastv.py] searchresults")
 
    itemlist = getsearchresults(params,url,category)
    xbmctools.renderItems(itemlist, params, url, category)
 
def getsearchresults(params,url,category):
    logger.info("[programastv.py] getsearchresults")
 
    if (not url.startswith("http://")):
        url = "http://www.programastv.es/buscar/peliculas/?palabra="+url+"&categoria=&valoracion="
 
    return getlistpeliconcaratula(params,url,category)
 
def secciones(params,url,category):
    logger.info("[programastv.py] seccions")
 
    itemlist = getsecciones(params,url,category)
    xbmctools.renderItems(itemlist, params, url, category)
 
def getsecciones(params,url,category):
    logger.info("[programastv.py] getsecciones")
 
    # ------------------------------------------------------
    # Descarga la página
    # ------------------------------------------------------
    data = scrapertools.cachePage(url)
 
    #logger.info(data)
 
    # ------------------------------------------------------
    # Extrae las entradas
    # ------------------------------------------------------
    # seccion novedades
    '''
    <!--PELICULA-->
    <div class="peli_item textcenter">
    <div class="pelicula_img"><a href='/peliculas/thriller/ver-pelicula-un-segundo-despues-2.html' >
    <img src="http://caratulas.programastv.es/pelis/7058.jpg" alt="Un segundo despu&eacute;s 2" /></a>
    </div><a href="/peliculas/thriller/ver-pelicula-un-segundo-despues-2.html" ><div class="dvdrip"></div></a><a href='/peliculas/thriller/ver-pelicula-un-segundo-despues-2.html' ><p class="white">Un segundo despu&eacute;s 2</p></a><p><span class="rosa">DVD-RIP</span></p><div class="icos_lg"><img src="http://caratulas.programastv.es/img/cont/espanol.png" alt="espanol" /><img src="http://caratulas.programastv.es/img/cont/megavideo.png" alt="" /><img src="http://caratulas.programastv.es/img/cont/ddirecta.png" alt="descarga directa" /> </div>
    </div>
    <!--FIN PELICULA-->
    '''
    # listado alfabetico
    '''
    <!--PELICULA-->
    <div class="peli_item textcenter">
    <div class="pelicula_img"><a href="/peliculas/musical/ver-pelicula-a-chorus-line.html">
    <img src="http://caratulas.programastv.es/pelis/246.jpg" alt="A Chorus Line" /></a>
    </div>
    <a href="/peliculas/musical/ver-pelicula-a-chorus-line.html"><p class="white">A Chorus Line</p></a>
    <p><span class="rosa">DVD-RIP</span></p><div class="icos_lg"><img src="http://caratulas.programastv.es/img/cont/espanol.png" alt="espanol" /><img src="http://caratulas.programastv.es/img/cont/megavideo.png" alt="" /><img src="http://caratulas.programastv.es/img/cont/ddirecta.png" alt="descarga directa" /> </div>                                    </div>
    <!--FIN PELICULA-->
    '''
    patronvideos  = '<a dir=\'ltr\' href=\'(.+?)\'>(.+?)</a>'
    #patronvideos += '<div class="peli_item textcenter">[^<]+'
    #patronvideos += '<div class="pelicula_img"><a[^<]+'
    #patronvideos += '<img src="([^"]+)"[^<]+</a>[^<]+'
    #patronvideos += '</div[^<]+<a href="([^"]+)".*?<p class="white">([^<]+)</p>.*?<p><span class="rosa">([^>]+)</span></p><div class="icos_lg">(.*?)</div>'
 
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    if DEBUG: scrapertools.printMatches(matches)
 
    itemlist = []
    for match in matches:
        # Titulo
        scrapedtitle = match[1]
        scrapedurl = match[0]
        itemlist.append( Item(channel=CHANNELNAME, title=match[1] , action="parsear", url=match[0], folder=True) )
 
        #scrapedtitle = match[2] + " [" + match[3] + "]"
        #matchesconectores = re.compile('<img.*?alt="([^"]*)"',re.DOTALL).findall(match[4])
        #conectores = ""
        #for matchconector in matchesconectores:
        #    logger.info("matchconector="+matchconector)
        #    if matchconector=="":
        #        matchconector = "megavideo"
        #    conectores = conectores + matchconector + "/"
        #if len(matchesconectores)>0:
        #    scrapedtitle = scrapedtitle + " (" + conectores[:-1] + ")"
 
        ## Convierte desde UTF-8 y quita entidades HTML
        #try:
        #    scrapedtitle = unicode( scrapedtitle, "utf-8" ).encode("iso-8859-1")
        #except:
        #    pass
        #scrapedtitle = scrapertools.entityunescape(scrapedtitle)
 
        ## procesa el resto
        #scrapedplot = ""
 
        #scrapedurl = urlparse.urljoin("http://www.programastv.es/",match[1])
        #scrapedthumbnail = match[0]
        #if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")
 
        ## Añade al listado de XBMC
        #itemlist.append( Item(channel=CHANNELNAME, action="listmirrors", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )
 
    # ------------------------------------------------------
    # Extrae el paginador
    # ------------------------------------------------------
    #<li class="navs"><a class="pag_next" href="/peliculas-todas/2.html"></a></li>
    #patronvideos  = '<li class="navs"><a class="pag_next" href="([^"]+)"></a></li>'
    #matches = re.compile(patronvideos,re.DOTALL).findall(data)
    #scrapertools.printMatches(matches)
 
    #if len(matches)>0:
    #    scrapedurl = urlparse.urljoin(url,matches[0])
    #    itemlist.append( Item(channel=CHANNELNAME, action="listpeliconcaratula", title="!Página siguiente" , url=scrapedurl , folder=True) )
 
    return itemlist
 
def parsear(params,url,category):
    logger.info("[programastv.py] parsear")
 
    itemlist = parse(params,url,category)
    xbmctools.renderItems(itemlist, params, url, category)
 
def parse(params,url,category):
    logger.info("[programastv.py] parse")
 
    # ------------------------------------------------------
    # Descarga la página
    # ------------------------------------------------------
    data = scrapertools.cachePage(url)
    #logger.info(data)
    # ------------------------------------------------------
    # Extrae las entradas
    # ------------------------------------------------------
    patronvideos  = 'class=\'post-title entry-title\'>.+?<a href=\'(.+?)\'>(.+?)</a>.+?class=\'post-body entry-content\'>(.+?)<'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    if DEBUG: scrapertools.printMatches(matches)
    itemlist = []
    for match in matches:
        # Titulo
        scrapedtitle = match[1]
        scrapedurl = match[0]
        itemlist.append( Item(channel=CHANNELNAME, title=match[1] , action="searchvideos", url=match[0], folder=True) )
 
    patronvideos  = 'class=\'blog-pager-older-link\' href=\'(.+?)\'.*?title=\'(.+?)\''
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    if len(matches)>0:
        itemlist.append( Item(channel=CHANNELNAME, title=matches[0][1],action="parsear", url=matches[0][0], folder=True) )
 
    patronvideos  = 'class=\'blog-pager-newer-link\' href=\'(.+?)\'.*?title=\'(.+?)\''
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    if len(matches)>0:
        itemlist.append( Item(channel=CHANNELNAME, title=matches[0][1],action="parsear", url=matches[0][0], folder=True) )
 
 
    return itemlist
 
def searchvideos(params, url, category):
    logger.info("[programastv.py] parse")
 
    # ------------------------------------------------------
    # Descarga la página
    # ------------------------------------------------------
    data = scrapertools.cachePage(url)
    #logger.info(data)
    # ------------------------------------------------------
    # Extrae las entradas
    # ------------------------------------------------------
    #quitamos a partir de los comentarios
    data=data[0:data.index('class=\'post-footer\'>')]
    videos=servertools.findvideos(data)
 
    #xbmc.output( videos[0][2] + " es 02")
    #xbmc.output( videos[1][2] + " es 12")
    #TODO extract plot y thumbnail
    if len(videos)>0:
        if (videos[0][2] == "Megavideo") and (videos[1][2] == "Megaupload"):
            xbmc.output("asumimos que solo hay un video con dos mirrors")
            patronvideos  = 'class=\'post-title entry-title\'>.+?<a href=\'.+?\'>(.+?)</a>'
            matches = re.compile(patronvideos,re.DOTALL).findall(data)
            xbmc.output(matches[0])
            xbmctools.addnewvideo( CHANNELNAME , "play" , category , "Megavideo" , matches[0] , videos[0][1] , "" , "" )
            xbmctools.addnewvideo( CHANNELNAME , "play" , category , "Megaupload" , matches[0] , videos[1][1] , "" , "" )
        elif len(videos)==1:
            if re.search('&amp;xtp=(.+?)_VIDEO',videos[0][1]):
                patronvideos  = '&amp;xtp=(.+?)_VIDEO'
                matches = re.compile(patronvideos,re.DOTALL).findall(data)
                videos[0][1]=matches[0]
            xbmc.output("aqui estamos")
            patronvideos  = 'class=\'post-title entry-title\'>.+?<a href=\'.+?\'>(.+?)</a>'
            matches = re.compile(patronvideos,re.DOTALL).findall(data)    
            xbmctools.addnewvideo( CHANNELNAME , "play" , category , videos[0][2] , matches[0] , videos[0][1] , "" , "" )
        else:
            xbmc.output("hay mas de 1 video")
            for video in videos:
                if video[2].find("youtube")!=-1:
                    continue   
                #xbmc.output(video[2] + video[1] + " 2 + 1")
                indexvideo=data.index(video[1])
                #xbmc.output(str(indexvideo))
                #if (video[2]=="Megaupload"):
                #    #xbmc.output(str(indexvideo))
                #    indexvideo=data.rindex(">-",0,indexvideo)
                #    #xbmc.output(str(indexvideo))
                indexvideo1=data.rindex(">-",0,indexvideo)
                #xbmc.output(str(indexvideo1))
                indexvideo2=data.rindex(">-",0,indexvideo1)
                #xbmc.output(str(indexvideo2))
                #xbmc.output(data[indexvideo2+1:indexvideo1])
                nombre=re.sub('<.+?>','',data[indexvideo2+3:indexvideo1-5])
                while re.search('egaupl', nombre) or re.search('egavid', nombre):
                     indexvideo3=data.rindex(">-",0,    indexvideo2)
                     nombre=re.sub('<.+?>','',data[indexvideo3+3:indexvideo2-5])
                     indexvideo2=indexvideo3
                xbmctools.addnewvideo( CHANNELNAME , "play" , category , video[2] , nombre + " " + video[2] , video[1] , "" , "" )    
    else:
        xbmc.output("es un listado")
        #xbmc.output(data)
        data=data[data.index('class=\'post-header-line-1\'')+33:]
        #xbmc.output(data)
        xbmc.output("aqui llego")
 
        p = MyParser()
        p.feed(data)
        p.close()
        itemlist = []
        for k, v in p.anchors.items():
            print k, "=>", v
 
            if re.search('programastvonline.blogspot.com',v[0]):
                itemlist.append( Item(channel=CHANNELNAME, title=k , action="parsear", url=v[0], folder=True) )
        xbmctools.renderItems(itemlist, params, url, category)
 
 
 
            #'egaupl', nombre)
 
        #myparser=MyParser(data)
        #myparser.parse(data)
        #links = myparser.get_hyperlinks()   # get the hyperlinks list
        #xbmc.output(str(len(links)))   # print all the links
        #descriptions = myparser.get_descriptions()   # get the hyperlinks list
        #xbmc.output("b",descriptions)   # print all the links        
        #xbmc.output("aqui llego 1")
        #post-header-line-1
        #format = formatter.NullFormatter()           # create default formatter
        #htmlparser = LinksExtractor(format)        # create new parser object
 
 
#        for video in listavideos:
#            videotitle = video[0]
#            scrapedurl = video[1]
#            server = video[2]
#            xbmctools.addnewvideo( CHANNELNAME , "play" , category , server , title.strip()+" "+match[1]+" "+match[2]+" "+videotitle , scrapedurl , thumbnail , plot )
 
    # ------------------------------------------------------------------------------------
    # Busca los enlaces a los videos
    # ------------------------------------------------------------------------------------
 
    # ------------------------------------------------------------------------------------
 
    # Label (top-right)...
    xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )
 
    # Disable sorting...
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
 
    # End of directory...
    xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )
 
 
 
def listtemporadacaratula(params,url,category):
    logger.info("[programastv.py] listtemporadacaratula")
 
    # ------------------------------------------------------
    # Descarga la página
    # ------------------------------------------------------
    data = scrapertools.cachePage(url)
    #logger.info(data)
 
    # ------------------------------------------------------
    # Extrae las entradas
    # ------------------------------------------------------
    '''
    <li>
    <a href="/series/the-middleman/temporada-1/"><img src="http://caratulas.programastv.es/series/233.jpg" alt="peli" /></a>
    <p><span class="rosa"></span></p><div class="icos_lg"><img src="http://caratulas.programastv.es/img/cont/sub.png" alt="sub" /><img src="http://caratulas.programastv.es/img/cont/megavideo.png" alt="" /> </div>                                        <p class="tit_ficha">The middleman </p>
    <p class="tem_fich">1a Temporada</p>
    </li>
    '''
    '''
    <li>
    <a href="/series/cranford-de-e-gaskell/"><img src="http://caratulas.programastv.es/series/64.jpg" alt="peli" /></a>
    <p><span class="rosa"></span></p><div class="icos_lg"><img src="http://caratulas.programastv.es/img/cont/sub.png" alt="sub" /><img src="http://caratulas.programastv.es/img/cont/megavideo.png" alt="" /><img src="http://caratulas.programastv.es/img/cont/ddirecta.png" alt="descarga directa" /> </div>                                        <p class="tit_ficha">Cranford, de E. Gaskell </p>
    </li>
    '''
    patronvideos  = '<li>[^<]+'
    patronvideos += '<a href="([^"]+)"><img src="([^"]+)"[^>]+></a>[^<]+'
    patronvideos += '<p><span class="rosa"></span></p><div class="icos_lg">(.*?)</div>[^<]+'
    patronvideos += '<p class="tit_ficha">([^<]+)</p>[^<]+'
    patronvideos += '<p class="tem_fich">([^<]+)</p>[^<]+'
    patronvideos += '</li>'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    if DEBUG:
        scrapertools.printMatches(matches)
 
    for match in matches:
        # Titulo
        scrapedtitle = match[3].strip() + " - " + match[4].strip()
        matchesconectores = re.compile('<img.*?alt="([^"]*)"',re.DOTALL).findall(match[2])
        conectores = ""
        for matchconector in matchesconectores:
            logger.info("matchconector="+matchconector)
            if matchconector=="":
                matchconector = "megavideo"
            conectores = conectores + matchconector + "/"
        if len(matchesconectores)>0:
            scrapedtitle = scrapedtitle + " (" + conectores[:-1] + ")"
 
        # Convierte desde UTF-8 y quita entidades HTML
        try:
            scrapedtitle = unicode( scrapedtitle, "utf-8" ).encode("iso-8859-1")
        except:
            pass
        scrapedtitle = scrapertools.entityunescape(scrapedtitle)
 
 
        # procesa el resto
        scrapedplot = ""
 
        scrapedurl = urlparse.urljoin(url,match[0])
        scrapedthumbnail = match[1]
        if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")
 
        # Añade al listado de XBMC
        xbmctools.addnewfolder( CHANNELNAME , "listmirrors" , category , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )
 
    # ------------------------------------------------------
    # Extrae el paginador
    # ------------------------------------------------------
    #<li class="navs"><a class="pag_next" href="/peliculas-todas/2.html"></a></li>
    patronvideos  = '<li class="navs"><a class="pag_next" href="([^"]+)"></a></li>'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)
 
    if len(matches)>0:
        xbmctools.addnewfolder( CHANNELNAME , "listtemporadacaratula" , category , "!Página siguiente" , urlparse.urljoin(url,matches[0]) , "", "" )
 
    # Label (top-right)...
    xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
    xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )
 
def listserieconcaratula(params,url,category):
    logger.info("[programastv.py] listserieconcaratula")
 
    # ------------------------------------------------------
    # Descarga la página
    # ------------------------------------------------------
    data = scrapertools.cachePage(url)
    #logger.info(data)
 
    # ------------------------------------------------------
    # Extrae las entradas
    # ------------------------------------------------------
    '''
    <li>
    <a href="/series/the-middleman/temporada-1/"><img src="http://caratulas.programastv.es/series/233.jpg" alt="peli" /></a>
    <p><span class="rosa"></span></p><div class="icos_lg"><img src="http://caratulas.programastv.es/img/cont/sub.png" alt="sub" /><img src="http://caratulas.programastv.es/img/cont/megavideo.png" alt="" /> </div>                                        <p class="tit_ficha">The middleman </p>
    <p class="tem_fich">1a Temporada</p>
    </li>
    '''
    '''
    <li>
    <a href="/series/cranford-de-e-gaskell/"><img src="http://caratulas.programastv.es/series/64.jpg" alt="peli" /></a>
    <p><span class="rosa"></span></p><div class="icos_lg"><img src="http://caratulas.programastv.es/img/cont/sub.png" alt="sub" /><img src="http://caratulas.programastv.es/img/cont/megavideo.png" alt="" /><img src="http://caratulas.programastv.es/img/cont/ddirecta.png" alt="descarga directa" /> </div>                                        <p class="tit_ficha">Cranford, de E. Gaskell </p>
    </li>
    '''
    patronvideos  = '<li>[^<]+'
    patronvideos += '<a href="([^"]+)"><img src="([^"]+)"[^>]+></a>[^<]+'
    patronvideos += '<p><span class="rosa"></span></p><div class="icos_lg">(.*?)</div>[^<]+'
    patronvideos += '<p class="tit_ficha">([^<]+)</p>[^<]+'
    patronvideos += '</li>'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    if DEBUG:
        scrapertools.printMatches(matches)
 
    for match in matches:
        # Titulo
        scrapedtitle = match[3].strip()
        matchesconectores = re.compile('<img.*?alt="([^"]*)"',re.DOTALL).findall(match[2])
        conectores = ""
        for matchconector in matchesconectores:
            logger.info("matchconector="+matchconector)
            if matchconector=="":
                matchconector = "megavideo"
            conectores = conectores + matchconector + "/"
        if len(matchesconectores)>0:
            scrapedtitle = scrapedtitle + " (" + conectores[:-1] + ")"
 
        # Convierte desde UTF-8 y quita entidades HTML
        try:
            scrapedtitle = unicode( scrapedtitle, "utf-8" ).encode("iso-8859-1")
        except:
            pass
        scrapedtitle = scrapertools.entityunescape(scrapedtitle)
 
 
        # procesa el resto
        scrapedplot = ""
 
        scrapedurl = urlparse.urljoin(url,match[0])
        scrapedthumbnail = match[1]
        if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")
 
        # Añade al listado de XBMC
        xbmctools.addnewfolder( CHANNELNAME , "listmirrors" , category , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )
 
    # ------------------------------------------------------
    # Extrae el paginador
    # ------------------------------------------------------
    #<li class="navs"><a class="pag_next" href="/peliculas-todas/2.html"></a></li>
    patronvideos  = '<li class="navs"><a class="pag_next" href="([^"]+)"></a></li>'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)
 
    if len(matches)>0:
        xbmctools.addnewfolder( CHANNELNAME , "listserieconcaratula" , category , "!Página siguiente" , urlparse.urljoin(url,matches[0]) , "", "" )
 
    # Label (top-right)...
    xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
    xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )
 
def listseriesincaratula(params,url,category):
    logger.info("[programastv.py] listseriesincaratula")
    # ------------------------------------------------------
    # Descarga la página
    # ------------------------------------------------------
    data = scrapertools.cachePage(url)
    #logger.info(data)
 
    # ------------------------------------------------------
    # Extrae las entradas
    # ------------------------------------------------------
    '''
    <!--SERIE-->
    <div class="pelicula_bar_border">
    <div class="pelicula_bar series iframe3">
    <ul class="tabs-nav" id="video-1687">
    <li><span style="cursor:pointer;" class="peli_ico_1 bold" onclick="location.href='/peliculas/drama/ver-pelicula-belleza-robada.html'">Belleza robada </a></span></li>
    <li><a class="peli_ico_3" style="margin-left:10px;" href="/peliculas/drama/ver-pelicula-belleza-robada.html"><span>&nbsp;Ver ficha</span></a></li>
    </ul>
    </div>
    <div id="p_ver1" class="peli_bg1" style="display:none;">
    &nbsp;
    </div>
    </div>
    '''
    '''
    <!--SERIE-->
    <div class="pelicula_bar_border">
    <div class="pelicula_bar series iframe3">
    <ul class="tabs-nav" id="video-1692">
    <li><span style="cursor:pointer;" class="peli_ico_1 bold" onclick="location.href='/peliculas/terror/ver-pelicula-bendicion-mortal.html'">Bendici&oacute;n mortal </a></span></li>
    <li><a class="peli_ico_3" style="margin-left:10px;" href="/peliculas/terror/ver-pelicula-bendicion-mortal.html"><span>&nbsp;Ver ficha</span></a></li>
    </ul>
    </div>
    <div id="p_ver1" class="peli_bg1" style="display:none;">
    &nbsp;
    </div>
    </div>
    '''
    patronvideos  = '<!--SERIE-->[^<]+'
    patronvideos += '<div class="pelicula_bar_border">[^<]+'
    patronvideos += '<div class="pelicula_bar series iframe3">[^<]+'
    patronvideos += '<ul class="tabs-nav" id="([^"]+)">[^<]+'
    patronvideos += '<li><span[^>]+>([^<]+)</a></span></li>[^<]+'
    patronvideos += '<li><a.*?href="([^"]+)"'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)
 
    for match in matches:
        # Titulo
        try:
            scrapedtitle = unicode( match[1], "utf-8" ).encode("iso-8859-1")
        except:
            scrapedtitle = match[1]
        scrapedtitle = scrapertools.entityunescape(scrapedtitle)
        scrapedplot = ""
        scrapedurl = urlparse.urljoin(url,match[2])
        scrapedthumbnail = ""
        if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")
 
        # Añade al listado de XBMC
        xbmctools.addnewfolder( CHANNELNAME , "listmirrors" , category , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )
 
    # ------------------------------------------------------
    # Extrae el paginador
    # ------------------------------------------------------
    #<li class="navs"><a class="pag_next" href="/peliculas-todas/2.html"></a></li>
    patronvideos  = '<li class="navs"><a class="pag_next" href="([^"]+)"></a></li>'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)
 
    if len(matches)>0:
        xbmctools.addnewfolder( CHANNELNAME , "listseriesincaratula" , category , "!Página siguiente" , urlparse.urljoin(url,matches[0]) , "", "" )
 
    # Label (top-right)...
    xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_TITLE )
    xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )
 
def listalfabeticodocumentales(params, url, category):
    addfolder("0-9","http://www.programastv.es/subindices/idocumentalesnumero.html","list")
    addfolder("A","http://www.programastv.es/subindices/idocumentalesa.html","list")
    addfolder("B","http://www.programastv.es/subindices/idocumentalesb.html","list")
    addfolder("C","http://www.programastv.es/subindices/idocumentalesc.html","list")
    addfolder("D","http://www.programastv.es/subindices/idocumentalesd.html","list")
    addfolder("E","http://www.programastv.es/subindices/idocumentalese.html","list")
    addfolder("F","http://www.programastv.es/subindices/idocumentalesf.html","list")
    addfolder("G","http://www.programastv.es/subindices/idocumentalesg.html","list")
    addfolder("H","http://www.programastv.es/subindices/idocumentalesh.html","list")
    addfolder("I","http://www.programastv.es/subindices/idocumentalesi.html","list")
    addfolder("J","http://www.programastv.es/subindices/idocumentalesj.html","list")
    addfolder("K","http://www.programastv.es/subindices/idocumentalesk.html","list")
    addfolder("L","http://www.programastv.es/subindices/idocumentalesl.html","list")
    addfolder("M","http://www.programastv.es/subindices/idocumentalesm.html","list")
    addfolder("N","http://www.programastv.es/subindices/idocumentalesn.html","list")
    addfolder("O","http://www.programastv.es/subindices/idocumentaleso.html","list")
    addfolder("P","http://www.programastv.es/subindices/idocumentalesp.html","list")
    addfolder("Q","http://www.programastv.es/subindices/idocumentalesq.html","list")
    addfolder("R","http://www.programastv.es/subindices/idocumentalesr.html","list")
    addfolder("S","http://www.programastv.es/subindices/idocumentaless.html","list")
    addfolder("T","http://www.programastv.es/subindices/idocumentalest.html","list")
    addfolder("U","http://www.programastv.es/subindices/idocumentalesu.html","list")
    addfolder("V","http://www.programastv.es/subindices/idocumentalesv.html","list")
    addfolder("W","http://www.programastv.es/subindices/idocumentalesw.html","list")
    addfolder("X","http://www.programastv.es/subindices/idocumentalesx.html","list")
    addfolder("Y","http://www.programastv.es/subindices/idocumentalesy.html","list")
    addfolder("Z","http://www.programastv.es/subindices/idocumentalesz.html","list")
 
    # Cierra el directorio
    xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
    xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )
 
def listmirrors(params,url,category):
    logger.info("[programastv.py] listmirrors")
 
    title = urllib.unquote_plus( params.get("title") )
    thumbnail = urllib.unquote_plus( params.get("thumbnail") )
    #plot = unicode( xbmc.getInfoLabel( "ListItem.Plot" ), "utf-8" )
    plot = urllib.unquote_plus( params.get("plot") )
 
    # ------------------------------------------------------------------------------------
    # Descarga la página
    # ------------------------------------------------------------------------------------
    data = scrapertools.cachePage(url)
    #logger.info(data)
 
    # ------------------------------------------------------------------------------------
    # Busca el argumento
    # ------------------------------------------------------------------------------------
    patronvideos  = '<div class="ficha_des">(.*?)</div>'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    if len(matches)>0:
        plot = scrapertools.htmlclean(matches[0])
        logger.info("plot actualizado en detalle");
    else:
        logger.info("plot no actualizado en detalle");
 
    # ------------------------------------------------------------------------------------
    # Busca el thumbnail
    # ------------------------------------------------------------------------------------
    patronvideos  = '<div class="ficha_img pelicula_img">[^<]+'
    patronvideos += '<img src="([^"]+)"'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    if len(matches)>0:
        thumbnail = matches[0]
        logger.info("thumb actualizado en detalle");
    else:
        logger.info("thumb no actualizado en detalle");
 
    # ------------------------------------------------------------------------------------
    # Busca los enlaces a los mirrors, o a los capítulos de las series...
    # ------------------------------------------------------------------------------------
    #    url = "http://www.programastv.es/inc/mostrar_contenido.php?sec=pelis_ficha&zona=online&id=video-4637"
    #patronvideos  = '<div class="ver_des_peli iframe2">[^<]+'
    #patronvideos += '<ul class="tabs-nav" id="([^"]+)">'
    #matches = re.compile(patronvideos,re.DOTALL).findall(data)
    #data = scrapertools.cachePage("http://www.programastv.es/inc/mostrar_contenido.php?sec=pelis_ficha&zona=online&id="+matches[0])
 
    '''
    <div id="ficha_ver_peli">
    <div class="v_online">
    <h2>Ver online <span>El destino de Nunik</span></h2>
    <div class="opstions_pelicula_list">
    <div class="tit_opts" style="cursor:pointer;" onclick="location.href='http://www.programastv.es/peliculas/drama/el-destino-de-nunik_espanol-dvd-rip-megavideo-6026.html'">
    <p>Mirror 1: Megavideo</p>
    <p><span>CALIDAD: DVD-RIP | IDIOMA: ESPA&Ntilde;OL</span></p>
    <p class="v_ico"><img src="http://caratulas.programastv.es/img/cont/megavideo.png" alt="Megavideo" /></p>
    </div>
    <div class="tit_opts" style="cursor:pointer;" onclick="location.href='http://www.programastv.es/peliculas/drama/el-destino-de-nunik_espanol-dvd-rip-megavideo-6027.html'">
    <p>Mirror 2: Megavideo</p>
    <p><span>CALIDAD: DVD-RIP | IDIOMA: ESPA&Ntilde;OL</span></p>
    <p class="v_ico"><img src="http://caratulas.programastv.es/img/cont/megavideo.png" alt="Megavideo" /></p>
    </div>
    </div>
    </div>
    </div> 
    '''
    '''
    <div class="v_online">
    <h2>Ver online <span>Cantajuego 6</span></h2>
    <div class="opstions_pelicula_list"><div class="tit_opts"><a href="/peliculas/animacion-e-infantil/cantajuego-6_espanol-dvd-rip-megavideo-73371.html">
    <p>Mirror 1: Megavideo</p>
    <p><span>CALIDAD: DVD-RIP | IDIOMA: ESPA&Ntilde;OL</span></p>
    <p class="v_ico"><img src="http://caratulas.programastv.es/img/cont/megavideo.png" alt="Megavideo" /></p>
    </a></div>                </div>
    </div>
    </div><br/><div id="ficha_desc_peli">
    <div class="v_online">
    <h2 class="ico_fuego">Descargar <span>Cantajuego 6</span></h2>
    <div class="opstions_pelicula_list"><div class="tit_opts"><a href="/peliculas/animacion-e-infantil/descargar-cantajuego-6_espanol-dvd-rip-megaupload-73372.html" target="_blank">
    <p>Mirror 1: Megaupload </p>
    <p><span>CALIDAD: DVD-RIP | IDIOMA: ESPA&Ntilde;OL </span></p>
    <p class="v_ico"><img src="http://caratulas.programastv.es/img/cont/megaupload.png" alt="Megaupload" /></p>
    </a></div>
    </div>
    </div>
    </div>
    '''
    #patronvideos  = '<div class="tit_opts"><a href="([^"]+)">[^<]+'
    patronvideos = '<div class="tit_opts"><a href="([^"]+)".*?>[^<]+'
    patronvideos += '<p>([^<]+)</p>[^<]+'
    patronvideos += '<p><span>([^<]+)</span>'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
 
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
            videotitle = video[0]
            scrapedurl = video[1]
            server = video[2]
            xbmctools.addnewvideo( CHANNELNAME , "play" , category , server , title.strip()+" "+match[1]+" "+match[2]+" "+videotitle , scrapedurl , thumbnail , plot )
 
    # ------------------------------------------------------------------------------------
    # Busca los enlaces a los videos
    # ------------------------------------------------------------------------------------
 
    # ------------------------------------------------------------------------------------
 
    # Label (top-right)...
    xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )
 
    # Disable sorting...
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
 
    # End of directory...
    xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )
 
def play(params,url,category):
    logger.info("[programastv.py] play")
 
    title = urllib.unquote_plus( params.get("title") )
    thumbnail = urllib.unquote_plus( params.get("thumbnail") )
    plot = unicode( xbmc.getInfoLabel( "ListItem.Plot" ), "utf-8" )
    server = params["server"]
 
    xbmctools.playvideo(CHANNELNAME,server,url,category,title,thumbnail,plot)
 
def addfolder(nombre,url,accion):
    logger.info('[programastv.py] addfolder( "'+nombre+'" , "' + url + '" , "'+accion+'")"')
    listitem = xbmcgui.ListItem( nombre , iconImage="DefaultFolder.png")
    itemurl = '%s?channel=programastv&action=%s&category=%s&url=%s' % ( sys.argv[ 0 ] , accion , urllib.quote_plus(nombre) , url )
    xbmcplugin.addDirectoryItem( handle = int(sys.argv[ 1 ]), url = itemurl , listitem=listitem, isFolder=True)
 
def addvideo(nombre,url,category,server):
    logger.info('[programastv.py] addvideo( "'+nombre+'" , "' + url + '" , "'+server+'")"')
    listitem = xbmcgui.ListItem( nombre, iconImage="DefaultVideo.png" )
    listitem.setInfo( "video", { "Title" : nombre, "Plot" : nombre } )
    itemurl = '%s?channel=programastv&action=play&category=%s&url=%s&server=%s' % ( sys.argv[ 0 ] , category , url , server )
    xbmcplugin.addDirectoryItem( handle=int(sys.argv[ 1 ]), url=itemurl, listitem=listitem, isFolder=False)
 
def addthumbnailfolder( scrapedtitle , scrapedurl , scrapedthumbnail , accion ):
    logger.info('[programastv.py] addthumbnailfolder( "'+scrapedtitle+'" , "' + scrapedurl + '" , "'+scrapedthumbnail+'" , "'+accion+'")"')
    listitem = xbmcgui.ListItem( scrapedtitle, iconImage="DefaultFolder.png", thumbnailImage=scrapedthumbnail )
    itemurl = '%s?channel=programastv&action=%s&category=%s&url=%s' % ( sys.argv[ 0 ] , accion , urllib.quote_plus( scrapedtitle ) , urllib.quote_plus( scrapedurl ) )
    xbmcplugin.addDirectoryItem( handle = int(sys.argv[ 1 ]), url = itemurl , listitem=listitem, isFolder=True)