# -*- coding: utf-8 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para asia-team
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#------------------------------------------------------------

import urlparse,urllib2,urllib,re,string,time,xbmc,xbmcgui
import os, sys

try:
    from core import logger
    from core import config
    from core import scrapertools
    from core.item import Item
    from core import xbmctools
    from core import downloadtools
    from servers import servertools
except:
    # En Plex Media server lo anterior no funciona...
    from Code.core import logger
    from Code.core import config
    from Code.core import scrapertools
    from Code.core.item import Item


CHANNELNAME = "asiateam"
DEBUG = True
SUB_PATH = xbmc.translatePath( os.path.join( downloadtools.getDownloadPath() , 'Subtitulos\AsiaTeam' ) )
if not os.path.exists(SUB_PATH):
    os.mkdir(SUB_PATH)

SUBTEMP_PATH = xbmc.translatePath( os.path.join( config.get_data_path() , 'subtitulo.srt' ) )

def isGeneric():
    return True

def mainlist(item):
    logger.info("[asiateam.py] mainlist")

    itemlist = []
    itemlist.append( Item(channel=CHANNELNAME, title="Películas", action="peliculas", url="http://www.asia-team.net/foros/forumdisplay.php?f=119"))
    itemlist.append( Item(channel=CHANNELNAME, title="Series", action="series", url="http://www.asia-team.net/foros/forumdisplay.php?f=44"))	

    return itemlist

def peliculas(item):
    logger.info("[asiateam.py] tipo peliculas")

    itemlist = []
    itemlist.append( Item(channel=CHANNELNAME, action="lista_p", title="Estrenos" , url="http://www.asia-team.net/foros/forumdisplay.php?f=120" , folder=True) )
    itemlist.append( Item(channel=CHANNELNAME, action="lista_p", title="Acción / Sci-Fi" , url="http://www.asia-team.net/foros/forumdisplay.php?f=121" , folder=True) )
    itemlist.append( Item(channel=CHANNELNAME, action="lista_p", title="Artes Marciales / Samurai / Epicas" , url="http://www.asia-team.net/foros/forumdisplay.php?f=122" , folder=True) )
    itemlist.append( Item(channel=CHANNELNAME, action="lista_p", title="Aventuras / Comedia / Familiares" , url="http://www.asia-team.net/foros/forumdisplay.php?f=123" , folder=True) )
    itemlist.append( Item(channel=CHANNELNAME, action="lista_p", title="Drama / Romance" , url="http://www.asia-team.net/foros/forumdisplay.php?f=124" , folder=True) )
    itemlist.append( Item(channel=CHANNELNAME, action="lista_p", title="Documentales / Musicales" , url="http://www.asia-team.net/foros/forumdisplay.php?f=176" , folder=True) )
    itemlist.append( Item(channel=CHANNELNAME, action="lista_p", title="Terror / Horror / Gore" , url="http://www.asia-team.net/foros/forumdisplay.php?f=125" , folder=True) )
    itemlist.append( Item(channel=CHANNELNAME, action="lista_p", title="Thriller / Crimen" , url="http://www.asia-team.net/foros/forumdisplay.php?f=126" , folder=True) )
    itemlist.append( Item(channel=CHANNELNAME, title="Índice", action="indice_peliculas"))
			
    return itemlist

def series(item):
    logger.info("[asiateam.py] tipo series")
    
    itemlist = []
    itemlist.append( Item(channel=CHANNELNAME, action="lista_s", title="Series en Curso" , url="http://www.asia-team.net/foros/forumdisplay.php?f=45" , folder=True) )
    itemlist.append( Item(channel=CHANNELNAME, action="lista_s", title="Series Finalizadas" , url="http://www.asia-team.net/foros/forumdisplay.php?f=46" , folder=True) )
    itemlist.append( Item(channel=CHANNELNAME, title="Índice", action="indice_series"))	
			
    return itemlist	
	
def lista_p(item):
	logger.info("[asiateam.py] peliculas")

    # Descarga la página
	data = scrapertools.cachePage(item.url)

    # Extrae las entradas
	patronvideos  = '<!-- show threads -->(.*?)<!-- end show threads -->'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	#if DEBUG: scrapertools.printMatches(matches)
	itemlist = []
	for post in matches:
		patronvideos = '<tr>(.*?)</tr>'
		posts =re.compile(patronvideos, re.DOTALL).findall(post)
		for elemento in posts:
			patronvideos = '<td class="alt2"><img src="(.*?)" alt.*?>.*<a href="showthread.php\?t=(.*)" id=".*?>(.*?)</a>'
			matches2 = re.compile(patronvideos,re.DOTALL).findall(elemento)

			for match in matches2:
				title_invalid= match[2]
				title_invalid= title_invalid[:10]
				if title_invalid=="IMPORTANTE":break
				scrapedurl = "http://www.asia-team.net/foros/showthread.php?t="+match[1]
				scrapedtitle = match[2].split(' [')
				scrapedtitle = scrapedtitle[0]
				scrapedthumbnail = "http://imagenes.asia-team.net/afiche/"+match[1]+".jpg"

				# Añade al listado
				itemlist.append( Item(channel=CHANNELNAME, action="videos_p", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , folder=True) )
			  
	# Extrae la marca de siguiente página
	patronvideos  = '<!-- controls below thread list -->(.*?)<!-- / controls below thread list -->'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	if DEBUG: scrapertools.printMatches(matches)
	for elemento in matches:
		patronvideos = '<a rel="next" class="smallfont" href="(.*?)">'
		matches2 = re.compile(patronvideos,re.DOTALL).findall(elemento)

		if len(matches2)>0:
			scrapedtitle = "Página siguiente"
			scrapedurl = "http://www.asia-team.net/foros/"+matches2[0]
			scrapedurl = scrapedurl.replace('amp;','')
			scrapedthumbnail = ""
			itemlist.append( Item( channel=CHANNELNAME , title=scrapedtitle , action="lista_p" , url=scrapedurl , thumbnail=scrapedthumbnail, folder=True ) )

	return itemlist
	
def lista_s(item):
	logger.info("[asiateam.py] series")

    # Descarga la página
	data = scrapertools.cachePage(item.url)

    # Extrae las entradas
	patronvideos  = '<!-- show threads -->(.*?)<!-- end show threads -->'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	itemlist = []
	for post in matches:
		patronvideos = '<tr>(.*?)</tr>'
		posts =re.compile(patronvideos, re.DOTALL).findall(post)
		for elemento in posts:
			patronvideos = '<td class="alt2"><img src="(.*?)" alt.*?>.*<a href="showthread.php\?t=(.*)" id=".*?>(.*?)</a>'
			matches2 = re.compile(patronvideos,re.DOTALL).findall(elemento)
			if DEBUG: scrapertools.printMatches(matches2)
			for match in matches2:
				scrapedurl = "http://www.asia-team.net/foros/showthread.php?t="+match[1]
				scrapedtitle = match[2].split(' [')
				scrapedtitle = scrapedtitle[0]
				scrapedthumbnail = "http://imagenes.asia-team.net/afiche/"+match[1]+".jpg"

				# Añade al listado
				itemlist.append( Item(channel=CHANNELNAME, action="videos_s", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , folder=True) )
			  
	# Extrae la marca de siguiente página
	patronvideos  = '<!-- controls below thread list -->(.*?)<!-- / controls below thread list -->'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	if DEBUG: scrapertools.printMatches(matches)
	for elemento in matches:
		patronvideos = '<a rel="next" class="smallfont" href="(.*?)">'
		matches2 = re.compile(patronvideos,re.DOTALL).findall(elemento)

		if len(matches2)>0:
			scrapedtitle = "Página siguiente"
			scrapedurl = "http://www.asia-team.net/foros/"+matches2[0]
			scrapedurl = scrapedurl.replace('amp;','')
			scrapedthumbnail = ""
			itemlist.append( Item( channel=CHANNELNAME , title=scrapedtitle , action="lista_s" , url=scrapedurl , thumbnail=scrapedthumbnail, folder=True ) )

	return itemlist

def videos_p(item):

	logger.info("[asiateam.py] videos peliculas")
	# Descarga la página
	data = scrapertools.cachePage(item.url)
	title = item.title
	scrapedthumbnail = item.thumbnail
	scrapedplot = ""
	subtitulo = ""
	
    # Extrae las entradas
	patronimagen  = 'titulo.png".*?<img src="(.*?)".*?>'
	matches = re.compile(patronimagen,re.DOTALL).findall(data)
	if len(matches)>0:
		scrapedthumbnail = matches[0]
	patronplot  = 'sinopsis.png".*?>.*?<font color="(?:N|n)avy".*?>(.*?)</td>'
	matches = re.compile(patronplot,re.DOTALL).findall(data)
	if len(matches)>0:
		scrapedplot =  matches[0]
		scrapedplot = re.sub("</?\w+((\s+\w+(\s*=\s*(?:\".*?\"|'.*?'|[^'\">\s]+))?)+\s*|\s*)/?>",'',scrapedplot)
		scrapedplot = scrapedplot.replace('&quot;','"')
	patronsubs = 'subtitulos.png".*?>.*<a href="http://subs.asia-team.net/file.php\?id=(.*?)".*?>'
	matches = re.compile(patronsubs,re.DOTALL).findall(data)
	if len(matches)>0:
		subtitulo =  "http://subs.asia-team.net/download.php?id="+matches[0]
	itemlist = []
	listavideos = servertools.findvideos(data)
	for video in listavideos:
		scrapedtitle = title.strip() + " - " + video[0]
		videourl = video[1]
		server = video[2]
		if server.lower() =="megaupload":
			url = "http://www.megavideo.com/?d="+videourl
			data = scrapertools.cachePage(url)		
			patronname = 'flashvars.title = "(.*?)"'
			matches = re.compile(patronname,re.DOTALL).findall(data)
			if len(matches)>0:
				titulo = matches[0]
				#logger.info("Titulo: "+titulo)			
				if titulo[-3:]=="avi" or titulo[-3:]=="mkv" or titulo[-3:]=="mp4":
						scrapedtitle = "[MV] "+ title.strip()+"-"+titulo
				
		if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+videourl+"], thumbnail=["+scrapedthumbnail+"]")

		# Añade al listado de XBMC
		itemlist.append( Item(channel=CHANNELNAME, action="sub", title=scrapedtitle , url=videourl , thumbnail=scrapedthumbnail , plot=scrapedplot , extra=server , category=subtitulo , folder=True) )
	
	#Añade opcion para filestube y asianmovielink
	if re.search('asia-team.net',item.url)!=None:
		if re.search(' / ',title)!=None:
			title = title.split(' / ')
			buscar = title[0]
		else:
			buscar = title
		
		itemlist.append( Item(channel=CHANNELNAME, action="search", title="Buscar Película en FilesTube",  extra=buscar , folder=True) )
		
	return itemlist
	
def videos_s(item):

	logger.info("[asiateam.py] videos series")
	# Descarga la página
	data = scrapertools.cachePage(item.url)
	title = item.title
	scrapedthumbnail = item.thumbnail
	scrapedplot = ""
	sub = {"Capitulo 1":""}
	lista_titulos = []

    # Extrae las entradas
	patronimagen  = 'titulo.png".*?<img src="(.*?)".*?>'
	matches = re.compile(patronimagen,re.DOTALL).findall(data)
	if len(matches)>0:
		scrapedthumbnail = matches[0]
	patronplot  = 'sinopsis.png".*?>.*?<font color="(?:N|n)avy".*?>(.*?)</td>'
	matches = re.compile(patronplot,re.DOTALL).findall(data)
	if len(matches)>0:
		scrapedplot =  matches[0]
		scrapedplot = re.sub("</?\w+((\s+\w+(\s*=\s*(?:\".*?\"|'.*?'|[^'\">\s]+))?)+\s*|\s*)/?>",'',scrapedplot)
		scrapedplot = scrapedplot.replace('&quot;','"')
	
	patronsubs = 'subtitulos.png".*?>(.*?)<!-- sig -->'
	matches = re.compile(patronsubs,re.DOTALL).findall(data)
	for elemento in matches:
		patronsubs = '<a href="http://subs.asia-team.net/file.php\?id=(.*?)".*?>.*?<font color="navy">(.*?)</font></b></a>'
		matches2 = re.compile(patronsubs,re.DOTALL).findall(elemento)
		if len(matches2)>0:
			for match in matches2:
				sub[match[1]] = "http://subs.asia-team.net/download.php?id="+match[0]	
	itemlist = []
	listavideos = servertools.findvideos(data)
	for video in listavideos:
		try: 
			lista_titulos.index(video[0])
			scrapedtitle = title.strip() + " - " + video[0] + " X264"
		except:
			lista_titulos.append(video[0])
			scrapedtitle = title.strip() + " - " + video[0] + " XVID"

		videourl = video[1]
		server = video[2]
		try:
			clave_sub = video[0]
			clave_sub = clave_sub.split(' -')
			subtitulo = sub[clave_sub[0]]
			if DEBUG:logger.info("CLAVE "+ subtitulo)			
		except:
			subtitulo = ""
			logger.info("Sin subtitulo")
		if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+videourl+"], thumbnail=["+scrapedthumbnail+"]")

		# Añade al listado de XBMC
		itemlist.append( Item(channel=CHANNELNAME, action="sub", title=scrapedtitle , url=videourl , thumbnail=scrapedthumbnail , plot=scrapedplot , extra=server , category=subtitulo , folder=True) )
	
	#Añade opcion para filestube
	if re.search('asia-team.net',item.url)!=None:
		if re.search(' / ',title)!=None:
			title = title.split(' / ')
			buscar = title[0]
		else:
			buscar = title
		
		itemlist.append( Item(channel=CHANNELNAME, action="search", title="Buscar Serie en FilesTube",  extra=buscar , folder=True) )
		
	return itemlist

def search(item):
	logger.info("[asiateam.py] busqueda")
    
	tecleado = ""
	keyboard = xbmc.Keyboard(item.extra,"Acepte o Modifique la Búsqueda")
	keyboard.doModal()
	if (keyboard.isConfirmed()):
		tecleado = keyboard.getText()
		if len(tecleado)<=0:
			return
	item.extra = tecleado

	itemlist = searchresults(item)

	return itemlist
    
def searchresults(item):
	logger.info("[asiateam.py] resultados")
	teclado = item.extra.replace(" ", "+")
	return filestube(item,teclado)


def filestube(item,teclado):

	logger.info("[asiateam.py] filestube")

    # Descarga la página
	data = scrapertools.cachePage("http://www.filestube.com/search.html?q="+teclado+"+avi+mkv+mp4&hosting=3")
    # Extrae las entradas
	patronvideos  = '<div class="star.*?>.*?<div.*?>(.*?)<br />.*?<a href=".*?>.*?<a href="(.*?)".*?>'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	if DEBUG: scrapertools.printMatches(matches)

	itemlist = []
	if len(matches)>0:
		for match in matches:
			scrapedurl = match[1]
			scrapedtitle = match[0]
			scrapedtitle = re.sub("</?\w+((\s+\w+(\s*=\s*(?:\".*?\"|'.*?'|[^'\">\s]+))?)+\s*|\s*)/?>",'',scrapedtitle)
			logger.info(scrapedtitle)

			# Añade al listado
			itemlist.append( Item(channel=CHANNELNAME, action="videos_p", title=scrapedtitle , url=scrapedurl , folder=True) )
	
	# Extrae la marca de siguiente página
	patronvideos = '<span class="resultsLink3a">.*?</span>.*?<a href="(.*?)".*?>'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)

	if len(matches)>0:
		scrapedtitle = "Página siguiente"
		scrapedurl = matches[0]
		scrapedurl = scrapedurl.replace('amp;','')
		itemlist.append( Item( channel=CHANNELNAME , title=scrapedtitle , action="filestube" , url=scrapedurl , folder=True ) )
		
	return itemlist

	
def sub(item):

	itemlist = []
	if item.category!="asiateam":
		sub_file=download_subtitles(item.category)
		if sub_file!="":
			config.set_setting("subtitulo", "true")	
	else:
		mensaje = xbmcgui.Dialog()
		resultado = mensaje.ok('Subtítulo no disponible en Asia-Team', 'No se han encontrado subtítulos para este archivo' , 'Para asegurarse, pruebe a buscar en Xbmc Subtitles')	
	
	itemlist.append( Item(channel=CHANNELNAME, action="play", title=item.title , url=item.url , thumbnail=item.thumbnail , plot=item.plot , server=item.extra ,folder=False) )
	return itemlist
	
def download_subtitles (url):

    tmp_sub_dir= SUB_PATH #Carpeta temporal
    fullpath = os.path.join( config.get_data_path(), 'subtitulo.srt' )
    if os.path.exists(fullpath):   #Borro subtitulo anterior
        try:
          os.remove(fullpath)
        except IOError:
          xbmc.output("Error al eliminar el archivo subtitulo.srt "+fullpath)
          raise	
    for root, dirs, files in os.walk(tmp_sub_dir): #Borro archivos de la carpeta temporal
        for f in files:
            f = unicode(f,'utf8')
            os.unlink(os.path.join(root, f)) 
        for d in dirs:
            from shutil import rmtree						
            shutil.rmtree(os.path.join(root, d))
    #Mensaje de información
    mensaje = xbmcgui.DialogProgress()
    linea1 = 'Extrayendo archivo de subtítulos...'
    linea2 = 'Seleccione uno de la lista'
    linea3 = 'que aparecerá a continuación'
    mensaje.create(linea1 , linea2 , linea3)
    time.sleep(3)
    mensaje.close()	
    try:
        req = urllib2.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
        opener = urllib2.build_opener(SmartRedirectHandler())
        content = opener.open(req)
    except ImportError, inst:
        status,location = inst	
        response = urllib.urlopen(location)
        content =response.read()
    if content is not None:
        header = content[:4]
        if header == 'Rar!':
            local_tmp_file = os.path.join(tmp_sub_dir, "asia-team.rar")
            packed = True
        elif header == 'PK':
            local_tmp_file = os.path.join(tmp_sub_dir, "asia-team.zip")
            packed = True
        try:
            local_file_handle = open(local_tmp_file, "wb")
            local_file_handle.write(content)
            local_file_handle.close()
        except:
            logger.info("Fallo al guardar en '%s'" % (local_tmp_file))
        if packed:	
            files = os.listdir(tmp_sub_dir)
            init_filecount = len(files)
            filecount = init_filecount
            max_mtime = 0
            for file in files:
                if (string.split(file,'.')[-1] in ['srt','sub']):
                    mtime = os.stat(os.path.join(tmp_sub_dir, file)).st_mtime
                    if mtime > max_mtime:
                        max_mtime =  mtime
            init_max_mtime = max_mtime
            time.sleep(2)
            xbmc.executebuiltin("XBMC.Extract(" + local_tmp_file + "," + tmp_sub_dir +")")
            waittime  = 0
            while (filecount == init_filecount) and (waittime < 20) and (init_max_mtime == max_mtime):
                time.sleep(1) 
                files = os.listdir(tmp_sub_dir)
                filecount = len(files)
                for file in files:
                    if (string.split(file,'.')[-1] in ['srt','sub']):
                        mtime = os.stat(os.path.join(tmp_sub_dir, file)).st_mtime
                        if (mtime > max_mtime):
                            max_mtime =  mtime
                waittime  = waittime + 1
            if waittime == 20:
                logger.info("Error al extraer en '%s'" % (tmp_sub_dir))
            else:
                logger.info("Archivos extraídos en '%s'" % (tmp_sub_dir))			
                try:				
                    file = choice_one(files) #Nuevo dialogo para seleccionar subtitulo
                    subs_file = os.path.join(SUB_PATH,file)
                    if os.path.exists(subs_file):
                        from shutil import copy2
                        sub = copy2(subs_file, SUBTEMP_PATH)
                    return sub
                except:
                    return "" 			

		
def choice_one(files):
    opciones = []
    sub_list = []
    numero = 0
    
    for file in files:
        if (string.split(file, '.')[-1] in ['srt','sub','txt','idx','ssa']):		
            numero = numero + 1
            opciones.append("%02d) %s" % (numero , file))
            sub_list.append(file)
    choice = xbmcgui.Dialog()
    seleccion = choice.select("SELECCIONE UN SUBTÍTULO  -- Nº) SUBTITULO", opciones)
    if seleccion!= -1:
        return sub_list[seleccion]


class SmartRedirectHandler(urllib2.HTTPRedirectHandler):	
	def http_error_302(self, req, fp, code, msg, headers):
			if 'location' in headers:
				newurl = headers.getheaders('location')[0]
			elif 'uri' in headers:
				newurl = headers.getheaders('uri')[0]
			else:
				return
			newurl = newurl.replace(' ','%20')
			newurl = urlparse.urljoin(req.get_full_url(), newurl)
			raise ImportError(302,newurl)
			
			
def indice_series(item):
	logger.info("[asiateam.py] indice de series")

	itemlist = []
	itemlist.append( Item(channel=CHANNELNAME, action="indice_s", title="Series en Curso" , url="http://www.asia-team.net/index.php?page=Series1" , folder=True) )
	itemlist.append( Item(channel=CHANNELNAME, action="indice_s", title="Series Finalizadas" , url="http://www.asia-team.net/index.php?page=Series2" , folder=True) )		

	return itemlist	
	
def indice_peliculas(item):
    logger.info("[asiateam.py] indice de peliculas")
    
    itemlist = []
    itemlist.append( Item(channel=CHANNELNAME, action="indice_completo", title="Lista Completa" , url="http://www.asia-team.net/index.php?page=CineConSubTodos" , folder=True) )
    itemlist.append( Item(channel=CHANNELNAME, action="cat_p", title="Por Categorías" , folder=True) )	
			
    return itemlist	
	
def indice_completo(item):
	logger.info("[asiateam.py] lista de peliculas")
	
	itemlist =[]
	data = scrapertools.cachePage(item.url)
	patron = '<li><b><a href=(.*?) target=_blank>(.*?)</a></b></li>'
	matches = re.compile(patron,re.DOTALL).findall(data)
	
	for match in matches:
		scrapedtitle = match[1].split(' [')
		scrapedtitle = scrapedtitle[0]
		scrapedurl = urlparse.urljoin("http://www.asia-team.net/", match[0])
		itemlist.append( Item(channel=CHANNELNAME, action="videos_p", title= scrapedtitle , url= scrapedurl, folder=True) )
		
	return itemlist	
	
def indice_s(item):
	logger.info("[asiateam.py] lista de series")
	
	itemlist =[]
	data = scrapertools.cachePage(item.url)
	patron = '<li><b><a href=(.*?) target=_blank>(.*?)</a></b></li>'
	matches = re.compile(patron,re.DOTALL).findall(data)
	
	for match in matches:
		scrapedtitle = match[1].split(' [')
		scrapedtitle = scrapedtitle[0]
		scrapedurl = urlparse.urljoin("http://www.asia-team.net/", match[0])
		itemlist.append( Item(channel=CHANNELNAME, action="videos_s", title= scrapedtitle , url= scrapedurl, folder=True) )
		
	return itemlist	
	
def cat_p(item):
    logger.info("[asiateam.py] categorias peliculas")
    
    itemlist = []
    itemlist.append( Item(channel=CHANNELNAME, action="indice_p", title="Estrenos" , url="http://www.asia-team.net/index.php?page=CineConSub1" , folder=True) )
    itemlist.append( Item(channel=CHANNELNAME, action="indice_p", title="Acción / Sci-fi" , url="http://www.asia-team.net/index.php?page=CineConSub2",  folder=True) )
    itemlist.append( Item(channel=CHANNELNAME, action="indice_p" ,title="Artes Marciales / Samurai / Épicas",  url="http://www.asia-team.net/index.php?page=CineConSub3", folder=True) )
    itemlist.append( Item(channel=CHANNELNAME, action="indice_p", title="Aventuras / Comedia / Familiares" , url="http://www.asia-team.net/index.php?page=CineConSub4" , folder=True) )
    itemlist.append( Item(channel=CHANNELNAME, action="indice_p", title="Drama / Romance" , url="http://www.asia-team.net/index.php?page=CineConSub5",  folder=True) )
    itemlist.append( Item(channel=CHANNELNAME, action="indice_p" ,title="Documentales / Musicales",  url="http://www.asia-team.net/index.php?page=CineConSub6", folder=True) )
    itemlist.append( Item(channel=CHANNELNAME, action="indice_p", title="Terror / Horror / Gore" , url="http://www.asia-team.net/index.php?page=CineConSub7",  folder=True) )
    itemlist.append( Item(channel=CHANNELNAME, action="indice_p" ,title="Thiller / Crimen",  url="http://www.asia-team.net/index.php?page=CineConSub8", folder=True) )	
			
    return itemlist