# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para divxonline
# ermanitu
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#------------------------------------------------------------
import urlparse,urllib2,urllib,re
import os
import sys
import xbmc
import xbmcgui
import xbmcplugin
import anotador
import base64
import datetime

from servers import servertools
from core import scrapertools
from core import config
from core import logger
from core import xbmctools

from pelisalacarta import buscador

CHANNELNAME = "divxonline"

# Traza el inicio del canal
logger.info("[divxonline.py] init")

j=0;
i=0
ct=''

DEBUG = True
Generate = False # poner a true para generar listas de peliculas
Notas = False # indica si hay que añadir la nota a las películas
LoadThumbs = True # indica si deben cargarse los carteles de las películas; en MacOSX cuelga a veces el XBMC

def mainlist(params,url,category):
    logger.info("[divxonline.py] mainlist")
    #logger.info(base64.b64decode('yFA/B6/fgVeTE6fmN4HsindoCQarfil2sajKotYmPdqOlDhSMgr1+zFsqAj/M+GWmLJccUk0PjwfCqUf4/PwFCJQ9Yk1LYFsN2NZmrvxnCF9aTYVs589hFAPqEGto0ZGacMpzG7UZUf62wvaFBRNw9aaL5X2b+adEc92Ll3NykrWJji3reBwIN7VQQPFKvOBsD+wGnerkyIMfXXBQXLbF8ZrITbJGMUVSv4s5P6KYcVLyAlZNQXH9TrcrpIKplSZyBtGsGbHNEBUJg2KcnNiw8NGzJhwmDkWcvhGOWGKIG8E2r0jS5JTbZuuFE97pBgbA9KRi0y/NtLcOPE0E/1TmQcbgzsIIsKt1ZgjhVppel2479YmLtbYA7zrSmuGaEjGGbpoarc6X29FS+VPN6CCFCuRlHf9M122xJh+fisWWEYaFaZvDsYmhPPnERx3CK4UrUPIKdJcqoA8jkxFLQFPwT8Z0BMZ2vH5VlNOCCOZRpoM+wiJx+VDo8E78czIJzdePljQ6/QqqaAp3GDnD0i/S8lV8WCMu3OLwGeNe0IVyUYksx9FvJhFSjk='));

    xbmctools.addnewfolder( CHANNELNAME , "novedades" , CHANNELNAME , "Novedades" , "http://www.divxonline.info/" , "", "" )
    xbmctools.addnewfolder( CHANNELNAME , "megavideo" , CHANNELNAME , "Películas en Megavideo" , "" , "", "" )
#    xbmctools.addnewfolder( CHANNELNAME , "veoh" , CHANNELNAME , "Películas en Veoh" , "" , "", "" )
    xbmctools.addnewfolder( CHANNELNAME , "pelisconficha" , CHANNELNAME , "Estrenos" , "http://www.divxonline.info/peliculas-estreno/1.html" , "", "" )
    xbmctools.addnewfolder( CHANNELNAME , "pelisporletra" , CHANNELNAME , "Películas de la A a la Z" , "" , "", "" )
    xbmctools.addnewfolder( CHANNELNAME , "pelisporanio" , CHANNELNAME , "Películas por año de estreno" , "" , "", "" )
    xbmctools.addnewfolder( CHANNELNAME , "busqueda"     , category , "Buscar"                           ,"","","")
    # Label (top-right)...
    xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
    xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )



def search(params,url,category):
    
    buscador.listar_busquedas(params,url,category)
    
    
def searchresults(params,tecleado,category):
    logger.info("[divxonline.py] search")

    buscador.salvar_busquedas(params,tecleado,category)
    tecleado = tecleado.replace(" ", "+")
    #searchUrl = "http://documentalesatonline.loquenosecuenta.com/search/"+tecleado+"?feed=rss2&paged=1"
    busqueda(CHANNELNAME,tecleado,category)

def busqueda(params,url,category):
    logger.info("busqueda")
    tecleado = ""
    keyboard = xbmc.Keyboard('')
    keyboard.doModal()
    if (keyboard.isConfirmed()):
        tecleado = keyboard.getText()
        if len(tecleado)<=0:
            return
    
    tecleado = tecleado.replace(" ", "+")
    data=scrapertools.cachePagePost("http://www.divxonline.info/buscador.html",'texto=' + tecleado + '&categoria=0&tipobusqueda=1&Buscador=Buscar')

    #logger.info(data)
    data=data[data.find('Se han encontrado un total de'):]
    
    #<li><a href="/pelicula/306/100-chicas-2000/">100 chicas (2000)</a></li>
    patronvideos  = '<li><a href="(.+?)">(.+?)</a></li>'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    if DEBUG: 
        scrapertools.printMatches(matches)
    
    for match in matches:
        xbmctools.addnewfolder( CHANNELNAME , "listmirrors" , category , match[1] , 'http://www.divxonline.info' + match[0] , 'scrapedthumbnail', 'scrapedplot' )
    
    xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
    xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )


def novedades(params,url,category):
    logger.info("[divxonline.py] novedades")

    # Descarga la página
    data = scrapertools.cachePage(url)
    #logger.info(data)

    # Extrae las entradas
    '''
    <td class="contenido"><a href="/pelicula/8853/Conexion-Tequila-1998/"><img src="http://webs.ono.com/jeux/divxonline.info_conexiontequila.jpg" style="padding: 5px;"  border="0" width="150" height="200" align="left" alt="Conexión Tequila (1998)" title="Conexión Tequila (1998)" />
    <font color="#000000"><b>Género:</b></font> <a href="/peliculas/50/Accion-Megavideo/"><font color="#0066FF">Accion (Megavideo)</font></a><br />
    <b>Título:</b> <a href="/pelicula/8853/Conexion-Tequila-1998/"><font color="#0066FF"><b>Conexión Tequila (1998) - </b></font></a>
    <b>Director(es):</b> <a href="/director/2917/Robert-Towne/"><font color="#0066FF">Robert Towne </font></a>
    <b> - Año de estreno:</b><a href="/peliculas-anho/1998/1.html"><font color="#0066FF"> 1998</a></font> -
    <b>Autorizada:</b> <a href="/peliculas/Todos-los-publicos/1/"><font color="#0066FF"> Todos los publicos - </a></font>
    <b>Vista:</b><font color="#0066FF"> 1103 veces - </font><b>Colaborador(es):</b><font color="#0066FF"> jacinto</font><br /><BR><b>Sinopsis:</b> Nick y McKussic son amigos desde niños, pero ahora Nick es teniente de policía y McKussic el mejor traficante de drogas de la ciudad. Se prepara una operación de mil doscientos kilos de cocaína y la Brigada Antinarcóticos cree que McKussic va a coordinar la entrega.
    <a href="/pelicula/8853/Conexion-Tequila-1998/"> <font color="#0066FF">(leer más)</font></a><br><br>
    <a href="/pelicula/8853/Conexion-Tequila-1998/" style="font-weight: bold; font-size: 11pt">
    <img src="http://webs.ono.com/divx/imagenes/flecha.png" border="0"> <font size="3" color="#0066FF">Conexión Tequila (1998)</font></a></td>
    <td>
    '''
    patronvideos  = '<td class="contenido"><a href="([^"]+)"><img src="([^"]+)".*?title="([^"]+)"[^>]+>.*?'
    patronvideos += '<b>Sinopsis:</b>([^<]+)<'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    if DEBUG: scrapertools.printMatches(matches)

    for match in matches:
        # Titulo
        scrapedtitle = match[2]
        scrapedurl = urlparse.urljoin(url,match[0])
        scrapedurl = scrapedurl.replace("pelicula","pelicula-divx") # url de la página de reproducción
        scrapedthumbnail = "" # = match[1]
        scrapedplot = match[3]
        if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

        # Añade al listado de XBMC
        xbmctools.addnewfolder( CHANNELNAME , "listmirrors" , category , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )

    # ------------------------------------------------------
    # Extrae el paginador
    # ------------------------------------------------------
    #<a href="peliculas-online-divx-1.html" style="border: 1px solid rgb(0, 51, 102); margin: 2px; padding: 2px; text-decoration: none; color: white; background-color: rgb(0, 51, 102);" onmouseover="javascript:style.backgroundColor='#963100';" onmouseout="javascript:style.backgroundColor='#003366';">1-15</a>
    #<a href="peliculas-online-divx-2.html" style="border: 1px solid rgb(0, 51, 102); margin: 2px; padding: 2px; text-decoration: none; color: black; background-color: rgb(202, 217, 234);" onmouseover="javascript:style.backgroundColor='#ececd9';" onmouseout="javascript:style.backgroundColor='#cad9ea';">16-30</a>
    patronvideos  = '<a href="[^"]+" style="border: 1px solid rgb(0, 51, 102); margin: 2px; padding: 2px; text-decoration: none; color: white[^>]+>[^<]+</a><a href="([^"]+)" style="border: 1px solid rgb(0, 51, 102); margin: 2px; padding: 2px; text-decoration: none; color: black[^>]+>([^<]+)</a>'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    if len(matches)>0:
        xbmctools.addnewfolder( CHANNELNAME , "novedades" , category , "!Página siguiente (matches[0][1]" , urlparse.urljoin(url,matches[0][0]) , "", "" )

    # Label (top-right)...
    xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
    xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

def megavideo(params,url,category):
    logger.info("[divxonline.py] megavideo")

    xbmctools.addnewfolder( CHANNELNAME , "movielist" , CHANNELNAME , "Acción" , "http://www.divxonline.info/peliculas/50/accion-megavideo/" , "", "" )
    xbmctools.addnewfolder( CHANNELNAME , "movielist" , CHANNELNAME , "Animación" , "http://www.divxonline.info/peliculas/53/animacion-megavideo/" , "", "" )
    xbmctools.addnewfolder( CHANNELNAME , "movielist" , CHANNELNAME , "Anime" , "http://www.divxonline.info/peliculas/51/anime-megavideo/" , "", "" )
    xbmctools.addnewfolder( CHANNELNAME , "movielist" , CHANNELNAME , "Aventura" , "http://www.divxonline.info/peliculas/52/aventura-megavideo/" , "", "" )
    xbmctools.addnewfolder( CHANNELNAME , "movielist" , CHANNELNAME , "Bélicas" , "http://www.divxonline.info/peliculas/95/belicas-megavideo/" , "", "" )
    xbmctools.addnewfolder( CHANNELNAME , "movielist" , CHANNELNAME , "Ciencia Ficción" , "http://www.divxonline.info/peliculas/55/ciencia-ficcion-megavideo/" , "", "" )
    xbmctools.addnewfolder( CHANNELNAME , "movielist" , CHANNELNAME , "Cine Clásico" , "http://www.divxonline.info/peliculas/58/cine-clasico-megavideo/" , "", "" )
    xbmctools.addnewfolder( CHANNELNAME , "movielist" , CHANNELNAME , "Cine español" , "http://www.divxonline.info/peliculas/57/cine-espa%C3%B1ol-megavideo/" , "", "" )
    xbmctools.addnewfolder( CHANNELNAME , "movielist" , CHANNELNAME , "Clásicos Disney" , "http://www.divxonline.info/peliculas/59/clasicos-disney-megavideo/" , "", "" )
    xbmctools.addnewfolder( CHANNELNAME , "movielist" , CHANNELNAME , "Comedias" , "http://www.divxonline.info/peliculas/60/comedias-megavideo/" , "", "" )
    xbmctools.addnewfolder( CHANNELNAME , "movielist" , CHANNELNAME , "Documentales" , "http://www.divxonline.info/peliculas/54/documentales-megavideo/" , "", "" )
    xbmctools.addnewfolder( CHANNELNAME , "movielist" , CHANNELNAME , "Drama" , "http://www.divxonline.info/peliculas/62/drama-megavideo/" , "", "" )
    xbmctools.addnewfolder( CHANNELNAME , "movielist" , CHANNELNAME , "Infantil" , "http://www.divxonline.info/peliculas/63/infantil-megavideo/" , "", "" )
    xbmctools.addnewfolder( CHANNELNAME , "movielist" , CHANNELNAME , "Musicales" , "http://www.divxonline.info/peliculas/64/musicales-megavideo/" , "", "" )
    xbmctools.addnewfolder( CHANNELNAME , "movielist" , CHANNELNAME , "Suspense" , "http://www.divxonline.info/peliculas/65/suspense-megavideo/" , "", "" )
    xbmctools.addnewfolder( CHANNELNAME , "movielist" , CHANNELNAME , "Terror" , "http://www.divxonline.info/peliculas/66/terror-megavideo/" , "", "" )
    xbmctools.addnewfolder( CHANNELNAME , "movielist" , CHANNELNAME , "Western" , "http://www.divxonline.info/peliculas/67/western-megavideo/" , "", "" )

    # Label (top-right)...
    xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )

    # Disable sorting...
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )

    # End of directory...
    xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

def veoh(params,url,category):
    logger.info("[divxonline.py] veoh")

    xbmctools.addnewfolder( CHANNELNAME , "movielist" , CHANNELNAME , "Acción" , "http://www.divxonline.info/peliculas/30/accion-veoh/" , "", "" )
    xbmctools.addnewfolder( CHANNELNAME , "movielist" , CHANNELNAME , "Animación" , "http://www.divxonline.info/peliculas/33/animacion-veoh/" , "", "" )
    xbmctools.addnewfolder( CHANNELNAME , "movielist" , CHANNELNAME , "Anime" , "http://www.divxonline.info/peliculas/41/anime-veoh/" , "", "" )
    xbmctools.addnewfolder( CHANNELNAME , "movielist" , CHANNELNAME , "Aventura" , "http://www.divxonline.info/peliculas/32/aventura-veoh/" , "", "" )
    xbmctools.addnewfolder( CHANNELNAME , "movielist" , CHANNELNAME , "Bélicas" , "http://www.divxonline.info/peliculas/96/belicas-veoh/" , "", "" )
    xbmctools.addnewfolder( CHANNELNAME , "movielist" , CHANNELNAME , "Ciencia Ficción" , "http://www.divxonline.info/peliculas/35/ciencia0-ficcion-veoh/" , "", "" )
    xbmctools.addnewfolder( CHANNELNAME , "movielist" , CHANNELNAME , "Cine Clásico" , "http://www.divxonline.info/peliculas/38/cine-clasico-veoh/" , "", "" )
    xbmctools.addnewfolder( CHANNELNAME , "movielist" , CHANNELNAME , "Cine Español" , "http://www.divxonline.info/peliculas/37/cine-español-veoh/" , "", "" )
    xbmctools.addnewfolder( CHANNELNAME , "movielist" , CHANNELNAME , "Clásicos Disney" , "http://www.divxonline.info/peliculas/39/clasicos-disney-veoh/" , "", "" )
    xbmctools.addnewfolder( CHANNELNAME , "movielist" , CHANNELNAME , "Comedias" , "http://www.divxonline.info/peliculas/40/comedias-veoh/" , "", "" )
    xbmctools.addnewfolder( CHANNELNAME , "movielist" , CHANNELNAME , "Cortometrajes" , "http://www.divxonline.info/peliculas/41/cortometrajes-veoh/" , "", "" )
    xbmctools.addnewfolder( CHANNELNAME , "movielist" , CHANNELNAME , "Documentales" , "http://www.divxonline.info/peliculas/34/documentales-veoh/" , "", "" )
    xbmctools.addnewfolder( CHANNELNAME , "movielist" , CHANNELNAME , "Drama" , "http://www.divxonline.info/peliculas/42/dramas-veoh/" , "", "" )
    xbmctools.addnewfolder( CHANNELNAME , "movielist" , CHANNELNAME , "Infantiles" , "http://www.divxonline.info/peliculas/43/infantiles-veoh/" , "", "" )
    xbmctools.addnewfolder( CHANNELNAME , "movielist" , CHANNELNAME , "Musicales" , "http://www.divxonline.info/peliculas/44/musicales-veoh/" , "", "" )
    xbmctools.addnewfolder( CHANNELNAME , "movielist" , CHANNELNAME , "Suspense" , "http://www.divxonline.info/peliculas/45/suspense-veoh/" , "", "" )
    xbmctools.addnewfolder( CHANNELNAME , "movielist" , CHANNELNAME , "Terror" , "http://www.divxonline.info/peliculas/46/terror-veoh/" , "", "" )
    xbmctools.addnewfolder( CHANNELNAME , "movielist" , CHANNELNAME , "Western" , "http://www.divxonline.info/peliculas/49/western-veoh/" , "", "" )

    # Label (top-right)...
    xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
    xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

def stepinto (url, data, pattern): # expand a page adding "next page" links given some pattern
    # Obtiene el trozo donde están los links a todas las páginas de la categoría
    match = re.search(pattern,data)
    trozo = match.group(1)
    #logger.info(trozo)

    # carga todas las paginas juntas para luego extraer las urls
    patronpaginas = '<a href="([^"]+)"'
    matches = re.compile(patronpaginas,re.DOTALL).findall(trozo)
    #scrapertools.printMatches(matches)
    res = ''
    for match in matches:
        urlpage = urlparse.urljoin(url,match)
        #logger.info(match)
        #logger.info(urlpage)
        res += scrapertools.cachePage(urlpage)
    return res


html_escape_table = {
    "&ntilde;": "ñ", "&iquest;": "¿", "&iexcl;": "¡"
}
def removeacutes (s):
    for exp in html_escape_table.iterkeys():
        s = s.replace(exp,html_escape_table[exp])
    return s
        

def pelisporletra(params,url,category):
    logger.info("[divxonline.py] pelisporletra")

    letras = "9ABCDEFGHIJKLMNÑOPQRSTUVWXYZ" # el 9 antes era 1, que curiosamente está mal en la web divxonline (no funciona en el navegador)
    for letra in letras:
        xbmctools.addnewfolder( CHANNELNAME , "pelisconfichaB" , CHANNELNAME , str(letra) , "http://www.divxonline.info/verpeliculas/"+str(letra)+"_pagina_1.html" , "", "" )

    # Label (top-right)...
    xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )
    # Disable sorting...
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
    # End of directory...
    xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )


def pelisporanio(params,url,category):
    logger.info("[divxonline.py] pelisporanio")
    logger.info(datetime.datetime.today().year)
    #for anio in range(2009,1915,-1):
    for anio in range(datetime.datetime.today().year,1915,-1):
        xbmctools.addnewfolder( CHANNELNAME , "pelisconficha" , CHANNELNAME , str(anio) , "http://www.divxonline.info/peliculas-anho/"+str(anio)+"/1.html" , "", "" )

    # Label (top-right)...
    xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )
    # Disable sorting...
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
    # End of directory...
    xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

    
def pelisconficha(params,url,category): # fichas en listados por año y en estrenos
    logger.info("[divxonline.py] pelisconficha")
    # Descarga la página
    data = scrapertools.cachePage(url)
    #logger.info(data)
    if(data.find('Películas del  año') > 0):
    
    ##data=data[data.find('<!-- MENU IZQUIERDO -->'):]
        data=data[data.find('Películas del  año'):]
    
    logger.info(data.find('<!-- MENU IZQUIERDO -->'))
    #logger.info(data)
    # Extrae las entradas
    patronvideos  = '<td class="contenido"><a href="(.*?)">' # link
    patronvideos += '<img src="(.*?)"' # cartel
    patronvideos += '.*?title="(.*?)"' # título
#    patronvideos += '.*?<b>Descripción:</b>(.*?)\.\.\.'
        
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for match in matches:
        # Titulo
        scrapedtitle = removeacutes(match[2])
        if (not Generate and Notas):
            score = anotador.getscore(match[2])
            if (score != ""):
                scrapedtitle += " " + score

        # URL
        scrapedurl = urlparse.urljoin(url,match[0]) # url de la ficha divxonline
        scrapedurl = scrapedurl.replace("pelicula","pelicula-divx") # url de la página de reproducción

        # Thumbnail
        scrapedthumbnail = ""
        if LoadThumbs:
            scrapedthumbnail = match[1]

        # procesa el resto
        scrapeddescription = "" #match[3]

        # Depuracion
        if (DEBUG):
            logger.info("scrapedtitle="+scrapedtitle)
            logger.info("scrapedurl="+scrapedurl)
            logger.info("scrapedthumbnail="+scrapedthumbnail)

        # Añade al listado de XBMC
        xbmctools.addthumbnailfolder( CHANNELNAME , scrapedtitle , scrapedurl , scrapedthumbnail, "listmirrors" )


    # añade siguiente página
    match = re.search('(.*?)(\d+?)(\.html)',url)
    logger.info("url="+url)
    pag = match.group(2)
    newpag = match.group(1) + str(int(pag)+1) + match.group(3)
    logger.info("newpag="+newpag)
    xbmctools.addnewfolder( CHANNELNAME , "pelisconficha" , CHANNELNAME , "Siguiente" , newpag , "", "" )
    
    # Label (top-right)...
    xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )
    # Disable sorting...
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
    # End of directory...
    xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )
        

import time
def pelisconfichaB(params,url,category): # fichas con formato en entradas alfabéticas
    logger.info("[divxonline.py] pelisconfichaB")
    t0 = time.time()
    # Descarga la página
    data = scrapertools.cachePage(url)
    #logger.info(data)

    # carga N páginas
    N = 10
    match = re.search('(.*?)(\d+?)(\.html)',url)
    pag = int(match.group(2))
    #logger.info("pag="+match.group(2))
    
    for i in range(pag+1,pag+N):
        newurl = match.group(1) + str(i) + match.group(3)
        data += scrapertools.cachePage(newurl)

    nexturl = match.group(1) + str(pag+N) + match.group(3)

    # Extrae las entradas
    data=data[data.find('Películas online por orden alfabético'):]
    logger.info(data)
    
    patronvideos  = '<td class="contenido"><img src="(.*?)"' # cartel
    patronvideos += '.*?alt="(.*?)"' # título
    patronvideos += '.*?<b>Sinopsis.*?<a href="(.*?)"' # url
        
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for match in matches:
        # Titulo
        scrapedtitle = removeacutes(match[1]) # 7.49 seg 
#        scrapedtitle = match[1] # 7.33 seg
        if (not Generate and Notas):
            score = anotador.getscore(match[1])
            if (score != ""):
                scrapedtitle += " " + score

        # URL
        scrapedurl = urlparse.urljoin(url,match[2]) # url de la ficha divxonline
        scrapedurl = scrapedurl.replace("pelicula","pelicula-divx") # url de la página de reproducción

        # Thumbnail
        scrapedthumbnail = ""
        if LoadThumbs:
            scrapedthumbnail = match[0]

        # procesa el resto
        scrapeddescription = "" # match[3]

        # Depuracion
        if (DEBUG):
            logger.info("scrapedtitle="+scrapedtitle)
            logger.info("scrapedurl="+scrapedurl)
            logger.info("scrapedthumbnail="+scrapedthumbnail)

        # Añade al listado de XBMC
        xbmctools.addthumbnailfolder( CHANNELNAME , scrapedtitle , scrapedurl , scrapedthumbnail, "listmirrors" )


    # añade siguiente página
    xbmctools.addnewfolder( CHANNELNAME , "pelisconfichaB" , CHANNELNAME , "Siguiente" , nexturl , "", "" )
    
    # Label (top-right)...
    xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
    xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )
    
    if DEBUG:
        logger.info("Tiempo de ejecución = "+str(time.time()-t0))


def remove_html_tags(data):
    p = re.compile(r'<.*?>')
    return p.sub('', data)

def movielist(params,url,category): # pelis sin ficha (en listados por género)
    logger.info("[divxonline.py] movielist")

    # Descarga la página
    data = scrapertools.cachePage(url)
    #logger.info(data)

    data = stepinto(url,data,'Ver página:(.*?)</p>')

    # Extrae las entradas (carpetas)
    patronvideos  = '<li><h2><a href="([^"]+?)">(.*?)</a>'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    #scrapertools.printMatches(matches)

    if (Generate):
        f = open(config.DATA_PATH+'/films.tab', 'w') # fichero para obtener las notas

    for match in matches:
        # Titulo
        scrapedtitle = remove_html_tags(match[1])
        if (not Generate and Notas):
            score = anotador.getscore(remove_html_tags(match[1]))
            if (score != ""):
                scrapedtitle += " " + score

        # URL
        scrapedurl = urlparse.urljoin(url,match[0]) # url de la ficha divxonline
        scrapedurl = scrapedurl.replace("pelicula","pelicula-divx") # url de la página de reproducción

        # Thumbnail
        #scrapedthumbnail = urlparse.urljoin(url,match[1])
        scrapedthumbnail = ""

        # procesa el resto
        scrapeddescription = ""

        # Depuracion
        if (DEBUG):
            logger.info("scrapedtitle="+scrapedtitle)
            logger.info("scrapedurl="+scrapedurl)
            logger.info("scrapedthumbnail="+scrapedthumbnail)

        if (Generate):
            sanio = re.search('(.*?)\((.*?)\)',scrapedtitle)
            if (sanio): # si hay anio
                fareg = sanio.group(1) + "\t" + sanio.group(2) + "\t" + scrapedtitle
            else:
                fareg = scrapedtitle + "\t\t" + scrapedtitle
            f.write(fareg+"\n")

        # Añade al listado de XBMC
        xbmctools.addthumbnailfolder( CHANNELNAME , scrapedtitle , scrapedurl , scrapedthumbnail, "listmirrors" )
    # Label (top-right)...
    xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
    xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

    if (Generate):
        f.close()


def listmirrors(params,url,category):
    logger.info("[divxonline.py] listmirrors")
    logger.info(url)
    #try:
    #    title = urllib.unquote_plus( params.get("title") )
    #    thumbnail = urllib.unquote_plus( params.get("thumbnail") )
    #    plot = urllib.unquote_plus( params.get("plot") )
    #except:
    #    pass
    #data = scrapertools.cachePage(url) # descarga pagina de reproduccion
    #'''
    #<a style="color: #f2ac03; font-weight: bold; font-size: 12pt" href="/pelicula-divx/8853/Conexion-Tequila-1998/" target="_self" style="font-weight: bold; font-size: 11pt">
    #<h2><align="center"><font size="4"><img src="http://webs.ono.com/mis-videos/imagenes/filmes.png" border="0">&nbsp;Ver Película Online: Conexión Tequila (1998)</font></h2></a>
    #'''
    #patronvideos  = '<a style="[^"]+" href="([^"]+)"[^<]+'
    #patronvideos += '<h2><align[^>]+><font[^>]+><img[^>]+>.nbsp.Ver Pel'
    #matches = re.compile(patronvideos,re.DOTALL).findall(data)
    #if DEBUG: scrapertools.printMatches(matches)
#
#    for match in matches:
#        scrapedurl = urlparse.urljoin(url,match)
#        if (DEBUG): logger.info("url=["+scrapedurl+"]")

#        # Añade al listado de XBMC
#        xbmctools.addnewfolder( CHANNELNAME , "detail" , category , title + " [online]" , scrapedurl , thumbnail, plot )

#    '''
#    <a href="/descarga-directa/8853/Conexion-Tequila-1998/" style="color: #f2ac03; font-weight: bold; font-size: 12pt;">Descarga Directa de: Conexión Tequila (1998)</a>
#    '''
#    patronvideos  = '<a href="([^"]+)"[^>]+>Descarga Directa'
#    matches = re.compile(patronvideos,re.DOTALL).findall(data)
#    if DEBUG: scrapertools.printMatches(matches)
#
#    for match in matches:
#        scrapedurl = urlparse.urljoin(url,match)
#        if (DEBUG): logger.info("url=["+scrapedurl+"]")
#
#        # Añade al listado de XBMC
#        xbmctools.addnewfolder( CHANNELNAME , "detail" , category , title + " [descarga]" , scrapedurl , thumbnail, plot )

    # Label (top-right)...
    detail(params,url,category)
    xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
    xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

def detail(params,url,category):
    logger.info("[divxonline.py] detail")
    title=''
    thumbnail=''
    plot=''

    try:
        title = urllib.unquote_plus( params.get("title") )
        thumbnail = urllib.unquote_plus( params.get("thumbnail") )
        plot = urllib.unquote_plus( params.get("plot") )
    except:
        pass
    # Descarga la página
    data = scrapertools.cachePage(url)
    #logger.info(data)

    # ------------------------------------------------------------------------------------
    # Busca los enlaces a los videos
    # ------------------------------------------------------------------------------------
    
    data=decryptinks(data);
    listavideos = servertools.findvideos(data)

    for video in listavideos:
        videotitle = video[0]
        url = video[1]
        server = video[2]
        xbmctools.addnewvideo( CHANNELNAME , "play" , category , server , title.strip() + " - " + videotitle , url , thumbnail , plot )
    # ------------------------------------------------------------------------------------

    # Cierra el directorio
    xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
    xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )
    
def decryptinks(text):
    patronvideos  = "decodeBase64\('(.+?)'\)"
    matches = re.compile(patronvideos,re.DOTALL).findall(text)
    #string='yFA/B6/fgVeTFPS4NIqijSVtVUemN39H+e6EuYNxcNiHnCsZeU3W0iY29Fbye4GjyIrqXD9RTiVAU/gI7Pq7Qi1vnoRkLooganMExe36ySUofSME6cF5zgQPoQvnsRNQbp0owGrUZ0fx0EuMWghIg8PeCbyzW46jM/czf0neyBePLXvg6u0tYdvCHF7JdLLGpH20CWO6mX8bc2rDAz+bUNshJS/eHNhLCblzvrKbJcddzQRfOkyriWOTusBm3wDZ1kZMs2fEckZRMBvUIiQljZ0L1IV3wDkVQ9cbdDqEIHlWi/xmHtVsb4G+SAMpsBNpXJzfzle4IZaHWdt+GOsI+y1DiHdRJ9mizN0+mEUsIhGqgJMiIMzeFeSmRQ21PxDVXP0yLKcsX3IPfPlcIOGcAGXcpXLgchisgZoyej4aEk0MTsRFGto4kvGzHBAyFrsf+UfKZf4ZqYQmx1pFMl8A0CQbhAoOgKioUFNOASCSTpvNqwiL1aRJuYQo/MzOLjhTcwrTua5Cg50513LwRkC7BJcIsHKCuWvU3CyKKV5Iz1M4qB5C4dBISifGiaisjwmprQk4VWeLVmyba+lzpfDa7PjGs3Hh54cE6BoN4aJVqaUpLvbxJfd2A4ODlTrOQZmFa32dfZYEIpB5EejTqY6TU4AW3p9G+Kd4TNAjTE2KVfUIW5bhXSvEE5Gs8JCp1xxgPcwrSTVdqe+VsjhqKjihnMouWiXn5pQzv2DlsGzDB1jShTmdWvo9gv4kya16ZzBUalTPTXVVPlapL4OMIJgwXzGPkO+2mwjgdjF8jzaUjn3bowuDdMaix5xpfJmI5IlHAJYKL4T0oVBE+gMFJsUa09IuBMi48ARSa8hXDmGf9nCpcAJ8jCrBdtj0Apm3CgaNWwdhxJhGb5RCLenTvOwB81N7sbyuWI2XzlKdRuUddJgD+3YDFxh1/gkTFgPWyq4xMuEoiZGcVKvfXpIeIZR6JN7cX3kL1HYfJYyZUs6IsYqQOaOy+gjVVw6GgE25oBD9geh8cS5mx94XxIXmi/1KUcYztxx/+zPSihLJ404sVnaxQ2LfpM7QtUUFZnyz4olTEfdQXxaQPUzIbuceyGqJig1djjiGw5qAHYcQQ45gJC3Gs+bzo4xiIJQHSTvi1SP7b9Ge9bV9SjOJ5kt1Z4CZoehu9VYKc+PcUFwWVeWN2Xf+Xp8xf5txn6upEc0tiUbSsQCRkZmJVVJntibWDnq4MjeczapU/sBgsULj5h7+llwmaKgdTCAfOLqWWX69z7ncwXbg+Aws/t6W75nHeAMVbK+Xt+3zNgCQE8M='
    #logger.info(matches);
    result=base64.b64decode(matches[0])
    return(Procesa('cryptkey', result));

def Procesa (key, pt):
        s = [255] * 257

        for i in range(0, 256):
                s[i] = i;
        global j
        for i in range(0, 256):
                global j
                j= ( j + s[i] + ord(key[i%len(key)]))%256;
                x = s[i];
                s[i] = s[j];
                s[j] = x;

        i=0
        j=0
        for y in range(0, len(pt)):
                i = (i + 1) % 256;
                j = (j + s[i]) % 256;
                x = s[i];
                s[i] = s[j];
                s[j] = x;
                global ct
                ct += chr(ord(pt[y]) ^ s[(s[i] + s[j]) % 256]);
        return ct
    
    


def play(params,url,category):
    logger.info("[divxonline.py] play")

    title = unicode( xbmc.getInfoLabel( "ListItem.Title" ), "utf-8" )
    thumbnail = xbmc.getInfoImage( "ListItem.Thumb" )
    plot = unicode( xbmc.getInfoLabel( "ListItem.Plot" ), "utf-8" )
    server = params["server"]
    logger.info("[divxonline.py] thumbnail="+thumbnail)
    logger.info("[divxonline.py] server="+server)

    xbmctools.playvideo(CHANNELNAME,server,url,category,title,thumbnail,plot)

#mainlist(None,"","mainlist")
#detail(None,"http://impresionante.tv/ponyo.html","play")








