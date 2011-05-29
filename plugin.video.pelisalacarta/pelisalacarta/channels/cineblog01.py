# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para cinegratis
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#------------------------------------------------------------
import urlparse,urllib2,urllib,re
import os
import sys

from core import scrapertools
from core import logger
from core import config
from core.item import Item
from core import xbmctools
from pelisalacarta import buscador

from servers import servertools
from servers import vk

import xbmc
import xbmcgui
import xbmcplugin

CHANNELNAME = "cineblog01"

# Esto permite su ejecución en modo emulado
try:
    pluginhandle = int( sys.argv[ 1 ] )
except:
    pluginhandle = ""

# Traza el inicio del canal
xbmc.output("[cineblog01.py] init")

DEBUG = True

import re, htmlentitydefs

##
# Removes HTML or XML character references and entities from a text string.
#
# @param text The HTML (or XML) source text.
# @return The plain text, as a Unicode string, if necessary.

def unescape(text):
    def fixup(m):
        text = m.group(0)
        if text[:2] == "&#":
            # character reference
            try:
                if text[:3] == "&#x":
                    return unichr(int(text[3:-1], 16))
                else:
                    return unichr(int(text[2:-1]))
            except ValueError:
                pass
        else:
            # named entity
            try:
                text = unichr(htmlentitydefs.name2codepoint[text[1:-1]])
            except KeyError:
                pass
        return text # leave as is
    return re.sub("&#?\w+;", fixup, text)

def mainlist(params,url,category):
    xbmc.output("[cineblog01.py] mainlist")

    # Añade al listado de XBMC
    xbmctools.addnewfolder( CHANNELNAME , "listvideos"  , category , "Film - Novità"              ,"http://cineblog01.com/","","")
    xbmctools.addnewfolder( CHANNELNAME , "pelisalfa"   , category , "Film - Per Lettera"    ,"","","")
    xbmctools.addnewfolder( CHANNELNAME , "peliscat"   , category , "Film - Per Categoria"    ,"","","")
    xbmctools.addnewfolder( CHANNELNAME , "searchmovie" , category , "Film - Cerca"                           ,"","","")
    xbmctools.addnewfolder( CHANNELNAME , "listserie"  , category , "Serie"   ,"http://cineblog01.info/serietv/","","")
    xbmctools.addnewfolder( CHANNELNAME , "listanime"  , category , "Anime"   ,"http://cineblog01.info/anime/","","")

    # Label (top-right)...
    xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )

    # Disable sorting...
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )

    # End of directory...
    xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

def pelisalfa(params, url, category):

    xbmctools.addnewfolder( CHANNELNAME ,"listcat", category , "0-9","http://cineblog01.com/category/numero","","")
    xbmctools.addnewfolder( CHANNELNAME ,"listcat", category , "A","http://cineblog01.com/category/a","","")
    xbmctools.addnewfolder( CHANNELNAME ,"listcat", category , "B","http://cineblog01.com/category/b","","")
    xbmctools.addnewfolder( CHANNELNAME ,"listcat", category , "C","http://cineblog01.com/category/c","","")
    xbmctools.addnewfolder( CHANNELNAME ,"listcat", category , "D","http://cineblog01.com/category/d","","")
    xbmctools.addnewfolder( CHANNELNAME ,"listcat", category , "E","http://cineblog01.com/category/e","","")
    xbmctools.addnewfolder( CHANNELNAME ,"listcat", category , "F","http://cineblog01.com/category/f","","")
    xbmctools.addnewfolder( CHANNELNAME ,"listcat", category , "G","http://cineblog01.com/category/g","","")
    xbmctools.addnewfolder( CHANNELNAME ,"listcat", category , "H","http://cineblog01.com/category/h","","")
    xbmctools.addnewfolder( CHANNELNAME ,"listcat", category , "I","http://cineblog01.com/category/i","","")
    xbmctools.addnewfolder( CHANNELNAME ,"listcat", category , "J","http://cineblog01.com/category/j","","")
    xbmctools.addnewfolder( CHANNELNAME ,"listcat", category , "K","http://cineblog01.com/category/k","","")
    xbmctools.addnewfolder( CHANNELNAME ,"listcat", category , "L","http://cineblog01.com/category/l","","")
    xbmctools.addnewfolder( CHANNELNAME ,"listcat", category , "M","http://cineblog01.com/category/m","","")
    xbmctools.addnewfolder( CHANNELNAME ,"listcat", category , "N","http://cineblog01.com/category/n","","")
    xbmctools.addnewfolder( CHANNELNAME ,"listcat", category , "O","http://cineblog01.com/category/o","","")
    xbmctools.addnewfolder( CHANNELNAME ,"listcat", category , "P","http://cineblog01.com/category/p","","")
    xbmctools.addnewfolder( CHANNELNAME ,"listcat", category , "Q","http://cineblog01.com/category/q","","")
    xbmctools.addnewfolder( CHANNELNAME ,"listcat", category , "R","http://cineblog01.com/category/r","","")
    xbmctools.addnewfolder( CHANNELNAME ,"listcat", category , "S","http://cineblog01.com/category/s","","")
    xbmctools.addnewfolder( CHANNELNAME ,"listcat", category , "T","http://cineblog01.com/category/t","","")
    xbmctools.addnewfolder( CHANNELNAME ,"listcat", category , "U","http://cineblog01.com/category/u","","")
    xbmctools.addnewfolder( CHANNELNAME ,"listcat", category , "V","http://cineblog01.com/category/v","","")
    xbmctools.addnewfolder( CHANNELNAME ,"listcat", category , "W","http://cineblog01.com/category/w","","")
    xbmctools.addnewfolder( CHANNELNAME ,"listcat", category , "X","http://cineblog01.com/category/x","","")
    xbmctools.addnewfolder( CHANNELNAME ,"listcat", category , "Y","http://cineblog01.com/category/y","","")
    xbmctools.addnewfolder( CHANNELNAME ,"listcat", category , "Z","http://cineblog01.com/category/z","","")

    # Label (top-right)...
    xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )

    # Disable sorting...
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )

    # End of directory...
    xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

def peliscat(params, url, category):

    xbmctools.addnewfolder( CHANNELNAME ,"listcat", category , "Animazione","http://cineblog01.com/category/animazione/","","")
    xbmctools.addnewfolder( CHANNELNAME ,"listcat", category , "Avventura","http://cineblog01.com/category/avventura/","","")
    xbmctools.addnewfolder( CHANNELNAME ,"listcat", category , "Azione","http://cineblog01.com/category/azione/","","")
    xbmctools.addnewfolder( CHANNELNAME ,"listcat", category , "Biografico","http://cineblog01.com/category/biografico/","","")
    xbmctools.addnewfolder( CHANNELNAME ,"listcat", category , "Comico","http://cineblog01.com/category/comico/","","")
    xbmctools.addnewfolder( CHANNELNAME ,"listcat", category , "Commedia","http://cineblog01.com/category/commedia/","","")
    xbmctools.addnewfolder( CHANNELNAME ,"listcat", category , "Corti","http://cineblog01.com/category/solo-cortometraggio/","","")
    xbmctools.addnewfolder( CHANNELNAME ,"listcat", category , "Cult","http://cineblog01.com/category/cult/","","")
    xbmctools.addnewfolder( CHANNELNAME ,"listcat", category , "Documentario","http://cineblog01.com/category/documentario/","","")
    xbmctools.addnewfolder( CHANNELNAME ,"listcat", category , "Drammatico","http://cineblog01.com/category/drammatico/","","")
    xbmctools.addnewfolder( CHANNELNAME ,"listcat", category , "Erotico","http://cineblog01.com/category/erotico/","","")
    xbmctools.addnewfolder( CHANNELNAME ,"listcat", category , "Fantascienza","http://cineblog01.com/category/fantascienza/","","")
    xbmctools.addnewfolder( CHANNELNAME ,"listcat", category , "Fantasy","http://cineblog01.com/category/fantasyfantastico/","","")
    xbmctools.addnewfolder( CHANNELNAME ,"listcat", category , "Gangster","http://cineblog01.com/category/gangster/","","")
    xbmctools.addnewfolder( CHANNELNAME ,"listcat", category , "Grottesco","http://cineblog01.com/category/grottesco/","","")
    xbmctools.addnewfolder( CHANNELNAME ,"listcat", category , "Guerra","http://cineblog01.com/category/guerra/","","")
    xbmctools.addnewfolder( CHANNELNAME ,"listcat", category , "Horror","http://cineblog01.com/category/horror/","","")
    xbmctools.addnewfolder( CHANNELNAME ,"listcat", category , "Megavideo","http://cineblog01.com/category/solo-megavideo/","","")
    xbmctools.addnewfolder( CHANNELNAME ,"listcat", category , "Megaupload","http://cineblog01.com/?cat=410","","")
    xbmctools.addnewfolder( CHANNELNAME ,"listcat", category , "Musical","http://cineblog01.com/category/musicale/","","")
    xbmctools.addnewfolder( CHANNELNAME ,"listcat", category , "Noir","http://cineblog01.com/category/noir/","","")
    xbmctools.addnewfolder( CHANNELNAME ,"listcat", category , "Poliziesco","http://cineblog01.com/category/poliziesco/","","")
    xbmctools.addnewfolder( CHANNELNAME ,"listcat", category , "Sentimentale","http://cineblog01.com/category/sentimentale/","","")
    xbmctools.addnewfolder( CHANNELNAME ,"listcat", category , "Storico","http://cineblog01.com/category/storico/","","")
    xbmctools.addnewfolder( CHANNELNAME ,"listcat", category , "Thriller","http://cineblog01.com/category/thriller/","","")
    xbmctools.addnewfolder( CHANNELNAME ,"listcat", category , "Tutto Totò","http://cineblog01.com/category/st-toto/","","")
    xbmctools.addnewfolder( CHANNELNAME ,"listcat", category , "Western","http://cineblog01.com/category/western/","","")

    # Label (top-right)...
    xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )

    # Disable sorting...
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )

    # End of directory...
    xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

    ########################################

def searchmovie(params,url,category):
    xbmc.output("[cineblog01.py] searchmovie")

    keyboard = xbmc.Keyboard('')
    keyboard.doModal()
    if (keyboard.isConfirmed()):
        tecleado = keyboard.getText()
        if len(tecleado)>0:
            #convert to HTML
            tecleado = tecleado.replace(" ", "+")
            searchUrl = "http://www.cineblog01.com/?s="+tecleado
            listvideos(params,searchUrl,category)

def listcat(params,url,category):
    xbmc.output("[cineblog01.py] mainlist")
    if url =="":
        url = "http://cineblog01.com/"
        
    # Descarga la página
    data = scrapertools.cachePage(url)
    #xbmc.output(data)

    # Extrae las entradas (carpetas)
    patronvideos  = '<div id="covershot".*?<a.*?<img src="(.*?)".*?'
    patronvideos += '<div id="post-title"><a href="(.*?)".*?'
    patronvideos += '<h3>(.*?)</h3>'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for match in matches:
        # Titulo
        UnicodeDecodedTitle = match[2].decode("utf-8")
        unescapedTitle = unescape (UnicodeDecodedTitle)
        scrapedtitle = unescapedTitle.encode("latin1","ignore") 
        # URL
        scrapedurl = urlparse.urljoin(url,match[1])
        # Thumbnail
        scrapedthumbnail = urlparse.urljoin(url,match[0])
        # Argumento

        # Depuracion
        if (DEBUG):
            xbmc.output("scrapedtitle="+scrapedtitle)
            xbmc.output("scrapedurl="+scrapedurl)
            xbmc.output("scrapedthumbnail="+scrapedthumbnail)

        # Añade al listado de XBMC
        xbmctools.addthumbnailfolder( CHANNELNAME , scrapedtitle , scrapedurl , scrapedthumbnail, "detail" )
    # Remove the next page mark
    patronvideos = '<a href="(http://cineblog01.com/category/[a-z]+'
    patronvideos += '/page/[0-9]+/)">Avanti >'
    matches = re.compile (patronvideos, re.DOTALL).findall (data)
    scrapertools.printMatches (matches)

    if len(matches)>0:
        scrapedtitle = "(Avanti ->)"
        scrapedurl = matches[0]
        scrapedthumbnail = ""
        scrapedplot = ""
        if (DEBUG):
            xbmc.output("scrapedtitle="+scrapedtitle)
            xbmc.output("scrapedurl="+scrapedurl)
            xbmc.output("scrapedthumbnail="+scrapedthumbnail)
        xbmctools.addnewfolder( CHANNELNAME , "listcat" , category , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )

    # Label (top-right)...
    xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )

    # Disable sorting...
    xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )

    # End of directory...
    xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def listvideos(params,url,category):
    xbmc.output("[cineblog01.py] mainlist")

    if url =="":
        url = "http://cineblog01.com/"

    # Descarga la página
    data = scrapertools.cachePage(url)
    #xbmc.output(data)

    # Extrae las entradas (carpetas)
    patronvideos  = '<div id="covershot".*?<a.*?<img src="(.*?)".*?'
    patronvideos += '<div id="post-title"><a href="(.*?)".*?'
    patronvideos += '<h3>(.*?)</h3>.*?&#160;'
    patronvideos += '&#160;(.*?)</p>'
    #patronvideos += '<div id="description"><p>(.?*)</div>'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for match in matches:
        # Titulo
        UnicodeDecodedTitle = match[2].decode("utf-8")
        unescapedTitle = unescape (UnicodeDecodedTitle)
        scrapedtitle = unescapedTitle.encode("latin1","ignore") 
        # URL
        scrapedurl = urlparse.urljoin(url,match[1])
        # Thumbnail
        scrapedthumbnail = urlparse.urljoin(url,match[0])
        # Argumento
        UnicodeDecodedTitle = match[3].decode("utf-8")
        unescapedTitle = unescape (UnicodeDecodedTitle)
        scrapedplot = unescapedTitle.encode("latin1","ignore") 
        #scrapedplot = match[3]
        # Depuracion
        if (DEBUG):
            xbmc.output("scrapedtitle="+scrapedtitle)
            xbmc.output("scrapedurl="+scrapedurl)
            xbmc.output("scrapedthumbnail="+scrapedthumbnail)
#            xbmc.output("scrapeddescription="+scrapeddescription)

        # Añade al listado de XBMC
        xbmctools.addnewfolder( CHANNELNAME , "detail" , category , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )

    # Remove the next page mark <a href="http://cineblog01.com/page/2/">Avanti
    patronvideos = '<a href="(http://www.cineblog01.com/page/[0-9]+[^"]+)">Avanti >'
    matches = re.compile (patronvideos, re.DOTALL).findall (data)
    scrapertools.printMatches (matches)

    if len(matches)>0:
        scrapedtitle = "(Avanti ->)"
        scrapedurl = matches[0]
        scrapedthumbnail = ""
        scrapedplot = ""
        if (DEBUG):
            xbmc.output("scrapedtitle="+scrapedtitle)
            xbmc.output("scrapedurl="+scrapedurl)
            xbmc.output("scrapedthumbnail="+scrapedthumbnail)
        xbmctools.addnewfolder( CHANNELNAME , "listvideos" , category , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )

    # Label (top-right)...
    xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
    xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )
    xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def listanime(params,url,category):
    xbmc.output("[cineblog01.py] mainlist")

    if url =="":
        url = "http://www.cineblog01.info/anime/"

    # Descarga la página
    data = scrapertools.cachePage(url)
    #xbmc.output(data)

    # Extrae las entradas (carpetas)
    patronvideos  = '<div id="covershot".*?<a.*?<img src="(.*?)".*?'
    patronvideos += '<div id="post-title"><a href="(.*?)".*?'
    patronvideos += '<h3>(.*?)</h3>'
    patronvideos += '(.*?)</p>'
    #patronvideos += '<div id="description"><p>(.?*)</div>'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for match in matches:
        # Titulo
        UnicodeDecodedTitle = match[2].decode("utf-8")
        unescapedTitle = unescape (UnicodeDecodedTitle)
        scrapedtitle = unescapedTitle.encode("latin1","ignore") 
        # URL
        scrapedurl = urlparse.urljoin(url,match[1])
        # Thumbnail
        scrapedthumbnail = urlparse.urljoin(url,match[0])
        # Argumento
        UnicodeDecodedTitle = match[3].decode("utf-8")
        unescapedTitle = unescape (UnicodeDecodedTitle)
        scrapedplot = unescapedTitle.encode("latin1","ignore") 
        #scrapedplot = match[3]
        # Depuracion
        if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

        # Añade al listado de XBMC
        xbmctools.addnewfolder( CHANNELNAME , "detail" , category , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )

    # Remove the next page mark
    patronvideos = '<a href="(http://www.cineblog01.info/anime/page/[0-9]+)">&gt;'
    matches = re.compile (patronvideos, re.DOTALL).findall (data)
    scrapertools.printMatches (matches)

    if len(matches)>0:
        scrapedtitle = "(Avanti ->)"
        scrapedurl = matches[0]
        scrapedthumbnail = ""
        scrapedplot = ""
        if (DEBUG):
            xbmc.output("scrapedtitle="+scrapedtitle)
            xbmc.output("scrapedurl="+scrapedurl)
            xbmc.output("scrapedthumbnail="+scrapedthumbnail)
        xbmctools.addnewfolder( CHANNELNAME , "listanime" , category , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )

    # Label (top-right)...
    xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
    xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )
    xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )


def listserie(params,url,category):
    xbmc.output("[cineblog01.py] mainlist")

    if url =="":
        url = "http://www.cineblog01.info/serietv/"

    # Descarga la página
    data = scrapertools.cachePage(url)
    #xbmc.output(data)

    # Extrae las entradas (carpetas)
    patronvideos  = '<div id="covershot".*?<a.*?<img src="(.*?)".*?'
    patronvideos += '<div id="post-title"><a href="(.*?)".*?'
    patronvideos += '<h3>(.*?)</h3>'
    patronvideos += '(.*?)</p>'
    #patronvideos += '<div id="description"><p>(.?*)</div>'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for match in matches:
        # Titulo
        UnicodeDecodedTitle = match[2].decode("utf-8")
        unescapedTitle = unescape (UnicodeDecodedTitle)
        scrapedtitle = unescapedTitle.encode("latin1","ignore") 
        # URL
        scrapedurl = urlparse.urljoin(url,match[1])
        # Thumbnail
        scrapedthumbnail = urlparse.urljoin(url,match[0])
        # Argumento
        UnicodeDecodedTitle = match[3].decode("utf-8")
        unescapedTitle = unescape (UnicodeDecodedTitle)
        scrapedplot = unescapedTitle.encode("latin1","ignore") 
        #scrapedplot = match[3]
        # Depuracion
        if (DEBUG):
            xbmc.output("scrapedtitle="+scrapedtitle)
            xbmc.output("scrapedurl="+scrapedurl)
            xbmc.output("scrapedthumbnail="+scrapedthumbnail)
#            xbmc.output("scrapeddescription="+scrapeddescription)

        # Añade al listado de XBMC
        xbmctools.addnewfolder( CHANNELNAME , "detail" , category , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )

    # Remove the next page mark
    patronvideos = '<a href="(http://www.cineblog01.info/serietv/page/[0-9]+)">&gt;'
    matches = re.compile (patronvideos, re.DOTALL).findall (data)
    scrapertools.printMatches (matches)

    if len(matches)>0:
        scrapedtitle = "(Avanti ->)"
        scrapedurl = matches[0]
        scrapedthumbnail = ""
        scrapedplot = ""
        if (DEBUG):
            xbmc.output("scrapedtitle="+scrapedtitle)
            xbmc.output("scrapedurl="+scrapedurl)
            xbmc.output("scrapedthumbnail="+scrapedthumbnail)
        xbmctools.addnewfolder( CHANNELNAME , "listserie" , category , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )

    # Label (top-right)...
    xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
    xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )
    xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )


def detail(params,url,category):
    xbmc.output("[cineblog01.py] detail")

    title = params.get("title")
    thumbnail = params.get("thumbnail")
    xbmc.output("[cineblog01.py] title="+title)
    xbmc.output("[cineblog01.py] thumbnail="+thumbnail)

    # Descarga la página
    data = scrapertools.cachePage(url)
    #xbmc.output(data)

    # ------------------------------------------------------------------------------------
    # Busca los enlaces a los videos
    # ------------------------------------------------------------------------------------
    listavideos = servertools.findvideos(data)

    for video in listavideos:
        xbmctools.addvideo( CHANNELNAME , "Megavideo - "+video[0] , video[1] , category , video[2] )
    # ------------------------------------------------------------------------------------

    # Label (top-right)...
    xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
        
    # Disable sorting...
    xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )

    # End of directory...
    xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def play(params,url,category):
    xbmc.output("[cineblog01.py] play")

    title = unicode( xbmc.getInfoLabel( "ListItem.Title" ), "utf-8" )
    thumbnail = xbmc.getInfoImage( "ListItem.Thumb" )
    plot = unicode( xbmc.getInfoLabel( "ListItem.Plot" ), "utf-8" )
    server = params["server"]
    xbmc.output("[cineblog01.py] thumbnail="+thumbnail)
    xbmc.output("[cineblog01.py] server="+server)
    
    xbmctools.playvideo(CHANNELNAME,server,url,category,title,thumbnail,plot)

#mainlist(None,"","mainlist")
#detail(None,"http://impresionante.tv/ponyo.html","play")
