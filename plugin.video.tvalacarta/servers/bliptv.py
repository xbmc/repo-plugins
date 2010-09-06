# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Conector para Youtube
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#------------------------------------------------------------
import urlparse,urllib2,urllib,re,httplib
import xbmc,xbmcplugin,xbmcgui
import xmllib
import xbmctools
import scrapertools
from xml.dom import minidom
from pprint import pprint
import config

_VALID_URL = r'^((?:http://)?(?:\w+\.)?youtube\.com/(?:(?:v/)|(?:(?:watch(?:\.php)?)?\?(?:.+&)?v=)))?([0-9A-Za-z_-]+)(?(1).+)?$'
AVAILABLE_FORMATS  = ['13','17','34','5','18','35','22','37']
AVAILABLE_FORMATS2 = {'13':'Baja','17':'Media (3gp)','34':'High (FLV)','5':'360p','18':'480p','35':'1227KBS (FLV)','22':'720p','37':'1080p'}
std_headers = {
	'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US; rv:1.9.1.2) Gecko/20090729 Firefox/3.5.2',
	'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.7',
	'Accept': 'text/xml,application/xml,application/xhtml+xml,text/html;q=0.9,text/plain;q=0.8,image/png,*/*;q=0.5',
	'Accept-Language': 'en-us,en;q=0.5',
}
 
 
def bliptv(id):
	opciones = []
	links = []
	url = "http://blip.tv/rss/flash/" + id 
	dom = minidom.parse(urllib.urlopen(url))
	#pprint(dom)
	medias = dom.getElementsByTagName('media:content')
	for x in medias:
		xbmc.output(x.getAttribute("type"))
		opciones.append(x.getAttribute("type"))
		links.append(x.getAttribute("url"))
		#xbmc.output(x.toxml())
		pprint("esto")
	pprint(medias)
	#opciones.append("Ver [prueba]")
	#opciones.append("Ver [cosa]")
	dia = xbmcgui.Dialog()
	seleccion = dia.select("Elige una opción", opciones)
	pprint(str(seleccion)+" es la seleccion")
	if seleccion!=-1:
		#<media:title>Redes 54: La pendiente resbaladiza de la maldad</media:title> first child contiene el texto del elemento
		pprint(dom.getElementsByTagName('media:title')[0].firstChild.nodeValue)
 
		listitem = xbmcgui.ListItem( dom.getElementsByTagName('media:title')[0].firstChild.nodeValue , iconImage="DefaultVideo.png", thumbnailImage="thumbnail")
		listitem.setInfo( "video", { "Title": dom.getElementsByTagName('media:title')[0].firstChild.nodeValue, "Plot" : dom.getElementsByTagName('blip:puredescription')[0].firstChild.nodeValue ,  "Genre" : "bliptv" } )
		xbmctools.launchplayer(links[seleccion], listitem)
 
 
def video(id):
	url="http://blip.tv/play/" + id
	request=urllib.urlopen(url)
	#pprint(bla.geturl())
	patronvideos  = '.*?file=(.+?)&'
	matches = re.compile(patronvideos).findall(request.geturl())
	scrapertools.printMatches(matches)
	patronvideos  = '.*%2F(.+)'
	matchvideo= re.compile(patronvideos).findall(matches[0])
	#pprint(matchvideo[0])
	bliptv(matchvideo[0])
