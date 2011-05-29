# -*- coding: utf-8 -*-
#------------------------------------------------------------
# Gestión de parámetros de configuración - xbmc
#------------------------------------------------------------
# tvalacarta
# http://blog.tvalacarta.info/plugin-xbmc/tvalacarta/
#------------------------------------------------------------
# Creado por: Jesús (tvalacarta@gmail.com)
# Licencia: GPL (http://www.gnu.org/licenses/gpl-3.0.html)
#------------------------------------------------------------
# Historial de cambios:
#------------------------------------------------------------

print "[config.py] xbmc config 3.0.1"

import sys
import os

import xbmcplugin
import xbmc

PLUGIN_NAME = "pelisalacarta"

def get_system_platform():
    """ fonction: pour recuperer la platform que xbmc tourne """
    import xbmc
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
    xbmcplugin.openSettings( sys.argv[ 0 ] )

def get_setting(name):
    return xbmcplugin.getSetting(name)

def set_setting(name,value):
    xbmcplugin.setSetting(name,value)

def get_localized_string(code):
    dev = xbmc.getLocalizedString( code )

    try:
        dev = dev.encode ("utf-8") #This only aplies to unicode strings. The rest stay as they are.
    except:
        pass
    
    return dev
    
def get_library_path():
    return os.path.join( get_data_path(), 'library' )

def get_temp_file(filename):
    return xbmc.translatePath( os.path.join( "special://temp/", filename ))

def get_runtime_path():
    return os.getcwd()

def get_data_path():
    devuelve = xbmc.translatePath( os.path.join("special://home/","userdata","plugin_data","video",PLUGIN_NAME) )
    
    # XBMC en modo portable
    if devuelve.startswith("special:"):
        devuelve = xbmc.translatePath( os.path.join("special://xbmc/","userdata","plugin_data","video",PLUGIN_NAME) )

    # Plex 8
    if devuelve.startswith("special:"):
        devuelve = os.getcwd()

    return devuelve

print "[config.py] runtime path = "+get_runtime_path()
print "[config.py] data path = "+get_data_path()
print "[config.py] temp path = "+get_temp_file("test")
