# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Lista de descargas
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
import downloadtools
import shutil
import config
import logger

# Esto permite su ejecución en modo emulado
try:
	pluginhandle = int( sys.argv[ 1 ] )
except:
	pluginhandle = ""

CHANNELNAME = "descargadoslist"

logger.info("[descargadoslist.py] init")

DEBUG = True

DOWNLOAD_PATH = os.path.join( downloadtools.getDownloadListPath() )
IMAGES_PATH = xbmc.translatePath( os.path.join( os.getcwd(), 'resources' , 'images' ) )
ERROR_PATH = os.path.join( downloadtools.getDownloadListPath(), 'error' )

def mainlist(params,url,category):
	logger.info("[descargadoslist.py] mainlist")

	# Crea el directorio de la lista de descargas si no existe
	try:
		os.mkdir(DOWNLOAD_PATH)
	except:
		pass
	try:
		os.mkdir(ERROR_PATH)
	except:
		pass

	# Crea un listado con las entradas de favoritos
	ficheros = os.listdir(DOWNLOAD_PATH)
	ficheros.sort()
	for fichero in ficheros:
		xbmc.output("fichero="+fichero)
		try:
			# Lee el bookmark
			titulo,thumbnail,plot,server,url = readbookmark(fichero)

			# Crea la entrada
			# En la categoría va el nombre del fichero para poder borrarlo
			xbmctools.addnewvideo( CHANNELNAME , "play" , os.path.join( DOWNLOAD_PATH, fichero ) , server , titulo , url , thumbnail, plot )
		except:
			pass
			logger.info("[downloadall.py] error al leer bookmark")
			for line in sys.exc_info():
				logger.error( "%s" % line )

	xbmctools.addnewvideo( CHANNELNAME , "downloadall" , "category" , "server" , "(Empezar la descarga de la lista)" , "" , os.path.join(IMAGES_PATH, "Crystal_Clear_action_db_update.png"), "" )

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

def errorlist(params,url,category):
	logger.info("[descargadoslist.py] errorlist")

	# Crea el directorio de la lista de descargas con error si no existe
	try:
		os.mkdir(DOWNLOAD_PATH)
	except:
		pass
	try:
		os.mkdir(ERROR_PATH)
	except:
		pass

	# Crea un listado con las entradas de favoritos
	logger.info("[downloadall.py] ERROR_PATH="+ERROR_PATH)
	ficheros = os.listdir(ERROR_PATH)
	for fichero in ficheros:
		logger.info("[downloadall.py] fichero="+fichero)
		try:
			# Lee el bookmark
			titulo,thumbnail,plot,server,url = readbookmarkfile(fichero,ERROR_PATH)

			# Crea la entrada
			# En la categoría va el nombre del fichero para poder borrarlo
			xbmctools.addnewvideo( CHANNELNAME , "playerror" , os.path.join( ERROR_PATH, fichero ) , server , titulo , url , thumbnail, plot )
		except:
			pass
			logger.info("[downloadall.py] error al leer bookmark")
			for line in sys.exc_info():
				logger.error( "%s" % line )

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

def downloadall(params,url,category):
	logger.info("[downloadall.py] downloadall")

	logger.info("[downloadall.py] DOWNLOAD_PATH=%s" % DOWNLOAD_PATH)

	lista = os.listdir(DOWNLOAD_PATH)

	logger.info("[downloadall.py] numero de ficheros=%d" % len(lista))

	# Crea un listado con las entradas de favoritos
	for fichero in lista:
		# El primer video de la lista
		logger.info("[downloadall.py] fichero="+fichero)

		if fichero!="error":
			# Descarga el vídeo
			try:
				# Lee el bookmark
				titulo,thumbnail,plot,server,url = readbookmark(fichero)
				logger.info("[downloadall.py] url="+url)

				# Averigua la URL del vídeo
				if (server=="Megavideo" or server=="Megaupload") and config.getSetting("megavideopremium")=="true":
					if server=="Megaupload":
						mediaurl = servertools.getmegauploadhigh(url)
					else:
						mediaurl = servertools.getmegavideohigh(url)
				else:
					mediaurl = servertools.findurl(url,server)
				logger.info("[downloadall.py] mediaurl="+mediaurl)
				
				# Genera el NFO
				nfofilepath = downloadtools.getfilefromtitle("sample.nfo",titulo)
				outfile = open(nfofilepath,"w")
				outfile.write("<movie>\n")
				outfile.write("<title>"+titulo+")</title>\n")
				outfile.write("<originaltitle></originaltitle>\n")
				outfile.write("<rating>0.000000</rating>\n")
				outfile.write("<year>2009</year>\n")
				outfile.write("<top250>0</top250>\n")
				outfile.write("<votes>0</votes>\n")
				outfile.write("<outline></outline>\n")
				outfile.write("<plot>"+plot+"</plot>\n")
				outfile.write("<tagline></tagline>\n")
				outfile.write("<runtime></runtime>\n")
				outfile.write("<thumb></thumb>\n")
				outfile.write("<mpaa>Not available</mpaa>\n")
				outfile.write("<playcount>0</playcount>\n")
				outfile.write("<watched>false</watched>\n")
				outfile.write("<id>tt0432337</id>\n")
				outfile.write("<filenameandpath></filenameandpath>\n")
				outfile.write("<trailer></trailer>\n")
				outfile.write("<genre></genre>\n")
				outfile.write("<credits></credits>\n")
				outfile.write("<director></director>\n")
				outfile.write("<actor>\n")
				outfile.write("<name></name>\n")
				outfile.write("<role></role>\n")
				outfile.write("</actor>\n")
				outfile.write("</movie>")
				outfile.flush()
				outfile.close()
				logger.info("[downloadall.py] Creado fichero NFO")
				
				# Descarga el thumbnail
				logger.info("[downloadall.py] thumbnail="+thumbnail)
				thumbnailfile = downloadtools.getfilefromtitle(thumbnail,titulo)
				thumbnailfile = thumbnailfile[:-4] + ".tbn"
				logger.info("[downloadall.py] thumbnailfile="+thumbnailfile)
				try:
					downloadtools.downloadfile(thumbnail,thumbnailfile)
					logger.info("[downloadall.py] Thumbnail descargado")
				except:
					logger.info("[downloadall.py] error al descargar thumbnail")
					for line in sys.exc_info():
						logger.error( "%s" % line )
				
				# Descarga el video
				dev = downloadtools.downloadtitle(mediaurl,titulo)
				if dev == -1:
					# El usuario ha cancelado la descarga
					logger.info("[downloadall.py] Descarga cancelada")
					return
				elif dev == -2:
					# Error en la descarga, lo mueve a ERROR y continua con el siguiente
					logger.info("[downloadall.py] ERROR EN DESCARGA DE "+fichero)
					origen = os.path.join( DOWNLOAD_PATH , fichero )
					destino = os.path.join( ERROR_PATH , fichero )
					shutil.move( origen , destino )
				else:
					logger.info("[downloadall.py] Video descargado")
					# Borra el bookmark e itera para obtener el siguiente video
					filepath = os.path.join( DOWNLOAD_PATH , fichero )
					os.remove(filepath)
					logger.info("[downloadall.py] "+fichero+" borrado")
			except:
				logger.info("[downloadall.py] ERROR EN DESCARGA DE "+fichero)
				origen = os.path.join( DOWNLOAD_PATH , fichero )
				destino = os.path.join( ERROR_PATH , fichero )
				shutil.move( origen , destino )

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )
	
def play(params,url,category):
	logger.info("[descargadoslist.py] play")

	title = unicode( xbmc.getInfoLabel( "ListItem.Title" ), "utf-8" )
	thumbnail = xbmc.getInfoImage( "ListItem.Thumb" )
	plot = unicode( xbmc.getInfoLabel( "ListItem.Plot" ), "utf-8" )
	server = params["server"]
	
	xbmctools.playvideo3(CHANNELNAME,server,url,category,title,thumbnail,plot)

def playerror(params,url,category):
	logger.info("[descargadoslist.py] play")

	title = unicode( xbmc.getInfoLabel( "ListItem.Title" ), "utf-8" )
	thumbnail = xbmc.getInfoImage( "ListItem.Thumb" )
	plot = unicode( xbmc.getInfoLabel( "ListItem.Plot" ), "utf-8" )
	server = params["server"]
	
	xbmctools.playvideo4(CHANNELNAME,server,url,category,title,thumbnail,plot)

def readbookmark(filename):
	logger.info("[descargadoslist.py] readbookmark")
	return readbookmarkfile(filename,DOWNLOAD_PATH)

def readbookmarkfile(filename,path):

	filepath = os.path.join( path , filename )

	# Lee el fichero de configuracion
	logger.info("[descargadoslist.py] filepath="+filepath)
	bookmarkfile = open(filepath)

	try:
		lines = bookmarkfile.readlines()

		logger.info("[descargadoslist.py] numero lines=%d" % len(lines))
		try:
			titulo = urllib.unquote_plus(lines[0].strip())
		except:
			titulo = lines[0].strip()
	
		try:
			url = urllib.unquote_plus(lines[1].strip())
		except:
			url = lines[1].strip()
	
		try:
			thumbnail = urllib.unquote_plus(lines[2].strip())
		except:
			thumbnail = lines[2].strip()
	
		if len(lines)>3:
			try:
				server = urllib.unquote_plus(lines[3].strip())
			except:
				server = lines[3].strip()
		else:
			server=""

		if len(lines)>4:
			try:
				plot = urllib.unquote_plus(lines[4].strip())
			except:
				plot = lines[4].strip()
		else:
			plot=""
	except:
		logger.info("[descargadoslist.py] Error inesperado al leer el bookmark")
		for line in sys.exc_info():
			logger.error( "%s" % line )

	bookmarkfile.close();

	return titulo,thumbnail,plot,server,url

def savebookmark(titulo,url,thumbnail,server,plot):
	logger.info("[descargadoslist.py] savebookmark")

	try:
		os.mkdir(DOWNLOAD_PATH)
		os.mkdir(ERROR_PATH)
	except:
		pass

	# No va bien más que en Windows
	#bookmarkfiledescriptor,bookmarkfilepath = tempfile.mkstemp(suffix=".txt",prefix="",dir=DOWNLOAD_PATH)
	
	filenumber=0
	salir = False
	while not salir:
		filename = '%08d.txt' % filenumber
		logger.info("[descargadoslist.py] savebookmark filename="+filename)
		fullfilename = os.path.join(DOWNLOAD_PATH,filename)
		logger.info("[descargadoslist.py] savebookmark fullfilename="+fullfilename)
		if not os.path.exists(fullfilename):
			salir=True
		filenumber = filenumber + 1

	bookmarkfile = open(fullfilename,"w")
	bookmarkfile.write(urllib.quote_plus(downloadtools.limpia_nombre_excepto_1(titulo))+'\n')
	bookmarkfile.write(urllib.quote_plus(url)+'\n')
	bookmarkfile.write(urllib.quote_plus(thumbnail)+'\n')
	bookmarkfile.write(urllib.quote_plus(server)+'\n')
	bookmarkfile.write(urllib.quote_plus(downloadtools.limpia_nombre_excepto_1(plot))+'\n')
	bookmarkfile.flush();
	bookmarkfile.close()
