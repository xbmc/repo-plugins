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

thisPlugin = int(sys.argv[1])

def showEpisode(episode_page):
    
    providers = (
        {"function":showEpisodeBip, "regex":"(http://blip.tv/play/.*?)(.html|\")"},
        {"function":showEpisodeYoutube, "regex":"http://www.youtube.com/(embed|v)/(.*?)(\"|\?|\ |&)"},
        {"function":showEpisodeDorkly, "regex":"http://www.dorkly.com/(e/|moogaloop/noobtube.swf\?clip_id=)([0-9]*)"},
        {"function":showEpisodeSpringboard, "regex":"\.springboardplatform\.com/mediaplayer/springboard/video/(.*?)/(.*?)/(.*?)/"},
        {"function":showEpisodeSpringboard, "regex":"\\$sb\\(\"(.*?)\",{\"sbFeed\":{\"partnerId\":(.*?),\"type\":\"video\",\"contentId\":(.*?),\"cname\":\"(.*?)\"},\"style\":{\"width\":.*?,\"height\":.*?}}\\);"},
        {"function":showEpisodeDaylimotion, "regex":"(http://www.dailymotion.com/video/.*?)_"},          
        {"function":showEpisodeGametrailers, "regex":"<a href=\"(http://www.gametrailers.com/video/angry-video-screwattack/(.*))\" target=\"_blank\">"},
        {"function":showEpisodeSpike, "regex":"<a href=\"(http://www.spike.com/.*?)\""},               
    )
    
    for provider in providers:
        regex = re.compile(provider['regex'])
        videoItem = regex.search(episode_page)
        if videoItem is not None:
            return provider['function'](videoItem)

def showEpisodeBip(videoItem):
    _regex_extractVideoFeedURL = re.compile("file=(.*?)&", re.DOTALL);
    _regex_extractVideoFeedURL2 = re.compile("file=(.*)", re.DOTALL);
    _regex_extractVideoFeedURL3 = re.compile("data-episode-id=\"(.*?)\"", re.DOTALL);

    videoLink = videoItem.group(1)
    
    #GET the 301 redirect URL
    req = urllib2.Request(videoLink)
    response = urllib2.urlopen(req)
    fullURL = response.geturl()
    
    feedURL = _regex_extractVideoFeedURL.search(fullURL)
    if feedURL is None:
        feedURL = _regex_extractVideoFeedURL2.search(fullURL)
    
    if feedURL is None:
        page = showEpisodeLoadPage(videoLink) 
        blipId = _regex_extractVideoFeedURL3.search(page).group(1)
    else:#This still needed for older links
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
    _regex_extractVideoSpringboardStream = re.compile("<media:content duration=\"[0-9]*?\" medium=\"video\" bitrate=\"[0-9]*?\" fileSize=\"[0-9]*?\" url=\"(.*?)\" type=\".*?\" />");
    
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
    _regex_extractVideoGametrailersXML = re.compile("<media:content type=\"text/xml\" medium=\"video\" isDefault=\"true\" duration=\"[0-9]{1,4}\" url=\"(.*?)\"/>")
    _regex_extractVideoGametrailersStreamURL = re.compile("<src>(.*?)</src>")

    url = videoItem.group(1)
    videoId = videoItem.group(2)
    urlXml = "http://www.gametrailers.com/neo/?page=xml.mediaplayer.Mrss&mgid=mgid%3Amoses%3Avideo%3Agametrailers.com%3A" + videoId + "&keyvalues={keyvalues}"
    xml1 = showEpisodeLoadPage(urlXml)
    urlXml = _regex_extractVideoGametrailersXML.search(xml1).group(1)
    urlXml = urlXml.replace("&amp;", "&")
    xml2 = showEpisodeLoadPage(urlXml)
    stream_url = _regex_extractVideoGametrailersStreamURL.search(xml2).group(1)
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
    response = urllib2.urlopen(req)
    link = response.read()
    response.close()
    return link

