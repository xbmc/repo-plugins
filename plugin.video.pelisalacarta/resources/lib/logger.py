# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Configuracion
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#------------------------------------------------------------

import config
import xbmc

REMOTE_DBG = False

loggeractive = (config.getSetting("debug")=="true")

def info(texto):
	if loggeractive:
		if REMOTE_DBG:
			print(texto)
		else:
			xbmc.output(texto)

def debug(texto):
	if loggeractive:
		if REMOTE_DBG:
			print(texto)
		else:
			xbmc.output(texto)

def error(texto):
	if REMOTE_DBG:
		print(texto,xbmc.LOGERROR)
	else:
		xbmc.output(texto,xbmc.LOGERROR)
