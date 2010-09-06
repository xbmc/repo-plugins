# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# tvalacarta - XBMC Plugin
# Canal para TV Mallorca
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
import logger

try:
	pluginhandle = int( sys.argv[ 1 ] )
except:
	pluginhandle = ""

logger.info("[tvmallorca.py] init")

DEBUG = True
CHANNELNAME = "TV Mallorca"
CHANNELCODE = "tvmallorca"

def mainlist(params,url,category):
	logger.info("[tvmallorca.py] mainlist")

	# A�ade al listado de XBMC
	xbmctools.addnewfolder( CHANNELCODE , "programas" , CHANNELNAME , "Programas" , "" , "" , "" )
	xbmctools.addnewfolder( CHANNELCODE , "search"    , CHANNELNAME , "Buscar" , "" , "" , "" )

	# Cierra el directorio
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def search(params,url,category):
	logger.info("[tvmallorca.py] search")

	keyboard = xbmc.Keyboard('')
	keyboard.doModal()
	if (keyboard.isConfirmed()):
		tecleado = keyboard.getText()
		if len(tecleado)>0:
			#convert to HTML
			tecleado = tecleado.replace(" ", "+")
			searchUrl = "http://www.rtvmallorca.cat/inferior/cerca.php?id_sel=0&id=&par="+tecleado+"&da=&dm=&dd=&tipo=1"
			videolist(params,searchUrl,category)

def programas(params,url,category):
	logger.info("[tvmallorca.py] mainlist")

	# --------------------------------------------------------
	# Descarga la p�gina
	# --------------------------------------------------------
	url = 'http://www.rtvmallorca.cat/menu/cercador.php?tipo=tv'
	data = scrapertools.cachePage(url)
	logger.info(data)

	# --------------------------------------------------------
	# Extrae los programas
	# --------------------------------------------------------
	patron = '<SELECT NAME="prog">(.*?)</SELECT>'
	matches = re.compile(patron,re.DOTALL).findall(data)
	data = matches[0]
	
	patron = '<OPTION VALUE=([^>]+)>([^<]+)'
	matches = re.compile(patron,re.DOTALL).findall(data)
	if DEBUG: scrapertools.printMatches(matches)

	for match in matches:
		try:
			scrapedtitle = unicode( match[1], "utf-8" ).encode("iso-8859-1").strip()
		except:
			scrapedtitle = match[1].strip()
		scrapedurl = "http://www.rtvmallorca.cat/inferior/cerca.php?id_sel=0&id="+match[0]+"&par=&da=&dm=&dd=&tipo=1"
		scrapedthumbnail = ""
		scrapedplot = ""
		if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		# A�ade al listado de XBMC
		#addvideo( scrapedtitle , scrapedurl , category )
		xbmctools.addnewfolder( CHANNELCODE , "videolist" , CHANNELNAME , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def videolist(params,url,category):
	logger.info("[tvmallorca.py] videolist")

	'''
	http://www.rtvmallorca.cat/inferior/cerca.php?id_sel=0&id=131&par=&da=&dm=&dd=&tipo=1
	<div id="i_titol">
	<h2>Resultats de la cerca</h2>
	</div>
	﻿﻿	<div id="vistos">
	<div style="position: absolute; height:110;  width:974; left: 0; top: 0;" onmousemove="vist.onUpdateMouseCoordX(event);">
	<div id="i_fotos" onmouseOver="vist.onHorizMouseOver(34);" onmouseOut="vist.onHorizMouseOut();" >
	<div id="i_imgs" style="position:absolute; width:0px; left:0px;" >
	<table cellpadding="0px" cellspacing="0px"  border="0px" >
	<tr>
	<script>
	cargar('historic','historic/desc.php?id=15888');
	var w = document.getElementById('i_visor');
	visor('recursos/visor/veure_programa.php?id=15888');
	</script>

	<td width="146px" >
	<div style="width=146; cursor:pointer;" onclick="jQuery.noConflict();  jQuery.historyLoad('tv/carta/cerca/131----/15726'); return false;">
	<img width="146px" height="110px" title="" src="http://www.rtvmallorca.cat/recursos/img/frames/20100325_2214_memy_ria_i_oblit_d_una_guerra.ogg1.jpg" />
	<div class="titol_frame_alt">Memòria i Oblit ...<br><h8>2010-03-25</h8></div></div></td>

	<td width="146px" >
	<div style="width=146; cursor:pointer;" onclick="jQuery.noConflict();  jQuery.historyLoad('tv/carta/cerca/131----/15567'); return false;">
	<img width="146px" height="110px" title="l´exili: Adéu a les idees" src="http://www.rtvmallorca.cat/recursos/img/frames/20100318_2213_memy_ria_i_oblit_d_una_guerra.ogg1.jpg" />
	<div class="titol_frame_alt">Memòria i Oblit ...<br><h8>l´exili: Adéu a les ...</h8></div></div></td><td width="146px" ><div style="width=146; cursor:pointer;" onclick="jQuery.noConflict();  jQuery.historyLoad('tv/carta/cerca/131----/15407'); return false;"><img width="146px" height="110px" title="Menorca, el vent de la guerra (Part 2)" src="http://www.rtvmallorca.cat/recursos/img/frames/20100311_2213_memy_ria_i_oblit_d_una_guerra.ogg1.jpg" /><div class="titol_frame_alt">Memòria i Oblit ...<br><h8>Menorca, el vent de ...</h8></div></div></td><td width="146px" ><div style="width=146; cursor:pointer;" onclick="jQuery.noConflict();  jQuery.historyLoad('tv/carta/cerca/131----/15247'); return false;"><img width="146px" height="110px" title="Menorca, el vent de la guerra (Part 1)" src="http://www.rtvmallorca.cat/recursos/img/frames/20100304_2214_memy_ria_i_oblit_d_una_guerra.ogg1.jpg" /><div class="titol_frame_alt">Memòria i Oblit ...<br><h8>Menorca, el vent de ...</h8></div></div></td><td width="146px" ><div style="width=146; cursor:pointer;" onclick="jQuery.noConflict();  jQuery.historyLoad('tv/carta/cerca/131----/14921'); return false;"><img width="146px" height="110px" title="\"Artà i Son Servera, ferides de guerra”" src="http://www.rtvmallorca.cat/recursos/img/frames/20100218_2212_memy_ria_i_oblit_d_una_guerra.ogg1.jpg" /><div class="titol_frame_alt">Memòria i Oblit ...<br><h8>\"Artà i Son ...</h8></div></div></td><td width="146px" ><div style="width=146; cursor:pointer;" onclick="jQuery.noConflict();  jQuery.historyLoad('tv/carta/cerca/131----/14757'); return false;"><img width="146px" height="110px" title="Eivissa, ombres a l&#39;illa de la llum (part 2)" src="http://www.rtvmallorca.cat/recursos/img/frames/20100211_2229_memy_ria_i_oblit_d_una_guerra.ogg1.jpg" /><div class="titol_frame_alt">Memòria i Oblit ...<br><h8>Eivissa, ombres a ...</h8></div></div></td><td width="146px" ><div style="width=146; cursor:pointer;" onclick="jQuery.noConflict();  jQuery.historyLoad('tv/carta/cerca/131----/14585'); return false;"><img width="146px" height="110px" title="Eivissa, ombres a l&#39;illa de la llum (part 1)" src="http://www.rtvmallorca.cat/recursos/img/frames/20100204_2230_memy_ria_i_oblit_d_una_guerra.ogg1.jpg" /><div class="titol_frame_alt">Memòria i Oblit ...<br><h8>Eivissa, ombres a ...</h8></div></div></td><td width="146px" ><div style="width=146; cursor:pointer;" onclick="jQuery.noConflict();  jQuery.historyLoad('tv/carta/cerca/131----/14416'); return false;"><img width="146px" height="110px" title="Sa Pobla, el cost de la fidelitat" src="http://www.rtvmallorca.cat/recursos/img/frames/20100128_2229_memy_ria_i_oblit_d_una_guerra.ogg1.jpg" /><div class="titol_frame_alt">Memòria i Oblit ...<br><h8>Sa Pobla, el cost de ...</h8></div></div></td><td width="146px" ><div style="width=146; cursor:pointer;" onclick="jQuery.noConflict();  jQuery.historyLoad('tv/carta/cerca/131----/14294'); return false;"><img width="146px" height="110px" title="Campos, penediment i perdó" src="http://www.rtvmallorca.cat/recursos/img/frames/20100121_2215_memy_ria_i_oblit_d_una_guerra.ogg1.jpg" /><div class="titol_frame_alt">Memòria i Oblit ...<br><h8>Campos, penediment i ...</h8></div></div></td><td width="146px" ><div style="width=146; cursor:pointer;" onclick="jQuery.noConflict();  jQuery.historyLoad('tv/carta/cerca/131----/13818'); return false;"><img width="146px" height="110px" title="Els mestres de la república (cap. 25)" src="http://www.rtvmallorca.cat/recursos/img/frames/20091217_2215_memy_ria_i_oblit_d_una_guerra.ogg1.jpg" /><div class="titol_frame_alt">Memòria i Oblit ...<br><h8>Els mestres de la ...</h8></div></div></td><td width="146px" ><div style="width=146; cursor:pointer;" onclick="jQuery.noConflict();  jQuery.historyLoad('tv/carta/cerca/131----/13717'); return false;"><img width="146px" height="110px" title="El preu de la guerra" src="http://www.rtvmallorca.cat/recursos/img/frames/20091210_2214_memy_ria_i_oblit_d_una_guerra.ogg1.jpg" /><div class="titol_frame_alt">Memòria i Oblit ...<br><h8>El preu de la guerra</h8></div></div></td><td width="146px" ><div style="width=146; cursor:pointer;" onclick="jQuery.noConflict();  jQuery.historyLoad('tv/carta/cerca/131----/13607'); return false;"><img width="146px" height="110px" title="Vilafranca, una història amagada (cap. 23)" src="http://www.rtvmallorca.cat/recursos/img/frames/20091203_2214_memy_ria_i_oblit_d_una_guerra.ogg1.jpg" /><div class="titol_frame_alt">Memòria i Oblit ...<br><h8>Vilafranca, una ...</h8></div></div></td><td width="146px" ><div style="width=146; cursor:pointer;" onclick="jQuery.noConflict();  jQuery.historyLoad('tv/carta/cerca/131----/13488'); return false;"><img width="146px" height="110px" title="Els soldats de Franco (cap. 22)" src="http://www.rtvmallorca.cat/recursos/img/frames/20091126_2217_memy_ria_i_oblit_d_una_guerra.ogg1.jpg" /><div class="titol_frame_alt">Memòria i Oblit ...<br><h8>Els soldats de Franco ...</h8></div></div></td><td width="146px" ><div style="width=146; cursor:pointer;" onclick="jQuery.noConflict();  jQuery.historyLoad('tv/carta/cerca/131----/13344'); return false;"><img width="146px" height="110px" title="Capdepera, brins de memòria (cap. 21)" src="http://www.rtvmallorca.cat/recursos/img/frames/20091119_2215_memy_ria_i_oblit_d_una_guerra.ogg1.jpg" /><div class="titol_frame_alt">Memòria i Oblit ...<br><h8>Capdepera, brins de ...</h8></div></div></td><td width="146px" ><div style="width=146; cursor:pointer;" onclick="jQuery.noConflict();  jQuery.historyLoad('tv/carta/cerca/131----/13242'); return false;"><img width="146px" height="110px" title="" src="http://www.rtvmallorca.cat/recursos/img/frames/20091112_2213_memy_ria_i_oblit_d_una_guerra___llucmajor__el_desig_da_una_nova_vida___cap._20_.ogg1.jpg" /><div class="titol_frame_alt">Memòria i Oblit ...<br><h8>2009-11-12</h8></div></div></td><td width="146px" ><div style="width=146; cursor:pointer;" onclick="jQuery.noConflict();  jQuery.historyLoad('tv/carta/cerca/131----/13137'); return false;"><img width="146px" height="110px" title="" src="http://www.rtvmallorca.cat/recursos/img/frames/20091105_2213_memy_ria_i_oblit_d_una_guerra___cementeris_sota_la_lluna___cap._19_.ogg1.jpg" /><div class="titol_frame_alt">Memòria i Oblit ...<br><h8>2009-11-05</h8></div></div></td><td width="146px" ><div style="width=146; cursor:pointer;" onclick="jQuery.noConflict();  jQuery.historyLoad('tv/carta/cerca/131----/13032'); return false;"><img width="146px" height="110px" title="" src="http://www.rtvmallorca.cat/recursos/img/frames/20091029_2214_memy_ria_i_oblit_d_una_guerra___esporles__la_cay_a_del_home___cap._18_.ogg1.jpg" /><div class="titol_frame_alt">Memòria i Oblit ...<br><h8>2009-10-29</h8></div></div></td><td width="146px" ><div style="width=146; cursor:pointer;" onclick="jQuery.noConflict();  jQuery.historyLoad('tv/carta/cerca/131----/12924'); return false;"><img width="146px" height="110px" title="" src="http://www.rtvmallorca.cat/recursos/img/frames/20091022_2213_memy_ria_i_oblit_d_una_guerra___montuy_ri__ses_escoles_del_progry_s___cap._17_.ogg1.jpg" /><div class="titol_frame_alt">Memòria i Oblit ...<br><h8>2009-10-22</h8></div></div></td><td width="146px" ><div style="width=146; cursor:pointer;" onclick="jQuery.noConflict();  jQuery.historyLoad('tv/carta/cerca/131----/12813'); return false;"><img width="146px" height="110px" title="" src="http://www.rtvmallorca.cat/recursos/img/frames/20091015_2213_memy_ria_i_oblit_d_una_guerra____cucabrera__trets_al_parady_s___cap._16_.ogg1.jpg" /><div class="titol_frame_alt">Memòria i Oblit ...<br><h8>2009-10-15</h8></div></div></td><td width="146px" ><div style="width=146; cursor:pointer;" onclick="jQuery.noConflict();  jQuery.historyLoad('tv/carta/cerca/131----/12917'); return false;"><img width="146px" height="110px" title="" src="http://www.rtvmallorca.cat/recursos/img/frames/20091008_2213_memy_ria_i_oblit_d_una_guerra__alaro_cap._15_.ogg1.jpg" /><div class="titol_frame_alt">Mem&ograve;ria i Oblit ...<br><h8>2009-10-08</h8></div></div></td><td width="146px" ><div style="width=146; cursor:pointer;" onclick="jQuery.noConflict();  jQuery.historyLoad('tv/carta/cerca/131----/12604'); return false;"><img width="146px" height="110px" title="" src="http://www.rtvmallorca.cat/recursos/img/frames/20091001_2213_memy_ria_i_oblit_d_una_guerra___can_sales__presy__de_dones___cap._14_.ogg1.jpg" /><div class="titol_frame_alt">Memòria i Oblit ...<br><h8>2009-10-01</h8></div></div></td><td width="146px" ><div style="width=146; cursor:pointer;" onclick="jQuery.noConflict();  jQuery.historyLoad('tv/carta/cerca/131----/7996'); return false;"><img width="146px" height="110px" title="" src="http://www.rtvmallorca.cat/recursos/img/frames/20081211_2313_memy_ria_i_oblit_d_couna_guerra.__cap_13_..ogg1.jpg" /><div class="titol_frame_alt">Memòria i oblit ...<br><h8>2008-12-11</h8></div></div></td><td width="146px" ><div style="width=146; cursor:pointer;" onclick="jQuery.noConflict();  jQuery.historyLoad('tv/carta/cerca/131----/7882'); return false;"><img width="146px" height="110px" title="" src="http://www.rtvmallorca.cat/recursos/img/frames/20081204_2239_memy_ria_i_oblit_d_couna_guerra.__cap_12_..ogg1.jpg" /><div class="titol_frame_alt">Memòria i oblit ...<br><h8>2008-12-04</h8></div></div></td><td width="146px" ><div style="width=146; cursor:pointer;" onclick="jQuery.noConflict();  jQuery.historyLoad('tv/carta/cerca/131----/7766'); return false;"><img width="146px" height="110px" title="" src="http://www.rtvmallorca.cat/recursos/img/frames/20081127_2239_memy_ria_i_oblit_d_couna_guerra.__cap_11_..ogg1.jpg" /><div class="titol_frame_alt">Memòria i oblit ...<br><h8>2008-11-27</h8></div></div></td><td width="146px" ><div style="width=146; cursor:pointer;" onclick="jQuery.noConflict();  jQuery.historyLoad('tv/carta/cerca/131----/7650'); return false;"><img width="146px" height="110px" title="" src="http://www.rtvmallorca.cat/recursos/img/frames/20081120_2239_memy_ria_i_oblit_d_couna_guerra.__cap_10_..ogg1.jpg" /><div class="titol_frame_alt">Memòria i oblit ...<br><h8>2008-11-20</h8></div></div></td><td width="146px" ><div style="width=146; cursor:pointer;" onclick="jQuery.noConflict();  jQuery.historyLoad('tv/carta/cerca/131----/7532'); return false;"><img width="146px" height="110px" title="" src="http://www.rtvmallorca.cat/recursos/img/frames/20081113_2254_memy_ria_i_oblit_d_couna_guerra.__cap_09_..ogg1.jpg" /><div class="titol_frame_alt">Memòria i oblit ...<br><h8>2008-11-13</h8></div></div></td><td width="146px" ><div style="width=146; cursor:pointer;" onclick="jQuery.noConflict();  jQuery.historyLoad('tv/carta/cerca/131----/7418'); return false;"><img width="146px" height="110px" title="" src="http://www.rtvmallorca.cat/recursos/img/frames/20081106_2243_memy_ria_i_oblit_d_couna_guerra.__cap_08_..ogg1.jpg" /><div class="titol_frame_alt">Memòria i oblit ...<br><h8>2008-11-06</h8></div></div></td><td width="146px" ><div style="width=146; cursor:pointer;" onclick="jQuery.noConflict();  jQuery.historyLoad('tv/carta/cerca/131----/7306'); return false;"><img width="146px" height="110px" title="" src="http://www.rtvmallorca.cat/recursos/img/frames/20081030_2243_memy_ria_i_oblit_d_couna_guerra.__cap_07_..ogg1.jpg" /><div class="titol_frame_alt">Memòria i oblit ...<br><h8>2008-10-30</h8></div></div></td><td width="146px" ><div style="width=146; cursor:pointer;" onclick="jQuery.noConflict();  jQuery.historyLoad('tv/carta/cerca/131----/7193'); return false;"><img width="146px" height="110px" title="" src="http://www.rtvmallorca.cat/recursos/img/frames/20081023_2244_memy_ria_i_oblit_d_couna_guerra.__cap_06_..ogg1.jpg" /><div class="titol_frame_alt">Memòria i oblit ...<br><h8>2008-10-23</h8></div></div></td><td width="146px" ><div style="width=146; cursor:pointer;" onclick="jQuery.noConflict();  jQuery.historyLoad('tv/carta/cerca/131----/7070'); return false;"><img width="146px" height="110px" title="" src="http://www.rtvmallorca.cat/recursos/img/frames/20081016_2239_memyoria_i_oblit_duna_guerra_cap_05.ogg1.jpg" /><div class="titol_frame_alt">Memòria i oblit ...<br><h8>2008-10-16</h8></div></div></td><td width="146px" ><div style="width=146; cursor:pointer;" onclick="jQuery.noConflict();  jQuery.historyLoad('tv/carta/cerca/131----/6963'); return false;"><img width="146px" height="110px" title="" src="http://www.rtvmallorca.cat/recursos/img/frames/20081009_2239_memy_ria_i_oblit_d_couna_guerra.__cap_04_..ogg1.jpg" /><div class="titol_frame_alt">Memòria i oblit ...<br><h8>2008-10-09</h8></div></div></td><td width="146px" ><div style="width=146; cursor:pointer;" onclick="jQuery.noConflict();  jQuery.historyLoad('tv/carta/cerca/131----/6857'); return false;"><img width="146px" height="110px" title="" src="http://www.rtvmallorca.cat/recursos/img/frames/20081002_2239_memy_ria_i_oblit_d_couna_guerra.__cap_03_..ogg1.jpg" /><div class="titol_frame_alt">Memòria i oblit ...<br><h8>2008-10-02</h8></div></div></td><td width="146px" ><div style="width=146; cursor:pointer;" onclick="jQuery.noConflict();  jQuery.historyLoad('tv/carta/cerca/131----/6750'); return false;"><img width="146px" height="110px" title="" src="http://www.rtvmallorca.cat/recursos/img/frames/20080925_2239_memy_ria_i_oblit_d_couna_guerra.__cap_02_..ogg1.jpg" /><div class="titol_frame_alt">Memòria i oblit ...<br><h8>2008-09-25</h8></div></div></td><td width="146px" ><div style="width=146; cursor:pointer;" onclick="jQuery.noConflict();  jQuery.historyLoad('tv/carta/cerca/131----/6645'); return false;"><img width="146px" height="110px" title="" src="http://www.rtvmallorca.cat/recursos/img/frames/20080918_2239_memy_ria_i_oblit_d_couna_guerra.__cap_01_..ogg1.jpg" /><div class="titol_frame_alt">Memòria i oblit ...<br><h8>2008-09-18</h8></div></div></td>						</tr>

	</table>
	</div>
	</div>
	</div>
	</div>
	'''

	# --------------------------------------------------------
	# Descarga la p�gina
	# --------------------------------------------------------
	data = scrapertools.cachePage(url)
	logger.info(data)

	# --------------------------------------------------------
	# Extrae los cap�tulos
	# --------------------------------------------------------
	patron  = '<td width="146px[^>]+>'
	patron += '<div.*?onclick="jQuery.noConflict\(\)\;  jQuery.historyLoad\(\'([^\']+)\'[^>]+>'
	patron += '<img.*?src="([^"]+)"[^>]+>'
	patron += '<div class="titol_frame_alt">([^<]+)<br><h8>([^<]+)</h8>'
	matches = re.compile(patron,re.DOTALL).findall(data)
	if DEBUG: scrapertools.printMatches(matches)

	for match in matches:
		scrapedtitle = match[2] + " (" + match[3] + ")"
		scrapedurl = match[0]
		scrapedthumbnail = match[1]
		scrapedplot = ""
		if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		# A�ade al listado de XBMC
		xbmctools.addnewfolder( CHANNELCODE , "detail" , CHANNELNAME , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def detail(params,url,category):
	logger.info("[tvmallorca.py] detail")

	title = urllib.unquote_plus( params.get("title") )
	thumbnail = urllib.unquote_plus( params.get("thumbnail") )
	plot = urllib.unquote_plus( params.get("plot") )

	# --------------------------------------------------------
	# Obtiene el id
	# --------------------------------------------------------
	trozos = url.split("/")
	codigo = trozos[len(trozos)-1]
	
	# --------------------------------------------------------
	# Obtiene el argumento
	# --------------------------------------------------------
	url = "http://www.rtvmallorca.cat/recursos/flash/desc/"+codigo+".txt"
	data = scrapertools.cachePage(url)
	#logger.info(data)
	scrapedplot = data[6:]
	
	# --------------------------------------------------------
	# Obtiene la URL
	# --------------------------------------------------------
	#http://www.rtvmallorca.cat/recursos/visor/veure_programa.php?id=15567
	url = "http://www.rtvmallorca.cat/recursos/visor/veure_programa.php?id="+codigo
	data = scrapertools.cachePage(url)
	patron = "v\=([^\&]+)\&amp\;"
	matches = re.compile(patron,re.DOTALL).findall(data)
	if DEBUG: scrapertools.printMatches(matches)
	scrapedurl = matches[0][:-4]
	
	scrapedtitle = title
	scrapedthumbnail = thumbnail

	# A�ade al listado de XBMC
	xbmctools.addnewvideo( CHANNELCODE , "play" , CHANNELNAME , "" , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

	
def play(params,url,category):
	logger.info("[tvmallorca.py] play")

	title = urllib.unquote_plus( params.get("title") )
	thumbnail = urllib.unquote_plus( params.get("thumbnail") )
	plot = urllib.unquote_plus( params.get("plot") )
	server = "Directo"
	
	logger.info("url="+url)

	xbmctools.playvideo(CHANNELNAME,server,url,category,title,thumbnail,plot)
