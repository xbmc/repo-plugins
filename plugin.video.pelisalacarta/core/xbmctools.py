# -*- coding: utf-8 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# XBMC Tools
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
# 2010/02/13 Añadida funcionalidad de Biblioteca - JUR
#------------------------------------------------------------

import urllib
import xbmc
import xbmcgui
import xbmcplugin
import sys
import os

from servers import servertools
from core import config
from core import logger

# Esto permite su ejecución en modo emulado
try:
    pluginhandle = int( sys.argv[ 1 ] )
except:
    pluginhandle = ""

LIBRARY_CATEGORIES = ['Series'] #Valor usuarios finales

#LIBRARY_CATEGORIES = ['Cine','Series'] #Valor developers (descomentar para activar)
# Para test de programadores. Se pueden añadir aquellos canales de cine que 
#   queramos que tengan opción de añadir a la biblioteca.
#   (SÓLO VERSIONES XBMC COMPILADAS CON BUGFIX INCLUIDO)

DEBUG = True

# TODO: (3.2) Esto es un lío, hay que unificar
def addnewfolder( canal , accion , category , title , url , thumbnail , plot , Serie="",totalItems=0,fanart="",context=0):
    ok = addnewfolderextra( canal , accion , category , title , url , thumbnail , plot , "" ,Serie,totalItems,fanart,context)
    return ok

def addnewfolderextra( canal , accion , category , title , url , thumbnail , plot , extradata ,Serie="",totalItems=0,fanart="",context=0):
    contextCommands = []
    ok = False
    #logger.info("pluginhandle=%d" % pluginhandle)
    if DEBUG:
        try:
            logger.info('[xbmctools.py] addnewfolder( "'+canal+'" , "'+accion+'" , "'+category+'" , "'+title+'" , "' + url + '" , "'+thumbnail+'" , "'+plot+'")" , "'+Serie+'")"')
        except:
            logger.info('[xbmctools.py] addnewfolder(<unicode>)')
    listitem = xbmcgui.ListItem( title, iconImage="DefaultFolder.png", thumbnailImage=thumbnail )
    if fanart!="":
        listitem.setProperty('fanart_image',fanart) 
    listitem.setInfo( "video", { "Title" : title, "Plot" : plot, "Studio" : canal } )
    #Realzamos un quote sencillo para evitar problemas con títulos unicode
#    title = title.replace("&","%26").replace("+","%2B").replace("%","%25")
    try:
        title = title.encode ("utf-8") #This only aplies to unicode strings. The rest stay as they are.
    except:
        pass
    itemurl = '%s?channel=%s&action=%s&category=%s&title=%s&url=%s&thumbnail=%s&plot=%s&extradata=%s&Serie=%s' % ( sys.argv[ 0 ] , canal , accion , urllib.quote_plus( category ) , urllib.quote_plus(title) , urllib.quote_plus( url ) , urllib.quote_plus( thumbnail ) , urllib.quote_plus( plot ) , urllib.quote_plus( extradata ) , Serie)

    if Serie != "": #Añadimos opción contextual para Añadir la serie completa a la biblioteca
        addSerieCommand = "XBMC.RunPlugin(%s?channel=%s&action=addlist2Library&category=%s&title=%s&url=%s&extradata=%s&Serie=%s)" % ( sys.argv[ 0 ] , canal , urllib.quote_plus( category ) , urllib.quote_plus( title ) , urllib.quote_plus( url ) , urllib.quote_plus( extradata ) , Serie)
        contextCommands.append(("Añadir Serie a Biblioteca",addSerieCommand))
        
    if context == 1 and accion != "por_teclado":
        DeleteCommand = "XBMC.RunPlugin(%s?channel=buscador&action=borrar_busqueda&title=%s&url=%s)" % ( sys.argv[ 0 ]  ,  urllib.quote_plus( title ) , urllib.quote_plus( url ) )
        contextCommands.append((config.get_localized_string( 30300 ),DeleteCommand))
        
    if len (contextCommands) > 0:
        listitem.addContextMenuItems ( contextCommands, replaceItems=False)
    if totalItems == 0:
        ok = xbmcplugin.addDirectoryItem( handle = pluginhandle, url = itemurl , listitem=listitem, isFolder=True)
    else:
        ok = xbmcplugin.addDirectoryItem( handle = pluginhandle, url = itemurl , listitem=listitem, isFolder=True, totalItems=totalItems)
    return ok

def addnewvideo( canal , accion , category , server , title , url , thumbnail, plot ,Serie="",duration="",fanart="",IsPlayable='false',context = 0, subtitle="", totalItems = 0):
    contextCommands = []
    ok = False
    if DEBUG:
        try:
            logger.info('[xbmctools.py] addnewvideo( "'+canal+'" , "'+accion+'" , "'+category+'" , "'+server+'" , "'+title+'" , "' + url + '" , "'+thumbnail+'" , "'+plot+'")" , "'+Serie+'")"')
        except:
            logger.info('[xbmctools.py] addnewvideo(<unicode>)')
    listitem = xbmcgui.ListItem( title, iconImage="DefaultVideo.png", thumbnailImage=thumbnail )
    if fanart!="":
        listitem.setProperty('fanart_image',fanart) 
    listitem.setInfo( "video", { "Title" : title, "Plot" : plot, "Duration" : duration, "Studio" : canal } )
    if IsPlayable == 'true': #Esta opcion es para poder utilizar el xbmcplugin.setResolvedUrl()
        listitem.setProperty('IsPlayable', 'true')
    #listitem.setProperty('fanart_image',os.path.join(IMAGES_PATH, "cinetube.png"))
    if context == 1: #El uno añade al menu contextual la opcion de guardar en megalive un canal a favoritos
        addItemCommand = "XBMC.RunPlugin(%s?channel=%s&action=%s&category=%s&title=%s&url=%s&thumbnail=%s&plot=%s&server=%s&Serie=%s)" % ( sys.argv[ 0 ] , canal , "saveChannelFavorites" , urllib.quote_plus( category ) , urllib.quote_plus( title ) , urllib.quote_plus( url ) , urllib.quote_plus( thumbnail ) , urllib.quote_plus( plot ) , server , Serie)
        contextCommands.append((config.get_localized_string(30301),addItemCommand))
        
    if context == 2:#El dos añade al menu contextual la opciones de eliminar y/o renombrar un canal en favoritos 
        addItemCommand = "XBMC.RunPlugin(%s?channel=%s&action=%s&category=%s&title=%s&url=%s&thumbnail=%s&plot=%s&server=%s&Serie=%s)" % ( sys.argv[ 0 ] , canal , "deleteSavedChannel" , urllib.quote_plus( category ) , urllib.quote_plus( title ) , urllib.quote_plus( url ) , urllib.quote_plus( thumbnail ) , urllib.quote_plus( plot ) , server , Serie)
        contextCommands.append((config.get_localized_string(30302),addItemCommand))
        addItemCommand = "XBMC.RunPlugin(%s?channel=%s&action=%s&category=%s&title=%s&url=%s&thumbnail=%s&plot=%s&server=%s&Serie=%s)" % ( sys.argv[ 0 ] , canal , "renameChannelTitle" , urllib.quote_plus( category ) , urllib.quote_plus( title ) , urllib.quote_plus( url ) , urllib.quote_plus( thumbnail ) , urllib.quote_plus( plot ) , server , Serie)
        contextCommands.append((config.get_localized_string(30303),addItemCommand))    
    if len (contextCommands) > 0:
        listitem.addContextMenuItems ( contextCommands, replaceItems=False)
    try:
        title = title.encode ("utf-8")     #This only aplies to unicode strings. The rest stay as they are.
        plot  = plot.encode ("utf-8")
    except:
        pass
    
    itemurl = '%s?channel=%s&action=%s&category=%s&title=%s&url=%s&thumbnail=%s&plot=%s&server=%s&Serie=%s&subtitle=%s' % ( sys.argv[ 0 ] , canal , accion , urllib.quote_plus( category ) , urllib.quote_plus( title ) , urllib.quote_plus( url ) , urllib.quote_plus( thumbnail ) , urllib.quote_plus( plot ) , server , Serie , urllib.quote_plus(subtitle))
    #logger.info("[xbmctools.py] itemurl=%s" % itemurl)
    if totalItems == 0:
        ok = xbmcplugin.addDirectoryItem( handle = pluginhandle, url=itemurl, listitem=listitem, isFolder=False)
    else:
        ok = xbmcplugin.addDirectoryItem( handle = pluginhandle, url=itemurl, listitem=listitem, isFolder=False, totalItems=totalItems)
    return ok

def addthumbnailfolder( canal , scrapedtitle , scrapedurl , scrapedthumbnail , accion ):
    logger.info('[xbmctools.py] addthumbnailfolder( "'+scrapedtitle+'" , "' + scrapedurl + '" , "'+scrapedthumbnail+'" , "'+accion+'")"')
    listitem = xbmcgui.ListItem( scrapedtitle, iconImage="DefaultFolder.png", thumbnailImage=scrapedthumbnail )
    itemurl = '%s?channel=%s&action=%s&category=%s&url=%s&title=%s&thumbnail=%s' % ( sys.argv[ 0 ] , canal , accion , urllib.quote_plus( scrapedtitle ) , urllib.quote_plus( scrapedurl ) , urllib.quote_plus( scrapedtitle ) , urllib.quote_plus( scrapedthumbnail ) )
    xbmcplugin.addDirectoryItem( handle = pluginhandle, url = itemurl , listitem=listitem, isFolder=True)

def addfolder( canal , nombre , url , accion ):
    logger.info('[xbmctools.py] addfolder( "'+nombre+'" , "' + url + '" , "'+accion+'")"')
    listitem = xbmcgui.ListItem( nombre , iconImage="DefaultFolder.png")
    itemurl = '%s?channel=%s&action=%s&category=%s&url=%s' % ( sys.argv[ 0 ] , canal , accion , urllib.quote_plus(nombre) , urllib.quote_plus(url) )
    xbmcplugin.addDirectoryItem( handle = pluginhandle, url = itemurl , listitem=listitem, isFolder=True)

def addvideo( canal , nombre , url , category , server , Serie=""):
    logger.info('[xbmctools.py] addvideo( "'+nombre+'" , "' + url + '" , "'+server+ '" , "'+Serie+'")"')
    listitem = xbmcgui.ListItem( nombre, iconImage="DefaultVideo.png" )
    listitem.setInfo( "video", { "Title" : nombre, "Plot" : nombre } )
    itemurl = '%s?channel=%s&action=play&category=%s&url=%s&server=%s&title=%s&Serie=%s' % ( sys.argv[ 0 ] , canal , category , urllib.quote_plus(url) , server , urllib.quote_plus( nombre ) , Serie)
    xbmcplugin.addDirectoryItem( handle=pluginhandle, url=itemurl, listitem=listitem, isFolder=False)

def playvideo(canal,server,url,category,title,thumbnail,plot,strmfile=False,Serie="",subtitle=""):
    playvideoEx(canal,server,url,category,title,thumbnail,plot,False,False,False,strmfile,Serie,subtitle)

def playvideo2(canal,server,url,category,title,thumbnail,plot):
    playvideoEx(canal,server,url,category,title,thumbnail,plot,True,False,False)

def playvideo3(canal,server,url,category,title,thumbnail,plot):
    playvideoEx(canal,server,url,category,title,thumbnail,plot,False,True,False)

def playvideo4(canal,server,url,category,title,thumbnail,plot):
    playvideoEx(canal,server,url,category,title,thumbnail,plot,False,False,True)

def playvideoEx(canal,server,url,category,title,thumbnail,plot,desdefavoritos,desdedescargados,desderrordescargas,strmfile=False,Serie="",subtitle=""):

    try:
        server = server.lower()
    except:
        server = ""

    logger.info("[xbmctools.py] playvideo")
    logger.info("[xbmctools.py] playvideo canal="+canal)
    logger.info("[xbmctools.py] playvideo server="+server)
    logger.info("[xbmctools.py] playvideo url="+url)
    logger.info("[xbmctools.py] playvideo category="+category)
    logger.info("[xbmctools.py] playvideo serie="+Serie)
    logger.info("[xbmctools.py] playvideo subtitle="+config.get_setting("subtitulo")+" "+subtitle)
    
    # Abre el diálogo de selección
    opciones = []
    default_action = config.get_setting("default_action")
    logger.info("default_action="+default_action)
    # Los vídeos de Megavídeo sólo se pueden ver en calidad alta con cuenta premium
    # Los vídeos de Megaupload sólo se pueden ver con cuenta premium, en otro caso pide captcha
    if (server=="megavideo") and config.get_setting("megavideopremium")=="true":
        opcion = config.get_localized_string(30150)+" ["+server+"]"
        logger.info(opcion)
        opciones.append(opcion) # "Ver en calidad alta"
        # Si la accion por defecto es "Ver en calidad alta", la seleccion se hace ya
        if default_action=="2":
            seleccion = len(opciones)-1
    elif (server=="megaupload"):

        opcion = config.get_localized_string(30150)+" ["+server+"]"
        logger.info(opcion)
        opciones.append(opcion) # "Ver en calidad alta"
        # Si la accion por defecto es "Ver en calidad alta", la seleccion se hace ya
        if default_action=="2":
            seleccion = len(opciones)-1

    # Los vídeos de Megavídeo o Megaupload se pueden ver en calidad baja sin cuenta premium, aunque con el límite
    if (server=="megavideo" or server=="megaupload"):
        opcion = config.get_localized_string(30152)+" [megavideo]"
        logger.info(opcion)
        opciones.append(opcion) # "Ver en calidad baja"
        # Si la accion por defecto es "Ver en calidad baja", la seleccion se hace ya
        if default_action=="1":
            seleccion = len(opciones)-1
    else:
        opcion = config.get_localized_string(30151)+" ["+server+"]"
        logger.info(opcion)
        opciones.append(opcion) # "Ver en calidad normal"
        # Si la accion por defecto es "Ver en calidad baja", la seleccion se hace ya
        if default_action<>"0":  #Si hay alguna calidad elegida (alta o baja) seleccionarmos esta para los no megavideo
            seleccion = len(opciones)-1

    if config.get_setting("download.enabled")=="true":
        opcion = config.get_localized_string(30153)
        logger.info(opcion)
        opciones.append(opcion) # "Descargar"

    if desdefavoritos: 
        opciones.append(config.get_localized_string(30154)) # "Quitar de favoritos"
    else:
        opciones.append(config.get_localized_string(30155)) # "Añadir a favoritos"

    if config.get_setting("download.enabled")=="true":
        if desdedescargados:
            opciones.append(config.get_localized_string(30156)) # "Quitar de lista de descargas"
        else:
            opciones.append(config.get_localized_string(30157)) # "Añadir a lista de descargas"

    opciones.append(config.get_localized_string(30158)) # "Enviar a JDownloader"
    if default_action=="3":
        seleccion = len(opciones)-1

    if config.get_setting("download.enabled")=="true":
        if desderrordescargas:
            opciones.append(config.get_localized_string(30159)) # "Borrar descarga definitivamente"
            opciones.append(config.get_localized_string(30160)) # "Pasar de nuevo a lista de descargas"

    if not strmfile:
        if category in LIBRARY_CATEGORIES:
            opciones.append(config.get_localized_string(30161)) # "Añadir a Biblioteca"

    # Busqueda de trailers en youtube    
    if not canal in ["Trailer","ecarteleratrailers"]:
        opciones.append(config.get_localized_string(30162)) # "Buscar Trailer"

    # Si la accion por defecto es "Preguntar", pregunta
    if default_action=="0":
        dia = xbmcgui.Dialog()
        seleccion = dia.select(config.get_localized_string(30163), opciones) # "Elige una opción"
        #dia.close()
    logger.info("seleccion=%d" % seleccion)
    logger.info("seleccion=%s" % opciones[seleccion])

    # No ha elegido nada, lo más probable porque haya dado al ESC 
    if seleccion==-1:
        if strmfile:  #Para evitar el error "Uno o más elementos fallaron" al cancelar la selección desde fichero strm
            listitem = xbmcgui.ListItem( title, iconImage="DefaultVideo.png", thumbnailImage=thumbnail)
            xbmcplugin.setResolvedUrl(int(sys.argv[ 1 ]),False,listitem)    # JUR Added
        if config.get_setting("subtitulo") == "true":
            config.set_setting("subtitulo", "false")
        return

    if opciones[seleccion]==config.get_localized_string(30158): # "Enviar a JDownloader"
        if server=="Megaupload":
            d = {"web": "http://www.megaupload.com/?d=" + url}
        else:
            d = {"web": "http://www.megavideo.com/?v=" + url}
        
        from core import scrapertools
        data = scrapertools.cachePage(config.get_setting("jdownloader")+"/action/add/links/grabber0/start1/"+urllib.urlencode(d)+ " " +thumbnail)
        return

    # Ver en calidad alta
    if opciones[seleccion].startswith(config.get_localized_string(30150)): # "Ver en calidad alta"
        if server=="megaupload":
            if canal == 'asiateam':
                mediaurl = servertools.getmegauploadhigh(url, password='www.Asia-Team.net')
            else:
                mediaurl = servertools.getmegauploadhigh(url)
        else:
            mediaurl = servertools.getmegavideohigh(url)
    
    # Ver (calidad baja megavideo o resto servidores)
    elif opciones[seleccion].startswith(config.get_localized_string(30151)) or opciones[seleccion].startswith(config.get_localized_string(30152)): # Ver en calidad (normal o baja)
        if server=="megavideo" or server=="megaupload":
            # Advertencia límite 72 minutos megavideo
            if config.get_setting("megavideopremium")=="false":
                advertencia = xbmcgui.Dialog()
                resultado = advertencia.ok(config.get_localized_string(30052) , config.get_localized_string(30053) , config.get_localized_string(30054))            
            if server == "megavideo":
                if canal == 'asiateam':
                    mediaurl = servertools.getmegavideolow(url, password='www.Asia-Team.net')
                else:
                    mediaurl = servertools.getmegavideolow(url)
            else:
                if canal == 'asiateam':
                    mediaurl = servertools.getmegauploadlow(url, password='www.Asia-Team.net')
                else:
                    mediaurl = servertools.getmegauploadlow(url)
        else:
            mediaurl = servertools.findurl(url,server)

    # Descargar
    elif opciones[seleccion]==config.get_localized_string(30153): # "Descargar"
        if server=="megaupload":
            if canal == 'asiateam':
                mediaurl = servertools.getmegauploadhigh(url, password='www.Asia-Team.net')
            else:
                mediaurl = servertools.getmegauploadhigh(url)
        elif server=="megavideo":
            if config.get_setting("megavideopremium")=="false":
                if canal == 'asiateam':
                    mediaurl = servertools.getmegavideolow(url, password='www.Asia-Team.net')
                else:
                    mediaurl = servertools.getmegavideolow(url)
            else:
                mediaurl = servertools.getmegavideohigh(url)
        else:
            mediaurl = servertools.findurl(url,server)

        from core import downloadtools
        keyboard = xbmc.Keyboard(downloadtools.limpia_nombre_excepto_1(title))
        keyboard.doModal()
        if (keyboard.isConfirmed()):
            title = keyboard.getText()
            downloadtools.downloadtitle(mediaurl,title)
        return

    elif opciones[seleccion]==config.get_localized_string(30154): #"Quitar de favoritos"
        from core import favoritos
        # La categoría es el nombre del fichero en favoritos
        favoritos.deletebookmark(category)
                
        advertencia = xbmcgui.Dialog()
        resultado = advertencia.ok(config.get_localized_string(30102) , title , config.get_localized_string(30105)) # 'Se ha quitado de favoritos'
        
        xbmc.executebuiltin( "Container.Refresh" )
        return

    # TODO: (3.1) Mover a modulo descargadoslist
    elif opciones[seleccion]==config.get_localized_string(30159): #"Borrar descarga definitivamente"
        # La categoría es el nombre del fichero en favoritos
        os.remove(urllib.unquote_plus( category ))
        advertencia = xbmcgui.Dialog()
        resultado = advertencia.ok(config.get_localized_string(30101) , title , config.get_localized_string(30106)) # 'Se ha quitado de la lista'
        return

    # TODO: (3.1) Mover a modulo descargadoslist
    elif opciones[seleccion]==config.get_localized_string(30160): #"Pasar de nuevo a lista de descargas":
        from core import descargadoslist
        # La categoría es el nombre del fichero en favoritos, así que lee el fichero
        titulo,thumbnail,plot,server,url = descargadoslist.readbookmarkfile(urllib.unquote_plus( category ),"")
        # Lo añade a la lista de descargas
        descargadoslist.savebookmark(title,url,thumbnail,server,plot)
        # Y lo borra de la lista de errores
        os.remove(urllib.unquote_plus( category ))
        advertencia = xbmcgui.Dialog()
        resultado = advertencia.ok(config.get_localized_string(30101) , title , config.get_localized_string(30107)) # 'Ha pasado de nuevo a la lista de descargas'
        return

    # TODO: (3.1) Mover a modulo favoritos
    elif opciones[seleccion]==config.get_localized_string(30155): #"Añadir a favoritos":
        from core import favoritos
        from core import downloadtools
        keyboard = xbmc.Keyboard(downloadtools.limpia_nombre_excepto_1(title)+" ["+canal+"]")
        keyboard.doModal()
        if keyboard.isConfirmed():
            title = keyboard.getText()
            favoritos.savebookmark(title,url,thumbnail,server,plot)
            advertencia = xbmcgui.Dialog()
            resultado = advertencia.ok(config.get_localized_string(30102) , title , config.get_localized_string(30108)) # 'se ha añadido a favoritos'
        return

    elif opciones[seleccion]==config.get_localized_string(30156): #"Quitar de lista de descargas":
        from core import descargadoslist
        # La categoría es el nombre del fichero en la lista de descargas
        descargadoslist.deletebookmark(category)
                
        advertencia = xbmcgui.Dialog()
        resultado = advertencia.ok(config.get_localized_string(30101) , title , config.get_localized_string(30106)) # 'Se ha quitado de lista de descargas'
        
        xbmc.executebuiltin( "Container.Refresh" )
        return

    # TODO: (3.1) Mover a modulo descargadoslist
    elif opciones[seleccion]==config.get_localized_string(30157): #"Añadir a lista de descargas":
        from core import descargadoslist
        from core import downloadtools
        keyboard = xbmc.Keyboard(downloadtools.limpia_nombre_excepto_1(title))
        keyboard.doModal()
        if keyboard.isConfirmed():
            title = keyboard.getText()
            descargadoslist.savebookmark(title,url,thumbnail,server,plot)
            advertencia = xbmcgui.Dialog()
            resultado = advertencia.ok(config.get_localized_string(30101) , title , config.get_localized_string(30109)) # 'se ha añadido a la lista de descargas'
        return

    elif opciones[seleccion]==config.get_localized_string(30161): #"Añadir a Biblioteca":  # Library
        from core import library
        library.savelibrary(title,url,thumbnail,server,plot,canal=canal,category=category,Serie=Serie)
        return

    elif opciones[seleccion]==config.get_localized_string(30162): #"Buscar Trailer":
        config.set_setting("subtitulo", "false")
        xbmc.executebuiltin("Container.Update(%s?channel=%s&action=%s&category=%s&title=%s&url=%s&thumbnail=%s&plot=%s&server=%s)" % ( sys.argv[ 0 ] , "trailertools" , "buscartrailer" , urllib.quote_plus( category ) , urllib.quote_plus( title ) , urllib.quote_plus( url ) , urllib.quote_plus( thumbnail ) , urllib.quote_plus( "" ) , server ))
        return

    # Si no hay mediaurl es porque el vídeo no está :)
    logger.info("[xbmctools.py] mediaurl="+mediaurl)
    if mediaurl=="":
        if server == "unknown":
            alertUnsopportedServer()
        else:
            alertnodisponibleserver(server)
        return
    

    # Crea un listitem para pasárselo al reproductor

    # Obtención datos de la Biblioteca (solo strms que estén en la biblioteca)
    if strmfile:
        logger.info("[xbmctools.py] 1")
        listitem = getLibraryInfo(mediaurl)
    else:
        logger.info("[xbmctools.py] 2")
        listitem = xbmcgui.ListItem( title, iconImage="DefaultVideo.png", thumbnailImage=thumbnail)
        listitem.setInfo( "video", { "Title": title, "Plot" : plot , "Studio" : canal , "Genre" : category } )

        
    # Lanza el reproductor
    if strmfile: #Si es un fichero strm no hace falta el play
        logger.info("[xbmctools.py] 3")
        xbmcplugin.setResolvedUrl(int(sys.argv[ 1 ]),True,listitem)
    else:
        logger.info("[xbmctools.py] 4")
        launchplayer(mediaurl, listitem)
        
    if (config.get_setting("subtitulo") == "true") and (opciones[seleccion].startswith("Ver") or opciones[seleccion].startswith("Watch")):
        logger.info("Con subtitulos")
        setSubtitles()


def getLibraryInfo (mediaurl):
    '''Obtiene información de la Biblioteca si existe (ficheros strm) o de los parámetros
    '''
    if DEBUG:
        logger.info('[xbmctools.py] playlist OBTENCIÓN DE DATOS DE BIBLIOTECA')

    # Información básica
    label = xbmc.getInfoLabel( 'listitem.label' )
    label2 = xbmc.getInfoLabel( 'listitem.label2' )
    iconImage = xbmc.getInfoImage( 'listitem.icon' )
    thumbnailImage = xbmc.getInfoImage( 'listitem.Thumb' ) #xbmc.getInfoLabel( 'listitem.thumbnailImage' )
    if DEBUG:
        logger.info ("[xbmctools.py]getMediaInfo: label = " + label) 
        logger.info ("[xbmctools.py]getMediaInfo: label2 = " + label2) 
        logger.info ("[xbmctools.py]getMediaInfo: iconImage = " + iconImage) 
        logger.info ("[xbmctools.py]getMediaInfo: thumbnailImage = " + thumbnailImage) 

    # Creación de listitem
    listitem = xbmcgui.ListItem(label, label2, iconImage, thumbnailImage, mediaurl)

    # Información adicional    
    lista = [
        ('listitem.genre', 's'),            #(Comedy)
        ('listitem.year', 'i'),             #(2009)
        ('listitem.episode', 'i'),          #(4)
        ('listitem.season', 'i'),           #(1)
        ('listitem.top250', 'i'),           #(192)
        ('listitem.tracknumber', 'i'),      #(3)
        ('listitem.rating', 'f'),           #(6.4) - range is 0..10
#        ('listitem.watched', 'd'),          # depreciated. use playcount instead
        ('listitem.playcount', 'i'),        #(2) - number of times this item has been played
#        ('listitem.overlay', 'i'),          #(2) - range is 0..8.  See GUIListItem.h for values
        ('listitem.overlay', 's'),          #JUR - listitem devuelve un string, pero addinfo espera un int. Ver traducción más abajo
        ('listitem.cast', 's'),             # (Michal C. Hall) - List concatenated into a string
        ('listitem.castandrole', 's'),      #(Michael C. Hall|Dexter) - List concatenated into a string
        ('listitem.director', 's'),         #(Dagur Kari)
        ('listitem.mpaa', 's'),             #(PG-13)
        ('listitem.plot', 's'),             #(Long Description)
        ('listitem.plotoutline', 's'),      #(Short Description)
        ('listitem.title', 's'),            #(Big Fan)
        ('listitem.duration', 's'),         #(3)
        ('listitem.studio', 's'),           #(Warner Bros.)
        ('listitem.tagline', 's'),          #(An awesome movie) - short description of movie
        ('listitem.writer', 's'),           #(Robert D. Siegel)
        ('listitem.tvshowtitle', 's'),      #(Heroes)
        ('listitem.premiered', 's'),        #(2005-03-04)
        ('listitem.status', 's'),           #(Continuing) - status of a TVshow
        ('listitem.code', 's'),             #(tt0110293) - IMDb code
        ('listitem.aired', 's'),            #(2008-12-07)
        ('listitem.credits', 's'),          #(Andy Kaufman) - writing credits
        ('listitem.lastplayed', 's'),       #(%Y-%m-%d %h
        ('listitem.album', 's'),            #(The Joshua Tree)
        ('listitem.votes', 's'),            #(12345 votes)
        ('listitem.trailer', 's'),          #(/home/user/trailer.avi)
    ]
    # Obtenemos toda la info disponible y la metemos en un diccionario
    # para la función setInfo.
    infodict = dict()
    for label,tipo in lista:
        key = label.split('.',1)[1]
        value = xbmc.getInfoLabel( label )
        if value != "":
            if DEBUG:
                logger.info ("[xbmctools.py]getMediaInfo: "+key+" = " + value) #infoimage=infolabel
            if tipo == 's':
                infodict[key]=value
            elif tipo == 'i':
                infodict[key]=int(value)
            elif tipo == 'f':
                infodict[key]=float(value)
                
    #Transforma el valor de overlay de string a int.
    if infodict.has_key('overlay'):
        value = infodict['overlay'].lower()
        if value.find('rar') > -1:
            infodict['overlay'] = 1
        elif value.find('zip')> -1:
            infodict['overlay'] = 2
        elif value.find('trained')> -1:
            infodict['overlay'] = 3
        elif value.find('hastrainer')> -1:
            infodict['overlay'] = 4
        elif value.find('locked')> -1:
            infodict['overlay'] = 5
        elif value.find('unwatched')> -1:
            infodict['overlay'] = 6
        elif value.find('watched')> -1:
            infodict['overlay'] = 7
        elif value.find('hd')> -1:
            infodict['overlay'] = 8
        else:
            infodict.pop('overlay')
    if len (infodict) > 0:
        listitem.setInfo( "video", infodict )
    
    return listitem

# Lanza el reproductor
def launchplayer(mediaurl, listitem):

    # TODO: (3.1) Ver compatibilidad de este cambio para sustituir todo lo demás (a mí no me funciona)
    '''
    listitem.setPath(mediaurl)
    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, listitem)
    '''

    # Añadimos el listitem a una lista de reproducción (playlist)
    logger.info("[xbmctools.py] 5")
    playlist = xbmc.PlayList( xbmc.PLAYLIST_VIDEO )
    playlist.clear()
    playlist.add( mediaurl, listitem )

    # Reproduce
    logger.info("[xbmctools.py] 6")
    playersettings = config.get_setting('player_type')
    logger.info("[xbmctools.py] playersettings="+playersettings)

    logger.info("[xbmctools.py] 7")
    player_type = xbmc.PLAYER_CORE_AUTO
    if playersettings == "0":
        player_type = xbmc.PLAYER_CORE_AUTO
        logger.info("[xbmctools.py] PLAYER_CORE_AUTO")
    elif playersettings == "1":
        player_type = xbmc.PLAYER_CORE_MPLAYER
        logger.info("[xbmctools.py] PLAYER_CORE_MPLAYER")
    elif playersettings == "2":
        player_type = xbmc.PLAYER_CORE_DVDPLAYER
        logger.info("[xbmctools.py] PLAYER_CORE_DVDPLAYER")
    logger.info("[xbmctools.py] 8")

    xbmcPlayer = xbmc.Player( player_type )
    xbmcPlayer.play(playlist)

def logdebuginfo(DEBUG,scrapedtitle,scrapedurl,scrapedthumbnail,scrapedplot):
    if (DEBUG):
        logger.info("[xmbctools.py] scrapedtitle="+scrapedtitle)
        logger.info("[xmbctools.py] scrapedurl="+scrapedurl)
        logger.info("[xmbctools.py] scrapedthumbnail="+scrapedthumbnail)
        logger.info("[xmbctools.py] scrapedplot="+scrapedplot)

def alertnodisponible():
    advertencia = xbmcgui.Dialog()
    #'Vídeo no disponible'
    #'No se han podido localizar videos en la página del canal'
    resultado = advertencia.ok(config.get_localized_string(30055) , config.get_localized_string(30056))

def alertnodisponibleserver(server):
    advertencia = xbmcgui.Dialog()
    # 'El vídeo ya no está en %s' , 'Prueba en otro servidor o en otro canal'
    resultado = advertencia.ok( config.get_localized_string(30055),(config.get_localized_string(30057)%server),config.get_localized_string(30058))

def alertUnsopportedServer():
    advertencia = xbmcgui.Dialog()
    # 'Servidor no soportado o desconocido' , 'Prueba en otro servidor o en otro canal'
    resultado = advertencia.ok( config.get_localized_string(30065),config.get_localized_string(30058))

def alerterrorpagina():
    advertencia = xbmcgui.Dialog()
    #'Error en el sitio web'
    #'No se puede acceder por un error en el sitio web'
    resultado = advertencia.ok(config.get_localized_string(30059) , config.get_localized_string(30060))

def alertanomegauploadlow(server):
    advertencia = xbmcgui.Dialog()
    #'La calidad elegida no esta disponible', 'o el video ha sido borrado',
    #'Prueba a reproducir en otra calidad'
    resultado = advertencia.ok( config.get_localized_string(30055) , config.get_localized_string(30061) , config.get_localized_string(30062))

def unseo(cadena):
    if cadena.upper().startswith("VER GRATIS LA PELICULA "):
        cadena = cadena[23:]
    elif cadena.upper().startswith("VER GRATIS PELICULA "):
        cadena = cadena[20:]
    elif cadena.upper().startswith("VER ONLINE LA PELICULA "):
        cadena = cadena[23:]
    elif cadena.upper().startswith("VER GRATIS "):
        cadena = cadena[11:]
    elif cadena.upper().startswith("VER ONLINE "):
        cadena = cadena[11:]
    elif cadena.upper().startswith("DESCARGA DIRECTA "):
        cadena = cadena[17:]
    return cadena

# AÑADIDO POR JUR. SOPORTE DE FICHEROS STRM
def playstrm(params,url,category):
    '''Play para videos en ficheros strm
    '''
    logger.info("[xbmctools.py] playstrm url="+url)

    title = unicode( xbmc.getInfoLabel( "ListItem.Title" ), "utf-8" )
    thumbnail = urllib.unquote_plus( params.get("thumbnail") )
    plot = unicode( xbmc.getInfoLabel( "ListItem.Plot" ), "utf-8" )
    server = params["server"]
    if (params.has_key("Serie")):
        serie = params.get("Serie")
    else:
        serie = ""
    
    playvideo("Biblioteca pelisalacarta",server,url,category,title,thumbnail,plot,strmfile=True,Serie=serie)

def renderItems(itemlist, params, url, category,isPlayable='false'):
    if itemlist <> None:
        for item in itemlist:
            if item.category == "":
                item.category = category
            if item.folder :
                if len(item.extra)>0:
                    addnewfolderextra( item.channel , item.action , item.category , item.title , item.url , item.thumbnail , item.plot , extradata = item.extra , totalItems = item.totalItems, fanart=item.fanart , context=item.context )
                else:
                    addnewfolder( item.channel , item.action , item.category , item.title , item.url , item.thumbnail , item.plot , totalItems = item.totalItems , fanart = item.fanart, context = item.context  )
            else:
                if item.duration:
                    addnewvideo( item.channel , item.action , item.category , item.server, item.title , item.url , item.thumbnail , item.plot , "" , item.duration , IsPlayable=isPlayable,context = item.context , subtitle=item.subtitle, totalItems = item.totalItems  )
                else:    
                    addnewvideo( item.channel , item.action , item.category , item.server, item.title , item.url , item.thumbnail , item.plot, IsPlayable=isPlayable , context = item.context , subtitle = item.subtitle , totalItems = item.totalItems )
    
        # Cierra el directorio
        xbmcplugin.setContent(pluginhandle,"Movies")
        xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
        xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )
    xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )
    
def setSubtitles():
    logger.info("[xbmctools.py] setSubtitles: start")
    import time
    while xbmc.Player().isPlayingVideo()==False:
        logger.info("[xbmctools.py] setSubtitles: Waiting 2 seconds for video to start before setting subtitles")
        time.sleep(2)
    logger.info("[xbmctools.py] setSubtitles: Setting subtitles now that the video start")
    xbmc.Player().setSubtitles(os.path.join( config.get_data_path(), 'subtitulo.srt' ))
    config.set_setting("subtitulo", "false")
    logger.info("[xbmctools.py] setSubtitles: end")
    return
