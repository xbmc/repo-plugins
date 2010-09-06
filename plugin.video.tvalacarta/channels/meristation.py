# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# tvalacarta - XBMC Plugin
# Canal para Meristation
# http://blog.tvalacarta.info/plugin-xbmc/tvalacarta/
#------------------------------------------------------------

import urlparse,urllib2,urllib,re
import os
import sys
import xbmc
import xbmcgui
import xbmcplugin
import scrapertools
import binascii
import xbmctools

try:
	pluginhandle = int( sys.argv[ 1 ] )
except:
	pluginhandle = ""

xbmc.output("[meristation.py] init")

DEBUG = True
CHANNELNAME = "Meristation"
CHANNELCODE = "meristation"

def mainlist(params,url,category):
	xbmc.output("[meristation.py] mainlist")

	# Añade al listado de XBMC
	xbmctools.addnewfolder( CHANNELCODE , "ultimosvideos"   , CHANNELNAME , "Últimos vídeos"     , "http://www.meristation.com/v3/GEN_videos.php" , "" , "" )
	xbmctools.addnewfolder( CHANNELCODE , "listaconsolas"   , CHANNELNAME , "Listado por consola", "http://www.meristation.com/v3/GEN_videos.php" , "" , "" )
	xbmctools.addnewfolder( CHANNELCODE , "listaletras"     , CHANNELNAME , "Listado alfabético" , "http://www.meristation.com/v3/GEN_videos.php" , "" , "" )
	xbmctools.addnewfolder( CHANNELCODE , "listageneros"    , CHANNELNAME , "Listado por género" , "http://www.meristation.com/v3/GEN_videos.php" , "" , "" )
	xbmctools.addnewfolder( CHANNELCODE , "search"          , CHANNELNAME , "Buscar"             , "" , "" , "" )

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )

	# Disable sorting...
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )

	# End of directory...
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def search(params,url,category):
	xbmc.output("[meristation.py] search")

	keyboard = xbmc.Keyboard('')
	keyboard.doModal()
	if (keyboard.isConfirmed()):
		tecleado = keyboard.getText()
		if len(tecleado)>0:
			#convert to HTML
			tecleado = tecleado.replace(" ", "+")
			searchUrl = "http://www.meristation.com/v3/resultado_busqueda.php?busca="+tecleado+"&tipo=10&palabras=1&pic=GEN"
			searchresults(params,searchUrl,category)

def searchresults(params,url,category):
	xbmc.output("[meristation.py] searchresults")

	# Descarga la página
	xbmc.output("[meristation.py] url="+url)
	data = scrapertools.downloadpagewithcookies(url)
	#xbmc.output(data)

	# Extrae las entradas (carpetas)
	'''
	onMouseOut="this.style.background='#ffffff'"> 
	<td class="tabla_borde_down" valign="top" width="250">
	<font face="Arial, Helvetica, sans-serif" size="2">
	<a href="des_videos.php?pic=WII&idj=cw45ba12c3a8156&COD=cw4b002ff355067" class="mslink9">
	<b>MeriStation TV Noticias 3x11</b></a></font>
	<font face="Arial, Helvetica, sans-serif" size="2"> 
	<a href="WII_portada.php" class="mslink8">
	<font color="#3366CC"><b>WII</b></font></a><span class="mstrucos"></span> 
	<br>
	<a href="empresa.php?pic=GEN&id=cw428d365050c81" class="mslink9">
	Nintendo</a></font>
	<font face="Arial, Helvetica, sans-serif" size="2"></font>
	<font face="Arial, Helvetica, sans-serif" size="2"> 
	</font>
	</td>
	<td class="tabla_borde_down" valign="top" width="100">
	<font face="Arial, Helvetica, sans-serif" size="2">
	<a href="GEN_.php" class="mslink9">
	Simulador</a></font>
	<font face="Arial, Helvetica, sans-serif" size="2"></font><br>
	<span class=fecha>
	16/11/09					                 </span>
	</td>
	<td class="tabla_borde_down" valign="top" width="200">
	<a href="shopping.php?idj=cw45ba12c3a8156" target="_blank">
	<img src="imgs/icono_busqueda_carrito1.gif" width="22" height="20" alt="Comprar" border="0"></a>
	<a href="listado_imagenes.php?pic=WII&idj=cw45ba12c3a8156">
	<img src="imgs/icono_busqueda_imagenes.gif" width="22" height="20" alt="Galería de Imágenes" border="0"></a>
	<a href="des_avances.php?pic=WII&pes=1&idj=cw45ba12c3a8156" >
	<img src="imgs/icono_busqueda_avances.gif" width="22" height="20" alt="Avance" border="0"></a>
	<a href="des_videos.php?pic=WII&pes=1&idj=cw45ba12c3a8156" >
	<img src="imgs/icono_busqueda_videos.gif" width="22" height="20" alt="Vídeos" border="0"></a>
	</td>
	<td class="tabla_borde_down" width="50" valign="top" align="center"> 
	<font face="Arial, Helvetica, sans-serif" size="2">
	<b>--</b></a></font>
	</td>
	'''
	
	patron  = '<tr onMouseOver="this.style.background =\'\'  "; this.style.cursor = \'hand\'"(.*?)</tr>'
	matches = re.compile(patron,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)

	for match in matches:

		patron2  = '<td class="tabla_borde_down" valign="top" width="250">[^<]+'
		patron2 += '<font face="Arial, Helvetica, sans-serif" size="2">[^<]+'
		patron2 += '<a href="([^"]+)" class="mslink9">[^<]+'
		patron2 += '<b>([^<]+)</b></a></font>[^<]+'
		patron2 += '<font face="Arial, Helvetica, sans-serif" size="2">[^<]+'
		patron2 += '<a href="[^"]+" class="mslink8">[^<]+'
		patron2 += '<font color="[^"]+"><b>([^<]+)</b></font></a><span class="mstrucos"></span>[^<]+'
		patron2 += '<br>[^<]+'
		patron2 += '<a href="empresa.php[^"]+" class="mslink9">([^<]+)</a></font>[^<]+'
		matches2 = re.compile(patron2,re.DOTALL).findall(match)

		for match2 in matches2:

			# Atributos del vídeo
			scrapedtitle = match2[1].strip()+" ["+match2[2].strip()+"] ["+match2[3].strip()+"]"
			scrapedurl = urlparse.urljoin(url,match2[0])
			scrapedthumbnail = ""
			scrapedplot = ""
			if (DEBUG): xbmc.output("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

			# Añade al listado de XBMC
			xbmctools.addnewvideo( CHANNELCODE , "play" , category , "Directo" , scrapedtitle , scrapedurl , scrapedthumbnail , scrapedplot )
	
	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )

	# Disable sorting...
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )

	# End of directory...
	xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

def letraresults(params,url,category):
	xbmc.output("[meristation.py] letraresults")

	# Descarga la página
	xbmc.output("[meristation.py] url="+url)
	data = scrapertools.downloadpagewithcookies(url)
	#xbmc.output(data)

	# Extrae las entradas (carpetas)
	'''
	<tr> 
	<td valign="top"><font face="Arial, Helvetica, sans-serif" size="2">
	<a href="des_videos.php?id=cw4b30babc22255&idj=cw4a697e97d6fe4&pic=GEN" class="mslink9"><b>Army Of Two: 40th Day</b></a></font>
	<font face="Arial, Helvetica, sans-serif" size="2"> 
	<a href="PS3_portada.php" class="mslink8">
	<font color="#999999"><b>PS3</b></font></a><span class="mstrucos"></span> 
	<br>
	<a href="empresa.php?pic=GEN&id=cw45772dad6567c" class="mslink9">
	EA Montreal</a></font>
	<font face="Arial, Helvetica, sans-serif" size="2"></font>
	<font face="Arial, Helvetica, sans-serif" size="2"> 
	</font></td>
	<td valign="top" width="100">
	<font face="Arial, Helvetica, sans-serif" size="2">
	<a href="GEN_accion.php" class="mslink9">
	Acción</a></font><font face="Arial, Helvetica, sans-serif" size="2"></font><br>
	<span class=fecha>20/12/09</span> </td>
	<td width="50" valign="top" align="center"> 
	<font face="Arial, Helvetica, sans-serif" size="2">
	<span class="mslink9"><b>1232</b></span></font></td>
	</tr>
	'''

	patron  = '<tr>[^<]+'
	patron += '<td valign="top"><font face="Arial, Helvetica, sans-serif" size="2">[^<]+'
	patron += '<a href="([^"]+)" class="mslink9"><b>([^<]+)</b></a></font>[^<]+'
	patron += '<font face="Arial, Helvetica, sans-serif" size="2">[^<]+'
	patron += '<a href="[^"]+" class="mslink8">[^<]+'
	patron += '<font color="[^"]+"><b>([^<]+)</b></font></a><span class="mstrucos"></span>[^<]+'
	patron += '<br>[^<]+'
	patron += '<a href="[^"]+" class="mslink9">([^<]+)</a></font>[^<]+'
	patron += '<font face="Arial, Helvetica, sans-serif" size="2"></font>[^<]+'
	patron += '<font face="Arial, Helvetica, sans-serif" size="2"> [^<]+'
	patron += '</font></td>[^<]+'
	patron += '<td valign="top" width="100">[^<]+'
	patron += '<font face="Arial, Helvetica, sans-serif" size="2">[^<]+'
	patron += '<a href="[^"]+" class="mslink9">([^<]+)</a></font><font face="Arial, Helvetica, sans-serif" size="2"></font><br>[^<]+'
	patron += '<span class=fecha>([^<]+)</span>'
	matches = re.compile(patron,re.DOTALL).findall(data)

	for match in matches:
		# Atributos del vídeo
		scrapedtitle = match[1].strip()+" ["+match[2].strip()+"] ["+match[3].strip()+"] ["+match[4].strip()+"]"
		scrapedurl = urlparse.urljoin(url,match[0])
		scrapedthumbnail = ""
		scrapedplot = ""
		if (DEBUG): xbmc.output("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		# Añade al listado de XBMC
		xbmctools.addnewvideo( CHANNELCODE , "play" , category , "Directo" , scrapedtitle , scrapedurl , scrapedthumbnail , scrapedplot )

	patron = '<a href="([^"]+)" class="mslink9">[^<]+<b>Siguiente</b></a></font>&nbsp;<img src="imgs/flecha_derecha.gif" width="4" height="6">'
	matches = re.compile(patron,re.DOTALL).findall(data)
	for match in matches:
		# Atributos del vídeo
		scrapedtitle = "Página siguiente"
		scrapedurl = urlparse.urljoin(url,match)
		scrapedthumbnail = ""
		scrapedplot = ""
		if (DEBUG): xbmc.output("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		# Añade al listado de XBMC
		xbmctools.addnewfolder( CHANNELCODE , "letraresults" , CHANNELNAME , scrapedtitle , scrapedurl , scrapedthumbnail , scrapedplot )

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )

	# Disable sorting...
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )

	# End of directory...
	xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

def ultimosvideos(params,url,category):
	xbmc.output("[meristation.py] ultimosvideos")

	# Descarga la página
	xbmc.output("[meristation.py] url="+url)
	data = scrapertools.downloadpagewithcookies(url)
	#xbmc.output(data)

	# Ultimos vídeos
	xbmc.output("[meristation.py] recientes")
	'''
	<td valign="top" align="center">
	<a href="des_videos.php?id=cw4b39e7ef51a6f&pic=PC&idj=cw49a26c7a07937" class="mslink9news"><b>Mass Effect 2 </b></a> <span class="mslink8">|</span> 
	<a href="PC_portada.php" class="mslink8"><b><font color="#990066">PC</font></b></a><span class="fecha"></span> 
	<br>
	<div class=fecha> 29 Dic 2009 | <font face="Arial, Helvetica, sans-serif" size="2" color="#000000">
	<span class="fecha"><a href="PC_rol.php" class="mslink8news">
	<font color="#666666">Rol</font></a></span></font> 
	</div>
	</td>
	'''
	patron  = '<td valign="top" align="center">[^<]+'
	patron += '<a href="([^"]+)" class="mslink9news"><b>([^<]+)</b></a> <span class="mslink8">.</span>[^<]+'
	patron += '<a href="[^"]+" class="mslink8"><b><font color="[^"]+">([^<]+)</font></b></a><span class="fecha"></span>[^<]+'
	patron += '<br>[^<]+'
	patron += '<div class=fecha>([^\|]+)\| <font face="Arial, Helvetica, sans-serif" size="2" color="#000000">[^<]+'
	patron += '<span class="fecha"><a href="[^"]+" class="mslink8news">[^<]+'
	patron += '<font color="[^"]+">([^<]+)</font>'
	matches = re.compile(patron,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)

	for match in matches:

		# Atributos del vídeo
		scrapedtitle = match[1]+" ("+match[2]+")"+" ("+match[3].strip()+")"+" ("+match[4]+")"
		scrapedurl = urlparse.urljoin(url,match[0])
		scrapedthumbnail = ""
		scrapedplot = ""
		if (DEBUG): xbmc.output("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		# Añade al listado de XBMC
		xbmctools.addnewvideo( CHANNELCODE , "play" , category , "Directo" , scrapedtitle , scrapedurl , scrapedthumbnail , scrapedplot )

	# Ultimos vídeos
	xbmc.output("[meristation.py] ultimos")
	'''
	<tr valign="middle" bgcolor="#F2F2F2"> 
	<td width="15" valgin="middle"><font face="Arial, Helvetica, sans-serif" size="2"><img src="imgs/trucos/top10_mantiene.gif" width="11" height="10"></font></td>
	<td width="55"  valign="middle"><span class=fecha>11/12/09</span></td>
	<td width="230"  valign="middle"><a href="des_videos.php?id=cw4b27546152101&pic=360&idj=cw4a1fa3d144f98" class="mslink9news"><b>BRINK, Ciudad Parte 1</b></a></td>
	<td width="55"  valign="middle"> 
	<div align="center"><font face="Arial, Helvetica, sans-serif" size="2" color="#000000"><span class="fecha"><a href="360_portada.php" class="mslink8"><font color="#99CC00"><b>360</b></font></a></span></font> </div>
	</td>
	<td width="75"  valign="middle"><font face="Arial, Helvetica, sans-serif" size="2" color="#000000"><a href="360_accion.php" class="mslink8news">Acción</a></font></td>
	</tr>
	'''
	patron  = '<tr valign="middle" bgcolor="[^"]+">[^<]+'
	patron += '<td width="15" valgin="middle"><font face="Arial, Helvetica, sans-serif" size="2"><img[^>]+></font></td>[^<]+'
	patron += '<td width="55"  valign="middle"><span class=fecha>([^<]+)</span></td>[^<]+'
	patron += '<td width="230"  valign="middle"><a href="([^"]+)" class="mslink9news"><b>([^<]+)</b></a></td>[^<]+'
	patron += '<td width="55"  valign="middle"> [^<]+'
	patron += '<div align="center"><font face="Arial, Helvetica, sans-serif" size="2" color="#000000"><span class="fecha"><a href="[^"]+" class="mslink8"><font color="[^"]+"><b>([^<]+)</b></font></a></span></font> </div>[^<]+'
	patron += '</td>[^<]+'
	patron += '<td width="75"  valign="middle"><font face="Arial, Helvetica, sans-serif" size="2" color="#000000"><a href="[^"]+" class="mslink8news">([^<]+)</a></font></td>[^<]+'
	matches = re.compile(patron,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)

	for match in matches:

		# Atributos del vídeo
		scrapedtitle = match[2]+" ("+match[0]+")"+" ("+match[3]+")"+" ("+match[4]+")"
		scrapedurl = urlparse.urljoin(url,match[1])
		scrapedthumbnail = ""
		scrapedplot = ""
		if (DEBUG): xbmc.output("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		# Añade al listado de XBMC
		xbmctools.addnewvideo( CHANNELCODE , "play" , category , "Directo" , scrapedtitle , scrapedurl , scrapedthumbnail , scrapedplot )
	
	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )

	# Disable sorting...
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )

	# End of directory...
	xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

def listaletras(params,url,category):
	xbmc.output("[meristation.py] listaalfabetica")
	
	# --------------------------------------------------------
	# Descarga la página
	# --------------------------------------------------------
	data = scrapertools.cachePage(url)
	#xbmc.output(data)

	# --------------------------------------------------------
	# Extrae las categorias (carpetas)
	# --------------------------------------------------------
	patron = '<a href="([^"]+)" class="mr_link11negro">([^<]+)</a>'
	matches = re.compile(patron,re.DOTALL).findall(data)
	if DEBUG: scrapertools.printMatches(matches)

	for match in matches:
		scrapedtitle = match[1]
		scrapedurl = urlparse.urljoin(url,match[0])
		scrapedthumbnail = ""
		scrapedplot = ""
		if (DEBUG): xbmc.output("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		# Añade al listado de XBMC
		#addvideo( scrapedtitle , scrapedurl , category )
		xbmctools.addnewfolder( CHANNELCODE , "letraresults" , CHANNELNAME , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )

	# Disable sorting...
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )

	# End of directory...
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def listageneros(params,url,category):
	xbmc.output("[meristation.py] listaporgenero")
	
	# --------------------------------------------------------
	# Descarga la página
	# --------------------------------------------------------
	data = scrapertools.cachePage(url)
	#xbmc.output(data)

	# --------------------------------------------------------
	# Extrae las categorias (carpetas)
	# --------------------------------------------------------
	patron = '<option  value="([^"]+)">([^<]+)</option>'
	matches = re.compile(patron,re.DOTALL).findall(data)
	if DEBUG: scrapertools.printMatches(matches)

	for match in matches:
		scrapedtitle = match[1].replace("&nbsp;","").strip()
		scrapedurl = urlparse.urljoin(url,match[0])
		scrapedthumbnail = ""
		scrapedplot = ""
		if (DEBUG): xbmc.output("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		# Añade al listado de XBMC
		#addvideo( scrapedtitle , scrapedurl , category )
		xbmctools.addnewfolder( CHANNELCODE , "letraresults" , CHANNELNAME , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )

	# Disable sorting...
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )

	# End of directory...
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def listaconsolas(params,url,category):
	xbmc.output("[meristation.py] listaporconsola")

	url = 'http://www.meristation.com/v3/GEN_videos.php'

	# --------------------------------------------------------
	# Descarga la página
	# --------------------------------------------------------
	data = scrapertools.cachePage(url)
	#xbmc.output(data)

	# --------------------------------------------------------
	# Extrae las categorias (carpetas)
	# --------------------------------------------------------
	patron = '<a href="([^"]+)" class="mslink8">[^<]+<font color="[^"]+"><b>([^<]+)</b></font></a><span class="mstrucos">'
	matches = re.compile(patron,re.DOTALL).findall(data)
	if DEBUG: scrapertools.printMatches(matches)

	for match in matches:
		scrapedtitle = match[1]
		scrapedurl = urlparse.urljoin(url,match[0])
		scrapedthumbnail = ""
		scrapedplot = ""
		if (DEBUG): xbmc.output("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		# Añade al listado de XBMC
		#addvideo( scrapedtitle , scrapedurl , category )
		xbmctools.addnewfolder( CHANNELCODE , "detalleconsola" , CHANNELNAME , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )

	# Disable sorting...
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )

	# End of directory...
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def detalleconsola(params,url,category):
	xbmc.output("[meristation.py] mainlist")

	title = urllib.unquote_plus( params.get("title") )

	# Añade al listado de XBMC
	xbmctools.addnewfolder( CHANNELCODE , "ultimosvideos" , CHANNELNAME , "Últimos vídeos "+title     , url , "" , "" )
	xbmctools.addnewfolder( CHANNELCODE , "listaletras"   , CHANNELNAME , "Listado alfabético "+title , url , "" , "" )
	xbmctools.addnewfolder( CHANNELCODE , "listageneros"  , CHANNELNAME , "Listado por género "+title , url , "" , "" )

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )

	# Disable sorting...
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )

	# End of directory...
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def play(params,url,category):
	xbmc.output("[meristation.py] play")

	title = unicode( xbmc.getInfoLabel( "ListItem.Title" ), "utf-8" )
	thumbnail = urllib.unquote_plus( params.get("thumbnail") )
	plot = unicode( xbmc.getInfoLabel( "ListItem.Plot" ), "utf-8" )
	server = "Directo"

	# URL de detalle
	# http://www.meristation.com/v3/des_videos.php?pic=WII&idj=cw49944ba621067&COD=cw4a8d04e8e355d
	# URL con el vídeo
	# http://www.meristation.com/v3/des_videos.php?id=cw4a8d04e8e355d&c=1&pic=WII&idj=cw49944ba621067
	# URL descargar vídeo
	# http://www.meristation.com/v3/des_videos.php?id=cw4a8d04e8e355d&c=1&pic=WII&idj=cw49944ba621067
	# XML
	# http://www.meristation.com/v3/video_player.php?vid=cw48fc48c0d0da9&res=alta&format=xml&version=1.5.002

	# Extrae el código del vídeo
	xbmc.output("[meristation.py] url="+url)
	patron  = 'http\://www.meristation.com/v3/des_videos.php.*?\&COD\=([^$]+)$'
	matches = re.compile(patron,re.DOTALL).findall(url)
	scrapertools.printMatches(matches)
	
	if len(matches)==0:
		patron  = 'id\=([^\&]+)\&'
		matches = re.compile(patron,re.DOTALL).findall(url)
		scrapertools.printMatches(matches)

	if len(matches)==0:
		patron  = 'http\://www.meristation.com/v3/des_videos.php.*?\&id\=([^$]+)$'
		matches = re.compile(patron,re.DOTALL).findall(url)
		scrapertools.printMatches(matches)
	
	if len(matches)==0:
		xbmctools.alertnodisponible()
		return

	# Descarga la página
	xbmc.output("[meristation.py] vid="+matches[0])
	url = 'http://www.meristation.com/v3/video_player.php?id='+matches[0]+'&format=xml'
	xbmc.output("[meristation.py] url="+url)
	data = scrapertools.downloadpagewithcookies(url)
	xbmc.output(data[:200])

	# Extrae las entradas (carpetas)
	patron  = '<location>([^<]+)</location>'
	matches = re.compile(patron,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)

	if len(matches)==0:
		return
	
	url = matches[0]
	url = url.replace(" ","%20")
	
	xbmctools.playvideo(CHANNELCODE,server,url,category,title,thumbnail,plot)
