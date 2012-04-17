import xbmcplugin
import xbmcgui
import sys
import urllib, urllib2, urlparse
import re
import pprint

import httplib
from pyamf import AMF0, AMF3

from pyamf import remoting
from pyamf.remoting.client import RemotingService

thisPlugin = int(sys.argv[1])
baseLink = "http://www.dmax.de"
urlShows = baseLink + "/video/shows/"

rootLink = "http://www.dmax.de"
height = 1080;#268|356|360|400|572|576
const = "ef59d16acbb13614346264dfe58844284718fb7b"
playerID = 586587148001;
publisherID = 1659832546;
playerKey = "AAAAAGLvCOI~,a0C3h1Jh3aQKs2UcRZrrxyrjE0VH93xl"

_regex_extractShows = re.compile("<li class=\"(first-child|last-child)\"><a href=\"(.*)\">(.*)</a></li>");    
_regex_extractShowsPages = re.compile("<strong class=\"title\">Seite <em>(.*?)</em>von<em>(.*?)</em></strong>");
_regex_extractEpisode = re.compile("<dl class=\" item item-(.*?)\">(.*?)</dl>", re.DOTALL);
_regex_extractEpisodeLink = re.compile("<a href=\"(.*)\">");
_regex_extractEpisodeTitle = re.compile("<dd class=\"description\"> (.*?)(Teil 1| - 1|1)</dd>");
_regex_extractEpisodeTitleClassic = re.compile("<a href=\".*?\">(.*?)<span class=\"video-play\"></span>.*?<dd class=\"description\"> (.*?)(Teil 1| - 1|1)</dd>?",re.DOTALL);
_regex_extractEpisodeImg = re.compile("src=\"(.*?)\"");
_regex_extractVideoIds = re.compile("videoIds.push\(\"(.*)\"\);");

def mainPage():
    global thisPlugin
    page = load_page(urlShows)
    shows = list(_regex_extractShows.finditer(page))
    for show in shows:
        show_title = show.group(3);
        show_link = show.group(2) + "moreepisodes/"
        addDirectoryItem(show_title, {"action" : "show", "link": show_link})  
    xbmcplugin.endOfDirectory(thisPlugin)

def showPage(link):
    global thisPlugin
    page = load_page(baseLink + link)
    pageCount = int(_regex_extractShowsPages.search(page).group(2))
    
    for i in range(1, pageCount + 1, 1):
        if i > 1:
            page = load_page(baseLink + link + "?page=" + str(i))
        
        episodes = list(_regex_extractEpisode.finditer(page))
    
        for episode in episodes:
            episode_html = episode.group(2)
            if link == "/video/shows/dmax-classics/moreepisodes/":
                episod_title = _regex_extractEpisodeTitleClassic.search(episode_html).group(1)
                episod_title = episod_title + " - "
                episod_title = episod_title +  _regex_extractEpisodeTitleClassic.search(episode_html).group(2)
                episod_title = episod_title.strip()
            else:
                episod_title = _regex_extractEpisodeTitle.search(episode_html).group(1)
            episode_link = _regex_extractEpisodeLink.search(episode_html).group(1)
            episode_img = _regex_extractEpisodeImg.search(episode_html).group(1)
            addDirectoryItem(episod_title, {"action" : "episode", "link": episode_link}, episode_img)
    xbmcplugin.endOfDirectory(thisPlugin)

def showEpisode(link):
    page = load_page(baseLink + link)
    
    videoIds = list(_regex_extractVideoIds.finditer(page));
    playlistContent = []
    x = 0
    for videoId in videoIds:
        video = play(const, playerID, videoId.group(1), publisherID);
        playlistContent.append(video)
        x = x + 1
    
    playPlaylist(link, playlistContent)
    
def load_page(url):
    print "Load: " + url
    req = urllib2.Request(url)
    response = urllib2.urlopen(req)
    link = response.read()
    response.close()
    return link

def addDirectoryItem(name, parameters={}, pic=""):
    li = xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=pic)
    url = sys.argv[0] + '?' + urllib.urlencode(parameters)
    return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=li, isFolder=True)

def build_amf_request(const, playerID, videoPlayer, publisherID):
    env = remoting.Envelope(amfVersion=3)
    env.bodies.append(
        (
            "/1",
            remoting.Request(
                target="com.brightcove.player.runtime.PlayerMediaFacade.findMediaById",
                body=[const, playerID, videoPlayer, publisherID],
                envelope=env
            )
        )
    )
    return env

def get_clip_info(const, playerID, videoPlayer, publisherID):
    conn = httplib.HTTPConnection("c.brightcove.com")
    envelope = build_amf_request(const, playerID, videoPlayer, publisherID)
    conn.request("POST", "/services/messagebroker/amf?playerKey=" + playerKey, str(remoting.encode(envelope).read()), {'content-type': 'application/x-amf'})
    response = conn.getresponse().read()
    response = remoting.decode(response).bodies[0][1].body
    return response  

def play(const, playerID, videoPlayer, publisherID):
    rtmpdata = get_clip_info(const, playerID, videoPlayer, publisherID)
    streamName = ""
    streamUrl = rtmpdata['FLVFullLengthURL'];
    
    for item in sorted(rtmpdata['renditions'], key=lambda item:item['frameHeight'], reverse=False):
        streamHeight = item['frameHeight']
        
        if streamHeight <= height:
            streamUrl = item['defaultURL']
    
    streamName = streamName + rtmpdata['displayName']
    return [streamName, streamUrl];

def playPlaylist(playlistLink, playlistContent):
    player = xbmc.Player();
    
    playerItem = xbmcgui.ListItem(playlistLink);
    playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO);
    playlist.clear();
    print "playPlaylist";
    
    for link in playlistContent:
        listItem = xbmcgui.ListItem(link[0]);
        listItem.setProperty("PlayPath", link[1]);
        playlist.add(url=link[1], listitem=listItem);
    
    player.play(playlist, playerItem);

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
    print params['action']
    if params['action'] == "show":
        showPage(urllib.unquote(params['link']))
    elif params['action'] == "episode":
        showEpisode(urllib.unquote(params['link']))
    else:
        mainPage()
