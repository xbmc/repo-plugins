# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para documaniatv.com
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

CHANNELNAME = "documaniatv"

# Esto permite su ejecución en modo emulado
try:
    pluginhandle = int( sys.argv[ 1 ] )
except:
    pluginhandle = ""

logger.info("[documaniatv.py] init")
tecleadoultimo = ""
DEBUG = True
IMAGES_PATH = xbmc.translatePath( os.path.join( os.getcwd(), 'resources' , 'images' , 'documaniatv' ) )


def mainlist(params,url,category):
    logger.info("[documaniatv.py] mainlist")
    
    xbmctools.addnewfolder( CHANNELNAME , "documentalesnuevos" , category , "Documentales Online Nuevos","http://www.documaniatv.com/newvideos.html",os.path.join(IMAGES_PATH, 'nuevos.png'),"")
    xbmctools.addnewfolder( CHANNELNAME , "TipoDocumental"   , category , "Tipo de Documental","",os.path.join(IMAGES_PATH, 'tipo.png'),"")
    xbmctools.addnewfolder( CHANNELNAME , "tagdocumentales"  , category , "Tag de Documentales","http://www.documaniatv.com/index.html",os.path.join(IMAGES_PATH, 'tag.png'),"")
    xbmctools.addnewfolder( CHANNELNAME , "topdocumentales"  , category , "Top Documentales Online","http://www.documaniatv.com/topvideos.html",os.path.join(IMAGES_PATH, 'top.png'),"")
    xbmctools.addnewfolder( CHANNELNAME , "listatipodocumental"     , category , "Documentales Siendo Vistos Ahora","http://www.documaniatv.com/index.html",os.path.join(IMAGES_PATH, 'viendose.png'),"")
    xbmctools.addnewfolder( CHANNELNAME , "documentaldeldia"     , category , "Documental del dia","http://www.documaniatv.com/index.html",os.path.join(IMAGES_PATH, 'deldia.png'),"")
    xbmctools.addnewfolder( CHANNELNAME , "search"           , category , "Buscar",tecleadoultimo,os.path.join(IMAGES_PATH, 'search_icon.png'),"")

    # Label (top-right)...
    xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )
        
    # Disable sorting...
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )

    # End of directory...
    xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

      
##############------------------------------------------------------#################        

def search(params,url,category):
    logger.info("[documaniatv.py] search")
    buscador.listar_busquedas(params,url,category)
    
def searchresults(params,url,category):
    logger.info("[documaniatv.py] search")
            
    buscador.salvar_busquedas(params,url,category)
    
    #convert to HTML
    tecleado = url.replace(" ", "+")
    searchUrl = "http://www.documaniatv.com/search.php?keywords="+tecleado+"&btn=Buscar"
    searchresults2(params,searchUrl,category)



###############---------------------------------------------------#####################

def performsearch(texto):
    logger.info("[documaniatv.py] performsearch")
    url = "http://www.documaniatv.com/search.php?keywords="+texto+"&btn=Buscar"

    # Descarga la página
    data = scrapertools.cachePage(url)

    # Extrae las entradas (carpetas)
    patronvideos = '<li class="video">[^<]+<div class="video_i">[^<]+<a href="([^"]+)">'
    patronvideos += '[^<]+<img src="([^"]+)"  '
    patronvideos += 'alt="([^"]+)"[^>]+><div class="tag".*?</div>.*?'
    patronvideos += '<span class="artist_name">([^<]+)</span>'    
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

def searchresults2(params,url,category):
    logger.info("[documaniatv.py] searchresults")

    # Descarga la página
    data = scrapertools.cachePage(url)
    #logger.info(data)

    # Extrae las entradas (carpetas)
    patronvideos = '<li class="video">[^<]+<div class="video_i">[^<]+<a href="([^"]+)">'
    patronvideos += '[^<]+<img src="([^"]+)"  '
    patronvideos += 'alt="([^"]+)"[^>]+><div class="tag".*?</div>.*?'
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
    logger.info("[documaniatv.py] TipoDocumental")
        
    xbmctools.addnewfolder(CHANNELNAME , "listatipodocumental" , category , "Arte y cine","http://www.documaniatv.com/browse-arte-","","")
    xbmctools.addnewfolder(CHANNELNAME , "listatipodocumental" , category , "Biografia","http://www.documaniatv.com/browse-biografias-","","")
    xbmctools.addnewfolder(CHANNELNAME , "listatipodocumental" , category , "Ciencia y tecnologia","http://www.documaniatv.com/browse-tecnologia-","","")
    xbmctools.addnewfolder(CHANNELNAME , "listatipodocumental" , category , "Deporte","http://www.documaniatv.com/browse-deporte-","","")
    xbmctools.addnewfolder(CHANNELNAME , "listatipodocumental" , category , "en ingles","http://www.documaniatv.com/browse-ingles-","","")
    xbmctools.addnewfolder(CHANNELNAME , "listatipodocumental" , category , "Historia","http://www.documaniatv.com/browse-historia-","","")
    xbmctools.addnewfolder(CHANNELNAME , "listatipodocumental" , category , "Naturaleza","http://www.documaniatv.com/browse-naturaleza-","","")
    xbmctools.addnewfolder(CHANNELNAME , "listatipodocumental" , category , "Politica","http://www.documaniatv.com/browse-politica-","","")
    xbmctools.addnewfolder(CHANNELNAME , "listatipodocumental" , category , "Social","http://www.documaniatv.com/browse-social-","","")
    xbmctools.addnewfolder(CHANNELNAME , "listatipodocumental" , category , "Viajes","http://www.documaniatv.com/browse-viajes-","","")
    

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
        opciones.append("Fecha")
        opciones.append("Vistas")
        opciones.append("Votos")
        dia = xbmcgui.Dialog()
        seleccion = dia.select("Ordenar '"+title+"' por: ", opciones)
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
    logger.info("[documaniatv.py] tagdocumentales")

    xbmctools.addnewfolder(CHANNELNAME , "tagdocumentaleslist" , category , "2gm","http://www.documaniatv.com/tags/2gm/","","")
    xbmctools.addnewfolder(CHANNELNAME , "tagdocumentaleslist" , category , "la2","http://www.documaniatv.com/tags/la2/","","")
    xbmctools.addnewfolder(CHANNELNAME , "tagdocumentaleslist" , category ,"tve","http://www.documaniatv.com/tags/tve/","","")
    xbmctools.addnewfolder(CHANNELNAME , "tagdocumentaleslist" , category , "ciencia","http://www.documaniatv.com/tags/ciencia/","","") 
    xbmctools.addnewfolder(CHANNELNAME , "tagdocumentaleslist" , category , "usa","http://www.documaniatv.com/tags/usa/","","")
    xbmctools.addnewfolder(CHANNELNAME , "tagdocumentaleslist" , category , "ovnis","http://www.documaniatv.com/tags/ovnis/","","")
    xbmctools.addnewfolder(CHANNELNAME , "tagdocumentaleslist" , category , "history channel","http://www.documaniatv.com/tags/history-channel/","","")
    xbmctools.addnewfolder(CHANNELNAME , "tagdocumentaleslist" , category ,"egipto","http://www.documaniatv.com/tags/history-channel/","","")
    xbmctools.addnewfolder(CHANNELNAME , "tagdocumentaleslist" , category , "national geographic","http://www.documaniatv.com/tags/national-geographic/","","") 
    xbmctools.addnewfolder(CHANNELNAME , "tagdocumentaleslist" , category , "discovery channel","http://www.documaniatv.com/tags/discovery-channel/","","")
    xbmctools.addnewfolder(CHANNELNAME , "tagdocumentaleslist" , category , "bbc","http://www.documaniatv.com/tags/bbc/","","")
    xbmctools.addnewfolder(CHANNELNAME , "tagdocumentaleslist" , category , "politica","http://www.documaniatv.com/tags/politica/","","")
    xbmctools.addnewfolder(CHANNELNAME , "tagdocumentaleslist" , category ,"historia","http://www.documaniatv.com/tags/historia/","","")
    xbmctools.addnewfolder(CHANNELNAME , "tagdocumentaleslist" , category , "biografias","http://www.documaniatv.com/tags/biografias/","","") 
    xbmctools.addnewfolder(CHANNELNAME , "tagdocumentaleslist" , category , "guerra mundial","http://www.documaniatv.com/tags/guerra-mundial/","","")
    xbmctools.addnewfolder(CHANNELNAME , "tagdocumentaleslist" , category , "cuatro","http://www.documaniatv.com/tags/cuatro/","","")
    xbmctools.addnewfolder(CHANNELNAME , "tagdocumentaleslist" , category , "españa","http://www.documaniatv.com/tags/espana/","","")
    xbmctools.addnewfolder(CHANNELNAME , "tagdocumentaleslist" , category ,"social","http://www.documaniatv.com/tags/social/","","")
    xbmctools.addnewfolder(CHANNELNAME , "tagdocumentaleslist" , category , "noche tematica","http://www.documaniatv.com/tags/noche-tematica/","","") 
    xbmctools.addnewfolder(CHANNELNAME , "tagdocumentaleslist" , category , "redes","http://www.documaniatv.com/tags/redes/","","")
    xbmctools.addnewfolder(CHANNELNAME , "tagdocumentaleslist" , category , "GUERRA","http://www.documaniatv.com/tags/guerra/","","")
    xbmctools.addnewfolder(CHANNELNAME , "tagdocumentaleslist" , category , "tecnologia","http://www.documaniatv.com/tags/tecnologia/","","")
    xbmctools.addnewfolder(CHANNELNAME , "tagdocumentaleslist" , category ,"viaje","http://www.documaniatv.com/tags/viajes","","")
    xbmctools.addnewfolder(CHANNELNAME , "tagdocumentaleslist" , category , "naturaleza","http://www.documaniatv.com/tags/naturaleza/","","") 
    xbmctools.addnewfolder(CHANNELNAME , "tagdocumentaleslist" , category , "nazis","http://www.documaniatv.com/tags/nazis/","","")


        # Label (top-right)...
    xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )

    # Disable sorting...
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )

    # End of directory...
    xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

       
############---------------------------------------------------------###########


def listatipodocumental(params,url,category):
    logger.info("[documaniatv.py] listatipodocumental")

    # busca tipo de listado por : FECHA | VISTAS | RATING #
    url = listarpor(params,url,category) 
    if len(url)==0 :
       return  
    # Descarga la página
    data = scrapertools.cachePage(url)
    
    # Extrae las entradas (carpetas)
            

    if url == "http://www.documaniatv.com/index.html":
        patronvideos = '<li class="item">[^<]+<a href="([^"]+)"><img src="([^"]+)" alt="([^"]+)" class="imag".*?/></a>'
        cat = "viendose"
    else:  
        patronvideos  = '<li class="video">[^<]+<div class="video_i">[^<]+<a href="([^"]+)"'
        patronvideos += '>[^<]+<img src="([^"]+)"  alt="([^"]+)".*?<span class="artist_name">([^<]+)</span>'
        cat = "tipo"
            
            
    
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)
    #logger.info("matches = "+matches[0])
    scrapedplot = ""
    for match in matches:
        # Titulo
        scrapedtitle = acentos(match[2])

        # URL
        scrapedurl = match[0]
        
        # Thumbnail
        scrapedthumbnail = match[1]
        
        # procesa el resto
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
 #  -------------------------------------------
 #         Busqueda de la siguiente pagina
        
        if cat == "tipo":
               patron_pagina_sgte = '</span><a href="([^"]+)"'
               paginasiguientes(patron_pagina_sgte,data,category,cat)

    # Label (top-right)...
    xbmcplugin.setContent(int( sys.argv[ 1 ] ),"movies")
    xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
    xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

##############---------------------------------------------------------##############

def documentalesnuevos(params,url,category):
    url1=url
    # Abre el diálogo de selección
    opciones = []
    opciones.append("Todo el tiempo")
    opciones.append("Hoy")
    opciones.append("Ayer")
    opciones.append("Este Mes")
    dia = xbmcgui.Dialog()
    seleccion = dia.select("Elige uno", opciones)
    logger.info("seleccion=%d" % seleccion)        
    if seleccion==-1:
       return
    if seleccion==0:
        url1 = "http://www.documaniatv.com/newvideos.html"
    elif seleccion==1:
        url1 = "http://www.documaniatv.com/newvideos.html?d=today"
    elif seleccion==2:
        url1 = "http://www.documaniatv.com/newvideos.html?d=yesterday"
    elif seleccion==3:
        url1 = "http://www.documaniatv.com/newvideos.html?d=month"
    documentalesnuevoslist(params,url1,category)

#############----------------------------------------########################


def documentalesnuevoslist(params,url,category):
    logger.info("[documaniatv.py] DocumentalesNuevos")

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

    for match in matches:
        scrapedtitle = acentos(match[2])+" - " + match[3]+" - " + match[4] 
        scrapedurl = match[0]
        scrapedthumbnail = match[1]
        imagen = ""
        scrapedplot = match[3]
        tipo = match[3]

        # Añade al listado de XBMC
        xbmctools.addnewfolder( CHANNELNAME , "detail" , category , scrapedtitle ,scrapedurl , scrapedthumbnail , scrapedplot )
        

    # Busca enlaces de paginas siguientes...
    cat = "nuevo"
    patronvideo = patronvideos
    paginasiguientes(patronvideo,data,category,cat)     

    # Label (top-right)...
    xbmcplugin.setContent(int( sys.argv[ 1 ] ),"movies")
    xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
    xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

##########---------------------------------------------------------------#############

def documentaldeldia(params,url,category):
#    list(params,url,category,patronvideos)
    logger.info("[documaniatv.py] Documentaldeldia")
               
    # Descarga la página
    data = scrapertools.cachePage(url)
    #logger.info(data)
        
    patronvideos = 'Documental del dia:<[^>]+>.*?<a href="([^"]+)">([^<]+)</a>'
    matches =  re.compile(patronvideos,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)
    for match in matches:
        scrapedtitle = acentos(match[1])
        scrapedurl = match[0]
        scrapedthumbnail = ""
        scrapedplot = ""
        xbmctools.addnewfolder( CHANNELNAME , "detail" , category , scrapedtitle , scrapedurl , scrapedthumbnail , scrapedplot ) 

    xbmcplugin.setContent(int( sys.argv[ 1 ] ),"movies")
    xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
    xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True ) 

################---------------------------------------------------------###########


def tagdocumentaleslist(params,url,category):
    logger.info("[documaniatv.py] tagdocumentaleslist")

    # Descarga la página
    data = scrapertools.cachePage(url)
    #logger.info(data)



    # Extrae el listado de documentales del tag
    
    patronvideos  = '<li class="video">[^<]+<div class="video_i">[^<]+<a href="([^"]+)"'
    patronvideos += '>[^<]+<img src="([^"]+)"  alt="([^"]+)".*?<span class="artist_name">([^<]+)</span>'
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
    xbmcplugin.setContent(int( sys.argv[ 1 ] ),"movies")
    xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
    xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

#############----------------------------------------------------------#############



############---------------------------------------------------#######################

def topdocumentales(params,url,category):
    url2=url
    # Abre el diálogo de selección
    opciones = []
    opciones.append("Todo el tiempo")
    opciones.append("Ultimos 7 dias")
    opciones.append("Politica")
    opciones.append("Naturaleza")
    opciones.append("Historia")
    opciones.append("Deporte")
    opciones.append("Biografias")
    opciones.append("en ingles")
    opciones.append("Ciencia y tecnologia")
    opciones.append("Social")
    opciones.append("Viajes")
    opciones.append("Arte y cine")
    dia = xbmcgui.Dialog()
    seleccion = dia.select("Elige Listar Top por :", opciones)
    logger.info("seleccion=%d" % seleccion) 
    if seleccion==-1:
       return
    if seleccion==0:
       url2 = "http://www.documaniatv.com/topvideos.html"
    elif seleccion==1:
       url2 = "http://www.documaniatv.com/topvideos.html?do=recent"
    elif seleccion==2:
       url2 = "http://www.documaniatv.com/topvideos.html?c=politica"  
    elif seleccion==3:
       url2 = "http://www.documaniatv.com/topvideos.html?c=naturaleza"
    elif seleccion==4:
       url2 = "http://www.documaniatv.com/topvideos.html?c=historia" 
    elif seleccion==5: 
       url2 = "http://www.documaniatv.com/topvideos.html?c=deporte"
    elif seleccion==6: 
       url2 = "http://www.documaniatv.com/topvideos.html?c=biografias"
    elif seleccion==7:
       url2 = "http://www.documaniatv.com/topvideos.html?c=ingles"
    elif seleccion==8:
       url2 = "http://www.documaniatv.com/topvideos.html?c=tecnologia"
    elif seleccion==9:
       url2 = "http://www.documaniatv.com/topvideos.html?c=social"
    elif seleccion==10:
       url2 = "http://www.documaniatv.com/topvideos.html?c=viajes"
    elif seleccion==11:
       url2 = "http://www.documaniatv.com/topvideos.html?c=arte" 
 
    toplist(params,url2,category)
############----------------------------------------------####################

def toplist(params,url,category):
    logger.info("[documaniatv.py] toplist")

    # Descarga la página
    data = scrapertools.cachePage(url)
    #logger.info(data)


    # Extrae las entradas (carpetas)
    logger.info("[documaniatv.py] toplist "+url) 
    if url== "http://www.documaniatv.com/topvideos.html?do=recent":
            
        patronvideos = '<tr>[^<]+<td[^>]+>([^<]+)</td>[^<]+<td'
        patronvideos += '[^>]+><a href="([^"]+)">'
        patronvideos += '<img src="([^"]+)" alt=[^>]+>'
        patronvideos += '</a></td>[^<]+<td[^>]+>([^<]+)</td>[^<]+<td[^>]+>'
        patronvideos += '<a href="[^"]+">([^<]+)</a>'
        patronvideos += '</td>[^<]+<td[^>]+>([^<]+)</td>'

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
        scrapedplot = match[4]+" - " + "Vistas : "+match[5]+" veces"

        xbmctools.addthumbnailfolder( CHANNELNAME , match[0]+") "+scrapedtitle+" - "+scrapedplot, scrapedurl , scrapedthumbnail, "detail" )

    # Label (top-right)...
    xbmcplugin.setContent(int( sys.argv[ 1 ] ),"movies")
    xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
    xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

#############----------------------------------------------------------#############

def detail(params,url,category):
    logger.info("[documaniatv.py] detail")

    title = urllib.unquote_plus( params.get("title") )
    thumbnail = urllib.unquote_plus( params.get("thumbnail") )
    thumnbail = thumbnail
    #logger.info("[prueba.py] title="+title)
    #logger.info("[prueba.py] thumbnail="+thumbnail)
    patrondescrip = '<h3>Descripci[^<]+</h3>(.*?)<br><br>'
    # Descarga la página
    data = scrapertools.cachePage(url)
    descripcion = ""
    plot = ""
    matches = re.compile(patrondescrip,re.DOTALL).findall(data)
    if len(matches)>0:
        descripcion = matches[0]
        descripcion = descripcion.replace("&nbsp;","")
        descripcion = descripcion.replace("<br/>","")
        descripcion = descripcion.replace("\r","")
        descripcion = descripcion.replace("\n"," ")
        descripcion = descripcion.replace("\t"," ")
        descripcion = re.sub("<[^>]+>"," ",descripcion)
        descripcion = acentos(descripcion)
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
        url1 = video[1].replace("&amp;","&")
        logger.info("url   ="+url)
        if  url.endswith(".jpg"):break
        server = video[2]
        if server=="Megavideo" or "Veoh":
            xbmctools.addnewvideo( CHANNELNAME , "play" , category , server , title.strip().replace("(Megavideo)","").replace("  "," ") + " - " + videotitle , url1 , thumbnail , plot )
        else:
            xbmctools.addnewvideo( CHANNELNAME , "play" , category , server , title.strip().replace(server,"").replace("  "," ") + " - " + videotitle , url1 , thumbnail , plot )

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
        extraevideos(patronvideos,data,category,title+" - [Video en google]",thumbnail,plot,servidor)
        # --------------------------------------- 

        #  --- Extrae los videos de http://n59.stagevu.com  ----
        patronvideos = '"http://.*?.stagevu.com/v/.*?/(.*?).avi"'
        servidor = "Stagevu"
        extraevideos(patronvideos,data,category,title,thumbnail,plot,servidor)

        # --Muestra Una opcion mas para videos documentales relacionados con el tema--
        print "esta es la url :%s" %url
        try:
            patron = "http://www.documaniatv.com.*?\_(.*?)\.html"
            matches = re.compile(patron,re.DOTALL).findall(url)
            url = "http://www.documaniatv.com/ajax.php?p=detail&do=show_more_best&vid="+matches[0]
            titulo = "Ver Videos Relacionados - MEJOR EN LA CATEGORIA"
            xbmctools.addnewfolder( CHANNELNAME , "Relacionados" , category , titulo , url , "" , "Lísta algunos Documentales relacionados con el mismo tema" )
        
            titulo = "Ver Videos Relacionados - MISMO TEMA"
            url = "http://www.documaniatv.com/ajax.php?p=detail&do=show_more_artist&vid="+matches[0]
            xbmctools.addnewfolder( CHANNELNAME , "Relacionados" , category , titulo , url , "" , "Lísta algunos Documentales relacionados con el mismo tema" )
        except:
            pass

    # Label (top-right)...
    xbmcplugin.setContent(int( sys.argv[ 1 ] ),"movies")
    xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
    xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )
    xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

#############----------------------------------------------------------#############

def extraevideos(patronvideos,data,category,title,thumbnail,plot,servidor):
    logger.info("patron="+patronvideos)
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)        

    if len(matches)>0:
        
        # Añade al listado de XBMC
        if servidor == "Directo":
            xbmctools.addnewvideo( CHANNELNAME , "play" , category , "Directo" , title, matches[0] , thumbnail , plot )

        elif servidor == "Veoh":
            veohurl = servertools.findurl(matches[0],"veoh")
            logger.info(" veohurl = " +veohurl)

            if len(veohurl)>0:
                if  veohurl=="http://./default.asp":
                    advertencia = xbmcgui.Dialog()
                    resultado = advertencia.ok('El Video Documental' , title , 'no existe en Veoh','visite la pagina www.documaniatv.com para reportarlo' )
                    return
                logger.info(" newmatches = "+veohurl)
                xbmctools.addnewvideo( CHANNELNAME , "play" , category , "Directo" , title, veohurl , thumbnail , plot )
            else:
                 advertencia = xbmcgui.Dialog()
                 resultado = advertencia.ok('El Video Documental' , title , 'no existe en Veoh')
                 return 
    
        elif servidor == "Google":
            url = "http://www.flashvideodownloader.org/download.php?u=http://video.google.com/videoplay?docid="+matches[0]
            logger.info(" Url = "+url)
            data = scrapertools.cachePage(url)
            newpatron = '</script>.*?<a href="(.*?)" title="Click to Download">'
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
    logger.info("[documaniatv.py] play")

    title = unicode( xbmc.getInfoLabel( "ListItem.Title" ), "utf-8" )
    title = unicode( xbmc.getInfoLabel( "ListItem.Title" ), "utf-8" )
    try:
        thumbnail = urllib.unquote_plus( params.get("thumbnail") )
    except:
        thumbnail = xbmc.getInfoImage( "ListItem.Thumb" )
    plot = urllib.unquote_plus( params.get("plot") )
    plot = urllib.unquote_plus( params.get("plot") )

    try:
        plot = unicode( xbmc.getInfoLabel( "ListItem.Plot" ), "utf-8" )
    except:
        plot = xbmc.getInfoLabel( "ListItem.Plot" )

    server = params["server"]
    logger.info("[documaniatv.py] thumbnail="+thumbnail)
    logger.info("[documaniatv.py] server="+server)
    
    xbmctools.playvideo(CHANNELNAME,server,url,category,title,thumbnail,plot)


#############----------------------------------------------------------#############

def paginasiguientes(patronvideos,data,category,cat):

    # ------------------------------------------------------
    # Extrae la página siguiente
    # ------------------------------------------------------
    patron    = '</span><a href="([^"]+)"' 
    matches   = re.compile(patron,re.DOTALL).findall(data)

    for match in matches:
        scrapedtitle = "Pagina siguiente"
        scrapedurl = "http://www.documaniatv.com/" + match
        scrapedthumbnail = os.path.join(IMAGES_PATH, 'next.png')
        scrapeddescription = ""

        if cat == 'tipo':   
            xbmctools.addthumbnailfolder( CHANNELNAME , scrapedtitle , scrapedurl , scrapedthumbnail, "listatipodocumental" )
        elif cat == 'nuevo':
            xbmctools.addthumbnailfolder( CHANNELNAME , scrapedtitle , scrapedurl , scrapedthumbnail, "documentalesnuevoslist" )
        elif cat == 'tag':
            xbmctools.addthumbnailfolder( CHANNELNAME , scrapedtitle , "http://www.documaniatv.com"+match , scrapedthumbnail, "tagdocumentaleslist" )
        elif cat == 'busca':
            xbmctools.addthumbnailfolder( CHANNELNAME , scrapedtitle , scrapedurl , scrapedthumbnail, "searchresults" )

    # Label (top-right)...
    xbmcplugin.setContent(int( sys.argv[ 1 ] ),"movies")
    xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
    xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )
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
        scrapedtitle = acentos(match[2])
        scrapedurl = match[0]
        scrapedthumbnail = match[1]
        scrapeddescription = match[3]
        scrapedplot = ""

        xbmctools.addnewfolder( CHANNELNAME , "detail" , category , scrapedtitle+" - "+scrapeddescription , scrapedurl , scrapedthumbnail , scrapedplot )

    xbmcplugin.setContent(int( sys.argv[ 1 ] ),"movies")
    xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
    xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )
    xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )
 
def Relacionados(params,url,category): 
    
    data = scrapertools.cachePage(url)
    print data
    verRelacionados(params,data,category)
