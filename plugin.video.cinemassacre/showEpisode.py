#v 0.0.1
import re
import xbmcplugin
import xbmcgui
import sys
import urllib, urllib2
try:
    import urlresolver
except:
    print "No urlresolver"
import thisCommonFunctions
common = thisCommonFunctions
thisPlugin = int(sys.argv[1])

def showEpisode(episode_page):
    episode_page2 = common.parseDOM(episode_page, "div", attrs={"id": "video-content"})
    if len(episode_page2):
      episode_page = episode_page2[0]
      
    providers = (
        {"function":showEpisodeBip, "regex":"(http://blip.tv/play/.*?)(.html|\")"},
        {"function":showEpisodeYoutube, "regex":"http://www.youtube.com/(embed|v)/(.*?)(\"|\?|\ |&)"},
        {"function":showEpisodeDorkly, "regex":"http://www.dorkly.com/(e/|moogaloop/noobtube.swf\?clip_id=)([0-9]*)"},
        {"function":showEpisodeSpringboard, "regex":"\.springboardplatform\.com/mediaplayer/springboard/video/(.*?)/(.*?)/(.*?)/"},
        {"function":showEpisodeSpringboard, "regex":"\\$sb\\(\"(.*?)\",{\"sbFeed\":{\"partnerId\":(.*?),\"type\":\"video\",\"contentId\":(.*?),\"cname\":\"(.*?)\"},\"style\":{\"width\":.*?,\"height\":.*?}}\\);"},
        {"function":showEpisodeDaylimotion, "regex":"(http://www.dailymotion.com/video/.*?)_"},
        {"function":showEpisodeGametrailers, "regex":"<a href=\"(http://www.gametrailers.com/videos/(.*).*)\" target=\"_blank\">"},
        {"function":showEpisodeSpringboadAfterResolve, "regex":"src=\"(http\:\/\/cdn\.springboard\.gorillanation\.com/mediaplayer/springboard/video/(?:.*?)/(?:.*?)/(?:.*?)/)"},
        {"function":showEpisodeSpringboadAfterResolve, "regex":"<script src=\"http://www.springboardplatform.com/js/overlay\"></script><iframe id=\"(?:.*?)\" src=\"(.*?)\""},
        {"function":showEpisodeSpike, "regex":"<a href=\"(http://www.spike.com/.*?)\""},
        {"function":showEpisodeScreenwave, "regex":"((?:[^\"\']*)screenwavemedia.com/(?:[^\/]*)/embed.php(?:[^\"\']*))"},
    )
    
    for provider in providers:
        regex = re.compile(provider['regex'])
        videoItem = regex.search(episode_page)
        if videoItem is not None:
            return provider['function'](videoItem)
            
def showEpisodeScreenwave(videoItem):
    tmpContent = showEpisodeLoadPage(videoItem.group(1))
  
    streamerVal = re.compile('streamer(?:[\'|\"]*):(?:[\s|\'|\"]*)([^\']*)', re.DOTALL).findall(tmpContent)
    flashplayerVal = re.compile('flashplayer(?:[\'|\"]*):(?:[\s|\'|\"]*)([^\']*)', re.DOTALL).findall(tmpContent)
    levelsVal = re.compile('levels(?:[\'|\"]*): \[(.*)\],', re.DOTALL).findall(tmpContent)
    files = ""
    if len(levelsVal)>0:
        filesVal = re.compile('file(?:[\'|\"]*):(?:[\s|\'|\"]*)([^\'|\"]*)', re.DOTALL).findall(levelsVal[0])
        for i in range(0,len(filesVal)):
            if "high" in filesVal[i]:
                files = filesVal[i]
                break
      
    if len(streamerVal)>0 and len(flashplayerVal)>0 and len(files)>0:
        rtmpurl = streamerVal[0]
        swfVfy = flashplayerVal[0]

        fileExt = re.compile('\.([^.]+)$', re.DOTALL).findall(files)
        if len(fileExt)>0:
            files = fileExt[0] + ":" + files
          
        if rtmpurl[-1:] != "/":
            rtmpurl = rtmpurl + "/"
        rtmpurl = rtmpurl + files

        segmentUrl = rtmpurl + " playpath=" + files + " pageurl=" + videoItem.group(1) + " swfVfy=" + swfVfy

        listitem = xbmcgui.ListItem(path=segmentUrl)
        return xbmcplugin.setResolvedUrl(thisPlugin, True, listitem)
    
def showEpisodeSpringboadAfterResolve(videoItem):
    _regex_extractVideoParameters = re.compile("http://cms\.springboard.*\.com/(.*?)/(.*?)/video/(.*?)/.*?/(.*?)")
    _regex_extractVideoParameters2 = re.compile("http\://cms\.springboardplatform\.com/xml_feeds_advanced/(.*?)/(.*?)/rss3/(.*?)/")

    # Handle shortened URLs
    req = urllib2.Request(videoItem.group(1))
    response = urllib2.urlopen(req)
    fullURL = response.geturl()

    videoItem = _regex_extractVideoParameters.search(fullURL)
    if videoItem is None:
       videoItem = _regex_extractVideoParameters2.search(fullURL)
    showEpisodeSpringboard(videoItem)
    return False

def showEpisodeBip(videoItem):
    _regex_extractVideoFeedURL = re.compile("file=(.*?)&", re.DOTALL);
    _regex_extractVideoFeedURL2 = re.compile("file=(.*)", re.DOTALL);
    _regex_extractVideoFeedURL3 = re.compile("data-episode-id=\"(.+?)\"", re.DOTALL);

    videoLink = videoItem.group(1)
    
    #GET the 301 redirect URL
    req = urllib2.Request(videoLink)
    response = urllib2.urlopen(req)
    fullURL = response.geturl()
    
    feedURL = _regex_extractVideoFeedURL.search(fullURL)
    if feedURL is None:
        feedURL = _regex_extractVideoFeedURL2.search(fullURL)
        if feedURL is None:
            feedURL = _regex_extractVideoFeedURL3.search(response.read())
    feedURL = urllib.unquote(feedURL.group(1))
    
    blipId = feedURL[feedURL.rfind("/") + 1:]
    
    stream_url = "plugin://plugin.video.bliptv/?action=play_video&videoid=" + blipId
    item = xbmcgui.ListItem(path=stream_url)
    return xbmcplugin.setResolvedUrl(thisPlugin, True, item)

def showEpisodeYoutube(videoItem):
    youTubeId = videoItem.group(2)
    stream_url = "plugin://plugin.video.youtube/?action=play_video&videoid=" + youTubeId
    item = xbmcgui.ListItem(path=stream_url)
    xbmcplugin.setResolvedUrl(thisPlugin, True, item)
    return False

def showEpisodeDorkly(videoItem):
    _regex_extractEpisodeDorklyVideo = re.compile("<file><!\[CDATA\[(.*?)\]\]></file>")
    
    dorklyID = videoItem.group(2)
    
    feedUrl = "http://www.dorkly.com/moogaloop/video/" + dorklyID
    feedPage = showEpisodeLoadPage(feedUrl)
    videoItem = _regex_extractEpisodeDorklyVideo.search(feedPage)
    if videoItem is not None:
        stream_url = videoItem.group(1)
        item = xbmcgui.ListItem(path=stream_url)
        xbmcplugin.setResolvedUrl(thisPlugin, True, item)
    return False
    
def showEpisodeSpringboard(videoItem):
    _regex_extractVideoSpringboardStream = re.compile("<media:content.*?url=\"(.*?)\".*?/>");
    
    siteId = videoItem.group(2)
    contentId = videoItem.group(3)
    feedUrl = "http://cms.springboard.gorillanation.com/xml_feeds_advanced/index/" + siteId + "/rss3/" + contentId + "/"

    req = urllib2.Request(feedUrl)
    response = urllib2.urlopen(req)
    feed = response.read()
    response.close()

    feedItem = _regex_extractVideoSpringboardStream.search(feed);
    stream_url = feedItem.group(1)
    item = xbmcgui.ListItem(path=stream_url)

    xbmcplugin.setResolvedUrl(thisPlugin, True, item)
    return False

def showEpisodeDaylimotion(videoItem):
    url = videoItem.group(1)
    stream_url = urlresolver.resolve(url)
    item = xbmcgui.ListItem(path=stream_url)
    xbmcplugin.setResolvedUrl(thisPlugin, True, item)
    return False

def showEpisodeGametrailers(videoItem):
    _regex_extractVideoGametrailerId = re.compile("<meta property=\"og:video\" content=\"(http://media.mtvnservices.com/fb/mgid:arc:video:gametrailers.com:(.*?)\.swf)\" />");
    _regex_extractVideoGametrailerStreamURL = re.compile("<rendition bitrate=\"(.*?)\".*?<src>(.*?)</src>.*?</rendition>",re.DOTALL)

    videoUrl = videoItem.group(1)
    videoPage = showEpisodeLoadPage(videoUrl)
    swfUrl = _regex_extractVideoGametrailerId.search(videoPage).group(1)

    #GET the 301 redirect URL
    req = urllib2.Request(swfUrl)
    response = urllib2.urlopen(req)
    swfUrl = response.geturl()
    videoId = _regex_extractVideoGametrailerId.search(videoPage).group(2)

    feedUrl = "http://udat.mtvnservices.com/service1/dispatch.htm?feed=mediagen_arc_feed&account=gametrailers.com&mgid=mgid%3Aarc%3Acontent%3Agametrailers.com%3A"+videoId+"&site=gametrailers.com&segment=0&mgidOfMrssFeed=mgid%3Aarc%3Acontent%3Agametrailers.com%3A"+videoId

    videoFeed = showEpisodeLoadPage(feedUrl)
    videoStreamUrls = _regex_extractVideoGametrailerStreamURL.finditer(videoFeed)

    curStream = None
    curBitrate = 0
    for stream in videoStreamUrls:
        streamUrl = stream.group(2)
        streamBitrate = int(stream.group(1))
        if streamBitrate>curBitrate:
            curStream = streamUrl.replace(" ","%20")
            curBitrate = streamBitrate

    swfUrl = swfUrl.replace("&geo=DE","&geo=US")
    swfUrl = swfUrl.replace("geo%3dDE%26","geo%3dUS%26")

    stream_url = curStream + " swfUrl="+swfUrl+" swfVfy=1"
    if curStream is not None:
        item = xbmcgui.ListItem(path=stream_url)
        xbmcplugin.setResolvedUrl(thisPlugin, True, item)
        return False

def showEpisodeSpike(videoItem):
    _regex_extraxtVideoSpikeId = re.compile("<meta property=\"og:video\" content=\"(http://media.mtvnservices.com/mgid:arc:video:spike.com:(.*?))\" />");
    _regex_extractVideoSpikeSreamURL = re.compile("<rendition bitrate=\"(.*?)\".*?<src>(.*?)</src>.*?</rendition>",re.DOTALL)
    
    videoUrl = videoItem.group(1)
    videoPage = showEpisodeLoadPage(videoUrl)
    swfUrl = _regex_extraxtVideoSpikeId.search(videoPage).group(1)
    #GET the 301 redirect URL
    req = urllib2.Request(swfUrl)
    response = urllib2.urlopen(req)
    swfUrl = response.geturl()
    
    videoId = _regex_extraxtVideoSpikeId.search(videoPage).group(2)
    feedUrl = "http://udat.mtvnservices.com/service1/dispatch.htm?feed=mediagen_arc_feed&account=spike.com&mgid=mgid%3Aarc%3Acontent%3Aspike.com%3A"+videoId+"&site=spike.com&segment=0&mgidOfMrssFeed=mgid%3Aarc%3Acontent%3Aspike.com%3A"+videoId
    videoFeed = showEpisodeLoadPage(feedUrl)
    videoStreamUrls = _regex_extractVideoSpikeSreamURL.finditer(videoFeed)
    
    curStream = None
    curBitrate = 0
    for stream in videoStreamUrls:
        streamUrl = stream.group(2)
        streamBitrate = int(stream.group(1))
        if streamBitrate>curBitrate:
            curStream = streamUrl.replace(" ","%20")
            curBitrate = streamBitrate
    
    swfUrl = swfUrl.replace("&geo=DE","&geo=US")
    swfUrl = swfUrl.replace("geo%3dDE%26","geo%3dUS%26")
   
    stream_url = curStream + " swfUrl="+swfUrl+" swfVfy=1"
    if curStream is not None:
        item = xbmcgui.ListItem(path=stream_url)
        xbmcplugin.setResolvedUrl(thisPlugin, True, item)
        return False
    
def showEpisodeLoadPage(url):
    print url
    req = urllib2.Request(url)
    req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; rv:14.0) Gecko/20100101 Firefox/14.0.1')
    response = urllib2.urlopen(req)
    link = response.read()
    response.close()
    return link

