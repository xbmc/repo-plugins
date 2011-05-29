# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para peliculashd
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#------------------------------------------------------------
import urlparse,urllib2,urllib,re,string
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

from pelisalacarta import buscador
from servers import megalive

import simplejson as json

__plugin__ = "plugin.video.pelisalacarta"
CHANNELNAME = "megalivewall"
try:
    import xbmcaddon
    Addon = xbmcaddon.Addon( id=__plugin__)
    PLUGIN_PATH = xbmc.translatePath( Addon.getAddonInfo( "Path" ))
except ImportError:
    PLUGIN_PATH = os.getcwd()

_VALID_URL = r'http\:\/\/www.megalive\.com/(?:(?:v/)|\?(?:s=.+?&(?:amp;)?)?((?:(?:v\=)))?)?([A-Z0-9]{8})'
file_path = xbmc.translatePath( os.path.join( PLUGIN_PATH,"pelisalacarta", 'channels' , "megalive.json" ) )

# Esto permite su ejecuciÛn en modo emulado
try:
    pluginhandle = int( sys.argv[ 1 ] )
except:
    pluginhandle = ""

# Traza el inicio del canal
logger.info("[megalivewall.py] init")

DEBUG = True

def mainlist(params,url,category):
    logger.info("[megalivewall.py] mainlist")
    
    itemlist = getmainlist(params,url,category)
    xbmctools.renderItems(itemlist, params, url, category)

def getmainlist(params,url,category):
    logger.info("[cinetube.py] getmainlist")

    itemlist = []
    itemlist.append( Item(channel=CHANNELNAME, title=config.get_localized_string(30401)    , action="listWall", url="http://www.megalive.com/"      , folder=True) )
    itemlist.append( Item(channel=CHANNELNAME, title= config.get_localized_string(30402)      , action="listcategory", url="http://www.megalive.com/?c=streams", folder=True) )
    itemlist.append( Item(channel=CHANNELNAME, title=config.get_localized_string(30403) , action="listfavorites"     , url=""                                       , folder=True) )
    itemlist.append( Item(channel=CHANNELNAME, title=config.get_localized_string(30404)   , action="playByID"             , url=""       , folder=True) )
    
    return itemlist
    
def listWall(params,url,category):
    logger.info("[megalivewall.py] listWall")
    
    itemlist = getlistWall(params,url,category)
    xbmctools.renderItems(itemlist, params, url, category,isPlayable='true')
    
def listcategory(params,url,category):
    logger.info("[megalivewall.py] listcategory")
    
    itemlist = getlistcategory(params,url,category)
    xbmctools.renderItems(itemlist, params, url, category)
    
def listfavorites(params,url,category):
    logger.info("[megalivewall.py] listfavorites")
    
    itemlist = getlistfavorites(params,url,category)
    if len(itemlist)>0:
        xbmctools.renderItems(itemlist, params, url, category,isPlayable='true')

def listchannel(params,url,category):
    logger.info("[megalivewall.py] listchannel")
    
    itemlist = getlistchannel(params,url,category)
    xbmctools.renderItems(itemlist, params, url, category,isPlayable='true')

def playByID(params,url,category):
    logger.info("[megalivewall.py] listchannel")
    
    itemlist = getplayByID(params,url,category)
    if len(itemlist)>0:
        xbmctools.renderItems(itemlist, params, url, category,isPlayable='true')    
    
def getplayByID(params,url,category):
    logger.info("[megalivewall.py] plyByID")
    tecleado = ""
    default = ""
    itemlist = []
    tecleado = string.upper(teclado(heading=config.get_localized_string(30405)))
    if len(tecleado)>0:
        url,thumbnail = megalive.getLiveUrl(tecleado,1)
        if len(url)>0:
            itemlist.append( Item(channel=CHANNELNAME, action="play" , title=tecleado , url=tecleado, thumbnail=thumbnail, plot="", show = tecleado, folder=False , context = True))
    return itemlist
            
def getlistWall(params,url,category):
    logger.info("[megalivewall.py] getlistWall")
    
    if url=="":
        url="http://www.megalive.com/"
    encontrados = set()
    # Descarga la p·gina
    data = scrapertools.cachePage(url)
    patron = "flashvars.xmlurl = '([^']+)'"
    matches = re.compile(patron,re.DOTALL).findall(data)
    if len(matches)>0:
        xmlurl = urllib.unquote_plus(matches[0])
        #logger.info(data)
        #<image click_url="?v=7RJPHQN0" images="http://img6.megalive.com/f29efb78905a482f00dacb5f5e41e953.jpg^
        #http://img6.megalive.com/eecd5b9bda6035095ef672b7c5e6dd5a.jpg" description="Expansion Ixcan TV" time="" thumb="http://img6.megalive.com/568a3de4a6b15fddce5c0f9609334529.jpg" hq="1" icon="ml">
        # Extrae las entradas (carpetas)
        patron  = '<image click_url="\?v=([^"]+)".*?'
        patron += 'description="(?:([^"]+)|)" time="" '
        patron += 'thumb="([^"]+)" '
        patron += 'hq="([^"]+)"'
        data = scrapertools.cachePage(xmlurl)
        matches = re.compile(patron,re.DOTALL).findall(data)
        scrapertools.printMatches(matches)
        itemlist = []

        for match in matches:
            # Titulo
            if len(match[1])>0:
                scrapedtitle = decodeHtmlentities(match[1]).encode("utf-8")
            else:
                scrapedtitle = "(no title)"
            # URL
            if match[0] in encontrados:
                continue
            scrapedurl = match[0]
            encontrados.add(match[0])
            # Thumbnail
            scrapedthumbnail = match[2]
            # Argumento
            scrapedplot = ""
            if match[3]=="1":
                hq=" [HQ]"
            else:
                hq=""

            # Depuracion
            if (DEBUG):
                logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

            # AÒade al listado de XBMC
            #addnewvideo( CHANNELNAME , "play" , category ,"Directo", scrapedtitle+hq , scrapedurl , scrapedthumbnail , scrapedplot )
            itemlist.append( Item(channel=CHANNELNAME, action="play" , title=scrapedtitle , url=scrapedurl, thumbnail=scrapedthumbnail, plot=scrapedplot, show = scrapedtitle, folder=False , context = True))

        return itemlist


def getlistcategory(params,url,category):
    logger.info("[megalivewall.py] getlistcategory")
    
    data = scrapertools.cachePage(url)
    patron = 'flashvars\.subitems \= "([^"]+)"'
    matches = re.compile(patron,re.DOTALL).findall(data)
    itemlist = []
    if len(matches)>0:
        #All categories^javascript:pagenav('0','1','20');Producers^javascript:pagenav('1','1','20');Social^javascript:pagenav('2','1','20');Entertainment^javascript:pagenav('3','1','20');Gaming^javascript:pagenav('4','1','20');Sports^javascript:pagenav('5','1','20');News+%26+Events^javascript:pagenav('6','1','20');Nature^javascript:pagenav('7','1','20');Science+%26+Tech^javascript:pagenav('8','1','20');Education^javascript:pagenav('9','1','20')"
        subitems = [(part.split('^')[0]) for part in matches[0].split(';')]
        subitemorder = [(part.split('^')[0]) for part in matches[1].split(';')]
        '''
        datajson = "{'item':["
        for part in subitemorder:
            datajson = datajson +'"'+ part + '",'
        datajson = datajson.strip(",") + "]}"
        '''
        datajson = json.dumps(subitemorder)
        print datajson
        for count,item in enumerate(subitems):
            scrapedurl = url+ "&cat="+ str(count)
            item = item.replace("+%26+"," ")
            itemlist.append( Item(channel=CHANNELNAME, action="listOrderBy", title=item , url=scrapedurl  , folder=True , extra = datajson) )
            
        return itemlist

def listOrderBy(params,url,category):
    logger.info("[megalivewall.py] listOrderBy")
    datajson = urllib.unquote_plus( params.get("extradata") )
    print datajson
    itemOrderBy = eval("("+datajson+")")
    
    opciones = []
    print itemOrderBy
    for item in itemOrderBy:
        opciones.append(item)
    dia = xbmcgui.Dialog()
    seleccion = dia.select("Order By: ", opciones)
    logger.info("seleccion=%d" % seleccion)
    if seleccion==-1:
        return
    url = url + "&orderby="+str(seleccion)+"&limit=20"
    listchannel(params,url,category)
    
def getlistchannel(params,url,category):
    logger.info("[megalivewall.py] listchannel")
    data = scrapertools.cachePage(url)
    patron = '<div class="forms_div2">(.*?</div></div>)'
    matches = re.compile(patron,re.DOTALL).findall(data)
    print matches
    itemlist = []    
    for match in matches:
        try:
            scrapedthumbnail = re.compile(r'<img src="(.+?)"').findall(match)[0]
        except:
            scrapedthumbnail = ""
        try:
            hd = re.compile(r'<div class="(hd_indicator)"').findall(match)[0]
            hd = " [HQ]"
        except:
            hd = ""
        try:
            scrapedurl = re.compile(r'<a href="\?v=(.+?)"').findall(match)[0]
        except:
            continue
        try:
            scrapedtitle = re.compile(r'<div class="bl_thumb_fl1"><[^>]+>(.+?)</').findall(match)[0]
        except:
            scrapedtitle = ""
        
        scrapedplot = ""    
        if (DEBUG):
            logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")
        
            
        itemlist.append( Item(channel=CHANNELNAME, action="play" , title=scrapedtitle + hd , url=scrapedurl, thumbnail=scrapedthumbnail, plot=scrapedplot, show = scrapedtitle, folder=False , context = 1))
    return itemlist
    
def saveChannelFavorites(params,url,category):
    logger.info("[megalivewall.py] saveChannelFavorites")
    title = unicode( xbmc.getInfoLabel( "ListItem.Title" ), "utf-8" )
    thumbnail = urllib.unquote_plus( params.get("thumbnail") )
    plot = unicode( xbmc.getInfoLabel( "ListItem.Plot" ), "utf-8" )
    server = urllib.unquote_plus( params.get("server") )
    
    datajson = ""
    datadict = []
    '''
    {
        'title':'canal tv',
        'url':'LOLZY40W',
        'thumbnail':'xxxx',
        'plot':'xxxyyxxy'
        'category':'xxxxx',
        'server':'Directo'
    }
    '''
    if os.path.exists( file_path ):
        try:
            filejson = open( file_path )
            datadict = json.load(filejson)
            
        except ValueError, err:
            print "error: ",err
        filejson.close();
        #logger.info("datajson="+datajson)
    if len(datadict)>0:
        #datadict = json.loads(datajson)
        #datadict = eval("("+datajson+")")
        for count,item in enumerate(datadict):
            if repr(item["url"]) == repr(unicode(url)):
                del datadict[count]
                break
    datadict = [{"title"   : title,
                "url"      : url,
                "thumbnail": thumbnail,
                "plot"     : plot,
                "category" : category,
                "server"   : server
                }] + datadict
        
    #datajson = json.dumps(datadict,sort_keys=True, indent=4)
    outfile =     open(file_path,"w")
    json.dump(datadict,outfile,separators=(',',':'))
    outfile.flush()
    outfile.close()
    logger.info("Salvado y Grabado en " + file_path)
    
def deleteSavedChannel(params,url,category):
    logger.info("[megalivewall.py] deleteSavedChannel")
    datajson = ""
    datadict = []
    '''
    {
        'title':'canal tv',
        'url':'LOLZY40W',
        'thumbnail':'xxxx',
        'plot':'xxxyyxxy'
        'category':'xxxxx',
        'server':'Directo'
    '''
    if os.path.exists( file_path ):
        try:
            filejson = open( file_path )
            datadict = json.load(filejson)
        except ValueError, err:
            print "error: ",err            
        filejson.close();
        
    if len(datadict)>0:
        for count,item in enumerate(datadict):
            if repr(item["url"]) == repr(unicode(url)):
                del datadict[count]
                break
    #datajson = json.dumps(datadict,sort_keys=True, indent=4)
    outfile =     open(file_path,"w")
    json.dump(datadict,outfile,separators=(',',':'))
    outfile.flush()
    outfile.close()
    logger.info("Borrado y Grabado a " + file_path)
    # refresh container so item is removed
    xbmc.executebuiltin( "Container.Refresh" )

def renameChannelTitle(params,url,category):
    logger.info("[megalivewall.py] renameChannelTitle")
    title = unicode( xbmc.getInfoLabel( "ListItem.Title" ), "utf-8" )
    datajson = ""
    datadict = []
    '''
    {
        'title':'canal tv',
        'url':'LOLZY40W',
        'thumbnail':'xxxx',
        'plot':'xxxyyxxy'
        'category':'xxxxx',
        'server':'Directo'
    '''
    if os.path.exists( file_path ):
        try:
            filejson = open( file_path )
            datadict = json.load(filejson)
        except ValueError, err:
            print "error: ",err        
        filejson.close();
        
    tecleado = teclado(title)
    if len(tecleado)>0:
        if len(datadict)>0:
            for count,item in enumerate(datadict):
                if repr(item["url"]) == repr(unicode(url)):
                    url2,thumbnail = megalive.getLiveUrl(url,1)
                    if len(thumbnail)>0:
                        item["thumbnail"]= unicode(thumbnail)
                    item["title"] = unicode(tecleado)
                    break
            outfile =     open(file_path,"w")
            json.dump(datadict,outfile,separators=(',',':'))
            outfile.flush()
            outfile.close()
            logger.info("Renombrado y Grabado en " + file_path)
            # refresh container so item is renamed
            xbmc.executebuiltin( "Container.Refresh" )
        
def play_fav(params,url,category):
    play(params,url,category)
    
def play(params,url,category):
    
    icon = "DefaultVideo.png"
    title = unicode( xbmc.getInfoLabel( "ListItem.Title" ), "utf-8" )
    thumbnail = urllib.unquote_plus( params.get("thumbnail") )
    plot = unicode( xbmc.getInfoLabel( "ListItem.Plot" ), "utf-8" )
    action = params.get("action")
    livelink,thumbnail = megalive.getLiveUrl(url,1)
    if len(livelink)<=0:
        
        print "Error de conexion: "+livelink
        
    else:
        if action == "play_fav":
            params["thumbnail"] = urllib.quote_plus(thumbnail)
            saveChannelFavorites(params,url,category)
        item=xbmcgui.ListItem(title, iconImage=icon, thumbnailImage=thumbnail, path=livelink)
        item.setInfo( type="Video",infoLabels={ "Title": title, "Plot": plot})
        item.setProperty('IsPlayable', 'true')
        xbmcplugin.setResolvedUrl(pluginhandle, True, item)

def getlistfavorites(params,url,category):
    logger.info("[megalivewall.py] getlistfavorites")
    datadict = ""
    itemlist = []
    print file_path
    if os.path.exists( file_path ):
        try:
            filejson = open( file_path )
            datadict = json.load(filejson)
        except ValueError, err:
            print "error: ",err    
        filejson.close();
        
    if len(datadict)>0:
        for item in datadict:
            itemlist.append( Item(channel=CHANNELNAME, action="play_fav" , title=item["title"] , url=item["url"], thumbnail=item["thumbnail"], plot=item["plot"], show = item["title"], folder=False , context = 2))
        return itemlist
    else:
            return ""
def addnewvideo( canal , accion , category , server , title , url , thumbnail, plot ,Serie=""):
    if DEBUG:
        try:
            logger.info('[xbmctools.py] addnewvideo( "'+canal+'" , "'+accion+'" , "'+category+'" , "'+server+'" , "'+title+'" , "' + url + '" , "'+thumbnail+'" , "'+plot+'")" , "'+Serie+'")"')
            title = title.encode("utf-8")
        except:
            logger.info('[xbmctools.py] addnewvideo(<unicode>)')
    listitem = xbmcgui.ListItem( title, iconImage="DefaultVideo.png", thumbnailImage=thumbnail )
    listitem.setInfo( "video", { "Title" : title, "Plot" : plot, "Studio" : canal } )
    listitem.setProperty('IsPlayable', 'true')
    
    itemurl = '%s?channel=%s&action=%s&category=%s&title=%s&url=%s&thumbnail=%s&plot=%s&server=%s&Serie=%s' % ( sys.argv[ 0 ] , canal , accion , urllib.quote_plus( category ) , urllib.quote_plus( title ) , urllib.quote_plus( url ) , urllib.quote_plus( thumbnail ) , urllib.quote_plus( plot ) , server , Serie)
    #logger.info("[xbmctools.py] itemurl=%s" % itemurl)
    xbmcplugin.addDirectoryItem( handle = pluginhandle, url=itemurl, listitem=listitem, isFolder=False)

def teclado(default="", heading="", hidden=False):
    tecleado = ""
    keyboard = xbmc.Keyboard(default,heading,hidden)
    keyboard.doModal()
    if (keyboard.isConfirmed()):
        tecleado = keyboard.getText()
        if len(tecleado)<=0:
            return ""
    
    return tecleado


def decodeHtmlentities(string):
    import re
    entity_re = re.compile("&(#?)(\d{1,5}|\w{1,8});")

    def substitute_entity(match):
        from htmlentitydefs import name2codepoint as n2cp
        ent = match.group(2)
        if match.group(1) == "#":
            return unichr(int(ent))
        else:
            cp = n2cp.get(ent)

            if cp:
                return unichr(cp)
            else:
                return match.group()

    return entity_re.subn(substitute_entity, string)[0]