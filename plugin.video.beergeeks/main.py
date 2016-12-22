import sys
import xbmc, xbmcplugin, xbmcgui, xbmcaddon
import re, os, time
import urllib, urllib2
import HTMLParser
import json


addon_handle = int(sys.argv[1])

print "HERE THE FING SHIT"
print addon_handle
print sys.argv
#Settings file location
settings = xbmcaddon.Addon(id='plugin.video.beergeeks')

#Main settings
QUALITY = int(settings.getSetting(id="quality"))
AUTO_PLAY = str(settings.getSetting(id="auto_play"))

#Localisation
local_string = xbmcaddon.Addon(id='plugin.video.beergeeks').getLocalizedString
ROOTDIR = xbmcaddon.Addon(id='plugin.video.beergeeks').getAddonInfo('path')
ICON = ROOTDIR+"/icon.png"
FANART = ROOTDIR+"/fanart.jpg"
USER_AGENT = 'Mozilla/5.0 (iPhone; CPU iPhone OS 8_3 like Mac OS X) AppleWebKit/600.1.4 (KHTML, like Gecko) Version/8.0 Mobile/12F70 Safari/600.1.4'

    
def GET_EPISODES():                    
    #url = 'http://www.ora.tv/beergeeks/schedule'
    url = 'http://www.ora.tv/beergeeks'
    req = urllib2.Request(url)
    req.add_header('User-Agent', ' Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
    response = urllib2.urlopen(req)
    source = response.read()
    response.close() 

    source = source.replace('\n',"")    
    #source = re.compile('<figure>(.+?)</figure').findall(source)
    #source = re.compile('class="panel accordian"(.+?)</div>').findall(source)
    source = re.compile('<div class="tab-ep-details">(.+?)</span>').findall(source)
        
    episodes = []

    #addDir("[B]Latest Episode[/B]",'/nothing',999,ICON,FANART)

    for block in source:
        #print block
        #name = GET_NAME(block)
        #image = GET_IMAGE(block)
        link = GET_LINK(block)
        location = GET_LOCATION(block)
        #print link
        v_code = link[link.find("_")+1:]
        print v_code
        try:
            json = GET_VIDEO_INFO(v_code)        
            #print json
            title = HTMLParser.HTMLParser().unescape(HTMLParser.HTMLParser().unescape(json['title']))
            image = 'http:'+HTMLParser.HTMLParser().unescape(json['thumbnail_url'])
            desc = HTMLParser.HTMLParser().unescape(json['description'])            
            end_desc = desc.find('<')
            desc = desc[0:end_desc]
            desc = location + '\n' + desc
            video_id = json['video_id']
            duration = int(json['duration'])
            #http://cedexis-video.ora.tv/i/beergeeks/video-14630/,basic400,basic600,sd900,sd1200,sd1500,hd720,hd1080,mobile400,.mp4.csmil/master.m3u8
            stream = 'http://cedexis-video.ora.tv/i/beergeeks/video-'+str(video_id)+'/,basic400,basic600,sd900,sd1200,sd1500,hd720,hd1080,mobile400,.mp4.csmil/master.m3u8'        
            #GET_STREAM_QUALITIES(stream)
            #q = GET_QUALITY(str(video_id))   
            #stream = stream + q + '|User-Agent='+USER_AGENT            

            #addLink(title, stream, title, image, desc, duration)
            #name = HTMLParser.HTMLParser().unescape(name)
            info = {'plot':desc,'tvshowtitle':'Beer Geeks','title':title,'originaltitle':title,'duration':duration}
            #name,url,mode,iconimage,fanart=None      
            if title not in episodes:
                #addDir(title,stream,100,image,info)
                addStream(title,stream,101,image,info)
                episodes.append(title)
        except:
            pass
    

def GET_STREAM_QUALITIES(m3u8_url):  
    stream_url = {}
    stream_title = []   
    print "M3U8!!!" + m3u8_url
    req = urllib2.Request(m3u8_url)
    response = urllib2.urlopen(req)                    
    master = response.read()
    response.close()
    #cookie =  urllib.quote(response.info().getheader('Set-Cookie'))

    #print cookie
    print master

    line = re.compile("(.+?)\n").findall(master)  

    try:
        for temp_url in line:
            if '.m3u8' in temp_url:
                if 'http://' not in temp_url:
                    end = m3u8_url.find('master.m3u8')
                    print m3u8_url.find('master.m3u8')
                    temp_url = m3u8_url[:end] + temp_url
                
                print temp_url
                print desc                                
                #addLink(name +' ('+desc+')',temp_url+'|User-Agent='+USER_AGENT, name +' ('+desc+')', img_url)
                title = '('+desc+') '+name
                stream_title.append(title)
                #stream_url.append(temp_url+'|User-Agent='+USER_AGENT)
                stream_url.update({title:temp_url+'|User-Agent='+USER_AGENT})
                
            else:
                desc = ''
                start = temp_url.find('RESOLUTION=')
                if start > 0:
                    start = start + len('RESOLUTION=')
                    end = temp_url.find(',',start)
                    if end != -1:
                        desc = temp_url[start:end]
                    else:
                        desc = temp_url[start:]
                else:
                    desc = "Audio"
    except:
        pass

    return stream_url, stream_title


def STREAM_SELECT(m3u8_url):
    stream_url, stream_title = GET_STREAM_QUALITIES(m3u8_url)
    stream_title.sort(key=natural_sort_key)

    if len(stream_title) > 0:
        ret = 0      
        if str(AUTO_PLAY) == 'true':
            ret = len(stream_title)-1            
        else:             
            dialog = xbmcgui.Dialog() 
            ret = dialog.select('Choose Stream Quality', stream_title)
        
        if ret >=0:
            url = stream_url.get(stream_title[ret]) 
            listitem = xbmcgui.ListItem(path=url)
            #listitem = xbmcgui.ListItem(path=stream_url[ret])
            print "Attempting to play stream..."
            print url
            xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, listitem)
        else:
            sys.exit()
    else:    
        msg = "No playable streams found."
        dialog = xbmcgui.Dialog() 
        ok = dialog.ok('Streams Not Found', msg)


def natural_sort_key(s):
    _nsre = re.compile('([0-9]+)')
    return [int(text) if text.isdigit() else text.lower()
            for text in re.split(_nsre, s)] 

def GET_VIDEO_INFO(v_code):
    #https://www.ora.tv/oembed/0_4473hnwr0g57?format=json
    url = 'http://www.ora.tv/oembed/0_'+v_code+'?format=json'
    print url
    req = urllib2.Request(url)
    req.add_header('User-Agent', USER_AGENT)
    response = urllib2.urlopen(req)    
    json_source = json.load(response)                       
    response.close()  

    return json_source


def GET_QUALITY(video_id):
    #http://cedexis-video.ora.tv/i/beergeeks/video-14630/,basic400,basic600,sd900,sd1200,sd1500,hd720,hd1080,mobile400,.mp4.csmil/index_7_av.m3u8
    temp =""
    if QUALITY == 0:
        temp = "index_7_av.m3u8"
        #temp = "video-"+video_id+"mobile400.mp4.csmil/master.m3u8"
    elif QUALITY == 1:
        temp = "index_0_av.m3u8"        
        #temp = "video-"+video_id+"basic400.mp4.csmil/master.m3u8"
    elif QUALITY == 2:
        temp = "index_2_av.m3u8"
        #temp = "video-"+video_id+"sd900.mp4.csmil/master.m3u8"
    elif QUALITY == 3:
        temp = "index_4_av.m3u8"
        #temp = "video-"+video_id+"sd1500.mp4.csmil/master.m3u8"
    elif QUALITY == 4:
        temp = "index_5_av.m3u8"
        #temp = "video-"+video_id+"hd720.mp4.csmil/master.m3u8"
    elif QUALITY == 5:
        temp = "index_6_av.m3u8"
        #temp = "video-"+video_id+"hd1080.mp4.csmil/master.m3u8"

    return temp

def GET_NAME(source):
    start_str = '<span class="showschedule-episodetitle">'
    end_str = '</span>'    
    return FIND(source,start_str,end_str)

def GET_IMAGE(source):
    start_str = '<img src="'
    end_str = '"'
    return 'http:'+FIND(source,start_str,end_str)

def GET_LINK(source):
    #start_str = '<a class="showschedule-cta cta-play" href="'
    start_str = '/beergeeks/'
    end_str = '"'
    return 'http://www.ora.tv/beergeeks/'+FIND(source,start_str,end_str)

def GET_LOCATION(source):
    start_str = '<p class="tab-ep-loc">'
    end_str = '</p>'
    return FIND(source, start_str, end_str)

def FIND(source,start_str,end_str):    
    start = source.find(start_str)
    end = source.find(end_str,start+len(start_str))

    return source[start+len(start_str):end]


def GET_VIDEO(name,url,img_url):    
    req = urllib2.Request(url)
    req.add_header('User-Agent', USER_AGENT)
    response = urllib2.urlopen(req)
    source = response.read()
    response.close() 
    #print source

    stream = FIND(source,'"hls_stream":"','"')
    #print 'STREAM ' + stream


    req = urllib2.Request(stream)
    response = urllib2.urlopen(req)                    
    master = response.read()
    response.close()
    #print master

    link = stream[:stream.find('master.m3u8')]
    link = link + "index_5_av.m3u8" + "|User-Agent="+USER_AGENT
    addLink(name,link, name, img_url)
    #line = re.compile("(.+?)\n").findall(master)  
    """
    for temp_url in line:
        if '.m3u8' in temp_url:
            #print temp_url
            #print desc                                
            addLink(name +' ('+desc+')',link+temp_url, name +' ('+desc+')', img_url)
        else:
            desc = ''
            start = temp_url.find('RESOLUTION=')
            if start > 0:
                start = start + len('RESOLUTION=')
                #end = temp_url.find(',',start)
                desc = temp_url[start:]
            else:
                desc = "Audio"
    """


def addLink(name,url,title,iconimage,desc=None,duration=None):
    ok=True
    liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
    liz.setProperty('fanart_image',FANART)
    liz.setProperty("IsPlayable", "true")
    liz.setInfo( type="Video", infoLabels={ "Title": title } )
    #if duration != None:
    #liz.setInfo( type="Video", infoLabels={ "duration": duration } )

    if desc != None:
        liz.setInfo( type="Video", infoLabels={ "plot": desc } )

    ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=liz)
    return ok


def addDir(name,url,mode,iconimage,info,fanart=None):       
    ok=True
    u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
    u = u+"&img_url="+urllib.quote_plus(iconimage)            
    liz=xbmcgui.ListItem(name, iconImage=ICON, thumbnailImage=iconimage)    
    liz.setInfo( type="Video", infoLabels=info)    
    if fanart != None:
        liz.setProperty('fanart_image', fanart)
    else:
        liz.setProperty('fanart_image', FANART)

    ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)    
    xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
    return ok

def addStream(name,url,mode,iconimage,info,fanart=None):       
    ok=True
    u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
    u = u+"&img_url="+urllib.quote_plus(iconimage)            
    liz=xbmcgui.ListItem(name, iconImage=ICON, thumbnailImage=iconimage)    
    liz.setInfo( type="Video", infoLabels=info)    
    if fanart != None:
        liz.setProperty('fanart_image', fanart)
    else:
        liz.setProperty('fanart_image', FANART)

    print u
    liz.setProperty("IsPlayable", "true")
    ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=False)
    xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
    
    return ok


def get_params():
    param=[]
    paramstring=sys.argv[2]
    if len(paramstring)>=2:
            params=sys.argv[2]
            cleanedparams=params.replace('?','')
            if (params[len(params)-1]=='/'):
                    params=params[0:len(params)-2]
            pairsofparams=cleanedparams.split('&')
            param={}
            for i in range(len(pairsofparams)):
                    splitparams={}
                    splitparams=pairsofparams[i].split('=')
                    if (len(splitparams))==2:
                            param[splitparams[0]]=splitparams[1]
                            
    return param

params=get_params()
url=None
name=None
mode=None
img_url=None

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
try:
    img_url=urllib.unquote_plus(params["img_url"])
except:
    pass


print "Mode: "+str(mode)
print "URL: "+str(url)
print "Name: "+str(name)
print "Image URL:"+str(img_url)



if mode==None or url==None or len(url)<1:
    #print ""                
    GET_EPISODES()        
    
elif mode==100:
    #print "GET_YEAR MODE!"
    #GET_VIDEO(name,url,img_url)
    GET_STREAM_QUALITIES(url,img_url)

elif mode==101:    
    STREAM_SELECT(url)    

elif mode==999:
    sys.exit()


xbmcplugin.endOfDirectory(int(sys.argv[1]))
