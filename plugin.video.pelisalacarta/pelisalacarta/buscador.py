# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#------------------------------------------------------------
import urlparse,urllib2,urllib,re
import sys
import xbmc
import xbmcgui
import xbmcplugin

from core import config
from core import logger
from core import xbmctools
from core.item import Item

CHANNELNAME = "buscador"

logger.info("[buscador.py] init")

DEBUG = True

def mainlist(params,url="",category=""):
    logger.info("[buscador.py] mainlist")

    listar_busquedas(params,url,category)

def searchresults(params,url="",category=""):
    logger.info("[buscador.py] searchresults")
    salvar_busquedas(params,url,category)
    if url == "" and category == "":
        tecleado = params.url
    else:
        tecleado = url
    tecleado = tecleado.replace(" ", "+")
    
    # Lanza las búsquedas
    
    # Cinegratis
    matches = []
    itemlist = []
    try:
        from pelisalacarta.channels import cinetube
        itemlist.extend( cinetube.getsearchresults(params,tecleado,category) )
    except:
        pass
    try:
        from pelisalacarta.channels import cinegratis
        matches.extend( cinegratis.performsearch(tecleado) )
    except:
        pass
    try:
        from pelisalacarta.channels import peliculasyonkis
        matches.extend( peliculasyonkis.performsearch(tecleado) )
    except:
        pass
    try:
        from pelisalacarta.channels import tumejortv
        matches.extend( tumejortv.performsearch(tecleado) )
    except:
        pass
    try:
        from pelisalacarta.channels import cine15
        matches.extend( cine15.performsearch(tecleado) )
    except:
        pass
    try:
        from pelisalacarta.channels import peliculas21
        matches.extend( peliculas21.performsearch(tecleado) )
    except:
        pass
    #matches.extend( sesionvip.performsearch(tecleado) )
    try:
        from pelisalacarta.channels import seriesyonkis
        matches.extend( seriesyonkis.performsearch(tecleado) )
    except:
        pass
    try:
        from pelisalacarta.channels import documaniatv
        matches.extend( documaniatv.performsearch(tecleado) )
    except:
        pass
    try:
        from pelisalacarta.channels import discoverymx
        matches.extend( discoverymx.performsearch(tecleado) )
    except:
        pass
    try:
        from pelisalacarta.channels import yotix
        matches.extend( yotix.performsearch(tecleado) )
    except:
        pass
    try:
        from pelisalacarta.channels import stagevusite
        matches.extend( stagevusite.performsearch(tecleado) )
    except:
        pass
    try:
        from pelisalacarta.channels import tutvsite
        matches.extend( tutvsite.performsearch(tecleado) )
    except:
        pass
    
    for item in itemlist:
        targetchannel = item.channel
        action = item.action
        category = category
        scrapedtitle = item.title+" ["+item.channel+"]"
        scrapedurl = item.url
        scrapedthumbnail = item.thumbnail
        scrapedplot = item.plot
        
        xbmctools.addnewfolder( targetchannel , action , category , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )
    
    # Construye los resultados
    for match in matches:
        targetchannel = match[0]
        action = match[1]
        category = match[2]
        scrapedtitle = match[3]+" ["+targetchannel+"]"
        scrapedurl = match[4]
        scrapedthumbnail = match[5]
        scrapedplot = match[6]
        
        xbmctools.addnewfolder( targetchannel , action , category , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )

    # Cierra el directorio
    xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_TITLE )
    xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )


def salvar_busquedas(params,url="",category=""):
    if url == "" and category == "":
        channel = params.channel
        url = params.url
    else:
        channel = params.get("channel")
    limite_busquedas = ( 10, 20, 30, 40, )[ int( config.get_setting( "limite_busquedas" ) ) ]
    matches = []
    try:
        presets = config.get_setting("presets_buscados")
        if "|" in presets:
            presets = matches = presets.split("|")            
            for count, preset in enumerate( presets ):
                if url in preset:
                    del presets[ count ]
                    break
        
        if len( presets ) >= limite_busquedas:
            presets = presets[ : limite_busquedas - 1 ]
    except:
        presets = ""
    presets2 = ""
    if len(matches)>0:
        for preset in presets:
            presets2 = presets2 + "|" + preset 
        presets = url + presets2
    elif presets != "":
        presets = url + "|" + presets
    else:
        presets = url
    config.set_setting("presets_buscados",presets)
    # refresh container so items is changed
    #xbmc.executebuiltin( "Container.Refresh" )
        
def listar_busquedas(params,url="",category=""):
    #print "category :" +category
    if url == "" and category == "":
        channel_preset = params.channel
        accion = params.action
        category = "Buscador_Generico"
    else:
        channel_preset = params.get("channel")
        accion = params.get("action")
        category = "Buscador_Normal"
    #print "listar_busquedas()"
    channel2 = ""
    itemlist=[]
    # Despliega las busquedas anteriormente guardadas
    try:
        presets = config.get_setting("presets_buscados")
        
        if channel_preset != CHANNELNAME:
            channel2 = channel_preset
        print "channel_preset :%s" %channel_preset
        
        matches = ""
        if "|" in presets:
            matches = presets.split("|")
            itemlist.append( Item(channel="buscador" , action="por_teclado"  , title=config.get_localized_string(30103)+"..."  , url=matches[0] ,thumbnail="" , plot=channel2, category = category , context = 1 ))
            #addfolder( "buscador"   , config.get_localized_string(30103)+"..." , matches[0] , "por_teclado", channel2 ) # Buscar
        else:
            itemlist.append( Item(channel="buscador" , action="por_teclado"  ,  title=config.get_localized_string(30103)+"..." ,   url="" ,thumbnail="" , plot=channel2 , category = category , context = 0 ))
            #addfolder( "buscador"   , config.get_localized_string(30103)+"..." , "" , "por_teclado", channel2 )
        if len(matches)>0:    
            for match in matches:
                
                title=scrapedurl = match
                itemlist.append( Item(channel=channel_preset , action="searchresults"  , title=title ,  url=scrapedurl, thumbnail="" , plot="" , category = category ,  context=1 ))
                #addfolder( channel_preset , title , scrapedurl , "searchresults" )
        elif presets != "":
        
            title = scrapedurl = presets
            itemlist.append( Item(channel=channel_preset , action="searchresults"  , title=title ,  url=scrapedurl, thumbnail= "" , plot="" , category = category , context = 1 ))
            #addfolder( channel_preset , title , scrapedurl , "searchresults" )
    except:
         itemlist.append( Item(channel="buscador" , action="por_teclado"  , title=config.get_localized_string(30103)+"..." ,  url="", thumbnail="" , plot=channel2 , category = category ,  context = 0  ))
        #addfolder( "buscador"   , config.get_localized_string(30103)+"..." , "" , "por_teclado" , channel2 )
    
    if url=="" and category=="Buscador_Generico":

        return itemlist
    else:
        for item in itemlist:
            channel = item.channel
            action = item.action
            category = category
            scrapedtitle = item.title
            scrapedurl = item.url
            scrapedthumbnail = item.thumbnail
            scrapedplot = item.plot
            extra=item.extra
            context = item.context
            xbmctools.addnewfolderextra( channel , action , category , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot , extradata = extra , context = context)
            
        # Cierra el directorio
        xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )
        xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
        xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )
    
def borrar_busqueda(params,url="",category=""):
    if url == "" and category == "":
        channel = params.channel
        url = params.url
    else:
        channel = params.get("channel")
    
    matches = []
    try:
        presets = config.get_setting("presets_buscados")
        if "|" in presets:
            presets = matches = presets.split("|")
            for count, preset in enumerate( presets ):
                if url in preset:
                    del presets[ count ]
                    break
        elif presets == url:
            presets = ""
            
    except:
        presets = ""
    if len(matches)>1:
        presets2 = ""
        c = 0
        barra = ""
        for preset in presets:
            if c>0:
                barra = "|"
            presets2 =  presets2 + barra + preset 
            c +=1
        presets = presets2
    elif len(matches) == 1:
        presets = presets[0]
    config.set_setting("presets_buscados",presets)
    # refresh container so item is removed
    xbmc.executebuiltin( "Container.Refresh" )

def teclado(default="", heading="", hidden=False):
    logger.info("[buscador.py] teclado")
    tecleado = ""
    keyboard = xbmc.Keyboard(default)
    keyboard.doModal()
    if (keyboard.isConfirmed()):
        tecleado = keyboard.getText()
        if len(tecleado)<=0:
            return
    
    return tecleado
    
def por_teclado(params,url="",category=""):
    logger.info("[buscador.py] por_teclado")
    print "category :"+category,"url :"+url
    if category == "" or category == "Buscador_Generico":

        channel  = params.channel
        tecleado = teclado(params.url)
        if len(tecleado)<=0:
            return
        if params.plot:
            channel = params.plot
            exec "import pelisalacarta.channels."+channel+" as plugin"
        else:
            exec "import pelisalacarta."+channel+" as plugin"


        params.url = tecleado
        itemlist = plugin.searchresults(params)
        return itemlist
    else:
        channel  = params.get("channel")
        tecleado = teclado(url)
        if len(tecleado)<=0:
            return
        if params.get("plot"):
            channel = params.get("plot")
            exec "import pelisalacarta.channels."+channel+" as plugin"
        else:
            exec "import pelisalacarta."+channel+" as plugin"

        url = tecleado
        plugin.searchresults(params, url, category)


def addfolder( canal , nombre , url , accion , channel2 = "" ):
    logger.info('[buscador.py] addfolder( "'+nombre+'" , "' + url + '" , "'+accion+'")"')
    listitem = xbmcgui.ListItem( nombre , iconImage="DefaultFolder.png")
    itemurl = '%s?channel=%s&action=%s&category=%s&url=%s&channel2=%s' % ( sys.argv[ 0 ] , canal , accion , urllib.quote_plus(nombre) , urllib.quote_plus(url),channel2 )
    
    
    if accion != "por_teclado":
        contextCommands = []
        DeleteCommand = "XBMC.RunPlugin(%s?channel=buscador&action=borrar_busqueda&title=%s&url=%s)" % ( sys.argv[ 0 ]  ,  urllib.quote_plus( nombre ) , urllib.quote_plus( url ) )
        contextCommands.append((config.get_localized_string( 30300 ),DeleteCommand))
        listitem.addContextMenuItems ( contextCommands, replaceItems=False)
        
    xbmcplugin.addDirectoryItem( handle = int( sys.argv[ 1 ] ), url = itemurl , listitem=listitem, isFolder=True)
