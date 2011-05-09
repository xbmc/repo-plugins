import urllib,urllib2,re,os,xbmcplugin,xbmcgui,xbmcaddon
from BeautifulSoup import BeautifulSoup

__settings__ = xbmcaddon.Addon(id='plugin.audio.internet.archive')
__language__ = __settings__.getLocalizedString
sort = __settings__.getSetting('sort_by')


def getCategories():
	if sort==__language__(30009):
		set = 'publicdate'
	elif sort==__language__(30010):
		set = 'date'
	elif sort==__language__(30011):
		set = 'downloads'
	elif sort==__language__(30012):
		set = 'avg_rating%3B-num_reviews'
	else:
		set = 'publicdate'
	addDir(__language__(30005),'getLiveArchive',4,'special://home/addons/plugin.audio.internet.archive/icon.png')
	addDir(__language__(30001),'getAudioBooks',5,'special://home/addons/plugin.audio.internet.archive/icon.png')
	addDir(__language__(30024),'getRadioPrograms',9,'special://home/addons/plugin.audio.internet.archive/icon.png')
	addDir(__language__(30006),'getMusicArts',10,'special://home/addons/plugin.audio.internet.archive/icon.png')
	addDir(__language__(30002),'http://www.archive.org/search.php?query=collection%3Aopensource_audio&sort=-'+set,1,'special://home/addons/plugin.audio.internet.archive/icon.png')
	addDir(__language__(30004),'http://www.archive.org/search.php?query=collection%3Aaudio_tech&sort=-'+set,1,'special://home/addons/plugin.audio.internet.archive/icon.png')
	addDir(__language__(30013),'http://www.archive.org/search.php?query=collection%3Anetlabels&sort=-'+set,1,'special://home/addons/plugin.audio.internet.archive/icon.png')
	addDir(__language__(30014),'http://www.archive.org/search.php?query=collection%3Aaudio_news&sort=-'+set,1,'special://home/addons/plugin.audio.internet.archive/icon.png')
	addDir(__language__(30015),'http://www.archive.org/search.php?query=collection%3Aaudio_foreign&sort=-'+set,1,'special://home/addons/plugin.audio.internet.archive/icon.png')
	addDir(__language__(30017),'http://www.archive.org/search.php?query=collection%3Aaudio_religion&sort=-'+set,1,'special://home/addons/plugin.audio.internet.archive/icon.png')



def getAudioBooks():
	if sort==__language__(30009):
		set = 'publicdate'
	elif sort==__language__(30010):
		set = 'date'
	elif sort==__language__(30011):
		set = 'downloads'
	elif sort==__language__(30012):
		set = 'avg_rating%3B-num_reviews'
	else:
		set = 'publicdate'
	addDir(__language__(30020),'audio_bookspoetry',8,'special://home/addons/plugin.audio.internet.archive/resources/search.png')
	addDir(__language__(30007),'audio_bookspoetry',6,'special://home/addons/plugin.audio.internet.archive/resources/search.png')
	addDir(__language__(30018),'http://www.archive.org/details/audio_bookspoetry',7,'special://home/addons/plugin.audio.internet.archive/icon.png')
	aurl='http://www.archive.org/details/audio_bookspoetry'
	req = urllib2.Request(aurl)
	req.addheaders = [('Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.3) Gecko/20100401 Firefox/3.6.3 ( .NET CLR 3.5.30729)')]
	response = urllib2.urlopen(req)
	alink=response.read()
	response.close()
	soup = BeautifulSoup(alink)
	divTag = soup.findAll('div', attrs={'style' : "padding:10px;"})
	cata=re.compile('<div style="padding:10px;"><b><a href="(.+?)">(.+?)</a></b><br />(.+?)</div>').findall(str(divTag))
	del cata[1]
	for url,name,desc in cata:
		url=url.replace('/details/','/search.php?query=collection%3A')
		addDir(name+' ) '+desc,'http://www.archive.org'+url+'&sort=-'+set,1,'special://home/addons/plugin.audio.internet.archive/icon.png')	
	url='http://www.archive.org/search.php?query=collection%3Aaudio_bookspoetry&sort=-'+set
	req = urllib2.Request(url)
	req.addheaders = [('Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.3) Gecko/20100401 Firefox/3.6.3 ( .NET CLR 3.5.30729)')]
	response = urllib2.urlopen(req)
	link=response.read()
	response.close()
	match=re.compile('<a class="titleLink" href="(.+?)">(.+?)</a>').findall(link)
	for url,name in match:
		addDir(name,'http://www.archive.org'+url,2,'special://home/addons/plugin.audio.internet.archive/icon.png')
	page=re.compile('</a> &nbsp;&nbsp;&nbsp; <a href="(.+?)">Next</a>').findall(link)
	if len(page)>1:del page[0]
	for url in page:
		url=url.replace('&amp;','&')
		addDir(__language__(30016),'http://www.archive.org'+url,1,'special://home/addons/plugin.audio.internet.archive/resources/next.png')


def getRadioPrograms():
	if sort==__language__(30009):
		set = 'publicdate'
	elif sort==__language__(30010):
		set = 'date'
	elif sort==__language__(30011):
		set = 'downloads'
	elif sort==__language__(30012):
		set = 'avg_rating%3B-num_reviews'
	else:
		set = 'publicdate'
	addDir(__language__(30020),'radioprograms',8,'special://home/addons/plugin.audio.internet.archive/resources/search.png')
	addDir(__language__(30007),'radioprograms',6,'special://home/addons/plugin.audio.internet.archive/resources/search.png')
	aurl='http://www.archive.org/details/radioprograms'
	req = urllib2.Request(aurl)
	req.addheaders = [('Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.3) Gecko/20100401 Firefox/3.6.3 ( .NET CLR 3.5.30729)')]
	response = urllib2.urlopen(req)
	alink=response.read()
	response.close()
	soup = BeautifulSoup(alink)
	divTag = soup.findAll('div', attrs={'style' : "padding:10px;"})
	cata=re.compile('<div style="padding:10px;"><b><a href="(.+?)">(.+?)</a></b><br />(.+?)</div>').findall(str(divTag))
	del cata[8]
	for url,name,desc in cata:
		url=url.replace('/details/','/search.php?query=collection%3A')
		addDir(name+' ) '+desc,'http://www.archive.org'+url+'&sort=-'+set,1,'special://home/addons/plugin.audio.internet.archive/icon.png')
	url='http://www.archive.org/search.php?query=collection%3Aaudio_music&sort=-'+set
	req = urllib2.Request(url)
	req.addheaders = [('Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.3) Gecko/20100401 Firefox/3.6.3 ( .NET CLR 3.5.30729)')]
	response = urllib2.urlopen(req)
	link=response.read()
	response.close()
	match=re.compile('<a class="titleLink" href="(.+?)">(.+?)</a>').findall(link)
	for url,name in match:
		addDir(name,'http://www.archive.org'+url,2,'special://home/addons/plugin.audio.internet.archive/icon.png')
	page=re.compile('</a> &nbsp;&nbsp;&nbsp; <a href="(.+?)">Next</a>').findall(link)
	if len(page)>1:del page[0]
	for url in page:
		url=url.replace('&amp;','&')
		addDir(__language__(30016),'http://www.archive.org'+url,1,'special://home/addons/plugin.audio.internet.archive/resources/next.png')


def getLiveArchive():
	if sort==__language__(30009):
		set = 'publicdate'
	elif sort==__language__(30010):
		set = 'date'
	elif sort==__language__(30011):
		set = 'downloads'
	elif sort==__language__(30012):
		set = 'avg_rating%3B-num_reviews'
	else:
		set = 'publicdate'
	addDir(__language__(30020),'etree',8,'special://home/addons/plugin.audio.internet.archive/resources/search.png')
	addDir(__language__(30000),'getArtist',3,'special://home/addons/plugin.audio.internet.archive/resources/search.png')
	url='http://www.archive.org/search.php?query=%28%28collection%3Aetree%20OR%20mediatype%3Aetree%29%20AND%20NOT%20collection%3AGratefulDead%29%20AND%20-mediatype%3Acollection&sort=-'+set
	req = urllib2.Request(url)
	req.addheaders = [('Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.3) Gecko/20100401 Firefox/3.6.3 ( .NET CLR 3.5.30729)')]
	response = urllib2.urlopen(req)
	link=response.read()
	response.close()
	match=re.compile('<a class="titleLink" href="(.+?)">(.+?)</a>').findall(link)
	for url,name in match:
		addDir(name,'http://www.archive.org'+url,2,'special://home/addons/plugin.audio.internet.archive/icon.png')
	page=re.compile('</a> &nbsp;&nbsp;&nbsp; <a href="(.+?)">Next</a>').findall(link)
	if len(page)>1:del page[0]
	for url in page:
		url=url.replace('&amp;','&')
		addDir(__language__(30016),'http://www.archive.org'+url,1,'special://home/addons/plugin.audio.internet.archive/resources/next.png')


def getMusicArts():
	if sort==__language__(30009):
		set = 'publicdate'
	elif sort==__language__(30010):
		set = 'date'
	elif sort==__language__(30011):
		set = 'downloads'
	elif sort==__language__(30012):
		set = 'avg_rating%3B-num_reviews'
	else:
		set = 'publicdate'
	addDir(__language__(30020),'audio_music',8,'special://home/addons/plugin.audio.internet.archive/resources/search.png')
	addDir(__language__(30007),'audio_music',6,'special://home/addons/plugin.audio.internet.archive/resources/search.png')
	aurl='http://www.archive.org/details/audio_music'
	req = urllib2.Request(aurl)
	req.addheaders = [('Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.3) Gecko/20100401 Firefox/3.6.3 ( .NET CLR 3.5.30729)')]
	response = urllib2.urlopen(req)
	alink=response.read()
	response.close()
	soup = BeautifulSoup(alink)
	divTag = soup.findAll('div', attrs={'style' : "padding:10px;"})
	cata=re.compile('<div style="padding:10px;"><b><a href="(.+?)">(.+?)</a></b><br />(.+?)</div>').findall(str(divTag))
	for url,name,desc in cata:
		url=url.replace('/details/','/search.php?query=collection%3A')
		addDir(name+' ) '+desc,'http://www.archive.org'+url+'&sort=-'+set,1,'special://home/addons/plugin.audio.internet.archive/icon.png')
	url='http://www.archive.org/search.php?query=collection%3Aaudio_music&sort=-'+set
	req = urllib2.Request(url)
	req.addheaders = [('Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.3) Gecko/20100401 Firefox/3.6.3 ( .NET CLR 3.5.30729)')]
	response = urllib2.urlopen(req)
	link=response.read()
	response.close()
	match=re.compile('<a class="titleLink" href="(.+?)">(.+?)</a>').findall(link)
	for url,name in match:
		addDir(name,'http://www.archive.org'+url,2,'special://home/addons/plugin.audio.internet.archive/icon.png')
	page=re.compile('</a> &nbsp;&nbsp;&nbsp; <a href="(.+?)">Next</a>').findall(link)
	if len(page)>1:del page[0]
	for url in page:
		url=url.replace('&amp;','&')
		addDir(__language__(30016),'http://www.archive.org'+url,1,'special://home/addons/plugin.audio.internet.archive/resources/next.png')

# get by artist listings
def getArtist():
	if sort==__language__(30009):
		set = 'publicdate'
	elif sort==__language__(30010):
		set = 'date'
	elif sort==__language__(30011):
		set = 'downloads'
	elif sort==__language__(30012):
		set = 'avg_rating%3B-num_reviews'
	else:
		set = 'publicdate'
	url='http://www.archive.org/browse.php?collection=etree&field=%2Fmetadata%2Fcreator'
	req = urllib2.Request(url)
	req.addheaders = [('Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.3) Gecko/20100401 Firefox/3.6.3 ( .NET CLR 3.5.30729)')]
	response = urllib2.urlopen(req)
	link=response.read()
	response.close()
	soup = BeautifulSoup(link)
	aTag = soup.find('tr', attrs={'valign' : 'top'}).findAll('a')
	tag = str(aTag)
	match=re.compile('href="(.+?)">(.+?)</a>, <a href=".+?">(.+?)</a>').findall(tag)
	for url,name,shows in match:
		url=url.replace('/details/','/search.php?query=collection%3A')
		addDir(name+'  | '+shows,'http://www.archive.org'+url+'&sort=-'+set,1,'special://home/addons/plugin.audio.internet.archive/icon.png')


# get the directories		
def getShows(url):
	req = urllib2.Request(url)
	req.addheaders = [('Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.3) Gecko/20100401 Firefox/3.6.3 ( .NET CLR 3.5.30729)')]
	response = urllib2.urlopen(req)
	link=response.read()
	response.close()
	match=re.compile('<a class="titleLink" href="(.+?)">(.+?)</a>.+?<br/>(.+?)</td>').findall(link)
	for url,name,desc in match:
		name=name.replace('<span class="searchTerm">','').replace('</span>','')
		addDir(name,'http://www.archive.org'+url,2,'special://home/addons/plugin.audio.internet.archive/icon.png')
	page=re.compile('</a> &nbsp;&nbsp;&nbsp; <a href="(.+?)">Next</a>').findall(link)
	if len(page)>1:del page[0]
	for url in page:
		url=url.replace('&amp;','&')
		addDir(__language__(30016),'http://www.archive.org'+url,1,'special://home/addons/plugin.audio.internet.archive/resources/next.png')


# gets names and urls	
def playMusic(url):
	req = urllib2.Request(url)
	req.addheaders = [('Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.3) Gecko/20100401 Firefox/3.6.3 ( .NET CLR 3.5.30729)')]
	response = urllib2.urlopen(req)
	link=response.read()
	response.close()
	soup = BeautifulSoup(link)
	title = soup('h1')[2].contents[1]
	pTag = soup.findAll('p', attrs={'class' : 'content'})
	aTag = str(pTag[1]('a'))
	apTag =str(pTag[0]('a'))
	scrTag = soup.findAll('script', attrs={'type' : 'text/javascript'})
	script = scrTag[6].string.replace("\'",'').replace('\n','').replace('\\/','/')
	names=re.compile('names     :\[\"(.+?)"\]').findall(script)
	mp3s=re.compile('mp3s      :\[\"(.+?)"\]').findall(script)
	lengths=re.compile('lengths   :\[\"(.+?)"\],').findall(script)
	mainDir=re.compile(' mainDir   :"(.+?)"').findall(script)
	ident=re.compile('IAD.identifier  ="(.+?)"').findall(script)
	iad=re.compile('IAD.identifier  =".+?";IAD.playlists = (.+?);').findall(script)
	server = 'http://www.archive.org/download/'
	ident = str(ident)[3:-2]
	mp3 = str(mp3s)[3:-2].split('","')
	name = str(names)[3:-2].split('","')
	length = str(lengths)[3:-2].split('","')
	conTent=re.compile('<a href=".+?">(.+?)</a>').findall(apTag)
	content=re.compile('<a href=".+?">(.+?)</a>').findall(aTag)
	if len(content)>1:
		del content[0]
	if iad==[u'false']:
		print 'sorry no playlist'
		dialog = xbmcgui.Dialog()
		ok = dialog.ok('Internet Archive',__settings__.getLocalizedString(30021))
		return
	else:
		if content==['64Kbps MP3 ZIP']:
			addLink('Play All )  '+title,server+ident+'/'+ident+'_64kb.mp3.zip','','special://home/addons/plugin.audio.internet.archive/resources/play.png')
			addDownload('Download  64Kbps MP3 ZIP)  '+title,server+ident+'/'+ident+'_64kb.mp3.zip',11,'special://home/addons/plugin.audio.internet.archive/resources/download.png')
		if content==['VBR ZIP']:
			addLink('Play All )  '+title,server+ident+'/'+ident+'_vbr_mp3.zip','','special://home/addons/plugin.audio.internet.archive/resources/play.png')
			addDownload('Download  VBR MP3 ZIP)  '+title,server+ident+'/'+ident+'_vbr_mp3.zip',11,'special://home/addons/plugin.audio.internet.archive/resources/download.png')
		if conTent==['Whole directory']:
			addLink('Play All )  '+title,'http://www.archive.org/compress/'+ident,'','special://home/addons/plugin.audio.internet.archive/resources/play.png')
			addDownload('Download  ZIP)  '+title,'http://www.archive.org/compress/'+ident,11,'special://home/addons/plugin.audio.internet.archive/resources/download.png')		
		if content==['Whole directory']:
			addLink('Play All )  '+title,'http://www.archive.org/compress/'+ident,'','special://home/addons/plugin.audio.internet.archive/resources/play.png')
			addDownload('Download  ZIP)  '+title,'http://www.archive.org/compress/'+ident,11,'special://home/addons/plugin.audio.internet.archive/resources/download.png')
		if len(name)==len(mp3)==len(length):
			for index in range(len(name)):
				addLink(length[index]+' '+name[index],server+ident+'/'+mp3[index],length[index],'special://home/addons/plugin.audio.internet.archive/icon.png')
	
	
def DownloadFiles(name,url):
	filename = name[19:]+'.zip'
	def download(url, dest):
		dialog = xbmcgui.DialogProgress()
		dialog.create(__settings__.getLocalizedString(30022), __settings__.getLocalizedString(30023), filename)
		urllib.urlretrieve(url, dest, lambda nb, bs, fs, url = url: _pbhook(nb, bs, fs, url, dialog))
	def _pbhook(numblocks, blocksize, filesize, url = None,dialog = None):
		try:
			percent = min((numblocks * blocksize * 100) / filesize, 100)
			dialog.update(percent)
		except:
			percent = 100
			dialog.update(percent)
		if dialog.iscanceled():
			dialog.close()
	if (__settings__.getSetting('download') == ''):
		__settings__.openSettings('download')
	filepath = xbmc.translatePath(os.path.join(__settings__.getSetting('download'),filename))
	download(url, filepath)


def Search(url):
	if sort==__language__(30009):
		set = 'publicdate'
	elif sort==__language__(30010):
		set = 'date'
	elif sort==__language__(30011):
		set = 'downloads'
	elif sort==__language__(30012):
		set = 'avg_rating%3B-num_reviews'
	else:
		set = 'publicdate'
	searchStr = ''
	keyboard = xbmc.Keyboard(searchStr, "Search")
	keyboard.doModal()
	if (keyboard.isConfirmed() == False):
		return
	searchstring = keyboard.getText()
	newStr = searchstring.replace(' ','%20')
	if len(newStr) == 0:
		return
	url = 'http://www.archive.org/search.php?query=' + newStr + '%20AND%20collection%3A'+url+'&sort=-'+set
	getShows(url)


def searchByTitle(url):
	url='http://www.archive.org/details/'+url
	req = urllib2.Request(url)
	req.addheaders = [('Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.3) Gecko/20100401 Firefox/3.6.3 ( .NET CLR 3.5.30729)')]
	response = urllib2.urlopen(req)
	link=response.read()
	response.close()
	soup = BeautifulSoup(link)
	aTag = soup.findAll(id="browsetitle")
	atag = str(aTag)
	match=re.compile('<a href="(.+?)">(.+?)</a>').findall(atag)
	for url,name in match:
		url=url.replace('&amp;','&').replace(' ','%20')
		addDir(name,'http://www.archive.org'+url,1,'special://home/addons/plugin.audio.internet.archive/icon.png')

# search audio books by author
def searchByAuthor():
	url='http://www.archive.org/details/audio_bookspoetry'
	req = urllib2.Request(url)
	req.addheaders = [('Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.3) Gecko/20100401 Firefox/3.6.3 ( .NET CLR 3.5.30729)')]
	response = urllib2.urlopen(req)
	link=response.read()
	response.close()
	soup = BeautifulSoup(link)
	aTag = soup.findAll(id="browsetitle")
	atag = str(aTag)
	match=re.compile('<a href="(.+?)">(.+?)</a>').findall(atag)
	for url,name in match:
		url=url.replace('&amp;','&').replace(' ','%20').replace('sort=title','sort=creator').replace('firstTitle','firstCreator')
		addDir(name,'http://www.archive.org'+url,1,'special://home/addons/plugin.audio.internet.archive/icon.png')


def addLink(name,url,length,iconimage):
	ok=True
	liz=xbmcgui.ListItem(name, iconImage="DefaultAudio.png", thumbnailImage=iconimage)
	liz.setInfo( type="Audio", infoLabels={ "Title": name, } )
	ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=liz)
	return ok

def addDir(name,url,mode,iconimage):
	u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
	ok=True
	liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
	liz.setInfo( type="Audio", infoLabels={ "Title": name } )
	ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)
	return ok

def addDownload(name,url,mode,iconimage):
	u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
	ok=True
	liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
	liz.setProperty("IsPlayable","false")
	ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=False,totalItems=1)
	return ok
	
	
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

params=get_params()
url=None
name=None
mode=None

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

print "Mode: "+str(mode)
print "URL: "+str(url)
print "Name: "+str(name)

if mode==None or url==None or len(url)<1:
	print ""
	getCategories()

elif mode==1:
	print ""+url
	getShows(url)
		
elif mode==2:
	print ""+url
	playMusic(url)

elif mode==3:
	print ""+url
	getArtist()

elif mode==4:
	print ""+url
	getLiveArchive()

elif mode==5:
	print ""+url
	getAudioBooks()

elif mode==6:
	print ""+url
	searchByTitle(url)

elif mode==7:
	print ""+url
	searchByAuthor()

elif mode==8:
	print ""+url
	Search(url)	

elif mode==9:
	print ""+url
	getRadioPrograms()

elif mode==10:
	print ""+url
	getMusicArts()

elif mode==11:
	print ""+url
	DownloadFiles(name,url)

xbmcplugin.endOfDirectory(int(sys.argv[1]))	