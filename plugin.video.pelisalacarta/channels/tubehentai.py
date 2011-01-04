# -*- coding: utf-8 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para tubehentai
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#------------------------------------------------------------
import urlparse,urllib2,urllib,re
import os
import sys
import xbmc
import xbmcgui
import xbmcplugin
import scrapertools
import megavideo
import servertools
import binascii
import xbmctools
import config
from item import Item
import logger

CHANNELNAME = "tubehentai"

# Esto permite su ejecución en modo emulado
try:
    pluginhandle = int( sys.argv[ 1 ] )
except:
    pluginhandle = ""

# Traza el inicio del canal
logger.info("[tubehentai.py] init")

DEBUG = True

def mainlist(params,url,category):
    logger.info("[tubehentai.py] mainlist")
    
    itemlist = getmainlist(params,url,category)
    xbmctools.renderItems(itemlist, params, url, category)

def getmainlist(params,url,category):
    logger.info("[tubehentai.py] getmainlist")

    itemlist = []
    itemlist.append( Item( channel=CHANNELNAME , title="Novedades" , action="novedades" , url="http://tubehentai.com/" , folder=True ) )
    
    return itemlist

def novedades(params,url,category):
    logger.info("[tubehentai.py] novedades")

    itemlist = getnovedades(params,url,category)
    xbmctools.renderItems(itemlist, params, url, category)

def getnovedades(params,url,category):
    logger.info("[tubehentai.py] getnovedades")

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
        <a href="http://www.tubehentai.com/videos/1167/teen-fuck-in-hospital.html" target="_self">
            <img src="http://media.tubehentai.com/thumbs/4cbb3700dbdd91.avi/4cbb3700dbdd91.avi-3.jpg" alt="Teen Fuck in Hospital" name="4cbb3700dbdd91.avi" id="4cbb3700dbdd91.avi" onmouseover='startm("4cbb3700dbdd91.avi","http://media.tubehentai.com/thumbs/4cbb3700dbdd91.avi/4cbb3700dbdd91.avi-",".jpg");' onmouseout='endm("4cbb3700dbdd91.avi"); this.src="http://media.tubehentai.com/thumbs/4cbb3700dbdd91.avi/4cbb3700dbdd91.avi-3.jpg";' height="164" width="218" border="0">
        </a>
    '''

    #patronvideos  = '<p style="text-align: center;">.*?'
    patronvideos = '<a href="(http://www.tubehentai.com/videos/[^"]+)"[^>]*?>[^<]*?'
    patronvideos += '<img src="(http://media.tubehentai.com/thumbs/[^"]+)" alt="([^"]+)"[^>]+>[^<]*?</a>'


    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    if DEBUG: scrapertools.printMatches(matches)

    itemlist = []
    for match in matches:
        # Titulo
        scrapedtitle = match[2]
        scrapedurl = match[0]
        scrapedthumbnail = match[1].replace(" ", "%20")
        scrapedplot = scrapertools.htmlclean(match[2].strip())
        if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

        # Añade al listado de XBMC
        itemlist.append( Item(channel=CHANNELNAME, action="play", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=False) )

    # ------------------------------------------------------
    # Extrae el paginador
    # ------------------------------------------------------
    #<a href="page2.html" class="next">Next »</a>
    patronvideos  = '<a href=\'(page[^\.]+\.html)\'[^>]*?>Next[^<]*?<\/a>'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    if len(matches)>0:
        scrapedurl = urlparse.urljoin(url,"/" + matches[0])
        logger.info("[tubehentai.py] " + scrapedurl)
        itemlist.append( Item(channel=CHANNELNAME, action="novedades", title="!Página siguiente" , url=scrapedurl , folder=True) )


    return itemlist

def play(params,url,category):
    logger.info("[tubehentai.py] detail")

    title = urllib.unquote_plus( params.get("title") )
    thumbnail = urllib.unquote_plus( params.get("thumbnail") )
    plot = urllib.unquote_plus( params.get("plot") )

    # Descarga la página
    data = scrapertools.cachePage(url)
    #logger.info(data)

    patron = 's1.addParam\("flashvars","settings=http\://www.tubehentai.com/playerConfig.php\?([^"]+)"\)'
    matches = re.compile(patron,re.DOTALL).findall(data)
    if len(matches)>0:
        url = "http://media.tubehentai.com/videos/" + matches[0]
        server="Directo"
        xbmctools.playvideo4(CHANNELNAME,server,url,category,title,thumbnail,plot)
    # ------------------------------------------------------------------------------------