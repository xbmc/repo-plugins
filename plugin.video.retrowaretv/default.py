import re, sys
import urllib, urllib2
import xbmcgui, xbmcplugin, xbmcaddon
import showEpisode

#Retroware TV, XBMC add-on

#@author: dethfeet
#@credits: Ricardo "Averre" Ocana Leal for the initial Version of the plugin
#@version: 1.1.3

addon = xbmcaddon.Addon(id='plugin.video.retrowaretv')

baseLink = "http://retrowaretv.com"

unwanteds = ['podcast', 'retrobeat']

thisPlugin = int(sys.argv[1])

def mainPage():
    addDirectoryItem(addon.getLocalizedString(30000),{'action':"listVideos","link":baseLink+"/category/shows/"})
    addDirectoryItem(addon.getLocalizedString(30001),{'action':"listShows"})
    addDirectoryItem(addon.getLocalizedString(30002),{'action':"listUserContent",'link' : "http://retrowaretv.com/user-blogs/"})
    addDirectoryItem(addon.getLocalizedString(30003),{'action':"listArchive"})
        
def listShows():
    addDirectoryItem(addon.getLocalizedString(30101),{'action':"listVideos",'link' : baseLink+"/category/shows/16bitgems/"},baseLink+"/wp-content/uploads/2011/06/16bitsitebanner-300x84.png")
    addDirectoryItem(addon.getLocalizedString(30102),{'action':"listVideos",'link' : baseLink+"/category/shows/the-game-chasers/"},baseLink+"/wp-content/uploads/2012/06/gamechasersbanner2-300x108.png")
    addDirectoryItem(addon.getLocalizedString(30103),{'action':"listVideos",'link' : baseLink+"/category/shows/gamequickies/"},baseLink+"/wp-content/uploads/2011/06/gquickie.png")
    addDirectoryItem(addon.getLocalizedString(30104),{'action':"listVideos",'link' : baseLink+"/category/shows/gaminghistorian/"},baseLink+"/wp-content/uploads/2011/06/gaming-historian-banner1-300x76.gif")
    addDirectoryItem(addon.getLocalizedString(30105),{'action':"listVideos",'link' : baseLink+"/category/shows/hvgn/"},baseLink+"/wp-content/uploads/2011/06/HVGN-2.0-sizeb1-300x112.png")
    addDirectoryItem(addon.getLocalizedString(30106),{'action':"listVideos",'link' : baseLink+"/category/shows/thehumansarecoming/"},baseLink+"/wp-content/uploads/2012/07/humans-are-coming-logo-3-gray-red-FINAL-300x287.png")
    addDirectoryItem(addon.getLocalizedString(30107),{'action':"listVideos",'link' : baseLink+"/category/shows/lazy-game-reviews/"},baseLink+"/wp-content/uploads/2012/06/LGRbg4b-300x168.png")
    addDirectoryItem(addon.getLocalizedString(30108),{'action':"listVideos",'link' : baseLink+"/category/shows/letsget/"},baseLink+"/wp-content/uploads/2011/06/letsgetbanner-300x189.png")
    addDirectoryItem(addon.getLocalizedString(30109),{'action':"listVideos",'link' : baseLink+"/category/shows/patnespunk/"},baseLink+"/wp-content/uploads/2011/06/PatNESLogo-300x196.jpg")
    addDirectoryItem(addon.getLocalizedString(30110),{'action':"listVideos",'link' : baseLink+"/category/shows/pixelstoplastic/"},baseLink+"/wp-content/uploads/2011/06/P2P-Banner-300x128.gif")
    addDirectoryItem(addon.getLocalizedString(30111),{'action':"listVideos",'link' : baseLink+"/category/shows/retroactive/"},baseLink+"/wp-content/uploads/2011/06/retroactiverwtvbanner-300x95.png")
    addDirectoryItem(addon.getLocalizedString(30112),{'action':"listVideos",'link' : baseLink+"/category/shows/rwtvshow/"},baseLink+"/wp-content/uploads/2011/06/rwtvthe-show-logo.png")
    addDirectoryItem(addon.getLocalizedString(30113),{'action':"listVideos",'link' : baseLink+"/category/shows/soldseparately/"},baseLink+"/wp-content/uploads/2011/06/sold-separately-banner.gif")
    addDirectoryItem(addon.getLocalizedString(30114),{'action':"listVideos",'link' : baseLink+"/category/shows/vgto/"},baseLink+"/wp-content/uploads/2012/06/vgtobanner-300x72.png")
    addDirectoryItem(addon.getLocalizedString(30115),{'action':"listVideos",'link' : baseLink+"/category/shows/the-video-game-years/"},baseLink+"/wp-content/uploads/2012/02/tvgypagebanner.png")
    addDirectoryItem(addon.getLocalizedString(30116),{'action':"listVideos",'link' : baseLink+"/category/shows/video-game-knowledge/"},baseLink+"/wp-content/uploads/2011/06/videogame-knowledge-banner.gif")
    addDirectoryItem(addon.getLocalizedString(30117),{'action':"listVideos",'link' : baseLink+"/category/shows/you-can-play-this-2/"},baseLink+"/wp-content/uploads/2012/06/ycpt-banner-e1340208312357.png")

def ListArchive():
    addDirectoryItem(addon.getLocalizedString(30201),{'action':"listVideos",'link' : baseLink+"/category/archives/boomstick/"},baseLink+"/wp-content/uploads/2011/06/Menu-Button-Boomstick.gif")
    addDirectoryItem(addon.getLocalizedString(30202),{'action':"listVideos",'link' : baseLink+"/category/archives/jam-enslaver/"},baseLink+"/wp-content/uploads/2011/06/jamenslaver1.png")
    addDirectoryItem(addon.getLocalizedString(30203),{'action':"listVideos",'link' : baseLink+"/category/archives/when-worlds-collide/"},"")

def listUserContent():
    addDirectoryItem(addon.getLocalizedString(30301),{'action':"listVideos",'link' : baseLink+"/category/user-submissions/rdubspotlight/"},"")
    addDirectoryItem(addon.getLocalizedString(30302),{'action':"listVideos",'link' : baseLink+"/category/user-submissions/"},"")

def listVideos(url):
	link = LoadPage(url)
	
	_regex_extractEpisode = re.compile("<div class=\"postarea\">.*?src=\"(.*?)\".*?href=\"(.*?)\".*?>(.*?)</a>.*?<div class=\"postexcerpt\">(.*?)</div>.*?<hr />",re.DOTALL)
	_regex_extractNextPage = re.compile("<li><a href=\"(.*)\">&gt;</a></li>")
    
	for videoItem in _regex_extractEpisode.finditer(link):
		name = videoItem.group(3)
		url = videoItem.group(2)
		description = videoItem.group(4)
		thumbnail = videoItem.group(1)
		name = remove_html_special_chars(name)
		addDirectoryItem(name,{'action':"playEpisode",'link':url},thumbnail,False)
	
	nextPageItem = _regex_extractNextPage.search(link)
	if nextPageItem is not None:
		addDirectoryItem(addon.getLocalizedString(30004),{'action':"listVideos",'link' : nextPageItem.group(1)},"")

def playEpisode(url):
    episode_page = LoadPage(url)
    showEpisode.showEpisode(episode_page)

def LoadPage(url):
    print url
    req = urllib2.Request(url)
    req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
    response = urllib2.urlopen(req)
    link = response.read()
    return link

def remove_html_special_chars(input):
    input = input.replace("&#8211;","-")
    input = input.replace("&#8217;","'")#\x92
    input = input.replace("&#039;",chr(39))# '
    input = input.replace("&#038;",chr(38))# &
    input = input.replace("&amp;",chr(38))# &
    input = input.replace(r"&quot;", "\"")
    input = input.replace(r"&apos;", "\'")
    input = input.replace(r"&#8216;", "\'")
    input = input.replace(r"&#8217;", "\'")
    input = input.replace(r"&#8230;", "...")
    return input

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

def addDirectoryItem(name, parameters={}, pic="", folder=True):
    li = xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=pic)
    if not folder:
        li.setProperty('IsPlayable', 'true')
    url = sys.argv[0] + '?' + urllib.urlencode(parameters)
    return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=li, isFolder=folder)

if not sys.argv[2]:
    mainPage()
else:
    params=get_params()
    if params['action'] == "listShows":
        listShows()
    elif params['action'] == "listArchive":
        ListArchive()
    elif params['action'] == "listUserContent":
        listUserContent()
    elif params['action'] == "listLatest":
        ListLatest(urllib.unquote(params['link']))
    elif params['action'] == "listVideos":
        listVideos(urllib.unquote(params['link']))
    elif params['action'] == "playEpisode":
        playEpisode(urllib.unquote(params['link']))
    else:
        mainPage()

xbmcplugin.endOfDirectory(int(sys.argv[1]))