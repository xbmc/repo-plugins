# -*- coding: utf-8 -*-
import cookielib
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

import xbmc
import xbmcgui
import xbmcplugin

CHANNELNAME = "vagos"
BASEURL = "http://www.vagos.es/"

USER = config.get_setting("privateuser")
PASSWORD = config.get_setting("privatepassword")

#La cookie se ha de ubicar en un sitio con permiso de lectura/escritura
COOKIEFILE = os.path.join(config.get_data_path(),"vagos.cookies")

####################################################
# COKIES
####################################################
# Cookie jar. Stored at the user's home folder.
cookie_jar = cookielib.LWPCookieJar(COOKIEFILE)
try:
    cookie_jar.load()
except Exception:
    pass

try:
    pluginhandle = int( sys.argv[ 1 ] )
except:
    pluginhandle = ""
   

DEBUG = True 
def mainlist(params,url,category):
    try:
        Login()
    except Exception:
        pass
    
    logger.info("[Vagos.py] mainlist")

    xbmctools.addnewfolder( CHANNELNAME , "NoParse" , category , "Peliculas - Hasta el 2008 (Inclusive)","http://www.vagos.es/forumdisplay.php?f=455","","")
    xbmctools.addnewfolder( CHANNELNAME , "NoParse" , category , "Peliculas - 2009/2010","http://www.vagos.es/forumdisplay.php?f=454","","")
    xbmctools.addnewfolder( CHANNELNAME , "Parse" , category , "Series - Temporadas completas" ,"http://www.vagos.es/forumdisplay.php?f=365","","")
    xbmctools.addnewfolder( CHANNELNAME , "Parse" , category , "Series - Temporadas en transmisión o incompletas","http://www.vagos.es/forumdisplay.php?f=364","","")
    xbmctools.addnewfolder( CHANNELNAME , "NoParse" , category , "Series - Capítulos sueltos","http://www.vagos.es/forumdisplay.php?f=372","","")

    xbmctools.addnewfolder( CHANNELNAME , "NoParse" , category , "Otros Videos","http://www.vagos.es/forumdisplay.php?f=363","","")
    xbmctools.addnewfolder( CHANNELNAME , "NoParse" , category , "Trailers","http://www.vagos.es/forumdisplay.php?f=456","","")
    xbmctools.addnewfolder( CHANNELNAME , "search", "" , "Buscador...","http://compras.vagos.es/share-cgi/search.ftcb","","")

    '''
    xbmctools.addnewfolder( CHANNELNAME , "Parse" , category , "Dibujos Castellano" ,"http://www.vagos.es/forumdisplay.php?f=289","","")
    xbmctools.addnewfolder( CHANNELNAME , "Parse" , category , "Dibujos Castellano - Temporadas completas" ,"http://www.vagos.es/forumdisplay.php?f=309","","")
    xbmctools.addnewfolder( CHANNELNAME , "Parse" , category , "Dibujos Latino" ,"http://www.vagos.es/forumdisplay.php?f=288","","")
    xbmctools.addnewfolder( CHANNELNAME , "Parse" , category , "Dibujos Latino - Temporadas completas" ,"http://www.vagos.es/forumdisplay.php?f=310","","")
    xbmctools.addnewfolder( CHANNELNAME , "Parse" , category , "Dibujos Otros Idiomas" ,"http://www.vagos.es/forumdisplay.php?f=290","","")
    xbmctools.addnewfolder( CHANNELNAME , "Parse" , category , "Dibujos Otros Idiomas - Temporadas completas" ,"http://www.vagos.es/forumdisplay.php?f=307","","")
    xbmctools.addnewfolder( CHANNELNAME , "Parse" , category , "Anime Castellano" ,"http://www.vagos.es/forumdisplay.php?f=292","","")
    xbmctools.addnewfolder( CHANNELNAME , "Parse" , category , "Anime Castellano - Temporadas completas" ,"http://www.vagos.es/forumdisplay.php?f=303","","")
    xbmctools.addnewfolder( CHANNELNAME , "Parse" , category , "Anime Latino" ,"http://www.vagos.es/forumdisplay.php?f=291","","")
    xbmctools.addnewfolder( CHANNELNAME , "Parse" , category , "Anime Latino - Temporadas completas" ,"http://www.vagos.es/forumdisplay.php?f=305","","")
    xbmctools.addnewfolder( CHANNELNAME , "Parse" , category , "Anime Otros Idiomas" ,"http://www.vagos.es/forumdisplay.php?f=293","","")
    xbmctools.addnewfolder( CHANNELNAME , "Parse" , category , "Anime Otros Idiomas - Temporadas completas" ,"http://www.vagos.es/forumdisplay.php?f=312","","")
    '''
    
    # Propiedades
    xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
    xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

def Parse(params,url,category):
    Foro(params,url,category,True)
    return
    
def NoParse(params,url,category):
    Foro(params,url,category,False)
    return

def search(params,url,category):
    logger.info("[Vagos.py] search")

    keyboard = xbmc.Keyboard('')
    keyboard.doModal()
    xbmctools.addnewfolder( CHANNELNAME , "search", "" , "Buscador...","http://compras.vagos.es/share-cgi/search.ftcb","","")
        
    if (keyboard.isConfirmed()):
        tecleado = keyboard.getText()
        if len(tecleado)>0:
            #convert to HTML
            tecleado = tecleado.replace(" ", "+")
            data = Search(tecleado)
            # Extrae las entradas (carpetas)
            patron = '<a href="([^"]+)" id="thread_title_([^"]+)">([^<]+)</a>'
            matches = re.compile(patron,re.DOTALL).findall(data)
            
            for match in matches:
                # Atributos
                scrapedurl = BASEURL + match[0]
                scrapedtitle = match[2]
                scrapedthumbnail = ""            
                scrapedplot = ""
                
                xbmctools.addnewfolder( CHANNELNAME , "SerieScan" , category , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )
                
    # Propiedades
    xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
    xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )     
      
            
def Foro(params,url,category,parse):
    logger.info("[Vagos.py] Vagos")

    try:
        data = get_page(url)
        
        chinchetas = MensajesChincheta(data)
        
        # Extrae las entradas (carpetas)
        patron = '<a href="([^"]+)" '
        patron += 'id="thread_title_([^"]+)".*?>([^<]+)</a>'
        matches = re.compile(patron,re.DOTALL).findall(data)

        for match in matches:
            # Atributos
            scrapedurl = BASEURL + match[0]
            scrapedtitle = match[2]
            scrapedthumbnail = ""            
            scrapedplot = ""
            if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")
    
            if match[1] not in chinchetas:
                # Añade al listado de XBMC
                if(parse):
                    xbmctools.addnewfolder( CHANNELNAME , "SerieScan" , category , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )
                else:
                    xbmctools.addnewfolder( CHANNELNAME , "MovieScan" , category , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )
            
            
        # Extrae la marca de siguiente pagina
        pnextp = '<a rel="next" class="smallfont" href="forumdisplay.php?f=.*page=(\d*)" title'
        pnextp = '<a rel="next" class="smallfont" href="([^"]+)" title'
        matches = re.compile(pnextp,re.DOTALL).findall(data)
        scrapertools.printMatches(matches)
    
        if len(matches)>0:
            scrapedtitle = "Página siguiente"
            replaced = str(matches[0]).replace("&amp;", "&")
            scrapedurl = urlparse.urljoin(url,replaced)        
            #scrapedurl = BASEURL + "forumdisplay.php?f="+matches[0][0]+"&order=desc&page="+matches[0][1]
            scrapedthumbnail = ""
            scrapedplot = ""
            if(parse):
                xbmctools.addnewfolder( CHANNELNAME , "Parse" , category , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot ) 
            else:
                xbmctools.addnewfolder( CHANNELNAME , "NoParse" , category , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )
    
    except Exception:
        pass  
    
      
    # Propiedades
    xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
    xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )


def SerieScan(params,url,category):
    try:
        data = get_page(url)
        
        #Intentamos filtrar y solo parsear el primer post
        messages =re.compile("<!-- message -->.*?<!-- / message -->", re.S).findall(data)
        if (len(messages)>0):
            for message in messages:
                data = message
                break
                
        title = urllib.unquote_plus( params.get("title") )      
        imagen = findimage (data)
                
        videos = findvideos(data,True)    
        if(len(videos)>0):
            numvideo=0
            for video in videos:
                if(len(str(video[0]))<=0):
                    numvideo+=1
                    try:
                        vtitle = title.split("[")[0]
                    except:
                        vtitle = title
                    if (len(videos)>1):
                        vtitle= str(numvideo) + ".- " + vtitle 
                    #vtitle=" [" + video[1] + "]"                   
                else:
                    vtitle = video[0] #+ " [" + video[1] + "]"
                
                xbmctools.addnewvideo( CHANNELNAME , "play" , category , video[2] , vtitle +" ["+video[2]+"]", video[1] , imagen , "" )
    except:
        printText("Error al obtener videos de" + title)    
           
    # Propiedades
    xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
    xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )   
    
def MovieScan(params,url,category):
    try:
        data = get_page(url)
        
        #Intentamos filtrar y solo parsear el primer post
        messages =re.compile("<!-- message -->.*?<!-- / message -->", re.S).findall(data)
        if (len(messages)>0):
            for message in messages:
                data = message
                break
                
        title = urllib.unquote_plus( params.get("title") )      
        imagen = findimage (data)
                
        videos = findvideos(data,False)    
        if(len(videos)>0):
            numvideo=0
            for video in videos:
                numvideo+=1
                if(len(videos)>1):
                    vtitle= str(numvideo) + ".- " + title
                else:
                    vtitle=title
                                
                xbmctools.addnewvideo( CHANNELNAME , "play" , category , video[2] , vtitle +" ["+video[2]+"]", video[1] , imagen , "" )
    except:
        printText("Error al obtener videos de" + title)    
           
    # Propiedades
    xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
    xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )   


def play(params,url,category):
    logger.info("[vagos.py] play")
    
    title = ""#unicode( xbmc.getInfoLabel( "ListItem.Title" ), "utf-8" )
    thumbnail = ""#urllib.unquote_plus( params.get("thumbnail") )
    plot = "" #unicode( xbmc.getInfoLabel( "ListItem.Plot" ), "utf-8" )
    server = params["server"]
   
   
    xbmctools.playvideo(CHANNELNAME,server,url,category,title,thumbnail,plot)
    return

#Devuelve el SECURITYTOKEN del codigo WEB recibido   
def SecurityTOKEN(data):
    ptoken = 'var SECURITYTOKEN = "([^"]+)";'
    matches = re.compile(ptoken,re.DOTALL).findall(data)
    if len(matches)<=0:
        return ''
        
    for match in matches:
        return str(match)  
def CurrentSecurityTOKEN():
    data = get_page(BASEURL+"index.php")
    token= SecurityTOKEN(data)
    return token


#La uso para imprimir texto por el plugin =D    
def printText(txt):
    lines = txt.split('\n')
    for line in lines:
        xbmctools.addnewfolder( CHANNELNAME , "Test" , '' ,line.strip(),"","","")
    return

# Request the given URL and return the response page, sin usar the cookie jar
def get_ExternalPage(url):
    request = urllib2.Request(url)
    request.add_header('User-Agent', 'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.0)')
    response = urllib2.urlopen(request)
    html = response.read()
    response.close()
    return html

# Request the given URL and return the response page, using the cookie jar
def get_page(url):
    request = urllib2.Request(url)
    request.add_header('User-Agent', 'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.0)')
    cookie_jar.add_cookie_header(request)
    response = urllib2.urlopen(request)
    cookie_jar.extract_cookies(response, request)
    html = response.read()
    response.close()
    cookie_jar.save()
    return html

def Search(text):
    token = CurrentSecurityTOKEN()
    
    url = 'http://www.vagos.es/search.php'
    values = {'do' : 'process',
          's' : '',
          'securitytoken' : token,
          'searchthreadid' : '',
          'query' : text,
          'titleonly' : '1',
          'searchuser' : '',
          'starteronly' : '0',
          'exactname' : '1',
          'replyless' : '0',
          'replylimit' : '0',
          'searchdate' : '0',
          'beforeafter' : 'after',
          'sortby' : 'lastpost',
          'order' : 'descending',
          'showposts' : '0',
          'childforums' : '1',
          'dosearch' : 'Buscar Ahora',
          'saveprefs' :'1',
          'forumchoice[]': ['355', '356']}

    search_data = urllib.urlencode(values,doseq=True)
    request = urllib2.Request(url,search_data)
    request.add_header('User-Agent', 'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.0)')
    cookie_jar.add_cookie_header(request)
    response = urllib2.urlopen(request)
    cookie_jar.extract_cookies(response, request)
    html = response.read()
    response.close()
    cookie_jar.save()
    
    psearch = 'searchid=([^"]+)">'
    matches = re.compile(psearch,re.DOTALL).findall(str(html))
    for match in matches:
        return get_page(BASEURL+'search.php?searchid='+match)
    return ''

# Request the given URL and return the response page, using the cookie jar
def Login():
    url = 'http://www.vagos.es/login.php'
    values = {'vb_login_username' : USER,
          'cookieuser' : '1',
          'vb_login_password' : PASSWORD,
          'securitytoken' : 'guest',
          'do' : 'login',
          'vb_login_md5password' : '',
          'vb_login_md5password_utf' : ''}
    login_data = urllib.urlencode(values)
    request = urllib2.Request(url,login_data)
    request.add_header('User-Agent', 'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.0)')
    cookie_jar.add_cookie_header(request)
    response = urllib2.urlopen(request)
    cookie_jar.extract_cookies(response, request)
    html = response.read()
    response.close()
    cookie_jar.save()
    return html

def cf(temp, cap):
    try:
        tt = '%(#)02d' % \
              {"#": int(temp)}
        cc = '%(#)02d' % \
              {"#": int(cap)}
    except:
        return cap
    
    return tt + "x" + cc
   
def findHayshirVideos(devuelve,encontrados,data,temp):
    
    prevcap=0
    title=""
    
    ##COMPLEJO
    logger.info ("Estilo Hayshir (Reverse)")
    pchap = '(.*?)<a href="http://www.mega([^"]+)" target="_blank">([^<]+)</a>'
    cmatches =re.compile(pchap, re.S).findall(data)
    for cdata in cmatches: 
        #tenemos el link y lo anterior
        pinfo = '<font color="DarkOrange"><b>([^ ]+) ([^<]+)</b>.*?<font color="RoyalBlue">([^<]+)</font>'
        imatches =re.compile(pinfo, re.S).findall(cdata[0])
        for cinfo in imatches:
            title = cf(temp,cinfo[1]) + " - " + cinfo[2]
            break
        
        ctitle=title
        pinfo = '<font color="DarkRed">([^<]+)</font>'
        imatches =re.compile(pinfo, re.S).findall(cdata[0])
        for cinfo in imatches:
            ctitle=title + " (" + cinfo + ")"
            AddVideoURL(devuelve,encontrados,ctitle,cdata[2])
            break   
    
    ##PARSER BASE 
    logger.info ("Estilo Hayshir (Base)")
    patronvideos = '<font color="DarkOrange"><b>(.*?)(\d*)</b>.*?<font color="RoyalBlue">([^<]+)</font>.*?<a href="http://www.mega([^"]+)" target="_blank">([^<]+)</a>'
    matches =re.compile(patronvideos, re.S).findall(data)
    for match in matches:        
        if(int(prevcap)>int(match[1])):                
            temp+=1        
        prevcap=int(match[1]) 
        title = cf(temp,match[1]) + " - " + match[2]
        AddVideoURL(devuelve,encontrados,title,match[4])
        
        
    return 

def findEdletVideos(devuelve,encontrados,data,temp):
    
    
    title=""
    
    ##COMPLEJO
    logger.info ("Estilo Edlet (Reverse)")    
    pchap = '(.*?)<object.*?"http://www.mega([^"]+)".*?</object>'
    cmatches =re.compile(pchap, re.S).findall(data)
    for cdata in cmatches: 
        #tenemos el link y lo anterior
        pinfo = '(.*?)(\d*)X(\d*)(.*?)'
        imatches =re.compile(pinfo, re.S).findall(cdata[0])
        for cinfo in imatches:
            try:
                if(temp==int(cinfo[1])):
                    title = cf(cinfo[1],cinfo[2])
                    AddVideoURL(devuelve,encontrados,title,"http://www.mega"+cdata[1])
                    break
            except:
                pass
        
        
        
        
    return



def findvideos(data,parse):
    logger.info("[vagos.py] findvideos")
    devuelve = []
    encontrados = set()
    temp = findTemp(str(data).lower())
    if(parse):
        try:
            findHayshirVideos(devuelve,encontrados,data,temp)
        except:
            pass
    
        #findEdletVideos(devuelve,encontrados,data)
        try:
            logger.info ("Estilo Antomio")
            #patronvideos = '<a href="http://www.megavideo.com/?v=E9CB86L7" target="_blank">Dexter 1x01 - Capitulo 01</a><br />'
            patronvideos = '<a href="http://www.mega([^"]+)" target="_blank">(.*?)(\d*)x(\d*) - (.*?)</a>'
            matches = re.compile(patronvideos).findall(data)
            for match in matches:        
                title = match[2]+"x"+ match[3] + " - " + match[4]         
                AddVideoURL(devuelve,encontrados,title,"http://www.mega" + match[0]) 
        except:
            pass
       
       
    #http://www.youtube.com/v/3_ptGFK8vTo&amp;hl=es&amp;fs=1    
    logger.info ("0) Enlace estricto a Youtube")
    patronvideos = 'youtube.com\/v\/([^ \t\n\r\f\v]{11})'
    matches = re.compile(patronvideos).findall(data)
    for match in matches:
        AddVideoID(devuelve,encontrados,'',match,'youtube')   
        
    #http://www.youtube.com/watch?v=HjjqZFfVXoU     
    logger.info ("1) Enlace estricto a Youtube")
    patronvideos = 'youtube.com\/watch.*?v=([^ \t\n\r\f\v]{11})'
    matches = re.compile(patronvideos).findall(data)
    for match in matches:
        AddVideoID(devuelve,encontrados,'',match,'youtube')     
        
                
    #videobb tipo "http://www.videobb.com/f/szIwlZD8ewaH.swf"
    logger.info ("0) Enlace estricto a VideoBB")
    patronvideos = 'videobb.com\/f\/([A-Z0-9a-z]{12}).swf'
    matches = re.compile(patronvideos).findall(data)
    for match in matches:
        AddVideoID(devuelve,encontrados,'','http://videobb.com/video/'+match,'videobb') 
  
    #videobb tipo "http://www.videobb.com/video/ZIeb370iuHE4"
    logger.info ("1) Enlace estricto a VideoBB")
    patronvideos = 'videobb.com\/video\/([A-Z0-9a-z]{12})'
    matches = re.compile(patronvideos).findall(data)
    for match in matches:
        AddVideoID(devuelve,encontrados,'','http://videobb.com/video/'+match,'videobb')
         
    #videobb tipo "http://videobb.com/e/LLqVzhw5ft7T"
    logger.info ("2) Enlace estricto a VideoBB")
    patronvideos = 'videobb.com\/e\/([A-Z0-9a-z]{12})'
    matches = re.compile(patronvideos).findall(data)
    for match in matches:
        AddVideoID(devuelve,encontrados,'','http://videobb.com/video/'+match,'videobb') 
    
    
    #Megavideo tipo "http://www.megavideo.com/?v=CN7DWZ8S"
    logger.info ("0) Enlace estricto a megavideo")
    patronvideos = 'http\:\/\/www.megavideo.com\/.*?v\=([A-Z0-9a-z]{8})'
    matches = re.compile(patronvideos).findall(data)
    for match in matches:
        AddVideoID(devuelve,encontrados,'',match,'Megavideo') 
            
    #Megavideo tipo "http://www.megavideo.com/v/CN7DWZ8S"
    logger.info ("1) Enlace estricto a megavideo")
    patronvideos = 'http\:\/\/www.megavideo.com\/v\/([A-Z0-9a-z]{8})'
    matches = re.compile(patronvideos).findall(data)
    for match in matches:
        AddVideoID(devuelve,encontrados,'',match,'Megavideo')  
            
    #Megavideo tipo "http://www.megaupload.com/?d=CN7DWZ8S"
    logger.info ("2) Enlace estricto a megaupload")
    patronvideos = 'http\:\/\/www.megaupload.com\/.*?d\=([A-Z0-9a-z]{8})'
    matches = re.compile(patronvideos).findall(data)
    for match in matches:
        AddVideoID(devuelve,encontrados,'',match,'Megaupload')
    
    #Megavideo tipo "http://www.megaupload.com/?d=CN7DWZ8S"
    logger.info ("3) Enlace estricto a megaupload")
    patronvideos = 'http\:\/\/www.megavideo.com\/.*?d\=([A-Z0-9a-z]{8})'
    matches = re.compile(patronvideos).findall(data)
    for match in matches:
        AddVideoID(devuelve,encontrados,'',match,'Megaupload')
            
    #Megavideo tipo "http://www.megaupload.com/?d=CN7DWZ8S"
    logger.info ("4) Enlace estricto a megavideo")
    patronvideos = 'http\:\/\/wwwstatic.megavideo.com\/mv_player.swf\?v\=([A-Z0-9a-z]{8})'
    matches = re.compile(patronvideos).findall(data)
    for match in matches:
        AddVideoID(devuelve,encontrados,'',match,'Megavideo')

    videosarray = servertools.findvideos(data)
    for videoa in videosarray:
        AddVideoID(devuelve,encontrados,videoa[0],videoa[1],videoa[2])
                      
    return devuelve



def AddVideoURL(devuelve,encontrados,title,url):
    
    #Megavideo tipo "http://www.megavideo.com/?v=CN7DWZ8S"
    logger.info ("0) Enlace estricto a megavideo")
    patronvideos = 'http\:\/\/www.megavideo.com\/.*?v\=([A-Z0-9a-z]{8})'
    matches = re.compile(patronvideos).findall(url)
    for match in matches:
        AddVideoID(devuelve,encontrados,title,match,'Megavideo')
            
    #Megavideo tipo "http://www.megavideo.com/v/CN7DWZ8S"
    logger.info ("1) Enlace estricto a megavideo")
    patronvideos = 'http\:\/\/www.megavideo.com\/v\/([A-Z0-9a-z]{8})'
    matches = re.compile(patronvideos).findall(url)
    for match in matches:
        AddVideoID(devuelve,encontrados,title,match,'Megavideo')
            
    #Megavideo tipo "http://www.megaupload.com/?d=CN7DWZ8S"
    logger.info ("2) Enlace estricto a megaupload")
    patronvideos = 'http\:\/\/www.megaupload.com\/.*?d\=([A-Z0-9a-z]{8})'
    matches = re.compile(patronvideos).findall(url)
    for match in matches:
        AddVideoID(devuelve,encontrados,title,match,'Megaupload')
    
    #Megavideo tipo "http://www.megaupload.com/?d=CN7DWZ8S"
    logger.info ("3) Enlace estricto a megaupload")
    patronvideos = 'http\:\/\/www.megavideo.com\/.*?d\=([A-Z0-9a-z]{8})'
    matches = re.compile(patronvideos).findall(url)
    for match in matches:
        AddVideoID(devuelve,encontrados,title,match,'Megaupload')
    
    #Megavideo tipo "http://www.megaupload.com/?d=CN7DWZ8S"
    logger.info ("4) Enlace estricto a megavideo")
    patronvideos = 'http\:\/\/wwwstatic.megavideo.com\/mv_player.swf\?v\=([A-Z0-9a-z]{8})'
    matches = re.compile(patronvideos).findall(url)
    for match in matches:
        AddVideoID(devuelve,encontrados,title,match,'Megavideo')
    
    videosarray = servertools.findvideos(url)
    for videoa in videosarray:
        AddVideoID(devuelve,encontrados,title,videoa[1],videoa[2])
    
    return 

def AddVideoID(devuelve,encontrados,title,id,servidor):  
    if id not in encontrados:
        devuelve.append( [title, id , servidor] )
        encontrados.add(id)
    else:
        logger.info(" id duplicado="+id) 
        
    return

def findimage(data):
    try:
        patronmensajes = '<div id="post_message_([^"]+)">[^<]+'
        patronmensajes += '<div align="([^"]+)">.*<img src="([^"]+)"'
        mensajes = re.compile(patronmensajes).findall(data)
        if(len(mensajes)>0):
            for mensaje in mensajes:
                return mensaje[2]
        
        patronmensajes = '<div id="post_message_([^"]+)">[^<]+'
        patronmensajes += '<img src="([^"]+)"'
        mensajes = re.compile(patronmensajes).findall(data)
        if(len(mensajes)>0):
            for mensaje in mensajes:
                return mensaje[1]
            
        patronmensajes = '<div id="post_message_([^"]+)">[^<]+'
        patronmensajes += '<font color="([^"]+)">.*<img src="([^"]+)"'
        mensajes = re.compile(patronmensajes).findall(data)
        if(len(mensajes)>0):
            for mensaje in mensajes:
                return mensaje[2] 
        
       
        
        return ""    
    except:
        return ""
    
def findTemp(data):
        
       
    patronvideos = '(\d*) temporada'
    matches = re.compile(patronvideos).findall(data)
    for match in matches:  
        try:      
            return int(match)
        except:
            pass
    
    patronvideos = 'temporada (\d*)'
    matches = re.compile(patronvideos).findall(data)
    for match in matches:  
        try:      
            return int(match)
        except:
            pass
        
    patronvideos = '(\d*)ª temporada'
    matches = re.compile(patronvideos).findall(data)
    for match in matches:  
        try:      
            return int(match)
        except:
            pass
        
    patronvideos = 'temporada (\d*)ª'
    matches = re.compile(patronvideos).findall(data)
    for match in matches:  
        try:      
            return int(match)
        except:
            pass
        
    
    
    return 0
        
def MensajesChincheta(data):
    logger.info("[vagos.py] MensajesChincheta")
    encontrados = set()    
    
    patronch = '<td class="alt1" id="td_threadtitle_([^"]+)" title="">[^<]+'
    patronch += '<div>[^<]+'
    patronch += '<span style="float:right">[^<]+'
    patronch += '<img class="inlineimg" src="http://wf1.vagos.es/images/misc/sticky.gif" alt="Mensaje Adherido" />[^<]+'
    patronch += '</span>'
    matches = re.compile(patronch).findall(data)
    for match in matches:
        url = match
        if url not in encontrados:
            encontrados.add(url)
        else:
            logger.info(" url duplicada="+url)            
    
    return encontrados

    
