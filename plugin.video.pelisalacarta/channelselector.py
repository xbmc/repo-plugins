# -*- coding: iso-8859-1 -*-

import urlparse,urllib2,urllib,re
import os
import sys
import xbmc
import xbmcgui
import xbmcplugin
import scrapertools
import config
import logger
import parametrizacion

DEBUG = True

if config.getSetting("thumbnail_type")=="0":
	IMAGES_PATH = xbmc.translatePath( os.path.join( os.getcwd(), 'resources' , 'images' , 'posters' ) )
else:
	IMAGES_PATH = xbmc.translatePath( os.path.join( os.getcwd(), 'resources' , 'images' , 'banners' ) )

if config.getSetting("thumbnail_type")=="0":
	WEB_PATH = "http://www.mimediacenter.info/xbmc/pelisalacarta/posters/"
else:
	WEB_PATH = "http://www.mimediacenter.info/xbmc/pelisalacarta/banners/"

def listchannels(params,url,category):
	logger.info("[channelselector.py] listchannels")

	# Verifica actualizaciones solo en el primer nivel
	try:
		import updater
	except ImportError:
		logger.info("[pelisalacarta.py] No disponible modulo actualizaciones")
	else:
		if config.getSetting("updatecheck2") == "true":
			logger.info("[channelselector.py] Verificar actualizaciones activado")
			updater.checkforupdates()
		else:
			logger.info("[channelselector.py] Verificar actualizaciones desactivado")

	# Añade los canales
	addfolder("Cinetube","cinetube","mainlist")
	addfolder("Peliculasyonkis","peliculasyonkis","mainlist")
	#addfolder("Divx Online","divxonline","mainlist") # added by ermanitu
	addfolder("Cinegratis","cinegratis","mainlist")
	addfolder("tumejortv.com","tumejortv","mainlist")
	addfolder("Peliculas21","peliculas21","mainlist")
	addfolder("Dospuntocerovision","dospuntocerovision","mainlist")
	addfolder("Cine15","cine15","mainlist")
	#addfolder("Eduman Movies","edumanmovies","mainlist")
	#addfolder("SesionVIP","sesionvip","mainlist")
	addfolder("Peliculasid","peliculasid","mainlist")
	addfolder("Cinegratis24h","cinegratis24h","mainlist")
	addfolder("Cine-Adicto","cineadicto","mainlist")
	#addfolder("PelisFlv","pelisflv","mainlist")  # de momento queda apartado por falta de tiempo
	addfolder("NoloMires","nolomires","mainlist")
	addfolder("NewDivx","newdivx","mainlist")
	#addfolder("Pelis-Sevillista56","sevillista","mainlist")
	addfolder("FilmesOnlineBr [Portugues]","filmesonlinebr","mainlist")
	addfolder("TVShack.net (VO)","tvshack","mainlist")
	addfolder("DeLaTV","delatv","mainlist")
	addfolder("Pelis24","pelis24","mainlist")
	addfolder("Veocine","veocine","mainlist")
	addfolder("Pintadibujos","pintadibujos","mainlist")
	if config.getSetting("enableadultmode") == "true":
		addfolder("PeliculasEroticas","peliculaseroticas","mainlist")
		addfolder("MocosoftX","mocosoftx","mainlist")
		addfolder("Anifenix.com","anifenix","mainlist")
		addfolder("tuporno.tv","tupornotv","mainlist")
	addfolder("Descarga Cine Clásico","descargacineclasico","mainlist")
	addfolder("Capitan Cinema","capitancinema","mainlist")
	addfolder("Film Streaming [IT]","filmstreaming","mainlist")
	addfolder("No Megavideo","nomegavideo","mainlist")
	addfolder("LetMeWatchThis","letmewatchthis","mainlist")
	addfolder("Seriesyonkis","seriesyonkis","mainlist","Series") #Modificado por JUR para añadir la categoría
	addfolder("Seriespepito","seriespepito","mainlist")
	#addfolder("seriesonline.us","seriesonline","mainlist")
	addfolder("Series21","series21","mainlist")
	#addfolder("Newcineonline","newcineonline","mainlist")
	addfolder("CastTV","casttv","mainlist")
	addfolder("Ver Telenovelas Online","vertelenovelasonline","mainlist")
	addfolder("Anime Foros","animeforos","mainlist")
	addfolder("Yotix.tv","yotix","mainlist")
	addfolder("MCAnime","mcanime","mainlist")
	addfolder("Animetakus","animetakus","mainlist")
	addfolder("Ver-anime","veranime","mainlist")
	addfolder("Watchanimeon [EN]","watchanimeon","mainlist")
	addfolder("Animeid","animeid","mainlist")
	addfolder("Ovasid","ovasid","mainlist")
	addfolder("dibujosanimadosgratis.net","dibujosanimadosgratis","mainlist")
	addfolder("DocumaniaTV","documaniatv","mainlist")
	addfolder("DocumentariesTV [EN]","documentariestv","mainlist")
	addfolder("Documentalesyonkis","documentalesyonkis","mainlist")
	addfolder("Documentalesatonline","documentalesatonline","mainlist")
	addfolder("Discoverymx.Wordpress","discoverymx","mainlist")
	addfolder("Gratisdocumentales","gratisdocumentales","mainlist")
	addfolder("Redes.tv","redestv","mainlist")
	addfolder("Buscador de Trailers (Youtube)","trailertools","mainlist")
	addfolder("ecartelera (Trailers)","ecarteleratrailers","mainlist")
	addfolder("Stagevu","stagevusite","mainlist")
	addfolder("tu.tv","tutvsite","mainlist")
	addfolder("Megavideo","megavideosite","mainlist")
	addfolder("Megaupload","megauploadsite","mainlist")
	
	addfolder(config.getLocalizedString(30100),"configuracion","mainlist") # Configuracion
	
	if (parametrizacion.DOWNLOAD_ENABLED):
		addfolder(config.getLocalizedString(30101),"descargados","mainlist")   # Descargas
	addfolder(config.getLocalizedString(30102),"favoritos","mainlist")     # Favoritos
	addfolder(config.getLocalizedString(30103),"buscador","mainlist")      # Buscador
	addfolder(config.getLocalizedString(30104),"ayuda","mainlist")         # Ayuda

	#addfolder("Kochikame","kochikame","mainlist")
	#addfolder("PeliculasHD","peliculashd","mainlist")
	#addfolder("Wuapi","wuapisite","mainlist")
	#addfolder("Frozen Layer","frozenlayer","mainlist")

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category="Canales" )
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

def addfolder(nombre,channelname,accion,category="Varios"):

	#Si no se indica categoría poner "Otros" por defecto
	if category == "":
		category = "Otros"
	
	# Preferencia: primero JPG
	thumbnail = thumbnailImage=os.path.join(IMAGES_PATH, channelname+".jpg")
	# Preferencia: segundo PNG
	if not os.path.exists(thumbnail):
		thumbnail = thumbnailImage=os.path.join(IMAGES_PATH, channelname+".png")
	# Preferencia: tercero WEB
	if not os.path.exists(thumbnail):
		thumbnail = thumbnailImage=WEB_PATH+channelname+".png"

	#logger.info("thumbnail="+thumbnail)

	listitem = xbmcgui.ListItem( nombre , iconImage="DefaultFolder.png", thumbnailImage=thumbnail)
	itemurl = '%s?channel=%s&action=%s&category=%s' % ( sys.argv[ 0 ] , channelname , accion , urllib.quote_plus(category) )
	xbmcplugin.addDirectoryItem( handle = int(sys.argv[ 1 ]), url = itemurl , listitem=listitem, isFolder=True)
