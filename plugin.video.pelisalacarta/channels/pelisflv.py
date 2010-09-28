# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para pelisflv.net by Bandavi
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#------------------------------------------------------------
import urlparse,urllib2,urllib,re
import os
import sys
import xbmc
import xbmcgui
import xbmcplugin
import scrapertools
import megavideo
import servertools
import binascii
import xbmctools
import config
import logger
import downloadtools
import vk
from xml.dom import minidom
from xml.dom import EMPTY_NAMESPACE

CHANNELNAME = "pelisflv"
ATOM_NS = 'http://www.w3.org/2005/Atom'
PLAYLIST_FILENAME_TEMP = "video_playlist.temp.pls"
FULL_FILENAME_PATH = os.path.join( downloadtools.getDownloadPath(), PLAYLIST_FILENAME_TEMP )


# Esto permite su ejecución en modo emulado
try:
	pluginhandle = int( sys.argv[ 1 ] )
except:
	pluginhandle = ""

# Traza el inicio del canal
logger.info("[pelisflv.py] init")

DEBUG = True

def mainlist(params,url,category):
	logger.info("[pelisflv.py] mainlist")

	# Añade al listado de XBMC

	xbmctools.addnewfolder( CHANNELNAME , "listvideofeeds" , category , "Listar - Novedades"    ,"http://www.blogger.com/feeds/3207505541212690627/posts/default?start-index=1&max-results=25","","")
	xbmctools.addnewfolder( CHANNELNAME , "listvideos"     , category , "Listar - Estrenos","http://www.pelisflv.net/search/label/Estrenos","","")
	xbmctools.addnewfolder( CHANNELNAME , "ListadoSeries"  , category , "Listar - Generos"        ,"http://www.pelisflv.net/","","")
	#xbmctools.addnewfolder( CHANNELNAME , "ListadoSeries"  , category , "Listar - Series"        ,"http://www.pelisflv.net/","","")
	xbmctools.addnewfolder( CHANNELNAME , "listvideos"     , category , "Listar - Animacion"        ,"http://www.pelisflv.net/search/label/Animaci%C3%B3n","","")
	xbmctools.addnewfolder( CHANNELNAME , "listvideos"     , category , "Listar - Videos no Megavideo (FLV)"        ,"http://www.pelisflv.net/search/label/Flv","","")
	xbmctools.addnewfolder( CHANNELNAME , "listvideos"     , category , "Listar - Videos en Megavideo"        ,"http://www.pelisflv.net/search/label/Megavideo","","")
	xbmctools.addnewfolder( CHANNELNAME , "listvideos"     , category , "Videos Audio Español"        ,"http://www.pelisflv.net/search/label/Espa%C3%B1ol","","")
	xbmctools.addnewfolder( CHANNELNAME , "listvideos"     , category , "Videos Audio Latino"        ,"http://www.pelisflv.net/search/label/Latino","","")
	xbmctools.addnewfolder( CHANNELNAME , "listvideos"     , category , "Videos Audio Original Sub Español"        ,"http://www.pelisflv.net/search/label/Sub%20Espa%C3%B1ol","","")
	xbmctools.addnewfolder( CHANNELNAME , "search"         , category , "Buscar","http://www.pelisflv.net/","","")
	

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )

	# Disable sorting...
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )

	# End of directory...
	xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

def search(params,url,category):
	logger.info("[pelisflv.py] search")

	keyboard = xbmc.Keyboard()
	#keyboard.setDefault('')
	keyboard.doModal()
	if (keyboard.isConfirmed()):
		tecleado = keyboard.getText()
		if len(tecleado)>0:
			#convert to HTML
			tecleado = tecleado.replace(" ", "+")
			searchUrl = "http://www.pelisflv.net/search?q="+tecleado
			listvideos(params,searchUrl,category)

def searchresults(params,url,category):
	logger.info("[pelisflv.py] SearchResult")
	
	
	# Descarga la página
	data = scrapertools.cachePage(url)
	#print data
	# Extrae las entradas (carpetas)
	patronvideos  = '<div class="poster">[^<]+<a href="([^"]+)"'                          # URL
	patronvideos += '><img src="([^"]+)" width=[^\/]+\/>'                                 # TUMBNAIL
	patronvideos += '</a>[^<]+<[^>]+>[^<]+<[^>]+>[^<]+<a href="[^"]+">([^<]+)</a>'        # TITULO 
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)

	for match in matches:
		# Atributos
		scrapedurl = match[0]
		
		scrapedtitle =match[2]
		scrapedtitle = scrapedtitle.replace("&#8211;","-")
		scrapedtitle = scrapedtitle.replace("&nbsp;"," ")
		scrapedthumbnail = match[1]
		scrapedplot = ""
		if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		# Añade al listado de XBMC
		xbmctools.addnewfolder( CHANNELNAME , "detail" , category , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )

	# Propiedades
	xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )
			


def ListadoCapitulosSeries(params,url,category):
	logger.info("[pelisflv.py] ListadoCapitulosSeries")
	title = urllib.unquote_plus( params.get("title") )
	thumbnail = urllib.unquote_plus( params.get("thumbnail") )
	
	# Descarga la página
	data = scrapertools.downloadpageGzip(url)
	#logger.info(data)

	# Patron de las entradas

	patron = "<div class='post-body entry-content'>(.*?)<div class='post-footer'>"
	matches = re.compile(patron,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)
	

	patron = '<a href="([^"]+)"[^>]+><[^>]+>(.*?)<'
	matches = re.compile(patron,re.DOTALL).findall(matches[0])
	scrapertools.printMatches(matches)
	patron2 = '<iframe src="([^"]+)"'
	
	# Añade las entradas encontradas
	for match in matches:
		# Atributos
		scrapedtitle = match[1]
		data2 = scrapertools.downloadpageGzip(match[0])
		matches2 = re.compile(patron2,re.DOTALL).findall(data2)
		scrapertools.printMatches(matches2)	
		scrapedurl = matches2[0]
		scrapedthumbnail = thumbnail
		scrapedplot = ""
		if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		# Añade al listado de XBMC
		xbmctools.addnewfolder( CHANNELNAME , "detail" , category , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )

	# Asigna el título, desactiva la ordenación, y cierra el directorio
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )
        

def ListadoSeries(params,url,category):
	logger.info("[pelisflv.py] ListadoSeries")
	title = urllib.unquote_plus( params.get("title") )
	# Descarga la página
	data = scrapertools.cachePage(url)
	#logger.info(data)

	# Patron de las entradas
	if "Series" in title:
		patron = "<center><form>(.*?)</form></center>"
		matches = re.compile(patron,re.DOTALL).findall(data)
		scrapertools.printMatches(matches)
	
		patron = '<option value="([^"]+)" />(.*?)\n'
		matches = re.compile(patron,re.DOTALL).findall(matches[0])
		scrapertools.printMatches(matches)
	
	elif "Generos" in title:
		
		patron = "<h2>Generos</h2>[^<]+<[^>]+>[^<]+<ul>(.*?)</ul>"
		matches = re.compile(patron,re.DOTALL).findall(data)
		scrapertools.printMatches(matches)
	
		patron = "<a dir='ltr' href='([^']+)'>(.*?)</a>"
		matches = re.compile(patron,re.DOTALL).findall(matches[0])
		scrapertools.printMatches(matches)

	# Añade las entradas encontradas
	for match in matches:
		# Atributos
		scrapedtitle = match[1]
		scrapedurl = match[0]
		scrapedthumbnail = ""
		scrapedplot = ""
		if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		# Añade al listado de XBMC
		xbmctools.addnewfolder( CHANNELNAME , "listvideos" , category , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )

	# Asigna el título, desactiva la ordenación, y cierra el directorio
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )
        

def listvideos(params,url,category):
	logger.info("[pelisflv.py] listvideos")

	if url=="":
		url = "http://www.pelisflv.net/"
                
	# Descarga la página
	data = scrapertools.cachePage(url)
	#logger.info(data)


	# Extrae las entradas (carpetas)
	patronvideos  = "<h3 class='post-title entry-title'>[^<]+<a href='([^']+)'"  # URL
	patronvideos += ">([^<]+)</a>.*?"                                            # Titulo   
	patronvideos += '<img style="[^"]+" src="([^"]+).*?'           # TUMBNAIL               
	patronvideos += 'border=[^>]+>.*?<span[^>]+>(.*?)</span></div>'        # Argumento	
	#patronvideos += '</h1>[^<]+</div>.*?<div class=[^>]+>[^<]+'
	#patronvideos += '</div>[^<]+<div class=[^>]+>.*?href="[^"]+"><img '                    
	#patronvideos += 'style=.*?src="([^"]+)".*?alt=.*?bold.*?>(.*?)</div>'                  # IMAGEN , DESCRIPCION
	#patronvideos += '.*?flashvars="file=(.*?flv)\&amp'                                      # VIDEO FLV 
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)
	scrapedtitle = ""
	for match in matches:
		# Titulo
		
		scrapedtitle = match[1]
		# URL
		scrapedurl = match[0]
		# Thumbnail
		scrapedthumbnail = match[2]
         
		# Argumento
		scrapedplot = match[3]
		scrapedplot = re.sub("<[^>]+>"," ",scrapedplot)
		scrapedplot = scrapedplot.replace('&#8220;','"')
		scrapedplot = scrapedplot.replace('&#8221;','"')
		scrapedplot = scrapedplot.replace('&#8230;','...')
		scrapedplot = scrapedplot.replace("&nbsp;","")

		# Depuracion
		if (DEBUG):
			logger.info("scrapedtitle="+scrapedtitle)
			logger.info("scrapedurl="+scrapedurl)
			logger.info("scrapedthumbnail="+scrapedthumbnail)

		
			# Añade al listado de XBMC
			xbmctools.addnewfolder( CHANNELNAME , "detail" , category , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )

	# Extrae la marca de siguiente página

	patronvideos  = "<div class='status-msg-hidden'>.*?<a href=\"([^\"]+)\""
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)

	if len(matches)>0:
		scrapedtitle = "Página siguiente"
		scrapedurl = matches[0]
		scrapedthumbnail = ""
		scrapedplot = ""
		xbmctools.addnewfolder( CHANNELNAME , "listvideos" , category , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )

	# Disable sorting...
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )

	# End of directory...
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def listvideofeeds(params,url,category):
	logger.info("[pelisflv.py] listvideosfeeds")
	data = None
	thumbnail = ""
	xmldata = urllib2.urlopen(url,data)
	
	xmldoc = minidom.parse(xmldata)
	xmldoc.normalize()
	#print xmldoc.toxml().encode('utf-8')
	xmldata.close()
	c = 0
	for entry in xmldoc.getElementsByTagNameNS(ATOM_NS, u'entry'):
	#First title element in doc order within the entry is the title
		entrytitle = entry.getElementsByTagNameNS(ATOM_NS, u'title')[0]
		entrylink = entry.getElementsByTagNameNS(ATOM_NS, u'link')[2]
		entrythumbnail = entry.getElementsByTagNameNS(ATOM_NS, u'content')[0]
		etitletext = get_text_from_construct(entrytitle)
		elinktext = entrylink.getAttributeNS(EMPTY_NAMESPACE, u'href')
		ethumbnailtext = get_text_from_construct(entrythumbnail)
		regexp = re.compile(r'src="([^"]+)"')
		match = regexp.search(ethumbnailtext)
		if match is not None:
			thumbnail = match.group(1)
		regexp = re.compile(r'bold;">([^<]+)<')
		match = regexp.search(ethumbnailtext)
		if match is not None:
			plot = match.group(1)
		
		# Depuracion
		if (DEBUG):
			logger.info("scrapedtitle="+etitletext)
			logger.info("scrapedurl="+elinktext)
			logger.info("scrapedthumbnail="+thumbnail)
				
		#print etitletext, '(', elinktext, thumbnail,plot, ')'
		xbmctools.addnewfolder( CHANNELNAME , "detail" , category ,  etitletext,  elinktext, thumbnail, plot )
		c +=1
	
	if c >= 25:
		regexp = re.compile(r'start-index=([^\&]+)&')
		match = regexp.search(url)
		if match is not None:
			start_index = int(match.group(1)) + 25
		scrapedtitle = "Página siguiente"
		scrapedurl =  "http://www.blogger.com/feeds/3207505541212690627/posts/default?start-index="+str(start_index)+"&max-results=25"
		scrapedthumbnail = ""
		scrapedplot = ""
		xbmctools.addnewfolder( CHANNELNAME , "listvideofeeds" , category , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )

	# Cierra el directorio
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )
	
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


	
def detail(params,url,category):
	logger.info("[pelisflv.py] detail")

	title = urllib.unquote_plus( params.get("title") )
	thumbnail = urllib.unquote_plus( params.get("thumbnail") )
	plot = urllib.unquote_plus( params.get("plot") )
	accion = params.get("accion")

	# Descarga la página
	datafull = scrapertools.cachePage(url)
	#logger.info(data)
	patron = "google_ad_section_start(.*?)google_ad_section_end -->"
	matches = re.compile(patron,re.DOTALL).findall(datafull)

	if len(matches)>0:
		data = matches[0]
	else:
		data = datafull
	patron = '<iframe src="(http://pelisflv.net63.net/player/[^"]+)"'
	matches = re.compile(patron,re.DOTALL).findall(data)
	if len(matches)>0:
		data = scrapertools.cachePage(matches[0])
	ok = False               
          
	# ------------------------------------------------------------------------------------
	# Busca los enlaces a los videos
	# ------------------------------------------------------------------------------------
	
	listavideos = servertools.findvideos(data)

	for video in listavideos:
		videotitle = video[0]
		url = video[1]
		server = video[2]
		
		xbmctools.addnewvideo( CHANNELNAME , "play" , category , server , title.strip() + " - " + videotitle , url , thumbnail , plot )
	
	# Busca enlaces en el servidor Stagevu - "el modulo servertools.findvideos() no los encuentra"
	
	patronvideos  = "'(http://stagevu.com[^']+)'"
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	if len(matches)>0:
		logger.info(" Servidor Stagevu")
		for match in matches:
			ok = True
			scrapedurl = match.replace("&amp;","&")
			xbmctools.addnewvideo( CHANNELNAME ,"play"  , category , "Stagevu" , title+" - [Stagevu]", scrapedurl , thumbnail , plot )

	# Busca enlaces en el servidor Movshare - "el modulo servertools.findvideos() no los encuentra"
	
	patronvideos  = "'(http://www.movshare.net[^']+)'"
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	if len(matches)>0:
		logger.info(" Servidor Movshare")
		for match in matches:
			ok = True
			scrapedurl = match.replace("&amp;","&")
			xbmctools.addnewvideo( CHANNELNAME ,"play"  , category , "Movshare" , title+" - [Movshare]", scrapedurl , thumbnail , plot )


		
	# ------------------------------------------------------------------------------------
        #--- Busca los videos Directos
        
	patronvideos = 'file=(http\:\/\/[^\&]+)\&'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)
	print "link directos encontrados :%s" %matches

	#print data
	if len(matches)>0:
		for match in matches:
			subtitle = "[FLV-Directo]"
			if ("xml" in match):
				data2 = scrapertools.cachePage(match)
				logger.info("data2="+data2)
				patronvideos  = '<track>.*?'
				patronvideos += '<title>([^<]+)</title>[^<]+'
				patronvideos += '<location>([^<]+)</location>(?:[^<]+'
				patronvideos += '<meta rel="type">video</meta>[^<]+|[^<]+)'
				patronvideos += '<meta rel="captions">([^<]+)</meta>[^<]+'
				patronvideos += '</track>'
				matches2 = re.compile(patronvideos,re.DOTALL).findall(data2)
				scrapertools.printMatches(matches)
				
				for match2 in matches2:
					sub = ""
					playWithSubt = "play"
					if match2[2].endswith(".xml"): # Subtitulos con formato xml son incompatibles con XBMC
						sub = "[Subtitulo incompatible con xbmc]"
						
					if ".mp4" in match2[1]:
						subtitle = "[MP4-Directo]"
					scrapedtitle = '%s  - (%s)  %s' %(title,match2[0],subtitle)
					
					scrapedurl = match2[1].strip()
					scrapedthumbnail = thumbnail
					scrapedplot = plot
					
					if match2[2].endswith(".srt"): 
						scrapedurl = scrapedurl + "|" + match2[2]
						playWithSubt = "play2"
							
					if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")
							
					# Añade al listado de XBMC
					xbmctools.addnewvideo( CHANNELNAME , playWithSubt , category , "Directo" , scrapedtitle, scrapedurl , scrapedthumbnail, scrapedplot )
					ok = True
			else:
				if match.endswith(".srt"):
					scrapedurl = scrapedurl + "|" + match 
					xbmctools.addnewvideo( CHANNELNAME ,"play2"  , category , "Directo" , title + " (V.O.S) - "+subtitle, scrapedurl , thumbnail , plot )
					ok = True
				if 	match.endswith(".xml"):
					sub = "[Subtitulo incompatible con xbmc]"
					xbmctools.addnewvideo( CHANNELNAME ,"play"  , category , "Directo" , title + " (V.O) - %s %s" %(subtitle,sub), scrapedurl , thumbnail , plot )
					ok = True
				scrapedurl = match
				print scrapedurl
	#src="http://pelisflv.net63.net/player/videos.php?x=http://pelisflv.net63.net/player/xmls/The-Lord-Of-The-Ring.xml"			
	patronvideos = '(http\:\/\/[^\/]+\/[^\/]+\/[^\/]+\/[^\.]+\.xml)'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)
	#print data
	
	if len(matches)>0:
		playlistFile = open(FULL_FILENAME_PATH,"w")
		playlistFile.write("[playlist]\n")
		playlistFile.write("\n")
		for match in matches:
			subtitle = "[FLV-Directo]"
					

			data2 = scrapertools.cachePage(match.replace(" ","%20"))
			logger.info("data2="+data2)
			patronvideos  = '<track>.*?'
			patronvideos += '<title>([^<]+)</title>.*?'
			patronvideos += '<location>([^<]+)</location>(?:[^<]+'
			patronvideos += '<meta rel="captions">([^<]+)</meta>[^<]+'
			patronvideos += '|([^<]+))</track>'
			matches2 = re.compile(patronvideos,re.DOTALL).findall(data2)
			scrapertools.printMatches(matches)
			c = 0
			for match2 in matches2:
				c +=1
				sub = ""
				playWithSubt = "play"
				if match2[2].endswith(".xml"): # Subtitulos con formato xml son incompatibles con XBMC
					sub = "[Subtitulo incompatible con xbmc]"
					
				if  match2[1].endswith(".mp4"):
					subtitle = "[MP4-Directo]"
				scrapedtitle = '%s  - (%s)  %s' %(title,match2[0],subtitle)
				
				scrapedurl = match2[1].strip()
				scrapedthumbnail = thumbnail
				scrapedplot = plot
				
				if match2[2].endswith(".srt"): 
					scrapedurl = scrapedurl + "|" + match2[2]
					playWithSubt = "play2"
						
				if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")
						
				# Añade al listado de XBMC
				xbmctools.addnewvideo( CHANNELNAME , playWithSubt , category , "Directo" , scrapedtitle, scrapedurl , scrapedthumbnail, scrapedplot )					
				ok =True
				
				playlistFile.write("File%d=%s\n"  %(c,match2[1]))
				playlistFile.write("Title%d=%s\n" %(c,match2[0]))
				playlistFile.write("\n")
				
			
			playlistFile.write("NumberOfEntries=%d\n" %c)
			playlistFile.write("Version=2\n")
			playlistFile.flush();
			playlistFile.close()
			xbmctools.addnewvideo( CHANNELNAME , "play" , category , "Directo" , "Reproducir Todo a la vez...", FULL_FILENAME_PATH , scrapedthumbnail, scrapedplot )
	
	# Busca enlaces en el servidor Videoweed - "el modulo servertools.findvideos() no los encuentra"
	patronvideos = '(http\:\/\/[^\.]+\.videoweed.com\/[^"]+)"'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)
	if len(matches)>0:
		logger.info(" Servidor Videoweed")
		for match in matches:
			ok = True
			scrapedurl = match.replace("&amp;","&")
			xbmctools.addnewvideo( CHANNELNAME ,"play"  , category , "Videoweed" , title+" - [Videoweed]", scrapedurl , thumbnail , plot )		
	
	# Busca enlaces en el servidor Gigabyteupload # http://cdn-2.gigabyteupload.com/files/207bb7b658d5068650ebabaca8ffc52d/vFuriadeTitanes_newg.es.avi
	patronvideos = '(http\:\/\/[^\.]+\.gigabyteupload.com\/[^"]+)"'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)
	if len(matches)>0:
		logger.info(" Servidor Gigabyteupload")
		for match in matches:
			ok = True
			xbmctools.addnewvideo( CHANNELNAME ,"play"  , category , "Gigabyteupload" , title+" - [Gigabyteupload]",match  , thumbnail , plot )

	## --------------------------------------------------------------------------------------##
	#            Busca enlaces de videos para el servidor vk.com                             #
	## --------------------------------------------------------------------------------------##
	'''
	var video_host = '447.gt3.vkadre.ru';
	var video_uid = '0';
	var video_vtag = '2638f17ddd39-';
	var video_no_flv = 0;
	var video_max_hd = '0';
	var video_title = 'newCine.NET+-+neWG.Es+%7C+Chicken+Little';

	'''
	patronvideos = '<iframe src="(http://[^\/]+\/video_ext.php[^"]+)"'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	if len(matches)>0:
		ok = True
		print " encontro VK.COM :%s" %matches[0]

 		videourl = 	vk.geturl(matches[0])
 		xbmctools.addnewvideo( CHANNELNAME , "play" , category , "Directo" , title + " - "+"[VK]", videourl , thumbnail , plot )		
 	"""	
		data2 = scrapertools.downloadpageGzip(matches[0].replace("amp;",""))
		print data2
		regexp =re.compile(r'vkid=([^\&]+)\&')
		match = regexp.search(data2)
		vkid = ""
		print 'match %s'%str(match)
		if match is not None:
			vkid = match.group(1)
		else:
			print "no encontro vkid"
			
		patron  = "var video_host = '([^']+)'.*?"
		patron += "var video_uid = '([^']+)'.*?"
		patron += "var video_vtag = '([^']+)'.*?"
		patron += "var video_no_flv = ([^;]+);.*?"
		patron += "var video_max_hd = '([^']+)'"
		matches2 = re.compile(patron,re.DOTALL).findall(data2)
		if len(matches2)>0:    
			for match in matches2:
				if match[3].strip() == "0" and match[1] != "0":
					tipo = "flv"

					if "http://" in match[0]:
						videourl = "%s/u%s/video/%s.%s" % (match[0],match[1],match[2],tipo)
					else:
						videourl = "http://%s/u%s/video/%s.%s" % (match[0],match[1],match[2],tipo)
					xbmctools.addnewvideo( CHANNELNAME , "play" , category , "Directo" , title + " - "+"[VK] [%s]" %tipo, videourl , thumbnail , plot )

				elif match[1]== "0" and vkid != "":     #http://447.gt3.vkadre.ru/assets/videos/2638f17ddd39-75081019.vk.flv 
					tipo = "flv"

					if "http://" in match[0]:
						videourl = "%s/assets/videos/%s%s.vk.%s" % (match[0],match[2],vkid,tipo)
					else:
						videourl = "http://%s/assets/videos/%s%s.vk.%s" % (match[0],match[2],vkid,tipo)
					xbmctools.addnewvideo( CHANNELNAME , "play" , category , "Directo" , title + " - "+"[VK] [%s]" %tipo, videourl , thumbnail , plot )
				else:
					tipo = "360.mp4"
					videourl = "%s/u%s/video/%s.%s" % (match[0],match[1],match[2],tipo)
					xbmctools.addnewvideo( CHANNELNAME , "play" , category , "Directo" , title + " - "+"[VK] [%s]" %tipo, videourl , thumbnail , plot )
					tipo = "240.mp4"
					videourl = "%s/u%s/video/%s.%s" % (match[0],match[1],match[2],tipo)
					xbmctools.addnewvideo( CHANNELNAME , "play" , category , "Directo" , title + " - "+"[VK] [%s]" %tipo, videourl , thumbnail , plot )
		
	"""
	if not ok:
		patron = "SeriesPage"
		matches = re.compile(patron,re.DOTALL).findall(datafull)
		if len(matches)>0:
			ListadoCapitulosSeries(params,url,category)
	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
		
	# Disable sorting...
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )

	# End of directory...
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )


def play(params,url,category):
	logger.info("[pelisflv.py] play")

	title = unicode( xbmc.getInfoLabel( "ListItem.Title" ), "utf-8" )
	thumbnail = urllib.unquote_plus( params.get("thumbnail") )
	plot = unicode( xbmc.getInfoLabel( "ListItem.Plot" ), "utf-8" )
	server = params["server"]

	xbmctools.playvideo(CHANNELNAME,server,url,category,title,thumbnail,plot)

def play2(params,url,category):
	logger.info("[pelisflv.py] play2")
	url1 = url
	if "|" in url:
		urlsplited = url.split("|")
		url1 = urlsplited[0]
		urlsubtit = urlsplited[1]
		subt_ok = "0"
		count = 0
		while subt_ok == "0":
			if count==0:
				subt_ok = downloadstr(urlsubtit)
				count += 1 
			print "subtitulo subt_ok = %s" % str(subt_ok)
			if subt_ok is None: # si es None la descarga del subtitulo esta ok
				config.setSetting("subtitulo", "true")
				break
	play(params,url1,category)

def acentos(title):

        title = title.replace("Ã‚Â", "")
        title = title.replace("ÃƒÂ©","é")
        title = title.replace("ÃƒÂ¡","á")
        title = title.replace("ÃƒÂ³","ó")
        title = title.replace("ÃƒÂº","ú")
        title = title.replace("ÃƒÂ­","í")
        title = title.replace("ÃƒÂ±","ñ")
        title = title.replace("Ã¢â‚¬Â", "")
        title = title.replace("Ã¢â‚¬Å“Ã‚Â", "")
        title = title.replace("Ã¢â‚¬Å“","")
        title = title.replace("Ã©","é")
        title = title.replace("Ã¡","á")
        title = title.replace("Ã³","ó")
        title = title.replace("Ãº","ú")
        title = title.replace("Ã­","í")
        title = title.replace("Ã±","ñ")
        title = title.replace("Ãƒâ€œ","Ó")
        return(title)
        
def downloadstr(urlsub):
	
	import downloadtools
	
	fullpath = os.path.join( config.DATA_PATH , 'subtitulo.srt' )
	if os.path.exists(fullpath):
		try:
			subtitfile = open(fullpath,"w")
			subtitfile.close()
		except IOError:
			logger.info("Error al limpiar el archivo subtitulo.srt "+fullpath)
			raise
	try:		
		ok = downloadtools.downloadfile(urlsub,fullpath)
	except IOError:
		logger.info("Error al descargar el subtitulo "+urlsub)
		return -1
	return ok

        
