# -*- coding: utf-8 -*-
import urllib, re, time, os, urllib2, sys, simplejson
import xbmc, xbmcgui, xbmcplugin, xbmcaddon


__plugin__  = "prensayrevistas"
__author__  = "Xextil"
__url__     = "http://code.google.com/p/xbmc-xextil/"
__date__    = "19-06-2011"
__version__ = "0.2"
__settings__ = xbmcaddon.Addon(id='plugin.image.prensayrevistas')
__language__ = __settings__.getLocalizedString
__cwd__      = __settings__.getAddonInfo('path')
__profile__  = __settings__.getAddonInfo('profile')

CACHE_PATH = xbmc.translatePath(os.path.join(__profile__,'cache'))
SAVE_PATH = xbmc.translatePath(__settings__.getSetting('save_path'))
IMAGE_PATH = xbmc.translatePath(os.path.join(__cwd__,'resources/images'))
FAVORITE_PATH = xbmc.translatePath(os.path.join(__profile__,'favorites'))

if not os.path.exists(CACHE_PATH): os.makedirs(CACHE_PATH)
if not os.path.exists(SAVE_PATH): os.makedirs(SAVE_PATH)
if not os.path.exists(FAVORITE_PATH): os.makedirs(FAVORITE_PATH)

BASE_RESOURCE_PATH = xbmc.translatePath( os.path.join( __cwd__, 'lib' ) )
sys.path.append (BASE_RESOURCE_PATH)

import download, marcador



def CATEGORIES():
	addDir(__language__(30013),'youkioske',1,os.path.join(IMAGE_PATH,'youkioske.png'))
	addDir(__language__(30091),'submanga',6,os.path.join(IMAGE_PATH,'submanga.png'))
	addDir(__language__(30130),'search_youkioske',2,os.path.join(IMAGE_PATH,'youkioske.png'))
	addDir(__language__(30131),'issuu',7,os.path.join(IMAGE_PATH,'issuu.png'))
	addDir(__language__(30132),'scribd',8,os.path.join(IMAGE_PATH,'scribd.png'))
	addDir(__language__(30134),'google',49,os.path.join(IMAGE_PATH,'google.png'))
	addDir(__language__(30092),'marcadores',9,os.path.join(IMAGE_PATH,'favorites.png'))
	addDir(__language__(30015),'descargas',3,os.path.join(IMAGE_PATH,'downloads.png'))
	addDir(__language__(30016),'configuracion',4,os.path.join(IMAGE_PATH,'settings.png'))


def addDir(name,url,mode,iconimage,count=0,input=''):
	u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+name+"&count="+str(count)+"&input="+input
	ok=True
	liz=xbmcgui.ListItem(name, 'test',iconImage="DefaultFolder.png", thumbnailImage=iconimage)
	liz.setInfo( type="image", infoLabels={"Title": name} )
	return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True,totalItems=0)

def addItem(name,url,mode,iconimage,category='',path=''):
	u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
	ok=True
	liz=xbmcgui.ListItem(name, 'test',iconImage="DefaultFolder.png", thumbnailImage=iconimage)
	liz.setInfo( type="image", infoLabels={"Title": name} )
	savename = name

	menu = []
	if re.search('youkioske',url) is not None: #Menu contextual para descargar pdf
		menu.append((__language__(30097),'XBMC.RunScript('+__cwd__+'/default.py,save_you,'+url+','+savename+')'))
	elif re.search('submanga',url) is not None:
		savename = savename.replace(' -- ','_').replace('.','')
		menu.append ((__language__(30097),'XBMC.RunScript('+__cwd__+'/default.py,save_sub,'+url+','+savename+')'))
	elif re.search('scribd',url) is not None:
		menu.append((__language__(30097),'XBMC.RunScript('+__cwd__+'/default.py,save_scribd,'+url+','+savename+')'))
	elif re.search('google',url) is not None:
		savename = savename.split(' - ')
		savename = savename[0]
		menu.append((__language__(30097),'XBMC.RunScript('+__cwd__+'/default.py,save_google,'+url+','+savename+')'))
	else:
		savename = savename.split(' -- ')
		savename = savename[0]
		menu.append((__language__(30097),'XBMC.RunScript('+__cwd__+'/default.py,save_issuu,'+url+','+savename+')'))

	if category == 'marcadores': #Menu para añadir o eliminar marcadores
		menu.append((__language__(30096),'XBMC.RunScript('+__cwd__+'/default.py,delete_fav,'+path+')'))
	else:
		if iconimage!='':
			savename = savename.split(' -- ')
			savename = savename[0]
			menu.append((__language__(30095),'XBMC.RunScript('+__cwd__+'/default.py,save_fav,'+savename+','+url+','+str(mode)+','+iconimage+')'))
		else:
			menu.append((__language__(30095),'XBMC.RunScript('+__cwd__+'/default.py,save_fav,'+name+','+url+','+str(mode)+','+'vacio'+')'))

	liz.addContextMenuItems(menu)
	return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True,totalItems=0)

def addLink(name,url,iconimage):
	ok=True
	liz=xbmcgui.ListItem(name, iconImage="DefaultImage.png", thumbnailImage=iconimage)
	liz.setInfo( type="image", infoLabels={ "Title": name } )
	temp = str(time.time())
	savename = name
	savename = savename+"_"+temp+".jpg"
	contextMenu = [(__language__(30098),'XBMC.RunScript('+__cwd__+'/default.py,save_image,'+url+','+savename+')')]
	liz.addContextMenuItems(contextMenu)
	return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=liz,isFolder=False,totalItems=0)


def youkioske():
	#Idioma de youkioske
	language = __settings__.getSetting('language')
	Switch={'0':'all', '1':'es', '2':'en', '3':'fr', '4':'it', '5':'pt', '6':'de', '7':'ot'}
	lang = Switch[language]
	addDir(__language__(30017),lang,10,'')
	addDir(__language__(30018),lang,11,'')
	addDir(__language__(30019),lang,12,'')
	addDir(__language__(30020),lang,13,'')
	addDir(__language__(30021),lang,14,'')
	addDir(__language__(30022),lang,15,'')
	addDir(__language__(30023),lang,16,'')
	addDir(__language__(30024),lang,17,'')

def press(lang):
	addDir(__language__(30025),'http://www.youkioske.com/prensa-espanola/lang/'+lang,20,'')
	addDir(__language__(30026),'http://www.youkioske.com/prensa-deportiva/lang/'+lang,20,'')
	addDir(__language__(30027),'http://www.youkioske.com/prensa-europea/lang/'+lang,20,'')
	addDir(__language__(30028),'http://www.youkioske.com/prensa-americana/lang/'+lang,20,'')

def magazines(lang):
	addDir(__language__(30029),'http://www.youkioske.com/revistas-femeninas/lang/'+lang,20,'')
	addDir(__language__(30030),'http://www.youkioske.com/revistas-masculinas/lang/'+lang,20,'')
	addDir(__language__(30031),'http://www.youkioske.com/actualidad-economia/lang/'+lang,20,'')
	addDir(__language__(30032),'http://www.youkioske.com/decoracion/lang/'+lang,20,'')
	addDir(__language__(30033),'http://www.youkioske.com/ciencia/lang/'+lang,20,'')
	addDir(__language__(30034),'http://www.youkioske.com/cine/lang/'+lang,20,'')
	addDir(__language__(30035),'http://www.youkioske.com/fotografia/lang/'+lang,20,'')
	addDir(__language__(30036),'http://www.youkioske.com/historia-cultura/lang/'+lang,20,'')
	addDir(__language__(30037),'http://www.youkioske.com/musica/lang/'+lang,20,'')
	addDir(__language__(30038),'http://www.youkioske.com/salud/lang/'+lang,20,'')
	addDir(__language__(30039),'http://www.youkioske.com/viajes-guias/lang/'+lang,20,'')
	addDir(__language__(30040),'http://www.youkioske.com/otros-magazines/lang/'+lang,20,'')

def tecnology(lang):
	addDir(__language__(30041),'http://www.youkioske.com/informatica/lang/'+lang,20,'')
	addDir(__language__(30042),'http://www.youkioske.com/videojuegos/lang/'+lang,20,'')
	addDir(__language__(30043),'http://www.youkioske.com/telefonia/lang/'+lang,20,'')
	addDir(__language__(30044),'http://www.youkioske.com/otros-tecnologia/lang/'+lang,20,'')

def motor(lang):
	addDir(__language__(30045),'http://www.youkioske.com/automovil/lang/'+lang,20,'')
	addDir(__language__(30046),'http://www.youkioske.com/motos/lang/'+lang,20,'')
	addDir(__language__(30047),'http://www.youkioske.com/nautica/lang/'+lang,20,'')
	addDir(__language__(30048),'http://www.youkioske.com/aviacion/lang/'+lang,20,'')
	addDir(__language__(30049),'http://www.youkioske.com/otros-motor/lang/'+lang,20,'')

def sports(lang):
	addDir(__language__(30050),'http://www.youkioske.com/futbol/lang/'+lang,20,'')
	addDir(__language__(30051),'http://www.youkioske.com/fitness-entrenamiento/lang/'+lang,20,'')
	addDir(__language__(30052),'http://www.youkioske.com/acuaticos/lang/'+lang,20,'')
	addDir(__language__(30053),'http://www.youkioske.com/caza-pesca/lang/'+lang,20,'')
	addDir(__language__(30054),'http://www.youkioske.com/skate-ciclismo/lang/'+lang,20,'')
	addDir(__language__(30055),'http://www.youkioske.com/golf/lang/'+lang,20,'')
	addDir(__language__(30056),'http://www.youkioske.com/nieve/lang/'+lang,20,'')
	addDir(__language__(30057),'http://www.youkioske.com/otros-deportes/lang/'+lang,20,'')

def books(lang):
	addDir(__language__(30058),'http://www.youkioske.com/autores/lang/'+lang,20,'')
	addDir(__language__(30059),'http://www.youkioske.com/bienestar/lang/'+lang,20,'')
	addDir(__language__(30060),'http://www.youkioske.com/cultura-historia/lang/'+lang,20,'')
	addDir(__language__(30061),'http://www.youkioske.com/informatica-tecnologia/lang/'+lang,20,'')
	addDir(__language__(30062),'http://www.youkioske.com/manualidades/lang/'+lang,20,'')
	addDir(__language__(30063),'http://www.youkioske.com/naturaleza/lang/'+lang,20,'')
	addDir(__language__(30065),'http://www.youkioske.com/otras-tematicas/lang/'+lang,20,'')

def comics(lang):
	addDir(__language__(30066),'http://www.youkioske.com/comic-espanoles/lang/'+lang,20,'')
	addDir(__language__(30067),'http://www.youkioske.com/comic-clasicos/lang/'+lang,20,'')
	addDir(__language__(30068),'http://www.youkioske.com/comic-superheroes/lang/'+lang,20,'')
	addDir(__language__(30069),'http://www.youkioske.com/comic-infantiles/lang/'+lang,20,'')
	addDir(__language__(30070),'http://www.youkioske.com/manga-anime/lang/'+lang,20,'')
	addDir(__language__(30072),'http://www.youkioske.com/otros-comics/lang/'+lang,20,'')

def others(lang):
	addDir(__language__(30073),'http://www.youkioske.com/arte/lang/'+lang,20,'')
	addDir(__language__(30074),'http://www.youkioske.com/cocina/lang/'+lang,20,'')
	addDir(__language__(30075),'http://www.youkioske.com/mamas-y-bebes/lang/'+lang,20,'')
	addDir(__language__(30076),'http://www.youkioske.com/bricolaje-jardin/lang/'+lang,20,'')
	addDir(__language__(30077),'http://www.youkioske.com/cursos-idiomas/lang/'+lang,20,'')
	addDir(__language__(30078),'http://www.youkioske.com/revistas-manualidades/lang/'+lang,20,'')
	addDir(__language__(30079),'http://www.youkioske.com/mundo-animal/lang/'+lang,20,'')
	addDir(__language__(30080),'http://www.youkioske.com/graffitis/lang/'+lang,20,'')
	addDir(__language__(30081),'http://www.youkioske.com/tattoo/lang/'+lang,20,'')
	addDir(__language__(30082),'http://www.youkioske.com/otra-tematica/lang/'+lang,20,'')


def content_youkioske(url):

	itemlist = []
	data = urllib.urlopen(url).read()
	patron = '<div class="storycontent">.*?<a title="(.*?)".*?href="(.*?)".*?>.*?<img.*?src="(.*?)".*?>'
	matches = re.compile(patron,re.DOTALL).findall(data)
	for match in matches:
		url = "http://www.youkioske.com"+match[1]
		titulo = match[0]
		thumb = "http://www.youkioske.com"+match[2]
		itemlist.append(addItem(titulo,url,21,thumb))
	patron = '<span class="pagescurrent">.*?</span><a href="(.*?)">'
	matches = re.compile(patron,re.DOTALL).findall(data)
	if len(matches)>0:
		url = "http://www.youkioske.com"+matches[0]
		itemlist.append(addDir(__language__(30111),url,20,''))
	return itemlist

def pages_youkioske(url,name):

	itemlist = []
	data = urllib.urlopen(url).read()
	patron = '<iframe.*?src="http://www.youkioske.com/modules/video_plus/video_plus.php\?id=(.*?)".*?>'
	url_id = 'http://www.youkioske.com/modules/video_plus/video_plus.php?id='
	matches = re.compile(patron,re.DOTALL).findall(data)
	if len(matches)>0:
		redirect = url_id+matches[0]
		patron = '<iframe.*?src="(.*?)".*?>'
		data = urllib.urlopen(redirect).read()
		matches2 = re.compile(patron,re.DOTALL).findall(data)
		if len(matches2)>0:
			redirect = matches2[0]
			if re.search('scribd.com',redirect) is not None: #Si el contenido esta en scribd
				download.clean_path()
				patron_scrib = 'http://www.scribd.com/fullscreen/(.*?)\?access_key'
				scrib_matches = re.compile(patron_scrib,re.DOTALL).findall(redirect)
				id = scrib_matches[0]
				url_scrib = 'http://es.scribd.com/mobile/documents/'+id+'/download?commit=Download+Now&secret_password='
				savename = os.path.join(CACHE_PATH,name+".pdf")
				try:
					file = urllib.urlretrieve(url_scrib,savename,reporthook=None)
					download.extract_pdf(savename)
				except:
					xbmcgui.Dialog().ok(__language__(30104),'')
				for file in os.listdir(CACHE_PATH):
					url = os.path.join(CACHE_PATH,file)
					if url[-4:]!='.pdf':
						itemlist.append(addLink(file,url,url))
			else:
				#Si el contenido esta en issuu
				data = urllib.urlopen(redirect).read()
				patron = 'documentId: "(.*?)"'
				matches2 = re.compile(patron,re.DOTALL).findall(data)
				print redirect
				id = matches2[0]
				index = "http://document.issuu.com/"+id+"/document.xml?unique=9999999999999"
				req = urllib2.Request(index)
				req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 6.0; es-ES; rv:1.9.0.14) Gecko/2009082707 Firefox/3.0.14')
				try:
					response = urllib2.urlopen(req)
				except:
					req = urllib2.Request(index.replace(" ","%20"))
					req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 6.0; es-ES; rv:1.9.0.14) Gecko/2009082707 Firefox/3.0.14')
					response = urllib2.urlopen(req)
				data=response.read()
				patron_page = 'pageCount="(.*?)"'
				matches3 = re.compile(patron_page,re.DOTALL).findall(data)
				total = matches3[0]
				total = int(total)- 1
				for i in range(total):
					titulo = __language__(30110)+str(i+1)
					url = "http://image.issuu.com/"+id+"/jpg/page_"+str(i+1)+".jpg"
					thumb = "http://image.issuu.com/"+id+"/jpg/page_"+str(i+1)+"_thumb_large.jpg"
					itemlist.append(addLink(titulo,url,thumb))
		return itemlist


def submanga():
	addDir(__language__(30112),'indice',31,'')
	addDir(__language__(30113),'genero',31,'')	

def submanga_index(url):
	itemlist = []
	if url == 'indice':
		url = 'http://submanga.com/series/n'
		data = urllib.urlopen(url).read()
		patron = '<td class="c"><a href=".*?">(.*?)</a></td>'
		matches = re.compile(patron,re.DOTALL).findall(data)
		for match in matches:
			link = url+"#"+match
			link = urllib.quote(link).replace('%3A',':').replace('%23','#')
			titulo = match
			itemlist.append(addDir(titulo,link,32,''))
	elif url == 'genero':
		url = 'http://submanga.com/series/g'
		data = urllib.urlopen(url).read()
		patron = '<td class="c"><a href=".*?">(.*?)</a></td>'
		matches = re.compile(patron,re.DOTALL).findall(data)
		for match in matches:
			link = "http://submanga.com/genero/"+match
			link = urllib.quote(link).replace('%3A',':').replace('%23','#')
			titulo = match
			print titulo
			if titulo != 'Adulto' and titulo !='Porno' and titulo !='Hentai' and titulo !='Ecchi' and titulo !='OrgÃ­a' and titulo!='Transexual':
				itemlist.append(addDir(titulo,link,32,''))

	return itemlist

def submanga_content(url):
	itemlist = []
	data = urllib.urlopen(url).read()
	if re.search('series/n',url): #Si procede del menu indice
		limit = url[-1:]
		patron = '<th class="" colspan="2"><a href="series/n#'+limit+'".*?>(.*?)<th class="" colspan="2">'
		matches = re.compile(patron,re.DOTALL).findall(data)
		for match in matches:
			patron = '<td><a href="(.*?)"><b class="xs">.*?</b> (.*?)</a></td>'
			matches2 = re.compile(patron,re.DOTALL).findall(match)
			for element in matches2:
				link = element[0]+"/completa"
				titulo = element[1]
				itemlist.append(addDir(titulo,link,33,''))
	else:	#Si procede del menu genero
		patron = '<td><a href="(.*?)">(.*?)</a></td>'
		matches = re.compile(patron,re.DOTALL).findall(data)
		for match in matches:
			link = match[0]+"/completa"
			titulo = match[1]
			itemlist.append(addDir(titulo,link,33,''))

	return itemlist

def submanga_cap(url):
	itemlist = []
	data = urllib.urlopen(url).read()
	patron = '<td class="s"><a href="(.*?)">(.*?)<strong>(.*?)</strong>.*?<a class="grey s".*?>(.*?)</a></td>'
	matches = re.compile(patron,re.DOTALL).findall(data)
	for match in matches:
		link = match[0]
		titulo = match[1]+match[2]+" -- "+match[3]
		itemlist.append(addItem(titulo,link,34,''))

	return itemlist

def submanga_view(url):
	itemlist = []
	patron_url = 'http://submanga.com/.*?/.*?/(.*)'
	matches = re.compile(patron_url,re.DOTALL).findall(url)
	url = 'http://submanga.com/c/'+matches[0]
	data = urllib.urlopen(url).read()
	patron = '<option.*?>(.*?)</option>'
	matches2 = re.compile(patron,re.DOTALL).findall(data)
	num = len(matches2)
	total = matches2[num-1]
	total = int(total)-1
	patron = '<div>.*?<a.*?><img.*?src="(.*?)"'
	matches2 = re.compile(patron,re.DOTALL).findall(data)
	url = matches2[0][:-5]
	for i in range(total):
		link = url+str(i+1)+".jpg"
		titulo = __language__(30110)+str(i+1)
		itemlist.append(addLink(titulo,link,link))
	
	return itemlist


def search_youkioske():
	tecleado = ""
	keyboard = xbmc.Keyboard('',__language__(30130))
	keyboard.doModal()
	if (keyboard.isConfirmed()):
		tecleado = keyboard.getText()
		tecleado = tecleado.replace(' ','+')
		if len(tecleado)<=0:
			return
	else:
		return
	url = 'http://www.youkioske.com/search/'+tecleado
	content(url)

def search_issuu():
	teclado = ""
	keyboard = xbmc.Keyboard('',__language__(30131))
	keyboard.doModal()
	if (keyboard.isConfirmed()):
		teclado = keyboard.getText()
		if len(teclado)<=0:
			return
		teclado = teclado.replace(' ','%20')
	else:
		return
	#Limite de busqueda por pagina
	pagesize = __settings__.getSetting('pagesize')
	Switch = {'0':'10','1':'20','2':'30','3':'50','4':'100','5':'200','6':'500'}
	pagesize = Switch[pagesize]
	#Idioma
	language = __settings__.getSetting('language_issuu')
	Switch={'0':'all', '1':'es', '2':'en', '3':'fr', '4':'it', '5':'pt', '6':'de'}
	lang = Switch[language]
	url = 'http://search.issuu.com/ds?q='+teclado+'&startIndex=0&pageSize='+pagesize+'&sortBy=visual&responseParams=*&language='+lang+'&jsoncallback=?'
	results_issuu(url,0,teclado)

def results_issuu(url,count,input):
	#Limite de busqueda por pagina
	pagesize = __settings__.getSetting('pagesize')
	Switch = {'0':'10','1':'20','2':'30','3':'50','4':'100','5':'200','6':'500'}
	pagesize = Switch[pagesize]
	#Idioma
	language = __settings__.getSetting('language_issuu')
	Switch={'0':'all', '1':'es', '2':'en', '3':'fr', '4':'it', '5':'pt', '6':'de'}
	lang = Switch[language]
	data=urllib.urlopen(url).read()
	patron = 'description":"(.*?)","documentId":"(.*?)".*?"title":"(.*?)"'
	matches = re.compile(patron,re.DOTALL).findall(data)

	if len(matches)==int(pagesize): #Busca pagina siguiente
		itemlist = []
		for match in matches:
			title = match[2]+" -- "+match[0]
			url = "http://document.issuu.com/"+match[1]+"/document.xml?unique=9999999999999"
			thumb = "http://image.issuu.com/"+match[1]+"/jpg/page_1_thumb_large.jpg" 
			itemlist.append(addItem(title,url,42,thumb))
		
		start = count + int(pagesize) #Pagina desde donde empieza la siguiente busqueda
		url_next = 'http://search.issuu.com/ds?q='+input+'&startIndex='+str(start)+'&pageSize='+pagesize+'&sortBy=visual&responseParams=*&language='+lang+'&jsoncallback=?'
		itemlist.append(addDir(__language__(30111),url_next,41,'',count = start,input=input))
		return itemlist	
	else:
		itemlist = []
		for match in matches:
			title = match[2]+" -- "+match[0]
			url = "http://document.issuu.com/"+match[1]+"/document.xml?unique=9999999999999"
			thumb = "http://image.issuu.com/"+match[1]+"/jpg/page_1_thumb_large.jpg" 
			itemlist.append(addItem(title,url,42,thumb))
		return itemlist	

def content_issuu(url):
	id = url.split('http://document.issuu.com/')
	id = id[1].split('/document.xml')
	id = id[0]
	itemlist = []
	req = urllib2.Request(url)
	req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 6.0; es-ES; rv:1.9.0.14) Gecko/2009082707 Firefox/3.0.14')
	try:
		response = urllib2.urlopen(req)
	except:
		req = urllib2.Request(url.replace(" ","%20"))
		req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 6.0; es-ES; rv:1.9.0.14) Gecko/2009082707 Firefox/3.0.14')
		response = urllib2.urlopen(req)
	data=response.read()
	patron_page = 'pageCount="(.*?)"'
	matches3 = re.compile(patron_page,re.DOTALL).findall(data)
	total = matches3[0]
	total = int(total)- 1 #total de paginas
	for i in range(total):
		titulo = __language__(30110)+str(i+1)
		url = "http://image.issuu.com/"+id+"/jpg/page_"+str(i+1)+".jpg"
		thumb = "http://image.issuu.com/"+id+"/jpg/page_"+str(i+1)+"_thumb_large.jpg"
		itemlist.append(addLink(titulo,url,thumb))
	return itemlist

def search_scribd():

	teclado = ""
	keyboard = xbmc.Keyboard('',__language__(30132))
	keyboard.doModal()
	if (keyboard.isConfirmed()):
		teclado = keyboard.getText()
		if len(teclado)<=0:
			return
		teclado = teclado.replace(' ','+')
	else:
		return
	#Limite de busqueda por pagina
	pagesize = __settings__.getSetting('pagesize')
	Switch = {'0':'10','1':'20','2':'30','3':'50','4':'100','5':'200','6':'500'}
	pagesize = Switch[pagesize]
	#Idioma
	language = __settings__.getSetting('language_scribd')
	Switch={'0':'', '1':'4', '2':'1', '3':'5', '4':'8', '5':'13', '6':'9'}
	lang = Switch[language]
	url = 'http://es.scribd.com/opensearch?category=&filetype=&language='+lang+'&limit='+pagesize+'&num_pages=&page=1&paid=false&query='+teclado
	results_scribd(url)

def results_scribd(url):
	itemlist = []
	data=urllib.urlopen(url).read()
	patron = '<div class="document_thumbnail">.*?<a href="(.*?)">.*?<img src="(.*?)".*?/>.*?<a class="name_link".*?>(.*?)</a>'
	matches = re.compile(patron,re.DOTALL).findall(data)
	for match in matches:
		url = match[0]
		title = match[2]
		thumb = match[1]+'.jpg'
		itemlist.append(addItem(title,url,45,thumb))
	patron = '<a class="next" href="(.*?)".*?>'
	matches = re.compile(patron,re.DOTALL).findall(data)
	if len(matches)>0:
		url = "http://es.scribd.com"+matches[0]
		itemlist.append(addDir(__language__(30111),url,44,''))
	return itemlist

def content_scribd(url,name):
	itemlist = []
	download.clean_path()
	patron_scrib = 'http://es.scribd.com/doc/(.*?)/.*?'
	scrib_matches = re.compile(patron_scrib,re.DOTALL).findall(url)
	id = scrib_matches[0]
	url_scrib = 'http://es.scribd.com/mobile/documents/'+id+'/download?commit=Download+Now&secret_password='
	savename = os.path.join(CACHE_PATH,name+".pdf")
	try:
		#Descargo pdf
		file = urllib.urlretrieve(url_scrib,savename,reporthook=None)
		#Extraigo jpgs del pdf
		download.extract_pdf(savename)
		import glob
		ficheros = glob.glob(CACHE_PATH+'/*.jpg')
		count = 0
		for file in ficheros:
			count += 1
			url = os.path.join(CACHE_PATH,file)
			title = __language__(30109)+"%d" % count
			itemlist.append(addLink(title,url,url))
		return itemlist
	except: #Si no hay jpgs en el pdf, opcion descarga
		dialog = xbmcgui.Dialog()
		resp = dialog.yesno('',__language__(30145),__language__(30146))
		if resp == True:
			xbmc.executebuiltin("XBMC.RunScript("+__cwd__+"/default.py,save_scribd,"+url_scrib+","+name+")")

def search_google():
	teclado = ""
	keyboard = xbmc.Keyboard('',__language__(30134))
	keyboard.doModal()
	if (keyboard.isConfirmed()):
		teclado = keyboard.getText()
		if len(teclado)<=0:
			return
		teclado = teclado.replace(' ','+').replace('Ã±','ñ')
	else:
		return
	#Tipo de busqueda
	type = __settings__.getSetting('type_google')
	Switch={'0':'p', '1':'f'}
	tipo = Switch[type]
	#Idioma
	language = __settings__.getSetting('language_google')
	Switch={'0':'all', '1':'es', '2':'en', '3':'fr', '4':'it', '5':'pt', '6':'de'}
	lang = Switch[language]
	#Buscar en contenido,titulo o autor
	search_ = __settings__.getSetting('search_google')
	Switch = {'0':'','1':'intitle:','2':'inauthor:'}
	search = Switch[search_]
	url = 'http://www.google.com/search?tbo=p&tbm=bks&q='+search+teclado+'&tbs=,bkv:'+tipo+'&lr=lang_'+lang
	results_google(url)

def results_google(index):
	download.clean_path()
	itemlist = []
	response = download.download_page(index)
	data=response.read()
	patron = '<li class=g>.*?<h3 class=r><a href="(.*?)".*?>(.*?)</a>(?=.*?<a href="/search.*?>.*?</a>(.*?)<).*?(?=</a>(.*?))'
	matches = re.compile(patron,re.DOTALL).findall(data)
	for match in matches:
		url_google = match[0]
		patron_url = 'id=(.*?)&amp;'
		matches2 = re.compile(patron_url,re.DOTALL).findall(url_google)
		id = matches2[0]
		title = match[1].replace('<em>','').replace('</em>','')+' '+match[2]+match[3]
		cache_thumb = os.path.join(CACHE_PATH,id+".jpg")
		thumb = open(cache_thumb,'w')
		thumb.write(download.download_page('http://books.google.com/books?id='+id+'&printsec=frontcover&img=1&w=800').read())
		thumb.close()
		url = 'http://books.google.com/books?id='+id+'&printsec=frontcover&#v=onepage&q&f=false'
		itemlist.append(addItem(title,url,51,cache_thumb))

	patron_next = '<a id="pnnext".*?href=".*?start=(.*?)&amp;'
	matches = re.compile(patron_next,re.DOTALL).findall(data)
	if len(matches)>0:
		url = index+"&start="+matches[0]
		itemlist.append(addDir(__language__(30111),url,50,''))
	return itemlist

def content_google(url):
	download.clean_path()
	itemlist = []
	response = download.download_page(url)
	data=response.read()
	patron = '\{"pid":"(.*?)".*?order'
	matches = re.compile(patron,re.DOTALL).findall(data)
	lpage = matches[0]
	encontrados = []
	patron_url = 'id=(.*?)&'
	matches2 = re.compile(patron_url,re.DOTALL).findall(url)
	id = matches2[0]
	for match in matches:
		url_2 = 'http://books.google.com/books?id='+id+'&lpg='+lpage+'&hl=es&pg='+match+'&jscmd=click3'
		response = download.download_page(url_2)
		try:
			json = simplejson.loads(response.read())
			url = json['page'][0]['src']
			url += '&w=1200'
			if url not in encontrados:
				title = match
				filename = os.path.join(CACHE_PATH , title+'.jpg')
				file = open(filename,'w')
				file.write(download.download_page(url).read())
				file.close()
				itemlist.append(addLink(title,filename,filename))
			encontrados.append(url)
		except:
			pass
	return itemlist

def downloads():

	itemlist= []
	for file in os.listdir(SAVE_PATH):
		itemlist.append(addLink(file,os.path.join(SAVE_PATH,file),os.path.join(SAVE_PATH,file)))
	return itemlist

def marcadores():
	itemlist = []
	for file in os.listdir(FAVORITE_PATH):
		try:
			name,url,mode,thumb = marcador.read(file)
			itemlist.append(addItem(name,url,mode,thumb,category='marcadores',path=file))
		except:
			pass
	return itemlist

def get_params():
        param=[]
        paramstring=sys.argv[2]
        if len(paramstring)>=2:
                params=sys.argv[2]
                cleanedparams=params.replace('?','')
                if (params[len(params)-1]=='/'):
                        params=params[0:len(params)-2]
                pairsofparams=cleanedparams.split('&')
                param={}
                for i in range(len(pairsofparams)):
                        splitparams={}
                        splitparams=pairsofparams[i].split('=')
                        if (len(splitparams))==2:
                                param[splitparams[0]]=splitparams[1]
                                
        return param

def doPlugin():
	params=get_params()
	url=None
	name=None
	mode=None
	count=None
	input=None

	try:
			url=urllib.unquote_plus(params["url"])
	except:
			pass
	try:
			name=urllib.unquote_plus(params["name"])
	except:
			pass
	try:
			mode=int(params["mode"])
	except:
			pass			
	try:
			count=int(params["count"])
	except:
			pass
	try:
			input=urllib.unquote_plus(params["input"])
	except:
			pass

	print "Mode: "+str(mode)
	print "URL: "+str(url)
	print "Name: "+str(name)

	if mode==None or url==None or len(url)<1:
			print ""
			CATEGORIES()

	elif mode==1:
			print "YouKioske"
			youkioske()

	elif mode==2:
			print "Search YouKioske"
			search_youkioske()

	elif mode==3:
			print "Downloads"
			downloads()

	elif mode==4:
			print "Config"
			__settings__.openSettings()
			return

	elif mode==6:
			print "Submanga"
			submanga()

	elif mode==7:
			print "Search Issuu"
			search_issuu()

	elif mode==8:
			print "Search Scribd"
			search_scribd()

	elif mode==9:
			print "Marcadores"
			marcadores()

	elif mode==10:
			print "press language: " + url
			press(url)

	elif mode==11:
			print "magazines language: " + url
			magazines(url)

	elif mode==12:
			print "tecnology language: " + url
			tecnology(url)

	elif mode==13:
			print "motor language: " + url
			motor(url)

	elif mode==14:
			print "sports language: " + url
			sports(url)

	elif mode==15:
			print "books language: " + url
			books(url)

	elif mode==16:
			print "comics language: " + url
			comics(url)

	elif mode==17:
			print "others language: " + url
			others(url)

	elif mode==20:
			print "items: "+url
			content_youkioske(url)

	elif mode==21:
			print "pages: "+url
			pages_youkioske(url,name)

	elif mode==31:
			print "index: "+url
			submanga_index(url)

	elif mode==32:
			print "content: "+url
			submanga_content(url)

	elif mode==33:
			print "cap: "+url
			submanga_cap(url)

	elif mode==34:
			submanga_view(url)			

	elif mode==41:
			print "Results Issuu" + url
			results_issuu(url,count,input)

	elif mode==42:
			content_issuu(url)

	elif mode==44:
			print "Results Scribd" + url
			results_scribd(url)

	elif mode==45:
			content_scribd(url,name)

	elif mode==49:
			search_google()

	elif mode==50:
			results_google(url)

	elif mode==51:
			content_google(url)


	xbmcplugin.endOfDirectory(int(sys.argv[1]))


if sys.argv[1] == 'save_you':
	download.download_youkioske()
elif sys.argv[1] == 'save_sub':
	download.download_submanga()
elif sys.argv[1] == 'save_image':
	download.save_image()
elif sys.argv[1] == 'save_issuu':
	download.download_issuu()
elif sys.argv[1] == 'save_scribd':
	download.download_scribd()
elif sys.argv[1] == 'save_google':
	download.download_google()
elif sys.argv[1] == 'save_fav':
	marcador.save()
elif sys.argv[1] == 'delete_fav':
	marcador.erase()
else:
	doPlugin()