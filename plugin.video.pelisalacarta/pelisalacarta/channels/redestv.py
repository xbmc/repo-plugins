# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para redestv
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#------------------------------------------------------------
import urlparse,urllib2,urllib,re
import os
import sys

from servers import bliptv
from pprint import pprint

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

CHANNELNAME = "redestv"
 
# Esto permite su ejecución en modo emulado
try:
    pluginhandle = int( sys.argv[ 1 ] )
except:
    pluginhandle = ""
 
# Traza el inicio del canal
logger.info("[redestv.py] init")
 
DEBUG = True
 
def mainlist(params,url,category):
    logger.info("[redestv.py] mainlist")
    #bliptv.video("+3KBt+grAg")
    # Añade al listado de XBMC
    xbmctools.addnewfolder( CHANNELNAME , "novedades" , category, "Novedades" , "http://www.redes-tv.com/" , "" , "")
    xbmctools.addnewfolder( CHANNELNAME , "buscacategorias" , category, "Categorias" , "http://www.redes-tv.com/index.php?option=com_xmap&sitemap=1&Itemid=31" , "" , "")
    xbmctools.addnewfolder( CHANNELNAME , "orden" , category, "Orden de emision" , "http://www.redes-tv.com/index.php?option=com_content&view=article&id=16&Itemid=30" , "" , "")
    xbmctools.addnewfolder( CHANNELNAME , "search" , category, "Búsqueda" , "" , "" , "")
 
     # Label (top-right)...
    xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
    xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )
 
def search(params,url,category):
    logger.info("[newdivx.py] search")
 
    keyboard = xbmc.Keyboard()
    #keyboard.setDefault('')
    keyboard.doModal()
    if (keyboard.isConfirmed()):
        tecleado = keyboard.getText()
        if len(tecleado)>0:
            #convert to HTML
            tecleado = tecleado.replace(" ", "+")
            searchUrl = "http://www.redes-tv.com/index.php?searchword="+tecleado+"&ordering=newest&searchphrase=all&limit=0&Itemid=3&option=com_search" 
            #searchUrl = "http://www.redestv.com/?s="+tecleado+"&searchsubmit="
            parsebusquedas(params,searchUrl,category)
 
 
def parsebusquedas(params,url,category):
    logger.info("[redestv.py] parsebusquedas")
    data = scrapertools.cachePage(url)
    #<td style="text-align: left;"><a href="/index.php?option=com_content&amp;view=article&amp;id=41:500-por-que-mas-es-menos&amp;catid=6:tercol&amp;Itemid=14" title="500: Por qué más es menos">500: Por qué más es menos</a></td>
    #<td style="text-align: center;">13 Ene 10</td>
 
    patronvideos  = '<fieldset>(.+?)</fieldset>'
 
    #logger.info("web"+data)
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)
    if len(matches)>0:
        for i in range(len(matches)):
            patronvideos  = '<a href="(.+?)">\s+(.+?)\s\s\s+</a>'
            matches1 = re.compile(patronvideos,re.DOTALL).findall(matches[i])
            scrapertools.printMatches(matches1)
            xbmctools.addnewvideo( CHANNELNAME , "buscavideos" , category , "redestv",  matches1[0][1] , matches1[0][0] , "thumbnail" , "")
    xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
    xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )
 
def buscacategorias(params,url,category):
    logger.info("[redestv.py] buscacategorias")
    data = scrapertools.cachePage(url)
    #href='http://www.redestv.com/category/arte/' title="ARTE">ARTE</a></li><li><a
    #href="/index.php?option=com_content&amp;view=category&amp;layout=blog&amp;id=1&amp;Itemid=9" title="Biotecnolog\xc3\xada y Salud"
    patronvideos  = 'href="/index\.php\?(option=com_content\&amp;view=category.*?)" title="(.+?)"'
    #pprint(data)
    #logger.info("web"+data)
    matches = re.compile(patronvideos).findall(data)
    #if DEBUG:
    scrapertools.printMatches(matches)
    if len(matches)>0:
        for i in range(len(matches)):
            xbmctools.addnewfolder( CHANNELNAME , "parsewebcategorias" , category, matches[i][1] , matches[i][0] , "" , "")
    xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
    xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )
 
def parsewebcategorias(params,url,category):
    logger.info("[redestv.py] buscacategorias")
    data = scrapertools.cachePage("http://www.redes-tv.com/index.php?option=com_xmap&sitemap=1&Itemid=31")
    #href='http://www.redestv.com/category/arte/' title="ARTE">ARTE</a></li><li><a
    #href="/index.php?option=com_content&amp;view=category&amp;layout=blog&amp;id=1&amp;Itemid=9" title="Biotecnolog\xc3\xada y Salud"
    patronvideos  = "index.php." + url + '(.*?)</ul>'
    #patronvideos=patronvideos.replace("&","\&")
    #patronvideos=patronvideos.replace(";","\;")
    #patronvideos=patronvideos.replace("=","\=")
    #patronvideos=patronvideos.replace("_","\_")
    #logger.info(patronvideos)
    #logger.info("web"+data)
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    if DEBUG:
        scrapertools.printMatches(matches)
    if len(matches)>0:
        #href="/index.php?option=com_content&amp;view=article&amp;id=65:473-farmacos-para-las-emociones&amp;catid=1:biosalud&amp;Itemid=9" title="473: FÃ¡rmacos para las emociones"
        patronvideos = 'href="(.+?)" title="(.+?)"'
        matches1 = re.compile(patronvideos).findall(matches[0])
        for i in range(len(matches1)):
            #xbmctools.addnewvideo( CHANNELNAME , "buscavideos" , category, matches1[i][1] , matches1[i][0] , "thumbnail" , "")
            xbmctools.addnewvideo( CHANNELNAME , "buscavideos" , category , "redestv",  matches1[i][1] , matches1[i][0] , "thumbnail" , "")
 
    xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
    xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )
 
def orden(params,url,category):
    logger.info("[redestv.py] buscacategorias")
    data = scrapertools.cachePage(url)
    #<td style="text-align: left;"><a href="/index.php?option=com_content&amp;view=article&amp;id=41:500-por-que-mas-es-menos&amp;catid=6:tercol&amp;Itemid=14" title="500: Por qué más es menos">500: Por qué más es menos</a></td>
    #<td style="text-align: center;">13 Ene 10</td>
 
    patronvideos  = '<td style="text-align: left;"><a href="(.+?)" title="(.+?)".+?<td style="text-align: center;">(.+?)</td>'
 
    #logger.info("web"+data)
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    #if DEBUG:
    scrapertools.printMatches(matches)
    if len(matches)>0:
        for i in range(len(matches)):
            xbmctools.addnewvideo( CHANNELNAME , "buscavideos" , category , "redestv",  matches[i][1] + " - " + matches[i][2], matches[i][0] , "thumbnail" , "")
            #xbmctools.addnewfolder( CHANNELNAME , "parseweb" , category, matches[i][1] , matches[i][0] , "" , "")
    xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
    xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )
 
def buscavideos(params,url,category):
    data = scrapertools.cachePage("http://www.redes-tv.com"+url)
    #<embed src="http://blip.tv/play/+3KB0rYcAg" type="application/x-shockwave-flash"
    patronvideos  = '\n<div style="text-align: justify;">.+?</div>'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    if DEBUG:
        scrapertools.printMatches(matches)    
    #<embed src="http://blip.tv/play/+3KB0rYcAg" type="application/x-shockwave-flash"    
    patronvideos  = '<embed src="(http://blip.tv/play/\+.*?)" type="application/x-shockwave-flash"'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    if DEBUG:
        scrapertools.printMatches(matches)
    #bliptv.bliptv("3011527")
    #mediaurl = bliptv.geturl(matches[0])
    #logger.info("mediaurl="+mediaurl)
    
    xbmctools.playvideo(CHANNELNAME,"bliptv",matches[0],"","","","")

def novedades(params,url,category):
    logger.info("[redestv.py] parseweb")
 
    # ------------------------------------------------------
    # Descarga la página
    # ------------------------------------------------------
    data = scrapertools.cachePage(url)
    #logger.info(data)
 
    #<div style="text-align: justify;">Cre?amos que el ser humano era el ?nico animal capaz de sentir empat?a.  Sin embargo, el altruismo existe en muchos otros animales. Estar  conectado con los dem?s, entenderlos y sentir su dolor no es exclusivo  del ser humano. El prim?tologo Frans de Waal, gran estudiador de las  emociones animales, habla con Punset sobre empat?a y simpat?a,  capacidades clave para el ?xito en la vida social.</div><div class="jcomments-links"> <a href="/index.php?option=com_content&amp;view=article&amp;id=161:501-nuestro-cerebro-altruista&amp;catid=2:cermen&amp;Itemid=10#addcomments" class="comment-link">Escribir un comentario</a></div> 
 
    patronvideos  = '<td class="contentheading" width="100%">.+?<a href="(.+?)" class="contentpagetitle">\s+(\d+.+?)</a>'
    #patronvideos  = '<div style="text-align: justify;">.+?</div>.+?<a href="(.+?)#'
 
    #logger.info("web"+data)
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    if DEBUG:
        scrapertools.printMatches(matches)
    #xbmctools.addnewfolder( CHANNELNAME , "buscavideos" , category, "redestv" , "http://www.redes-tv.com"+matches[0][0] , "" , "")
    #scrapertools.printMatches(matches)
 
    #    patronvideos1 = 'src="http://www.megavideo.com/v/(.{8}).+?".+?></embed>.*?<p>(.+?)</p><div'
    #    matches1 = re.compile(patronvideos1,re.DOTALL).findall(data)
    #    if DEBUG:
    #        scrapertools.printMatches(matches1)
 
    for i in range(len(matches)):
        xbmctools.addnewvideo( CHANNELNAME , "buscavideos" , category , "redestv" , matches[i][1] , matches[i][0] , "thumbnail" , "")
 
    xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
    xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )
 
 
 
 
######################################################################################
 
 
 
 
 
 
def listmirrors(params,url,category):
    logger.info("[redestv.py] detail")
 
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
 
    # ------------------------------------------------------------------------------------
    # Busca el thumbnail
    # ------------------------------------------------------------------------------------
    patronvideos  = '<div class="ficha_img pelicula_img">[^<]+'
    patronvideos += '<img src="([^"]+)"'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    if len(matches)>0:
        thumbnail = matches[0]
 
    # ------------------------------------------------------------------------------------
    # Busca los enlaces a los mirrors, o a los capítulos de las series...
    # ------------------------------------------------------------------------------------
    #    url = "http://www.redestv.es/inc/mostrar_contenido.php?sec=pelis_ficha&zona=online&id=video-4637"
    patronvideos  = '<div class="ver_des_peli iframe2">[^<]+'
    patronvideos += '<ul class="tabs-nav" id="([^"]+)">'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
 
    '''
    <div id="ficha_ver_peli">
    <div class="v_online">
    <h2>Ver online <span>El destino de Nunik</span></h2>
    <div class="opstions_pelicula_list">
    <div class="tit_opts" style="cursor:pointer;" onclick="location.href='http://www.redestv.es/peliculas/drama/el-destino-de-nunik_espanol-dvd-rip-megavideo-6026.html'">
    <p>Mirror 1: Megavideo</p>
    <p><span>CALIDAD: DVD-RIP | IDIOMA: ESPA&Ntilde;OL</span></p>
    <p class="v_ico"><img src="http://caratulas.redestv.es/img/cont/megavideo.png" alt="Megavideo" /></p>
    </div>
    <div class="tit_opts" style="cursor:pointer;" onclick="location.href='http://www.redestv.es/peliculas/drama/el-destino-de-nunik_espanol-dvd-rip-megavideo-6027.html'">
    <p>Mirror 2: Megavideo</p>
    <p><span>CALIDAD: DVD-RIP | IDIOMA: ESPA&Ntilde;OL</span></p>
    <p class="v_ico"><img src="http://caratulas.redestv.es/img/cont/megavideo.png" alt="Megavideo" /></p>
    </div>
    </div>
    </div>
    </div> 
    '''
    data = scrapertools.cachePage("http://www.redestv.es/inc/mostrar_contenido.php?sec=pelis_ficha&zona=online&id="+matches[0])
    patronvideos  = '<div class="tit_opts" style="cursor:pointer;" onclick="location.href=\'([^\']+)\'">[^<]+'
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
    logger.info("[redestv.py] play")
 
    title = urllib.unquote_plus( params.get("title") )
    thumbnail = urllib.unquote_plus( params.get("thumbnail") )
    plot = unicode( xbmc.getInfoLabel( "ListItem.Plot" ), "utf-8" )
    server = params["server"]
 
    xbmctools.playvideo(CHANNELNAME,server,url,category,title,thumbnail,plot)
 
def addfolder(nombre,url,accion):
    logger.info('[redestv.py] addfolder( "'+nombre+'" , "' + url + '" , "'+accion+'")"')
    listitem = xbmcgui.ListItem( nombre , iconImage="DefaultFolder.png")
    itemurl = '%s?channel=redestv&action=%s&category=%s&url=%s' % ( sys.argv[ 0 ] , accion , urllib.quote_plus(nombre) , url )
    xbmcplugin.addDirectoryItem( handle = int(sys.argv[ 1 ]), url = itemurl , listitem=listitem, isFolder=True)
 
def addvideo(nombre,url,category,server):
    logger.info('[redestv.py] addvideo( "'+nombre+'" , "' + url + '" , "'+server+'")"')
    listitem = xbmcgui.ListItem( nombre, iconImage="DefaultVideo.png" )
    listitem.setInfo( "video", { "Title" : nombre, "Plot" : nombre } )
    itemurl = '%s?channel=redestv&action=play&category=%s&url=%s&server=%s' % ( sys.argv[ 0 ] , category , url , server )
    xbmcplugin.addDirectoryItem( handle=int(sys.argv[ 1 ]), url=itemurl, listitem=listitem, isFolder=False)
 
def addthumbnailfolder( scrapedtitle , scrapedurl , scrapedthumbnail , accion ):
    logger.info('[redestv.py] addthumbnailfolder( "'+scrapedtitle+'" , "' + scrapedurl + '" , "'+scrapedthumbnail+'" , "'+accion+'")"')
    listitem = xbmcgui.ListItem( scrapedtitle, iconImage="DefaultFolder.png", thumbnailImage=scrapedthumbnail )
    itemurl = '%s?channel=redestv&action=%s&category=%s&url=%s' % ( sys.argv[ 0 ] , accion , urllib.quote_plus( scrapedtitle ) , urllib.quote_plus( scrapedurl ) )
    xbmcplugin.addDirectoryItem( handle = int(sys.argv[ 1 ]), url = itemurl , listitem=listitem, isFolder=True)
