# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para documentariestv.com
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

CHANNELNAME = "documentariestv"

# Esto permite su ejecución en modo emulado
try:
    pluginhandle = int( sys.argv[ 1 ] )
except:
    pluginhandle = ""

logger.info("[documentariestv.py] init")
tecleadoultimo = ""
DEBUG = True
IMAGES_PATH = xbmc.translatePath( os.path.join( os.getcwd(), 'resources' , 'images' , 'documaniatv' ) )
#############----------------------------------------------------------#############

def mainlist(params,url,category):
    logger.info("[documentariestv.py] mainlist")
    
    xbmctools.addnewfolder( CHANNELNAME , "documentalesnuevos" , category , "New Documentaries","http://www.documentariestv.net/newvideos.html",os.path.join(IMAGES_PATH, 'nuevos.png'),"")
    xbmctools.addnewfolder( CHANNELNAME , "TipoDocumental"   , category , "Documentary Type","",os.path.join(IMAGES_PATH, 'tipo.png'),"")
    xbmctools.addnewfolder( CHANNELNAME , "tagdocumentales"  , category , "Documentary Tags","http://www.documentariestv.net/index.html",os.path.join(IMAGES_PATH, 'tag.png'),"")
    xbmctools.addnewfolder( CHANNELNAME , "topdocumentales"  , category , "Top Documentaries","http://www.documentariestv.net/topvideos.html",os.path.join(IMAGES_PATH, 'top.png'),"")
    xbmctools.addnewfolder( CHANNELNAME , "listatipodocumental"     , category , "Documentaries being watched right now","http://www.documentariestv.net/index.html",os.path.join(IMAGES_PATH, 'viendose.png'),"")
    xbmctools.addnewfolder( CHANNELNAME , "documentaldeldia"     , category , "Featured documentary - Now Playing","http://www.documentariestv.net/index.html",os.path.join(IMAGES_PATH, 'deldia.png'),"")
    xbmctools.addnewfolder( CHANNELNAME , "search"           , category , "Search",tecleadoultimo,os.path.join(IMAGES_PATH, 'search_icon.png'),"")

    # Label (top-right)...
    xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )
        
    # Disable sorting...
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )

    # End of directory...
    xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

################-----------------------------------------------------##############

        
##############------------------------------------------------------#################        

def search(params,url,category):
    logger.info("[documentariestv.py] search")

    ultimo = params.get("url")
    keyboard = xbmc.Keyboard(ultimo)
    keyboard.doModal()
        
    if (keyboard.isConfirmed()):
        tecleado = keyboard.getText()
        if len(tecleado)>0:
            tecleadoultimo = tecleado
            #convert to HTML
            tecleado = tecleado.replace(" ", "+")
            #keyboard.setHeading(tecleadoultimo)
            logger.info("tecleadoultimo = "+tecleadoultimo)
            searchUrl = "http://www.documentariestv.net/search.php?keywords="+tecleado+"&btn=Search"
            searchresults(params,searchUrl,category)



###############---------------------------------------------------#####################

def performsearch(texto):
    logger.info("[documentariestv.py] performsearch")
    url = "http://www.documentariestv.net/search.php?keywords="+texto+"&btn=Search"

    # Descarga la página
    data = scrapertools.cachePage(url)

    # Extrae las entradas (carpetas)
    patronvideos = '<li class="video">[^<]+<div class="video_i">[^<]+<a href="([^"]+)"[^"]+"([^"]+)"  alt="([^"]+)"[^/]+/><div class="tag".*?</div>[^<]+<span class="artist_name">([^<]+)</span>'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)
    
    resultados = []

    for match in matches:
        scrapedtitle = acentos(match[2])
        scrapedurl = match[0]
        scrapedthumbnail = match[1]
        scrapedplot = match[3]
        if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

        # Añade al listado de XBMC
        resultados.append( [CHANNELNAME , "detail" , "buscador" , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot ] )
        
    return resultados

def searchresults(params,url,category):
    logger.info("[documentariestv.py] searchresults")

    # Descarga la página
    data = scrapertools.cachePage(url)
    #logger.info(data)

    # Extrae las entradas (carpetas)
    patronvideos = '<li class="video">[^<]+<div class="video_i">[^<]+<a href="([^"]+)"[^"]+"([^"]+)"  alt="([^"]+)"[^/]+/><div class="tag".*?</div>[^<]+<span class="artist_name">([^<]+)</span>'
    
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for match in matches:
        # Titulo
        scrapedtitle = acentos(match[2])

        # URL
        scrapedurl = match[0]
        
        # Thumbnail
        scrapedthumbnail = match[1]
        
        # procesa el resto
        scrapedplot = match[3]

        # Depuracion
        if (DEBUG):
            logger.info("scrapedtitle="+scrapedtitle+" - "+scrapedplot)
            logger.info("scrapedurl="+scrapedurl)
            logger.info("scrapedthumbnail="+scrapedthumbnail)

        # Añade al listado de XBMC
        xbmctools.addnewfolder( CHANNELNAME , "detail" , category , scrapedtitle + " - " + scrapedplot , scrapedurl , scrapedthumbnail , scrapedplot )


                #llama a la rutina paginasiguiente
        cat = 'busca'
        paginasiguientes(patronvideos,data,category,cat)
    
    # Label (top-right)...
    xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )

    # Disable sorting...
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )

    # End of directory...
    xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

#############----------------------------------------------------------#############        


def TipoDocumental(params, url, category):
    logger.info("[documentariestv.py] TipoDocumental")
    xbmctools.addnewfolder(CHANNELNAME , "listatipodocumental" , category , "Art/Cinema","http://www.documentariestv.net/browse-art-","","")
    xbmctools.addnewfolder(CHANNELNAME , "listatipodocumental" , category , "Biography","http://www.documentariestv.net/browse-Biography-","","")
    xbmctools.addnewfolder(CHANNELNAME , "listatipodocumental" , category , "Crime/Prison","http://www.documentariestv.net/browse-crime-","","")
    xbmctools.addnewfolder(CHANNELNAME , "listatipodocumental" , category , "Drugs","http://www.documentariestv.net/browse-drugs-","","")
    xbmctools.addnewfolder(CHANNELNAME , "listatipodocumental" , category , "History","http://www.documentariestv.net/browse-history-","","")
    xbmctools.addnewfolder(CHANNELNAME , "listatipodocumental" , category , "Mysteries","http://www.documentariestv.net/browse-Mysteries-","","")
    xbmctools.addnewfolder(CHANNELNAME , "listatipodocumental" , category , "Nature","http://www.documentariestv.net/browse-nature-","","")
    xbmctools.addnewfolder(CHANNELNAME , "listatipodocumental" , category , "Politics","http://www.documentariestv.net/browse-politics-","","")
    xbmctools.addnewfolder(CHANNELNAME , "listatipodocumental" , category , "Religion/Spiritualy","http://www.documentariestv.net/browse-religion-","","")
    xbmctools.addnewfolder(CHANNELNAME , "listatipodocumental" , category , "Science","http://www.documentariestv.net/browse-Science-","","")
    xbmctools.addnewfolder(CHANNELNAME , "listatipodocumental" , category , "Social","http://www.documentariestv.net/browse-social-","","")
    xbmctools.addnewfolder(CHANNELNAME , "listatipodocumental" , category , "Sports","http://www.documentariestv.net/browse-Sports-","","")
    xbmctools.addnewfolder(CHANNELNAME , "listatipodocumental" , category , "Technology","http://www.documentariestv.net/browse-Technology-","","")
    xbmctools.addnewfolder(CHANNELNAME , "listatipodocumental" , category , "Terrorism","http://www.documentariestv.net/browse-terrorism-","","")
    xbmctools.addnewfolder(CHANNELNAME , "listatipodocumental" , category , "Travel/adventure","http://www.documentariestv.net/browse-travel-","","")

    # Label (top-right)...
    xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )

    # Disable sorting...
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )

    # End of directory...
    xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

 


#############--------------------------------------------------------###########

def listarpor(params,url,category):
    
    url1=url
    title = urllib.unquote_plus(params.get("title"))[:11]
       
    #verifica si es la primera vez o viene de una paginacion
    if  url.endswith(".html"):               
        return(url)
    else:
        fecha = "videos-1-date.html"
        vistas = "videos-1-views.html"
        rating = "videos-1-rating.html" 
    # Abre el diálogo de selección
    opciones = []
    opciones.append("Date")
    opciones.append("Views")
    opciones.append("Rating")
    dia = xbmcgui.Dialog()
    seleccion = dia.select("List "+title+"  for: ", opciones)
    logger.info("seleccion=%d" % seleccion)        
    if seleccion==-1:
        return("")
    if seleccion==0:
        url1 = url + fecha
    elif seleccion==1:
        url1 = url + vistas
    elif seleccion==2:
        url1 = url + rating
    return(url1)
#############-----------------------------------#########################

def tagdocumentales(params,url,category):
    logger.info("[documentariestv.py] tagdocumentales")

    xbmctools.addnewfolder(CHANNELNAME , "tagdocumentaleslist" , category , "nature","http://www.documentariestv.net/tags/nature/","","")
    xbmctools.addnewfolder(CHANNELNAME , "tagdocumentaleslist" , category , "religion","http://www.documentariestv.net/tags/religion/","","")
    xbmctools.addnewfolder(CHANNELNAME , "tagdocumentaleslist" , category ,"mysteries","http://www.documentariestv.net/tags/mysteries/","","")
    xbmctools.addnewfolder(CHANNELNAME , "tagdocumentaleslist" , category ,"history","http://www.documentariestv.net/tags/history/","","")
    xbmctools.addnewfolder(CHANNELNAME , "tagdocumentaleslist" , category , "horizon","http://www.documentariestv.net/tags/horizon/","","") 
    xbmctools.addnewfolder(CHANNELNAME , "tagdocumentaleslist" , category , "bbc","http://www.documentariestv.net/tags/bbc/","","")
    xbmctools.addnewfolder(CHANNELNAME , "tagdocumentaleslist" , category , "technology","http://www.documentariestv.net/tags/technology/","","")
    xbmctools.addnewfolder(CHANNELNAME , "tagdocumentaleslist" , category , "channel4","http://www.documentariestv.net/tags/channel4/","","")
    xbmctools.addnewfolder(CHANNELNAME , "tagdocumentaleslist" , category ,"politics","http://www.documentariestv.net/tags/politics/","","")
    xbmctools.addnewfolder(CHANNELNAME , "tagdocumentaleslist" , category , "pbs","http://www.documentariestv.net/tags/pbs/","","") 
    xbmctools.addnewfolder(CHANNELNAME , "tagdocumentaleslist" , category , "crime","http://www.documentariestv.net/tags/crime/","","")
    xbmctools.addnewfolder(CHANNELNAME , "tagdocumentaleslist" , category , "social","http://www.documentariestv.net/tags/social/","","")
    xbmctools.addnewfolder(CHANNELNAME , "tagdocumentaleslist" , category , "history channel","http://www.documentariestv.net/tags/history-channel/","","")
    xbmctools.addnewfolder(CHANNELNAME , "tagdocumentaleslist" , category ,"the universe","http://www.documentariestv.net/tags/the-universe/","","")
    xbmctools.addnewfolder(CHANNELNAME , "tagdocumentaleslist" , category , "terrorism","http://www.documentariestv.net/tags/terrorism/","","") 
    xbmctools.addnewfolder(CHANNELNAME , "tagdocumentaleslist" , category , "discovery channel","http://www.documentariestv.net/tags/discovery-channel/","","")
    xbmctools.addnewfolder(CHANNELNAME , "tagdocumentaleslist" , category , "biography","http://www.documentariestv.net/tags/biography/","","")
    xbmctools.addnewfolder(CHANNELNAME , "tagdocumentaleslist" , category , "astronomy","http://www.documentariestv.net/tags/astronomy/","","")
    xbmctools.addnewfolder(CHANNELNAME , "tagdocumentaleslist" , category ,"national geographic","http://www.documentariestv.net/tags/national-geographic/","","")
    xbmctools.addnewfolder(CHANNELNAME , "tagdocumentaleslist" , category , "science","http://www.documentariestv.net/tags/science/","","") 
   

        # Label (top-right)...
    xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )

    # Disable sorting...
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )

    # End of directory...
    xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

       
############---------------------------------------------------------###########


def listatipodocumental(params,url,category):
    logger.info("[documentariestv.py] listatipodocumental")

    # busca tipo de listado por : FECHA | VISTAS | RATING #
    url = listarpor(params,url,category) 
    if len(url)==0 :
        return  
    # Descarga la página
    data = scrapertools.cachePage(url)
    
    # Extrae las entradas (carpetas)
    

    if url == "http://www.documentariestv.net/index.html":
        patronvideos = '<li class="item">[^<]+<a href="([^"]+)"><img src="([^"]+)" alt="([^"]+)" class="imag".*?/></a>'
        cat = "viendose"
    else:  
        patronvideos  = '<li class="video">[^<]+<div class="video_i">[^<]+<a href="([^"]+)"[^"]+"([^"]+)"  alt="([^"]+)"[^/]+/><div class="tag".*?</div>[^<]+<span class="artist_name">([^<]+)</span>'
        cat = "tipo"
        
            
    
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)
    #logger.info("matches = "+matches[0])
    scrapedplot = ""
    for match in matches:
        scrapedtitle = acentos(match[2])
        scrapedurl = match[0]
        scrapedthumbnail = match[1]
        if cat == "tipo":
            scrapedplot = match[3]
        else:
            for campo in re.findall("/(.*?)/",match[0]):
                scrapedplot = campo
        # Depuracion
        if (DEBUG):
            logger.info("scrapedtitle="+scrapedtitle)
            logger.info("scrapedurl="+scrapedurl)
            logger.info("scrapedthumbnail="+scrapedthumbnail)

        # Añade al listado de XBMC
        xbmctools.addnewfolder( CHANNELNAME , "detail" , category , scrapedtitle + " - " + scrapedplot , scrapedurl , scrapedthumbnail , scrapedplot )

        if cat == "tipo":
            patron_pagina_sgte = '</span><a href="([^"]+)"'
            paginasiguientes(patron_pagina_sgte,data,category,cat)

    # Label (top-right)...
    xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )

    # Disable sorting...
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )

    # End of directory...
    xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

##############---------------------------------------------------------##############

def documentalesnuevos(params,url,category):
    
    url1=url
    # Abre el diálogo de selección
    opciones = []
    opciones.append("All time")
    opciones.append("Today")
    opciones.append("Yesterday")
    opciones.append("This month")
    dia = xbmcgui.Dialog()
    seleccion = dia.select("Select one", opciones)
    logger.info("seleccion=%d" % seleccion)        
    if seleccion==-1:
        return
    if seleccion==0:
        url1 = "http://www.documentariestv.net/newvideos.html"
    elif seleccion==1:
        url1 = "http://www.documentariestv.net/newvideos.html?d=today"
    elif seleccion==2:
        url1 = "http://www.documentariestv.net/newvideos.html?d=yesterday"
    elif seleccion==3:
        url1 = "http://www.documentariestv.net/newvideos.html?d=month"
    documentalesnuevoslist(params,url1,category)

#############----------------------------------------########################

def documentalesnuevoslist(params,url,category):
    logger.info("[documentariestv.py] DocumentalesNuevos")

    # Descarga la página
    data = scrapertools.cachePage(url)
    #logger.info(data)

    # Extrae las entradas (carpetas)
    patronvideos  = '<tr><td.*?<a href="([^"]+)">'
    patronvideos += '<img src="([^"]+)".*?'
    patronvideos += 'alt="([^"]+)".*?'
    patronvideos += 'width="250">([^<]+)<'
    patronvideos += 'td class.*?<a href="[^"]+">[^<]+</a></td><td class.*?>([^<]+)</td></tr>'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    #logger.info("matches = "+str(matches))
    if DEBUG:
            scrapertools.printMatches(matches)
    for match in matches:
        # Titulo
        # Titulo
        scrapedtitle = acentos(match[2])+" - " + match[3]+" - " + match[4] 

        # URL
        scrapedurl = match[0]
        
        # Thumbnail
        scrapedthumbnail = match[1]
        imagen = ""
        # procesa el resto
        scrapedplot = match[3]
        tipo = match[3]

        # Depuracion
        if (DEBUG):
            logger.info("scrapedtitle="+scrapedtitle)
            logger.info("scrapedurl="+scrapedurl)
            logger.info("scrapedthumbnail="+scrapedthumbnail)

        # Añade al listado de XBMC
        #xbmctools.addthumbnailfolder( CHANNELNAME , scrapedtitle, scrapedurl , scrapedthumbnail, "detail" )
        xbmctools.addnewfolder( CHANNELNAME , "detail" , category , scrapedtitle ,scrapedurl , scrapedthumbnail , scrapedplot )

        # Busca enlaces de paginas siguientes...
        cat = "nuevo"
        patronvideo = patronvideos
        paginasiguientes(patronvideo,data,category,cat)     

    # Label (top-right)...
    xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )

    # Disable sorting...
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )

    # End of directory...
    xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

##########---------------------------------------------------------------#############

def documentaldeldia(params,url,category):
#    list(params,url,category,patronvideos)
    logger.info("[documentariestv.py] Documentaldeldia")
               
    # Descarga la página
    data = scrapertools.cachePage(url)
    #logger.info(data)
        
    patronvideos = 'Now Playing: <a href="([^"]+)">([^<]+)</a>'
    matches =  re.compile(patronvideos,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)
    for match in matches:
        # Titulo
        # Titulo
        scrapedtitle = acentos(match[1])
        
        # URL
        scrapedurl = match[0]
                  
            # Thumbnail
        scrapedthumbnail = ""
        
        # scrapedplot
        scrapedplot = ""
        if (DEBUG):
            logger.info("scrapedtitle="+scrapedtitle)
            logger.info("scrapedurl="+scrapedurl)
            logger.info("scrapedthumbnail="+scrapedthumbnail)
        
        xbmctools.addnewfolder( CHANNELNAME , "detail" , category , scrapedtitle , scrapedurl , scrapedthumbnail , scrapedplot ) 
    xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )

    # Disable sorting...
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )

    # End of directory...
    xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True ) 

################---------------------------------------------------------###########

def tagdocumentaleslist(params,url,category):
    logger.info("[documentariestv.py] tagdocumentaleslist")

    # Descarga la página
    data = scrapertools.cachePage(url)
    #logger.info(data)



    # Extrae el listado de documentales del tag
    patronvideos = '<li class="video">[^<]+<div class="video_i">[^<]+<a href="([^"]+)"[^"]+"([^"]+)"  alt="([^"]+)"[^/]+/><div class="tag".*?</div>[^<]+<span class="artist_name">([^<]+)</span>'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

         

    for match in matches:
        # Titulo
        scrapedtitle = acentos(match[2])

        # URL
        scrapedurl = match[0]
        
        # Thumbnail
        scrapedthumbnail = match[1]
        
                # procesa el resto
        scrapeddescription = match[3]

        # procesa el resto
        scrapedplot = ""

        # Depuracion
        if (DEBUG):
            logger.info("scrapedtitle="+scrapedtitle)
            logger.info("scrapedurl="+scrapedurl)
            logger.info("scrapedthumbnail="+scrapedthumbnail)

        # Añade al listado de XBMC
        xbmctools.addnewfolder( CHANNELNAME , "detail" , category , scrapedtitle+" - "+scrapeddescription , scrapedurl , scrapedthumbnail , scrapedplot )

        #Busca la pagina siguiente
        cat = "tag"
        patronvideo = patronvideos
        paginasiguientes(patronvideo,data,category,cat)

    # Label (top-right)...
    xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )

    # Disable sorting...
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )

    # End of directory...
    xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

#############----------------------------------------------------------#############



############---------------------------------------------------#######################

def topdocumentales(params,url,category):
    url2=url
    # Abre el diálogo de selección
    opciones = []
    opciones.append("All time")
    opciones.append("Last 7 days")
    opciones.append("Biography")
    opciones.append("Technology")
    opciones.append("Science")
    opciones.append("Nature")
    opciones.append("Politics")
    opciones.append("History")
    opciones.append("Sport")
    opciones.append("Mysteries")
    opciones.append("Social")
    opciones.append("Travel/adventure")
    opciones.append("Art/Cinema")
    opciones.append("Religion/Spirituality")
    opciones.append("Terrorism/911")
    opciones.append("Drugs")
    opciones.append("Crime/Prison")
    dia = xbmcgui.Dialog()
    seleccion = dia.select("Select one", opciones)
    logger.info("seleccion=%d" % seleccion) 
    if seleccion==-1:
        return
    if seleccion==0:
        url2 = "http://www.documentariestv.net/topvideos.html"
    elif seleccion==1:
        url2 = "http://www.documentariestv.net/topvideos.html?do=recent"
    elif seleccion==2:
        url2 = "http://www.documentariestv.net/topvideos.html?c=Biography"
    elif seleccion==3:
        url2 = "http://www.documentariestv.net/topvideos.html?c=Technology" 
    elif seleccion==4: 
        url2 = "http://www.documentariestv.net/topvideos.html?c=Science"
    elif seleccion==5: 
        url2 = "http://www.documentariestv.net/topvideos.html?c=nature"
    elif seleccion==6:
        url2 = "http://www.documentariestv.net/topvideos.html?c=politics"
    elif seleccion==7:
        url2 = "http://www.documentariestv.net/topvideos.html?c=history"
    elif seleccion==8:
        url2 = "http://www.documentariestv.net/topvideos.html?c=Sports"
    elif seleccion==9:
        url2 = "http://www.documentariestv.net/topvideos.html?c=Mysteries"
    elif seleccion==10:
        url2 = "http://www.documentariestv.net/topvideos.html?c=social" 
    elif seleccion==11:
        url2 = "http://www.documentariestv.net/topvideos.html?c=travel"
    elif seleccion==12:
        url2 = "http://www.documentariestv.net/topvideos.html?c=art"               
    elif seleccion==13:
        url2 = "http://www.documentariestv.net/topvideos.html?c=religion"
    elif seleccion==14:
        url2 = "http://www.documentariestv.net/topvideos.html?c=terrorism"               
    elif seleccion==15:
        url2 = "http://www.documentariestv.net/topvideos.html?c=drugs"               
    elif seleccion==16:
        url2 = "http://www.documentariestv.net/topvideos.html?c=crime"                  
                        
    toplist(params,url2,category)
############----------------------------------------------####################

def toplist(params,url,category):
    logger.info("[documentariestv.py] toplist")

    # Descarga la página
    data = scrapertools.cachePage(url)
    #logger.info(data)


    # Extrae las entradas (carpetas)
    logger.info("[documentariestv.py] toplist "+url) 
    if url== "http://www.documentariestv.net/topvideos.html?do=recent":
            
        patronvideos = '<tr>[^>]+>([^<]+)</td>'
        patronvideos += '[^>]+><a href="([^"]+)">'
        patronvideos += '<img src="([^"]+)" alt="" class[^>]+>'
        patronvideos += '</a></td>[^>]+>([^<]+)</td>[^>]+>'
        patronvideos += '<a href="[^"]+">([^<]+)</a>'
        patronvideos += '</td>[^>]+>([^<]+)</td>'

    else:
        
        patronvideos = '<tr>[^>]+>([^<]+)</td>'
        patronvideos += '[^>]+><a href="([^"]+)">'
        patronvideos += '<img src="([^"]+)"'
        patronvideos += ' alt="([^"]+)"[^>]+>'
        patronvideos += '</a></td>[^>]+>([^<]+)</td>[^>]+>'
        patronvideos += '<a href="[^"]+">[^>]+></td>[^>]+>([^<]+)</td>'
    
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for match in matches:
        # Titulo
        scrapedtitle = acentos(match[3])

        # URL
        scrapedurl = match[1]
        
        # Thumbnail
        scrapedthumbnail = match[2]
        
        # procesa el resto
        scrapedplot = match[4]+" - " + "Views : "+match[5]+" times"

        # Depuracion
        if (DEBUG):
            logger.info("scrapedtitle="+scrapedtitle)
            logger.info("scrapedurl="+scrapedurl)
            logger.info("scrapedthumbnail="+scrapedthumbnail)

        # Añade al listado de XBMC
        #        xbmctools.addnewvideo( CHANNELNAME , "detail" , category , "directo" , match[0]+") "+scrapedtitle + " - " + scrapedplot , scrapedurl , scrapedthumbnail , scrapedplot )

        xbmctools.addthumbnailfolder( CHANNELNAME , match[0]+") "+scrapedtitle+" - "+scrapedplot, scrapedurl , scrapedthumbnail, "detail" )

    # Label (top-right)...
    xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )

    # Disable sorting...
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )

    # End of directory...
    xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

#############----------------------------------------------------------#############

def detail(params,url,category):
    logger.info("[documentariestv.py] detail")

    title = urllib.unquote_plus( params.get("title") )
    thumbnail = urllib.unquote_plus( params.get("thumbnail") )
    logger.info("[prueba.py] title="+title)
    logger.info("[prueba.py] thumbnail="+thumbnail)
    patrondescrip = '<h3>Description</h3>(.*?)</tr>'
    # Descarga la página
    data = scrapertools.cachePage(url)
    descripcion = ""
    plot = ""
    matches = re.compile(patrondescrip,re.DOTALL).findall(data)
    if DEBUG:
        if len(matches)>0:
            descripcion = matches[0]
            descripcion = descripcion.replace("&nbsp;","")
            descripcion = descripcion.replace("<br/>","")
            descripcion = descripcion.replace("\r","")
            descripcion = descripcion.replace("\n"," ")
            descripcion = descripcion.replace("\t"," ")
            descripcion = re.sub("<[^>]+>"," ",descripcion)
#                logger.info("descripcion="+descripcion)
            descripcion = acentos(descripcion)
#                logger.info("descripcion="+descripcion)
            try :
                plot = unicode( descripcion, "utf-8" ).encode("iso-8859-1")
            except:
                plot = descripcion
    # ----------------------------------------------------------------------------
    # Busca los enlaces a los videos de : "Megavideo"
    # ------------------------------------------------------------------------------------
    listavideos = servertools.findvideos(data)

    for video in listavideos:
        videotitle = video[0]
        url = video[1]
        logger.info("url   ="+url)
        if  url.endswith(".jpg"):break
        server = video[2]
        if server=="Megavideo" or "Veoh":
            xbmctools.addnewvideo( CHANNELNAME , "play" , category , server , title.strip().replace("(Megavideo)","").replace("  "," ") + " - " + videotitle , url , thumbnail , plot )
        else:
            xbmctools.addnewvideo( CHANNELNAME , "play" , category , server , title.strip().replace(server,"").replace("  "," ") + " - " + videotitle , url , thumbnail , plot )

    # ------------------------------------------------------------------------------------
    #  ---- Extrae los videos directos ----- 
    
    # Extrae los enlaces a los vídeos (Directo)
    patronvideos = "file: '([^']+)'"
    servidor = "Directo"
    extraevideos(patronvideos,data,category,title+" - directo",thumbnail,plot,servidor)
    # ---------------------------------------

    #  --- Extrae los videos de veoh  ----
    patronvideos = 'var embed_code[^>]+>   <param name="movie" value="http://www.veoh.com/static/swf/webplayer/WebPlayer.swf.*?permalinkId=(.*?)&player=videodetailsembedded&videoAutoPlay=0&id=anonymous"></param>'
    servidor = "Veoh"
    extraevideos(patronvideos,data,category,title+" - Video en  Veoh",thumbnail,plot,servidor)
    # ---------------------------------------

    #var embed_code =  '<embed id="VideoPlayback" src="http://video.google.com/googleplayer.swf?docid=1447612366747092264&hl=en&fs=true" style="width:496px;height:401px" allowFullScreen="true" allowScriptAccess="always" type="application/x-shockwave-flash" wmode="window">  </embed>' ;
    
    #  --- Extrae los videos de google  ----
    patronvideos = '<embed id="VideoPlayback" src="http://video.google.com/googleplayer.swf.*?docid=(.*?)&hl=en&'
    servidor = "Google"
    extraevideos(patronvideos,data,category,title+" - Video en google",thumbnail,plot,servidor)
    # --------------------------------------- 
    
    #  --- Extrae los videos de http://n59.stagevu.com  ----
    patronvideos = '"http://n59.stagevu.com/v/.*?/(.*?).avi"'
    servidor = "Stagevu"
    extraevideos(patronvideos,data,category,title,thumbnail,plot,servidor)
    
    # --Muestra Una opcion mas para videos documentales relacionados con el tema--
    
    xbmctools.addnewfolder( CHANNELNAME , "verRelacionados" , category , "Watch related video" , data , thumbnail , "Search some related Documenties" )

    # Label (top-right)...
    xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
        
    # Disable sorting...
    xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )

    # End of directory...
    xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

#############----------------------------------------------------------#############

def extraevideos(patronvideos,data,category,title,thumbnail,plot,servidor):
    logger.info("patron="+patronvideos)
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)        

    if len(matches)>0 :
    # Añade al listado de XBMC
        if servidor == "Directo":
            xbmctools.addnewvideo( CHANNELNAME , "play" , category , "Directo" , title, matches[0] , thumbnail , plot )
        
        elif servidor == "Veoh":
            veohurl = servertools.findurl(matches[0],"veoh")
            logger.info(" veohurl = " +veohurl)
        
            if len(veohurl)>0:
                if  veohurl=="http://./default.asp":
                    advertencia = xbmcgui.Dialog()
                    resultado = advertencia.ok('The Documental video' , title , 'not exist in Veoh','visit the web www.documentariestv.net for report this' )
                    return
                logger.info(" newmatches = "+veohurl)
                xbmctools.addnewvideo( CHANNELNAME , "play" , category , "Directo" , title, veohurl , thumbnail , plot )
            else:
                advertencia = xbmcgui.Dialog()
                resultado = advertencia.ok('The Documental video' , title , 'not exist in Veoh')
                return 
        
        elif servidor == "Google":
            url = "http://www.flashvideodownloader.org/download.php?u=http://video.google.com/videoplay?docid="+matches[0]
            logger.info(" Url = "+url)
            data = scrapertools.cachePage(url)
            newpatron = '</script><div.*?<a href="(.*?)" title="Click to Download">'
            newmatches = re.compile(newpatron,re.DOTALL).findall(data)
            if len(newmatches)>0:
                logger.info(" newmatches = "+newmatches[0])
                xbmctools.addnewvideo( CHANNELNAME , "play" , category , "Directo" , title, newmatches[0] , thumbnail , plot )

        elif servidor == "Stagevu":
            url= "http://stagevu.com/video/"+matches[0]
            url = servertools.findurl(url,servidor)
            logger.info(" url = "+url)
            videotitle = "Video en Stagevu"
            server = servidor
            xbmctools.addnewvideo( CHANNELNAME , "play" , category , "Directo" , title.strip().replace(server,"").replace("  "," ") + " - " + videotitle , url , thumbnail , plot )
#############----------------------------------------------------------#############

def play(params,url,category):
    logger.info("[documentariestv.py] play")

    title = unicode( xbmc.getInfoLabel( "ListItem.Title" ), "utf-8" )
    title = unicode( xbmc.getInfoLabel( "ListItem.Title" ), "utf-8" )
    try:
        thumbnail = urllib.unquote_plus( params.get("thumbnail") )
    except:
        thumbnail = xbmc.getInfoImage( "ListItem.Thumb" )
    plot = urllib.unquote_plus( params.get("plot") )

    try:
        plot = unicode( xbmc.getInfoLabel( "ListItem.Plot" ), "utf-8" )
    except:
        plot = xbmc.getInfoLabel( "ListItem.Plot" )

    server = params["server"]
    logger.info("[documentariestv.py] thumbnail="+thumbnail)
    logger.info("[documentariestv.py] server="+server)
    
    xbmctools.playvideo(CHANNELNAME,server,url,category,title,thumbnail,plot)

#############----------------------------------------------------------#############

def paginasiguientes(patronvideos,data,category,cat):

    # ------------------------------------------------------
    # Extrae la página siguiente
    # ------------------------------------------------------
    patron    = '</span><a href="([^"]+)"' 
    matches   = re.compile(patron,re.DOTALL).findall(data)
    #menutitle = "Volver Al Menu Principal"
    #menurl    = "http://www.documentariestv.net/"
    if DEBUG:
        scrapertools.printMatches(matches)

    for match in matches:
        scrapedtitle = "Next Page"
        scrapedurl = "http://www.documentariestv.net/" + match
        scrapedthumbnail = os.path.join(IMAGES_PATH, 'next.png')
        scrapeddescription = ""

        # Depuracion
        if DEBUG:
            logger.info("scrapedtitle="+scrapedtitle)
            logger.info("scrapedurl="+scrapedurl)
            logger.info("scrapedthumbnail="+scrapedthumbnail)

        if cat == 'tipo':   
        # Añade al listado de XBMC
            xbmctools.addthumbnailfolder( CHANNELNAME , scrapedtitle , scrapedurl , scrapedthumbnail, "listatipodocumental" )
        elif cat == 'nuevo':
            xbmctools.addthumbnailfolder( CHANNELNAME , scrapedtitle , scrapedurl , scrapedthumbnail, "documentalesnuevoslist" )
        elif cat == 'tag':
            xbmctools.addthumbnailfolder( CHANNELNAME , scrapedtitle , "http://www.documentariestv.net"+match , scrapedthumbnail, "tagdocumentaleslist" )
        elif cat == 'busca':
            xbmctools.addthumbnailfolder( CHANNELNAME , scrapedtitle , scrapedurl , scrapedthumbnail, "searchresults" )
                       

    #xbmctools.addthumbnailfolder( CHANNELNAME , menutitle , menurl , "", "volvermenu" )
    # Label (top-right)...
    xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )

    # Disable sorting...
    xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )

    # End of directory...
    xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )
########-------------------------------------------------------############
  
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
######-----------------------------------------------##############

def verRelacionados(params,data,category):
        
    patronvideos  = '<div class="item">.*?<a href="([^"]+)"'
    patronvideos += '><img src="([^"]+)".*?'
    patronvideos += 'alt="([^"]+)".*?/></a>.*?'
    patronvideos += '<span class="artist_name">([^<]+)</span>'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)
    for match in matches:
        # Titulo
        scrapedtitle = acentos(match[2])
    
        # URL
        scrapedurl = match[0]
        
        # Thumbnail
        scrapedthumbnail = match[1]
        
                # procesa el resto
        scrapeddescription = match[3]
    
        # procesa el resto
        scrapedplot = ""
    
        # Depuracion
        if (DEBUG):
            logger.info("scrapedtitle="+scrapedtitle)
            logger.info("scrapedurl="+scrapedurl)
            logger.info("scrapedthumbnail="+scrapedthumbnail)
    
        # Añade al listado de XBMC
        xbmctools.addnewfolder( CHANNELNAME , "detail" , category , scrapedtitle+" - "+scrapeddescription , scrapedurl , scrapedthumbnail , scrapedplot )

    # Label (top-right)...
    xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )

    # Disable sorting...
    xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )

    # End of directory...
    xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )
  
