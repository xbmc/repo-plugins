# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Lista de vídeos favoritos
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#------------------------------------------------------------
import urllib
import os
import sys
try:
    import xbmc
    import xbmcgui
    import xbmcplugin
except:
    pass
import downloadtools
import config
import logger
import samba

CHANNELNAME = "favoritos"
DEBUG = True
bookmark_setting = config.getSetting( "bookmarkpath")

BOOKMARK_PATH = (len(bookmark_setting)>0 and bookmark_setting) or os.path.join(config.DATA_PATH,"bookmarks")  

usingsamba=BOOKMARK_PATH.upper().startswith("SMB://")

if not usingsamba:    
    if not os.path.exists(BOOKMARK_PATH):
        logger.debug("[favoritos.py] Path de bookmarks no existe, se crea: "+BOOKMARK_PATH)
        os.mkdir(BOOKMARK_PATH)

def mainlist(params,url,category):
    logger.info("[favoritos.py] mainlist")

    import xbmctools

    # Crea un listado con las entradas de favoritos
    if usingsamba:
        ficheros = samba.get_files(BOOKMARK_PATH)
    else:
        ficheros = os.listdir(BOOKMARK_PATH)
    ficheros.sort()
    for fichero in ficheros:

        try:
            # Lee el bookmark
            titulo,thumbnail,plot,server,url = readbookmark(fichero)

            # Crea la entrada
            # En la categoría va el nombre del fichero para poder borrarlo
            xbmctools.addnewvideo( CHANNELNAME , "play" , os.path.join( BOOKMARK_PATH, fichero ) , server , titulo , url , thumbnail, plot )
        except:
            pass

    # Label (top-right)...
    xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
    xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

def play(params,url,category):
    logger.info("[favoritos.py] play")

    title = unicode( xbmc.getInfoLabel( "ListItem.Title" ), "utf-8" )
    thumbnail = xbmc.getInfoImage( "ListItem.Thumb" )
    plot = unicode( xbmc.getInfoLabel( "ListItem.Plot" ), "utf-8" )
    server = params["server"]
    
    import xbmctools
    xbmctools.playvideo2(CHANNELNAME,server,url,category,title,thumbnail,plot)

def readbookmark(filename):
    logger.info("[favoritos.py] readbookmark")

    if usingsamba:
        bookmarkfile = samba.get_file_handle_for_reading(filename, BOOKMARK_PATH)
    else:
        filepath = os.path.join( BOOKMARK_PATH , filename )

        # Lee el fichero de configuracion
        logger.info("[favoritos.py] filepath="+filepath)
        bookmarkfile = open(filepath)
    lines = bookmarkfile.readlines()

    try:
        titulo = urllib.unquote_plus(lines[0].strip())
    except:
        titulo = lines[0].strip()
    
    try:
        url = urllib.unquote_plus(lines[1].strip())
    except:
        url = lines[1].strip()
    
    try:
        thumbnail = urllib.unquote_plus(lines[2].strip())
    except:
        thumbnail = lines[2].strip()
    
    try:
        server = urllib.unquote_plus(lines[3].strip())
    except:
        server = lines[3].strip()
        
    try:
        plot = urllib.unquote_plus(lines[4].strip())
    except:
        plot = lines[4].strip()

    bookmarkfile.close();

    return titulo,thumbnail,plot,server,url

def savebookmark(titulo,url,thumbnail,server,plot):
    logger.info("[favoritos.py] savebookmark")

    # No va bien más que en Windows
    #bookmarkfiledescriptor,bookmarkfilepath = tempfile.mkstemp(suffix=".txt",prefix="",dir=BOOKMARK_PATH)

    # Crea el directorio de favoritos si no existe
    if not usingsamba:
        try:
            os.mkdir(BOOKMARK_PATH)
        except:
            pass

    # Lee todos los ficheros
    if usingsamba:
        ficheros = samba.get_files(BOOKMARK_PATH)
    else:
        ficheros = os.listdir(BOOKMARK_PATH)
    ficheros.sort()
    #print ficheros
    #Filtra solo los ficheros
    ficheros2 = [f for f in ficheros
                if os.path.isfile(os.path.join(BOOKMARK_PATH, f)) and os.path.join(BOOKMARK_PATH, f).endswith(".txt")]

    # Averigua el último número
    if len(ficheros)>0:
        filenumber = int( ficheros[len(ficheros)-1][0:-4] )+1
    else:
        filenumber=1

    # Genera el contenido
    filecontent = ""
    filecontent = filecontent + urllib.quote_plus(downloadtools.limpia_nombre_excepto_1(titulo))+'\n'
    filecontent = filecontent + urllib.quote_plus(url)+'\n'
    filecontent = filecontent + urllib.quote_plus(thumbnail)+'\n'
    filecontent = filecontent + urllib.quote_plus(server)+'\n'
    filecontent = filecontent + urllib.quote_plus(downloadtools.limpia_nombre_excepto_1(plot))+'\n'

    # Genera el nombre de fichero    
    filename = '%08d.txt' % filenumber
    logger.info("[favoritos.py] savebookmark filename="+filename)

    # Graba el fichero
    if not usingsamba:
        fullfilename = os.path.join(BOOKMARK_PATH,filename)
        bookmarkfile = open(fullfilename,"w")
        bookmarkfile.write(filecontent)
        bookmarkfile.flush();
        bookmarkfile.close()
    else:
        samba.write_file(filename, filecontent, BOOKMARK_PATH)

def deletebookmark(fullfilename):
    
    if not usingsamba:
        os.remove(urllib.unquote_plus( fullfilename ))
    else:
        fullfilename = fullfilename.replace("\\","/")
        partes = fullfilename.split("/")
        filename = partes[len(partes)-1]
        samba.remove_file(filename,BOOKMARK_PATH)
