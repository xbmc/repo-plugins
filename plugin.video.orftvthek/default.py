#!/usr/bin/python
# -*- coding: utf-8 -*-

import urllib,urllib2,re,xbmcplugin,xbmcgui,sys,xbmcaddon,base64,socket,datetime,time,os,os.path,urlparse,json
import CommonFunctions as common

try:
   import StorageServer
except:
   import storageserverdummy as StorageServer

socket.setdefaulttimeout(30) 
cache = StorageServer.StorageServer("plugin.video.orftvthek", 999999)

version = "0.3.1"
plugin = "ORF-TVthek-" + version
author = "sofaking"

#initial
common.plugin = plugin
settings = xbmcaddon.Addon(id='plugin.video.orftvthek') 
pluginhandle = int(sys.argv[1])
basepath = settings.getAddonInfo('path')
translation = settings.getLocalizedString

current_skin = xbmc.getSkinDir();

print current_skin
if 'confluence' in current_skin:
   defaultViewMode = 'Container.SetViewMode(503)'
else:
   defaultViewMode = 'Container.SetViewMode(518)'

thumbViewMode = 'Container.SetViewMode(500)'
smallListViewMode = 'Container.SetViewMode(51)'
playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO) 
opener = urllib2.build_opener()
opener.addheaders = [('User-agent', 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/535.7 (KHTML, like Gecko) Chrome/16.0.912.77 Safari/535.7')]

 
#hardcoded
base_url="http://tvthek.orf.at" 
resource_path = os.path.join( basepath, "resources" )
media_path = os.path.join( resource_path, "media" )

videoProtocol = "http"
videoDelivery = "progressive"
video_quality_list = ["q1a", "q4a", "q6a"]
defaultbanner =  os.path.join(media_path,"default_banner.jpg")
defaultbackdrop = os.path.join(media_path,"fanart_top.png")

schedule_url = 'http://tvthek.orf.at/schedule'
recent_url = 'http://tvthek.orf.at/newest'
live_url = "http://tvthek.orf.at/live"
mostviewed_url = 'http://tvthek.orf.at/most_viewed'
tip_url = 'http://tvthek.orf.at/tips'
search_base_url = 'http://tvthek.orf.at/search'

#settings
forceView = settings.getSetting("forceView") == "true"
videoQuality = settings.getSetting("videoQuality")
try:
    videoQuality = video_quality_list[int(videoQuality)]
except:
    videoQuality = video_quality_list[2]
livestreamInfo = settings.getSetting("livestreamInfo")


def parameters_string_to_dict(parameters):
    paramDict = {}
    if parameters:
        paramPairs = parameters[1:].split("&")
        for paramsPair in paramPairs:
            paramSplits = paramsPair.split('=')
            if (len(paramSplits)) == 2:
                paramDict[paramSplits[0]] = paramSplits[1]
    return paramDict

def cleanText(string):
    string = string.replace('\\n', '').replace("&#160;"," ").replace("&quot;","'").replace('&amp;', '&').replace('&#039;', '´')
    return string	

def createListItem(title,banner,description,duration,date,channel,videourl,playable,folder,subtitles=None): 
    if banner == '':
        banner = defaultbanner
    if description == '':
        description = (translation(30008)).encode("utf-8")
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
            liz.addStreamInfo('video', { 'codec': 'h264','duration':int(duration) ,"aspect": 1.78, "width": 640, "height": 360})
            liz.addStreamInfo('audio', {"codec": "aac", "language": "de", "channels": 2})
            if subtitles != None:
                liz.addStreamInfo('subtitle', {"language": "de"})
        except:
            liz.addStreamInfo('video', { 'codec': 'h264',"aspect": 1.78, "width": 640, "height": 360})
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

def getVideoUrl(sources):
    for source in sources:
        if source["protocol"].lower() == videoProtocol:
            if source["delivery"].lower() == videoDelivery:
                if source["quality"].lower() == videoQuality:
                    return source["src"]
    return False
    
def getLinks(url,banner):
    playlist.clear()
    videoUrls = []
    url = urllib.unquote(url)
    
    if banner != None:
        banner = urllib.unquote(banner)
        
    html = common.fetchPage({'link': url})
    data = common.parseDOM(html.get("content"),name='div',attrs={'class': "jsb_ jsb_VideoPlaylist"},ret='data-jsb')
    data = data[0]
    data = common.replaceHTMLCodes(data)
    data = json.loads(data)
    
    video_items = data.get("playlist")["videos"]
    
    try:
        current_title_prefix = data.get("selected_video")["title_prefix"]
        current_title = data.get("selected_video")["title"]
        current_desc = data.get("selected_video")["description"].encode('UTF-8')
        current_duration = data.get("selected_video")["duration"]
        current_preview_img = data.get("selected_video")["preview_image_url"]
        if "subtitles" in data.get("selected_video"):
            current_subtitles = data.get("selected_video")["subtitles"]
        else:
            current_subtitles = ''
        current_id = data.get("selected_video")["id"]
        current_videourl = getVideoUrl(data.get("selected_video")["sources"]);
    except Exception, e:
        current_subtitles = ''

    if len(video_items) > 1:
        parameters = {"mode" : "playList"}
        u = sys.argv[0] + '?' + urllib.urlencode(parameters)
        createListItem("[ "+(translation(30015)).encode("utf-8")+" ]",banner,(translation(30015)).encode("utf-8"),"","","",u,'false',False)
        for video_item in video_items:
            try:
                title_prefix = video_item["title_prefix"]
                title = video_item["title"].encode('UTF-8')
                desc = video_item["description"].encode('UTF-8')
                duration = video_item["duration"]
                preview_img = video_item["preview_image_url"]
                id = video_item["id"]
                sources = video_item["sources"]
                if "subtitles" in video_item:
                    subtitles = video_item["subtitles"]
                else:
                    subtitles = ''
                videourl = getVideoUrl(sources);
                listItem = createListItem(title,preview_img,desc,duration,'','',videourl,'true',False,subtitles)
                playlist.add(videourl,listItem)
            except Exception, e:
                continue
    else:
        listItem = createListItem(current_title,current_preview_img,current_desc,current_duration,'','',current_videourl,'true',False,current_subtitles)
        playlist.add(current_videourl,listItem)
    listCallback(False)
	
def listCallback(sort,viewMode=defaultViewMode):
    xbmcplugin.setContent(pluginhandle,'episodes')
    if sort:
        xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_TITLE)
    xbmcplugin.endOfDirectory(pluginhandle)
    if forceView:
        xbmc.executebuiltin(viewMode)

def getMainMenu():
    addDirectory((translation(30000)).encode("utf-8"),defaultbanner,'',"","getNewShows")
    addDirectory((translation(30001)).encode("utf-8"),defaultbanner,'',"","getAktuelles")
    addDirectory((translation(30002)).encode("utf-8"),defaultbanner,'',"","getSendungen")
    addDirectory((translation(30003)).encode("utf-8"),defaultbanner,'',"","getThemen")
    addDirectory((translation(30004)).encode("utf-8"),defaultbanner,'',"","getLive")
    addDirectory((translation(30005)).encode("utf-8"),defaultbanner,'',"","getTipps")
    addDirectory((translation(30006)).encode("utf-8"),defaultbanner,'',"","getMostViewed")
    addDirectory((translation(30018)).encode("utf-8"),defaultbanner,"","","getArchiv")
    addDirectory((translation(30007)).encode("utf-8"),defaultbanner,'',"","searchPhrase")
    listCallback(False,thumbViewMode)

def getArchiv(url):
    html = common.fetchPage({'link': url})
    articles = common.parseDOM(html.get("content"),name='a',attrs={'class': 'day_wrapper'})
    articles_href = common.parseDOM(html.get("content"),name='a',attrs={'class': 'day_wrapper'},ret="href")
    i = 0
    
    for article in articles:
        link = articles_href[i]
        i = i+1

        day = common.parseDOM(article,name='strong',ret=False)
        if len(day) > 0:
            day = day[0].encode("utf-8")
        else:
            day = ''
        
        date = common.parseDOM(article,name='small',ret=False)
        if len(date) > 0:
            date = date[0].encode("utf-8")
        else:
            date = ''
        
        title = day + " - " + date
        
        addDirectory(title,defaultbanner,date,link,"openArchiv")
    listCallback(False)
	
def openArchiv(url):
    url =  urllib.unquote(url)
    html = common.fetchPage({'link': url})
    teasers = common.parseDOM(html.get("content"),name='a',attrs={'class': 'item_inner.clearfix'})
    teasers_href = common.parseDOM(html.get("content"),name='a',attrs={'class': 'item_inner.clearfix'},ret="href")

    i = 0
    for teaser in teasers:
        link = teasers_href[i]
        i = i+1
        
        title = common.parseDOM(teaser,name='h4',attrs={'class': "item_title"},ret=False)
        title = common.replaceHTMLCodes(title[0]).encode("utf-8")
        
        time = common.parseDOM(teaser,name='span',attrs={'class': "meta.meta_time"},ret=False)
        time = common.replaceHTMLCodes(time[0]).encode("utf-8")
		
        title = "["+time+"] "+title
		
        description = common.parseDOM(teaser,name='div',attrs={'class': "item_description"},ret=False)
        description = common.replaceHTMLCodes(description[0])
		
        banner = common.parseDOM(teaser,name='img',ret='src')
        banner = common.replaceHTMLCodes(banner[1]).encode("utf-8")
        
        banner = common.parseDOM(teaser,name='img',ret='src')
        banner = common.replaceHTMLCodes(banner[1]).encode("utf-8")
		
        addDirectory(title,banner,description,link,"openSeries")
    listCallback(True)
    
def getCategoryList(category,banner):
    url =  urllib.unquote(category)
    banner =  urllib.unquote(banner)
    
    html = common.fetchPage({'link': url})
	
    try:
        show = common.parseDOM(html.get("content"),name='h3',attrs={'class': 'video_headline'})
        showname = common.replaceHTMLCodes(show[0]).encode("utf-8")
    except:
        showname = ""
    playerHeader = common.parseDOM(html.get("content"),name='header',attrs={'class': 'player_header'})
    bcast_info = common.parseDOM(playerHeader,name='div',attrs={'class': 'broadcast_information'})
    
    try:
        current_duration = common.parseDOM(bcast_info,name='span',attrs={'class': 'meta.meta_duration'})
        current_date = common.parseDOM(bcast_info,name='span',attrs={'class': 'meta meta_date'})
        current_date = current_date[0].encode("utf-8")
        current_time = common.parseDOM(bcast_info,name='span',attrs={'class': 'meta meta_time'})
        current_link = url
        current_title = "%s - %s" % (showname,current_date)       
        try:
            current_desc = (translation(30009)).encode("utf-8")+' %s - %s\n'+(translation(30011)).encode("utf-8")+': %s' % (current_date,current_time,current_duration)
        except:
            current_desc = "";
        addDirectory(current_title,banner,current_desc,current_link,"openSeries")
    except:
        addDirectory((translation(30014)).encode("utf-8"),defaultbanner,"","","")
	
    itemwrapper = common.parseDOM(html.get("content"),name='div',attrs={'class': 'base_list_wrapper.mod_latest_episodes'})
    if len(itemwrapper) > 0:
        items = common.parseDOM(itemwrapper,name='li',attrs={'class': 'base_list_item'})
        feedcount = len(items)
        i = 0
        for item in items:
            i = i+1
            duration = common.parseDOM(item,name='span',attrs={'class': 'meta.meta_duration'})
            date = common.parseDOM(item,name='span',attrs={'class': 'meta.meta_date'})
            date = date[0].encode("utf-8")
            time = common.parseDOM(item,name='span',attrs={'class': 'meta.meta_time'})
            title = "%s - %s" % (showname,date)
            title = "%s - %s" % (showname,date)
            link = common.parseDOM(item,name='a',ret="href")
            try:
                desc = (translation(30009)).encode("utf-8")+" %s - %s\n"+(translation(30011)).encode("utf-8")+": %s" % (date,time,duration)
            except:
                desc = "";
            addDirectory(title,banner,desc,link,"openSeries")
    listCallback(False)

def getLiveStreams():
    liveurls = {}
    liveurls['ORF1'] = "http://apasfiisl.apa.at/ipad/orf1_q6a/orf.sdp/playlist.m3u8";
    liveurls['ORF2'] = "http://apasfiisl.apa.at/ipad/orf2_q6a/orf.sdp/playlist.m3u8";
    liveurls['ORF3'] = "http://apasfiisl.apa.at/ipad/orf2e_q6a/orf.sdp/playlist.m3u8";
    liveurls['ORFS'] = "http://apasfiisl.apa.at/ipad/orfs_q6a/orf.sdp/playlist.m3u8";
	
    html = common.fetchPage({'link': live_url})
    wrapper = common.parseDOM(html.get("content"),name='div',attrs={'class': 'base_list_wrapper.*mod_epg'})
    items = common.parseDOM(wrapper[0],name='li',attrs={'class': 'base_list_item.program.*?'})
    items_class = common.parseDOM(wrapper[0],name='li',attrs={'class': 'base_list_item.program.*?'},ret="class")
    i = 0
    for item in items:
        program = common.parseDOM(item,ret="class")
        program = items_class[i].split(" ")[2].encode('UTF-8').upper()

        i += 1
        
        banner = common.parseDOM(item,name='img',ret="src")
        banner = common.replaceHTMLCodes(banner[0]).encode('UTF-8')
        
        title = common.parseDOM(item,name='h4')
        title = common.replaceHTMLCodes(title[0]).encode('UTF-8')
        
        time = common.parseDOM(item,name='span',attrs={'class': 'meta.meta_time'})
        time = common.replaceHTMLCodes(time[0]).encode('UTF-8').replace("Uhr","").replace(".",":").strip()

        if getBroadcastState(time):
            state = (translation(30019)).encode("utf-8")
            state_short = "Online"
        else:
            state = (translation(30020)).encode("utf-8")
            state_short = "Offline"

        link = liveurls[program]
        
        title = "[%s] - %s (%s)" % (program,title,time)
        createListItem(title,banner,state,time,program,program,link,'true',False)
    listCallback(False,smallListViewMode)

def getBroadcastState(time):
    time_probe = time.split(":")
        
    current_hour = datetime.datetime.now().strftime('%H')
    current_min = datetime.datetime.now().strftime('%M')
    if time_probe[0] == current_hour and time_probe[1] >= current_min:
        return False
    elif time_probe[0] > current_hour:
        return False
    else:
        return True
    
def getRecentlyAdded():
    html = common.fetchPage({'link': base_url})
    html_content = html.get("content")
    teaserbox = common.parseDOM(html_content,name='a',attrs={'class': 'item_inner'})
    teaserbox_href = common.parseDOM(html_content,name='a',attrs={'class': 'item_inner'},ret="href")

    i = 0
    for teasers in teaserbox:
        link = teaserbox_href[i]
        i = i+1
        title = common.parseDOM(teasers,name='h3',attrs={'class': 'item_title'})
        title = common.replaceHTMLCodes(title[0]).encode('UTF-8')
        
        desc = common.parseDOM(teasers,name='div',attrs={'class': 'item_description'})
        desc = common.replaceHTMLCodes(desc[0]).encode('UTF-8')
        
        image = common.parseDOM(teasers,name='img',ret="src")
        image = common.replaceHTMLCodes(image[0]).encode('UTF-8')
        
        addDirectory(title,image,desc,link,"openSeries")
    listCallback(False)

def getThemenListe(url):
    url = urllib.unquote(url)
    html = common.fetchPage({'link': url})
    html_content = html.get("content")
	
    content = common.parseDOM(html_content,name='section',attrs={'class':'mod_container_list'})
    topics = common.parseDOM(content,name='article',attrs={'class':'item.*?'})

    for topic in topics:
        title = common.parseDOM(topic,name='h4',attrs={'class': 'item_title'})
        title = common.replaceHTMLCodes(title[0]).encode('UTF-8')
        
        link = common.parseDOM(topic,name='a',ret="href")
        link = common.replaceHTMLCodes(link[0]).encode('UTF-8')
        
        image = common.parseDOM(topic,name='img',ret="src")
        if len(image) > 0:
            image = common.replaceHTMLCodes(image[0]).encode('UTF-8')
        else:
            image = defaultbanner
            
        desc = common.parseDOM(topic,name='div',attrs={'class':'item_description'})
        if len(desc) > 0:
            desc = common.replaceHTMLCodes(desc[0]).encode('UTF-8')
        else:
            desc = ""

        date = common.parseDOM(topic,name='time')
        date = common.replaceHTMLCodes(date[0]).encode('UTF-8')

        time = common.parseDOM(topic,name='span',attrs={'class':'meta.meta_duration'})
        time = common.replaceHTMLCodes(time[0]).encode('UTF-8')

        desc = "%s - (%s) \n%s" % (str(date),str(time).strip(),str(desc))
        
        addDirectory(title,image,desc,link,"openSeries")
    listCallback(False)

def playFile():
    player = xbmc.Player()
    player.play(playlist)
    if not player.isPlayingVideo():
        d = xbmcgui.Dialog()
        d.ok('VIDEO QUEUE EMPTY', 'The XBMC video queue is empty.','Add more links to video queue.')

def getThemen():
    url = "http://tvthek.orf.at/topics"
    html = common.fetchPage({'link': url})
    html_content = html.get("content")
    
    content = common.parseDOM(html_content,name='section',attrs={'class':'mod_container_list'})
    topics = common.parseDOM(content,name='section',attrs={'class':'item_wrapper'})

    for topic in topics:
        title = common.parseDOM(topic,name='h3',attrs={'class':'item_wrapper_headline.subheadline.*?'})
        title = common.replaceHTMLCodes(title[0]).encode('UTF-8')
        
        link = common.parseDOM(topic,name='a',attrs={'class':'more.service_link.service_link_more'},ret="href")
        link = common.replaceHTMLCodes(link[0]).encode('UTF-8')
        
        image = common.parseDOM(topic,name='img',ret="src")
        image = common.replaceHTMLCodes(image[0]).replace("width=395","width=500").replace("height=209.07070707071","height=265").encode('UTF-8')
        
        descs = common.parseDOM(topic,name='h4',attrs={'class':'item_title'})
        description = ""
        for desc in descs:
            description += "* "+common.replaceHTMLCodes(desc).encode('UTF-8') + "\n"

        addDirectory(title,image,description,link,"openTopicPosts")
    listCallback(True)

def getCategories():
    html = common.fetchPage({'link': base_url})
    html_content = html.get("content")
    
    content = common.parseDOM(html_content,name='div',attrs={'class':'mod_carousel'})
    items = common.parseDOM(content,name='a',attrs={'class':'carousel_item_link'})
    items_href = common.parseDOM(content,name='a',attrs={'class':'carousel_item_link'},ret="href")
    i = 0
    for item in items:
        link = common.replaceHTMLCodes(items_href[i]).encode('UTF-8')
        i = i + 1
        title = programUrlTitle(link).encode('UTF-8')
        
        image = common.parseDOM(item,name='img',ret="src")
        image = common.replaceHTMLCodes(image[0]).replace("height=56","height=280").replace("width=100","width=500").encode('UTF-8')

        desc = '  '
        addDirectory(title,image,desc,link,"openCategoryList")
    listCallback(True,thumbViewMode)

def programUrlTitle(url):
    title = url.replace(base_url,"").split("/")
    if title[1] == 'index.php':
        return title[3].replace("-"," ")
    else:
        return title[2].replace("-"," ")
		
def search():
    addDirectory((translation(30007)).encode("utf-8")+" ...",defaultbanner,' ',"","searchNew")
    cache.table_name = "searchhistory"
    some_dict = cache.get("searches").split("|")
    for str in reversed(some_dict):
        if str.strip() != '':
            addDirectory(str.encode('UTF-8'),defaultbanner," ",str.replace(" ","+"),"searchNew")
    listCallback(False)
	
def searchTV():
    keyboard = xbmc.Keyboard('')
    keyboard.doModal()
    if (keyboard.isConfirmed()):
      cache.table_name = "searchhistory"
      keyboard_in = keyboard.getText()
      some_dict = cache.get("searches") + "|"+keyboard_in
      cache.set("searches",some_dict);
      searchurl = "%s/search?q=%s"%(base_url,keyboard_in.replace(" ","+").replace("Ö","").replace("ö","").replace("Ü","").replace("ü","").replace("Ä","").replace("ä",""))
      searchurl = searchurl
      getTableResults(searchurl)
    else:
      addDirectory((translation(30014)).encode("utf-8"),defaultbanner,"","","")
    listCallback(False)

def getTableResults(url):
    url = urllib.unquote(url)
    html = common.fetchPage({'link': url})
    items = common.parseDOM(html.get("content"),name='article',attrs={'class': "item.*?"},ret=False)
    
    i = 1
    for item in items:
        i = i+1
        title = common.parseDOM(item,name='h4',attrs={'class': "item_title"},ret=False)
        title = common.replaceHTMLCodes(title[0]).encode('UTF-8')
        desc = common.parseDOM(item,name='div',attrs={'class': "item_description"},ret=False)
        time = ""
        date = ""
        if desc != None and len(desc) > 0:
            desc = common.replaceHTMLCodes(desc[0]).encode('UTF-8')
            date = common.parseDOM(item,name='time',attrs={'class':'meta.meta_date'},ret=False)
            date = date[0].encode('UTF-8')
            time = common.parseDOM(item,name='span',attrs={'class':'meta.meta_time'},ret=False)
            time = time[0].encode('UTF-8')
            desc = (translation(30009)).encode("utf-8")+' %s - %s\n%s' % (date,time,desc)
        else:
            desc = (translation(30008)).encode("utf-8")
            
        image = common.parseDOM(item,name='img',attrs={},ret='src')
        image = common.replaceHTMLCodes(image[0]).encode('UTF-8')
        link = common.parseDOM(item,name='a',attrs={},ret='href')
        link = link[0].encode('UTF-8')
        if date != "":
            title = "%s - %s" % (title,date)
        addDirectory(title,image,desc,link,"openSeries")
    listCallback(False)
				
def searchTVHistory(link):
    keyboard = xbmc.Keyboard(link)
    keyboard.doModal()
    if (keyboard.isConfirmed()):
      cache.table_name = "searchhistory"
      keyboard_in = keyboard.getText()
      if keyboard_in != link:
           some_dict = cache.get("searches") + "|"+keyboard_in
           cache.set("searches",some_dict);
      searchurl = "%s?q=%s"%(search_base_url,keyboard_in.replace(" ","+"))
      getTableResults(searchurl)
    else:
      addDirectory((translation(30014)).encode("utf-8"),defaultbanner,defaultbackdrop,"","")
    listCallback(False)
    	
#parameters
params=parameters_string_to_dict(sys.argv[2])
mode=params.get('mode')
title=params.get('title')
link=params.get('link')
banner=params.get('banner')
backdrop=params.get('backdrop')

#modes
if mode == 'openSeries':
    getLinks(link,banner)
elif mode == 'openShowList':
    getMoreShows(link,banner,backdrop)
elif mode == 'openCategoryList':
    getCategoryList(link,banner)
elif mode == 'getSendungen':
    getCategories()
elif mode == 'getAktuelles':
    getRecentlyAdded()
elif mode == 'getLive':
    getLiveStreams()
elif mode == 'getTipps':
    getTableResults(tip_url)
elif mode == 'getNewShows':
    getTableResults(recent_url)
elif mode == 'getMostViewed':
    getTableResults(mostviewed_url)
elif mode == 'getThemen':
    getThemen()
elif mode == 'openTopicPosts':
    getThemenListe(link)
elif mode == 'playVideo':
    playFile()
elif mode == 'playList':
    playFile()
elif mode == 'getArchiv':
    getArchiv(schedule_url)
elif mode == 'openArchiv':
    openArchiv(link)
elif mode == 'searchPhrase':
    search()
elif mode == 'searchNew':
    if not link == None:
        searchTVHistory(urllib.unquote(link));
    else:
        searchTV()
else:
    getMainMenu()
