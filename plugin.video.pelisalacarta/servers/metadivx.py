# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Conector para Metadivx
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#------------------------------------------------------------

import urlparse,urllib2,urllib,re

try:
    from core import scrapertools
    from core import logger
    from core import config
    from core import unpackerjs
except:
    from Code.core import scrapertools
    from Code.core import logger
    from Code.core import config
    from Code.core import unpackerjs

import os
COOKIEFILE = os.path.join(config.get_data_path() , "cookies.lwp")

def geturl(urlvideo):
    logger.info("[metadivx.py] url="+urlvideo)
    # ---------------------------------------
    #  Inicializa la libreria de las cookies
    # ---------------------------------------
    ficherocookies = COOKIEFILE
    try:
        os.remove(ficherocookies)
    except:
        pass
    # the path and filename to save your cookies in

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
    url=urlvideo
    #print url
    #print "-------------------------------------------------------"
    theurl = url
    # an example url that sets a cookie,
    # try different urls here and see the cookie collection you can make !

    txdata = None
    # if we were making a POST type request,
    # we could encode a dictionary of values here,
    # using urllib.urlencode(somedict)

    txheaders =  {'User-Agent':'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0; SLCC1; .NET CLR 2.0.50727; Media Center PC 5.0; .NET CLR 3.0.04506)'}
    # fake a user agent, some websites (like google) don't like automated exploration

    req = Request(theurl, txdata, txheaders)
    handle = urlopen(req)
    cj.save(ficherocookies)                     # save the cookies again    

    data=handle.read()
    handle.close()
    #print data

    # Lo pide una segunda vez, como si hubieras hecho click en el banner
    patron = 'http\:\/\/www\.metadivx\.com/([^\/]+)/(.*?)\.html'
    matches = re.compile(patron,re.DOTALL).findall(url)
    logger.info("[metadivx.py] fragmentos de la URL")
    scrapertools.printMatches(matches)
    
    codigo = ""
    nombre = ""
    if len(matches)>0:
        codigo = matches[0][0]
        nombre = matches[0][1]

    txdata = "op=download1&usr_login=&id="+codigo+"&fname="+nombre+"&referer=&method_free=Continue"
    logger.info(txdata)
    req = Request(theurl, txdata, txheaders)
    handle = urlopen(req)
    cj.save(ficherocookies)                     # save the cookies again    

    data=handle.read()
    handle.close()
    #print data
    
    patron = '<div id="embedcontmvshre[^>]+>(.*?)</div>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)
    logger.info("[metadivx.py] bloque packed")
    if len(matches)>0:
        logger.info(matches[0])
    '''
    <center>
    <script type='text/javascript'>eval(function(p,a,c,k,e,d){while(c--)if(k[c])p=p.replace(new RegExp('\\b'+c.toString(a)+'\\b','g'),k[c]);return p}('1e.1d(\'<7 w="1c"1b="1a:19-18-17-16-15"h="g"f="e"14="4://a.6.3/9/13.12"><2 1="j"0="i"><2 1="v"0="u"><2 1="b"0="5"/><2 1="c"0="5"/><2 1="t"0="4://s.r.q.p:o/d/n/m.3.-l.k"/><8 w="11"v="u"10="z/6"t="4://s.r.q.p:o/d/n/m.3.-l.k"j="i"h="g"f="e"c="5"b="5"y="4://a.6.3/9/x/"></8></7>\');',36,51,'value|name|param|com|http|false|divx|object|embed|plugin|go|bannerEnabled|autoPlay||320px|height|630px|width|none|custommode|avi|El_Concierto__BrSc__Spanish_HOMIEZTEAM__2010_|Capitancinema|pfq3vaf2xypwtrv77uw334hb55ctx5tcd6dva|182|206|45|73|76|src|auto|bufferingMode|id|download|pluginspage|video|type|embedmvshre|cab|DivXBrowserPlugin|codebase|CC0F21721616|9C46|41fa|D0AB|67DABFBF|clsid|classid|embedcontmvshre|write|document'.split('|')))
    </script>
    </center>
    '''
    # El javascript empaquetado es
    #eval(function(p,a,c,k,e,d){while(c--)if(k[c])p=p.replace(new RegExp('\\b'+c.toString(a)+'\\b','g'),k[c]);return p}('1e.1d(\'<7 w="1c"1b="1a:19-18-17-16-15"h="g"f="e"14="4://a.6.3/9/13.12"><2 1="j"0="i"><2 1="v"0="u"><2 1="b"0="5"/><2 1="c"0="5"/><2 1="t"0="4://s.r.q.p:o/d/n/m.3.-l.k"/><8 w="11"v="u"10="z/6"t="4://s.r.q.p:o/d/n/m.3.-l.k"j="i"h="g"f="e"c="5"b="5"y="4://a.6.3/9/x/"></8></7>\');',36,51,'value|name|param|com|http|false|divx|object|embed|plugin|go|bannerEnabled|autoPlay||320px|height|630px|width|none|custommode|avi|El_Concierto__BrSc__Spanish_HOMIEZTEAM__2010_|Capitancinema|pfq3vaf2xypwtrv77uw334hb55ctx5qa5wdfa|182|206|45|73|76|src|auto|bufferingMode|id|download|pluginspage|video|type|embedmvshre|cab|DivXBrowserPlugin|codebase|CC0F21721616|9C46|41fa|D0AB|67DABFBF|clsid|classid|embedcontmvshre|write|document'.split('|')))
    '''
    eval(function(p,a,c,k,e,d){while(c--)if(k[c])p=p.replace(new RegExp('\\b'+c.toString(a)+'\\b','g'),k[c]);return p}('1e.1d(\'
    <7 w="1c"1b="1a:19-18-17-16-15"h="g"f="e"14="4://a.6.3/9/13.12">
    <2 1="j"0="i">
    <2 1="v"0="u">
    <2 1="b"0="5"/>
    <2 1="c"0="5"/>
    <2 1="t"0="4://s.r.q.p:o/d/n/m.3.-l.k"/>
    <8 w="11"v="u"10="z/6"t="4://s.r.q.p:o/d/n/m.3.-l.k"j="i"h="g"f="e"c="5"b="5"y="4://a.6.3/9/x/">
    <embed id="embedmvshre"bufferingMode="auto"type="video/divx"src="http://76.73.45.206:182/d/pfq3vaf2xypwtrv77uw334hb55ctx5qa5wdfa/Capitancinema.com.-El_Concierto__BrSc__Spanish_HOMIEZTEAM__2010_.avi"custommode="none"width="630px"height="320px"autoPlay="false"bannerEnabled="false"pluginspage="http://go.divx.com/plugin/download/">
    </8>
    </7>\');',36,51,
    0'value
    1|name
    2|param
    3|com
    4|http
    5|false
    6|divx
    7|object
    8|embed
    9|plugin
    a|go
    b|bannerEnabled
    c|autoPlay
    d|
    e|320px
    f|height
    g|630px
    h|width
    i|none
    j|custommode
    k|avi
    l|El_Concierto__BrSc__Spanish_HOMIEZTEAM__2010_
    m|Capitancinema
    n|pfq3vaf2xypwtrv77uw334hb55ctx5qa5wdfa
    o|182
    p|206
    q|45
    r|73
    s|76
    t|src
    u|auto
    v|bufferingMode
    w|id
    x|download
    y|pluginspage
    z|video
    10|type
    11|embedmvshre
    12|cab
    13|DivXBrowserPlugin
    14|codebase
    15|CC0F21721616
    16|9C46
    17|41fa
    18|D0AB
    19|67DABFBF
    1a|clsid
    1b|classid
    1c|embedcontmvshre
    1d|write
    1e|document
    '.split('
    |')))
    '''
    # El javascript desempaquetado es
    #document.write('<object id="embedcontmvshre"classid="clsid:67DABFBF-D0AB-41fa-9C46-CC0F21721616"width="630px"height="320px"codebase="http://go.divx.com/plugin/DivXBrowserPlugin.cab"><param name="custommode"value="none"><param name="bufferingMode"value="auto"><param name="bannerEnabled"value="false"/><param name="autoPlay"value="false"/><param name="src"value="http://76.73.45.206:182/d/pfq3vaf2xypwtrv77uw334hb55ctx5qa5wdfa/Capitancinema.com.-El_Concierto__BrSc__Spanish_HOMIEZTEAM__2010_.avi"/><embed id="embedmvshre"bufferingMode="auto"type="video/divx"src="http://76.73.45.206:182/d/pfq3vaf2xypwtrv77uw334hb55ctx5qa5wdfa/Capitancinema.com.-El_Concierto__BrSc__Spanish_HOMIEZTEAM__2010_.avi"custommode="none"width="630px"height="320px"autoPlay="false"bannerEnabled="false"pluginspage="http://go.divx.com/plugin/download/"></embed></object>');
    '''
    <object id="embedcontmvshre"classid="clsid:67DABFBF-D0AB-41fa-9C46-CC0F21721616"width="630px"height="320px"codebase="http://go.divx.com/plugin/DivXBrowserPlugin.cab">
    <param name="custommode"value="none">
    <param name="bufferingMode"value="auto">
    <param name="bannerEnabled"value="false"/>
    <param name="autoPlay"value="false"/>
    <param name="src"value="http://76.73.45.206:182/d/pfq3vaf2xypwtrv77uw334hb55ctx5qa5wdfa/Capitancinema.com.-El_Concierto__BrSc__Spanish_HOMIEZTEAM__2010_.avi"/>
    <embed id="embedmvshre"bufferingMode="auto"type="video/divx"src="http://76.73.45.206:182/d/pfq3vaf2xypwtrv77uw334hb55ctx5qa5wdfa/Capitancinema.com.-El_Concierto__BrSc__Spanish_HOMIEZTEAM__2010_.avi"custommode="none"width="630px"height="320px"autoPlay="false"bannerEnabled="false"pluginspage="http://go.divx.com/plugin/download/">
    </embed>
    </object>');
    '''
    # La URL del video es 
    #http://76.73.45.206:182/d/pfq3vaf2xypwtrv77uw334hb55ctx5qa5wdfa/Capitancinema.com.-El_Concierto__BrSc__Spanish_HOMIEZTEAM__2010_.avi
    
    # Lo descifra
    descifrado = unpackerjs.unpackjs(data)
    logger.info("descifrado="+descifrado)
    
    # Extrae la URL
    patron = '<param name="src"value="([^"]+)"/>'
    matches = re.compile(patron,re.DOTALL).findall(descifrado)
    scrapertools.printMatches(matches)
    
    url = ""
    
    if len(matches)>0:
        url = matches[0]

    logger.info("[metadivx.py] url="+url)
    return url
