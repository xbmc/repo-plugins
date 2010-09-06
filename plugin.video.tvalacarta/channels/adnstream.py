# -*- coding: utf-8 -*-

import urlparse,urllib2,urllib,re
import os
import sys
import xbmc
import xbmcgui
import xbmcplugin
import scrapertools

try:
	pluginhandle = int( sys.argv[ 1 ] )
except:
	pluginhandle = ""

DEBUG = True
CHANNELNAME = "ADNStream"
CHANNELCODE = "adnstream"
IMAGES_PATH = xbmc.translatePath( os.path.join( os.getcwd(), 'resources' , 'images' , 'adnstream' ) )
ADNURL = 'http://www.adnstream.tv/canales.php?prf=box'

searchresultsnum = 50

def mainlist(params,url,category):
	xbmc.output("adnstream.actionlist")

	#53=wall
	#xbmc.executebuiltin("Container.SetViewMode(53)")
	#50=full list
	#xbmc.executebuiltin("Container.SetViewMode(50)")

	# Lee la URL de la página con las entradas
	if params.has_key("url"):
		url = urllib.unquote_plus( params.get("url") )
		primera = False
	else:
		url=ADNURL
		primera = True
	xbmc.output("url="+url)

	# Lee la categoría de la página
	if params.has_key("category"):
		categoria = urllib.unquote_plus( params.get("category") )
	else:
		categoria='ADNStream'

	# Verifica actualizaciones solo en el primer nivel
	if primera:
		scrapedtitle = "Buscar..."
		listitem = xbmcgui.ListItem( scrapedtitle, iconImage="DefaultFolder.png" , thumbnailImage=os.path.join(IMAGES_PATH, "busqueda.jpg") )
		itemurl = '%s?channel=adnstream&action=search&category=%s' % ( sys.argv[ 0 ] , urllib.quote_plus( scrapedtitle ) )
		xbmcplugin.addDirectoryItem( handle = int(sys.argv[ 1 ]), url = itemurl , listitem=listitem, isFolder=True)

	# Descarga la página
	data = scrapertools.cachePage(url)
	#print data

	# Extrae las entradas (carpetas)
	patronvideos  = '<channel title\="([^"]+)" media\:thumbnail\="([^"]+)" clean_name\="([^"]+)"></channel>'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	"""
	if (DEBUG):
		print "-- CANALES --"
		scrapertools.printMatches(matches)
		print "-- CANALES --"
	"""
	for match in matches:
		# Titulo
		try:
			scrapedtitle = unicode( match[0], "utf-8" ).encode("iso-8859-1")
		except:
			scrapedtitle = match[0]

		# URL
		scrapedurl = ADNURL+'&c='+match[2]
		
		# Thumbnail
		scrapedthumbnail = match[1]
		
		# Depuracion
		#if (DEBUG):
		#	print "scrapedtitle="+scrapedtitle
		#	print "scrapedurl="+scrapedurl
		#	print "scrapedthumbnail="+scrapedthumbnail

		# Añade al listado de XBMC
		listitem = xbmcgui.ListItem( scrapedtitle, iconImage="DefaultFolder.png", thumbnailImage=scrapedthumbnail )
		itemurl = '%s?channel=adnstream&action=mainlist&category=%s&url=%s' % ( sys.argv[ 0 ] , urllib.quote_plus( scrapedtitle ) , urllib.quote_plus( scrapedurl ) )
		xbmcplugin.addDirectoryItem( handle = int(sys.argv[ 1 ]), url = itemurl , listitem=listitem, totalItems=len(matches), isFolder=True)

	# Extrae las entradas (Vídeos)
	patronpubli   = '<item>[^<]+<guid>[^<]+</guid>[^<]+<title>[^<]+</title>[^<]+<description />[^<]+<enclosure type="[^"]+" url="([^"]+)"/>[^<]+<link />[^<]+<category>preroll</category>.*?'
	patronvideos  = '<item>[^<]+<guid>([^<]+)</guid>[^<]+<title>([^<]+)</title>[^<]+<description>([^<]+)</description>[^<]+<enclosure type="([^"]+)" url="([^"]+)"/>[^<]+<media\:thumbnail type="[^"]+" url="([^"]+)"/>[^<]+<link>[^<]+</link>([^<]+<minimum_age>18</minimum_age>)?[^<]+(<featured>1</featured>[^<]+)?</item>'
	matches = re.compile(patronpubli+patronvideos,re.DOTALL).findall(data)
	nopubli = False
	indicenopub = 0
	if(len(matches)==0):
		nopubli = True
		indicenopub = -1
		matches = re.compile(patronvideos,re.DOTALL).findall(data)
	
	"""
	if (DEBUG):
		print "-- VIDEOS --"
		scrapertools.printMatches(matches)
		print "-- VIDEOS --"
	"""
	for match in matches:
		# Video page
		if(nopubli==False):
			scrapedad = match[0]
		else:
			scrapedad = ""
		
		# Title
		try:
			scrapedtitle = unicode( match[2+indicenopub], "utf-8" ).encode("iso-8859-1")
		except:
			scrapedtitle = match[2+indicenopub]

		try:
			scrapeddescription = unicode( match[3+indicenopub], "utf-8" ).encode("iso-8859-1")
		except:
			scrapeddescription = match[3+indicenopub]

		# Video page
		scrapedurl = match[5+indicenopub]
		
		# Thumb
		scrapedthumbnail = match[6+indicenopub]
		
		scrapedage = match[7+indicenopub]
		if scrapedage!='':
			scrapedage='18'
		
		# Prueba para Videoclub
		# Si la URL no contiene "http" es Videoclub, y le metemos un random, para que XBMC no crea que son las mismas películas
		if(not "http" in scrapedurl):
			scrapedurl = scrapedurl + "_" + scrapertools.getRandom(scrapedtitle)
		
		# Debug info...
		if (DEBUG) :
			xbmc.output("scrapedad="+scrapedad)
			xbmc.output( "scrapedtitle="+scrapedtitle)
			#print "scrapeddescription="+scrapeddescription
			xbmc.output( "scrapedurl="+scrapedurl)
			xbmc.output( "scrapedthumbnail="+scrapedthumbnail)
			xbmc.output( "scrapedage="+scrapedage)
		
		# Add to list...
		listitem = xbmcgui.ListItem( scrapedtitle, iconImage="DefaultVideo.png", thumbnailImage=scrapedthumbnail )
		listitem.setInfo( "video", { "Title" : scrapedtitle, "Plot" : scrapeddescription } )
		itemurl = '%s?channel=adnstream&action=play&category=%s&url=%s&ad=%s&age=%s' % ( sys.argv[ 0 ] , params["category"] , urllib.quote_plus( scrapedurl ) , urllib.quote_plus( scrapedad ) , scrapedage )
		xbmcplugin.addDirectoryItem( handle=int(sys.argv[ 1 ]), url=itemurl, listitem=listitem, totalItems=len(matches), isFolder=False)

	if primera:
		# Canales especiales
		scrapedtitle = "Los más valorados"
		scrapedurl = "http://www.adnstream.tv/canal_magico.new.php?i=0&n=30&c=masvalorados"
		listitem = xbmcgui.ListItem( scrapedtitle, iconImage="DefaultFolder.png" , thumbnailImage=os.path.join(IMAGES_PATH, "masvalorados.jpg") )
		itemurl = '%s?channel=adnstream&action=mainlist&category=%s&url=%s' % ( sys.argv[ 0 ] , urllib.quote_plus( scrapedtitle ) , urllib.quote_plus( scrapedurl ) )
		xbmcplugin.addDirectoryItem( handle = int(sys.argv[ 1 ]), url = itemurl , listitem=listitem, isFolder=True)

		scrapedtitle = "Los más vistos"
		scrapedurl = "http://www.adnstream.tv/canal_magico.new.php?i=0&n=30&c=masvistos"
		listitem = xbmcgui.ListItem( scrapedtitle, iconImage="DefaultFolder.png" , thumbnailImage=os.path.join(IMAGES_PATH, "masvistos.jpg") )
		itemurl = '%s?channel=adnstream&action=mainlist&category=%s&url=%s' % ( sys.argv[ 0 ] , urllib.quote_plus( scrapedtitle ) , urllib.quote_plus( scrapedurl ) )
		xbmcplugin.addDirectoryItem( handle = int(sys.argv[ 1 ]), url = itemurl , listitem=listitem, isFolder=True)

		scrapedtitle = "Novedades"
		scrapedurl = "http://www.adnstream.tv/canal_magico.new.php?i=0&n=30&c=novedades"
		listitem = xbmcgui.ListItem( scrapedtitle, iconImage="DefaultFolder.png" , thumbnailImage=os.path.join(IMAGES_PATH, "New.jpg") )
		itemurl = '%s?channel=adnstream&action=mainlist&category=%s&url=%s' % ( sys.argv[ 0 ] , urllib.quote_plus( scrapedtitle ) , urllib.quote_plus( scrapedurl ) )
		xbmcplugin.addDirectoryItem( handle = int(sys.argv[ 1 ]), url = itemurl , listitem=listitem, isFolder=True)

		scrapedtitle = "Destacados"
		scrapedurl = "http://www.adnstream.tv/canales.php?c=destacados"
		listitem = xbmcgui.ListItem( scrapedtitle, iconImage="DefaultFolder.png" , thumbnailImage=os.path.join(IMAGES_PATH, "Destacados.jpg") )
		itemurl = '%s?channel=adnstream&action=mainlist&category=%s&url=%s' % ( sys.argv[ 0 ] , urllib.quote_plus( scrapedtitle ) , urllib.quote_plus( scrapedurl ) )
		xbmcplugin.addDirectoryItem( handle = int(sys.argv[ 1 ]), url = itemurl , listitem=listitem, isFolder=True)
		"""
		scrapedtitle = "Buscar..."
		listitem = xbmcgui.ListItem( scrapedtitle, iconImage="DefaultFolder.png" , thumbnailImage=os.path.join(IMAGES_PATH, "busqueda.jpg") )
		itemurl = '%s?action=search&category=%s' % ( sys.argv[ 0 ] , urllib.quote_plus( scrapedtitle ) )
		xbmcplugin.addDirectoryItem( handle = int(sys.argv[ 1 ]), url = itemurl , listitem=listitem, isFolder=True)
		"""


	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=categoria )
		
	# Disable sorting...
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )

	# End of directory...
	xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

def search(params,url,category):
	xbmc.output("adnstream.search")

	keyboard = xbmc.Keyboard('')
	keyboard.doModal()
	if (keyboard.isConfirmed()):
		tecleado = keyboard.getText()
		if len(tecleado)>0:
			#convert to HTML
			tecleado = tecleado.replace(" ", "+")
			#tecleado = urllib.quote( tecleado )
			searchUrl = "http://www.adnstream.tv/adn/buscador.php?q="+tecleado+"&n="+str(searchresultsnum)+"&i=0&cachebuster=1243592712726"
			print searchUrl
			params['url']=searchUrl
			searchresults(params,url,category)

def searchresults(params,url,category):
	print "adnstream.actionsearchresults"

	# Lee la URL de la página con las entradas
	if params.has_key("url"):
		url = urllib.unquote_plus( params.get("url") )
	else:
		url=ADNURL
	url = url.replace(" ", "+")
	print "url="+url

	# Lee la categoría de la página
	if params.has_key("category"):
		categoria = urllib.unquote_plus( params.get("category") )
	else:
		categoria='ADNStream'

	# Descarga la página
	data = scrapertools.cachePage(url)
	#print data

	# Extrae las entradas (Vídeos)
	patronvideos  = '<item>([^<]+)<guid>([^<]+)</guid>[^<]+<title>([^<]+)</title>[^<]+<description>([^<]+)</description>[^<]+<enclosure type="([^"]+)" url="([^"]+)"/>[^<]+<media\:thumbnail type="[^"]+" url="([^"]+)"/>[^<]+<link>[^<]+</link>([^<]+<minimum_age>18</minimum_age>)?[^<]+</item>'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	if (DEBUG):
		scrapertools.printMatches(matches)

	for match in matches:
		# Video page
		scrapedad = ''
		
		# Title
		try:
			scrapedtitle = unicode( match[2], "utf-8" ).encode("iso-8859-1")
		except:
			scrapedtitle = match[2]

		try:
			scrapeddescription = unicode( match[3], "utf-8" ).encode("iso-8859-1")
		except:
			scrapeddescription = match[3]

		# Video page
		scrapedurl = match[5]
		
		# Thumb
		scrapedthumbnail = match[6]
		
		scrapedage = match[7]
		if scrapedage!='':
			scrapedage='18'
		
		# Debug info...
		if (DEBUG) :
			print "scrapedad="+scrapedad
			print "scrapedtitle="+scrapedtitle
			print "scrapeddescription="+scrapeddescription
			print "scrapedurl="+scrapedurl
			print "scrapedthumbnail="+scrapedthumbnail
			print "scrapedage="+scrapedage
		
		# Add to list...
		listitem = xbmcgui.ListItem( scrapedtitle, iconImage="DefaultVideo.png", thumbnailImage=scrapedthumbnail )
		listitem.setInfo( "video", { "Title" : scrapedtitle, "Plot" : scrapeddescription } )
		itemurl = '%s?channel=adnstream&action=play&category=%s&url=%s&ad=%s&age=%s' % ( sys.argv[ 0 ] , params["category"] , urllib.quote_plus( scrapedurl ) , urllib.quote_plus( scrapedad ) , scrapedage )
		xbmcplugin.addDirectoryItem( handle=int(sys.argv[ 1 ]), url=itemurl, listitem=listitem, totalItems=len(matches), isFolder=False)

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=categoria )
		
	# Disable sorting...
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )

	# End of directory...
	xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

def mostrarTextoPPV():
	dialog = xbmcgui.Dialog()
	# yesno = dialog.yesno('PPV', 'El vídeo que intentas ver es de pago', 'Envía 123 al 9999 e introduce el código en la siguiente ventana', 'o llama al 905xxxyyy e introduce el código en la siguiente ventana',"Cancelar","Continuar")
	yesno = 0;
	dialog.ok('Videoclub', 'Este servicio estará disponible', 'próximamente en Telebision');
	"""
	ventest = xbmcgui.WindowDialog()
	ventest.addControl(xbmcgui.ControlButton(350, 500, 80, 30, "HELLO"))
	ventest.doModal()
	ventest.show()
	"""
	del dialog
	return yesno

def leeCodigo():
	tecleado = ""
	while (len(tecleado)<=0):
		"""
		dialog = xbmcgui.Dialog()
		yesno = dialog.yesno('PPV', 'El vídeo que intentas ver es de pago', 'Envía 123 al 9999 e introduce el código en la siguiente ventana', 'o llama al 905xxxyyy e introduce el código en la siguiente ventana',"Cancelar","Continuar")
		print ("yesno: %d" % yesno)
		if(yesno==1):
		"""
		keyboard = xbmc.Keyboard('')
		keyboard.setHeading("Introduzca su código")
		keyboard.doModal()
		if (keyboard.isConfirmed()):
			tecleado = keyboard.getText()
		del keyboard
	return tecleado			

def play(params,url,category):
	print "adnstream.actionplay"
	
	url = urllib.unquote( params[ "url" ] )
	print "url = " + url

	ad = urllib.unquote( params[ "ad" ] )
	print "ad = " + ad

	age = urllib.unquote( params[ "age" ] )
	print "age = " + age

	
	if("PPV" in url):
		print "Es PPV"
		todook = False
		while todook == False:
			if(mostrarTextoPPV()==0):
				return 0
			tecleado = leeCodigo()
			url = "http://www.adnstream.tv/ppv/check.php?idvideo=SiVpKefDag&codigo=%s&modalidad=4" % tecleado
			req = urllib2.Request(url)
			resp = urllib2.urlopen(req)
			resp = resp.read()
			if(resp.startswith("&")):
				resp = resp[1:]
			resparams = dict(part.split('=') for part in resp.split('&'))
			
			try:
				if(resparams["idtemporal"]):
					print ("idtemporal"+resparams["idtemporal"])
					todook = True
					dialog = xbmcgui.Dialog()
					dialog.ok("OK", "Sí Señor, podrás ver la peli con el ID Temporal:", "%s" % resparams["idtemporal"], "Aceptar")
					playpath = ("videos/%s" % resparams["idtemporal"])
					rtmp_url = "rtmp://91.121.138.77/vod"
					pageurl = ""
					SWFPlayer = ""
					item = xbmcgui.ListItem("test")
					item.setProperty("SWFPlayer", SWFPlayer)
					item.setProperty("PlayPath", playpath)
					item.setProperty("PageURL", pageurl)
					
					xbmc.Player(xbmc.PLAYER_CORE_DVDPLAYER).play(rtmp_url, item)
					
					return True
			except:
				dialog = xbmcgui.Dialog()
				#dialog.ok("ERROR", "El código que has introducido no es correcto", "Vuelve a intentarlo", " ","Aceptar")
				dialog.yesno('ERROR', 'El código que has introducido no es correcto', '¿Volver a intentarlo?', ' ',"Cancelar","Continuar")
				print ("nanai")

	# Lee la categoría de la página
	if (params.has_key("category")):
		categoria = urllib.unquote_plus( params.get("category") )
	else:
		categoria='ADNStream'

	title = unicode( xbmc.getInfoLabel( "ListItem.Title" ), "utf-8" )
	thumbnail = xbmc.getInfoImage( "ListItem.Thumb" )
	plot = unicode( xbmc.getInfoLabel( "ListItem.Plot" ), "utf-8" )
	
	# Abre dialogo
	dialogWait = xbmcgui.DialogProgress()
	dialogWait.create( 'Accediendo al video...', title )

	# Obtiene el anuncio preroll
	preroll = getpreroll(ad)

	# Cierra dialogo
	dialogWait.close()
	del dialogWait

	if age=='18':
		advertencia = xbmcgui.Dialog()
		#resultado = advertencia.yesno('ATENCION: Contenido explícito' , 'Los contenidos que usted se dispone a ver pueden incluir textos, imágenes u otros materiales para adultos' , 'Queda prohibido acceder a estos materiales si no es usted mayor de edad y tiene la capacidad para acceder a ellos según la legislación vigente.' , '¿Desea continuar?' )
		resultado = advertencia.yesno( '', '¡Atención! Contenido explícito exclusivo para mayores de 18 años' , '¿Es usted mayor de edad?', '', 'No, soy menor de edad', 'Sí, soy mayor de edad' )
		if resultado == True:
			# Playlist vacia
			launchplayer(preroll,url,title,thumbnail,plot,categoria)
	else:
		launchplayer(preroll,url,title,thumbnail,plot,categoria)

def launchplayer2(preroll,video,title,thumbnail,plot,categoria):
	playlist = xbmc.PlayList( xbmc.PLAYLIST_VIDEO )
	playlist.clear()

	if preroll!=None:
		# Anade el anuncio al playlist
		print "Añadiendo publicidad "+preroll
		listitem = xbmcgui.ListItem( "Publicidad", iconImage="DefaultVideo.png" )
		listitem.setInfo( "video", { "Title": "Publicidad", "Studio" : "ADNStream" , "Genre" : categoria } )
		playlist.add( preroll, listitem )

	print "Añadiendo video "+video
	listitem2 = xbmcgui.ListItem( title, iconImage="DefaultVideo.png", thumbnailImage=thumbnail )
	listitem2.setInfo( "video", { "Title": title, "Plot" : plot , "Studio" : "ADNStream" , "Genre" : categoria } )
	playlist.add( video, listitem2 )
	
	# Reproduce
	xbmcPlayer = xbmc.Player( xbmc.PLAYER_CORE_AUTO )
	xbmcPlayer.play(playlist)
	

def launchplayer(preroll,video,title,thumbnail,plot,categoria):

	# Reproduce la publicidad
	if preroll!=None:
		print "Reproduciendo publicidad "+preroll
		xbmcPlayer = xbmc.Player( xbmc.PLAYER_CORE_AUTO )
		xbmcPlayer.play(preroll)   

		while xbmcPlayer.isPlaying():
			#print "is playing..."
			xbmc.sleep(2000)
	
	# Reproduce el video
	print "Reproduciendo video "+video
	newlistitem = xbmcgui.ListItem( title, iconImage="DefaultVideo.png", thumbnailImage=thumbnail )
	newlistitem.setInfo( "video", { "Title": title, "Plot" : plot , "Studio" : "ADNStream" , "Genre" : categoria } )

	xbmcPlayer = xbmc.Player( xbmc.PLAYER_CORE_AUTO )
	xbmcPlayer.play(video,newlistitem)

def getpreroll(url):
	print "adnstream.getpreroll"
	if url=='':
		return None
	#url = "http://www.adnstream.tv/ads/ad.php?CLICKTAG=YES&s=plink&v=nefLweQyoJ&t=preroll"
	print "url="+url
	data = scrapertools.cachePage(url)
	print "data="
	print data
	patronvideos  = 'publi=([^\|]+)\|\|\|'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	print "matches="
	if (DEBUG):
		scrapertools.printMatches(matches)

	location = None
	for match in matches:
		'''
		urladserver = match.replace("%26","&")
		print "urladserver="+urladserver
		req = urllib2.Request(urladserver)
		#req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
		response = urllib2.urlopen(req)
		responseinfo = response.info()
		location = responseinfo.getheader("Location")
		print "Location"
		print location
		print "responseinfo"
		print responseinfo
		data=response.read()
		print "headers"
		print response.headers
		response.close()
		#print data
		'''
		import httplib
		parsedurl = urlparse.urlparse(match)
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
			if not location.endswith(".flv"):
				print "No es un flv, se ignora"
				location=None
		
	#location='http://backup.zappinternet.com/publi/flv/promo-cine-terror.flv'

	return location
