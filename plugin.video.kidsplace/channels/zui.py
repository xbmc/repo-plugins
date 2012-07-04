import xbmcplugin, xbmcgui
import urllib, sys, re
import helper
import json
import pprint

import brightcovePlayer

height = 1080

thisChannel = "zui"
baseLink = "http://zui.com"

def mainPage():
    page = helper.load_page(baseLink + "/videos")
    
    heroCats = re.compile("<ul id=\"hero_cats\">(.*?</ul><ul id=\"more_cats\">.*?)</ul>", re.DOTALL).search(page).group(1)
    
    items = re.compile("<a href=\"(/videos/category/(.*?))\" class=\".*?\"><span>(.*?)</span></a>").finditer(heroCats)
    
    helper.addDirectoryItem("All", {"channel":thisChannel, "action":"showCategory", "link":"/videos"})
    
    for category in items:
        catName = category.group(3)
        catLink = category.group(1)
        catImg = baseLink + "/assets/icons/cats/" + category.group(2).replace("+", "_") + "_normal.png"
        helper.addDirectoryItem(catName, {"channel":thisChannel, "action":"showCategory", "link":catLink}, catImg)

    helper.endOfDirectory()

def showCategory(link):
    page = helper.load_page(baseLink+urllib.unquote(link))

    extractVideos = re.compile("<div class=\"peepshow\">.*?<a href=\"(.*?)\">(.*?)</a>.*?<img.*?src=\"(.*?)\".*?<p>(.*?)</p>")
    
    for video in extractVideos.finditer(page):
        vidName = video.group(2)
        vidLink = video.group(1)
        vidImg = video.group(3)
        vidPlot = video.group(4)
        parameters = {"channel":thisChannel, "action":"playVideo", "link":vidLink}
        helper.addDirectoryItem(vidName, parameters, vidImg, False, plot=vidPlot)
        
    extractNextPage = re.compile("<li class=\"next\"><a href=\"(.*?)\" rel=\"next\">Next")
    
    nextPage = extractNextPage.search(page)
    
    if nextPage is not None:
        helper.addDirectoryItem("Show more", {"channel":thisChannel, "action":"showCategory", "link":nextPage.group(1)})
    
    helper.endOfDirectory()

def playVideo(link):
    page = helper.load_page(baseLink + urllib.unquote(link))
    
    extractYouTubeId = re.compile("<div data-youtube=\"(.*?)\" id=\"yt_video\">")
    
    youTubeInfo = extractYouTubeId.search(page)
    
    if youTubeInfo is not None:
        youTubeId = youTubeInfo.group(1)
        streamUrl = "plugin://plugin.video.youtube/?action=play_video&videoid=" + youTubeId 
        helper.setResolvedUrl(streamUrl)
    else:
        const = "07e6acedf6c0f426a377e5b3ba077229e6e826f9"
        publisherID = "1521649306001"
    
        extractVideo = re.compile("<param name=\"playerID\" value=\"([0-9]*)\".*?name=\"playerKey\" value=\"(.*?)\".*name=\"@videoPlayer\" value=\"([0-9]*)\"")
    
        video = extractVideo.search(page)
        playerID = video.group(1)
        playerKey = video.group(2)
        videoPlayer = video.group(3)
    
        stream = brightcovePlayer.play(const, playerID, videoPlayer, publisherID, playerKey)
    
        vidStr = "?videoId="+videoPlayer+"&lineUpId=&pubId="+publisherID+"&playerId="+playerID+"&affiliateId="
    
        rtmpbase = stream[1][0:stream[1].find("&")]
        conn = stream[1][stream[1].find("&") + 1:]
        playpath = conn[0:conn.find("&")]+vidStr
        app = rtmpbase[rtmpbase.find("/",7)+1:-1]+vidStr;
    
        finalurl = rtmpbase + ' playpath=' + playpath +" conn=B:0 conn=S:"+conn+" app="+app

        helper.setResolvedUrl(finalurl)

params = helper.get_params()
if len(params) == 1:
    mainPage()
else:
    if params['action'] == "showCategory":
        showCategory(params['link'])
    if params['action'] == "playVideo":
        playVideo(params['link'])
