# -*- coding: utf-8 -*-

#------------------------------------------------------------
# pelisalacarta
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta
# XBMC Plugin
#------------------------------------------------------------

import urlparse,urllib2,urllib,re
import os
import sys
import xbmc
import xbmcgui
import xbmcplugin
from core import xbmctools
from core import scrapertools
import time
from core import config
from platform.xbmc import config as platform
from core import logger

PLUGIN_NAME = "pelisalacarta"
CHANNELNAME = 'updater4buscador'
if config.get_setting("thumbnail_type")=="0":
    IMAGES_PATH = xbmc.translatePath( os.path.join( config.get_runtime_path(), 'resources' , 'images' , 'posters' ) )
else:
    IMAGES_PATH = xbmc.translatePath( os.path.join( config.get_runtime_path(), 'resources' , 'images' , 'banners' ) )

ROOT_DIR = config.get_runtime_path()

REMOTE_VERSION_FILE = "http://blog.tvalacarta.info/descargas/"+PLUGIN_NAME+"-version.xml"
LOCAL_VERSION_FILE = xbmc.translatePath( os.path.join( ROOT_DIR , "version.xml" ) )
LOCAL_FILE = xbmc.translatePath( os.path.join( ROOT_DIR , PLUGIN_NAME+"-" ) )

try:
    # Añadida a la opcion : si plataforma xbmcdharma es "True", no debe ser con la plataforma de la xbox
    # porque seria un falso "True", ya que el xbmc en las xbox no son dharma por lo tanto no existen los addons   
    if config.get_platform()=="xbmcdharma" and not platform.get_system_platform() == "xbox":
        REMOTE_FILE = "http://blog.tvalacarta.info/descargas/"+PLUGIN_NAME+"-xbmc-addon-"
        DESTINATION_FOLDER = xbmc.translatePath( "special://home/addons")
    else:
        REMOTE_FILE = "http://blog.tvalacarta.info/descargas/"+PLUGIN_NAME+"-xbmc-plugin-"
        DESTINATION_FOLDER = xbmc.translatePath( "special://home/plugins/video")
except:
    REMOTE_FILE = "http://blog.tvalacarta.info/descargas/"+PLUGIN_NAME+"-xbmc-plugin-"
    DESTINATION_FOLDER = xbmc.translatePath( os.path.join( ROOT_DIR , ".." ) )

def mainlist(params,url,category):

    xbmctools.addnewfolder( CHANNELNAME , "actualizar"         , category , "Actualizar el Buscador","buscador","","")
    xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )
def actualizar(params,url,category):
    ok = updatechannel(url)
    if ok:
         xbmc.executebuiltin('XBMC.Notification("plugin '+url+'.py","A sido actualizado correctamente",3000,'+os.path.join(IMAGES_PATH, "buscador.png") + ")")

def get_channel_remote_url(channel_name):

    remote_channel_url = "http://xbmc-tvalacarta.googlecode.com/svn/trunk/"+PLUGIN_NAME+"/pelisalacarta/"+channel_name+".py"


    logger.info("remote_channel_url="+remote_channel_url)

    
    return remote_channel_url 

def get_channel_local_path(channel_name):
    import xbmc

    local_channel_path = xbmc.translatePath( os.path.join( config.get_runtime_path() ,PLUGIN_NAME, channel_name+".py" ) )

    local_compiled_path = xbmc.translatePath( os.path.join( config.get_runtime_path() ,PLUGIN_NAME, channel_name+".pyo" ) )

    logger.info("local_channel_path="+local_channel_path)

    logger.info("local_compiled_path="+local_compiled_path)
    
    return local_channel_path  , local_compiled_path

def updatechannel(channel_name):
    logger.info("[updater4buscador.py] updatechannel('"+channel_name+"')")
    
    # Canal remoto
    remote_channel_url  = get_channel_remote_url(channel_name)
    
    # Canal local
    local_channel_path , local_compiled_path = get_channel_local_path(channel_name)
    
    if not os.path.exists(local_channel_path):
        return False;


    updated = download_channel(channel_name)

    return updated

def download_channel(channel_name):
    logger.info("[updater.py] download_channel('"+channel_name+"')")
    # Canal remoto
    remote_channel_url  = get_channel_remote_url(channel_name)
    
    # Canal local
    local_channel_path  , local_compiled_path = get_channel_local_path(channel_name)

    # Descarga el canal
    updated_channel_data = scrapertools.cachePage( remote_channel_url )
    outfile = open(local_channel_path,"w")
    outfile.write(updated_channel_data)
    outfile.flush()
    outfile.close()
    logger.info("Grabado a " + local_channel_path)



    if os.path.exists(local_compiled_path):
        os.remove(local_compiled_path)
    return True