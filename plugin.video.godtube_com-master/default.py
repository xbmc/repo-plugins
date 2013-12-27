import urllib,urllib2,re,xbmcplugin,xbmcgui,os,xbmcaddon,sys,xbmcvfs
dbg = False
try:
	import StorageServer
	cache = StorageServer.StorageServer("GodTube")
except:
	import storageserverdummy as StorageServer
	cache = StorageServer.StorageServer("GodTube")

settings = xbmcaddon.Addon( id = 'plugin.video.godtube_com' )
translation = settings.getLocalizedString
next_thumb = os.path.join( settings.getAddonInfo( 'path' ), 'thumbnails', 'nextpage.png' )
browse_thumb = os.path.join( settings.getAddonInfo( 'path' ), 'thumbnails', 'explore.png' )
search_thumb = os.path.join( settings.getAddonInfo( 'path' ), 'thumbnails', 'search.png' )
timeout_thumb = os.path.join( settings.getAddonInfo( 'path' ), 'thumbnails', 'timeout.png' )
base_url='http://www.godtube.com'


##################################################################################################################################

def MAIN():
	addDir(translation(30001),base_url,3, browse_thumb)
        addDir(translation(30002),base_url,2, search_thumb)

##################################################################################################################################
        
def ADDLINKS(url):
	if search_function == 1:
        	keyboard = xbmc.Keyboard('', '')
        	keyboard.doModal()
        if search_function == 0 or keyboard.isConfirmed() and keyboard.getText():
		if search_function == 1:
			search_list=[]
			search_hist = cache.get('Search')
			try:
                		search_list = eval(search_hist)
			except:
				search_list.insert(0, search_hist)
			search_string = keyboard.getText().replace(" ","+")
                	content = url+search_string
			try:			
				if search_string not in search_list:
					search_list.insert(0, search_string)
				if len(search_list) > 12:
                			del search_list[12]
        			cache.set('Search', str(search_list))
			except:
				pass
		else:
			content = url
                req = urllib2.Request(content)
                req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
                response = urllib2.urlopen(req)
                link=response.read()
                response.close()
		name=re.compile('<a class="image" title="(.+?)"').findall(link)
		try:
			name[0]
			name=unique(name)
		except:
			name=re.compile('class="name".+?>(.+?)</a>').findall(link)
		thumbnail=re.compile('<img src="(.+?)".+?mediakey=').findall(link)
		thumbnail=unique(thumbnail)
		nextpage=re.compile('</ul></div><a href="(.+?)".+?<span>Next</span>').findall(link)
		try:
			nextpage=nextpage[0]
			nextpage=nextpage.replace('&amp;','&')
			nextpage=nextpage.replace(' ','+')
		except:
			pass
		mylist=zip((name),(thumbnail))
		pDialog = xbmcgui.DialogProgress()
		pDialog.create('GodTube', 'Initializing Script...')
		try:
			percent=len(mylist)
			percent=100/float(percent)
			percent=round(percent)
			percent=int(percent)
			totalpercent=0
		except:
			pass
		for name,thumbnail in mylist:
			if "_" in thumbnail:
				url = re.compile('(.+?_.+?)_').findall(thumbnail)
			if "-" in thumbnail:
				url = re.compile('(.+?)-').findall(thumbnail)
			url = url[0]				
			try:
  				urllib2.urlopen(urllib2.Request(url+'.mp4'))
				url = url+'.mp4'
			except:
				url=url+'.flv'
			if "/resource/user/profile" not in thumbnail:
				totalpercent=totalpercent+percent
				pDialog.update(totalpercent, translation(30103)+'...')
				name=name.replace('&quot;','"')
                        	addLink(name,url,thumbnail)
                if nextpage:
                        addDir('More',nextpage,1,next_thumb)

        else:
		PREVIOUS()


##############################################################################################################

def Search(url):
	search_list=[]
	search_hist = cache.get('Search')
	try:
                search_list = eval(search_hist)
	except:
		search_list.insert(0, search_hist)	
        addDir(translation(30106)+'...',base_url+'/search/?q=',1, search_thumb, search_function=1)
	try:
		for name in search_list:
			if not name == '':
				title = name.replace('+',' ')
				addDir(title,base_url+'/search/?q='+str(name),1, search_thumb, search_function=0)
	except:
		pass	

##############################################################################################################

def Categories(url):
	addDir(translation(30003),base_url+'/artists-directory/',4,'')
	addDir(translation(30004),base_url+'/music-videos/',1,browse_thumb)	
	addDir(translation(30005),base_url+'/ministry-videos/',1,browse_thumb)
	addDir(translation(30006),base_url+'/inspirational-videos/',1,browse_thumb)
	addDir(translation(30007),base_url+'/comedy-videos/',1,browse_thumb)
	addDir(translation(30008),base_url+'/cute-videos/',1,browse_thumb)
	addDir(translation(30009),base_url+'/movies/',1,browse_thumb)
	addDir(translation(30101),base_url+'/sermon-videos/',1,browse_thumb)
	addDir(translation(30102),base_url+'/espa%C3%B1ol-videos/',1,'')

##################################################################################################################################

def ArtistDirectory(url):
	try:	
		req = urllib2.Request(url)
        	req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
		response = urllib2.urlopen(req)
		link=response.read()
		response.close()
		match=re.compile('<a href="http://www.godtube.com/artist/(.+?)">').findall(link)
		name=re.compile('<span class="ShowLink" >(.+?)</span>').findall(link)
		mylist=zip((match),(name))
		for match,name in mylist:
			addDir(name,base_url+'/artist/'+match,1,'http://www.godtube.com/resource/user/profile/'+match[:-1]+'.jpg')
	except:
        	xbmc.executebuiltin('XBMC.Notification("%s","%s",%d,"%s")' %
                            	(translation(30104), translation(30105),5000, timeout_thumb))
		PREVIOUS()
	

##############################################################################################################

def unique(a):
    seen = set()
    return [seen.add(x) or x for x in a if x not in seen]

##################################################################################################################################

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

##################################################################################################################################

def PREVIOUS():
	xbmc.executebuiltin('Action(Back)')

##################################################################################################################################
	

def addLink(name,url,iconimage):
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name } )
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=liz)
        return ok

##################################################################################################################################

def addDir(name,url,mode,iconimage,search_function=0):
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)+"&search_function="+urllib.quote_plus(str(search_function))
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name } )
        xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)
        return ok

##################################################################################################################################
        
              
params=get_params()
url=None
name=None
mode=None
search_function=None

try:
        url=urllib.unquote_plus(params["url"])
except:
        pass
try:
        mode=int(params["mode"])
except:
        pass
try:
        search_function=int(params["search_function"])
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
        MAIN()
elif mode==1:
        print ""+url
        ADDLINKS(url)
elif mode==2:
        print ""+url
        Search(url)
elif mode==3:
        print ""+url
        Categories(url)
elif mode==4:
        print ""+url
        ArtistDirectory(url)
if mode==1:
	xbmc.executebuiltin("Container.SetViewMode(500)")
if mode==None:
	xbmc.executebuiltin("Container.SetViewMode(50)")
if mode>=2:
	xbmc.executebuiltin("Container.SetViewMode(50)")
xbmcplugin.endOfDirectory(int(sys.argv[1]))
