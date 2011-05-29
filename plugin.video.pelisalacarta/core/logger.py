# -*- coding: utf-8 -*-
#------------------------------------------------------------
# Logger multiplataforma
#------------------------------------------------------------
# pelisalacarta
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#------------------------------------------------------------
# Creado por: Jesús (tvalacarta@gmail.com)
# Licencia: GPL (http://www.gnu.org/licenses/gpl-3.0.html)
#------------------------------------------------------------
# Historial de cambios:
#------------------------------------------------------------

try:
    from core import config
except:
    import config

try:
    exec "import platform."+config.get_platform()+".logger as platformlogger"
except:
    exec "import dreamboxlogger as platformlogger"

loggeractive = (config.get_setting("debug")=="true")

def log_enable(active):
    global loggeractive
    loggeractive = active

def info(texto):
    if loggeractive: platformlogger.info(texto)

def debug(texto):
    if loggeractive: platformlogger.info(texto)

def error(texto):
    if loggeractive: platformlogger.info(texto)
