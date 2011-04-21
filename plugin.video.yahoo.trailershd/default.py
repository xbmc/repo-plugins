import xbmc, xbmcgui, xbmcplugin, urllib2, urllib, re, string, sys, os, traceback, time, pickle, xbmcaddon

__plugin__ = 'Yahoo Movie Trailers (HD)'
__author__ = 'EbiL <rmrfworld@gmail.com>'
__url__ = 'git://github.com/rmrfworld/Yahoo-Movie-Trailers--HD-.git'
__date__ = '20 Apr 2011'
__version__ = '1.0.0'
__settings__ = xbmcaddon.Addon(id='plugin.video.yahoo.trailershd')

if not os.path.exists(__settings__.getAddonInfo('profile')): os.makedirs(__settings__.getAddonInfo('profile'))

def load():
#download new trailer links
	url = "http://movies.yahoo.com/feature/hdtrailers.html"
	req = urllib2.Request(url)
	req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
	response = urllib2.urlopen(req)
	link=response.read()
	response.close()
	match=re.compile('(?s)<dt class="a-m-t">(.+?) - (.+?)</dt>\n<dd class="a-m-d">\n<div class="bd">\n<div class="smallThumb">\n<div class="shadow">\n<a href=".+?"><img src="(.+?)" border="0" align="left" /></a>\n</div>\n</div>\n<div>\n(.+?)\n<br /><br />\n.+?<br />\n(.+?)<br />\n(.+?)<br />\n.+?<br />\n<br /><br />\n<div class="trailer-wrapper">\n<div class="clip1">.+?\n<ul class="hd-btn-wrapper-small">\n<li><a class="hd-nav-button" href="(.+?)"></a>').findall(link)
	
#download old trailer links
	url = "http://movies.yahoo.com/feature/hdtrailers_archive.html"
	req = urllib2.Request(url)
	req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
	response = urllib2.urlopen(req)
	link=response.read()
	response.close()
	match1=re.compile('<dt class="a-m-t">(.+?) - (.+?)</dt>\n<dd class="a-m-d">\n<div class="bd">\n<div class="smallThumb">\n<div class="shadow">\n<a href=".+?"><img src="(.+?)" border="0" align="left" /></a>\n</div>\n</div>\n<div>\n(.+?)\n<br /><br />\n.+?<br />\n(.+?)<br />\n(.+?)<br />\n.+?<br />\n<br /><br />\n<div class="trailer-wrapper">\n<div class="clip1">.+?\n<ul class="hd-btn-wrapper-small">\n<li><a class="hd-nav-button" href="(.+?)"></a>').findall(link)

#download coming soon (cs), opening this week (otw), top at the box office (tbo) info
	url = "http://movies.yahoo.com"
	req = urllib2.Request(url)
	req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
	response = urllib2.urlopen(req)
	link=response.read()
	response.close()	

#cacheing info for multiple use
	tbo=re.compile('<li.+?id="tbo_.+?"><a href="(.+?)"><strong>.+?</strong><span><b>(.+?)</b></span></a></li>').findall(link)
	f = open(os.path.join( __settings__.getAddonInfo('profile'), "tbo"),'wb')
	pickle.dump(tbo, f)
	f.close()
	otw=re.compile('<li.+?id="otw_.+?"><a href="(.+?)"><span>&bull;</span><b>(.+?)</b></a></li>').findall(link)
	f = open(os.path.join( __settings__.getAddonInfo('profile'), "otw"),'wb')
	pickle.dump(otw, f)
	f.close()
	cs=re.compile('<li.+?id="cs_.+?"><a href="(.+?)"><span>&bull;</span><b>(.+?)</b></a></li>').findall(link)
	f = open(os.path.join( __settings__.getAddonInfo('profile'), "cs"),'wb')
	pickle.dump(cs, f)
	f.close()
	allmovies = match + match1
	f = open(os.path.join( __settings__.getAddonInfo('profile'), "allmovies"),'wb')
	pickle.dump(allmovies, f)
	f.close()

def catlist():
#categories...
	tb = os.path.join( __settings__.getAddonInfo('path'), "icon.png")
	opts = ["Top Box Office","Opening This Week","Coming Soon","All"]
	for name in opts:
		li=xbmcgui.ListItem(name, iconImage=tb, thumbnailImage=tb)
		u=sys.argv[0]+"?mode=1&name="+urllib.quote_plus("".join(re.findall('[A-Z]',name)))
		xbmcplugin.addDirectoryItem(int(sys.argv[1]),u,li,True,len(opts))

def seclist(name):
#fill selection list with titles depending on what category was chosen
	f = open(os.path.join( __settings__.getAddonInfo('profile'), "allmovies"),'rb')
	allmovies = pickle.load(f)
	f.close()
	if name=='TBO':
		f = open(os.path.join( __settings__.getAddonInfo('profile'), "tbo"),'rb')
		tbo = pickle.load(f)
		f.close()
		for date,title,thumb,plot,genre,release,vurl in allmovies:
			fdate = re.sub('/','.',date)
			year = '20' + fdate[-2:]
			fdate = fdate[:6] + year
			temp = re.compile('(.+?) ([1-9]{1,2}).+?, (.+?) .+?').findall(release)
			if (len(temp)<1):
				rdate=""
			else: 
				try: 
					temp = time.strptime(temp[0][0][:3]+' '+temp[0][1]+' '+temp[0][2], "%b %d %Y")
					rdate = time.strftime("%Y-%m-%d", temp)
					year = time.strftime("%Y", temp)
				except ValueError:
					rdate=""
			for infolink, t in tbo:
				if (title==t): #matching allmovie titles with tbo titles
					li=xbmcgui.ListItem(title, iconImage=thumb, thumbnailImage=thumb)
					li.setInfo( type="Video", infoLabels={ "date": fdate, "Title": title, "plot": plot, "genre": genre, "year": int(year), "premiered": rdate } )
					li.setProperty('IsPlayable', 'true')
					u=sys.argv[0]+"?mode=2&name="+urllib.quote_plus(title)+"&url="+urllib.quote_plus(vurl)
					li.addContextMenuItems([('Theater Showtimes', 'XBMC.RunPlugin('+sys.argv[0]+'?mode=3&name='+urllib.quote_plus(title)+')',)])
					xbmcplugin.addDirectoryItem(int(sys.argv[1]),u,li,False)
	elif name=='OTW':
		f = open(os.path.join( __settings__.getAddonInfo('profile'), "otw"),'rb')
		otw = pickle.load(f)
		f.close()
		for date,title,thumb,plot,genre,release,vurl in allmovies:
			fdate = re.sub('/','.',date)
			year = '20' + fdate[-2:]
			fdate = fdate[:6] + year
			temp = re.compile('(.+?) ([1-9]{1,2}).+?, (.+?) .+?').findall(release)
			if (len(temp)<1):
				rdate=""
			else: 
				try: 
					temp = time.strptime(temp[0][0][:3]+' '+temp[0][1]+' '+temp[0][2], "%b %d %Y")
					rdate = time.strftime("%Y-%m-%d", temp)
					year = time.strftime("%Y", temp)
				except ValueError:
					rdate=""
			for infolink, t in otw:
				if (title==t): #matching allmovie titles with otw titles
					li=xbmcgui.ListItem(title, iconImage=thumb, thumbnailImage=thumb)
					li.setInfo( type="Video", infoLabels={ "date": fdate, "Title": title, "plot": plot, "genre": genre, "year": int(year), "premiered": rdate } )
					li.setProperty('IsPlayable', 'true')
					u=sys.argv[0]+"?mode=2&name="+urllib.quote_plus(title)+"&url="+urllib.quote_plus(vurl)
					li.addContextMenuItems([('Theater Showtimes', 'XBMC.RunPlugin('+sys.argv[0]+'?mode=3&name='+urllib.quote_plus(title)+')',)])
					xbmcplugin.addDirectoryItem(int(sys.argv[1]),u,li,False)
	elif name=='CS':
		f = open(os.path.join( __settings__.getAddonInfo('profile'), "cs"),'rb')
		cs = pickle.load(f)
		f.close()		
		for date,title,thumb,plot,genre,release,vurl in allmovies:
			fdate = re.sub('/','.',date)
			year = '20' + fdate[-2:]
			fdate = fdate[:6] + year
			temp = re.compile('(.+?) ([1-9]{1,2}).+?, (.+?) .+?').findall(release)
			if (len(temp)<1):
				rdate=""
			else: 
				try: 
					temp = time.strptime(temp[0][0][:3]+' '+temp[0][1]+' '+temp[0][2], "%b %d %Y")
					rdate = time.strftime("%Y-%m-%d", temp)
					year = time.strftime("%Y", temp)
				except ValueError:
					rdate=""
			for infolink, t in cs:
				if (title==t): #matching allmovie titles with cs titles
					li=xbmcgui.ListItem(title, iconImage=thumb, thumbnailImage=thumb)
					li.setInfo( type="Video", infoLabels={ "date": fdate, "Title": title, "plot": plot, "genre": genre, "year": int(year), "premiered": rdate } )
					li.setProperty('IsPlayable', 'true')
					u=sys.argv[0]+"?mode=2&name="+urllib.quote_plus(title)+"&url="+urllib.quote_plus(vurl)
					li.addContextMenuItems([('Theater Showtimes', 'XBMC.RunPlugin('+sys.argv[0]+'?mode=3&name='+urllib.quote_plus(title)+')',)])
					xbmcplugin.addDirectoryItem(int(sys.argv[1]),u,li,False,len(cs))
	elif name=='A':
		for date,title,thumb,plot,genre,release,vurl in allmovies:
			fdate = re.sub('/','.',date)
			year = '20' + fdate[-2:]
			fdate = fdate[:6] + year
			temp = re.compile('(.+?) ([1-9]{1,2}).+?, (.+?) .+?').findall(release)
			if (len(temp)<1):
				rdate=""
			else: 
				try: 
					temp = time.strptime(temp[0][0][:3]+' '+temp[0][1]+' '+temp[0][2], "%b %d %Y")
					rdate = time.strftime("%Y-%m-%d", temp)
					year = time.strftime("%Y", temp)
				except ValueError:
					rdate=""
			li=xbmcgui.ListItem(title, iconImage=thumb, thumbnailImage=thumb)
			li.setInfo( type="Video", infoLabels={ "date": fdate, "Title": title, "plot": plot, "genre": genre, "year": int(year), "premiered": rdate } )
			li.setProperty('IsPlayable', 'true')
			u=sys.argv[0]+"?mode=2&name="+urllib.quote_plus(title)+"&url="+urllib.quote_plus(vurl)
			xbmcplugin.addDirectoryItem(int(sys.argv[1]),u,li,False,len(allmovies))

def showtimes(name):
#thanks for the showtimes google
	res = __settings__.getSetting('zip')
	url = "http://www.google.com/movies?near="+res
	req = urllib2.Request(url)
	req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
	response = urllib2.urlopen(req)
	link=response.read()
	response.close()
	match=re.compile('(?s)<div class=theater>.+?<h2 class=name><a href=.+?>(.+?)</a></h2><div class=info>(.+?)</div></div></div><p class=clear></div></div>').findall(link)
	theater=[]
	times=[]
	found=0
	back=True
	for i in range(0,len(match)):
		shows = re.compile('(?s)<div class=movie><div class=name><a href=".+?">(.+?)</a>.+?<div class=times>(.+?)</div></div>').findall(match[i][1])
		for title,timeinfo in shows:
			if name.lower()[0:8]==title.lower()[0:8]:
				found=1
				theater[len(theater):] = [match[i][0]]	
				times[len(times):] = [re.compile(r'<[^<]*?/?>').sub('',timeinfo)]		
	while back==True:
		dialog = xbmcgui.Dialog()
		if found==0:
			back = dialog.yesno(name, "", "Showtimes not found", "", 'Done', 'Back');
			back = False
		else:
			ret = dialog.select(name, theater)
			dialog = xbmcgui.Dialog()
			back = dialog.yesno(theater[ret], name, "", times[ret].replace('&nbsp;',''), 'Done', 'Back');

def resolveLink(url,name):
	li=xbmcgui.ListItem(name, path = url)
	li.setInfo( type="Video", infoLabels={ "Title": name } )
	xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, li)
	return True

def playVideo(url, name):
	res = __settings__.getSetting('res')
	test=re.sub('480',res,url) #replace default setting with user chosen resolution
	req = urllib2.Request(test)
	req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
	req.add_header('Referer', 'http://movies.yahoo.com/')
	response = urllib2.urlopen(req)
	link=response.read()
	response.close()
	videourl=re.compile('<\?xml version="1.0"\?><\?quicktime type="application/x-quicktime-media-link"\?><embed src="(.+?)" autoplay="false" type="video/quicktime" controller="true" quitwhendone="false" cache="false" loop="false" name="test file"></embed>').findall(link)
        resolveLink(videourl[0],name)
	xbmc.sleep(200)

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
mode=None
name=None
url=None
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

if mode==None:
	load()
	catlist()
elif mode==1:
	seclist(name)
elif mode==2:
	playVideo(url, name)
elif mode==3:
	showtimes(name)

xbmcplugin.setContent(int(sys.argv[1]), 'Movies')
sortmethods = ( xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE, xbmcplugin.SORT_METHOD_VIDEO_TITLE, xbmcplugin.SORT_METHOD_DATE, xbmcplugin.SORT_METHOD_VIDEO_YEAR )
for sortmethod in sortmethods:	
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=sortmethod )	
xbmcplugin.endOfDirectory(int(sys.argv[1]))
