#------------------------------------------------------------
# -*- coding: utf-8 -*-
#------------------------------------------------------------
# Download Tools
# Based on the code from VideoMonkey XBMC Plugin
#------------------------------------------------------------
# pelisalacarta
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#------------------------------------------------------------
# Creado por:
# Jesús (tvalacarta@gmail.com)
# jurrabi (jurrabi@gmail.com)
# bandavi (xbandavix@gmail.com)
# Licencia: GPL (http://www.gnu.org/licenses/gpl-3.0.html)
#------------------------------------------------------------
# Historial de cambios:
#------------------------------------------------------------

import urlparse,urllib2,urllib
import time
import md5
import os
import config
import logger
import re, htmlentitydefs
import downloadtools

logger.info("[scrapertools.py] init")

CACHE_ACTIVA = "0"  # Automatica
CACHE_SIEMPRE = "1" # Cachear todo
CACHE_NUNCA = "2"   # No cachear nada

CACHE_PATH = config.get_setting("cache.dir")
logger.info("[scrapertools.py] CACHE_PATH="+CACHE_PATH)

DEBUG = False

def cache_page(url,post=None,headers=[['User-Agent', 'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.6; es-ES; rv:1.9.2.12) Gecko/20101026 Firefox/3.6.12']],modo_cache=CACHE_ACTIVA):
    return cachePage(url,post,headers,modo_cache)

# TODO: (3.1) Quitar el parámetro modoCache (ahora se hace por configuración)
# TODO: (3.2) Usar notación minusculas_con_underscores para funciones y variables como recomienda Python http://www.python.org/dev/peps/pep-0008/
def cachePage(url,post=None,headers=[['User-Agent', 'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.6; es-ES; rv:1.9.2.12) Gecko/20101026 Firefox/3.6.12']],modoCache=CACHE_ACTIVA):

    logger.info("[scrapertools.py] cachePage url="+url)
    modoCache = config.get_setting("cache.mode")
    
    if config.get_platform()=="plex":
        from PMS import HTTP
        try:
            logger.info("url="+url)
            data = HTTP.Request(url)
            logger.info("descargada")
        except:
            data = ""
            logger.error("Error descargando "+url)
            import sys
            for line in sys.exc_info():
                logger.error( "%s" % line )
        
        return data

    else:
        # CACHE_NUNCA: Siempre va a la URL a descargar
        # obligatorio para peticiones POST
        if modoCache == CACHE_NUNCA or post is not None:
            logger.info("[scrapertools.py] MODO_CACHE=2 (no cachear)")
            
            data = downloadpage(url,post,headers)
        
        # CACHE_SIEMPRE: Siempre descarga de cache, sin comprobar fechas, excepto cuando no está
        elif modoCache == CACHE_SIEMPRE:
            logger.info("[scrapertools.py] MODO_CACHE=1 (cachear todo)")
            
            # Obtiene los handlers del fichero en la cache
            cachedFile, newFile = getCacheFileNames(url)
        
            # Si no hay ninguno, descarga
            if cachedFile == "":
                logger.debug("[scrapertools.py] No está en cache")
        
                # Lo descarga
                data = downloadpage(url,post,headers)
        
                # Lo graba en cache
                outfile = open(newFile,"w")
                outfile.write(data)
                outfile.flush()
                outfile.close()
                logger.info("[scrapertools.py] Grabado a " + newFile)
            else:
                logger.info("[scrapertools.py] Leyendo de cache " + cachedFile)
                infile = open( cachedFile )
                data = infile.read()
                infile.close()
        
        # CACHE_ACTIVA: Descarga de la cache si no ha cambiado
        else:
            logger.info("[scrapertools.py] MODO_CACHE=0 (automática)")
            
            # Datos descargados
            data = ""
            
            # Obtiene los handlers del fichero en la cache
            cachedFile, newFile = getCacheFileNames(url)
        
            # Si no hay ninguno, descarga
            if cachedFile == "":
                logger.debug("[scrapertools.py] No está en cache")
        
                # Lo descarga
                data = downloadpage(url,post,headers)
                
                # Lo graba en cache
                outfile = open(newFile,"w")
                outfile.write(data)
                outfile.flush()
                outfile.close()
                logger.info("[scrapertools.py] Grabado a " + newFile)
        
            # Si sólo hay uno comprueba el timestamp (hace una petición if-modified-since)
            else:
                # Extrae el timestamp antiguo del nombre del fichero
                oldtimestamp = time.mktime( time.strptime(cachedFile[-20:-6], "%Y%m%d%H%M%S") )
        
                logger.info("[scrapertools.py] oldtimestamp="+cachedFile[-20:-6])
                logger.info("[scrapertools.py] oldtimestamp="+time.ctime(oldtimestamp))
                
                # Hace la petición
                updated,data = downloadtools.downloadIfNotModifiedSince(url,oldtimestamp)
                
                # Si ha cambiado
                if updated:
                    # Borra el viejo
                    logger.debug("[scrapertools.py] Borrando "+cachedFile)
                    os.remove(cachedFile)
                    
                    # Graba en cache el nuevo
                    outfile = open(newFile,"w")
                    outfile.write(data)
                    outfile.flush()
                    outfile.close()
                    logger.info("[scrapertools.py] Grabado a " + newFile)
                # Devuelve el contenido del fichero de la cache
                else:
                    logger.info("[scrapertools.py] Leyendo de cache " + cachedFile)
                    infile = open( cachedFile )
                    data = infile.read()
                    infile.close()

    return data

def getCacheFileNames(url):

    # Obtiene el directorio de la cache para esta url
    siteCachePath = getSiteCachePath(url)
        
    # Obtiene el ID de la cache (md5 de la URL)
    import binascii
    cacheId = binascii.hexlify(md5.new(url).digest())
    logger.debug("[scrapertools.py] cacheId="+cacheId)

    # Timestamp actual
    nowtimestamp = time.strftime("%Y%m%d%H%M%S", time.localtime())
    logger.debug("[scrapertools.py] nowtimestamp="+nowtimestamp)

    # Nombre del fichero
    # La cache se almacena en una estructura CACHE + URL
    ruta = os.path.join( siteCachePath , cacheId[:2] , cacheId[2:] )
    newFile = os.path.join( ruta , nowtimestamp + ".cache" )
    logger.debug("[scrapertools.py] newFile="+newFile)
    if not os.path.exists(ruta):
        os.makedirs( ruta )

    # Busca ese fichero en la cache
    cachedFile = getCachedFile(siteCachePath,cacheId)

    return cachedFile, newFile 

# Busca ese fichero en la cache
def getCachedFile(siteCachePath,cacheId):
    mascara = os.path.join(siteCachePath,cacheId[:2],cacheId[2:],"*.cache")
    logger.debug("[scrapertools.py] mascara="+mascara)
    import glob
    ficheros = glob.glob( mascara )
    logger.debug("[scrapertools.py] Hay %d ficheros con ese id" % len(ficheros))

    cachedFile = ""

    # Si hay más de uno, los borra (serán pruebas de programación) y descarga de nuevo
    if len(ficheros)>1:
        logger.debug("[scrapertools.py] Cache inválida")
        for fichero in ficheros:
            logger.debug("[scrapertools.py] Borrando "+fichero)
            os.remove(fichero)
        
        cachedFile = ""

    # Hay uno: fichero cacheado
    elif len(ficheros)==1:
        cachedFile = ficheros[0]

    return cachedFile

def getSiteCachePath(url):
    # Obtiene el dominio principal de la URL    
    dominio = urlparse.urlparse(url)[1]
    logger.debug("[scrapertools.py] dominio="+dominio)
    nombres = dominio.split(".")
    if len(nombres)>1:
        dominio = nombres[len(nombres)-2]+"."+nombres[len(nombres)-1]
    else:
        dominio = nombres[0]
    logger.debug("[scrapertools.py] dominio="+dominio)
    
    # Crea un directorio en la cache para direcciones de ese dominio
    siteCachePath = os.path.join( CACHE_PATH , dominio )
    if not os.path.exists(CACHE_PATH):
        try:
            os.mkdir( CACHE_PATH )
        except:
            logger.error("[scrapertools.py] Error al crear directorio "+CACHE_PATH)

    if not os.path.exists(siteCachePath):
        try:
            os.mkdir( siteCachePath )
        except:
            logger.error("[scrapertools.py] Error al crear directorio "+siteCachePath)
    
    logger.debug("[scrapertools.py] siteCachePath="+siteCachePath)

    return siteCachePath

def cachePage2(url,headers):

    logger.info("Descargando " + url)
    inicio = time.clock()
    req = urllib2.Request(url)
    for header in headers:
        logger.info(header[0]+":"+header[1])
        req.add_header(header[0], header[1])

    try:
        response = urllib2.urlopen(req)
    except:
        req = urllib2.Request(url.replace(" ","%20"))
        for header in headers:
            logger.info(header[0]+":"+header[1])
            req.add_header(header[0], header[1])
        response = urllib2.urlopen(req)
    data=response.read()
    response.close()
    fin = time.clock()
    logger.info("Descargado en %d segundos " % (fin-inicio+1))

    '''
        outfile = open(localFileName,"w")
        outfile.write(data)
        outfile.flush()
        outfile.close()
        logger.info("Grabado a " + localFileName)
    '''
    return data

def cachePagePost(url,post):

    logger.info("Descargando " + url)
    inicio = time.clock()
    req = urllib2.Request(url,post)
    req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')

    try:
        response = urllib2.urlopen(req)
    except:
        req = urllib2.Request(url.replace(" ","%20"),post)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
        response = urllib2.urlopen(req)
    data=response.read()
    response.close()
    fin = time.clock()
    logger.info("Descargado en %d segundos " % (fin-inicio+1))

    '''
        outfile = open(localFileName,"w")
        outfile.write(data)
        outfile.flush()
        outfile.close()
        logger.info("Grabado a " + localFileName)
    '''
    return data

def downloadpage(url,post=None,headers=[['User-Agent', 'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.6; es-ES; rv:1.9.2.12) Gecko/20101026 Firefox/3.6.12']]):
    logger.info("[scrapertools.py] downloadpage")
    logger.info("[scrapertools.py] url="+url)
    
    if post is not None:
        logger.info("[scrapertools.py] post="+post)
    else:
        logger.info("[scrapertools.py] post=None")
    
    # ---------------------------------
    # Instala las cookies
    # ---------------------------------

    #  Inicializa la librería de las cookies
    ficherocookies = os.path.join( config.get_setting("cookies.dir"), 'cookies.lwp' )
    logger.info("[scrapertools.py] ficherocookies="+ficherocookies)

    cj = None
    ClientCookie = None
    cookielib = None

    # Let's see if cookielib is available
    try:
        logger.info("[scrapertools.py] Importando cookielib")
        import cookielib
    except ImportError:
        logger.info("[scrapertools.py] cookielib no disponible")
        # If importing cookielib fails
        # let's try ClientCookie
        try:
            logger.info("[scrapertools.py] Importando ClientCookie")
            import ClientCookie
        except ImportError:
            logger.info("[scrapertools.py] ClientCookie no disponible")
            # ClientCookie isn't available either
            urlopen = urllib2.urlopen
            Request = urllib2.Request
        else:
            logger.info("[scrapertools.py] ClientCookie disponible")
            # imported ClientCookie
            urlopen = ClientCookie.urlopen
            Request = ClientCookie.Request
            cj = ClientCookie.LWPCookieJar()

    else:
        logger.info("[scrapertools.py] cookielib disponible")
        # importing cookielib worked
        urlopen = urllib2.urlopen
        Request = urllib2.Request
        cj = cookielib.LWPCookieJar()
        # This is a subclass of FileCookieJar
        # that has useful load and save methods

    if cj is not None:
    # we successfully imported
    # one of the two cookie handling modules
        logger.info("[scrapertools.py] Hay cookies")

        if os.path.isfile(ficherocookies):
            logger.info("[scrapertools.py] Leyendo fichero cookies")
            # if we have a cookie file already saved
            # then load the cookies into the Cookie Jar
            cj.load(ficherocookies)

        # Now we need to get our Cookie Jar
        # installed in the opener;
        # for fetching URLs
        if cookielib is not None:
            logger.info("[scrapertools.py] opener usando urllib2 (cookielib)")
            # if we use cookielib
            # then we get the HTTPCookieProcessor
            # and install the opener in urllib2
            opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
            urllib2.install_opener(opener)

        else:
            logger.info("[scrapertools.py] opener usando ClientCookie")
            # if we use ClientCookie
            # then we get the HTTPCookieProcessor
            # and install the opener in ClientCookie
            opener = ClientCookie.build_opener(ClientCookie.HTTPCookieProcessor(cj))
            ClientCookie.install_opener(opener)

    # -------------------------------------------------
    # Cookies instaladas, lanza la petición
    # -------------------------------------------------

    # Contador
    inicio = time.clock()

    # Diccionario para las cabeceras
    txheaders = {}

    # Añade las cabeceras
    for header in headers:
        logger.info("[scrapertools.py] header="+header[0]+": "+header[1])
        txheaders[header[0]]=header[1]

    # Construye el request
    if post is None:
        logger.info("[scrapertools.py] petición GET")
    else:
        logger.info("[scrapertools.py] petición POST")
    
    req = Request(url, post, txheaders)
    handle = urlopen(req)
    
    # Actualiza el almacén de cookies
    cj.save(ficherocookies)

    # Lee los datos y cierra
    data=handle.read()
    handle.close()

    '''
    # Lanza la petición
    try:
        response = urllib2.urlopen(req)
    # Si falla la repite sustituyendo caracteres especiales
    except:
        req = urllib2.Request(url.replace(" ","%20"))
    
        # Añade las cabeceras
        for header in headers:
            req.add_header(header[0],header[1])

        response = urllib2.urlopen(req)
    '''
    
    # Tiempo transcurrido
    fin = time.clock()
    logger.info("[scrapertools.py] Descargado en %d segundos " % (fin-inicio+1))

    return data

def downloadpagewithcookies(url):
    # ---------------------------------
    # Instala las cookies
    # ---------------------------------

    #  Inicializa la librería de las cookies
    ficherocookies = os.path.join( config.get_data_path(), 'cookies.lwp' )
    logger.info("[scrapertools.py] Cookiefile="+ficherocookies)

    cj = None
    ClientCookie = None
    cookielib = None

    # Let's see if cookielib is available
    try:
        import cookielib
    except ImportError:
        # If importing cookielib fails
        # let's try ClientCookie
        try:
            import ClientCookie
        except ImportError:
            # ClientCookie isn't available either
            urlopen = urllib2.urlopen
            Request = urllib2.Request
        else:
            # imported ClientCookie
            urlopen = ClientCookie.urlopen
            Request = ClientCookie.Request
            cj = ClientCookie.LWPCookieJar()

    else:
        # importing cookielib worked
        urlopen = urllib2.urlopen
        Request = urllib2.Request
        cj = cookielib.LWPCookieJar()
        # This is a subclass of FileCookieJar
        # that has useful load and save methods

    if cj is not None:
    # we successfully imported
    # one of the two cookie handling modules

        if os.path.isfile(ficherocookies):
            # if we have a cookie file already saved
            # then load the cookies into the Cookie Jar
            cj.load(ficherocookies)

        # Now we need to get our Cookie Jar
        # installed in the opener;
        # for fetching URLs
        if cookielib is not None:
            # if we use cookielib
            # then we get the HTTPCookieProcessor
            # and install the opener in urllib2
            opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
            urllib2.install_opener(opener)

        else:
            # if we use ClientCookie
            # then we get the HTTPCookieProcessor
            # and install the opener in ClientCookie
            opener = ClientCookie.build_opener(ClientCookie.HTTPCookieProcessor(cj))
            ClientCookie.install_opener(opener)

    #print "-------------------------------------------------------"
    theurl = url
    # an example url that sets a cookie,
    # try different urls here and see the cookie collection you can make !

    #txheaders =  {'User-Agent':'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3',
    #              'Referer':'http://www.megavideo.com/?s=signup'}
    txheaders =  {
    'User-Agent':'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3',
    'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Host':'www.meristation.com',
    'Accept-Language':'es-es,es;q=0.8,en-us;q=0.5,en;q=0.3',
    'Accept-Charset':'ISO-8859-1,utf-8;q=0.7,*;q=0.7',
    'Keep-Alive':'300',
    'Connection':'keep-alive'}

    # fake a user agent, some websites (like google) don't like automated exploration

    req = Request(theurl, None, txheaders)
    handle = urlopen(req)
    cj.save(ficherocookies) # save the cookies again

    data=handle.read()
    handle.close()

    return data
    
def downloadpageWithoutCookies(url):
    logger.info("[scrapertools.py] Descargando " + url)
    inicio = time.clock()
    req = urllib2.Request(url)
    req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 6.0; es-ES; rv:1.9.0.14) Gecko/2009082707 Firefox/3.0.14')
    req.add_header('X-Requested-With','XMLHttpRequest')
    try:
        response = urllib2.urlopen(req)
    except:
        req = urllib2.Request(url.replace(" ","%20"))
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 6.0; es-ES; rv:1.9.0.14) Gecko/2009082707 Firefox/3.0.14')

        response = urllib2.urlopen(req)
    data=response.read()
    response.close()
    fin = time.clock()
    logger.info("[scrapertools.py] Descargado en %d segundos " % (fin-inicio+1))
    return data
    

def downloadpageGzip(url):
    
    #  Inicializa la librería de las cookies
    ficherocookies = os.path.join( config.get_data_path(), 'cookies.lwp' )
    print "Cookiefile="+ficherocookies
    inicio = time.clock()
    
    cj = None
    ClientCookie = None
    cookielib = None

    # Let's see if cookielib is available
    try:
        import cookielib
    except ImportError:
        # If importing cookielib fails
        # let's try ClientCookie
        try:
            import ClientCookie
        except ImportError:
            # ClientCookie isn't available either
            urlopen = urllib2.urlopen
            Request = urllib2.Request
        else:
            # imported ClientCookie
            urlopen = ClientCookie.urlopen
            Request = ClientCookie.Request
            cj = ClientCookie.LWPCookieJar()

    else:
        # importing cookielib worked
        urlopen = urllib2.urlopen
        Request = urllib2.Request
        cj = cookielib.LWPCookieJar()
        # This is a subclass of FileCookieJar
        # that has useful load and save methods

    # ---------------------------------
    # Instala las cookies
    # ---------------------------------

    if cj is not None:
    # we successfully imported
    # one of the two cookie handling modules

        if os.path.isfile(ficherocookies):
            # if we have a cookie file already saved
            # then load the cookies into the Cookie Jar
            cj.load(ficherocookies)

        # Now we need to get our Cookie Jar
        # installed in the opener;
        # for fetching URLs
        if cookielib is not None:
            # if we use cookielib
            # then we get the HTTPCookieProcessor
            # and install the opener in urllib2
            opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
            urllib2.install_opener(opener)

        else:
            # if we use ClientCookie
            # then we get the HTTPCookieProcessor
            # and install the opener in ClientCookie
            opener = ClientCookie.build_opener(ClientCookie.HTTPCookieProcessor(cj))
            ClientCookie.install_opener(opener)

    #print "-------------------------------------------------------"
    theurl = url
    # an example url that sets a cookie,
    # try different urls here and see the cookie collection you can make !

    #txheaders =  {'User-Agent':'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3',
    #              'Referer':'http://www.megavideo.com/?s=signup'}
    
    import httplib
    parsedurl = urlparse.urlparse(url)
    print "parsedurl=",parsedurl
        
    txheaders =  {
    'User-Agent':'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3',
    'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language':'es-es,es;q=0.8,en-us;q=0.5,en;q=0.3',
    'Accept-Charset':'ISO-8859-1,utf-8;q=0.7,*;q=0.7',
    'Accept-Encoding':'gzip,deflate',
    'Keep-Alive':'300',
    'Connection':'keep-alive',
    'Referer':parsedurl[0]+"://"+parsedurl[1]}
    print txheaders

    # fake a user agent, some websites (like google) don't like automated exploration

    req = Request(theurl, None, txheaders)
    handle = urlopen(req)
    cj.save(ficherocookies) # save the cookies again

    data=handle.read()
    handle.close()
    
    fin = time.clock()
    logger.info("[scrapertools.py] Descargado 'Gzipped data' en %d segundos " % (fin-inicio+1))
        
    # Descomprime el archivo de datos Gzip
    try:
        fin = inicio
        import StringIO
        compressedstream = StringIO.StringIO(data)
        import gzip
        gzipper = gzip.GzipFile(fileobj=compressedstream)
        data1 = gzipper.read()
        gzipper.close()
        fin = time.clock()
        logger.info("[scrapertools.py] 'Gzipped data' descomprimido en %d segundos " % (fin-inicio+1))
        return data1
    except:
        return data

def printMatches(matches):
    i = 0
    for match in matches:
        logger.info("[scrapertools.py] %d %s" % (i , match))
        i = i + 1

def entityunescape(cadena):
    from xml.sax.saxutils import unescape
    cadena = unescape(cadena)

    '''
    cadena = cadena.replace('&amp;','&')
    cadena = cadena.replace('&Agrave;','À')
    cadena = cadena.replace('&Aacute;','Á')
    cadena = cadena.replace('&Eacute;','É')
    cadena = cadena.replace('&Iacute;','Í')
    cadena = cadena.replace('&Oacute;','Ó')
    cadena = cadena.replace('&Uacute;','Ú')
    cadena = cadena.replace('&ntilde;','ñ')
    cadena = cadena.replace('&Ntilde;','Ñ')
    cadena = cadena.replace('&agrave;','à')
    cadena = cadena.replace('&aacute;','á')
    cadena = cadena.replace('&eacute;','é')
    cadena = cadena.replace('&iacute;','í')
    cadena = cadena.replace('&oacute;','ó')
    cadena = cadena.replace('&uacute;','ú')
    cadena = cadena.replace('&iexcl;','¡')
    cadena = cadena.replace('&iquest;','¿')
    cadena = cadena.replace('&ordf;','ª')
    cadena = cadena.replace('&quot;','"')
    cadena = cadena.replace('&hellip;','...')
    cadena = cadena.replace('&#39;','\'')
    cadena = cadena.replace('&Ccedil;','Ç')
    cadena = cadena.replace('&ccedil;','ç')
    '''
    return cadena

def unescape(text):
    """Removes HTML or XML character references 
       and entities from a text string.
       keep &amp;, &gt;, &lt; in the source code.
    from Fredrik Lundh
    http://effbot.org/zone/re-sub.htm#unescape-html
    """
    def fixup(m):
        text = m.group(0)
        if text[:2] == "&#":
            # character reference
            try:
                if text[:3] == "&#x":   
                    return unichr(int(text[3:-1], 16)).encode("utf-8")
                else:
                    return unichr(int(text[2:-1])).encode("utf-8")
                  
            except ValueError:
                print "error de valor"
                pass
        else:
            # named entity
            try:
                '''
                if text[1:-1] == "amp":
                    text = "&amp;amp;"
                elif text[1:-1] == "gt":
                    text = "&amp;gt;"
                elif text[1:-1] == "lt":
                    text = "&amp;lt;"
                else:
                    print text[1:-1]
                    text = unichr(htmlentitydefs.name2codepoint[text[1:-1]]).encode("utf-8")
                '''
                text = unichr(htmlentitydefs.name2codepoint[text[1:-1]]).encode("utf-8")
            except KeyError:
                print "keyerror"
                pass
        return text # leave as is
    return re.sub("&#?\w+;", fixup, text)

def htmlclean(cadena):
    cadena = cadena.replace("<center>","")
    cadena = cadena.replace("</center>","")
    cadena = cadena.replace("<cite>","")
    cadena = cadena.replace("</cite>","")
    cadena = cadena.replace("<em>","")
    cadena = cadena.replace("</em>","")
    cadena = cadena.replace("<b>","")
    cadena = cadena.replace("</b>","")
    cadena = cadena.replace("<li>","")
    cadena = cadena.replace("</li>","")
    cadena = cadena.replace("<![CDATA[","")

    cadena = re.compile("<div[^>]*>",re.DOTALL).sub("",cadena)
    cadena = cadena.replace("</div>","")
    
    cadena = re.compile("<dd[^>]*>",re.DOTALL).sub("",cadena)
    cadena = cadena.replace("</dd>","")

    cadena = re.compile("<font[^>]*>",re.DOTALL).sub("",cadena)
    cadena = cadena.replace("</font>","")
    
    cadena = re.compile("<strong[^>]*>",re.DOTALL).sub("",cadena)
    cadena = cadena.replace("</strong>","")

    cadena = re.compile("<span[^>]*>",re.DOTALL).sub("",cadena)
    cadena = cadena.replace("</span>","")

    cadena = re.compile("<a[^>]*>",re.DOTALL).sub("",cadena)
    cadena = cadena.replace("</a>","")
    
    cadena = re.compile("<p[^>]*>",re.DOTALL).sub("",cadena)
    cadena = cadena.replace("</p>","")

    cadena = re.compile("<ul[^>]*>",re.DOTALL).sub("",cadena)
    cadena = cadena.replace("</ul>","")
    
    cadena = re.compile("<h1[^>]*>",re.DOTALL).sub("",cadena)
    cadena = cadena.replace("</h1>","")
    
    cadena = re.compile("<h2[^>]*>",re.DOTALL).sub("",cadena)
    cadena = cadena.replace("</h2>","")

    cadena = re.compile("<h3[^>]*>",re.DOTALL).sub("",cadena)
    cadena = cadena.replace("</h3>","")

    cadena = re.compile("<!--[^-]+-->",re.DOTALL).sub("",cadena)
    
    cadena = re.compile("<img[^>]*>",re.DOTALL).sub("",cadena)
    cadena = re.compile("<br[^>]*>",re.DOTALL).sub("",cadena)
    cadena = re.compile("<object[^>]*>",re.DOTALL).sub("",cadena)
    cadena = cadena.replace("</object>","")
    cadena = re.compile("<param[^>]*>",re.DOTALL).sub("",cadena)
    cadena = cadena.replace("</param>","")
    cadena = re.compile("<embed[^>]*>",re.DOTALL).sub("",cadena)
    cadena = cadena.replace("</embed>","")

    cadena = re.compile("<title[^>]*>",re.DOTALL).sub("",cadena)
    cadena = cadena.replace("</title>","")

    cadena = re.compile("<link[^>]*>",re.DOTALL).sub("",cadena)

    cadena = cadena.replace("\t","")
    cadena = entityunescape(cadena)
    return cadena

def getRandom(str):
    return binascii.hexlify(md5.new(str).digest())

def getLocationHeaderFromResponse(url):
    logger.info("[scrapertools.py] getLocationHeaderFromResponse")

    if url=='':
        return None

    import httplib
    parsedurl = urlparse.urlparse(url)
    print "parsedurl=",parsedurl

    try:
        host = parsedurl.netloc
    except:
        host = parsedurl[1]
    print "host=",host

    try:
        print "1"
        query = parsedurl.path+";"+parsedurl.query
    except:
        print "2"
        query = parsedurl[2]+";"+parsedurl[3]+"?"
    print "query=",query
    query = urllib.unquote( query )
    print "query = " + query

    import httplib
    conn = httplib.HTTPConnection(host)
    conn.request("GET", query)
    response = conn.getresponse()
    location = response.getheader("location")
    conn.close()
    
    print "location=",location

    if location!=None:
        print "Encontrado header location"
    
    return location
