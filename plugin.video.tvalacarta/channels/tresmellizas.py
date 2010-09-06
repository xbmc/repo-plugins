# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# tvalacarta - XBMC Plugin
# Canal para "El cine de las tres mellizas"
# http://blog.tvalacarta.info/plugin-xbmc/tvalacarta/
#------------------------------------------------------------
import urlparse,urllib2,urllib,re
import os
import sys
import xbmc
import xbmcgui
import xbmcplugin
import xbmctools
import scrapertools
import binascii
import time

try:
	pluginhandle = int( sys.argv[ 1 ] )
except:
	pluginhandle = ""

xbmc.output("[tresmellizas.py] init")

DEBUG = True
CHANNELNAME = "El cine de las 3 mellizas"
CHANNELCODE = "tresmellizas"

def mainlist(params,url,category):
	xbmc.output("[tresmellizas.py] mainlist")

	# Añade al listado de XBMC
	xbmctools.addnewfolder( CHANNELCODE , "series" , CHANNELNAME , "Castellano" , "http://styleguide.thetriplets.com/bessones/cinema/taquilla.php?idioma=es" , "" , "" )
	xbmctools.addnewfolder( CHANNELCODE , "series" , CHANNELNAME , "Catalá"     , "http://styleguide.thetriplets.com/bessones/cinema/taquilla.php?idioma=ca" , "" , "" )
	xbmctools.addnewfolder( CHANNELCODE , "series" , CHANNELNAME , "English"    , "http://styleguide.thetriplets.com/bessones/cinema/taquilla.php?idioma=en" , "" , "" )

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def series(params,url,category):
	xbmc.output("[tresmellizas.py] series")

	# Descarga la página
	#data = scrapertools.cachePage(url)
	data = scrapertools.downloadpagewithcookies(url)
	#xbmc.output(data)

	# Extrae las entradas (series)
	patronvideos = '<li><a href="([^"]+)">[^<]+<img src="([^"]+)"/></a></li>'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	if DEBUG: scrapertools.printMatches(matches)
	
	for match in matches:
		#javascript:ObtenirDades('carregaCapitols.php?idSerie=2&idIdioma=3'
		scrapedurl = match[0]
		patronurl = "javascript\:ObtenirDades\(\'([^']+)\'"
		matchesurl = re.compile(patronurl,re.DOTALL).findall(scrapedurl)
		scrapedurl = urlparse.urljoin(url,matchesurl[0])

		scrapedthumbnail = urlparse.urljoin(url,match[1])
		trozos = match[1].split("/")
		scrapedtitle = trozos[ len(trozos)-1 ][:-4]
		scrapedplot = ""
		if (DEBUG): xbmc.output("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		# Añade al listado de XBMC
		xbmctools.addnewfolder( CHANNELCODE , "episodios" , CHANNELNAME , scrapedtitle , scrapedurl , scrapedthumbnail , scrapedplot )

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_LABEL )
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def episodios(params,url,category):
	xbmc.output("[tresmellizas.py] episodios")

	# Descarga la página
	data = scrapertools.cachePage(url)
	#xbmc.output(data)

	# Extrae las entradas (videos, el parámetro url es el id de la serie)
	'''
	<tr>
	<td width="106" valign="top"><img src="./img_captures/3bb_weare.jpg" alt="Som Les Tres Bebès" width="106" height="78" vspace="5" /></td>
	<td width="119" valign="top">
	<form id="form1" name="form1" method="post" action="cine.php">
	<table width="50" border="0" cellpadding="0" cellspacing="0">
	<tr>
	<td><label><select name="idiomesCombo" id="idiomesCombo"><option  value="3">English</option><option  value="6">Fran&ccedil;ais</option></select></label>
	<label></label></td>
	<td valign="middle"><input type="submit" name="enviar" id="enviar" value="&gt;"/></td>
	</tr>
	</table>
	<label></label>
	<input name="idCapitol" type="hidden" id="idCapitol"  value="4">
	<input name="idIdiomaInterficie" type="hidden" id="idIdiomaInterficie"  value="1">  						 
	</form>              <p>&nbsp;</p></td>
	</tr><tr>
	<td width="5" rowspan="2" valign="top">&nbsp;</td>
	<td colspan="2" valign="top" class="titolcapitol">Les Tres Bebès Flors i papallones</td>
	</tr>
	'''
	patronvideos  = '<tr>[^<]+'
	patronvideos += '<td[^>]+><img src="([^"]+)" alt="([^"]+)"[^>]+>.*?'
	patronvideos += '<select name="idiomesCombo" id="idiomesCombo">(.*?)</select>.*?'
	patronvideos += '<input name="idCapitol" type="hidden" id="idCapitol"  value="([^"]+)">[^<]+'
	patronvideos += '<input name="idIdiomaInterficie" type="hidden" id="idIdiomaInterficie"  value="([^"]+)">'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	if (DEBUG): scrapertools.printMatches(matches)

	for match in matches:
		scrapedtitle = match[1]
		scrapedurl = ""
		scrapedthumbnail = urlparse.urljoin(url,match[0])
		scrapedplot = ""
		if (DEBUG): xbmc.output("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")
		
		patronidiomas = '<option.*?value="([^"]+)">([^<]+)</option>'
		matchesidiomas = re.compile(patronidiomas,re.DOTALL).findall(match[2])
		for matchidioma in matchesidiomas:
			scrapedtitle = scrapertools.entityunescape(match[1] + " (" + matchidioma[1] + ")")
			scrapedurl = "idiomesCombo="+matchidioma[0]+"&enviar=%3E&idCapitol="+match[3]+"&idIdiomaInterficie="+match[4]
			xbmctools.addnewvideo( CHANNELCODE , "play" , category , "Directo" , scrapedtitle , scrapedurl , scrapedthumbnail , scrapedplot )

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_LABEL )
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def play(params,url,category):
	xbmc.output("[tresmellizas.py] play")

	title = unicode( xbmc.getInfoLabel( "ListItem.Title" ), "utf-8" )
	thumbnail = urllib.unquote_plus( params.get("thumbnail") )
	plot = unicode( xbmc.getInfoLabel( "ListItem.Plot" ), "utf-8" )
	server = "Directo"

	postdata = url
	data = postespecial("http://styleguide.thetriplets.com/bessones/cinema/cine.php",postdata)
	#xbmc.output("[tresmellizas.py] data="+data)
	
	patron = "'movie','([^']+)'"
	matches = re.compile(patron,re.DOTALL).findall(data)
	if (DEBUG): scrapertools.printMatches(matches)
	url="http://styleguide.thetriplets.com/bessones/cinema/"+matches[0]+".flv"
	'''
	http://styleguide.thetriplets.com/bessones/cinema/videos/bess/BESS_Sireneta_castellano.flv
	'movie','videos/bess/BESS_Sireneta_castellano'
	'''

	xbmctools.playvideo(CHANNELNAME,server,url,category,title,thumbnail,plot)

def postespecial(url,data):

	xbmc.output("[scrapertools.py] postespecial - " + url)
	#xbmc.output("[scrapertools.py] postespecial - data=" + data)
	inicio = time.clock()
	req = urllib2.Request(url,data)
	req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
	req.add_header('Accept', 'image/gif, image/x-xbitmap, image/jpeg, image/pjpeg, application/x-ms-application, application/vnd.ms-xpsdocument, application/xaml+xml, application/x-ms-xbap, application/x-shockwave-flash, application/vnd.ms-excel, application/vnd.ms-powerpoint, application/msword, */*')
	req.add_header('Referer', 'http://styleguide.thetriplets.com/bessones/cinema/index.php?idioma=es')
	req.add_header('Accept-Language', 'es')
	req.add_header('Content-Type', 'application/x-www-form-urlencoded')
	req.add_header('UA-CPU', 'x86')
	req.add_header('Accept-Encoding', 'gzip, deflate')
	req.add_header('Host', 'styleguide.thetriplets.com')
	req.add_header('Connection', 'Keep-Alive')
	req.add_header('Cache-Control', 'no-cache')
	req.add_header('Cookie', 'TimeCookie=1270294552; PHPSESSID=7bc5644b74b1c2198c0fe86fb2c8242d; __utma=234483420.1450462216.1270294218.1270294218.1270295348.2; __utmb=234483420; __utmz=234483420.1270294218.1.1.utmccn=(direct)|utmcsr=(direct)|utmcmd=(none); __utmc=234483420')

	try:
		response = urllib2.urlopen(req)
	except:
		req = urllib2.Request(url.replace(" ","%20"),data)
		req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
		req.add_header('Accept', 'image/gif, image/x-xbitmap, image/jpeg, image/pjpeg, application/x-ms-application, application/vnd.ms-xpsdocument, application/xaml+xml, application/x-ms-xbap, application/x-shockwave-flash, application/vnd.ms-excel, application/vnd.ms-powerpoint, application/msword, */*')
		req.add_header('Referer', 'http://styleguide.thetriplets.com/bessones/cinema/index.php?idioma=es')
		req.add_header('Accept-Language', 'es')
		req.add_header('Content-Type', 'application/x-www-form-urlencoded')
		req.add_header('UA-CPU', 'x86')
		req.add_header('Accept-Encoding', 'gzip, deflate')
		req.add_header('Host', 'styleguide.thetriplets.com')
		req.add_header('Connection', 'Keep-Alive')
		req.add_header('Cache-Control', 'no-cache')
		req.add_header('Cookie', 'TimeCookie=1270294552; PHPSESSID=7bc5644b74b1c2198c0fe86fb2c8242d; __utma=234483420.1450462216.1270294218.1270294218.1270295348.2; __utmb=234483420; __utmz=234483420.1270294218.1.1.utmccn=(direct)|utmcsr=(direct)|utmcmd=(none); __utmc=234483420')
		response = urllib2.urlopen(req)
	data=response.read()
	response.close()
	fin = time.clock()
	xbmc.output("Descargado en %d segundos " % (fin-inicio+1))
	return data