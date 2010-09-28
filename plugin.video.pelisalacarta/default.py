# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Launcher
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#------------------------------------------------------------

# Constantes
__plugin__  = "pelisalacarta"
__author__  = "tvalacarta"
__url__     = "http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/"
__date__    = "27 Septiembre 2010"
__version__ = "2.18"

import os
import sys
import xbmc

xbmc.output("[default.py] pelisalacarta init...")

# Configura los directorios donde hay librerías
librerias = xbmc.translatePath( os.path.join( os.getcwd(), 'resources', 'lib' ) )
sys.path.append (librerias)
librerias = xbmc.translatePath( os.path.join( os.getcwd(), 'channels' ) )
sys.path.append (librerias)
librerias = xbmc.translatePath( os.path.join( os.getcwd(), 'servers' ) )
sys.path.append (librerias)
librerias = xbmc.translatePath( os.path.join( os.getcwd(), 'youtubeAPI' ) )
sys.path.append (librerias)

import logger
from logger import REMOTE_DBG

# append pydev remote debugger
if REMOTE_DBG:
    # Make pydev debugger works for auto reload.
    # Note pydevd module need to be copied in XBMC\system\python\Lib\pysrc
    try:
        import pysrc.pydevd as pydevd
    # stdoutToServer and stderrToServer redirect stdout and stderr to eclipse console
    # El server está en el PC donde tengas ejecutando eclipse
        pydevd.settrace('localhost', stdoutToServer=True, stderrToServer=True)
        logger.debug ("[default.py] REMOTE_DGB ON -  conectando con el server en 192.168.1.30")
    except ImportError:
        xbmc.output("[default.py] REMOTE_DBG Error: " +
            "You must add org.python.pydev.debug.pysrc to your PYTHONPATH.")
        REMOTE_DBG = False 

# Ejecuta el programa principal
import pelisalacarta
pelisalacarta.run()


