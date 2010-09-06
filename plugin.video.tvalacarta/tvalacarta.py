# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# tvalacarta - XBMC Plugin
# Main
# http://blog.tvalacarta.info/plugin-xbmc/tvalacarta/
#------------------------------------------------------------

import urllib
import os
import sys
import xbmc
import xbmcgui
import logger
import config
import urllib2

def run():
	logger.info("[tvalacarta.py] run")
	
	# Verifica si el path de usuario del plugin está creado
	if not os.path.exists(config.DATA_PATH):
		logger.debug("[tvalacarta.py] Path de usuario no existe, se crea: "+config.DATA_PATH)
		os.mkdir(config.DATA_PATH)

	# Imprime en el log los parámetros de entrada
	logger.info("[tvalacarta.py] sys.argv=%s" % str(sys.argv))
	
	# Crea el diccionario de parametros
	params = dict()
	if len(sys.argv)>=2 and len(sys.argv[2])>0:
		params = dict(part.split('=') for part in sys.argv[ 2 ][ 1: ].split('&'))
	logger.info("[tvalacarta.py] params=%s" % str(params))
	
	# Extrae la url de la página
	if (params.has_key("url")):
		url = urllib.unquote_plus( params.get("url") )
	else:
		url=''

	# Extrae la accion
	if (params.has_key("action")):
		action = params.get("action")
	else:
		action = "selectchannel"

	# Extrae el server
	if (params.has_key("server")):
		server = params.get("server")
	else:
		server = ""

	# Extrae la categoria
	if (params.has_key("category")):
		category = urllib.unquote_plus( params.get("category") )
	else:
		if params.has_key("channel"):
			category = params.get("channel")
		else:
			category = ""


	try:
		# Accion por defecto - elegir canal
		if ( action=="selectchannel" ):
			import channelselector as plugin
			plugin.listchannels(params, url, category)
		# Actualizar version
		elif ( action=="update" ):
			import updater
			updater.update(params)
			import channelselector as plugin
			plugin.listchannels(params, url, category)
		# El resto de acciones vienen en el parámetro "action", y el canal en el parámetro "channel"
		else:
			exec "import "+params.get("channel")+" as channel"
			generico = False
			try:
				generico = channel.isGeneric()
			except:
				generico = False

			print "generico=" , generico 
			
			if not generico:
				exec "channel."+action+"(params, url, category)"
			else:
				if params.has_key("title"):
					title = urllib.unquote_plus( params.get("title") )
				else:
					title = ""
				if params.has_key("thumbnail"):
					thumbnail = urllib.unquote_plus( params.get("thumbnail") )
				else:
					thumbnail = ""
				if params.has_key("plot"):
					plot = urllib.unquote_plus( params.get("plot") )
				else:
					plot = ""
				if params.has_key("server"):
					server = urllib.unquote_plus( params.get("server") )
				else:
					server = "directo"
			
				import xbmctools
				if action=="play":
					xbmctools.playvideo(params.get("channel"),server,url,category,title,thumbnail,plot)
				else:
					from item import Item
					item = Item(channel=params.get("channel"), title=title , url=url, thumbnail=thumbnail , plot=plot , server=server)
		
					exec "itemlist = channel."+action+"(item)"
					xbmctools.renderItems(itemlist, params, url, category)

	except urllib2.URLError,e:
		ventana_error = xbmcgui.Dialog()
		# Agarra los errores surgidos localmente enviados por las librerias internas
		if hasattr(e, 'reason'):
			logger.info("Razon del error, codigo: %d , Razon: %s" %(e.reason[0],e.reason[1]))
			texto = config.getLocalizedString(30050) # "No se puede conectar con el sitio web"
			ok = ventana_error.ok ("pelisalacarta", texto)
		# Agarra los errores con codigo de respuesta del servidor externo solicitado 	
		elif hasattr(e,'code'):
			logger.info("codigo de error HTTP : %d" %e.code)
			texto = (config.getLocalizedString(30051) % e.code) # "El sitio web no funciona correctamente (error http %d)"
			ok = ventana_error.ok ("pelisalacarta", texto)	
		else:
			pass
