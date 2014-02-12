#!/usr/bin/python
# -*- coding: utf-8 -*-

import urllib,urllib2,re,xbmcplugin,xbmcgui,sys,xbmcaddon,base64,socket,datetime,time,os,os.path,urlparse
from BeautifulSoup import BeautifulSoup 

try:
   import StorageServer
except:
   import storageserverdummy as StorageServer
 
socket.setdefaulttimeout(30) 
cache = StorageServer.StorageServer("plugin.video.orftvthek", 999999)

version = "0.2.2"
plugin = "ORF-TVthek-" + version
author = "sofaking"
 

settings = xbmcaddon.Addon(id='plugin.video.orftvthek') 
pluginhandle = int(sys.argv[1])
basepath = settings.getAddonInfo('path')

translation = settings.getLocalizedString
base_url="http://tvthek.orf.at"

forceView = settings.getSetting("forceView") == "true"
if xbmc.getSkinDir() == 'skin.confluence':
   defaultViewMode = 'Container.SetViewMode(503)'
else:
   defaultViewMode = 'Container.SetViewMode(518)'

defaultbackdrop = os.path.join(basepath,"fanart.jpg")
defaultbanner = "http://goo.gl/FG03G"
defaultlogo = "http://goo.gl/FRLJK"

opener = urllib2.build_opener()
opener.addheaders = [('User-agent', 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/535.7 (KHTML, like Gecko) Chrome/16.0.912.77 Safari/535.7')]
playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO) 

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

def createListItem(title,banner,description,duration,date,channel,videourl,playable,folder): 
    if banner == '':
        banner = defaultbanner
    if description == '':
        description = (translation(30008)).encode("utf-8")
    liz=xbmcgui.ListItem(cleanText(title), iconImage=banner, thumbnailImage=banner)
    liz.setInfo( type="Video", infoLabels={ "Title": cleanText(title) } )
    liz.setInfo( type="Video", infoLabels={ "Tvshowtitle": cleanText(title) } )
    liz.setInfo( type="Video", infoLabels={ "Sorttitle": cleanText(title) } )
    liz.setInfo( type="Video", infoLabels={ "Plot": cleanText(description) } )
    liz.setInfo( type="Video", infoLabels={ "Plotoutline": cleanText(description) } )
    liz.setInfo( type="Video", infoLabels={ "Duration": cleanText(duration) } )
    liz.setInfo( type="Video", infoLabels={ "Aired": cleanText(date) } )
    liz.setInfo( type="Video", infoLabels={ "Studio": cleanText(channel) } )
    liz.setProperty('fanart_image',defaultbackdrop)
    liz.setProperty('IsPlayable', playable)
    xbmcplugin.addDirectoryItem(handle=pluginhandle, url=videourl, listitem=liz, isFolder=folder)
    return liz


def addFile(name,videourl,banner,summary,runtime,backdrop):
    createListItem(name,banner,summary,runtime,'','',videourl,'true',False,'')

def addDirectory(title,banner,description,link,mode):
    parameters = {"link" : link,"title" : cleanText(title),"banner" : banner,"backdrop" : defaultbackdrop, "mode" : mode}
    u = sys.argv[0] + '?' + urllib.urlencode(parameters)
    createListItem(title,banner,description,'','','',u,'false',True)

def getLinks(url,banner):
    playlist.clear()
    url = urllib.unquote(url)
    banner = urllib.unquote(banner)
    arrayReg = re.compile("{.*?}")
    html = opener.open(url)
    html = html.read()
    soup = BeautifulSoup(html)
    data = soup.find('div',{'class':'jsb_ jsb_VideoPlaylist'})
    videoUrls = []
    array = arrayReg.findall(str(data))
    #get video links
    for item in array:
        split = item.replace("{","").replace("}","").replace(",","").replace(":","").replace("\/","/").split('"')
        if split[1] == "quality" and split[3] == "Q6A":
            if len(split) > 13 and split[21] == "protocol" and split[23] == "http":
                if split[9] == "src":
                    path = urlparse.urlparse(split[11]).path
                    ext = os.path.splitext(path)[1]
                    if ext == ".mp4":
                        videoUrls.append(str(split[11]).replace("http//",'http://'))
    #check for broadcast infos
    bcast = soup.find('div',{'class':'broadcast_information'})
    bcast_desc = ''
    if bcast != None:
        bcast_date = bcast.find('span',{'class':'meta meta_date'})
        bcast_time = bcast.find('span',{'class':'meta meta_time'})
        if bcast_time != None and bcast_date != None:
            bcast_desc = (translation(30009)).encode("utf-8")+" %s - %s\n" % (bcast_date.text.encode('UTF-8'),bcast_time.text.encode('UTF-8'))
    #check if there are more playlist items
    descbox = soup.find('div',{'class':'base_list_wrapper mod_playlist'})
    if descbox != None:
        videoDescs = []
        parameters = {"mode" : "playList"}
        u = sys.argv[0] + '?' + urllib.urlencode(parameters)
        createListItem("[ "+(translation(30015)).encode("utf-8")+" ]",banner,(translation(30015)).encode("utf-8"),"","","",u,'false',False)
        details = descbox.findAll('div',{'class':'details'})
        for detail in details:
            videoDescs.append(detail.text.encode('UTF-8'))
        videoTitles = []
        titles = descbox.findAll('h4',{'class':'base_list_item_headline'})
        for title in titles:
	        videoTitles.append(title.text.encode('UTF-8'))
        i = 0
        for url in videoTitles:
            liz = createListItem(videoTitles[i],banner,"%s%s"%(bcast_desc,videoDescs[i]),'','','',videoUrls[i],'true',False)
            playlist.add(videoUrls[i],liz)
            i = i + 1
    #only one item one video page
    else:
        title = soup.find('h3',{'class':'video_headline'}).text.encode('UTF-8')
        desc = soup.find('div',{'class':'details_description'}).text.encode('UTF-8')
        link = videoUrls[0]
        createListItem(title,banner,"%s%s"%(bcast_desc,desc),'','','',link,'true',False)
    listCallback()
	
def listCallback():
    xbmcplugin.setContent(pluginhandle,'episodes')
    xbmcplugin.endOfDirectory(pluginhandle)
    if forceView:
       xbmc.executebuiltin(defaultViewMode)

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
    listCallback()

def getArchiv(url):
    progressbar = xbmcgui.DialogProgress()
    progressbar.create((translation(30010)).encode("utf-8"))
    progressbar.update(0)
	
    html = opener.open(url)
    html = html.read()
    suppn = BeautifulSoup(html)
    links = suppn.findAll('a',{'class':'day_wrapper'})
    i = 1
    feedcount = len(links)
    for link in links:
        if progressbar.iscanceled() :
            xbmcplugin.endOfDirectory(pluginhandle)
            xbmc.executebuiltin("Container.SetViewMode(503)")
            progressbar.close()
            break
        i = i+1
        percent = i*100/feedcount
        progressbar.update(percent)
        day = link.find('strong').text.encode('UTF-8')
        date = link.find('small').text.encode('UTF-8')
        title = day + " - " + date
        addDirectory(title,defaultbanner,date,link['href'],"openArchiv")
    listCallback()
	
def openArchiv(url):
    progressbar = xbmcgui.DialogProgress()
    progressbar.create((translation(30000)).encode("utf-8"))
    progressbar.update(0)
    url =  urllib.unquote(url)
    html = opener.open(url)
    html = html.read()
    suppn = BeautifulSoup(html)
    teaserbox = suppn.findAll('a',{'class':'item_inner clearfix'})
    feedcount = len(teaserbox)
    i = 0
    for teasers in teaserbox:
        if progressbar.iscanceled() :
            xbmcplugin.endOfDirectory(pluginhandle)
            progressbar.close()
            break
        i = i+1
        percent = i*100/feedcount
        progressbar.update(percent)
        title = teasers.find('h4',{'class':'item_title'}).text.encode('UTF-8')
        link = teasers['href']
        time = teasers.find('span',{'class':'meta meta_time'}).text.encode('UTF-8')
        title = "["+time+"] "+title
        desc = teasers.find('div',{'class':'item_description'}).text.encode('UTF-8').strip()
        banner = teasers.find('figure',{'class':'item_image'}).find('img')['src'].replace("width=395","width=500").replace("height=209.07070707071","height=265").encode('UTF-8')
        addDirectory(title,banner,desc,link,"openSeries")
    listCallback()
	
def getCategoryList(category,banner):
    progressbar = xbmcgui.DialogProgress()
    progressbar.create((translation(30000)).encode("utf-8"))
    progressbar.update(0)

    url =  urllib.unquote(category)
    banner =  urllib.unquote(banner)
    html = opener.open(url)
    html = html.read()
    soup = BeautifulSoup(html)
	
    try:
        showname = soup.find('h3',{'class':'video_headline'}).text.encode('UTF-8')
    except:
        showname = ""
    new = soup.find('header',{'class':'player_header'}).find('div',{'class':'broadcast_information'})
    new_duration = new.find('span',{'class':'meta meta_duration'}).text.encode('UTF-8')
    new_date = new.find('span',{'class':'meta meta_date'}).text.encode('UTF-8')
    new_time = new.find('span',{'class':'meta meta_time'}).text.encode('UTF-8')
    new_link = url
    new_title = "%s - %s" % (showname,new_date)
    try:
        new_desc = (translation(30009)).encode("utf-8")+' %s - %s\n'+(translation(30011)).encode("utf-8")+': %s' % (new_date,new_time,new_duration)
    except:
        new_desc = "";
    addDirectory(new_title,banner,new_desc,new_link,"openSeries")
	
    progressbar.update(15)
    latest = soup.find('div',{'class':'base_list_wrapper mod_latest_episodes'})
    if latest != None:
      latestbox = latest.findAll('li',{'class':'base_list_item'})
      feedcount = len(latestbox)
      i = 1
      for item in latestbox:
        i = i+1
        percent = i*100/feedcount
        progressbar.update(percent)
        duration = item.find('span',{'class':'meta meta_duration'}).text.encode('UTF-8')
        date = item.find('span',{'class':'meta meta_date'}).text.encode('UTF-8')
        time = item.find('span',{'class':'meta meta_time'}).text.encode('UTF-8')
        title = "%s - %s" % (showname,date)
        title = "%s - %s" % (showname,date)
        link = item.find('a')['href']
        try:
            desc = (translation(30009)).encode("utf-8")+" %s - %s\n"+(translation(30011)).encode("utf-8")+": %s" % (date,time,duration)
        except:
            desc = "";
        addDirectory(title,banner,desc,link,"openSeries")
    listCallback()


def getLiveStreams():
    url = "http://tvthek.orf.at/live"
    liveurls = {}
    liveurls['ORF1'] = "http://apasfiisl.apa.at/ipad/orf1_q4a/orf.sdp/playlist.m3u8";
    liveurls['ORF2'] = "http://apasfiisl.apa.at/ipad/orf2_q6a/orf.sdp/playlist.m3u8";
    liveurls['ORF3'] = "http://apasfiisl.apa.at/ipad/orf2e_q6a/orf.sdp/playlist.m3u8";
    liveurls['ORFS'] = "http://apasfiisl.apa.at/ipad/orfs_q6a/orf.sdp/playlist.m3u8";
	
    html = opener.open(url)
    html = html.read()
    soup = BeautifulSoup(html)
	
    epg = soup.find('ul',{'class':'base_list epg'})
    epgbox = epg.findAll('li',{'class':re.compile(r'\bbase_list_item program\b')})
    for item in epgbox:
        program = item.get('class', []).split(" ")[2].encode('UTF-8').upper()
        banner = ''
        title = item.find('h4').text.encode('UTF-8')
        time = item.find('div',{'class':'broadcast_information'}).find('span').text.encode('UTF-8').replace("Uhr","").replace(".",":").strip()
        link = liveurls[program]
        
        title = "[%s] %s (%s)" % (program,title,time)
        createListItem(title,banner,'djsjsj',time,'jsdjjs',program,link,'true',False)
    listCallback()

def getRecentlyAdded():
    progressbar = xbmcgui.DialogProgress()
    progressbar.create('Ladevorgang' )
    progressbar.update(0)
    html = opener.open(base_url)
    html = html.read()
    soup = BeautifulSoup(html)
    teaserbox = soup.findAll('a',{'class':'item_inner'})
    feedcount = len(teaserbox)
    i = 0
    for teasers in teaserbox:
        if progressbar.iscanceled() :
            xbmcplugin.endOfDirectory(pluginhandle)
            progressbar.close()
            break
        i = i+1
        percent = i*100/feedcount
        progressbar.update(percent)
        title = teasers.find('h3',{'class':'item_title'}).text.encode('UTF-8')
        desc = teasers.find('div',{'class':'item_description'}).text.encode('UTF-8')
        image = teasers.find('img')['src']
        link = teasers['href'] 
        addDirectory(title,image,desc,link,"openSeries")
    listCallback()


def getThemenListe(url):
    progressbar = xbmcgui.DialogProgress()
    progressbar.create('Ladevorgang' )
    progressbar.update(0)
    url = urllib.unquote(url)
    html = opener.open(url)
    html = html.read()
    soup = BeautifulSoup(html)
	
    content = soup.find('section',{'class':'mod_container_list'})
    topics = soup.findAll('article',{'class':'item'})
	
    i = 1
    feedcount = len(topics)
    for topic in topics:
        if progressbar.iscanceled() :
            xbmcplugin.endOfDirectory(pluginhandle)
            progressbar.close()
            break
        i = i+1
        percent = i*100/feedcount
        progressbar.update(percent)
            
        title = topic.find('h4',{'class':'item_title'}).text.encode('UTF-8')
        link = topic.find('a')['href'].encode('UTF-8')
        image = topic.find('img')
        if image != None:
            image = image['src'].encode('UTF-8')
        else:
            image = ''
        desc = topic.find('div',{'class':'item_description'})
        if desc != None:
            desc = desc.text.encode('UTF-8')
        else:
            desc = (translation(30008)).encode("utf-8")
        date = topic.find('time').text.encode('UTF-8')
        time = topic.find('span',{'class':'meta meta_duration'}).text.encode('UTF-8')
        try:
            desc = (translation(30016)).encode("utf-8")+": %s \n"+(translation(30017)).encode("utf-8")+": %s \n\n%s" % (date,time,desc)
        except:
            desc = ""
        addDirectory(title,image,desc,link,"openSeries")
    listCallback()

def playFile():
    player = xbmc.Player()
    player.play(playlist)
    if not player.isPlayingVideo():
        d = xbmcgui.Dialog()
        d.ok('VIDEO QUEUE EMPTY', 'The XBMC video queue is empty.','Add more links to video queue.')




def getThemen():
    progressbar = xbmcgui.DialogProgress()
    progressbar.create((translation(30010)).encode("utf-8"))
    progressbar.update(15)
	
    url = "http://tvthek.orf.at/topics"
    html = opener.open(url)
    html = html.read()
    soup = BeautifulSoup(html)
    
    
    content = soup.find('section',{'class':'mod_container_list'})
    topics = soup.findAll('section',{'class':'item_wrapper'})
    feedcount = len(topics)
    i = 1
    for topic in topics:
        if progressbar.iscanceled() :
                xbmcplugin.endOfDirectory(pluginhandle)
                progressbar.close()
                break
        i = i+1
        percent = i*100/feedcount
        progressbar.update(percent)
		
        title = topic.find('h3').text.encode('UTF-8')
        link = topic.find('a',{'class':'more service_link service_link_more'})['href'].encode('UTF-8')
        image = topic.find('img')['src'].replace("width=395","width=500").replace("height=209.07070707071","height=265").encode('UTF-8')
        desc = ""
        addDirectory(title,image,desc,link,"openTopicPosts")
    listCallback()

def getCategories():
    html = opener.open(base_url)
    html = html.read()
    soup = BeautifulSoup(html)
    
    slideview = soup.find('div',{'class':'mod_carousel'})
    catbox = slideview.findAll('a',{'class':'carousel_item_link'})
    for cat in catbox:
        link = cat['href']
        title = programUrlTitle(link).encode('UTF-8')
        image = cat.find('img')['src'].replace("height=56.34328358209","height=280").replace("width=100","width=500")
        desc = ''
        addDirectory(title,image,desc,link,"openCategoryList")
    listCallback()

def programUrlTitle(url):
    title = url.replace(base_url,"").split("/")
    return title[2].replace("-"," ")
		
def search():
    addDirectory((translation(30007)).encode("utf-8")+" ...",defaultbanner,defaultbackdrop,"","searchNew")
    cache.table_name = "searchhistory"
    some_dict = cache.get("searches").split("|")
    for str in reversed(some_dict):
        addDirectory(str.encode('UTF-8'),defaultbanner,"",str.replace(" ","+"),"searchNew")
    listCallback()
	
def searchTV():
    keyboard = xbmc.Keyboard('')
    keyboard.doModal()
    if (keyboard.isConfirmed()):
      cache.table_name = "searchhistory"
      keyboard_in = keyboard.getText()
      some_dict = cache.get("searches") + "|"+keyboard_in
      cache.set("searches",some_dict);
      searchurl = "%s/search?q=%s"%(base_url,keyboard_in.replace(" ","+"))
      getTableResults(searchurl)
    else:
      addDirectory((translation(30014)).encode("utf-8"),defaultlogo,"","","")
    listCallback()

def getTableResults(url):
    url = urllib.unquote(url)
    progressbar = xbmcgui.DialogProgress()
    progressbar.create((translation(30010)).encode("utf-8"))
    progressbar.update(0)

    html = opener.open(url)
    html = html.read()
    soup = BeautifulSoup(html)
    tipps = soup.findAll('article',{'class':'item'})
    i = 1
    feedcount = len(tipps)
    for tip in tipps:
        if progressbar.iscanceled() :
            xbmcplugin.endOfDirectory(pluginhandle)
            progressbar.close()
            break
        i = i+1
        percent = i*100/feedcount
        progressbar.update(percent)
        title = tip.find('h4',{'class':'item_title'}).text.encode('UTF-8')
        desc = tip.find('div',{'class':'item_description'})
        if desc != None:
            desc = desc.text.encode('UTF-8')
            date = tip.find('time',{'class':'meta meta_date'}).text.encode('UTF-8')
            time = tip.find('span',{'class':'meta meta_time'}).text.encode('UTF-8')
            #title = "%s | %s %s" % (title,date,time)
            desc = (translation(30009)).encode("utf-8")+' %s - %s\n%s' % (date,time,desc)
        else:
            desc = (translation(30008)).encode("utf-8")
            
        image = tip.find('img')['src'].replace("width=395","width=500").replace("height=209.07070707071","height=265").replace("height=77.753731343284","height=265").replace("width=138","width=500")
        link = tip.find('a')['href']
        addDirectory(title,image,desc,link,"openSeries")
    listCallback()
		
		
def searchTVHistory(link):
    keyboard = xbmc.Keyboard(link)
    keyboard.doModal()
    if (keyboard.isConfirmed()):
      cache.table_name = "searchhistory"
      keyboard_in = keyboard.getText()
      if keyboard_in != link:
           some_dict = cache.get("searches") + "|"+keyboard_in
           cache.set("searches",some_dict);
      searchurl = "%s/search?q=%s"%(base_url,keyboard_in.replace(" ","+"))
      getTableResults(searchurl)
    else:
      addDirectory((translation(30014)).encode("utf-8"),defaultlogo,defaultbackdrop,"","")
    listCallback()
    
	
#Getting Parameters
params=parameters_string_to_dict(sys.argv[2])
mode=params.get('mode')
title=params.get('title')
link=params.get('link')
banner=params.get('banner')
backdrop=params.get('backdrop')


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
    getTableResults("http://tvthek.orf.at/tips")
elif mode == 'getNewShows':
    getTableResults("http://tvthek.orf.at/newest")
elif mode == 'getMostViewed':
    getTableResults('http://tvthek.orf.at/most_viewed')
elif mode == 'getThemen':
    getThemen()
elif mode == 'openTopicPosts':
    getThemenListe(link)
elif mode == 'playVideo':
    playFile()
elif mode == 'playList':
    playFile()
elif mode == 'getArchiv':
    getArchiv('http://tvthek.orf.at/schedule')
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
