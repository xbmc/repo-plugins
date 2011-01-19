import urllib,urllib2,re,xbmcplugin,xbmcgui,sys,os,xbmc
		
###################################
#########  Class Day[9]  ##########
###################################
				
class Day9:	
		
	def categories(self):
		self.addDir('Top 10 Videos','http://day9tv.blip.tv/posts?keywords=&nsfw=dc&sort=popularity&pagelen=10',2,'','')
		self.addDir('Latest Videos','http://day9tv.blip.tv/posts',2,'','')
		self.addDir('Search Videos','http://day9tv.blip.tv/search?q=day9tv+',2,'','')

	def addLink(self,name,url,iconimage,duration):
		ok=True
		liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
		liz.setInfo( type="Video", infoLabels={ "Title": name , "Duration": duration } )
		xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=liz)
		
	def addDir(self,name,url,mode,iconimage,duration):
		u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)+"&duration="+urllib.quote_plus(duration)
		ok=True
		liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
		liz.setInfo( type="Video", infoLabels={ "Title": name , "Plot": duration} )
		xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)
		
	def index(self,url):
		if url=='http://day9tv.blip.tv/search?q=day9tv+' or url == 'http://djwheat.blip.tv/search?q=djwheat+':
			keyboard = xbmc.Keyboard('')
			keyboard.doModal()			
			url+=keyboard.getText()+'&pagelen=500'
		req = urllib2.Request(url)
		req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
		response = urllib2.urlopen(req)
		link=response.read()
		response.close()
		info=re.compile('<a href="(.+?)" title="Watch (.+?)">\n\t\t\t\t\n\t\t\t\t  <img class="thumb" src="(.+?)"').findall(link)
		duration=re.compile('<span class="EpisodeDuration">Duration: (.+?)</span>').findall(link)
		for i in range(len(info)):
			self.addDir(info[i][1],'http://day9tv.blip.tv'+info[i][0],3,info[i][2],duration[i])
			
	def videolinks(self,url,name,duration):
		req = urllib2.Request(url)
		req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
		response = urllib2.urlopen(req)
		link=response.read()
		response.close()
		info=re.compile('<option value="/file/.+?filename=(.+?)(...)">(.+?) &mdash;').findall(link)
		thumb=re.compile('<link rel="videothumbnail" href="(.+?)" />').findall(link)
		for i in range(len(info)):
			if info[i][2] == 'Blip SD' or info[i][1] == 'FLV' or info[i][1] == 'flv':
				self.addLink('SD - '+name,'http://blip.tv/file/get/'+info[i][0]+info[i][1],thumb[0],duration)
			if info[i][2] == 'Blip HD 720':
				self.addLink('HD - '+name,'http://blip.tv/file/get/'+info[i][0]+info[i][1],thumb[0],duration)
				
	def get_params(self):
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