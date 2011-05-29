# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Conector para tu.tv
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#------------------------------------------------------------

import urlparse,urllib2,urllib,re
import os

try:
    from core import scrapertools
    from core import logger
    from core import config
except:
    from Code.core import scrapertools
    from Code.core import logger
    from Code.core import config

COOKIEFILE = os.path.join(config.get_data_path() , "cookies.lwp")

def geturl(url):
    logger.info("[tutv.py] url="+url)

    if url.startswith("http://"):
        patronvideos  = '"http://tu.tv.*?\&xtp\=([^"]+)"'
        matches = re.compile(patronvideos,re.DOTALL).findall('"'+url+'"')
        i = 0

        if len(matches)==0:
            patronvideos  = '"http://www.tu.tv.*?\&xtp\=([^"]+)"'
            matches = re.compile(patronvideos,re.DOTALL).findall('"'+url+'"')

        i = 0
        codigo = matches[0]
    else:
        codigo = url

    #for match in matches:
    #    print "%d %s" % (i , match)
    #    i = i + 1

    url = "http://tu.tv/visualizacionExterna2.php?web=undefined&codVideo="+codigo
    #print "-------------------------------------------------------"
    #print url
    #print "-------------------------------------------------------"

    req = urllib2.Request(url)
    req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
    response = urllib2.urlopen(req)
    data=response.read()
    response.close()
    #print data

    patronvideos  = 'urlVideo0=([^\&]+)\&'

    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    i = 0

    #for match in matches:
    #    print "%d %s" % (i , match)
    #    i = i + 1
    url = urllib.unquote_plus( matches[0] )

    return url
