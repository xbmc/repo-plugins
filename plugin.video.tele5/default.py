import xbmcplugin
import xbmcgui

import sys
import urllib, urllib2
import re

thisPlugin = int(sys.argv[1])

baseUrl = "http://www.tele5.de/videos.html"

def mainPage():
    page = load_page(baseUrl)
    _regex_extractShows = re.compile("<div class=\"videosGesamt\">(.*?)</div>", re.DOTALL)
    shows = _regex_extractShows.search(page).group(1)

    _regex_extractShow = re.compile("<a href=\"(.*?)\" >.*?<img src=\"(.*?)\".*?/>.*?<h3>(.*?)</h3>.*?</a>",re.DOTALL)
    
    for show in _regex_extractShow.finditer(shows):
        link = show.group(1)
        img = show.group(2)
        title = show.group(3)
        addDirectoryItem(title, parameters={"action":"show", "link":link}, pic=img, folder=True)
    xbmcplugin.endOfDirectory(thisPlugin)

def showPage(link):
    link = urllib.unquote(link)
    css_class = urllib.unquote(link)[1:]

    page = load_page(link)
    
    _regex_extractEpisodes = re.compile("<div class=\"videosGesamt\">(.*?)</div>", re.DOTALL)
    episodes = _regex_extractEpisodes.search(page).group(1)
    
    _regex_extractEpisode = re.compile("<a href=\"(.*?)\">.*?<img src=\"(.*?)\".*?/>.*?<h3>(.*?)</h3>.*?</a>",re.DOTALL)
    for episode in _regex_extractEpisode.finditer(episodes):
        img = episode.group(2)
        title = episode.group(3).replace("<br>"," ")
        addDirectoryItem(title, parameters={"action":"episode", "link":episode.group(1)}, pic=img, folder=False)
    xbmcplugin.endOfDirectory(thisPlugin)

def episodePage(link):
    link = urllib.unquote(link)
    page = load_page(link)

    #medianac.nacamar.de
    _regex_extractVideoId = re.compile("<param name=\"movie\" value=\".*?/(0_[a-z0-9]*)\" />")
    videoIdRe = _regex_extractVideoId.search(page)
    if videoIdRe:
        videoId = videoIdRe.group(1)
        
        videoUrl = ""
        videoUrl += "http://medianac.nacamar.de/p/657/sp/65700/playManifest/entryId/"
        videoUrl += videoId
        videoUrl += "/format/rtmp/protocol/rtmp/cdnHost/medianac.nacamar.de/ks/"
        
        videoPage = load_page(videoUrl)
        
        _regex_extractBaseURL = re.compile("<baseURL>(.*?)</baseURL>")        
        _regex_extractMedia = re.compile("<media url=\"(.*?)\" bitrate=\"([0-9]*)\" width=\"[0-9]*\" height=\"[0-9]*\"/>")
        
        baseURL = _regex_extractBaseURL.search(videoPage).group(1)
        maxBitrate = 0
        for media in _regex_extractMedia.finditer(videoPage):
            bitrate = media.group(2)
            tmpPlaypath =  media.group(1)
            print tmpPlaypath[0:4]
            if bitrate > maxBitrate and tmpPlaypath[0:4] == "mp4:":
                playpath = tmpPlaypath
                
        stream_url = baseURL+"/"+playpath
    else:
        #YouTube
        "//www.youtube.com/embed/RRDSj62tlvQ?rel=0"
        _regex_extractVideoId = re.compile("//www.youtube.com/(embed|v)/(.*?)(\"|\?|\ |&)")
        youTubeId = _regex_extractVideoId.search(page).group(2)
        stream_url = "plugin://plugin.video.youtube/?action=play_video&videoid=" + youTubeId
    
    item = xbmcgui.ListItem(path=stream_url)
  
    xbmcplugin.setResolvedUrl(thisPlugin, True, item)
    return False
 
def getText(nodelist):
    rc = []
    for node in nodelist:
        if node.nodeType == node.TEXT_NODE:
            rc.append(node.data)
    return ''.join(rc)
                                 
def load_page(url):
    print url
    req = urllib2.Request(url)
    response = urllib2.urlopen(req)
    link = response.read()
    response.close()
    return link

def addDirectoryItem(name, parameters={}, pic="", folder=True):
    li = xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=pic)
    if not folder:
        li.setProperty('IsPlayable', 'true')
    url = sys.argv[0] + '?' + urllib.urlencode(parameters)
    return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=li, isFolder=folder)
    
def get_params():
    param = []
    paramstring = sys.argv[2]
    if len(paramstring) >= 2:
        params = sys.argv[2]
        cleanedparams = params.replace('?', '')
        if (params[len(params) - 1] == '/'):
            params = params[0:len(params) - 2]
        pairsofparams = cleanedparams.split('&')
        param = {}
        for i in range(len(pairsofparams)):
            splitparams = {}
            splitparams = pairsofparams[i].split('=')
            if (len(splitparams)) == 2:
                param[splitparams[0]] = splitparams[1]
    
    return param

if not sys.argv[2]:
    mainPage()
else:
    params = get_params()
    if params['action'] == "show":
        showPage(params['link'])
    if params['action'] == "episode":
        episodePage(params['link'])
