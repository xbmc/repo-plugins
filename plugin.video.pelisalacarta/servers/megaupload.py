# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Conector para Megaupload
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#------------------------------------------------------------

import re,xbmcgui,xbmc
import urlparse, urllib, urllib2,socket
import megavideo



try:
	from core import scrapertools
	from core import logger
	from core import config
except:
	from Code.core import scrapertools
	from Code.core import logger
	from Code.core import config

import os
COOKIEFILE = os.path.join(config.get_data_path() , "cookies.lwp")

DEBUG = False


# Convierte el código de megaupload a megavideo
def convertcode(megauploadcode):
        # Descarga la página de megavideo pasándole el código de megaupload
        url = "http://www.megavideo.com/?d="+megauploadcode
        data = scrapertools.cachePage(url)
        #logger.info(data)

        # Extrae las entradas (carpetas)
        patronvideos  = 'flashvars.v = "([^"]+)"'
        matches = re.compile(patronvideos,re.DOTALL).findall(data)
        #scrapertools.printMatches(matches)
        
        megavideocode = ""
        if len(matches)>0:
                megavideocode = matches[0]

        return megavideocode

# Extrae directamente la URL del vídeo de Megaupload
def getmegauploaduser(login,password):

	# ---------------------------------------
	#  Inicializa la librería de las cookies
	# ---------------------------------------
	ficherocookies = COOKIEFILE
	try:
		os.remove(ficherocookies)
	except:
		pass

	# the path and filename to save your cookies in

	cj = None
	ClientCookie = None
	cookielib = None

	# Let's see if cookielib is available
	try:
		import cookielib
	except ImportError:
		# If importing cookielib fails
		# let's try ClientCookie
		try:
			import ClientCookie
		except ImportError:
			# ClientCookie isn't available either
			urlopen = urllib2.urlopen
			Request = urllib2.Request
		else:
			# imported ClientCookie
			urlopen = ClientCookie.urlopen
			Request = ClientCookie.Request
			cj = ClientCookie.LWPCookieJar()

	else:
		# importing cookielib worked
		urlopen = urllib2.urlopen
		Request = urllib2.Request
		cj = cookielib.LWPCookieJar()
		# This is a subclass of FileCookieJar
		# that has useful load and save methods

	# ---------------------------------
	# Instala las cookies
	# ---------------------------------

	if cj is not None:
	# we successfully imported
	# one of the two cookie handling modules

		if os.path.isfile(ficherocookies):
			# if we have a cookie file already saved
			# then load the cookies into the Cookie Jar
			cj.load(ficherocookies)

		# Now we need to get our Cookie Jar
		# installed in the opener;
		# for fetching URLs
		if cookielib is not None:
			# if we use cookielib
			# then we get the HTTPCookieProcessor
			# and install the opener in urllib2
			opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
			urllib2.install_opener(opener)

		else:
			# if we use ClientCookie
			# then we get the HTTPCookieProcessor
			# and install the opener in ClientCookie
			opener = ClientCookie.build_opener(ClientCookie.HTTPCookieProcessor(cj))
			ClientCookie.install_opener(opener)

	#print "-------------------------------------------------------"
	url="http://www.megaupload.com/?c=login"
	#print url
	#print "-------------------------------------------------------"
	theurl = url
	# an example url that sets a cookie,
	# try different urls here and see the cookie collection you can make !

	passwordesc=password.replace("&","%26")
	txdata = "login=1&redir=1&username="+login+"&password="+passwordesc
	# if we were making a POST type request,
	# we could encode a dictionary of values here,
	# using urllib.urlencode(somedict)

	txheaders =  {'User-Agent':'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3',
				  'Referer':'http://www.megaupload.com'}
	# fake a user agent, some websites (like google) don't like automated exploration

	req = Request(theurl, txdata, txheaders)
	handle = urlopen(req)
	cj.save(ficherocookies)					 # save the cookies again	
	data=handle.read()
	handle.close()

	cookiedatafile = open(ficherocookies,'r')
	cookiedata = cookiedatafile.read()
	cookiedatafile.close();

	'''
	logger.info("----------------------")
	logger.info("Cookies despues")
	logger.info("----------------------")
	logger.info(cookiedata)
	logger.info("----------------------")
	'''

	login = re.search('Welcome', data)
	premium = re.search('flashvars.status = "premium";', data)		

	if login is not None:
		if premium is not None:
			return 'premium'
		elif premium is None:
			return 'gratis'
	elif login is None:
		return None

import exceptions

class SmartRedirectHandler(urllib2.HTTPRedirectHandler):
	def http_error_302(self, req, fp, code, msg, headers):
		raise ImportError(302,headers.getheader("Location"))

def gethighurl(code , password=None):

	megavideologin = config.get_setting("megavideouser")
	if DEBUG:
		logger.info("[megaupload.py] megavideouser=#"+megavideologin+"#")
	megavideopassword = config.get_setting("megavideopassword")
	if megavideologin == '' or megavideopassword == '':
		login = None
	else:
		login = getmegauploaduser(megavideologin,megavideopassword)
	if DEBUG:
		logger.info("[megaupload.py] megavideopassword=#"+megavideopassword+"#")

	video = resuelve("http://www.megaupload.com/?d="+code,login,password)

	if video is not None:
		return video
	else:
		return ""
	
	
def resuelve(url,login, password=None):

	data=scrapertools.cachePage(url)
	password_data = re.search('filepassword',data)
	if password_data is not None:
		teclado = password_mega(password)
		if teclado is not None:
			data = scrapertools.cachePage(url, post="filepassword="+teclado)
		else:
			return None
	enlace = get_filelink(data)
	

	if enlace is None:
		return None
	else:
		if login == 'premium':
			espera = handle_wait(1,'Megaupload','Cargando video.')	
		elif login == 'gratis':
			espera = handle_wait(26,'Megaupload','Cargando video.')	
		else:
			espera = handle_wait(46,'Megaupload','Cargando video.')
	
		if espera == True:
			return enlace
		else:
			advertencia = xbmcgui.Dialog()
			resultado = advertencia.ok('pelisalacarta','Se canceló la reproducción')		
			return None
	

def get_filelink(data):

	#Comprueba si es un enlace premium
	match1=re.compile('<a href="(.+?)" class="down_ad_butt1">').findall(data)
	if str(match1)=='[]':
		match2=re.compile('id="downloadlink"><a href="(.+?)" class=').findall(data)
		try:
			url=match2[0]
		except:
			return None
	else:
		url=match1[0]


	#Si es un archivo .divx lo sustituye por .avi
	if url.endswith('divx'):
		return url[:-4]+'avi'
	else:          
		return url
		
def handle_wait(time_to_wait,title,text):

    print 'Esperando '+str(time_to_wait)+' segundos'    

    espera = xbmcgui.DialogProgress()
    ret = espera.create(' '+title)

    secs=0
    percent=0
    increment = int(100 / time_to_wait)

    cancelled = False
    while secs < time_to_wait:
        secs = secs + 1
        percent = increment*secs
        secs_left = str((time_to_wait - secs))
        remaining_display = ' Espera '+secs_left+' segundos para que comience el vídeo...'
        espera.update(percent,' '+text,remaining_display)
        xbmc.sleep(1000)
        if (espera.iscanceled()):
             cancelled = True
             break
    if cancelled == True:     
         print 'Espera cancelada'
         return False
    else:
         print 'Espera finalizada'
         return True

def password_mega(password):

	if password is not None:
		keyboard = xbmc.Keyboard(password,"Contraseña:")
	else:
		keyboard = xbmc.Keyboard("","Contraseña:")
	keyboard.doModal()
	if (keyboard.isConfirmed()):
		tecleado = keyboard.getText()
		if len(tecleado)<=0:
			return
		else:
			return tecleado
			
def getlowurl(code , password=None):
        return megavideo.getlowurl(convertcode(code),password)