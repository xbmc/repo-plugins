import urllib,urllib2,re,xbmcplugin,xbmcgui,xbmcaddon
from time import strftime

__settings__ = xbmcaddon.Addon(id='plugin.video.jupiterbroadcasting')
__language__ = __settings__.getLocalizedString

def CATEGORIES():
	plugins = {}
	plugins[__language__(30006)] = {
		'feed': 'http://feeds2.feedburner.com/AllJupiterVideos?format=xml',
		'image': 'http://images2.wikia.nocookie.net/__cb20110118004527/jupiterbroadcasting/images/2/24/JupiterBadgeGeneric.jpg',
		'plot': 'All the latest videos from Jupiter Broadcasting.',
		'genre': 'Technology'
	}
	plugins[__language__(30000)] = {
		'feed': 'http://feeds.feedburner.com/computeractionshowvideo?format=xml',
		'image': 'http://www.jupiterbroadcasting.com/images/LAS-VIDEO.jpg',
		'plot': 'The Linux Action Show covers the latest news in free and open source software, especially Linux.',
		'genre': 'Technology'
	}
	plugins[__language__(30001)] = {
		'feed': 'http://feeds2.feedburner.com/jupiterbeeristasty-hd?format=xml',
		'image': 'http://www.jupiterbroadcasting.com/images/beeristasty/BeerisTasty-iTunesBadgeHD.png',
		'plot': 'Finding interesting combinations of food and beer.',
		'genre': 'Technology'
	}
	plugins[__language__(30002)] = {
		'feed': 'http://feeds.feedburner.com/stokedhd?format=xml',
		'image': 'http://www.jupiterbroadcasting.com/images/STOked-BadgeHD.png',
		'plot': 'All the news about Star Trek Online you would ever need.',
		'genre': 'Technology'
	}
	plugins[__language__(30003)] = {
		'feed': 'http://feeds.feedburner.com/lotsovideo?format=xml',
		'image': 'http://www.jupiterbroadcasting.com/images/LOTSOiTunesVideo144.jpg',
		'plot': 'Video games, reviews and coverage.',
		'genre': 'Technology'
	}
	plugins[__language__(30004)] = {
		'feed': 'http://feeds.feedburner.com/jupiternitehd?format=xml',
		'image': 'http://www.jupiterbroadcasting.com/images/JANBADGE-LVID.jpg',
		'plot': 'Jupiter Broadcasting hooliganisms covered in front of a live audience on the intertubes.',
		'genre': 'Technology'
	}
	plugins[__language__(30005)] = {
		'feed': 'http://feeds.feedburner.com/ldf-video?format=xml',
		'image': 'http://www.jupiterbroadcasting.com/images/LDF-FullStill144x139.jpg',
		'plot': 'Bryan takes a peek into alien life.',
		'genre': 'Technology'
	}
	plugins[__language__(30007)] = {
		'feed': 'http://feeds.feedburner.com/MMOrgueHD?format=xml',
		'image': 'http://www.jupiterbroadcasting.com/images/MMOrgueBadgeHD144.jpg',
		'plot': 'The MMOrgue is a show presented by Jeremy about Massively Multiplayer Online (MMO) games.',
		'genre': 'Technology'
	}
	plugins[__language__(30008)] = {
		'feed': 'http://feeds.feedburner.com/techsnaphd?format=xml',
		'image': 'http://images3.wikia.nocookie.net/jupiterbroadcasting/images/d/d6/Techsnapcenter.jpg',
		'plot': 'TechSNAP is a show about technology news hosted by Chris Fisher and Allan Jude which records live on Thursdays and is released on the following Monday.',
		'genre': 'Technology'
	}
	plugins[__language__(30009)] = {
		'feed': 'http://feeds.feedburner.com/scibytehd?format=xml',
		'image': 'http://www.jupiterbroadcasting.com/images/SciByteBadgeHD.jpg',
		'plot': 'SciByte is a show about science topics presented by Heather and Jeremy.',
		'genre': 'Science'
	}
	# TODO: Add FauxShow?
	#plugins[__language__(30011)] = {
	#	'feed': 'http://blip.tv/fauxshow/rss',
	#	'image': 'http://images3.wikia.nocookie.net/__cb20110422002134/jupiterbroadcasting/images/0/0b/Fauxshow.jpg',
	#	'plot': 'The FauxShow is not a real show, but a social experience. Unlike most of the shows on the network, the FauxShow has no defined subject and the topic varies week to week.',
	#	'genre': 'Humour'
	#}
	x = 1
	for name, data in plugins.iteritems():
		data['count'] = x
		x = x + 1
		addDir(name, data['feed'], 1, data['image'], data)
	#TODO: Add Jupiter Broadcasting Live via Justin.tv?
	#addLink(__language__(30010), 'http://www.justin.tv/widgets/live_embed_player.swf?channel=jupiterbroadcasting', '', '', 'http://www.jupiterbroadcasting.com/wp-content/themes/ondemand/images/logo.jpg')

def INDEX(name, url):
	import feedparser
	data = feedparser.parse(url)
	x = 1
	for item in data.entries:
		info = {}
		# The title
		title = info['title'] = str(x) + '. ' + item.title
		# Process the enclosures
		if hasattr(item, 'enclosures'):
			# Video URL
			video = getattr(item.enclosures[0], 'href', 0);
			if video == 0:
				video = getattr(item.enclosures[0], 'url', '')
			size = getattr(item.enclosures[0], 'length', 0)
			info['size'] = int(size)
		info['count'] = x
		# Date
		date = info['date'] = strftime("%d.%m.%Y", item.updated_parsed)
		info['plot'] = re.sub(r'<[^>]*?>', '', item.summary)
		info['plotoutline'] = item.subtitle
		info['director'] = item.author
		info['tvshowtitle'] = name
		addLink(title, video, date, '', info)
		x = x + 1

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

# Info takes Plot, date, size
def addLink(name, url, date, iconimage, info):
        ok=True
        liz=xbmcgui.ListItem(name, date, iconImage=iconimage, thumbnailImage=iconimage)
        liz.setInfo( type="video", infoLabels=info )
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=liz)
        return ok

def addDir(name,url,mode,iconimage, info):
	u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
	ok=True
	info["Title"] = name
	liz=xbmcgui.ListItem(name, iconImage=iconimage, thumbnailImage=iconimage)
	liz.setInfo(type="video", infoLabels=info)
	ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)
	return ok

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
        CATEGORIES()

elif mode==1:
        print ""+url
        INDEX(name, url)


xbmcplugin.endOfDirectory(int(sys.argv[1]))
