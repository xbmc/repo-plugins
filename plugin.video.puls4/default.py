#!/usr/bin/python
# -*- coding: utf-8 -*-

import urllib,urllib2,re,xbmcplugin,xbmcgui,sys,xbmcaddon,base64,socket,datetime,time,os,os.path,urlparse,json
import CommonFunctions as common

version = "0.2.3"
plugin = "Puls 4 -" + version
author = "sofaking"

#init
common.plugin = plugin
settings = xbmcaddon.Addon(id='plugin.video.puls4') 
pluginhandle = int(sys.argv[1])
basepath = settings.getAddonInfo('path')
resource_path = os.path.join( basepath, "resources" )
media_path = os.path.join( resource_path, "media" )
translation = settings.getLocalizedString

#view-mode
current_skin = xbmc.getSkinDir();
if 'confluence' in current_skin:
   defaultViewMode = 'Container.SetViewMode(503)'
else:
   defaultViewMode = 'Container.SetViewMode(518)'
thumbViewMode = 'Container.SetViewMode(500)'
smallListViewMode = 'Container.SetViewMode(51)'

#urls
base_url = "http://m.puls4.com"
file_base_url = "http://files.puls4.com/"
top_url = "http://www.puls4.com/api/json-fe/page/"
highlight_url = "http://m.puls4.com/api/teaser/highlight"
highlight_view_url = "http://m.puls4.com/api/teaser/highlight-view"
show_url = "http://m.puls4.com/api/channel/"
video_url = "http://m.puls4.com/api/video/"

main_url = "http://www.puls4.com/api/json-fe/page/"
highlight_url = "http://www.puls4.com/api/json-fe/page/sendungen"
show_directory = "http://www.puls4.com/api/json-fe/page/Alle-Sendungen"
detail_infos_url = "http://m.puls4.com/api/video/%s"

#paths
logopath = os.path.join(media_path,"logos")
defaultlogo = defaultbanner = os.path.join(logopath,"DefaultV2.png")
defaultbackdrop = ""

#urlib init
opener = urllib2.build_opener()
opener.addheaders = [('User-agent', 'Mozilla/5.0 (iPad; CPU OS 7_0 like Mac OS X) AppleWebKit/537.51.1 (KHTML, like Gecko) Version/7.0 Mobile/11A465 Safari/9537.53')]
 

def getMainMenu():
    addDirectory((translation(30000)).encode("utf-8"),defaultlogo,"","","","getHighlights")
    addDirectory((translation(30001)).encode("utf-8"),defaultlogo,"","","","getSendungen")
    getDynamicMenuItems()

def getDynamicMenuItems():
    json_links = getJsonContentUrls(main_url)
    for json_link in json_links:
        url = "%s%s" % (base_url,json_link['url'])
        html = common.fetchPage({'link':url })
        data = json.loads(html.get("content"))   
        if data.has_key("headingText") and data.has_key("rows"):
            title = data["headingText"].encode('UTF-8')
            addDirectory(title,defaultlogo,"","",url,"getDynamicVideo")

def getJsonContentUrl(url):
    html = common.fetchPage({'link': url})
    data = json.loads(html.get("content"))
    if data.has_key("content"):
        if len(data['content']) > 1:
            return "%s%s" % (base_url,data['content'][0]['url'])
        else:
            return "%s%s" % (base_url,data['content'][0]['url'])
            
def getJsonContentUrls(url):
    html = common.fetchPage({'link': url})
    data = json.loads(html.get("content"))
    links = []
    if data.has_key("content"):
        if len(data['content']) > 0:
            return data['content'];

            
def parseJsonDirectoryContent(url):
    html = common.fetchPage({'link': url})
    data = json.loads(html.get("content"))   
    if data.has_key("formatOverviewItems"):
        for video in data['formatOverviewItems']:
            for item in video["blocks"]:
                name = item['channel'].encode('UTF-8')
                if name != "":
                    id = item['channelId']
                    logo = "%s%s" % (base_url,video['channelLogoImg'])
                    poster = "%s%s" % (base_url,video['formatOverviewItemImgVersions']['low'])
                    fanart = "%s%s" % (base_url,video['formatOverviewItemImgVersions']['hi'])
                    desc = "%s \n%s: %s \n\n(%s)" % (name,item['label'].encode('UTF-8'),item['title'].encode('UTF-8'),item['date'].encode('UTF-8'))
                    addDirectory(name,fanart,fanart,desc,id,"getShowByID")            

def parseJsonVideoContent(url):
    html = common.fetchPage({'link': url})
    data = json.loads(html.get("content"))   
    if data.has_key("formatOverviewItems"):
        for video in data['formatOverviewItems']:
            for item in video["blocks"]:
                name = item['channel'].encode('UTF-8')
                if name != "":
                    id = item['objectId']
                    title = "%s - %s" % (name,item['title'].encode('UTF-8'))
                    logo = "%s%s" % (base_url,video['channelLogoImg'])
                    poster = "%s%s" % (base_url,video['formatOverviewItemImgVersions']['low'])
                    fanart = "%s%s" % (base_url,video['formatOverviewItemImgVersions']['hi'])
                    desc = "%s \n%s\n%s \n\n(%s)" % (name,video['announcement'].encode('UTF-8'),item['title'].encode('UTF-8'),item['date'].encode('UTF-8'))
                    if video.has_key("isVideo"):
                        isVideo = video_item["isVideo"]
                    else:
                        isVideo = False
                    addDirectory(title,fanart,fanart,desc,id,"getShowByID",isVideo)
                
def parseJsonGridVideoContent(url):
    html = common.fetchPage({'link': url})
    data = json.loads(html.get("content"))   
    if data.has_key("rows"):
        for video in data['rows']:
            for item in video["cols"]:
                if item.has_key("content"):
                    for video_item in item['content']:
                        isVideo = False
                        name = video_item['channel'].encode('UTF-8')
                        if video_item.has_key("isVideo") and video_item["isVideo"]:
                            isVideo = video_item["isVideo"]
                            id = video_item['objectId']
                        else:
                            id = video_item['channelId']
                        title = "%s - %s" % (name,video_item['title'].encode('UTF-8'))
                        logo = video_item['previewLink']
                        poster = video_item['previewLinkVersions']['low']
                        fanart = video_item['previewLinkVersions']['hi']
                        if video_item.has_key("description"):
                            desc = video_item['description'].encode('UTF-8')
                        else:
                            desc = ""                        
                        
                        if video_item.has_key("date"):
                            date = "(%s)" % video_item['date'].encode('UTF-8')
                        else:
                            date = ""
                            
                        subline = "%s\n%s\n\n%s" % (name,desc,date)
                        addDirectory(title,fanart,fanart,subline,id,"getShowByID",isVideo)
                
def getJSONVideos(url):
    html = common.fetchPage({'link': url})
    data = json.loads(html.get("content"))   
    if data.has_key("videos"):
        for video in data['videos']:
            image = video["picture"]["orig"].encode('UTF-8')
            id = video['id']
            desc = cleanText(video["description"].encode('UTF-8'))
            duration = video["duration"]
            date = video["broadcast_date"].encode('UTF-8')
            time = video["broadcast_time"].encode('UTF-8')
            utime = video["broadcast_datetime"]
            
            day = datetime.datetime.fromtimestamp(float(utime)).strftime('%d').lstrip('0')
            
            hour = datetime.datetime.fromtimestamp(float(utime)).strftime('%H').lstrip('0')
            min = datetime.datetime.fromtimestamp(float(utime)).strftime('%M')
            weekday = datetime.datetime.fromtimestamp(float(utime)).strftime('%A')
            weekday = translateDay(weekday)
            
            year = datetime.datetime.fromtimestamp(float(utime)).strftime('%Y')
            month = datetime.datetime.fromtimestamp(float(utime)).strftime('%m')
            aired = weekday+", "+day+"."+month+"."+year+" ("+hour+":"+min+")"
            channel = video["channel"]["name"].encode('UTF-8')
            title = cleanText(video["title"].encode('UTF-8'))
            videourl = ""
            addDirectory(title,image,"",channel+"\n"+aired+"\n"+desc,id,"getShowByID")

def translateDay(day):  
    if day == "Monday":
        return "Montag"
    elif day == "Tuesday":
        return "Dienstag"
    elif day == "Wednesday":
        return "Mittwoch"
    elif day == "Thursday":
        return "Donnerstag"
    elif day == "Friday":
        return "Freitag"
    elif day == "Saturday":
        return "Samstag"
    elif day == "Sunday":
        return "Sonntag"
    return day
    
        
def getShowByID(id):
    url = detail_infos_url % id
    html = common.fetchPage({'link': url})
    data = json.loads(html.get("content"))   
    for video in data:
        image = video["picture"]["orig"].encode('UTF-8')
        desc = cleanText(video["description"].encode('UTF-8'))
        duration = video["duration"]
        date = video["broadcast_date"].encode('UTF-8')
        time = video["broadcast_time"].encode('UTF-8')
        utime = video["broadcast_datetime"]
           
        day = datetime.datetime.fromtimestamp(float(utime)).strftime('%d').lstrip('0')
            
        hour = datetime.datetime.fromtimestamp(float(utime)).strftime('%H').lstrip('0')
        min = datetime.datetime.fromtimestamp(float(utime)).strftime('%M')
        weekday = datetime.datetime.fromtimestamp(float(utime)).strftime('%A')
        weekday = translateDay(weekday)
            
        year = datetime.datetime.fromtimestamp(float(utime)).strftime('%Y')
        month = datetime.datetime.fromtimestamp(float(utime)).strftime('%m')
        aired = weekday+", "+day+"."+month+"."+year+" ("+hour+":"+min+")"
        channel = video["channel"]["name"].encode('UTF-8')
        title = cleanText(video["title"].encode('UTF-8'))
        videourl = ""
        if video["files"]["h3"]:
            if video["files"]["h3"]["url"]:
                videourl = video["files"]["h3"]["url"]
        if videourl == "":
            if video["files"]["h1"]:
                if video["files"]["h1"]["url"]:
                    videourl = video["files"]["h1"]["url"]
        if videourl != "":
            createListItem(title,image,channel+"\n"+aired+"\n"+desc,duration,date,channel,videourl,"True",False,None)

    
############################
# s0fakings little helpers #
############################
def listCallback(sort,viewMode=defaultViewMode):
    xbmcplugin.setContent(pluginhandle,'episodes')
    if sort:
        xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_TITLE)
    xbmcplugin.endOfDirectory(pluginhandle)
    xbmc.executebuiltin(viewMode)

def createListItem(title,banner,description,duration,date,channel,videourl,playable,folder,subtitles=None,width=1280,height=720): 
    if banner == '':
        banner = defaultbanner
    if description == '':
        description = (translation(30004)).encode("utf-8")
    liz=xbmcgui.ListItem(title, iconImage=banner, thumbnailImage=banner)
    liz.setInfo( type="Video", infoLabels={ "Title": title } )
    liz.setInfo( type="Video", infoLabels={ "Tvshowtitle": title } )
    liz.setInfo( type="Video", infoLabels={ "Sorttitle": title } )
    liz.setInfo( type="Video", infoLabels={ "Plot": description } )
    liz.setInfo( type="Video", infoLabels={ "Plotoutline": description } )
    liz.setInfo( type="Video", infoLabels={ "Aired": date } )
    liz.setInfo( type="Video", infoLabels={ "Studio": channel } )
    liz.setProperty('fanart_image',defaultbackdrop)
    liz.setProperty('IsPlayable', playable)
    
    if not folder:
        try:
            liz.addStreamInfo('video', { 'codec': 'h264','duration':int(duration) ,"aspect": 1.78, "width": width, "height":height})
            liz.addStreamInfo('audio', {"codec": "aac", "language": "de", "channels": 2})
            if subtitles != None:
                liz.addStreamInfo('subtitle', {"language": "de"})
        except:
            liz.addStreamInfo('video', { 'codec': 'h264',"aspect": 1.78, "width": width, "height": height})
            liz.addStreamInfo('audio', {"codec": "aac", "language": "de", "channels": 2})
            if subtitles != None:
                liz.addStreamInfo('subtitle', {"language": "de"})
            
    xbmcplugin.addDirectoryItem(handle=pluginhandle, url=videourl, listitem=liz, isFolder=folder)
    return liz
  
def addDirectory(title,banner,backdrop,description,link,mode,isVideo=False):
    parameters = {"link" : link,"title" : cleanText(title),"banner" : banner,"backdrop" : backdrop, "mode" : mode}
    u = sys.argv[0] + '?' + urllib.urlencode(parameters)
    createListItem(title,banner,description,'','','',u,'false',True)
    
def cleanText(string):
    string = string.replace('\\n', '').replace("&#160;"," ").replace("&Ouml;","Ö").replace("&ouml;","ö").replace("&szlig;","ß").replace("&Auml;","Ä").replace("&auml;","ä").replace("&Uuml;","Ü").replace("&uuml;","ü").replace("&quot;","'").replace('&amp;', '&').replace('&#039;', '´')
    return string

def parameters_string_to_dict(parameters):
    paramDict = {}
    if parameters:
        paramPairs = parameters[1:].split("&")
        for paramsPair in paramPairs:
            paramSplits = paramsPair.split('=')
            if (len(paramSplits)) == 2:
                paramDict[paramSplits[0]] = paramSplits[1]
    return paramDict

       
#Getting Parameters
params=parameters_string_to_dict(sys.argv[2])
mode=params.get('mode')
title=params.get('title')
link=params.get('link')
backdrop=params.get('backdrop')


if mode == 'getHighlights':
    json_link = getJsonContentUrl(highlight_url)
    parseJsonVideoContent(json_link)
    listCallback(False,defaultViewMode)
if mode == 'getDynamicVideo':
    link = urllib.unquote(link)
    parseJsonGridVideoContent(link)
    listCallback(False,defaultViewMode)
if mode == 'getShowByID':
    getShowByID(link)
    listCallback(False,defaultViewMode)
if mode == 'getSendungen':
    json_link = getJsonContentUrl(show_directory)
    parseJsonDirectoryContent(json_link)
    listCallback(False,defaultViewMode)
else:
    getMainMenu()
    listCallback(False,defaultViewMode)
