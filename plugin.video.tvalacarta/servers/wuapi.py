# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Conector para Wuapi
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#------------------------------------------------------------
import urlparse,urllib2,urllib,re
import config

def Wuapi(urloriginal):
	# La URL del vídeo está en un XML
	patronvideos  = 'http://wuapi.com/video/([^?]+)?'
	matches = re.compile(patronvideos,re.DOTALL).findall(urloriginal)
	url = 'http://wuapi.com/vv/'+matches[0]
	#logFile.info('url='+url)
	
	# Lee el XML
	req = urllib2.Request(url)
	req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
	response = urllib2.urlopen(req)
	data=response.read()
	response.close()

	# Saca la URL del video
	patronvideos  = '<ruta_video><\!\[CDATA\[([^\]]+)]]></ruta_video>'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	
	return matches[0]
