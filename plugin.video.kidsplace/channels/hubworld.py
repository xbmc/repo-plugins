import urllib, re
import helper

import brightcovePlayer


thisChannel = "hubworld"

baseLink = "http://www.hubworld.com/"

playerKey = "AQ~~,AAAA0Zd2KCE~,a1ZzPs5ODGffVvk2dn1CRCof3Ru_I9gE"

height = 1080
const = "d833dffff3160dc3ca9269e875abd8805b3b0f38"
playerID = 1379595107001
publisherID = 90719631001

extractSection = re.compile("<section class=\".*?video-box\">.*?<div class=\"fb-top\">.*?<h2>(.*?)</h2>(.*?)<div class=\"fb-bottom\">", re.DOTALL)

def mainPage():
    helper.addDirectoryItem("Videos", {"channel":thisChannel, "action":"showVideos", "link":baseLink + "videos"}, "")
    helper.addDirectoryItem("Shows", {"channel":thisChannel, "action":"showShows", "link":baseLink + "shows"}, "")
    helper.endOfDirectory()
    
def showVideos(link):
    link = urllib.unquote(link)
    page = helper.load_page(link)
    extractShowMoreButton = re.compile("<a href=\"(.*?)\" class=\"lite-button\">")
    extractSections = extractSection.findall(page)
    if len(extractSections) == 1:
        showVideosSection(link, extractSections[0][0])
        return False
    else:
        for section in extractSections:
            sectionLink = link
            sectionTitle = section[0]
            sectionHtml = section[1]
            showMoreButton = extractShowMoreButton.search(sectionHtml)
            sectionLinkSection = sectionTitle
            if showMoreButton is not None:
                sectionLink = baseLink + showMoreButton.group(1)
                sectionLinkSection = ""
            helper.addDirectoryItem(sectionTitle, {"channel":thisChannel, "action":"showVideosSection", "link":sectionLink, "section":sectionLinkSection}, "")
    
    helper.endOfDirectory()
    
def showVideosSection(link, section):
    link = urllib.unquote(link)
    showSection = urllib.unquote_plus(section)
    
    page = helper.load_page(link)
    
    extractVideo = re.compile("<section class=\".*?\">.*?<img src=\"(.*?)\".*?<a href=\"(.*?)\" class=\"title\">(.*?)</a>.*?<p>(.*?)</p>.*?<span class=\"content-item-short-description\">(.*?)</span>.*?</section>", re.DOTALL)

    sectionHtml = "";
    
    if showSection != "":
        extractSections = extractSection.finditer(page)
        for section in extractSections:
            sectionTitle = section.group(1)
            if sectionTitle == showSection:
                sectionHtml = section.group(2)
    else:
        sectionHtml = page

    for video in extractVideo.finditer(sectionHtml):
        videoTitle = video.group(3) + " (" + video.group(4).strip() + ")"
        videoImg = baseLink + video.group(1)
        videoLink = baseLink + video.group(2)
        videoPlot = video.group(5)
        helper.addDirectoryItem(videoTitle, {"channel":thisChannel, "action":"playVideo", "link":videoLink}, videoImg, False,plot=videoPlot)

    helper.endOfDirectory()

def showShows(link):
    page = helper.load_page(urllib.unquote(link))
    
    extractShow = re.compile("<section class=\".*?content-item-vertical.*?\">.*?<div class=\"thumbimg\">.*?src=\"(.*?)\".*?href=\"(.*?)\".*?>(.*?)</a>", re.DOTALL)
    
    for show in extractShow.finditer(page):
        showImg = baseLink + show.group(1)
        showLink = baseLink + show.group(2) + "/videos"
        showTitle = show.group(3)
        
        showPage = urllib.urlopen(showLink)
        if showLink == showPage.geturl():
            if extractSection.search(showPage.read()) is not None:
                helper.addDirectoryItem(showTitle, {"channel":thisChannel, "action":"showVideos", "link":showLink}, showImg)
    helper.endOfDirectory()

def playVideo(link):
    page = helper.load_page(urllib.unquote(link))
    videoPlayer = re.compile("brightcove_mediaId: ([0-9]*),").search(page).group(1)
    stream = brightcovePlayer.play(const, playerID, videoPlayer, publisherID, playerKey)
    
    rtmpbase = stream[1][0:stream[1].find("&")]
    playpath = stream[1][stream[1].find("&") + 1:]
    finalurl = rtmpbase + ' playpath=' + playpath
    
    helper.setResolvedUrl(finalurl)

params = helper.get_params()
if len(params) == 1:
    mainPage()
else:
    if params['action'] == "showVideos":
        showVideos(params['link'])
    if params['action'] == "showVideosSection":
        showVideosSection(params['link'], params['section'])
    if params['action'] == "showShows":
        showShows(params['link'])
    if params['action'] == "playVideo":
        playVideo(params['link'])
    else:
        mainPage()
