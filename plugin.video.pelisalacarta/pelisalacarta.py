# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Main
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#------------------------------------------------------------

import urllib
import urllib2
import os
import sys
import logger
import config

def run():
    logger.info("[pelisalacarta.py] run")
    
    # Verifica si el path de usuario del plugin está creado
    if not os.path.exists(config.DATA_PATH):
        logger.debug("[pelisalacarta.py] Path de usuario no existe, se crea: "+config.DATA_PATH)
        os.mkdir(config.DATA_PATH)

    # Imprime en el log los parámetros de entrada
    logger.info("[pelisalacarta.py] sys.argv=%s" % str(sys.argv))
    
    # Crea el diccionario de parametros
    params = dict()
    if len(sys.argv)>=2 and len(sys.argv[2])>0:
        params = dict(part.split('=') for part in sys.argv[ 2 ][ 1: ].split('&'))
    logger.info("[pelisalacarta.py] params=%s" % str(params))
    
    # Extrae la url de la página
    if (params.has_key("url")):
        url = urllib.unquote_plus( params.get("url") )
    else:
        url=''

    # Extrae la accion
    if (params.has_key("action")):
        action = params.get("action")
    else:
        action = "selectchannel"

    # Extrae el server
    if (params.has_key("server")):
        server = params.get("server")
    else:
        server = ""

    # Extrae la categoria
    if (params.has_key("category")):
        category = urllib.unquote_plus( params.get("category") )
    else:
        if params.has_key("channel"):
            category = params.get("channel")
        else:
            category = ""

    # Extrae la serie
    if (params.has_key("Serie")):
        serie = params.get("Serie")
    else:
        serie = ""
    logger.info("[pelisalacarta.py] url="+url+", action="+action+", server="+server+", category="+category+", serie="+serie)

    #JUR - Gestión de Errores de Internet (Para que no casque el plugin 
    #      si no hay internet (que queda feo)
    try:

        # Accion por defecto - elegir canal
        if ( action=="selectchannel" ):
            import channelselector as plugin
            plugin.mainlist(params, url, category)

        # Actualizar version
        elif ( action=="update" ):
            try:
                import updater
                updater.update(params)
            except ImportError:
                logger.info("[pelisalacarta.py] Actualizacion automática desactivada")
                
            import channelselector as plugin
            plugin.mainlist(params, url, category)

        # Reproducir un STRM
        elif (action=="strm"):
            import xbmctools
            xbmctools.playstrm(params, url, category)

        # El resto de acciones vienen en el parámetro "action", y el canal en el parámetro "channel"
        else:

            # Actualiza el canal si ha cambiado    
            if action=="mainlist" and config.getSetting("updatechannels")=="true":
                try:
                    import updater
                    actualizado = updater.updatechannel(params.get("channel"))
    
                    if actualizado:
                        import xbmcgui
                        advertencia = xbmcgui.Dialog()
                        advertencia.ok("pelisalacarta",params.get("channel"),config.getLocalizedString(30063))
                except:
                    logger.info("Actualización de canales desactivada")

            # Ejecuta el canal
            exec "import "+params.get("channel")+" as channel"
            generico = False
            try:
                generico = channel.isGeneric()
            except:
                generico = False

            print "generico=" , generico 
            
            # Es un canal específico de xbmc
            if not generico:
                exec "channel."+action+"(params, url, category)"
            
            # Es un canal genérico
            else:
                if params.has_key("title"):
                    title = urllib.unquote_plus( params.get("title") )
                else:
                    title = ""
                if params.has_key("thumbnail"):
                    thumbnail = urllib.unquote_plus( params.get("thumbnail") )
                else:
                    thumbnail = ""
                if params.has_key("plot"):
                    plot = urllib.unquote_plus( params.get("plot") )
                else:
                    plot = ""
                if params.has_key("server"):
                    server = urllib.unquote_plus( params.get("server") )
                else:
                    server = "directo"
            
                import xbmctools
                if action=="play":
                    xbmctools.playvideo(params.get("channel"),server,url,category,title,thumbnail,plot)
                else:
                    from item import Item
                    item = Item(channel=params.get("channel"), title=title , url=url, thumbnail=thumbnail , plot=plot , server=server)
        
                    if action!="findvideos":
                        exec "itemlist = channel."+action+"(item)"
                    else:
                        # Intenta ejecutar una posible funcion "findvideos" del canal
                        try:
                            exec "itemlist = channel."+action+"(item)"
                        # Si no funciona, lanza el método genérico para detectar vídeos
                        except:
                            itemlist = findvideos(item)

                    xbmctools.renderItems(itemlist, params, url, category)
    
    except urllib2.URLError,e:
        for line in sys.exc_info():
            logger.error( "%s" % line )
        import xbmcgui
        ventana_error = xbmcgui.Dialog()
        # Agarra los errores surgidos localmente enviados por las librerias internas
        if hasattr(e, 'reason'):
            logger.info("Razon del error, codigo: %d , Razon: %s" %(e.reason[0],e.reason[1]))
            texto = config.getLocalizedString(30050) # "No se puede conectar con el sitio web"
            ok = ventana_error.ok ("pelisalacarta", texto)
        # Agarra los errores con codigo de respuesta del servidor externo solicitado     
        elif hasattr(e,'code'):
            logger.info("codigo de error HTTP : %d" %e.code)
            texto = (config.getLocalizedString(30051) % e.code) # "El sitio web no funciona correctamente (error http %d)"
            ok = ventana_error.ok ("pelisalacarta", texto)    
        else:
            pass

# Función genérica para encontrar vídeos en una página
def findvideos(item):
    logger.info("[pelisalacarta.py] findvideos")

    # Descarga la página
    import scrapertools
    data = scrapertools.cachePage(item.url)
    #logger.info(data)

    # Busca los enlaces a los videos
    import servertools
    listavideos = servertools.findvideos(data)

    itemlist = []
    for video in listavideos:
        scrapedtitle = item.title.strip() + " - " + video[0]
        scrapedurl = video[1]
        server = video[2]
        import xbmctools
        xbmctools.addnewvideo( item.channel , "play" , "" , server , scrapedtitle , scrapedurl , item.thumbnail , item.plot )
    # ------------------------------------------------------------------------------------

    return itemlist
