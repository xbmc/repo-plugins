# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Configuracion
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#------------------------------------------------------------

import sys
import os

PLUGIN_ID = "plugin.video.pelisalacarta"

try:
	import xbmcaddon
	import xbmc
	DHARMA = True
	__settings__ = xbmcaddon.Addon(id=PLUGIN_ID)
	__language__ = __settings__.getLocalizedString
	DATA_PATH = xbmc.translatePath("special://profile/addon_data/%s" % PLUGIN_ID)
except ImportError:
	DHARMA = False
	DATA_PATH = os.getcwd()

def get_system_platform():
	""" fonction: pour recuperer la platform que xbmc tourne """
	platform = "unknown"
	if xbmc.getCondVisibility( "system.platform.linux" ):
		platform = "linux"
	elif xbmc.getCondVisibility( "system.platform.xbox" ):
		platform = "xbox"
	elif xbmc.getCondVisibility( "system.platform.windows" ):
		platform = "windows"
	elif xbmc.getCondVisibility( "system.platform.osx" ):
		platform = "osx"
	return platform
	
def openSettings():

	# Nuevo XBMC
	if DHARMA:
		__settings__.openSettings()
	# Antiguo XBMC
	else:
		try:
			import xbmcplugin
			xbmcplugin.openSettings( sys.argv[ 0 ] )
		except:
			pass

def getSetting(name):
	# Nuevo XBMC
	if DHARMA:
		return __settings__.getSetting( name )
	# Antiguo XBMC
	else:
		try:
			import xbmcplugin
			value = xbmcplugin.getSetting(name)
			#xbmc.output("[config.py] antiguo getSetting(%s)=%s" % (name,value))
		except:
			if name=="debug":
				value="true"
			else:
				value=""
		return value

def setSetting(name,value):
	# Nuevo XBMC
	if DHARMA:
		__settings__.setSetting( name,value ) # this will return "foo" setting value
	# Antiguo XBMC
	else:
		try:
			import xbmcplugin
			xbmcplugin.setSetting(name,value)
		except:
			pass

def getLocalizedString(code):
	# Nuevo XBMC
	if DHARMA:
		dev = __language__(code)
	# Antiguo XBMC
	else:
		try:
			import xbmc
			dev = xbmc.getLocalizedString( code )
		except:
			dev = "No soportado"
	
	try:
		dev = dev.encode ("utf-8") #This only aplies to unicode strings. The rest stay as they are.
	except:
		pass
	
	return dev
	
def getPluginId():
	if DHARMA:
		return PLUGIN_ID
	else:
		return "pelisalacarta"
	
def getLibraryPath():
	if DHARMA:
		try:
			import xbmc
			LIBRARY_PATH = xbmc.translatePath("special://profile/addon_data/%s/library" % getPluginId())
		except:
			LIBRARY_PATH = os.path.join( os.getcwd(), 'library' )
			
	else:
		#Este directorio no es el correcto. 
		#Debería ser special://profile/addon_data/<plugin_id>
		#Pero mantenemos el antiguo por razones de compatibilidad preDHARMA
		LIBRARY_PATH = os.path.join( os.getcwd(), 'library' )
		
	return LIBRARY_PATH

def getTempFile(filename):
	try:
		import xbmc
		dev = xbmc.translatePath( os.path.join( "special://temp/", filename ))
	except:
		dev = filename

	return dev
