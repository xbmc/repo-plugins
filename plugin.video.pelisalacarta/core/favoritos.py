# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Lista de vídeos favoritos
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#------------------------------------------------------------
import urllib
import os
import sys
import downloadtools
import config
import logger
import samba

CHANNELNAME = "favoritos"
DEBUG = True
BOOKMARK_PATH = config.get_setting( "bookmarkpath" )

if not BOOKMARK_PATH.upper().startswith("SMB://"):
    if BOOKMARK_PATH=="":
        BOOKMARK_PATH = os.path.join( config.get_data_path() , "bookmarks" )
    if not os.path.exists(BOOKMARK_PATH):
        logger.debug("[favoritos.py] Path de bookmarks no existe, se crea: "+BOOKMARK_PATH)
        os.mkdir(BOOKMARK_PATH)

logger.info("[favoritos.py] path="+BOOKMARK_PATH)

def mainlist(params,url,category):
    logger.info("[favoritos.py] mainlist")

    import xbmctools

    # Crea un listado con las entradas de favoritos
    if usingsamba(BOOKMARK_PATH):
        ficheros = samba.get_files(BOOKMARK_PATH)
    else:
        ficheros = os.listdir(BOOKMARK_PATH)
    
    # Ordena el listado por nombre de fichero (orden de incorporación)
    ficheros.sort()
    
    # Rellena el listado
    for fichero in ficheros:

        try:
            # Lee el bookmark
            titulo,thumbnail,plot,server,url = readbookmark(fichero)

            # Crea la entrada
            # En la categoría va el nombre del fichero para poder borrarlo
            xbmctools.addnewvideo( CHANNELNAME , "play" , os.path.join( BOOKMARK_PATH, fichero ) , server , titulo , url , thumbnail, plot , fanart=thumbnail )
        except:
            pass

    # Label (top-right)...
    import xbmcplugin
    xbmcplugin.setContent(int( sys.argv[ 1 ] ),"movies")
    xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
    xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

def play(params,url,category):
    logger.info("[favoritos.py] play")

    import xbmc
    title = unicode( xbmc.getInfoLabel( "ListItem.Title" ), "utf-8" )
    thumbnail = xbmc.getInfoImage( "ListItem.Thumb" )
    plot = unicode( xbmc.getInfoLabel( "ListItem.Plot" ), "utf-8" )
    server = params["server"]
    
    import xbmctools
    xbmctools.playvideo2(CHANNELNAME,server,url,category,title,thumbnail,plot)

def readbookmark(filename,readpath=BOOKMARK_PATH):
    logger.info("[favoritos.py] readbookmark")

    if usingsamba(readpath):
        bookmarkfile = samba.get_file_handle_for_reading(filename, readpath)
    else:
        filepath = os.path.join( readpath , filename )

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

def savebookmark(titulo,url,thumbnail,server,plot,savepath=BOOKMARK_PATH):
    logger.info("[favoritos.py] savebookmark(path="+savepath+")")

    # Crea el directorio de favoritos si no existe
    if not usingsamba(savepath):
        try:
            os.mkdir(savepath)
        except:
            pass

    # Lee todos los ficheros
    if usingsamba(savepath):
        ficheros = samba.get_files(savepath)
    else:
        ficheros = os.listdir(savepath)
    ficheros.sort()
    
    # Averigua el último número
    if len(ficheros)>0:
        # XRJ: Linea problemática, sustituida por el bucle siguiente
        #filenumber = int( ficheros[len(ficheros)-1][0:-4] )+1
        filenumber = 1
        for fichero in ficheros:
            logger.info("fichero="+fichero)
            try:
                tmpfilenumber = int( fichero[0:-4] )+1
                if tmpfilenumber > filenumber:
                    filenumber = tmpfilenumber
            except:
                pass
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
    if not usingsamba(savepath):
        fullfilename = os.path.join(savepath,filename)
        bookmarkfile = open(fullfilename,"w")
        bookmarkfile.write(filecontent)
        bookmarkfile.flush();
        bookmarkfile.close()
    else:
        samba.write_file(filename, filecontent, savepath)

def deletebookmark(fullfilename,deletepath=BOOKMARK_PATH):
    
    if not usingsamba(deletepath):
        os.remove(urllib.unquote_plus( fullfilename ))
    else:
        fullfilename = fullfilename.replace("\\","/")
        partes = fullfilename.split("/")
        filename = partes[len(partes)-1]
        samba.remove_file(filename,deletepath)

def usingsamba(path):
    return path.upper().startswith("SMB://")
