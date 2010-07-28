# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Configuracion
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#------------------------------------------------------------

import xbmc
import xbmcplugin
import sys
import os

try:
	import xbmcaddon
	DHARMA = True
except ImportError:
	DHARMA = False

PLUGIN_ID = "plugin.video.pelisalacarta"
if DHARMA:
	__settings__ = xbmcaddon.Addon(id=PLUGIN_ID)
	DATA_PATH = xbmc.translatePath("special://profile/addon_data/%s" % PLUGIN_ID)
else:
	DATA_PATH = os.getcwd()
	
def openSettings():
	
	# Nuevo XBMC
	if DHARMA:
		__settings__.openSettings()
	# Antiguo XBMC
	else:
		xbmcplugin.openSettings( sys.argv[ 0 ] )

def getSetting(name):
	# Nuevo XBMC
	if DHARMA:
		return __settings__.getSetting( name )
	# Antiguo XBMC
	else:
		value = xbmcplugin.getSetting(name)
		#xbmc.output("[config.py] antiguo getSetting(%s)=%s" % (name,value))
		return value

def setSetting(name,value):
	# Nuevo XBMC
	if DHARMA:
		__settings__.setSetting( name,value ) # this will return "foo" setting value
	# Antiguo XBMC
	else:
		xbmcplugin.setSetting(name,value)

def getLocalizedString(code):
	# Nuevo XBMC
	if DHARMA:
		__language__ = __settings__.getLocalizedString
		return __language__(code)
	# Antiguo XBMC
	else:
		return xbmc.getLocalizedString( code )
		
	
def getPluginId():
	if DHARMA:
		return PLUGIN_ID
	else:
		return "pelisalacarta"
	
def getLibraryPath():
	if DHARMA:
		LIBRARY_PATH = xbmc.translatePath("special://profile/addon_data/%s/library" % getPluginId())
	else:
		#Este directorio no es el correcto. 
		#Debería ser special://profile/addon_data/<plugin_id>
		#Pero mantenemos el antiguo por razones de compatibilidad preDHARMA
		LIBRARY_PATH = os.path.join( os.getcwd(), 'library' )
		
	return LIBRARY_PATH
