# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Configuración
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#------------------------------------------------------------

from core import downloadtools
from core import config
from core import logger

logger.info("[configuracion.py] init")

def mainlist(params,url,category):
    logger.info("[configuracion.py] mainlist")
    
    # Verifica ruta de descargas
    downloadtools.getDownloadPath()
    downloadtools.getDownloadListPath()

    config.open_settings( )
