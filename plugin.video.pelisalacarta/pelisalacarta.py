# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Main
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#------------------------------------------------------------

import urllib,urllib2
import os
import sys
import xbmc
import xbmcgui
import logger
import config

def run():
	logger.info("[pelisalacarta.py] run")
	
	# Verifica si el path de usuario del plugin está creado
	if not os.path.exists(config.DATA_PATH):
		logger.debug("[pelisalacarta.py] Path de usuario no existe, se crea: "+config.DATA_PATH)
		os.mkdir(config.DATA_PATH)

	# Imprime en el log los parámetros de entrada
	logger.info("[pelisalacarta.py] sys.argv=%s" % str(sys.argv))
	
	# Crea el diccionario de parametros
	params = dict()
	if len(sys.argv)>=2 and len(sys.argv[2])>0:
		params = dict(part.split('=') for part in sys.argv[ 2 ][ 1: ].split('&'))
	logger.info("[pelisalacarta.py] params=%s" % str(params))
	
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

	# Extrae la serie
	if (params.has_key("Serie")):
		serie = params.get("Serie")
	else:
		serie = ""
	logger.info("[pelisalacarta.py] url="+url+", action="+action+", server="+server+", category="+category+", serie="+serie)

	#JUR - Gestión de Errores de Internet (Para que no casque el plugin 
	#      si no hay internet (que queda feo)
	try:
	# Accion por defecto - elegir canal
		if ( action=="selectchannel" ):
			import channelselector as plugin
			plugin.listchannels(params, url, category)
		# Actualizar version
		elif ( action=="update" ):
			try:
				import updater
				updater.update(params)
			except ImportError:
				logger.info("[pelisalacarta.py] Actualizacion automática desactivada")
				
			import channelselector as plugin
			plugin.listchannels(params, url, category)
		# El resto de acciones vienen en el parámetro "action", y el canal en el parámetro "channel"
		elif (action=="strm"):
			import xbmctools
			xbmctools.playstrm(params, url, category)
		else:
			exec "import "+params.get("channel")+" as plugin"
			exec "plugin."+action+"(params, url, category)"
	
	except urllib2.URLError,e:
		ventana_error = xbmcgui.Dialog()
		# Agarra los errores surgidos localmente enviados por las librerias internas
		if hasattr(e, 'reason'):
			logger.info("Razon del error, codigo: %d , Razon: %s" %(e.reason[0],e.reason[1]))
			ok= ventana_error.ok ("pelisalacarta", "No se puede conectar con el servidor",'compruebe la direccion de la página',"o su conexión a internet")
		# Agarra los errores con codigo de respuesta del servidor externo solicitado 	
		elif hasattr(e,'code'):
			logger.info("codigo de error HTTP : %d" %e.code)
			ok= ventana_error.ok ("pelisalacarta", "El servidor solicitado no pudo realizar la peticion", texto_error(e.code),"codigo de error : %d " %e.code)	
		else:
			pass	


def texto_error(codigo):
	texto = {"400":"Peticion incorrecta",
			 "401":"No autorizado",
			 "402":"Pago Requerido",
			 "403":"Peticion Prohibida",
			 "404":"Pagina no encontrada o no disponible",
			 "405":"Metodo no Permitido",
			 "406":"Formato de URL no Aceptable",
			 "407":"Autentificacion de proxy requerida",
			 "408":"Tiempo de espera de peticion terminada",
			 "409":"Conflicto de peticion",
			 "410":"La URL no existe o ha sido removida"
			 }
			 
	if codigo in range(400,410):
		codtext = texto[str(codigo)]
		
	else:
		codtext = "Ocurrio un error con la URL"
	return codtext
