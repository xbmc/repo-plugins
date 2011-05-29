# -*- coding: utf-8 -*-
#------------------------------------------------------------
# Gestión de parámetros de configuración multiplataforma
#------------------------------------------------------------
# pelisalacarta
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#------------------------------------------------------------
# Creado por: Jesús (tvalacarta@gmail.com)
# Licencia: GPL (http://www.gnu.org/licenses/gpl-3.0.html)
#------------------------------------------------------------
# Historial de cambios:
#------------------------------------------------------------

PLATFORM = ""

# Intenta averiguar la plataforma de entre una de las siguientes:

# boxee
# xbmc
# xbmcdharma
# developer

# plex
# mediaportal
# windowsmediacenter

try:
    from enigma import iPlayableService
    PLATFORM="dreambox"
except:
    try:
        import mc
        PLATFORM="boxee"
    except:
        try:
            import xbmcaddon
            PLATFORM = "xbmcdharma"
        except ImportError:
            # XBMC
            try:
                import xbmc
                PLATFORM = "xbmc"
            except ImportError:
                print "Platform=DEVELOPER"
                # Eclipse
                PLATFORM = "developer"

def force_platform(platform):
    global PLATFORM
    
    PLATFORM = platform
    # En PLATFORM debería estar el módulo a importar
    try:
        exec "import platform."+PLATFORM+".config as platformconfig"
    except:
        exec "import "+PLATFORM+"config as platformconfig"
        

def get_platform():
    return PLATFORM

def get_system_platform():
    try:
        exec "import platform."+PLATFORM+".config as platformconfig"
    except:
        exec "import "+PLATFORM+"config as platformconfig"
    return platformconfig.get_system_platform()

def open_settings():
    try:
        exec "import platform."+PLATFORM+".config as platformconfig"
    except:
        exec "import "+PLATFORM+"config as platformconfig"
    return platformconfig.open_settings()

def get_setting(name,channel=""):
    try:
        exec "import platform."+PLATFORM+".config as platformconfig"
    except:
        exec "import "+PLATFORM+"config as platformconfig"
    # La cache recibe un valor por defecto la primera vez que se solicita

    dev=platformconfig.get_setting(name)

    if name=="download.enabled":
        try:
            from core import descargados
            dev="true"
        except:
            import sys
            for line in sys.exc_info():
                print line
            dev="false"
    
    elif name=="cookies.dir":
        dev=get_data_path()
    
    # TODO: (3.1) De momento la cache está desactivada...
    elif name=="cache.mode" and PLATFORM!="developer":
        dev="2"
    
    if channel!="":
        import os,re
        nombre_fichero_config_canal = os.path.join( get_data_path() , channel+".xml" )
        if os.path.exists( nombre_fichero_config_canal ):
            config_canal = open( nombre_fichero_config_canal )
            data = config_canal.read()
            config_canal.close();
        
            patron = "<"+name+">([^<]+)</"+name+">"
            matches = re.compile(patron,re.DOTALL).findall(data)
            if len(matches)>0:
                dev = matches[0]
            else:
                dev = ""
        else:
            dev = ""
    
    return dev

def set_setting(name,value):
    try:
        exec "import platform."+PLATFORM+".config as platformconfig"
    except:
        exec "import "+PLATFORM+"config as platformconfig"
    platformconfig.set_setting(name,value)

def get_localized_string(code):
    try:
        exec "import platform."+PLATFORM+".config as platformconfig"
    except:
        exec "import "+PLATFORM+"config as platformconfig"
    return platformconfig.get_localized_string(code)

def get_library_path():
    try:
        exec "import platform."+PLATFORM+".config as platformconfig"
    except:
        exec "import "+PLATFORM+"config as platformconfig"
    return platformconfig.get_library_path()

def get_temp_file(filename):
    try:
        exec "import platform."+PLATFORM+".config as platformconfig"
    except:
        exec "import "+PLATFORM+"config as platformconfig"
    return platformconfig.get_temp_file()

def get_runtime_path():
    try:
        exec "import platform."+PLATFORM+".config as platformconfig"
    except:
        exec "import "+PLATFORM+"config as platformconfig"
    return platformconfig.get_runtime_path()

def get_data_path():
    try:
        exec "import platform."+PLATFORM+".config as platformconfig"
    except:
        exec "import "+PLATFORM+"config as platformconfig"
    return platformconfig.get_data_path()
