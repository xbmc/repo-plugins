# -*- coding: utf-8 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para seriesdanko.com
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#------------------------------------------------------------
import urlparse,urllib2,urllib,re
import os, sys
import xbmc,xbmcplugin
from core import scrapertools,xbmctools
from servers import servertools
from core import logger,config
from pelisalacarta import buscador
from core.item import Item
from xml.dom import minidom
from xml.dom import EMPTY_NAMESPACE
from platform.xbmc.config import  get_system_platform

PLUGIN_NAME = "pelisalacarta"
CHANNELNAME = "seriesdanko"
ATOM_NS = 'http://www.w3.org/2005/Atom'
DEBUG = config.get_setting("debug")

if get_system_platform() == "xbox":
    MaxResult = "55"
else:
    MaxResult = "500"


def isGeneric():
    return True

def mainlist(item):
    logger.info("[seriesdanko.py] mainlist")

    
    itemlist = []
    itemlist.append( Item(channel=CHANNELNAME, title="Noticias"       , action="novedades"   , url="http://www.blogger.com/feeds/5090863330072217342/posts/default/-/Noticias?start-index=1&max-results=25&orderby=published&alt=json&callback=nuevoscapitulos"))
    itemlist.append( Item(channel=CHANNELNAME, title="Series Actualizadas"    , action="listvideofeeds", url="http://www.blogger.com/feeds/5090863330072217342/posts/default/-/sd?start-index=1&max-results=%s" %MaxResult))
    itemlist.append( Item(channel=CHANNELNAME, title="Lista Alfanumerica" , action="ListByLetters", url="http://www.seriesdanko.com/documentales/"))
    itemlist.append( Item(channel=CHANNELNAME, title="Listado completo"    , action="allserieslist", url="http://www.seriesdanko.com"))
    
    return itemlist

def listvideofeeds(item):
    logger.info("[seriesdanko.py] listvideosfeeds")

    url = item.url
    data = None
    thumbnail = ""
    plot = ""
    xmldata = urllib2.urlopen(url,data)
    
    xmldoc = minidom.parse(xmldata)
    xmldoc.normalize()
    #print xmldoc.toxml().encode('utf-8')
    xmldata.close()
    c = 0
    itemlist = []
    totalitems = len(xmldoc.getElementsByTagNameNS(ATOM_NS, u'entry'))
    for entry in xmldoc.getElementsByTagNameNS(ATOM_NS, u'entry'):
    #First title element in doc order within the entry is the title
        entrytitle = entry.getElementsByTagNameNS(ATOM_NS, u'title')[0]
        entrylink = entry.getElementsByTagNameNS(ATOM_NS, u'link')[2]
        entrythumbnail = entry.getElementsByTagNameNS(ATOM_NS, u'content')[0]
        etitletext = get_text_from_construct(entrytitle) 
        elinktext = entrylink.getAttributeNS(EMPTY_NAMESPACE, u'href')+ "?alt=json"
        ethumbnailtext = get_text_from_construct(entrythumbnail)
        regexp = re.compile(r'src="([^"]+)"')
        match = regexp.search(ethumbnailtext)
        if match is not None:
            thumbnail = match.group(1)


        regexp = re.compile(r'(Informac.*?/>)</div>')
        match = regexp.search(ethumbnailtext)
        print ethumbnailtext
        if match is not None:
            try:
                eplot = re.compile(r'(Informac.*?/>)</div>').findall(match.group(1))
                eplot = re.sub('<[^>]+>'," ",eplot)
            except:
                eplot = re.sub('<[^>]+>'," ",match.group(1))
        else:
            eplot = ""
        etitletext = etitletext.replace("Lista de capitulos de","")
        etitletext = etitletext.replace("Lista de Capitulos de","")
        etitletext = etitletext.replace("Lista de Capitulos","")
        etitletext = etitletext.replace("Lista de capitulos","")
        etitletext = etitletext.replace("Lista de Capitulo de ","")
        etitletext = etitletext.replace("Lista de Capitulo","")
        etitletext = etitletext.replace(":","").strip()
        
        
        # Depuracion
        if (DEBUG):
            logger.info("scrapedtitle="+etitletext)
            logger.info("scrapedurl="+elinktext)
            logger.info("scrapedthumbnail="+thumbnail)
                
        #print etitletext, '(', elinktext, thumbnail,plot, ')'
        #xbmctools.addnewfolder( CHANNELNAME , "detail" , category ,  etitletext,  elinktext, thumbnail, plot )
        itemlist.append( Item(channel=CHANNELNAME, action="capitulos" ,category = "Tv show",  title=etitletext , url=elinktext, thumbnail=thumbnail, plot=eplot, extra=ethumbnailtext, totalItems = totalitems))
        c +=1
    
    if c >= MaxResult:
        regexp = re.compile(r'start-index=([^\&]+)&')
        match = regexp.search(url)
        if match is not None:
            start_index = int(match.group(1)) + MaxResult
        scrapedtitle = "Página siguiente"
        scrapedurl =  "http://www.blogger.com/feeds/5090863330072217342/posts/default?start-index="+str(start_index)+"&max-results=%s" %MaxResult
        scrapedthumbnail = ""
        scrapedplot = ""
        #xbmctools.addnewfolder( CHANNELNAME , "listvideofeeds" , category , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )
        itemlist.append( Item(channel=CHANNELNAME, action="listvideofeeds", title=scrapedtitle , url=scrapedurl , folder=True, totalItems = totalitems + 1) )

    if config.get_setting("forceview")=="true":
        xbmc.executebuiltin("Container.SetViewMode(53)")  #53=icons    
    return itemlist


    
def get_text_from_construct(element):
    '''
    Return the content of an Atom element declared with the
    atomTextConstruct pattern.  Handle both plain text and XHTML
    forms.  Return a UTF-8 encoded string.
    '''
    if element.getAttributeNS(EMPTY_NAMESPACE, u'type') == u'xhtml':
        #Grab the XML serialization of each child
        childtext = [ c.toxml('utf-8') for c in element.childNodes ]
        #And stitch it together
        content = ''.join(childtext).strip()
        return content
    else:
        return element.firstChild.data.encode('utf-8')


def novedades(item):
    logger.info("[seriesdanko.py] novedades")
    

    # Descarga la página
    data = scrapertools.downloadpageGzip(item.url)
    data = data.replace("nuevoscapitulos","")
    data = data.replace(";","")
    datadict = eval( data  )
    url = item.url
    #print datadict

    extra = ""
    itemlist = []
    totalItems = len(datadict["feed"]["entry"])
    for entry in datadict["feed"]["entry"]:
        scrapedtitle = entry["title"]["$t"]
        content = urllib.unquote_plus(entry["content"]["$t"].replace("\\u00","%"))
        
        #print content
        
        try:
            scrapedthumbnail = re.compile(r'src="(.+?)"').findall(content)[0]
        except:
            scrapedthumbnail = ""
        try:
            scrapedplot = re.compile(r'<b>(.+?)</span>').findall(content)[0]
            scrapedplot = re.sub("<[^>]+>"," ",scrapedplot)
        except:
            scrapedplot = ""
        try:
            scrapedurl = re.compile(r'href="(.+?)"').findall(content)[0]
            
        except:
            try:
                scrapedurl = entry["link"][4]["href"]
            except:
                scrapedurl =""
    
            
        if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

        # Añade al listado de XBMC
        itemlist.append( Item(channel=CHANNELNAME, action="capitulos", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , extra = extra , folder=True , totalItems = totalItems ) )
        

    # Extrae el paginador
    if len(itemlist) >= 25:
        regexp = re.compile(r'start-index=([^\&]+)&')
        match = regexp.search(url)
        if match is not None:
            start_index = int(match.group(1)) + 25
        scrapedtitle = "Página siguiente"
        scrapedurl =  "http://www.blogger.com/feeds/5090863330072217342/posts/default/-/Noticias?start-index="+str(start_index)+"&max-results=25&orderby=published&alt=json&callback=nuevoscapitulos"
        scrapedthumbnail = ""
        scrapedplot = ""
        #xbmctools.addnewfolder( CHANNELNAME , "listvideofeeds" , category , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )
        itemlist.append( Item(channel=CHANNELNAME, action="novedades", title=scrapedtitle , url=scrapedurl , folder=True, totalItems = len(itemlist) + 1) )


    return itemlist

def ListByLetters(item):
    logger.info("[seriesdanko.py] ListByLetter")
    
    BaseChars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    BaseUrl   = "http://www.blogger.com/feeds/5090863330072217342/posts/default/-/%s?max-results=200&alt=json"
    itemlist = []
    itemlist.append( Item(channel=CHANNELNAME, action="ListVideos", title="0-9" , url=BaseUrl % "0-9" , thumbnail="" , plot="" , folder=True) )
    for letra in BaseChars:
        scrapedtitle = letra
        scrapedplot = ""
        scrapedurl = BaseUrl % letra
        scrapedthumbnail = ""
        if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

        # Añade al listado de XBMC
        itemlist.append( Item(channel=CHANNELNAME, action="ListVideos", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )

    return itemlist
def allserieslist(item):
    logger.info("[seriesdanko.py] allserieslist")

    Basechars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    BaseUrl   = "http://www.blogger.com/feeds/5090863330072217342/posts/default/-/%s?max-results=200&alt=json"
    itemlist = []

    # Descarga la página
    data = scrapertools.downloadpageGzip(item.url)
    #logger.info(data)

    # Extrae el bloque de las series
    patronvideos = "Listado de series disponibles</h2>(.*?)<div class='clear'></div>"
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    data = matches[0]
    scrapertools.printMatches(matches)

    # Extrae las entradas (carpetas)
    patronvideos  = "<a href='([^']+)'>([^<]+)</a>"
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)
    totalItems = len(matches)
    for url,title in matches:
        scrapedtitle = title
        scrapedurl = "http://www.blogger.com/feeds/5090863330072217342/posts/default/-/%s?alt=json|%s" % (title.strip(),url)
        scrapedthumbnail = ""
        scrapedplot = ""

        if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")
        if title in Basechars or title == "0-9":
            action = "ListVideos"
            scrapedurl = BaseUrl % title
        else:
            action = "capitulos"

        # Añade al listado de XBMC
        itemlist.append( Item(channel=CHANNELNAME, action=action , title=scrapedtitle , url=scrapedurl, thumbnail=scrapedthumbnail, plot=scrapedplot, show = scrapedtitle , totalItems = totalItems))

    return itemlist
def ListVideos(item):
    logger.info("[seriesdanko.py] ListVideos")
    
    # Descarga la página
    data = scrapertools.downloadpageGzip(item.url)
    datadict = eval( "(" + data + ")" )    
    data = urllib.unquote_plus(datadict["feed"]["entry"][0]["content"]["$t"].replace("\\u00","%"))
    data = data.replace("'",'"')
    print data
    patronvideos = '<a.+?href="([^"]+)"(.+?</a>)'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    itemlist = []
    for url,info in matches:
        try:
            scrapedtitle = re.compile('alt="(.+?)"').findall(info)[0]
        except:
            try:
                scrapedtitle = re.compile('<br />(.+?)</a>').findall(info)[0]
            except:
                scrapedtitle = ""
        try:
            scrapedthumbnail = re.compile('src="(.+?)"').findall(info)[0]
        except:
            scrapedthumbnail = ""

        scrapedplot = ""
        scrapedtitle = scrapedtitle.replace(",","")
        scrapedtitle = scrapedtitle.replace("online","")
        scrapedtitle = scrapedtitle.replace("Csi","CSI")
        scrapedurl = "http://www.blogger.com/feeds/5090863330072217342/posts/default/-/%s?alt=json|%s" % (scrapedtitle.strip(),url)
        
        if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

        # Añade al listado de XBMC
        itemlist.append( Item(channel=CHANNELNAME, action="capitulos", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )
        
    
    #print datalist
    return itemlist


def capitulos(item):
    logger.info("[seriesdanko.py] capitulos")
    
    if config.get_setting("forceview")=="true":
        xbmc.executebuiltin("Container.SetViewMode(53)")  #53=icons
        #xbmc.executebuiltin("Container.Content(Movies)")
        
    if "|" in item.url:
        url = item.url.split("|")[0]
        sw = True
    else:
        url = item.url
        sw = False
    # Descarga la página
    if item.extra:
        
        contenidos = item.extra
        #print contenidos
    else:
        data = scrapertools.downloadpageWithoutCookies(url)

    # Extrae las entradas
        if sw:
            try:
                datadict = eval( "(" + data + ")" )    
                data = urllib.unquote_plus(datadict["feed"]["entry"][0]["content"]["$t"].replace("\\u00","%"))
                #data = urllib.unquote_plus(data.replace("\u00","%")).replace('\\"','"')
                #patronvideos  = "content(.*?)post-footer"
                matches=[]
                matches.append(data)
            except:
                matches = []
        else:
            patronvideos = "entry-content(.*?)</div>"
            matches = re.compile(patronvideos,re.DOTALL).findall(data)
            
        if len(matches)>0:
            contenidos = matches[0]
        else:
            contenidos = item.url
            if sw:
                url = item.url.split("|")[1]
                # Descarga la página
                data = scrapertools.downloadpageGzip(url)
                patronvideos  = "entry-content(.*?)<div class='post-footer'>"
                matches = re.compile(patronvideos,re.DOTALL).findall(data)
                if len(matches)>0:
                    contenidos = matches[0]
                
    patronvideos  = '<a href="([^"]+)">([^<]+)</a>.*?src="([^"]+)"'
    matches = re.compile(patronvideos,re.DOTALL).findall(contenidos.replace("'",'"'))
    #print contenidos        
    try:
        plot = re.compile(r'(Informac.*?/>)</div>').findall(contenidos)[0]
        if len(plot)==0:
            plot = re.compile(r"(Informac.*?both;'>)</div>").findall(contenidos)[0]
        plot = re.sub('<[^>]+>'," ",plot)
    except:
        plot = ""

    itemlist = []
    for match in matches:
        scrapedtitle = match[1]
        if "es.png" in match[2]:
            subtitle = " (Español)"
        elif "la.png" in match[2]:
            subtitle = " (Latino)"
        elif "vo.png" in match[2]:
            subtitle = " (Version Original)"
        elif "vos.png" in match[2]:
            subtitle = " (Subtitulado)"
        else:
            subtitle = ""
        scrapedplot = plot
        scrapedurl = urlparse.urljoin(item.url,match[0])
        if not item.thumbnail:
            try:
                scrapedthumbnail = re.compile(r'src="(.+?)"').findall(contenidos)[0]
            except:
                scrapedthumbnail = ""
        else:
            scrapedthumbnail = item.thumbnail
        if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

        # Añade al listado de XBMC
        itemlist.append( Item(channel=CHANNELNAME, action="findvideos", title=scrapedtitle+subtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )
    
    #xbmc.executebuiltin("Container.Content(Movies)")
    
    
    if len(itemlist)==0:
        listvideos = servertools.findvideos(contenidos)
        
        for title,url,server in listvideos:
            
            if server == "youtube":
                scrapedthumbnail = "http://i.ytimg.com/vi/" + url + "/0.jpg"
            else:
                scrapedthumbnail = item.thumbnail
            scrapedtitle = title
            scrapedplot = ""
            scrapedurl = url
            
            if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

            # Añade al listado de XBMC
            xbmctools.addnewvideo( CHANNELNAME , "play" , "" , server , item.title +" "+ scrapedtitle , scrapedurl , scrapedthumbnail , scrapedplot )
                
    return itemlist
    


    
def capitulos2(item):
    logger.info("[seriesdanko.py] capitulos")
    
    # Descarga la página
    url = item.url.split("|")[0]
    data = scrapertools.downloadpageGzip(url)
    # Convertimos los datos en json a diccionario
    datadict = eval( '(' + data + ')' )    
    #print datadict
    matches = []
    itemlist = []
    for match in matches:
        scrapedtitle = match[1]
        scrapedplot = ""
        scrapedurl = urlparse.urljoin(item.url,match[0])
        scrapedthumbnail = item.thumbnail
        if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

        # Añade al listado de XBMC
        itemlist.append( Item(channel=CHANNELNAME, action="findvideos", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )    
    return itemlist
    

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
# addon_path is this plugins path. i.e. plugin://plugin.video.myplugin/

