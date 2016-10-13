#!/usr/bin/python
# -*- coding: utf-8 -*-

import urllib,urllib2,re,xbmcplugin,xbmcgui,sys,xbmcaddon,base64,socket,datetime,time,os,os.path,urlparse,json
import CommonFunctions as common

version = "0.2.2"
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

#paths
logopath = os.path.join(media_path,"logos")
defaultlogo = defaultbanner = os.path.join(logopath,"DefaultV2.png")
defaultbackdrop = ""

#urlib init
opener = urllib2.build_opener()
opener.addheaders = [('User-agent', 'Mozilla/5.0 (iPad; CPU OS 7_0 like Mac OS X) AppleWebKit/537.51.1 (KHTML, like Gecko) Version/7.0 Mobile/11A465 Safari/9537.53')]
 

def getMainMenu():
    addDirectory((translation(30000)).encode("utf-8"),defaultlogo,"","","getHighlights")
    addDirectory((translation(30001)).encode("utf-8"),defaultlogo,"","","getSendungen")
    #addDirectory((translation(30002)).encode("utf-8"),defaultlogo,"","","getTopVideos")
    

def getPageTopItems():
    html = common.fetchPage({'link': top_url})
    data = json.loads(html.get("content"))    
    for video in data['content']:
        section_url = base_url+video['url']
        html_section = common.fetchPage({'link': section_url})
        data_section = json.loads(html_section.get("content"))
        if data_section.has_key("slides"):
            for item in data_section['slides']:
                print item['title'].encode('UTF-8')
        else:
            print data_section
    
def getJSONVideos(url):
    print url
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
            addDirectory(title,image,channel+"\n"+aired+"\n"+desc,id,"getShowByID")

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
                
def getJSONSendungen(url):
    html = common.fetchPage({'link': url})
    data = json.loads(html.get("content"))   
    for show in data:
        try:
            image = show["logo"]["orig"].encode('UTF-8')
        except:
            image = ""
        id = show["id"]
        title = cleanText(show["name"].encode('UTF-8'))
        addDirectory(title,image,"",id,"getShowByID")
        
        
def getShowByID(id):
    url = "http://m.puls4.com/api/video/"+id
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

def addFile(name,videourl,banner,summary,runtime,backdrop):
    createListItem(name,banner,summary,runtime,'','',videourl,'true',False,'')
    
def addDirectory(title,banner,description,link,mode):
    parameters = {"link" : link,"title" : cleanText(title),"banner" : banner,"backdrop" : defaultbackdrop, "mode" : mode}
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
logo=params.get('logo')
category=params.get('category')
backdrop=params.get('backdrop')


if mode == 'getHighlights':
    getJSONVideos(highlight_url)
    getJSONVideos(highlight_view_url)
    listCallback(False,defaultViewMode)
if mode == 'getTopVideos':
    getPageTopItems()
    listCallback(False,defaultViewMode)
if mode == 'getShowByID':
    getShowByID(link)
    listCallback(False,defaultViewMode)
if mode == 'getSendungen':
    getJSONSendungen(show_url)
    listCallback(False,defaultViewMode)
if mode == 'searchPhrase':
    searchVideos()
else:
    getMainMenu()
    listCallback(False,defaultViewMode)