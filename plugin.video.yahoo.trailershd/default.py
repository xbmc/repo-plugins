import xbmc, xbmcgui, xbmcplugin, urllib2, urllib, re, string, sys, os, traceback, time, pickle, xbmcaddon
import threading

__plugin__ = 'Yahoo Movie Trailers (HD)'
__author__ = 'EbiL <rmrfworld@gmail.com>'
__url__ = 'git://github.com/rmrfworld/plugin.video.yahoo.trailershd.git'
__date__ = '3 Jul 2012'
__version__ = '1.1.0'
__settings__ = xbmcaddon.Addon(id='plugin.video.yahoo.trailershd')

if not os.path.exists(__settings__.getAddonInfo('profile')): os.makedirs(__settings__.getAddonInfo('profile'))

responses=[]
vresponses=[]
class MyHandler(urllib2.HTTPHandler):
    def http_response(self, req, response):
	blah=""
	global responses
	blah=response.read()
	responses.append(blah)
        return response

class VMyHandler(urllib2.HTTPHandler):
    def http_response(self, req, response):
	blah=""
	global vresponses
	blah=response.read()
	vresponses.append(blah)
        return response

def load():
#download top of box office links (tbo)
	url = "http://movies.yahoo.com/box-office/"
	req = urllib2.Request(url)
	req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
	response = urllib2.urlopen(req)
	link=response.read()
	response.close()
	tbo=re.compile('<td class="rank">.+?</td><td class="rankpast">.+?</td><td class="movie-image"><a href=.+? style=".+?" class="lzbg"></a></td><td class="title"><div><a href="(.+?)" >(.+?)</a></div>').findall(link)
	
#download opening this weekend (otw)
	url = "http://movies.yahoo.com/in-theaters/"
	req = urllib2.Request(url)
	req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
	response = urllib2.urlopen(req)
	link=response.read()
	response.close()
	otw=re.compile('<div class="info"><a href="(.+?)" class="title">(.+?)</span></a><em class="movie-info">').findall(link)

#download coming soon (cs)
	url = "http://movies.yahoo.com/coming-soon/"
	req = urllib2.Request(url)
	req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
	response = urllib2.urlopen(req)
	link=response.read()
	response.close()
	match=re.compile('<div class="info"><a href="(.+?)" class="title">(.+?)</span></a><em class="movie-info">').findall(link)
	match1=re.compile('<div class="yom-mod yom-top-list yom-top-list-movie yom-top-list-dotted"><div class="hd"><h3>Further Out</h3></div><div class="bd"><ul><li class="first show-image"><div class="media-item">(.+?)</div></li></ul></div></div>').findall(link)
	cs1=re.compile('<div class="item-title"><a href="(.+?)" >(.+?)</a></div><em class="item-detail">').findall(match1[0])
	cs = match + cs1

#cacheing info for multiple use
	f = open(os.path.join( __settings__.getAddonInfo('profile'), "tbo"),'wb')
	pickle.dump(tbo, f)
	f.close()
	f = open(os.path.join( __settings__.getAddonInfo('profile'), "otw"),'wb')
	pickle.dump(otw, f)
	f.close()
	f = open(os.path.join( __settings__.getAddonInfo('profile'), "cs"),'wb')
	pickle.dump(cs, f)
	f.close()

def getDetails(link):
	ithumb=re.compile('<div class="yom-mod yom-ent-image"><div class="bd"><div class="yom-ent-image-frm" style=".+?"><img src="(.+?)" alt=".+?">').findall(link)
	iplot=re.compile('<h3>Synopsis</h3></div>.+?<div class=.+?>(.+?)</div>').findall(link)
	ititle=re.compile('<h1 property="name">(.+?)<span class="year">.+?</span></h1>').findall(link)
	if len(ititle)<1:
		iinfo = ['None','','']
	else:
		iinfo = ititle[0], iplot[0], ithumb[0]		
	return iinfo

def getVDetails(vlink):
	ititle=re.compile('<h1 property="name">(.+?)<span class="year">.+?</span></h1>').findall(vlink)
	ivid=re.compile('<param name="flashVars" value="vid=(.+?)&locale="></param>').findall(vlink)
	if len(ititle)<1:
		vvid = ['None','']
	elif len(ivid)<1:
		vvid = ['None','']
	else:
		vvid = ititle[0], ivid[0]		
	return vvid

def addTitles(tbo):
	for url,name in tbo:
		o = urllib2.build_opener(MyHandler())
		iurl = "http://movies.yahoo.com" + url + "/"
		t = threading.Thread(target=o.open, args=(iurl,))
		t.start()
		vo = urllib2.build_opener(VMyHandler())
		vurl = "http://movies.yahoo.com" + url + "/trailers/"
		vt = threading.Thread(target=vo.open, args=(vurl,))
		vt.start()
	pDialog = xbmcgui.DialogProgress()
	ret = pDialog.create('Yahoo Movie Trailers', 'Getting Trailers...')
	while (threading.activeCount()>1):
		f = (float(len(tbo)*2)-float(threading.activeCount()-1))/float(len(tbo)*2)
		f = int(f*100)
		pDialog.update(f)
	pDialog.close()
	iinfo=[]
	for link in responses:
		if (link!=''):
			blah = getDetails(link)
			iinfo.append(blah)
	vinfo=[]
	for vlink in vresponses:
		if (vlink!=''):
			blah = getVDetails(vlink)
			vinfo.append(blah)
	finfo=[]
	for title,p,t in iinfo:
		for vtitle,vid in vinfo:
			if(title!='None'):
				if(vtitle==title):
					blah=title,p,t,vid
					finfo.append(blah)
	for title,plot,thumb,vid in finfo:
			li=xbmcgui.ListItem(title, iconImage=thumb, thumbnailImage=thumb)
			li.setInfo( type="Video", infoLabels={ "Title": title, "Plot": plot } ) # "Genre": genre, "Premiered": rdate, "Mpaa": mpaa } )
			li.setProperty('IsPlayable', 'true')
			u=sys.argv[0]+"?mode=2&name="+urllib.quote_plus(title)+"&url="+urllib.quote_plus(vid)
			li.addContextMenuItems([('Theater Showtimes', 'XBMC.RunPlugin('+sys.argv[0]+'?mode=3&name='+urllib.quote_plus(title)+')',)])
			xbmcplugin.addDirectoryItem(int(sys.argv[1]),u,li,False)

def catlist():
#categories...
	tb = os.path.join( __settings__.getAddonInfo('path'), "icon.png")
	opts = ["Top Box Office","Opening This Week","Coming Soon"]
	for name in opts:
		li=xbmcgui.ListItem(name, iconImage=tb, thumbnailImage=tb)
		u=sys.argv[0]+"?mode=1&name="+urllib.quote_plus("".join(re.findall('[A-Z]',name)))
		xbmcplugin.addDirectoryItem(int(sys.argv[1]),u,li,True,len(opts))

def seclist(name):
#fill selection list with titles depending on what category was chosen
	if name=='TBO':
		f = open(os.path.join( __settings__.getAddonInfo('profile'), "tbo"),'rb')
		tbo = pickle.load(f)
		f.close()
		addTitles(tbo)
	elif name=='OTW':
		f = open(os.path.join( __settings__.getAddonInfo('profile'), "otw"),'rb')
		otw = pickle.load(f)
		f.close()
		addTitles(otw)
	elif name=='CS':
		f = open(os.path.join( __settings__.getAddonInfo('profile'), "cs"),'rb')
		cs = pickle.load(f)
		f.close()		
		addTitles(cs)
	
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
			back = dialog.yesno(theater[ret], name, "", times[ret].replace('&nbsp',''), 'Done', 'Back');

def resolveLink(url,name):
	li=xbmcgui.ListItem(name, path = url)
	li.setInfo( type="Video", infoLabels={ "Title": name } )
	xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, li)
	return True

def playVideo(url, name):
	
	res = __settings__.getSetting('res')
	if (res=='720_2Mbps'):
		rez = "2000"
	elif (res=='720_3Mbps'):
		rez = "3008"
	elif (res=='1080'):	
		rez = "4000"
	else:
		rez = "1504"
	#link = re.sub('480',res,url) #replace default setting with user chosen resolution
	url = "http://cosmos.bcst.yahoo.com/rest/v2/pops;element=stream;bw=" + rez + ";tech=mp4;id=" + url	
	req = urllib2.Request(url)
	req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
	req.add_header('Referer', 'http://movies.yahoo.com/')
	response = urllib2.urlopen(req)
	link=response.read()
	response.close()
	sid=re.compile('sid=\'(.+?)\'').findall(link)
	vurl = "http://playlist.yahoo.com/makeplaylist.dll?sdm=web&pt=rd&sid=" + sid[0]
        resolveLink(vurl,name)
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
