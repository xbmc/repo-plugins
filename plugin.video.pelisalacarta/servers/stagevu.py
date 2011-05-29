# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Conector para stagevu
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
    #print "-------------------------------------------------------"
    #print url
    #print "-------------------------------------------------------"
    req = urllib2.Request(url)
    req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
    response = urllib2.urlopen(req)
    data=response.read()
    response.close()
    #print data

    patronvideos  = '<param name="src" value="([^"]+)"'

    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    i = 0

    #for match in matches:
    #    print "%d %s" % (i , match)
    #    i = i + 1
    if len(matches) > 0:
      return matches[0]
    else:
#      patronvideos = 'type="video/divx" src="([^"]+)"'
      patronvideos = 'src="([^"]+stagevu.com/[^i][^"]+)"' #Forma src="XXXstagevu.com/ y algo distinto de i para evitar images e includes
      matches = re.findall(patronvideos,data)
      if len(matches)>0:
        return matches[0]
      else:
        return "ERROR"
#print "-------------------------------------------------------"
#url="http://stagevu.com/video/jnukfujabtdl"
#print Stagevu(url)
