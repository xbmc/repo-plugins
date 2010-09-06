# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# tvalacarta - XBMC Plugin
# Canal para antena 3
# http://blog.tvalacarta.info/plugin-xbmc/tvalacarta/
#------------------------------------------------------------
import urlparse,re
import logger
import scrapertools
from item import Item

logger.info("[a3.py] init")

DEBUG = True
CHANNELNAME = "a3"

def isGeneric():
	return True

def mainlist(item):
	logger.info("[a3parser.py] mainlist")

	itemlist = []
	itemlist.append( Item(channel=CHANNELNAME, title="Los más vistos" , action="losmasvistos" , url="http://www.antena3.com/videos/", folder=True) )
	itemlist.append( Item(channel=CHANNELNAME, title="Últimos vídeos" , action="ultimosvideos", url="http://www.antena3.com/videos/", folder=True) )
	itemlist.append( Item(channel=CHANNELNAME, title="Última semana"  , action="ultimasemana" , url="http://www.antena3.com/videos/ultima-semana.html", folder=True) )
	itemlist.append( Item(channel=CHANNELNAME, title="Series"         , action="series"       , url="http://www.antena3.com/videos/series.html", folder=True) )
	itemlist.append( Item(channel=CHANNELNAME, title="Noticias"       , action="noticias"     , url="http://www.antena3.com/videos/noticias.html", folder=True) )
	itemlist.append( Item(channel=CHANNELNAME, title="Programas"      , action="programas"    , url="http://www.antena3.com/videos/programas.html", folder=True) )
	itemlist.append( Item(channel=CHANNELNAME, title="TV Movies"      , action="tvmovies"     , url="http://www.antena3.com/videos/tv-movies.html", folder=True) )

	return itemlist

def losmasvistos(item):
	logger.info("[a3parser.py] losmasvistos")
	return videosportada(item,"masVistos")

def ultimosvideos(item):
	logger.info("[a3parser.py] ultimosvideos")
	return videosportada(item,"ultimosVideos")

def videosportada(item,id):
	logger.info("[a3parser.py] videosportada")
	
	print item.tostring()
	
	# Descarga la página
	data = scrapertools.cachePage(item.url)
	#logger.info(data)

	# Extrae las entradas
	patron = '<div id="'+id+'"(.*?)</div><!-- .visor -->'
	matches = re.compile(patron,re.DOTALL).findall(data)
	#if DEBUG: scrapertools.printMatches(matches)
	data = matches[0]
	
	'''
	<div>
	<a title="Vídeos de El Internado - Capítulo 8 - Temporada 7" href="/videos/el-internado/temporada-7/capitulo-8.html">
	<img title="Vídeos de El Internado - Capítulo 8 - Temporada 7" 
	src="/clipping/2010/07/21/00048/10.jpg"
	alt="El último deseo"
	href="/videos/el-internado/temporada-7/capitulo-8.html"
	/>
	<strong>El Internado</strong>
	<p>El último deseo</p></a>  
	</div>
	'''

	patron  = '<div>[^<]+'
	patron += '<a title="([^"]+)" href="([^"]+)">[^<]+'
	patron += '<img.*?src="([^"]+)"[^<]+'
	patron += '<strong>([^<]+)</strong>[^<]+'
	patron += '<p>([^<]+)</p>'
	matches = re.compile(patron,re.DOTALL).findall(data)
	#if DEBUG: scrapertools.printMatches(matches)

	itemlist = []
	for match in matches:
		scrapedtitle = match[3]+" - "+match[4]+" ("+match[0]+")"
		scrapedurl = urlparse.urljoin(item.url,match[1])
		scrapedthumbnail = urlparse.urljoin(item.url,match[2])
		scrapedplot = ""
		if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		# Añade al listado
		itemlist.append( Item(channel=CHANNELNAME, title=scrapedtitle , action="detalle" , url=scrapedurl, thumbnail=scrapedthumbnail, plot=scrapedplot , folder=True) )

	return itemlist

def ultimasemana(item):
	logger.info("[a3parser.py] ultimasemana")
	
	print item.tostring()
	
	# Descarga la página
	data = scrapertools.cachePage(item.url)
	#logger.info(data)

	# Extrae las entradas (series)
	'''
	<div>
	<em class="play_video"><img title="ver video" src="/static/modosalon/images/button_play_s1.png" alt="ver video"/></em>
	<a title="Vídeos de Noticias 1 - 19 de Agosto de 2.010" href="/videos/noticias/noticias-1-19-agosto.html">
	<img title="Vídeos de Noticias 1 - 19 de Agosto de 2.010"  
	src="/clipping/2010/05/21/00055/10.jpg"
	alt="19 de agosto"
	href="/videos/noticias/noticias-1-19-agosto.html"
	/>
	</a>
	<a title="Vídeos de Noticias 1 - 19 de Agosto de 2.010" href="/videos/noticias/noticias-1-19-agosto.html">
	<strong>Noticias 1</strong>
	<p>19 de agosto</p></a>  
	</div>
	'''
	patron  = '<div>[^<]+'
	patron += '<em[^>]+><img[^>]+></em>[^<]+'
	patron += '<a title="([^"]+)" href="([^"]+)">[^<]+'
	patron += '<img title="[^"]+"[^<]+'  
	patron += 'src="([^"]+)"[^>]+>[^<]+'
	patron += '</a>[^<]+'
	patron += '<a[^>]+>[^<]+'
	patron += '<strong>([^<]+)</strong>[^<]+'
	patron += '<p>([^<]+)</p>'
	matches = re.compile(patron,re.DOTALL).findall(data)
	#if DEBUG: scrapertools.printMatches(matches)

	itemlist = []
	for match in matches:
		scrapedtitle = match[3]+" - "+match[4]+" ("+match[0]+")"
		scrapedurl = urlparse.urljoin(item.url,match[1])
		scrapedthumbnail = urlparse.urljoin(item.url,match[2])
		scrapedplot = ""
		if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		# Añade al listado
		itemlist.append( Item(channel=CHANNELNAME, title=scrapedtitle , action="detalle" , url=scrapedurl, thumbnail=scrapedthumbnail, plot=scrapedplot , folder=True) )

	return itemlist

def series(item):
	logger.info("[a3parser.py] series")
	
	print item.tostring()
	
	# Descarga la página
	data = scrapertools.cachePage(item.url)
	#logger.info(data)

	# Extrae las entradas (series)
	'''
	<div>
	<a title="Vídeos de Share - Capítulos Completos" href="/videos/share.html">
	<img title="Vídeos de Share - Capítulos Completos" href="/videos/share.html"
	src="/clipping/2010/08/06/00246/10.jpg"
	alt="Share"
	/>
	<a title="Vídeos de Share - Capítulos Completos" href="/videos/share.html"><p>Share</p></a>                    
	</a>
	</div>
	</li>
	'''
	patron  = '<div>[^<]+'
	patron += '<a\W+title="[^"]+" href="([^"]+)"[^<]+'
	patron += '<img.*?src="([^"]+)"[^<]+'
	patron += '<a[^<]+<p>([^<]+)</p>'
	matches = re.compile(patron,re.DOTALL).findall(data)
	#if DEBUG: scrapertools.printMatches(matches)

	itemlist = []
	for match in matches:
		scrapedtitle = match[2]
		scrapedurl = urlparse.urljoin(item.url,match[0])
		scrapedthumbnail = urlparse.urljoin(item.url,match[1])
		scrapedplot = ""
		if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		# Añade al listado
		itemlist.append( Item(channel=CHANNELNAME, title=scrapedtitle , action="capitulos" , url=scrapedurl, thumbnail=scrapedthumbnail, plot=scrapedplot , folder=True) )

	return itemlist

def capitulos(item):
	logger.info("[a3parser.py] capitulos")
	
	print item.tostring()
	
	# Descarga la página
	data = scrapertools.cachePage(item.url)
	#logger.info(data)

	# Capitulos
	'''
	<div>
	<a  title="Vídeos de El Internado - Capítulo 8 - Temporada 7"
	href="/videos/el-internado/temporada-7/capitulo-8.html">
	<img title="Vídeos de El Internado - Capítulo 8 - Temporada 7" 
	src="/clipping/2010/07/21/00048/10.jpg"
	alt="EL INTERNADO T7 C8"
	href="/videos/el-internado/temporada-7/capitulo-8.html"
	/>
	<em class="play_video"><img title="ver video" src="/static/modosalon/images/button_play_s1.png" alt="ver video"/></em>
	<strong>EL INTERNADO T7 C8</strong>
	<p>El último deseo</p>
	</a>	
	</div>
	'''
	patron  = '<div>[^<]+'
	patron += '<a.*?href="([^"]+)"[^<]+'
	patron += '<img.*?src="([^"]+)".*?'
	patron += '<strong>([^<]+)</strong>[^<]+'
	patron += '<p>([^<]+)</p>'
	matches = re.compile(patron,re.DOTALL).findall(data)
	#if DEBUG: scrapertools.printMatches(matches)

	itemlist = []
	for match in matches:
		scrapedtitle = match[2]+" - "+match[3]
		scrapedurl = urlparse.urljoin(item.url,match[0])
		scrapedthumbnail = urlparse.urljoin(item.url,match[1])
		scrapedplot = ""
		if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		# Añade al listado
		itemlist.append( Item(channel=CHANNELNAME, title=scrapedtitle , action="detalle" , url=scrapedurl, thumbnail=scrapedthumbnail, plot=scrapedplot , folder=True) )

	# Otras temporadas
	patron = '<dd class="paginador">(.*?)</dd>'
	matches = re.compile(patron,re.DOTALL).findall(data)
	#if DEBUG: scrapertools.printMatches(matches)
	subdata = matches[0]
	
	'''
	<ul>
	<li  class="active" >
	<a 	title="Vídeos de El Internado - Temporada 7 - Capítulos Completos"
	href="/videos/el-internado.html" >7
	</a>
	</li>
	'''
	patron  = '<li[^<]+'
	patron += '<a.*?href="([^"]+)" >([^<]+)</a>'
	matches = re.compile(patron,re.DOTALL).findall(subdata)
	
	#if DEBUG: scrapertools.printMatches(matches)
	for match in matches:
		scrapedtitle = "Temporada "+match[1].strip()
		scrapedurl = urlparse.urljoin(item.url,match[0])
		scrapedthumbnail = item.thumbnail
		scrapedplot = ""
		if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		# Añade al listado
		itemlist.append( Item(channel=CHANNELNAME, title=scrapedtitle , action="capitulos" , url=scrapedurl, thumbnail=scrapedthumbnail, plot=scrapedplot , folder=True) )

	return itemlist

def noticias(item):
	logger.info("[a3parser.py] noticias")
	
	print item.tostring()
	
	# Descarga la página
	data = scrapertools.cachePage(item.url)
	#logger.info(data)

	# Extrae las entradas (series)
	'''
	<div>
	<a title="Vídeos de Noticias Fin de Semana - 22 de Agosto de 2.010" 
	href="/videos/noticias/noticias-fin-semana-22082010.html">
	<img title="Vídeos de Noticias Fin de Semana - 22 de -1 de 2.010" 
	src="/clipping/2010/06/01/00105/10.jpg"
	alt="Noticias fin de semana 22-08-2010 "
	href="/videos/noticias/fin-de-semana-completo/2010-agosto-22.html"
	/>
	<em class="play_video"><img title="ver video" src="/static/modosalon/images/button_play_s1.png" alt="ver video"/></em>
	<a 
	title="Vídeos de Noticias Fin de Semana - 22 de Agosto de 2.010"
	href="/videos/noticias/noticias-fin-semana-22082010.html"
	>
	<strong>Noticias Fin de Semana</strong>
	<p>22 de agosto 15.00h</p>
	</a>                    
	'''
	patron  = '<div>[^<]+'
	patron += '<a.*?href="([^"]+)">[^<]+'
	patron += '<img.*?src="([^"]+)"[^>]+>.*?'
	patron += '<strong>([^<]+)</strong>[^<]+'
	patron += '<p>([^<]+)</p>'
	matches = re.compile(patron,re.DOTALL).findall(data)
	#if DEBUG: scrapertools.printMatches(matches)

	itemlist = []
	for match in matches:
		scrapedtitle = match[2]+" - "+match[3]
		scrapedurl = urlparse.urljoin(item.url,match[0])
		scrapedthumbnail = urlparse.urljoin(item.url,match[1])
		scrapedplot = ""
		if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		# Añade al listado
		itemlist.append( Item(channel=CHANNELNAME, title=scrapedtitle , action="detalle" , url=scrapedurl, thumbnail=scrapedthumbnail, plot=scrapedplot , folder=True) )

	return itemlist
	
def programas(item):
	logger.info("[a3parser.py] programas")
	return series(item)
	
def tvmovies(item):
	logger.info("[a3parser.py] tvmovies")
	return series(item)

def detalle(item):
	logger.info("[a3parser.py] detalle")
	print item.tostring()

	# Descarga la página de detalle
	data = scrapertools.cachePage(item.url)

	# Extrae el xml
	patron = 'so.addVariable\("xml","([^"]+)"'
	matches = re.compile(patron,re.DOTALL).findall(data)
	if DEBUG: scrapertools.printMatches(matches)
	scrapedurl = urlparse.urljoin(item.url,matches[0])
	logger.info("url="+scrapedurl)
	
	# Descarga la página del xml
	data = scrapertools.cachePage(scrapedurl)

	# Extrae las entradas del video y el thumbnail
	patron = '<urlHttpVideo><\!\[CDATA\[([^\]]+)\]\]>'
	matches = re.compile(patron,re.DOTALL).findall(data)
	baseurlvideo = matches[0]
	logger.info("baseurlvideo="+baseurlvideo)
	
	patron = '<urlImg><\!\[CDATA\[([^\]]+)\]\]>'
	matches = re.compile(patron,re.DOTALL).findall(data)
	baseurlthumb = matches[0]
	logger.info("baseurlthumb="+baseurlthumb)
	
	patron  = '<archivoMultimediaMaxi>[^<]+'
	patron += '<archivo><\!\[CDATA\[([^\]]+)\]\]>'
	matches = re.compile(patron,re.DOTALL).findall(data)
	scrapedthumbnail = urlparse.urljoin(baseurlthumb,matches[0])
	logger.info("scrapedthumbnail="+scrapedthumbnail)
	
	patron  = '<archivoMultimedia>[^<]+'
	patron += '<archivo><\!\[CDATA\[([^\]]+)\]\]>'
	matches = re.compile(patron,re.DOTALL).findall(data)

	itemlist = []
	i = 1
	for match in matches:
		scrapedurl = urlparse.urljoin(baseurlvideo,match)
		logger.info("scrapedurl="+scrapedurl)
		itemlist.append( Item(channel=CHANNELNAME, title="(%d) %s" % (i,item.title) , action="play" , url=scrapedurl, thumbnail=scrapedthumbnail , plot=item.plot , server = "directo" , folder=False) )
		i=i+1

	return itemlist

def test():
	itemsmainlist = mainlist(None)
	for item in itemsmainlist: print item.tostring()

	# Listado principal
	itemsmasvistos = losmasvistos(itemsmainlist[0])
	
	# Listados de secciones
	itemsultimosvideos = ultimosvideos(itemsmainlist[1])
	itemsultimasemana = ultimasemana(itemsmainlist[2])
	itemsseries = series(itemsmainlist[3])
	itemsnoticias = noticias(itemsmainlist[4])
	itemsprogramas = programas(itemsmainlist[5])
	itemstvmovies = tvmovies(itemsmainlist[6])
	
	# Capítulos
	itemscapitulos = capitulos(itemsseries[1])
	
	# Detalle
	itemsdetalle = detalle(itemsmasvistos[0])

if __name__ == "__main__":
	test()