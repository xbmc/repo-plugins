# -*- coding: utf-8 -*-
import urllib, re, os, urllib2, sys, simplejson
import xbmc, xbmcgui, xbmcaddon


__settings__ = xbmcaddon.Addon(id='plugin.image.prensayrevistas')
__language__ = __settings__.getLocalizedString
__cwd__      = __settings__.getAddonInfo('path')
__profile__  = __settings__.getAddonInfo('profile')

CACHE_PATH = xbmc.translatePath(os.path.join(__profile__,'cache'))
SAVE_PATH = xbmc.translatePath(__settings__.getSetting('save_path'))

if not os.path.exists(CACHE_PATH): os.makedirs(CACHE_PATH)
if not os.path.exists(SAVE_PATH): os.makedirs(SAVE_PATH)

BASE_RESOURCE_PATH = xbmc.translatePath( os.path.join( __cwd__, 'lib' ) )
sys.path.append (BASE_RESOURCE_PATH)

from reportlab.lib import pagesizes
from reportlab.platypus import SimpleDocTemplate, Image
A2 = pagesizes.A2




class download_youkioske:
	def __init__(self):
		clean_path()
		dp = xbmcgui.DialogProgress()
		dp.create(__language__(30100),__language__(30099))
		url = sys.argv[2]
		savename = sys.argv[3]
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
				if re.search('scribd.com',redirect) is not None:
					try:
						patron_scrib = 'http://www.scribd.com/fullscreen/(.*?)\?access_key'
						scrib_matches = re.compile(patron_scrib,re.DOTALL).findall(redirect)
						id = scrib_matches[0]
						url = 'http://es.scribd.com/mobile/documents/'+id+'/download?commit=Download+Now&secret_password='
						urllib.urlretrieve(url,os.path.join(SAVE_PATH,savename),lambda nb, bs, fs, url=url: _pbhook(nb,bs,fs,url,dp))
						dp.close()
						xbmcgui.Dialog().ok(__language__(30101),__language__(30102).replace('@REPLACE@',savename),__language__(30103).replace('@REPLACE@',SAVE_PATH))
					except:
						dp.close()
						xbmcgui.Dialog().ok(__language__(30104),'')
				else:
					data = urllib.urlopen(redirect).read()
					patron = 'documentId: "(.*?)"'
					matches2 = re.compile(patron,re.DOTALL).findall(data)
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
					percent = 100 / float(total)
					total = int(total)- 1
					percent_total = 0
					parts = []
					files = []
					download = ''
					for i in range(total):
						titulo = "Pagina_"+str(i+1)
						url = "http://image.issuu.com/"+id+"/jpg/page_"+str(i+1)+".jpg"
						filename = os.path.join(CACHE_PATH , titulo+'.jpg')
						get_image(url,filename)
						files.append(filename)
						parts.append(Image(filename))
						percent_total = percent_total + percent
						dp.update(int(percent_total))
						download = 'ok'

					if download=='ok':
						teclado = ""
						keyboard = xbmc.Keyboard(savename,__language__(30133))
						keyboard.doModal()
						if (keyboard.isConfirmed()):
							teclado = keyboard.getText()
							if len(teclado)<=0:
								return
							teclado = urllib.unquote_plus(teclado)
							doc = SimpleDocTemplate(os.path.join(SAVE_PATH,teclado+".pdf"), pagesize=A2)
							doc.build(parts)
							dp.close()
							xbmcgui.Dialog().ok(__language__(30101),__language__(30102).replace('@REPLACE@',savename),__language__(30103).replace('@REPLACE@',SAVE_PATH))
					else:
						dp.close()
						xbmcgui.Dialog().ok(__language__(30104),'')


class download_submanga:
	def __init__(self):
		clean_path()
		dp = xbmcgui.DialogProgress()
		dp.create(__language__(30100),__language__(30099))
		url = sys.argv[2]
		savename = sys.argv[3]
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
		percent = 100 / float(total)
		total = int(total)- 1
		percent_total = 0
		parts = []
		download = ''
		for i in range(total):
			link = url+str(i+1)+".jpg"
			titulo = "Pagina_"+str(i+1)
			filename = os.path.join(CACHE_PATH , titulo+'.jpg')
			get_image(link,filename)
			parts.append(Image(filename))
			percent_total = percent_total + percent
			dp.update(int(percent_total))
			download = 'ok'

		if download=='ok':
			teclado = ""
			keyboard = xbmc.Keyboard(savename,__language__(30133))
			keyboard.doModal()
			if (keyboard.isConfirmed()):
				teclado = keyboard.getText()
				if len(teclado)<=0:
					return
				teclado = urllib.unquote_plus(teclado)
				doc = SimpleDocTemplate(os.path.join(SAVE_PATH,teclado+".pdf"), pagesize=A2)
				doc.build(parts)
				dp.close()
				xbmcgui.Dialog().ok(__language__(30101),__language__(30102).replace('@REPLACE@',savename),__language__(30103).replace('@REPLACE@',SAVE_PATH))
		else:
			dp.close()
			xbmcgui.Dialog().ok(__language__(30104),'')


class download_issuu:
	def __init__(self):
		clean_path()
		dp = xbmcgui.DialogProgress()
		dp.create(__language__(30100),__language__(30099))
		url = sys.argv[2]
		savename = sys.argv[3]
		id = url.split('http://document.issuu.com/')
		id = id[1].split('/document.xml')
		id = id[0]
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
		percent = 100 / float(total)
		total = int(total)- 1
		percent_total = 0
		parts = []
		download = ''
		for i in range(total):
			titulo = "Pagina_"+str(i+1)
			link = "http://image.issuu.com/"+id+"/jpg/page_"+str(i+1)+".jpg"
			filename = os.path.join(CACHE_PATH , titulo+'.jpg')
			get_image(link,filename)
			parts.append(Image(filename))
			percent_total = percent_total + percent
			dp.update(int(percent_total))
			download = 'ok'

		if download=='ok':
			teclado = ""
			keyboard = xbmc.Keyboard(savename,__language__(30133))
			keyboard.doModal()
			if (keyboard.isConfirmed()):
				teclado = keyboard.getText()
				if len(teclado)<=0:
					return
				teclado = urllib.unquote_plus(teclado)
				doc = SimpleDocTemplate(os.path.join(SAVE_PATH,teclado+".pdf"), pagesize=A2)
				doc.build(parts)
				dp.close()
				xbmcgui.Dialog().ok(__language__(30101),__language__(30102).replace('@REPLACE@',savename),__language__(30103).replace('@REPLACE@',SAVE_PATH))
		else:
			dp.close()
			xbmcgui.Dialog().ok(__language__(30104),'')

class download_scribd:
	def __init__(self):
		dp = xbmcgui.DialogProgress()
		dp.create(__language__(30100),__language__(30099))
		url = sys.argv[2]
		savename = sys.argv[3]
		print savename
		try:
			teclado = ""
			keyboard = xbmc.Keyboard(savename,__language__(30133))
			keyboard.doModal()
			if (keyboard.isConfirmed()):
				teclado = keyboard.getText()
				if len(teclado)<=0:
					return
				teclado = urllib.unquote_plus(teclado)
				urllib.urlretrieve(url,os.path.join(SAVE_PATH,teclado+".pdf"),lambda nb, bs, fs, url=url: _pbhook(nb,bs,fs,url,dp))
				dp.close()
				xbmcgui.Dialog().ok(__language__(30101),__language__(30102).replace('@REPLACE@',savename),__language__(30103).replace('@REPLACE@',SAVE_PATH))
		except:
			dp.close()
			xbmcgui.Dialog().ok(__language__(30104),'')

class download_google:
	def __init__(self):
		clean_path()
		dp = xbmcgui.DialogProgress()
		dp.create(__language__(30100),__language__(30099))
		url = sys.argv[2]
		savename = sys.argv[3]
		response = download_page(url)
		data=response.read()
		patron = '\{"pid":"(.*?)".*?order'
		matches = re.compile(patron,re.DOTALL).findall(data)
		lpage = matches[0]
		encontrados = []
		patron_url = 'id=(.*?)&'
		matches2 = re.compile(patron_url,re.DOTALL).findall(url)
		id = matches2[0]
		parts = []
		percent = 100 / float(len(matches))
		percent_total = 0
		for match in matches:
			url_2 = 'http://books.google.com/books?id='+id+'&lpg='+lpage+'&hl=es&pg='+match+'&jscmd=click3'
			response = download_page(url_2)
			json = simplejson.loads(response.read())
			url = json['page'][0]['src']
			if url not in encontrados:
				title = match
				filename = os.path.join(CACHE_PATH , title+'.jpg')
				file = open(filename,'w')
				file.write(download_page(url).read())
				file.close()
				parts.append(Image(filename))
				percent_total = percent_total + percent
				dp.update(int(percent_total))	
				download = 'ok'
			encontrados.append(url)

		if download=='ok':
			teclado = ""
			keyboard = xbmc.Keyboard(savename,__language__(30133))
			keyboard.doModal()
			if (keyboard.isConfirmed()):
				teclado = keyboard.getText()
				if len(teclado)<=0:
					return
				teclado = urllib.unquote_plus(teclado)
				teclado = teclado.replace('ñ','n')
				doc = SimpleDocTemplate(os.path.join(SAVE_PATH,teclado+".pdf"), pagesize=A2)
				doc.build(parts)
				dp.close()
				xbmcgui.Dialog().ok(__language__(30101),__language__(30102).replace('@REPLACE@',savename),__language__(30103).replace('@REPLACE@',SAVE_PATH))
		else:
			dp.close()
			xbmcgui.Dialog().ok(__language__(30104),'')


class save_image:
	def __init__(self):
		url = sys.argv[2]
		savename = sys.argv[3]
		save = os.path.join(SAVE_PATH, savename)
		try:
			get_image(url,save)
		except:
			import shutil
			shutil.copyfile(url,save)
		xbmcgui.Dialog().ok(__language__(30101),__language__(30102).replace('@REPLACE@',savename),__language__(30103).replace('@REPLACE@',SAVE_PATH))


def extract_pdf(savename):
	pdf = file(savename, "r").read()
	startmark = "\xff\xd8"
	startfix = 0
	endmark = "\xff\xd9"
	endfix = 2
	i = 0

	njpg = 1
	while True:
		istream = pdf.find("stream", i)
		if istream < 0:
			break
		istart = pdf.find(startmark, istream, istream+20)
		if istart < 0:
			i = istream+20
			continue
		iend = pdf.find("endstream", istart)
		if iend < 0:
			raise Exception("Didn't find end of stream!")
		iend = pdf.find(endmark, iend-20)
		if iend < 0:
			raise Exception("Didn't find end of JPG!")

		istart += startfix
		iend += endfix
		jpg = pdf[istart:iend]
		jpgfile = file(os.path.join(CACHE_PATH,"Pagina_%03d"+".jpg") % njpg, "wb")
		jpgfile.write(jpg)
		jpgfile.close()

		njpg += 1
		i = iend
	if njpg ==1:
		raise MiError(1)

class MiError(Exception):
    def __init__(self, valor):
        self.valor = valor

    def __str__(self):
        return "Error " + str(self.valor)



def _pbhook(numblocks, blocksize, filesize, url=None,dp=None):
    try:
        percent = min((numblocks*blocksize*100)/filesize, 100)
        print percent
        dp.update(percent)
    except:
        percent = 100
        dp.update(percent)
    if dp.iscanceled(): 
        print "DOWNLOAD CANCELLED"
        dp.close()

def get_image(url,filename):
    if not os.path.exists(filename):
        response = urllib2.urlopen(url)
        f = open(filename, 'w')
        f.write(response.read())
        f.close()

def clean_path():
	if os.path.exists(CACHE_PATH): 
		for f in os.listdir(CACHE_PATH):
			file = unicode( f, "utf-8") 
			file = os.path.join(CACHE_PATH,file)
			if os.path.isfile(file): os.remove(file)

def download_page(url, post=None, headers=[['User-Agent', 'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.6; es-ES; rv:1.9.2.12) Gecko/20101026 Firefox/4.0.1']]):

	cookies = xbmc.translatePath(os.path.join(__profile__, 'cookies.lwp'))
	import cookielib
	cookie = cookielib.LWPCookieJar()
	if os.path.isfile(cookies):
		cookie.load(cookies)
		opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookie))
		urllib2.install_opener(opener)

	txheaders = {}
	for header in headers:
		txheaders[header[0]]=header[1]


	req = urllib2.Request(url, post, txheaders)
	response = urllib2.urlopen(req)
	cookie.save(cookies)

	return response