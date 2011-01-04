# -*- coding: iso-8859-1 -*-
import urlparse,urllib2,urllib,re
import os
import sys
import scrapertools
import config
import logger
try:
    import parametrizacion
    DOWNLOAD_ENABLED = parametrizacion.DOWNLOAD_ENABLED
except:
    DOWNLOAD_ENABLED = False

DEBUG = True
CHANNELNAME = "channelselector"

def mainlist(params,url,category):
    logger.info("[channelselector.py] mainlist")

    # Verifica actualizaciones solo en el primer nivel
    try:
        import updater
    except ImportError:
        logger.info("[channelselector.py] No disponible modulo actualizaciones")
    else:
        if config.getSetting("updatecheck2") == "true":
            logger.info("[channelselector.py] Verificar actualizaciones activado")
            updater.checkforupdates()
        else:
            logger.info("[channelselector.py] Verificar actualizaciones desactivado")

    idioma = config.getSetting("languagefilter")
    logger.info("[channelselector.py] idioma=%s" % idioma)
    langlistv = [config.getLocalizedString(30025),config.getLocalizedString(30026),config.getLocalizedString(30027),config.getLocalizedString(30028),config.getLocalizedString(30029)]
    try:
        idiomav = langlistv[int(idioma)]
    except:
        idiomav = langlistv[0]
    #logger.info("[channelselector.py] idiomav=%s" % idiomav)

    addfolder(config.getLocalizedString(30118)+" ("+idiomav+")","channelselector","channeltypes")
    #searchwebs=": Cinetube,Peliculasyonkis,Cinegratis,tumejortv.com,Peliculas21,Cine15,Seriesyonkis,Yotix.tv,DocumaniaTV,Discoverymx,Stagevu,tu.tv"
    #channelslist.append([ config.getLocalizedString(30103)+searchwebs , "buscador" , "Buscador" , "" , "B" ])# Buscador
    addfolder(config.getLocalizedString(30103),"buscador"       ,"mainlist")
    addfolder(config.getLocalizedString(30102),"favoritos"      ,"mainlist")
    if (DOWNLOAD_ENABLED):
        addfolder(config.getLocalizedString(30101),"descargados","mainlist")
    addfolder(config.getLocalizedString(30100),"configuracion"  ,"mainlist")
    addfolder(config.getLocalizedString(30104),"ayuda"          ,"mainlist")

    # Label (top-right)...
    import xbmcplugin
    xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category="" )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
    xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

def channeltypes(params,url,category):
    logger.info("[channelselector.py] channeltypes")

    addfolder(config.getLocalizedString(30121),"channelselector","listchannels","*")   # Todos
    addfolder(config.getLocalizedString(30122),"channelselector","listchannels","F")  # Películas
    addfolder(config.getLocalizedString(30123),"channelselector","listchannels","S")  # Series
    addfolder(config.getLocalizedString(30124),"channelselector","listchannels","A")  # Anime
    addfolder(config.getLocalizedString(30125),"channelselector","listchannels","D")  # Dibujos
    addfolder(config.getLocalizedString(30126),"channelselector","listchannels","M")  # Música
    addfolder(config.getLocalizedString(30127),"channelselector","listchannels","G")  # Servidores

    # Label (top-right)...
    import xbmcplugin
    xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category="" )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
    xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )
    
def listchannels(params,url,category):
    logger.info("[channelselector.py] listchannels")

    try:
        idioma = config.getSetting("languagefilter")
        logger.info("[channelselector.py] idioma=%s" % idioma)
        langlistv = ["","ES","EN","IT","PT"]
        idiomav = langlistv[int(idioma)]
        logger.info("[channelselector.py] idiomav=%s" % idiomav)
    except:
        idiomav=""

    channelslist = channels_list()

    for channel in channelslist:
        # Pasa si no ha elegido "todos" y no está en la categoría elegida
        if category<>"*" and category not in channel[4]:
            #logger.info(channel[0]+" no entra por tipo #"+channel[4]+"#, el usuario ha elegido #"+category+"#")
            continue
        # Pasa si no ha elegido "todos" y no está en el idioma elegido
        if channel[3]<>"" and idiomav<>"" and idiomav not in channel[3]:
            #logger.info(channel[0]+" no entra por idioma #"+channel[3]+"#, el usuario ha elegido #"+idiomav+"#")
            continue
        addfolder(channel[0] , channel[1] , "mainlist" , channel[2])

    # Label (top-right)...
    import xbmcplugin
    xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
    xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

def channels_list():
    channelslist = []
    channelslist.append([ "Cinetube"              , "cinetube"             , "" , "ES" , "F" , "generic" ])
    channelslist.append([ "Peliculasyonkis"       , "peliculasyonkis"      , "" , "ES" , "F" , "xbmc" ])
    channelslist.append([ "Divx Online"           , "divxonline"           , "" , "ES" , "F" , "xbmc" ]) # added by ermanitu
    channelslist.append([ "Cinegratis"            , "cinegratis"           , "" , "ES" , "F,S,A,D" , "generic" ])
    channelslist.append([ "tumejortv.com"         , "tumejortv"            , "" , "ES" , "F,S" , "generic" ])
    channelslist.append([ "Peliculas21"           , "peliculas21"          , "" , "ES" , "F" , "xbmc"  ])
    channelslist.append([ "Dospuntocerovision"    , "dospuntocerovision"   , "" , "ES" , "F,S" , "xbmc"  ])
    channelslist.append([ "Cine15"                , "cine15"               , "" , "ES" , "F" , "generic" ])
    channelslist.append([ "Peliculasid"           , "peliculasid"          , "" , "ES" , "F" , "xbmc"  ])
    channelslist.append([ "Cinegratis24h"         , "cinegratis24h"        , "" , "ES" , "F" , "xbmc"  ])
    channelslist.append([ "Cine-Adicto"           , "cineadicto"           , "" , "ES" , "F,D" , "xbmc"  ])
    channelslist.append([ "PelisFlv"              , "pelisflv"             , "" , "ES" , "F" , "xbmc"  ])
    channelslist.append([ "NoloMires"             , "nolomires"            , "" , "ES" , "F" , "xbmc"  ])
    channelslist.append([ "NewDivx"               , "newdivx"              , "" , "ES" , "F,D" , "xbmc"  ])
    channelslist.append([ "Peliculas Online FLV"  , "peliculasonlineflv"   , "" , "ES" , "F,D" , "xbmc"  ])
    channelslist.append([ "FilmesOnlineBr"        , "filmesonlinebr"       , "" , "PT" , "F" , "xbmc"  ])
    channelslist.append([ "TVShack.cc (VO)"       , "tvshack"              , "" , "EN" , "F,S,A,D,M" , "xbmc"  ])
    channelslist.append([ "DeLaTV"                , "delatv"               , "" , "ES" , "F" , "xbmc"  ])
    channelslist.append([ "Pelis24"               , "pelis24"              , "" , "ES" , "F,S" , "xbmc"  ])
    channelslist.append([ "Veocine"               , "veocine"              , "" , "ES" , "F,A,D" , "xbmc"  ])
    channelslist.append([ "Pintadibujos"          , "pintadibujos"         , "" , "ES" , "F,A" , "xbmc"  ])
    channelslist.append([ "Pelis Pekes"           , "pelispekes"           , "" , "ES" , "F,A" , "xbmc"  ])
    channelslist.append([ "Descarga Cine Clásico" , "descargacineclasico"  , "" , "ES" , "F,S" , "xbmc"  ])
    channelslist.append([ "Capitan Cinema"        , "capitancinema"        , "" , "ES" , "F" , "generic" ])
    channelslist.append([ "Film Streaming"        , "filmstreaming"        , "" , "IT" , "F,A" , "xbmc"  ])
    channelslist.append([ "No Megavideo"          , "nomegavideo"          , "" , "ES" , "F" , "xbmc"  ])
    channelslist.append([ "LetMeWatchThis"        , "letmewatchthis"       , "" , "EN" , "F,S" , "xbmc"  ])
    channelslist.append([ "Cineblog01"            , "cineblog01"           , "" , "IT" , "F,S,A" , "xbmc"  ])
    channelslist.append([ "Descargapelis"         , "descargapelis"        , "" , "ES" , "F" , "xbmc"  ])
    channelslist.append([ "Vagos"                 , "vagos"                , "" , "ES" , "F,S" , "xbmc"  ])
    channelslist.append([ "Cuevana"               , "cuevana"              , "" , "ES" , "F,S" , "generic"  ])
    channelslist.append([ "Somosmovies"           , "somosmovies"          , "" , "ES" , "F,S,D,A" , "generic"  ])
    channelslist.append([ "PeliculasFLV"          , "peliculasflv"         , "" , "ES" , "F" , "generic"  ])
    channelslist.append([ "Seriematic"            , "seriematic"           , "" , "ES" , "S,D,A" , "generic"  ])
    channelslist.append([ "Serieonline"           , "serieonline"          , "" , "ES" , "F,S,D" , "generic"  ])
    #channelslist.append([ "Pelis-Sevillista56"    , "sevillista"           , "" , "ES" , "F" , "xbmc"])
    channelslist.append([ "Seriesyonkis"          , "seriesyonkis"         , "Series" , "ES" , "S,A" , "xbmc"  ]) #Modificado por JUR para añadir la categoría
    channelslist.append([ "Seriespepito"          , "seriespepito"         , "" , "ES" , "S" , "generic" ])
    channelslist.append([ "Series21"              , "series21"             , "" , "ES" , "S" , "xbmc"  ])
    channelslist.append([ "DeLaTV Series"         , "bancodeseries"        , "" , "ES" , "S" , "xbmc"  ])
    #channelslist.append([ "SoloSeries"            , "soloseries"           , "" , "ES" , "S" , "xbmc"  ])
    #channelslist.append([ "seriesonline.us"       , "seriesonline"         , "" , "ES" , "S" , "xbmc" ])
    channelslist.append([ "Ver Telenovelas Online", "vertelenovelasonline" , "" , "ES" , "S" , "xbmc"  ])
    channelslist.append([ "Yotix.tv"              , "yotix"                , "" , "ES" , "A" , "generic" ])
    channelslist.append([ "MCAnime"               , "mcanime"              , "" , "ES" , "A" , "xbmc"  ])
    channelslist.append([ "Animetakus"            , "animetakus"           , "" , "ES" , "A" , "generic" ])
    channelslist.append([ "Ver-anime"             , "veranime"             , "" , "ES" , "A" , "xbmc"  ])
    channelslist.append([ "Watchanimeon"          , "watchanimeon"         , "" , "EN" , "A" , "xbmc"  ])
    channelslist.append([ "Animeid"               , "animeid"              , "" , "ES" , "A" , "xbmc"  ])
    channelslist.append([ "dibujosanimadosgratis" , "dibujosanimadosgratis", "" , "ES" , "A" , "xbmc"  ])
    channelslist.append([ "Sonolatino"            , "sonolatino"           , "" , ""   , "M" , "xbmc"  ])
    channelslist.append([ "DocumaniaTV"           , "documaniatv"          , "" , "ES" , "D" , "xbmc"  ])
    channelslist.append([ "DocumentariesTV"       , "documentariestv"      , "" , "EN", "D" , "xbmc"  ])
    channelslist.append([ "Documentalesyonkis"    , "documentalesyonkis"   , "" , "ES" , "D" , "generic" ])
    channelslist.append([ "Documentalesatonline"  , "documentalesatonline" , "" , "ES" , "D" , "xbmc"  ])
    channelslist.append([ "Documentalesatonline2" , "documentalesatonline2", "" , "ES" , "D" , "xbmc"  ])
    channelslist.append([ "Discoverymx.Wordpress" , "discoverymx"          , "" , "ES" , "D" , "xbmc"  ])
    channelslist.append([ "Gratisdocumentales"    , "gratisdocumentales"   , "" , "ES" , "D" , "xbmc"  ])
    channelslist.append([ "Programas TV Online"   , "programastv"          , "" , "ES" , "D" , "xbmc"  ])
    #channelslist.append([ "Futbol Virtual"        , "futbolvirtual"        , "" , "ES" , "D" , "xbmc"  ])
    channelslist.append([ "Redes.tv"              , "redestv"              , "" , "ES" , "D" , "xbmc"  ])
    channelslist.append([ "Trailers ecartelera"   , "ecarteleratrailers"   , "" , "ES,EN" , "F" , "xbmc"  ])
    channelslist.append([ config.getLocalizedString(30128), "trailertools" , "" , "" , "F" , "xbmc"  ])
    channelslist.append([ "Stagevu"               , "stagevusite"          , "" , "" , "G" , "xbmc"  ])
    channelslist.append([ "tu.tv"                 , "tutvsite"             , "" , "ES", "G" , "xbmc"  ])
    channelslist.append([ "Megavideo"             , "megavideosite"        , "" , "" , "G" , "xbmc"  ])
    channelslist.append([ "Megaupload"            , "megauploadsite"       , "" , "" , "G" , "xbmc"  ])
    channelslist.append([ "Megalive"              , "megalivewall"         , "" , "" , "G" , "xbmc"  ])

    #channelslist.append([ "Eduman Movies" , "edumanmovies" , "" , "ES" , "F" ])
    #channelslist.append([ "SesionVIP" , "sesionvip" , "" , "ES" , "F" ])
    #channelslist.append([ "Newcineonline" , "newcineonline" , "" , "ES" , "S" ])
    #channelslist.append([ "PeliculasHD" , "peliculashd" , "" , "ES" , "F" ])
    #channelslist.append([ "Wuapi" , "wuapisite" , "" , "ES" , "F" ])
    #channelslist.append([ "Frozen Layer" , "frozenlayer" , "" , "ES" , "A" ])
    #channelslist.append([ "Ovasid"                , "ovasid"               , "" , "ES" , "A" , "xbmc"  ])
    return channelslist

def addfolder(nombre,channelname,accion,category=""):
    if category == "":
        try:
            category = unicode( nombre, "utf-8" ).encode("iso-8859-1")
        except:
            pass
    
    import xbmc
    if config.getSetting("thumbnail_type")=="0":
        IMAGES_PATH = xbmc.translatePath( os.path.join( os.getcwd(), 'resources' , 'images' , 'posters' ) )
    else:
        IMAGES_PATH = xbmc.translatePath( os.path.join( os.getcwd(), 'resources' , 'images' , 'banners' ) )
    
    if config.getSetting("thumbnail_type")=="0":
        WEB_PATH = "http://www.mimediacenter.info/xbmc/pelisalacarta/posters/"
    else:
        WEB_PATH = "http://www.mimediacenter.info/xbmc/pelisalacarta/banners/"

    # Preferencia: primero JPG
    thumbnail = thumbnailImage=os.path.join(IMAGES_PATH, channelname+".jpg")
    # Preferencia: segundo PNG
    if not os.path.exists(thumbnail):
        thumbnail = thumbnailImage=os.path.join(IMAGES_PATH, channelname+".png")
    # Preferencia: tercero WEB
    if not os.path.exists(thumbnail):
        thumbnail = thumbnailImage=WEB_PATH+channelname+".png"
    #Si no existe se usa el logo del plugin
    #if not os.path.exists(thumbnail):
    #    thumbnail = thumbnailImage=WEB_PATH+"ayuda.png" #Check: ruta del logo

    import xbmcgui
    import xbmcplugin
    listitem = xbmcgui.ListItem( nombre , iconImage="DefaultFolder.png", thumbnailImage=thumbnail)
    itemurl = '%s?channel=%s&action=%s&category=%s' % ( sys.argv[ 0 ] , channelname , accion , category )
    xbmcplugin.addDirectoryItem( handle = int(sys.argv[ 1 ]), url = itemurl , listitem=listitem, isFolder=True)

