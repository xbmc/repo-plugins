# -*- encoding: utf-8 -*-

import xbmc
import xbmcaddon
import xbmcplugin
import xbmcgui
import urllib, urllib2
from resources.lib import rtsProvider

__addon__       = xbmcaddon.Addon(id='plugin.video.rts-video')
__addonname__   = __addon__.getAddonInfo('name')
__icon__        = __addon__.getAddonInfo('icon')
 
def addTvShow(name, url, mode, iconimage, description=''):
    """Add one "TV show" item to the UI"""
    #Process the link
    url = '%s?url=%s&mode=%d&name=%s' % (
        sys.argv[0],
        urllib.quote_plus(url),
        mode,
        urllib.quote_plus(name))
    #If case of no image
    if not iconimage:
        iconimage = "DefaultVideo.png"
    #Create a XBMC directory item and set infos
    tvShow = xbmcgui.ListItem(
        name,
        iconImage=iconimage,
        thumbnailImage=iconimage)
    tvShow.setInfo(
        type="Video",
        infoLabels={
            "Title": name,
            "Plot": description})
    #Add the new directory item to the UI
    return xbmcplugin.addDirectoryItem(
        handle=int(sys.argv[1]),
        url=url,
        listitem = tvShow,
        isFolder=True)

def addEpisode(name, url, iconimage, description, date):
    """Add one "episode" item to the UI"""
    #Process the link
    url = '%s?url=%s&mode=%d&name=%s' % (
        sys.argv[0],
        urllib.quote_plus(url),
        2,
        urllib.quote_plus(name))
    if not iconimage:
        iconimage = 'DefaultVideo.png'
    listOfItems = xbmcgui.ListItem(
        name,
        iconImage=iconimage,
        thumbnailImage=iconimage)
    listOfItems.setInfo(
        type="Video",
        infoLabels={
            "Title": name,
            "Plot": description,
            "Date": date,
            "Genre": "Podcast"})
    return xbmcplugin.addDirectoryItem(
        handle=int(sys.argv[1]),
        url=url,
        listitem = listOfItems)

def listTvShows():
    """Display the list of TV shows """
    listOfTvShows = rtsProvider.get_tv_shows()
    for tvShow in listOfTvShows:
        # For each tv show, add an item in the ui
        addTvShow(
            tvShow.title.encode("utf-8"),
            tvShow.podcastUrl.encode("utf-8"),
            1,
            tvShow.imgUrl.encode("utf-8"),
            tvShow.info.encode("utf-8"))

def listTvEpisodes(urlOfPodcast=''):
    """Display the list of episodes of a TV show"""
    tvShow = rtsProvider.get_tv_show_from_podast_url(
        urlOfPodcast.decode("utf-8"))
    tvShow.getEpisodes()

    for episode in tvShow.listOfEpisodes:
        print "URL = " + episode.videoUrl
        addEpisode(
            name = episode.title.encode("utf-8"), 
            url = episode.videoUrl.encode("utf-8"), 
            iconimage = episode.image.encode("utf-8"), 
            description = episode.info.encode("utf-8"), 
            date = episode.pubDate.encode("utf-8"))

def playVideo(videoUrl):
    """Play the video. In HD if user want."""
    #Know if user want to watch the HD video
    addon = xbmcaddon.Addon('plugin.video.rts')
    playHD = addon.getSetting('32002')
    #If yes, get the url to the HD video
    if playHD == 'true':
        videoUrl = rtsProvider.get_HD_video_url_from(videoUrl)
    #Creat a playlist with the video and play it
    playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
    playlist.clear()
    playlist.add(videoUrl)
    xbmc.Player().play(playlist)

def get_params():
    """Clean the parameters"""
    finalParams = []
    paramStr = sys.argv[2]
    if len(paramStr) >= 2:
        params = sys.argv[2]
        cleanedparams = params.replace('?','')
        if (params[len(params)-1] == '/'):
            params = params[0:len(params)-2]
        pairsofparams = cleanedparams.split('&')
        finalParams = {}
        for i in range(len(pairsofparams)):
            splitparams = {}
            splitparams = pairsofparams[i].split('=')
            if (len(splitparams)) == 2:
                finalParams[splitparams[0]] = splitparams[1]
    return finalParams

# Part of thestring executing at every turn

params = get_params()
url = None
name = None
mode = None

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

print "Mode: " + str(mode)
print "URL: " + str(url)
print "Name: " + str(name)

#Mode of activities when user select an item
if mode==None or url==None or len(url)<1:
    listTvShows()
elif mode==1:
    listTvEpisodes(str(url))
elif mode==2:
    playVideo(str(url))

xbmcplugin.endOfDirectory(int(sys.argv[1]))
