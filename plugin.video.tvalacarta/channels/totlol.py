# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# tvalacarta - XBMC Plugin
# Canal para totlol
# http://blog.tvalacarta.info/plugin-xbmc/tvalacarta/
#------------------------------------------------------------
import urlparse,re
import logger
import scrapertools
from item import Item

logger.info("[totlol.py] init")

DEBUG = True
CHANNELNAME = "totlol"

def isGeneric():
	return True

def mainlist(item):
	logger.info("[totlol.py] mainlist")

	# Descarga la página
	data = scrapertools.cachePage("http://www.totlol.com/videos")
	#logger.info(data)

	patron = '<select class="subnavbarform" name="vdolanguage"[^>]+>(.*?)</select>'
	matches = re.compile(patron,re.DOTALL).findall(data)
	#if DEBUG: scrapertools.printMatches(matches)
	data = matches[0]

	patron = "<option.*?value=([^>]+)>(.*?)</option>"
	matches = re.compile(patron,re.DOTALL).findall(data)
	
	'''
	<select class="subnavbarform" name="vdolanguage" onchange="location.href = this[this.selectedIndex].value;">
	<option selected="selected" value="http://www.totlol.com/videos?&amp;flang=all&amp;orderby=df&amp;u=&amp;c=&amp;search_id=&amp;catid=0">- All Languages -</option>
	<option  value='http://www.totlol.com/videos?&amp;flang=zz&amp;u=&amp;c=&amp;search_id='>- No Language -</option><option  value='http://www.totlol.com/videos?&amp;flang=ar&amp;u=&amp;c=&amp;search_id='>Arabic</option><option  value='http://www.totlol.com/videos?&amp;flang=nl&amp;u=&amp;c=&amp;search_id='>Dutch</option><option  value='http://www.totlol.com/videos?&amp;flang=en&amp;u=&amp;c=&amp;search_id='>English</option><option  value='http://www.totlol.com/videos?&amp;flang=fr&amp;u=&amp;c=&amp;search_id='>French</option><option  value='http://www.totlol.com/videos?&amp;flang=de&amp;u=&amp;c=&amp;search_id='>German</option><option  value='http://www.totlol.com/videos?&amp;flang=el&amp;u=&amp;c=&amp;search_id='>Greek</option><option  value='http://www.totlol.com/videos?&amp;flang=he&amp;u=&amp;c=&amp;search_id='>Hebrew</option><option  value='http://www.totlol.com/videos?&amp;flang=it&amp;u=&amp;c=&amp;search_id='>Italian</option><option  value='http://www.totlol.com/videos?&amp;flang=ja&amp;u=&amp;c=&amp;search_id='>Japanese</option><option  value='http://www.totlol.com/videos?&amp;flang=pt&amp;u=&amp;c=&amp;search_id='>Portuguese</option><option  value='http://www.totlol.com/videos?&amp;flang=es&amp;u=&amp;c=&amp;search_id='>Spanish</option>
	</select>
	'''

	itemlist = []
	for match in matches:
		scrapedtitle = match[1]
		scrapedurl = scrapertools.entityunescape(match[0][1:-1])
		scrapedthumbnail = ""
		scrapedplot = ""
		#if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		# Añade al listado
		itemlist.append( Item(channel=CHANNELNAME, title=scrapedtitle , action="categoria" , url=scrapedurl, thumbnail=scrapedthumbnail, plot=scrapedplot , folder=True) )

	return itemlist

def categorias(item):
	logger.info("[totlol.py] categorias")

	# Descarga la página
	data = scrapertools.cachePage(item.url)
	#logger.info(data)

	patron = '<select class="subnavbarform" name="vdoorderby"[^>]+>(.*?)</select>'
	matches = re.compile(patron,re.DOTALL).findall(data)
	#if DEBUG: scrapertools.printMatches(matches)
	data = matches[0]

	patron = "<option.*?value=([^>]+)>(.*?)</option>"
	matches = re.compile(patron,re.DOTALL).findall(data)
	
	'''
	<select class="subnavbarform" name="vdoorderby" onchange="location.href = this[this.selectedIndex].value;">
	<option value="http://www.totlol.com/videos?&amp;orderby=df&amp;u=&amp;c=&amp;search_id=&amp;catid=0">- All Categories -</option>
	<option  value='http://www.totlol.com/videos?&amp;catid=1&amp;u=&amp;c=&amp;search_id='>Animals</option><option  value='http://www.totlol.com/videos?&amp;catid=6&amp;u=&amp;c=&amp;search_id='>Animated</option><option  value='http://www.totlol.com/videos?&amp;catid=16&amp;u=&amp;c=&amp;search_id='>Classic</option><option  value='http://www.totlol.com/videos?&amp;catid=17&amp;u=&amp;c=&amp;search_id='>Dance</option><option  value='http://www.totlol.com/videos?&amp;catid=13&amp;u=&amp;c=&amp;search_id='>Educational</option><option  value='http://www.totlol.com/videos?&amp;catid=24&amp;u=&amp;c=&amp;search_id='>Filmed or Live action</option><option  value='http://www.totlol.com/videos?&amp;catid=8&amp;u=&amp;c=&amp;search_id='>Food and Drinks</option><option  value='http://www.totlol.com/videos?&amp;catid=2&amp;u=&amp;c=&amp;search_id='>Funny</option><option  value='http://www.totlol.com/videos?&amp;catid=9&amp;u=&amp;c=&amp;search_id='>Games and Sports</option><option  value='http://www.totlol.com/videos?&amp;catid=7&amp;u=&amp;c=&amp;search_id='>Holidays and Special Events</option><option  value='http://www.totlol.com/videos?&amp;catid=26&amp;u=&amp;c=&amp;search_id='>Movie</option><option  value='http://www.totlol.com/videos?&amp;catid=23&amp;u=&amp;c=&amp;search_id='>Music</option><option  value='http://www.totlol.com/videos?&amp;catid=14&amp;u=&amp;c=&amp;search_id='>Places</option><option  value='http://www.totlol.com/videos?&amp;catid=19&amp;u=&amp;c=&amp;search_id='>Puppets Etc.</option><option  value='http://www.totlol.com/videos?&amp;catid=3&amp;u=&amp;c=&amp;search_id='>Songs</option><option  value='http://www.totlol.com/videos?&amp;catid=15&amp;u=&amp;c=&amp;search_id='>Stories</option><option  value='http://www.totlol.com/videos?&amp;catid=4&amp;u=&amp;c=&amp;search_id='>Transportation</option><option  value='http://www.totlol.com/videos?&amp;catid=27&amp;u=&amp;c=&amp;search_id='>TV show</option><option  value='http://www.totlol.com/videos?&amp;catid=20&amp;u=&amp;c=&amp;search_id='>Videos of Babies or Infants</option><option  value='http://www.totlol.com/videos?&amp;catid=22&amp;u=&amp;c=&amp;search_id='>Videos of Kindergarten or School Kids</option><option  value='http://www.totlol.com/videos?&amp;catid=21&amp;u=&amp;c=&amp;search_id='>Videos of Toddlers or Preschoolers</option><option  value='http://www.totlol.com/videos?&amp;catid=25&amp;u=&amp;c=&amp;search_id='>Videos of Tweens or Teens</option>
	</select>
	'''

	itemlist = []
	import config
	itemlist.append( Item(channel=CHANNELNAME, title=config.getLocalizedString(30103) , action="search" , folder=True) )

	for match in matches:
		scrapedtitle = match[1]
		scrapedurl = scrapertools.entityunescape(match[0][1:-1])
		scrapedthumbnail = ""
		scrapedplot = ""
		#if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		# Añade al listado
		itemlist.append( Item(channel=CHANNELNAME, title=scrapedtitle , action="listado" , url=scrapedurl, thumbnail=scrapedthumbnail, plot=scrapedplot , folder=True) )

	return itemlist

def listado(item):
	logger.info("[totlol.py] listado")

	# Descarga la página
	data = scrapertools.cachePage(item.url)
	#logger.info(data)

	patron = '<select class="subnavbarform" name="vdoorderby"[^>]+>(.*?)</select>'
	matches = re.compile(patron,re.DOTALL).findall(data)
	#if DEBUG: scrapertools.printMatches(matches)
	data = matches[0]

	patron = "<option.*?value=([^>]+)>(.*?)</option>"
	matches = re.compile(patron,re.DOTALL).findall(data)
	
	'''
	<select class="subnavbarform" name="vdoorderby" onchange="location.href = this[this.selectedIndex].value;">
	<option value="http://www.totlol.com/videos?&amp;orderby=df&amp;u=&amp;c=&amp;search_id=&amp;catid=0">- All Categories -</option>
	<option  value='http://www.totlol.com/videos?&amp;catid=1&amp;u=&amp;c=&amp;search_id='>Animals</option><option  value='http://www.totlol.com/videos?&amp;catid=6&amp;u=&amp;c=&amp;search_id='>Animated</option><option  value='http://www.totlol.com/videos?&amp;catid=16&amp;u=&amp;c=&amp;search_id='>Classic</option><option  value='http://www.totlol.com/videos?&amp;catid=17&amp;u=&amp;c=&amp;search_id='>Dance</option><option  value='http://www.totlol.com/videos?&amp;catid=13&amp;u=&amp;c=&amp;search_id='>Educational</option><option  value='http://www.totlol.com/videos?&amp;catid=24&amp;u=&amp;c=&amp;search_id='>Filmed or Live action</option><option  value='http://www.totlol.com/videos?&amp;catid=8&amp;u=&amp;c=&amp;search_id='>Food and Drinks</option><option  value='http://www.totlol.com/videos?&amp;catid=2&amp;u=&amp;c=&amp;search_id='>Funny</option><option  value='http://www.totlol.com/videos?&amp;catid=9&amp;u=&amp;c=&amp;search_id='>Games and Sports</option><option  value='http://www.totlol.com/videos?&amp;catid=7&amp;u=&amp;c=&amp;search_id='>Holidays and Special Events</option><option  value='http://www.totlol.com/videos?&amp;catid=26&amp;u=&amp;c=&amp;search_id='>Movie</option><option  value='http://www.totlol.com/videos?&amp;catid=23&amp;u=&amp;c=&amp;search_id='>Music</option><option  value='http://www.totlol.com/videos?&amp;catid=14&amp;u=&amp;c=&amp;search_id='>Places</option><option  value='http://www.totlol.com/videos?&amp;catid=19&amp;u=&amp;c=&amp;search_id='>Puppets Etc.</option><option  value='http://www.totlol.com/videos?&amp;catid=3&amp;u=&amp;c=&amp;search_id='>Songs</option><option  value='http://www.totlol.com/videos?&amp;catid=15&amp;u=&amp;c=&amp;search_id='>Stories</option><option  value='http://www.totlol.com/videos?&amp;catid=4&amp;u=&amp;c=&amp;search_id='>Transportation</option><option  value='http://www.totlol.com/videos?&amp;catid=27&amp;u=&amp;c=&amp;search_id='>TV show</option><option  value='http://www.totlol.com/videos?&amp;catid=20&amp;u=&amp;c=&amp;search_id='>Videos of Babies or Infants</option><option  value='http://www.totlol.com/videos?&amp;catid=22&amp;u=&amp;c=&amp;search_id='>Videos of Kindergarten or School Kids</option><option  value='http://www.totlol.com/videos?&amp;catid=21&amp;u=&amp;c=&amp;search_id='>Videos of Toddlers or Preschoolers</option><option  value='http://www.totlol.com/videos?&amp;catid=25&amp;u=&amp;c=&amp;search_id='>Videos of Tweens or Teens</option>
	</select>
	'''

	itemlist = []
	import config
	itemlist.append( Item(channel=CHANNELNAME, title=config.getLocalizedString(30103) , action="search" , folder=True) )

	for match in matches:
		scrapedtitle = match[1]
		scrapedurl = scrapertools.entityunescape(match[0][1:-1])
		scrapedthumbnail = ""
		scrapedplot = ""
		#if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		# Añade al listado
		itemlist.append( Item(channel=CHANNELNAME, title=scrapedtitle , action="listado" , url=scrapedurl, thumbnail=scrapedthumbnail, plot=scrapedplot , folder=True) )

	return itemlist

def detalle(item):
	logger.info("[totlol.py] detalle")
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
	itemsidiomas = mainlist(None)
	for item in itemsidiomas: print item.tostring()
	
	# Spanish
	itemscategorias = categorias(itemsidiomas[0])
	for item in itemscategorias: print item.tostring()
	'''
	
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
	'''

if __name__ == "__main__":
	test()