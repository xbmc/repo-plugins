# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Conector para Youtube
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#------------------------------------------------------------
import urlparse,urllib2,urllib,re,httplib
import xbmc,xbmcplugin,xbmcgui
import config

_VALID_URL = r'^((?:http://)?(?:\w+\.)?youtube\.com/(?:(?:v/)|(?:(?:watch(?:\.php)?)?\?(?:.+&)?v=)))?([0-9A-Za-z_-]+)(?(1).+)?$'
AVAILABLE_FORMATS  = ['13','17','5','34','18','35','22','37']
AVAILABLE_FORMATS2 = {'13':'Baja','17':'Media (3gp)','5':'240p (FLV)','34':'360p (FLV)','18':'360p (MP4)','35':'480p (FLV)','22':'720p (HD)','37':'1080p (HD)'}
std_headers = {
	'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US; rv:1.9.1.2) Gecko/20090729 Firefox/3.5.2',
	'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.7',
	'Accept': 'text/xml,application/xml,application/xhtml+xml,text/html;q=0.9,text/plain;q=0.8,image/png,*/*;q=0.5',
	'Accept-Language': 'en-us,en;q=0.5',
}


#### Busca las Urls originales de los formatos de calidad del video
def geturls(id,data):
	reglink = re.compile(r'fmt_stream_map=([^\&]+)\&')
	match = reglink.search(data)
	print 'Encontrado : %s'%str(match)
	if match is not None:
		reglink = match.group(1)
		reglink = urllib.unquote_plus(reglink)
		print 'los links : %s' %reglink
		reglinks= reglink.split(",")
		opciones = []
		links = []
		format = []
		for link in reglinks:
			try:
				fmt = link.replace("|http","*http").split('*')
				opciones.append("Calidad %s" %AVAILABLE_FORMATS2[fmt[0]])
				links.append(fmt[1])
				format.append(fmt[0])
			except:
				pass
				
		dia = xbmcgui.Dialog()
		seleccion = dia.select("Elige una Calidad", opciones)
		xbmc.output("seleccion=%d calidad : (%s) %s " % (seleccion,format[seleccion],AVAILABLE_FORMATS2[format[seleccion]]))
		if seleccion == -1:
			return "Esc"
		return links[seleccion]
	else:
		alertaNone()
	return "Esc"
	
	
def geturl( id ):
	print '[pelisalacarta] youtube.py Modulo: geturl(%s)' %id
	quality = int(config.getSetting("quality_youtube"))
	if id != "":
		url = "http://www.youtube.com/watch?v=%s" % id
		print 'esta es la url: %s'%url
		req = urllib2.Request(url)
		req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
		response=urllib2.urlopen(req)
		data = response.read()
		response.close()
		if data != "":
			print "Calidad encontrada es :%s" %quality
			if quality == 8:
				videourl = geturls(id,data)
				return videourl
			
			regexp = re.compile(r'fmt_stream_map=([^\&]+)\&')
			match = regexp.search(data)
			print 'match : %s'%str(match)
			videourl = ""
			if match is not None:
				fmt_stream_map = urllib.unquote_plus(match.group(1))
				print "fmt_stream_map :%s" %fmt_stream_map
				
				videourls = dict (nvp.replace("|http","*http").split("*") for nvp in fmt_stream_map.split(","))
				print videourls
				
				while True:
					Tquality = AVAILABLE_FORMATS[quality]
					print "AVAILABLE FORMAT :%s %s" %(Tquality,AVAILABLE_FORMATS2[Tquality])
					#videourl1 = "http://www.youtube.com/get_video?t=%s&video_id=%s&fmt=%s" % (  tParam ,id,Tquality)
					try:
						#videourl = verify_url( videourl1.encode( 'utf-8' ) ).decode( 'utf-8' )
						videourl = videourls[Tquality]
						break
					except:
						
						quality -= 1
						if quality == -1:
							break
				try:
					print "Quality Found: (%s) %s " % (AVAILABLE_FORMATS[quality],AVAILABLE_FORMATS2[AVAILABLE_FORMATS[quality]])
				except:
					print "Quality not available, result : -1"
				if videourl == "":
					alertaCalidad()
					return "Esc" 
				return videourl
			else:
				alertaNone()
		else:
			alertaNone()
		
	
	return "Esc"

def GetYoutubeVideoInfo(videoID,eurl=None):
	'''
	Return direct URL to video and dictionary containing additional info
	>> url,info = GetYoutubeVideoInfo("tmFbteHdiSw")
	>>
	'''
	
	if not eurl:
		params = urllib.urlencode({'video_id':videoID})
	else :
		params = urllib.urlencode({'video_id':videoID, 'eurl':eurl})
	try:
		conn = httplib.HTTPConnection("www.youtube.com")
		conn.request("GET","/get_video_info?&%s"%params)
		response = conn.getresponse()
		data = response.read()
	except:
		alertaNone()
		return ""
	video_info = dict((k,urllib.unquote_plus(v)) for k,v in
                               (nvp.split('=') for nvp in data.split('&')))
	
	conn.request('GET','/get_video?video_id=%s&t=%s&fmt=18' %
                         ( video_info['video_id'],video_info['token']))
	response = conn.getresponse()
	direct_url = response.getheader('location')
	return direct_url,video_info
	
def Extract_id(url):
	# Extract video id from URL
	mobj = re.match(_VALID_URL, url)
	if mobj is None:
		print 'ERROR: URL invalida: %s' % url
		alertaIDerror(url)
		return ""
	id = mobj.group(2)
	return id

def verify_url( url ):
	# Extract real URL to video
        request = urllib2.Request(url, None, std_headers)
        data = urllib2.urlopen(request)
        data.read(1)
        url = data.geturl()
        data.close()
        return url
        

def alertaCalidad():
	ventana = xbmcgui.Dialog()
	ok= ventana.ok ("Conector de Youtube", "La calidad elegida en configuracion",'no esta disponible o es muy baja',"elija otra calidad distinta y vuelva a probar")
	
def alertaNone():
	ventana = xbmcgui.Dialog()
	ok= ventana.ok ("Conector de Youtube", "!Aviso¡","El video no se encuentra disponible",'es posible que haya sido removido')
	
def alertaIDerror(url):
	ventana = xbmcgui.Dialog()
	ok= ventana.ok ("Conector de Youtube", "Lo sentimos, no se pudo extraer la ID de la URL"," %s" %url,'la URL es invalida ')
