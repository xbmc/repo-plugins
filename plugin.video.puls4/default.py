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

#urls
base_url = "http://m.puls4.com"
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
                    addDirectory(title,poster,fanart,desc,id,"getShowByID",isVideo)
                
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
                        addDirectory(title,poster,fanart,subline,id,"getShowByID",isVideo)

def translateDay(day):  
    if day == "Monday":
        return (translation(30005)).encode('UTF-8')
    elif day == "Tuesday":
        return (translation(30006)).encode('UTF-8')
    elif day == "Wednesday":
        return (translation(30007)).encode('UTF-8')
    elif day == "Thursday":
        return (translation(30008)).encode('UTF-8')
    elif day == "Friday":
        return (translation(30009)).encode('UTF-8')
    elif day == "Saturday":
        return (translation(30010)).encode('UTF-8')
    elif day == "Sunday":
        return (translation(30011)).encode('UTF-8')
    return day
    
        
def getShowByID(id):
    url = detail_infos_url % id
    html = common.fetchPage({'link': url})
    data = json.loads(html.get("content"))   
    for video in data:
        banner = video["picture"]["orig"].encode('UTF-8')
        outline = cleanText(video["description"].encode('UTF-8'))
        duration = video["duration"]

        broadcast_date_ts = float(video["broadcast_datetime"])
        broadcast_date = datetime.datetime.fromtimestamp(broadcast_date_ts)
        aired = formatAiredString(broadcast_date)
        
        title = cleanText(video["title"].encode('UTF-8'))
        channel = video["channel"]["name"].encode('UTF-8')
        description = channel+"\n"+aired+"\n\n"+outline
        
        videourl = ""
        if video["files"]["h3"]:
            if video["files"]["h3"]["url"]:
                videourl = video["files"]["h3"]["url"]
        if videourl == "":
            if video["files"]["h1"]:
                if video["files"]["h1"]["url"]:
                    videourl = video["files"]["h1"]["url"]
        if videourl != "":
            createListItem(title,banner,defaultbackdrop,description,duration,broadcast_date_ts,channel,videourl,"True",False,None)


    
############################
# s0fakings little helpers #
############################
def formatAiredString(airedDate):
    try:
        return '%s, %02d.%02d.%d - %d:%02d' % (translateDay(airedDate.strftime('%A')), airedDate.day, airedDate.month, airedDate.year, airedDate.hour, airedDate.minute)
    except:
        return ""

def listCallback(sort):
    xbmcplugin.setContent(pluginhandle,'videos')
    if sort:
        xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_TITLE)
    xbmcplugin.endOfDirectory(pluginhandle)

def createListItem(title,banner,backdrop,description,duration,date,channel,videourl,playable,folder,subtitles=None,width=1280,height=720): 
    if banner == '':
        banner = defaultbanner    
    if backdrop == '':
        backdrop = defaultbackdrop
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
    
    liz.setProperty('fanart_image',backdrop)
    liz.setProperty('IsPlayable', playable)
    
    if not folder:
        try:
            liz.setInfo( type="Video", infoLabels={ "mediatype" : 'video'})
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
  
def addDirectory(title,banner,backdrop,description,link,mode,isVideo=False):
    if banner == '':
        banner = defaultbanner    
    if backdrop == '':
        backdrop = defaultbackdrop
    parameters = {"link" : link,"title" : cleanText(title),"banner" : banner,"backdrop" : backdrop, "mode" : mode}
    u = sys.argv[0] + '?' + urllib.urlencode(parameters)
    createListItem(title,banner,backdrop,description,'','','',u,'false',True)
    
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
    listCallback(False)
if mode == 'getDynamicVideo':
    link = urllib.unquote(link)
    parseJsonGridVideoContent(link)
    listCallback(False)
if mode == 'getShowByID':
    getShowByID(link)
    listCallback(False)
if mode == 'getSendungen':
    json_link = getJsonContentUrl(show_directory)
    if json_link:
        parseJsonDirectoryContent(json_link)
    listCallback(False)
else:
    getMainMenu()
    listCallback(False)
