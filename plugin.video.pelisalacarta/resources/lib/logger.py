# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Configuracion
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#------------------------------------------------------------

import config
import xbmc

loggeractive = (config.getSetting("debug")=="true")

def info(texto):
	if loggeractive:
		xbmc.output(texto)

def debug(texto):
	if loggeractive:
		xbmc.output(texto)

def error(texto):
	xbmc.output(texto,xbmc.LOGERROR)

