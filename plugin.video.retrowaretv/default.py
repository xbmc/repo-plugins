import re, sys
import urllib, urllib2
import xbmcgui, xbmcplugin, xbmcaddon
import showEpisode

#Retroware TV, XBMC add-on

#@author: dethfeet
#@credits: Ricardo "Averre" Ocana Leal for the initial Version of the plugin

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
    shows_page = LoadPage(baseLink)
	
    regex_extract_shows = re.compile("Shows</a>\n<ul class=\"sub-menu\">(.*?)</ul>\n</li>\n</ul>\n</li>",re.DOTALL)
    shows_ul = regex_extract_shows.search(shows_page).group(1);
    
    regex_extract_show = re.compile("\n\t<li id=\".*?\" class=\".*?\"><a href=\"(.*?)\">(.*?)</a></li>");
    shows_li = regex_extract_show.findall(shows_ul)
    
    for show in shows_li:
        addDirectoryItem(show[1],{'action':"listVideos",'link' : show[0]},"")

def ListArchive():
    shows_page = LoadPage(baseLink)
	
    regex_extract_shows = re.compile("Archive</a>\n\t<ul class=\"sub-menu\">(.*?)</ul>\n</li>\n</ul>\n</li>",re.DOTALL)
    shows_ul = regex_extract_shows.search(shows_page).group(1);
    
    regex_extract_show = re.compile("\n\t\t<li id=\".*?\" class=\".*?\"><a href=\"(.*?)\">(.*?)</a></li>");
    shows_li = regex_extract_show.findall(shows_ul)
    
    for show in shows_li:
        addDirectoryItem(show[1],{'action':"listVideos",'link' : show[0]},"")


def listUserContent():
    addDirectoryItem(addon.getLocalizedString(30301),{'action':"listVideos",'link' : baseLink+"/category/usercontent/user-submission-of-the-week/"},"")
    addDirectoryItem(addon.getLocalizedString(30302),{'action':"listVideos",'link' : baseLink+"/category/usercontent/featured-user-content/"},"")
    addDirectoryItem(addon.getLocalizedString(30303),{'action':"listVideos",'link' : baseLink+"/category/usercontent/"},"")

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