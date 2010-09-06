# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# tvalacarta - XBMC Plugin
# Launcher
# http://blog.tvalacarta.info/plugin-xbmc/tvalacarta/
#------------------------------------------------------------

# Constantes
__plugin__  = "tvalacarta"
__author__  = "tvalacarta"
__url__     = "http://blog.tvalacarta.info/plugin-xbmc/tvalacarta/"
__date__    = "1 Septiembre 2010"
__version__ = "2.5"

import os
import sys
import xbmc

xbmc.output("[default.py] tvalacarta init...")

# Configura los directorios donde hay librerías
librerias = xbmc.translatePath( os.path.join( os.getcwd(), 'resources', 'lib' ) )
sys.path.append (librerias)
librerias = xbmc.translatePath( os.path.join( os.getcwd(), 'channels' ) )
sys.path.append (librerias)
librerias = xbmc.translatePath( os.path.join( os.getcwd(), 'servers' ) )
sys.path.append (librerias)
librerias = xbmc.translatePath( os.path.join( os.getcwd(), 'youtubeAPI' ) )
sys.path.append (librerias)

# Ejecuta el programa principal
import tvalacarta
tvalacarta.run()