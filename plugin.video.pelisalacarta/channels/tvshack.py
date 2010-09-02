# -*- coding: iso-8859-1 -*-
#----------------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# tvshack.cc - Movies, TV Series, Anime, Documentaries and Music in VO
# tvshack.cc - Pel�culas, series, Anime, Documentales y M�sica en VO
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
# Channel by jurrabi
#----------------------------------------------------------------------
import urllib
import re
import sys
import xbmc
import xbmcplugin
import xbmcgui
import scrapertools
import xbmctools
import os
import library
import string
import config
import logger

#TODO: Paso a Multilenguaje
from config import getLocalizedString as getStr
from compiler.syntax import check


CHANNELNAME = "tvshack"

MEGAVIDEO_POSTER = xbmc.translatePath( os.path.join( os.getcwd(), 'resources' , 'images' , 'posters' , "megavideosite.png") )

ALLOWED_SERVERS = ['megavideo','veoh','tudou','movshare','stagevu','smotri']
#No soportados comprobados por el momento 56.com,zshare

SEARCH_THUMBNAIL = xbmc.translatePath( os.path.join( os.getcwd(), 'resources' , 'images' , 'posters','buscador.png' ) )


FANART_PATH = xbmc.translatePath( os.path.join( os.getcwd(), 'resources' , 'images' , 'fanart' ) )

pluginhandle = int( sys.argv[ 1 ] )

# Trace the channel initialization
logger.debug("[tvshack.py] init")


fanartfile = xbmc.translatePath( os.path.join( FANART_PATH, 'tvshack.jpg' ) )
xbmcplugin.setPluginFanart(pluginhandle, fanartfile)

DEBUG = logger.loggeractive

##############################################################################
def mainlist(params,url,category):
    """Lists the main categories of the channel

    """
    logger.debug("[tvshac.py] mainlist")


    # Categories List
    test = config.getLocalizedString(30900)
    xbmctools.addnewfolder( CHANNELNAME , "ListaSeries" , "Series" , str(getStr(30901)) , "http://tvshack.cc/tv" , thumbnail="" , plot="" ) #    <string id="30901">Series TV (VO)</string>
    xbmctools.addnewfolder( CHANNELNAME , "ListaDetallada" , "Cine" , config.getLocalizedString(30902) , "http://tvshack.cc/movies" , thumbnail="" , plot="" )
    xbmctools.addnewfolder( CHANNELNAME , "ListaDetallada" , "Documentales" , getStr(30903) , "http://tvshack.cc/documentaries" , thumbnail="" , plot="" )
    xbmctools.addnewfolder( CHANNELNAME , "ListaSeries" , "Anime" , getStr(30904) , "http://tvshack.cc/anime" , thumbnail="" , plot="" )
    xbmctools.addnewfolder( CHANNELNAME , "ListaSeries" , "Musica" , getStr(30905) , "http://tvshack.cc/music" , thumbnail="" , plot="" )
    xbmctools.addnewfolder( CHANNELNAME , "Buscar" , "" , getStr(30906) , "http://tvshack.cc/search/" , thumbnail=SEARCH_THUMBNAIL , plot="" )

    FinalizaPlugin (pluginhandle,category)

def Buscar (params,url,category):
    '''Searches globally through tvshack and shows results list
    '''
    logger.info("[tvshack.py] Buscar")
    
    keyboard = xbmc.Keyboard()
    keyboard.doModal()
    if not (keyboard.isConfirmed()):
        return
    text = keyboard.getText()
    if len(text) < 3:
        return
  
    #Clean search text to avoid web errors
    text = string.capwords(text).replace(" ", "+")
    searchUrl = url+text
  
    # Get the search results
    data = ""
    try:
        furl = urllib.urlopen(searchUrl)
        newurl = furl.geturl()
        if newurl != searchUrl:
            # This means we got only one result and jumped directly to it.
            # We have to analyze the result page to figure out the category
            dlog ('[tvshack] buscar: single result: '+ newurl)
            if newurl.find('/tv/') == 18: #TV Serie
                data = '<li><a href="%s">Television - <strong>%s</strong></a><a href="%s"><span>0 episodes</span></a></li>' % (newurl,newurl[22:-1],newurl)
            elif newurl.find("/movies/") == 18: #Film
                data = '<li><a href="%s">Movies - <strong>%s</strong></a><a href="%s"><span>%s</span></a></li>' % (newurl,newurl[26:-8],newurl,newurl[-6:-2])
            elif newurl.find("/music/") == 18: #Singer
                data = '<li><a href="%s">Music - <strong>%s</strong></a><a href="%s"></a></li>' % (newurl,newurl[25:-1],newurl)
        else:
            # Multiple search results
            data = furl.read()
        furl.close()
    except:
        # Probably Internet connection problems or web changes. Nothing we can do :(
        pass
    if len(data) == 0:
        logger.error ("[tvshac.py] Buscar - No search results :"+text)
        error = xbmcgui.Dialog()
        error.ok('pelisalacarta - TVShack',getStr(30907) ) #"The search did not find anything"
        return

# Ej. TV Series: <li><a href="http://tvshack.cc/tv/The_Big_Bang_Theory/">Television - <strong>The Big Bang Theory</strong></a><a href="http://tvshack.cc/tv/The_Big_Bang_Theory/"><span>57 episodes</span></a></li>
# Ej. Movie:     <li><a href="http://tvshack.cc/movies/Bang_Bang_You_re_Dead__2002_/">Movies - <strong>Bang Bang You're Dead</strong></a><a href="http://tvshack.cc/movies/Bang_Bang_You_re_Dead__2002_/"><span>2002</span></a></li>
# Ej. Music:     <li><a href="http://tvshack.cc/music/Mr__Big/">Music - <strong>Mr. Big</strong></a><a href="http://tvshack.cc/music/Mr__Big/"></a></li>
    patronvideos = '''(?x)       #      VERBOSE option active
        <li><a\ href="           #      Trash
        (?P<url>[^"]+)">         # $0 = media url
        ([^\ ]+)\ -\             # $1 = media Category: TV, Movie or Music
        <strong>                 #      Trash
        ([^<]+)                  # $2 = Media Name
        </strong></a>            #      Trash
        (?:<a\ href=")           #      Trash
        (?P=url)">               # $0 = media url (again)
        (?:<span>)?              #      Trash
        ([0-9]+)?                # $3 = Number of episodes or Production Year
        (?:\ episodes)?          #      Trash
        (?:</span>)?</a></li>    #      Trash
        ''' 
    matches = re.findall(patronvideos,data)
            
    totalmatches = len(matches)
    if totalmatches == 0:
        logger.error ("[tvshac.py] Buscar - No matches found: "+text)
        error = xbmcgui.Dialog()
        error.ok('pelisalacarta - TVShack',getStr(30907)) #'No matches found'
        return

    for match in matches:
        if match[1]== 'Television':
            # Add to the directory listing
            if match[3] != '0':
                scrapedtitle = getStr(30908) % (match[2],match[3]) #'Serie - %s (%s episodios)'
            else:
                scrapedtitle = getStr(30909) + match[2] #'Serie - '
            xbmctools.addnewfolder( CHANNELNAME , "ListaEpisodios" , "Series" , scrapedtitle , match[0] , "" , "" , Serie=match[2] , totalItems=totalmatches)
        elif match[1] == 'Movies':
            scrapedtitle = getStr(30910) % (match[2],match[3]) #'Cine - %s (%s)'
            xbmctools.addnewfolder( CHANNELNAME , "listaVideosEpisodio" , "Cine" , scrapedtitle , match[0] , "" , "" , totalItems=totalmatches)
        else: #Music
            xbmctools.addnewfolder( CHANNELNAME , "ListaEpisodios" , "Musica" , getStr(30911)+match[2] , match[0] , "" , "" , totalItems=totalmatches) #"M�sica - "

    FinalizaPlugin (pluginhandle,category)

# END Buscar
###########################################################################

def ListaSeries(params,url,category):
    """Creates the list for TV Shows, Anime and Music categories and shows it for selection
    """
    logger.info("[tvshack.py] ListaSeries")

    # We use a loading dialog box to give progress feedback.
    pDialog = xbmcgui.DialogProgress()
    text1 = getStr(30912) %(category,) #'Leyendo %s...'
#    text1 = 'Leyendo %s...' %(category,) #'Leyendo %s...'
    pDialog.create('pelisalacarta - TVSack' , text1)
    pDialog.update(0, text1)

    # Get the web page
    data = scrapertools.cachePage(url)

    # We extract the data using regex (patr�n in Spanish)
    # Ex. TV Show: <li><a href="/tv/30_Rock/">30 Rock <font class="new-updated">Updated!</font><span style="margin-top:0px;">69 episodes</span></a></li> 
    # Ex. Anime:   <li><a href="http://tvshack.cc/anime/Avatar__The_Abridged_Series/">Avatar: The Abridged Series<span style="margin-top:0px;">5 episodes</span></a></li>
    # Ex. Music:   <li><a href="http://tvshack.cc/music/Michael_Jackson/">Michael Jackson<span style="margin-top:0px;">27 songs</span></a></li>
    patronvideos = '''(?x)                                  # VERBOSE
        <li><a\ href="                                      # Trash
        (?:http://tvshack\.cc)?([^"]+)">                    # $0 = URL Path (relative) Ej. "/tv/The_Wire/"
        ([^<]+)                                             # $1 = Media Name Ex. Wire, The
        (?:\ <font\ class="new-new">(New)!</font>)?         # $2 = 'New' if it's new media.
        (?:\ <font\ class="new-updated">(Updated)!</font>)? # $3 = 'Updated'
        <span\ style="margin-top:0px;">                     # Trash
        ([0-9]+)                                            # $4 = Number of episodes Ex. 59
        \ ((?:episodes)|(?:songs))                          # $5 = Episodes/Song flag
                                 ''' 
    matches = re.compile(patronvideos).findall(data)

    totalseries = len(matches)
    if totalseries == 0:
        pDialog.close()
        error = xbmcgui.Dialog()
        error.ok('pelisalacarta - TVShack', getStr(30913)) #'Nothing found'
        FinalizaPlugin_con_error(pluginhandle,category)
        return
    i = 0
    step = 100 / totalseries
    for match in matches:
        #Show
        scrapedserie = match[1].decode("utf-8").encode('iso-8859-1',"ignore")
        #Progress indicator update
        i = i + step
        pDialog.update(i, text1+scrapedserie)

        #Show URL
        scrapedurl = "http://tvshack.cc" + match[0]

        # We elaborate on the title that will be shown adding 
        #     * Number of episodes.
        #     * If it's a new show.
        #     * If it's been updated recently.
        if match[5]=='episodes':
            tipo_singular = getStr (30914) #'episodio'
            tipo_plural = getStr (30915) #'episodios'
        else: #'songs'
            tipo_singular = getStr (30916) #'canci�n'
            tipo_plural = getStr (30917) #'canciones'
        if match[4]=='1': #I like when software doesn't say "1 episodes" ;)
            scrapedtitle =    "%s (1 %s)" % (scrapedserie,tipo_singular) # Ex. House (1 episode)
        else:
            scrapedtitle = "%s (%s %s)" % (scrapedserie, match[4], tipo_plural) # Ex. House (69 episodes)

        if match[2]: #New Show
            scrapedtitle = scrapedtitle + getStr(30918) #" (Nuevo)"
        if match[3]: #Nuevos episodios
            scrapedtitle = scrapedtitle + getStr(30919) #" (Nuevos contenidos)"


        # This web doesn't have information about the show in the selection list
        #  This information is in the details view
        #  It will be very time compsumming to get the info now 
        #  if you think that there are more thatn 1300 TV shows
        #  I'm programming it anyway and keeping it just in case in the
        #  future someone programs smalled sellections (maybe alphabetical)

#        scrapedthumbnail, scrapednote = LeeDatosSerie (scrapedurl) #Slow for +100 shows

        scrapedthumbnail = ""
        scrapednote = ""
        
        # Addit to the list
        xbmctools.addnewfolder( CHANNELNAME , "ListaEpisodios" , category , scrapedtitle , scrapedurl , scrapedthumbnail , scrapednote , Serie=scrapedserie , totalItems=totalseries)

    #End of list creation
    pDialog.update(100, text1)
    FinalizaPlugin (pluginhandle,category)
    pDialog.close()

# FIN ListaSeries
###########################################################################
def ListaEpisodios(params,url,category):
    """Lists the episodes in a show
    """
    logger.info("[tvshack.py] ListaEpisodios")
    
    if params.has_key("Serie"):
        serie = params.get("Serie")
    else:
        serie = ""

    # Adds "Add all to Library" option
    if category != 'Musica':
        xbmctools.addnewvideo( CHANNELNAME , "addlist2Library" , category , "", getStr (30920) , url , "" , "" , serie) #"A�ADIR TODOS LOS EPISODIOS A LA BIBLIOTECA"

    listaEp = devuelveListaEpisodios (params,url,category)

    for ep in listaEp:
            xbmctools.addnewvideo( CHANNELNAME , "listaVideosEpisodio" , category , "" , ep['title'] , ep['url'] , ep['thumbnail'] , ep['plot'] , Serie=serie)

    FinalizaPlugin (pluginhandle,category)

def addlist2Library(params,url,category,verbose=True):
    """Adds al episodes of a given show to the library
    
        What it really does is create strm files containing plugin calls
        to the pelisalacarta plugin on each episode.
        For this to work you have to manually add the pelisalacarta-library path
        to the library with the apropiate Content provider (tvdb works just fine)
    """
    logger.info("[tvshack.py] addlist2Library")

    if params.has_key("Serie"):
        serie = params.get("Serie")
    else:
        serie = ""
    
    if verbose:
        pDialog = xbmcgui.DialogProgress()
        pDialog.create('pelisalacarta', 'A�adiendo episodios...')

    listaEp = devuelveListaEpisodios (params,url,category)
    episodios = 0
    errores = 0
    nuevos = 0
    for i,ep in enumerate(listaEp):
        if verbose:
            pDialog.update(i*100/len(listaEp), 'A�adiendo episodio...',ep['title'])
            if (pDialog.iscanceled()):
                return
        try:
            nuevos = nuevos + library.savelibrary(ep['title'],ep['url'],ep['thumbnail'],"",ep['plot'],canal=CHANNELNAME,category="Series",Serie=serie,verbose=False,accion="strm_detail",pedirnombre=False)
            episodios = episodios + 1
        except IOError:
            logger.info("Error al grabar el archivo "+ep['title'])
            errores = errores + 1

    if verbose:
        pDialog.close()
    if errores > 0:
        logger.info ("[tvshack.py - addlist2Library] No se pudo a�adir "+str(errores)+" episodios") 

    if verbose:
        library.update(episodios,errores,nuevos)

    return nuevos
    
def devuelveListaEpisodios (params,url,category):
    """Scrapea la p�gina de episodios y la devuelve como lista de diccionarios
    
    --> Los habituales en los canales de pelisalacarta.
    <-- [{Episodio}]    Lista de diccionarios con los datos de cada episodio
            Al a�adir los episodios como diccionarios nos permite a�adir o borrar claves a voluntad
            dejando abierto el dise�o a poder a�adir informaci�n en los canales que
            �sta exista.
            Las clave b�sicas en el momento de escribir este canal son:
            'title' : T�tulo del episodio - Para la biblioteca peferiblemente en formato
                                 NOMBRE_SERIE - TEMPORADAxEPISODIO T�TULO_EPISODIO LOQUESEA
            'url'     : URL del episodio
            'plot'    : Resumen del episodio (o de la serie si �ste no existe para este canal)
            'thumbnail' : Fotograma del episodio o car�tula de la serie 
    """

    if params.has_key("Serie"):
        serie = params.get("Serie")
    else:
        serie = ""

    # Descarga la p�gina
    data = scrapertools.cachePage(url)

    # Primero debemos separar los datos por temporada
    patrontemporadas = '''(?x)                                                        #            Activa opci�n VERBOSE. Esto permite
                                                                                                                #            un poco de libertad para ordenar
                                                                                                                #            el patr�n al ignorar los espacios.
                                                                                                                #            Tambi�n permite comentarios como �ste.
                                                                                                                # ---    COMIENZO DEL PATRON REAL    ---
        <h2\ class="h-list-title">Season\                                     #            Basura
        ([0-9]+)                                                                                        # $0 = Temporada
        <\/h2>                                                                                            #            Basura
        ''' 
    splitdata = re.split(patrontemporadas,data)
    
    #Ahora tenemos la p�gina separada entre
    #    1. Secciones sin v�deos (La primera)
    #    2. Secciones de texto de temporada. De aqu� sacamos el n�mero de temporada
    #    3. Secci�n de videos de temporada.
    temporada = '0'
    # Extraemos los episodios por medio de expresiones regulares (patr�n)
    # Ej. Serie:    <li><a href="/tv/Family_Guy/season_1/episode_1/">ep1. Death Has a Shadow</a><a href=""><span>31/1/1999</span></a></li>
    # Ej. Anime:    <li><a href="http://tvshack.cc/anime/07_Ghost/season_1/episode_5/">ep5. Episode 5</a><a href=""><span>??/??/????</span></a></li> 
    # Ej. Musica: <li><a href="http://tvshack.cc/music/Michael_Jackson/C85E8225E45E/">Black Or White<span>2,301 views</span></a></li><li><a 
    patronepisodios = '''(?x)                                                         #            Activa opci�n VERBOSE. Esto permite
        <li><a\ href="                                                                            #            Basura
        (?:http://tvshack\.cc)?([^"]+)">                                     #\g1 = Path (relativo) del episodio/video
        (?:ep([0-9]+)\.\ )?                                                                 #\g2 = N�mero de episodio
        ([^<]+)                                                                                         #\g3 = Nombre del episodio
        (?:<\/a><a\ href="">)?<span>                                                #            Basura
        ([0-9\?]+\/[0-9\?]+\/[0-9\?]+)?                                         #\g4 = Fecha de emisi�n (s�lo series)
        (?:([0-9,]+)\ views)?                                                             #\g5 = Veces visto (s�lo m�sica)
        <\/span><\/a><\/li>                                                                 #            Basura
    ''' 
    episodiosREO = re.compile(patronepisodios) ## Objeto de Expresi�n Regular (REO)

    listaEp = [] # Lista de Episodios
    Ep = {}            # Diccionario con la info de cada episodio

    # Como en �ste canal no hay informaci�n por episodio, cogemos el argumento
    # y la car�tula de la serie como datos para cada episodio 
    Ep['thumbnail'],Ep['plot'] = LeeDatosSerie (data)

    for parte in splitdata:
        if re.match("[0-9]+", parte): #texto de temporada
            temporada = parte
        else: # Busquemos episodios
            # Recorremos un iterador por los matches de episodiosREO 
            # (m�s elegante y breve en este caso aunque hay que conocer los 
            # Objetos de Expresi�n Regular (REO) y los matchobjects)
            for match in episodiosREO.finditer (parte):
                if category != 'Musica':
                    Ep['title'] = match.expand (serie + ' - ' + temporada + 'x\g<2> - \g<3> (\g<4>)') #con expand los grupos referenciaos empiezan en 1
                else:
                    Ep['title'] = match.expand ('\g<3> (visto \g<5> veces)') #con expand los grupos referenciaos empiezan en 1
                #URL del episodio
                Ep['url'] = "http://tvshack.cc" + match.group(1)
                listaEp.append(Ep.copy()) #Se a�ade el episodio a la lista (hay que copiarlo)

    return listaEp
                        
# FIN devuelveListaEpisodios
###########################################################################
def ListaDetallada(params,url,category):
    """Crea el listado de Espect�culos de las secciones de Cine y Docs.
    """
    logger.info("[tvshack.py] ListaDetallada")

    # Iniciamos un cruadro de di�logo de espera.
    pDialog = xbmcgui.DialogProgress()
    texto1 = 'Leyendo %s...' % (category,)
    pDialog.create('pelisalacarta' , texto1)
    pDialog.update(0, texto1)

    # Descargamos la p�gina
    data = scrapertools.cachePage(url)

    # Extraemos los videos por medio de expresiones regulares (patr�n)
    # Ej. Cine: <li><a href="/movies/_Rec__2__2009_/">[Rec] 2<span style="margin-top:0px;">2009</span></a></li> 
    # Ej. Docu: <li><a href="/movies/Ancient_Aliens__2009_/">Ancient Aliens<span style="margin-top:0px;">2009</span></a></li>
    patronvideos = '''(?x)                                                                #            Activa opci�n VERBOSE.
        <li><a\ href="                                                                            #            Basura
        ([^"]+)">                                                                                     # $0 = Path (relativo) del v�deo Ej. "/movies/Rec__2__2009_/"
        ([^<]+)                                                                                         # $1 = Nombre del video Ej. [Rec] 2
        (?:\ <font\ class="new-new">(New)!</font>)?                 # $2 = 'New' si el video es nuevo.
        (?:\ <font\ class="new-updated">(Updated)!</font>)? # $3 = 'Updated' Creo que no se usa. pero no hace da�o
        <span\ style="margin-top:0px;">                                         #            Basura
        ([0-9]+)</span>                                                                         # $4 = A�o de la producci�n Ej. 2009
                                 ''' 
    matches = re.compile(patronvideos).findall(data) # Paso del DOTALL-no hace falta para nada.

    totalmatches = len(matches)
    if totalmatches == 0:
        pDialog.close()
        error = xbmcgui.Dialog()
        error.ok('pelisalacarta - Canal TVShack','No se encontr� nada que listar')
        FinalizaPlugin_con_error(pluginhandle,category)
        return

    i = 0
    step = 100 / totalmatches
    for match in matches:
        #Serie
        scrapedserie = match[1]    

        #Actualizados el di�logo de espera. Esto muestra el avance y por cual serie vamos
        i = i + step
        pDialog.update(i, texto1+scrapedserie)

        #URL del video
        scrapedurl = "http://tvshack.cc" + match[0]

        # En el t�tulo (que se mostrar� en la siguiente pantalla) elaboramos 
        # un poquito m�s a�adiendo informaci�n sobre:
        #     * El a�o de producci�n.
        #     * Si el video ha sido a�adido recientemente.
        scrapedtitle = '%s (%s)' % (match[1],match[4])
        if match[2]: #Contenido Nuevo
            scrapedtitle = scrapedtitle + " (Nuevo)"
            
        # �sta web no tiene informaci�n de cada video en la lista de selecci�n.
        #     Esa informaci�n est� en la p�gina del video.
        #     Obtenerla en este momento seguramente ser�a muy costoso (en tiempo),
        #     Quiz� sea interesante para busquedas
        #     m�s limitadas... De todas formas lo programo para evaluar
#        scrapedthumbnail, scrapednote = LeeDatosSerie (scrapedurl)
        scrapedthumbnail = ""
        scrapednote = ""
        
        # A�ade al listado de XBMC
        xbmctools.addnewfolder( CHANNELNAME , "listaVideosEpisodio" , category , scrapedtitle , scrapedurl , scrapedthumbnail , scrapednote , totalItems=totalmatches)

    pDialog.update(100, texto1)
    FinalizaPlugin (pluginhandle,category)
    pDialog.close()

# FIN ListaDetalle
###########################################################################
def strm_detail (params,url,category):
    '''Reproduce el episodio seleccionado desde un fichero strm
    '''
    listaVideosEpisodio (params,url,category,strmfile=True)

def listaVideosEpisodio (params,url,category,strmfile=False):
    '''Extrae y muestra los v�deos disponibles para un episodio
    
    Inicialmente nos conformaremos s�lo con los de megavideo/megaupload
    Luego ir� a�adiendo el resto de los que me encuentre
    
    Tambien quiero considerar la opci�n de mostrar la lista de opciones o
    elegir una al azar o por alg�n mecanismo mejor. As� se ahorrar�a un paso
    aunque supongo que habr� riesgo de no elegir una buena opci�n.
    '''
    logger.info("[tvshack.py] ListaVideosEpisodios")


    if params.has_key("Serie"):
        serie = params.get("Serie")
    else:
        serie = ""

    title = urllib.unquote_plus( params.get("title") )
    thumbnail = urllib.unquote_plus( params.get("thumbnail") )

    # Descarga la p�gina
    data = scrapertools.cachePage(url)
    #Recortamos los datos al cuadro de enlaces alternativos
    match = re.search('<h3>Alternate links</h3>(.+?)</ul>',data,re.DOTALL)
    if not match:
        dlog ('[tvshack.py] listaVideosEpisodio - No hay secci�n de Alternate links')
        dlog (data)
        advertencia = xbmcgui.Dialog()
        advertencia.ok('No hay videos' , 'No hay videos v�lidos para este episodio.')
        return
    data = match.expand('\g<1>')
    
#Ej. Video por defecto:<li><a href="http://tvshack.cc/tv/Lost/season_4/episode_6/"><img src="http://road.../megavideo.gif" />megavideo.com</a> <small>(selected)</small></li>
#Ej. Alternat:<li><a href="http://tvshack.cc/tv/Lost/season_4/episode_6/a:723568/"><img src="http://road.../megavideo.gif" />megavideo.com</a></li>
    patronvideos = '''(?x)                                                                #            Activa opci�n VERBOSE.
        <li><a\ href="                                                                            #            Basura
        ([^"]+)">                                                                                     # $0 = URL del episodio
        <img\ src="                                                                                 #            Basura
        ([^"]+)"\ \/>                                                                             # $1 = URL de miniatura 
        ([^<]+)<\/a>                                                                                # $2 = Server
        (?:\ <small>\((selected)\)<\/small>)?                             # $3 = Opcional: Video seleccionado
        <\/li>                                                                                            #            Basura
    '''
    matches = re.findall(patronvideos, data)
    if len (matches) == 0:
        dlog ('[tvshack.py] listaVideosEpisodio - No hay enlaces en el cuadro alternate links.')
        dlog (data)
        advertencia = xbmcgui.Dialog()
        advertencia.ok('pelisalacarta - tvshack' , 'No hay videos v�lidos para este episodio.')
        return

    opciones = []
    servers = []
    for i,match in enumerate(matches):
        scrapedurl = match[0]
        scrapedthumbnail = match[1]
        if scrapedthumbnail.find('megavideo') > -1:
            scrapedthumbnail = MEGAVIDEO_POSTER
        scrapedserver = match[2].split ('.')[0].lower() #Convierte 'Megavideo.com' -> 'megavideo'
        servers.append (scrapedserver) 
        scrapedtitle = str(i) + '. [' + scrapedserver + ']'
        if match[3]=='selected':
            scrapedtitle = scrapedtitle + ' (Por defecto)'
        if scrapedserver not in ALLOWED_SERVERS:
            scrapedtitle = scrapedtitle + ' (NO SOPORTADO)'
            
        opciones.append(scrapedtitle)
    if config.getSetting("default_action")=="0" or config.getSetting("default_action")=="3":
        dia = xbmcgui.Dialog()
        seleccion = dia.select("Elige un v�deo", opciones)
    else:
        #Si existe, preferimos megavideo.
        try:
            seleccion = servers.index('megavideo')
        except: #Si no hay megavideo buscamos cualquiera que sirva
            seleccion = 0
            while seleccion < len (opciones) and servers[seleccion] not in ALLOWED_SERVERS:
                seleccion = seleccion +1 
        if seleccion == len(opciones):
            dlog ('[tvshack.py] listaVideosEpisodio - No hay videos en los servidores soportados para este episodio.')
            advertencia = xbmcgui.Dialog()
            advertencia.ok('pelisalacarta - tvshack' , 'No hay videos v�lidos para este episodio.')
            return
    dlog( str(seleccion))
    if seleccion == -1:
        return
    else:
        params['title'] = title + ' [' + servers[seleccion] + ']'
        params['server'] = servers[seleccion]
        playVideo (params,matches[seleccion][0],category,strmfile)

# FIN listaVideosEpisodio
###########################################################################
def playVideo(params,url,category,strmfile=False):
    '''Reproduce el video seleccionado
    '''
    logger.info("[tvshack.py] playVideo")

    if params.has_key("Serie"):
        serie = params.get("Serie")
    else:
        serie = ""

    if (params.has_key("category")):
        category = params.get("category")

    title = urllib.unquote_plus( params.get("title") )
    if params.has_key("thumbnail"):
        thumbnail = urllib.unquote_plus( params.get("thumbnail") )
    else:
        thumbnail = ''
        
    if params.has_key("plot"):
        plot = params.get("plot")
    else:
        plot = xbmc.getInfoLabel( "ListItem.Plot" )

    server = params["server"]

    if DEBUG:
        logger.info("[tvshack.py] url="+url)
        logger.info("[tvshack.py] title="+title)
        logger.info("[tvshack.py] plot="+plot)
        logger.info("[tvshack.py] thumbnail="+thumbnail)
        logger.info("[tvshack.py] server="+server)

    # Descarga la p�gina
    data = scrapertools.cachePage(url)

    #Averiguamos las partes del video (Puede tener m�s de una)
    partes = re.findall('<a href="javascript:changevid\(([0-9]+)\);"',data)

    # Y el path relativo de los v�deos    
#JUR CAMBIO EN WEB 01/04/2010
#    patronpath = '''(?x)                                    #            Activa opci�n VERBOSE.
#        http://tvshack\.cc/report_video/     #            Basura
#        ([^/]+/[^/]+)                                             # $0 = Path relativo Ej. 'tv/716063'
#        /","report"                                                 #            Basura
#    '''
    patronpath = '''(?x)                                    #            Activa opci�n VERBOSE.
        http://tvshack\.cc/video_load/         #            Basura
        ([^/]+/[^/]+)                                             # $0 = Path relativo Ej. 'tv/716063'
        /'\+part                                                        #            Basura
    '''
    paths=re.findall(patronpath,data)

    #JUR-PROV: De momento voy a considerar los v�deos de 1 s�la parte.
    # Para los v�deos con m�s partes habr� que crear una funci�n especial que
    # pregunte una sola vez y meta todos los v�deos juntos.
    if len(partes) > 1:
        logger.info ("[tvshack] playVideo - Video multiparte - pendiente:" + str(len(partes)))
        dialog = xbmcgui.Dialog()
        dialog.ok('pelisalacarta - tvshack','Este video tiene varias partes.','En esta versi�n de pelisalacarta no est�n soportados.','Eliga otro video con una s�la parte.')
#        for parte in partes:
    elif len(partes) == 1:
        url = 'http://tvshack.cc/video_load/'+paths[0] + '/' + partes[0]
        #Esta URL sigue sin ser un enlace megaupload u otro servidor v�lido por lo que seguimos scrapeando
        # para evitar excesivas selecciones por parte del usuario.

        # Descarga la p�gina
        data2 = scrapertools.cachePage(url)
        if server == 'megavideo':
            dlog ("[tvshack.py]playVideo: Server= megavideo")

            # 
            #Ej.<embed src="http://www.megavideo.com/v/5ZZHOM74...
            patronpath = '''(?x)                                                     #            Activa opci�n VERBOSE.
                <embed\ src="http://www\.megavideo\.com/v/     #            Basura
                (.{8})                                                                             # $0 = url megavideo Ej. '5ZZHOM74'
            '''
            mediaurl=re.findall(patronpath,data2)
            if len (mediaurl) == 0:
                dlog ("[tvshack.py]playVideo: No se encontr� la url de megavideo en:")
                dlog (data2)
                dialog = xbmcgui.Dialog()
                dialog.ok('pelisalacarta - tvshack','No se encontr� el video en megavideo.','Eliga otro video.')
                return
            elif len (mediaurl) > 1:
                dlog ("[tvshack.py]playVideo: Hay m�s de un enlace de megavideo (y no deber�a)")
                for url in mediaurl:
                    dlog (url)
            mediaurl = mediaurl[0]
#            xbmctools.playvideo(CHANNELNAME,server,mediaurl,category,title,thumbnail,plot,Serie=Serie)
            dlog ("[tvshack.py]playVideo: Llamando al play. mediaurl= "+mediaurl)
            xbmctools.playvideo(CHANNELNAME,'Megavideo',mediaurl,category,title,'','',Serie=serie,strmfile=strmfile)
        else: # Video de otro servidor (no megavideo)
            #Probamos si es flash...
            flashmatch = re.search('flashvars="file=(.+?)&type=flv',data2)
            if flashmatch != None:
                dlog ('[tvshack.py]playVideo: Video flash - url = ' + flashmatch.group(1))
                xbmctools.playvideo(CHANNELNAME,'Directo',flashmatch.group(1),category,title,'','',Serie=serie,strmfile=strmfile)
                return
            #Si no, buscamos otras fuentes de video
            othersmatch = re.search('src="([^"]+)"',data2)
            if othersmatch != None and server in ALLOWED_SERVERS:
                url = othersmatch.group(1).replace('&amp;','&')
                xbmctools.playvideo(CHANNELNAME,server,url,category,title,'','',Serie=serie,strmfile=strmfile)
                return

            dlog ("[tvshack.py]playVideo: Servidor no soportado: "+server)
            dialog = xbmcgui.Dialog()
            dialog.ok('pelisalacarta - tvshack - '+server,'El video seleccionado es de '+server,'Ese servidor a�n no est� soportado en TVShack.')
            return

def FinalizaPlugin (pluginhandle,category):
    """Tareas comunes al final del plugin. Sin ordenaci�n
    """
    # Indicar metadatos del plugin para skis (Categor�a y contenido)
    xbmcplugin.setPluginCategory (pluginhandle , category)
    xbmcplugin.setContent (pluginhandle , category) #Estamos usando category como content.

    # Deshabilitar ordenaci�n
    xbmcplugin.addSortMethod (handle=pluginhandle , sortMethod=xbmcplugin.SORT_METHOD_NONE)

    # Finalizar Directorio del Plugin
    xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )
    
def FinalizaPlugin_con_error (pluginhandle,category):
    """Tareas comunes al final del plugin. Sin ordenaci�n
    """
    # Indicar metadatos del plugin para skis (Categor�a y contenido)
    #xbmcplugin.setPluginCategory (pluginhandle , category)
    #xbmcplugin.setContent (pluginhandle , category) #Estamos usando category como content.

    # Deshabilitar ordenaci�n
    #xbmcplugin.addSortMethod (handle=pluginhandle , sortMethod=xbmcplugin.SORT_METHOD_NONE)

    # Finalizar Directorio del Plugin
    xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=False )
    
def LeeDatosSerie (tdata):
    """Obtiene una miniatura y la sinopsis de una serie
    
    tdata                                 --> Datos de la p�gina de episodios de la serie
    miniatura,sinopsis    <-- Tupla con los datos requeridos
    """

    # PATRON PARA EXTRAER LOS POSTER DE LAS SERIES
    patronposter = '''(?x)                                                                #            Activa opci�n VERBOSE. Esto permite
                                                                                                                #            un poco de libertad para ordenar
                                                                                                                #            el patr�n al ignorar los espacios.
                                                                                                                #            Tambi�n permite comentarios como �ste.
                                                                                                                # ---    COMIENZO DEL PATRON REAL    ---
        <img\ src="                                                                                 #            Basura    
        ([^"]+)                                                                                         # $0 = Poster Ej. http://roadrunner.tvshack.cc/tv-posters/16.jpg
        "\ alt="Poster"\ \/>                                                                #            Basura
    '''
    posterREO = re.compile(patronposter) # Objeto de Expresi�n Regular (REO)
    # Buscamos el Poster
    match = posterREO.search(tdata)
    if match:
        miniatura = match.group(1)
    else:
        miniatura = ""



    # PATRON PARA EXTRAER LA SINOPSIS DE LAS SERIES
    patronsinopsis = '''(?x)                                                            #            Activa opci�n VERBOSE. Esto permite
                                                                                                                #            un poco de libertad para ordenar
                                                                                                                #            el patr�n al ignorar los espacios.
                                                                                                                #            Tambi�n permite comentarios como �ste.
                                                                                                                # ---    COMIENZO DEL PATRON REAL    ---
        <p>                                                                                                 #            Basura    
        ([^<]+)                                                                                         # $0 = Sinopsis
        <\/p>                                                                                             #            Basura
    '''
    sinopsisREO = re.compile(patronsinopsis) # Objeto de Expresi�n Regular (REO)

    # Buscamos la sinopsis
    match = sinopsisREO.search(tdata)
    if match:
        sinopsis = match.group(1)
    else:
        sinopsis = ""

    return miniatura,sinopsis
    
# Estas son las expresiones XPATH para obtener el poster y la sinopsis.
# Averiguar si se pueden usar de alguna forma en python
#id('show-information-column2')/x:p
#id('show-information-column1')/x:div/x:img    

def dlog (text):
    if DEBUG:
        logger.info(text)

