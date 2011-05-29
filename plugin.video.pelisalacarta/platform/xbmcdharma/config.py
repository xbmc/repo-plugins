# -*- coding: utf-8 -*-
#------------------------------------------------------------
# Gestión de parámetros de configuración - xbmc dharma
#------------------------------------------------------------
# tvalacarta
# http://blog.tvalacarta.info/plugin-xbmc/tvalacarta/
#------------------------------------------------------------
# Creado por: 
# Jesús (tvalacarta@gmail.com)
# Jurrabi (jurrabi@gmail.com)
# Licencia: GPL (http://www.gnu.org/licenses/gpl-3.0.html)
#------------------------------------------------------------
# Historial de cambios:
#------------------------------------------------------------

print "[config.py] xbmcdharma config 3.0.1"

import sys
import os

import xbmcaddon
import xbmc

PLUGIN_NAME = "pelisalacarta"
__settings__ = xbmcaddon.Addon(id="plugin.video."+PLUGIN_NAME)
__language__ = __settings__.getLocalizedString

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
	
def open_settings():
	__settings__.openSettings()

def get_setting(name):
	dev = __settings__.getSetting( name )
	
	return dev

def set_setting(name,value):
	__settings__.setSetting( name,value )

def get_localized_string(code):
	dev = __language__(code)

	try:
		dev = dev.encode("utf-8")
	except:
		pass
	
	return dev

def get_library_path():
	if get_system_platform() == "xbox":
		return xbmc.translatePath(os.path.join(get_runtime_path(),"library"))
	else:
		return xbmc.translatePath("special://profile/addon_data/plugin.video."+PLUGIN_NAME+"/library")

def get_temp_file(filename):
	return xbmc.translatePath( os.path.join( "special://temp/", filename ))

def get_runtime_path():
	return xbmc.translatePath( __settings__.getAddonInfo('Path') )

def get_data_path():
	dev = xbmc.translatePath( __settings__.getAddonInfo('Profile') )
	
	# Parche para XBMC4XBOX
	if not os.path.exists(dev):
		os.makedirs(dev)
	
	return dev

print "[config.py] runtime path = "+get_runtime_path()
print "[config.py] data path = "+get_data_path()
print "[config.py] temp path = "+get_temp_file("test")
