# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para documentalesatonline2
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
import xml.dom.minidom
import buscador




CHANNELNAME = "documentalesatonline2"

# Esto permite su ejecución en modo emulado
try:
	pluginhandle = int( sys.argv[ 1 ] )
except:
	pluginhandle = ""

# Traza el inicio del canal
logger.info("[documentalesatonline2.py] init")

DEBUG = True





def mainlist(params,url,category):
	logger.info("[documentalesatonline2.py] mainlist")
	
	xbmctools.addnewfolder( CHANNELNAME , "novedades"  , category , "Novedades"     ,"http://documentalesatonline.loquenosecuenta.com/feed?paged=1","","")
	xbmctools.addnewfolder( CHANNELNAME , "categorias" , category , "Por categorias","http://documentalesatonline.loquenosecuenta.com/","","")
	xbmctools.addnewfolder( CHANNELNAME , "search"     , category , "Buscar"                           ,"","","")
	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )


def search(params,url,category):
	
	buscador.listar_busquedas(params,url,category)
	
	
def searchresults(params,tecleado,category):
	logger.info("[documentalesatonline2.py] search")

	buscador.salvar_busquedas(params,tecleado,category)
	tecleado = tecleado.replace(" ", "+")
	searchUrl = "http://documentalesatonline.loquenosecuenta.com/search/"+tecleado+"?feed=rss2&paged=1"
	novedades(params,searchUrl,category)

def categorias(params,url,category):
	logger.info("[documentalesatonline2.py] novedades")

	# Descarga la página
	data = scrapertools.cachePage(url)
	#logger.info(data)

	# Extrae las entradas (carpetas)
	patronvideos  = '<li class=.cat-item.+?href=\"(.+?)\" .+?>(.+?)</a> \(\d+\)'
	# '\" url nombre cantidad_entradas
	matches = re.compile(patronvideos).findall(data)
	scrapertools.printMatches(matches)

	for match in matches:
	#	scrapedtitle = match[1]+" "+match[2]
	#	scrapedurl = urlparse.urljoin(url,match[0])
	#	scrapedthumbnail = ""
	#	scrapedplot = ""
	#	if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		# Añade al listado de XBMC
		xbmctools.addnewfolder( CHANNELNAME , "novedades" , category , match[1] , match[0] + "feed?paged=1" , "" , "")

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def parsefeedwordpress(url):
	data = scrapertools.cachePage(url)
	doc = xml.dom.minidom.parseString(data)
	#logger.info(doc.toxml().encode("ascii","ignore"))
	items=doc.getElementsByTagName("item")
	returnarray=[];
	
	for item in items:
		#logger.info(item.toxml().encode("ascii","ignore"))
		#logger.info("---------------------------------------")
		#logger.info(item.getElementsByTagName("title")[0].firstChild.wholeText.encode("ascii","ignore"))
		#logger.info(item.getElementsByTagName("link")[0].firstChild.wholeText.encode("ascii","ignore"))
		#logger.info(item.getElementsByTagName("description")[0].firstChild.data.encode("ascii","ignore") )
		returnarray.append([item.getElementsByTagName("title")[0].firstChild.wholeText,item.getElementsByTagName("link")[0].firstChild.wholeText,item.getElementsByTagName("description")[0].firstChild.data])
		
	return(returnarray)	

	

def novedades(params,url,category):
	logger.info("[documentalesatonline2.py] novedades")

	# Descarga la página
	elementos=parsefeedwordpress(url)
	data=""	
	logger.info(str(len(elementos)) + " es la cantidad de elementos")
	if len(elementos)>0:
		
		for j in elementos:
			logger.info(j[0].encode("ascii","ignore")) #titulo 
			logger.info(j[1].encode("ascii","ignore")) #url
			logger.info(j[2].encode("ascii","ignore")) #plot
			
			xbmctools.addnewfolder( CHANNELNAME , "detail" , j[0].encode("utf-8","ignore") , j[0].encode("utf-8","ignore") , j[1].encode("utf-8","ignore") , "" , j[2].encode("utf-8","ignore"))
		
		if len(elementos)==30:
			logger.info("tiene 30 elementos tenemos que poner pagina siguiente")
			patronvideos  = '(.+?paged=)(\d+)'
	# '\" url nombre cantidad_entradas
			matches = re.compile(patronvideos).findall(url)
			if len(matches)>0:
				
				logger.info(matches[0][0])
				numero=(int)(matches[0][1]) + 1
				xbmctools.addnewfolder( CHANNELNAME , "novedades" , category , "pagina siguiente" , matches[0][0] + str(numero) , "" , "")
			else:
				logger.info("no hay matches para anyadir la pagina siguiente")
	#http://documentalesatonline.loquenosecuenta.com/categoria/documentales/feed?paged=3&feed=rss

	

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def detail(params,url,category):
	logger.info("[documentalesatonline2.py] detail")

	#title = unicode( xbmc.getInfoLabel( "ListItem.Title" ), "utf-8" )
	#thumbnail = urllib.unquote_plus( params.get("thumbnail") )
	#plot = unicode( xbmc.getInfoLabel( "ListItem.Plot" ), "utf-8" )

	# Descarga la página
	data = scrapertools.cachePage(url)
	#logger.info(data)
	patronvideos0  = '- [0-9]+? de [0-9]+?:(.+)'
	#- 1 de 3:
	
	
	matches0 = re.compile(patronvideos0).findall(data)
	
	if len(matches0)==0:
		patronvideos0  = 'Episodio \d+(.+)'
		#- Episodio 03:
		matches0 = re.compile(patronvideos0).findall(data)
		#logger.info(matches0)
	
	if len(matches0)>0:
		listavideos = servertools.findvideos(data)
		if (2*len(matches0))==len(listavideos):
			logger.info("es el doble, vamos a anadir un link de megavideo y uno de megaupload por cada fideo")
			length=len(matches0)
			for i in range(len(matches0)):
				
				logger.info(listavideos[0+i][0])
				logger.info(listavideos[0+i][1])
				logger.info(listavideos[0+i][2])
				#logger.info(matches0)
				xbmctools.addvideo( CHANNELNAME , strip_ml_tags(matches0[i]).replace(":","").strip() + " " + listavideos[0+i][0] , listavideos[0+i][1] , category , listavideos[0+i][2] )
				xbmctools.addvideo( CHANNELNAME , strip_ml_tags(matches0[i]).replace(":","").strip() + " " + listavideos[length+i][0] , listavideos[length+i][1] , category , listavideos[length+i][2] )
				 

		else:
			logger.info("vamos a ponerlos con el nombre del titulo todos, el mismo que el por defecto")
			logger.info("no hay capitulos")
			patronvideos  = '(.+?)\('
			matches = re.compile(patronvideos).findall(category)
		# ------------------------------------------------------------------------------------
		# Busca los enlaces a los videos
		# ------------------------------------------------------------------------------------
			listavideos = servertools.findvideos(data)
			
		
			for video in listavideos:
				xbmctools.addvideo( CHANNELNAME , matches[0] +  video[0] , video[1] , category , video[2] )
				#	addvideo( "Mafia rusa.2010 [Megavideo]" , "3KT95673" , "Megavideo" , "")"
			# ------------------------------------------------------------------------------------
		
				
			
		#for i in matches0:
			
		#	logger.info(strip_ml_tags(i))
			
			
		
	else: 
		logger.info("no hay capitulos")
		patronvideos  = '(.+?)\('
		matches = re.compile(patronvideos).findall(category)
	# ------------------------------------------------------------------------------------
	# Busca los enlaces a los videos
	# ------------------------------------------------------------------------------------
		listavideos = servertools.findvideos(data)
		
	
		for video in listavideos:
			xbmctools.addvideo( CHANNELNAME , matches[0] +  video[0] , video[1] , category , video[2] )
		# ------------------------------------------------------------------------------------


	patronvideos  = '<a rel="bookmark" href="../(.+?)">(.+?)<'
	matches = re.compile(patronvideos).findall(data)
	for z in matches:
		xbmctools.addfolder( CHANNELNAME, z[1], "http://documentalesatonline.loquenosecuenta.com/" + z[0], "detail")
		
	

	#<a href="http://programastvonline.blogspot.com/2010/09/cuarto-milenio-6x02-tardigrados-el.html">Cuarto Milenio 6&#215;02: Tardígrados, El Misterio Medjugorje, El fantasma del Verdugo y En los límites del miedo (26-09-10).Online.</a><br />
	patronvideos  = '<a href="(http://programastvonline.blogspot.com.+?)">(.+?)<'
	matches = re.compile(patronvideos).findall(data)
	#logger.info(str(len(matches)) + " no te veo!")
	for z in matches:
		#xbmctools.addnewfolder("programastv","detail",category,z[1],z[0],"","")
		#xbmctools.addnewfolder(canal, accion, category, title, url, thumbnail, plot, Serie, totalItems)
		xbmctools.addfolder("programastv", z[1], z[0], "parsear")
		#xbmctools.addnewfolder(canal, accion, category, title, url, thumbnail, plot, Serie, totalItems)
	#<a rel="bookmark" href="../2010/11/cuarto-milenio-6x06-el-pan-malditoanxelinossenales-del-espacio-exterior-y-murcia-la-torre-de-los-exorcismos-24-10-10-descargaronline/">Cuarto  Milenio 6×06: El pan maldito,Anxeliños,Señales del espacio exterior y  Murcia: La Torre de los exorcismos (24-10-10) (Descargaronline)</a><br />

	
	
	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
		
	# Disable sorting...
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )

	# End of directory...
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )


def strip_ml_tags(in_text):
	#source http://code.activestate.com/recipes/440481-strips-xmlhtml-tags-from-string/
	s_list = list(in_text)
	i = 0

	while i < len(s_list):
		if s_list[i] == '<':
			while s_list[i] != '>':
				s_list.pop(i)
			s_list.pop(i)
		else:
			i=i+1

	join_char=''
	return join_char.join(s_list)





def play(params,url,category):
	logger.info("[documentalesatonline2.py] play")

	title = unicode( xbmc.getInfoLabel( "ListItem.Title" ), "utf-8" )
	thumbnail = "" #urllib.unquote_plus( params.get("thumbnail") )
	plot = "" #unicode( xbmc.getInfoLabel( "ListItem.Plot" ), "utf-8" )
	server = params["server"]
	
	xbmctools.playvideo(CHANNELNAME,server,url,category,title,thumbnail,plot)
