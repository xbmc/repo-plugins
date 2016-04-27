#!/usr/bin/python
# -*- coding: utf-8 -*-
import urllib,urllib2,re,xbmcplugin,xbmcgui,sys,xbmcaddon,base64,socket,datetime,time,os,os.path,urlparse,json
import CommonFunctions as common
from resources.lib.helpers import *
from base import *

class htmlScraper:
    base_url        = 'http://tvthek.orf.at'
    
    schedule_url    = 'http://tvthek.orf.at/schedule'
    recent_url      = 'http://tvthek.orf.at/newest'
    live_url        = "http://tvthek.orf.at/live"
    mostviewed_url  = 'http://tvthek.orf.at/most_viewed'
    tip_url         = 'http://tvthek.orf.at/tips'
    search_base_url = 'http://tvthek.orf.at/search'
    topic_url       = 'http://tvthek.orf.at/topics'

    
    def __init__(self,xbmc,settings,pluginhandle,quality,protocol,delivery,defaultbanner,defaultbackdrop,useSubtitles,defaultViewMode):
        self.translation = settings.getLocalizedString
        self.xbmc = xbmc
        self.videoQuality = quality
        self.videoDelivery = delivery
        self.videoProtocol = protocol
        self.pluginhandle = pluginhandle
        self.defaultbanner = defaultbanner
        self.defaultbackdrop = defaultbackdrop
        self.useSubtitles = useSubtitles
        self.disableGeoblock = settings.getSetting("disableGeoblock") == "true"
        self.enableBlacklist = settings.getSetting("enableBlacklist") == "true"
        self.xbmc.log(msg='HTML Scraper - Init done', level=xbmc.LOGDEBUG)
        
    # Extracts VideoURL from JSON String    
    def getVideoUrl(self,sources):
        for source in sources:
            if source["protocol"].lower() == self.videoProtocol.lower():
                if source["delivery"].lower() == self.videoDelivery.lower():
                    if source["quality"].lower() == self.videoQuality.lower():
                        return source["src"]
        return False
    
    # Converts Page URL to Title 
    def programUrlTitle(self,url):
        title = url.replace(self.base_url,"").split("/")
        if title[1] == 'index.php':
            return title[3].replace("-"," ")
        else:
            return title[2].replace("-"," ")
    
    # Parses Basic Table Layout Page
    def getTableResults(self,url):
        url = urllib.unquote(url)
        html = common.fetchPage({'link': url})
        items = common.parseDOM(html.get("content"),name='article',attrs={'class': "item.*?"},ret=False)

        for item in items:
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
                desc = (self.translation(30009)).encode("utf-8")+' %s - %s\n%s' % (date,time,desc)
            else:
                desc = (self.translation(30008)).encode("utf-8")

            image = common.parseDOM(item,name='img',attrs={},ret='src')
            image = common.replaceHTMLCodes(image[0]).encode('UTF-8')
            link = common.parseDOM(item,name='a',attrs={},ret='href')
            link = link[0].encode('UTF-8')
            if date != "":
                title = "%s - %s" % (title,date)
                
            
            
            parameters = {"link" : link,"title" : title,"banner" : image,"backdrop" : "", "mode" : "openSeries"}
            

            
            url = sys.argv[0] + '?' + urllib.urlencode(parameters)
            liz = self.html2ListItem(title,image,"",desc,"","","",url,None,True,'false');
            
    	
    def openArchiv(self,url):
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
            if len(description) > 0 :
                description = common.replaceHTMLCodes(description[0])
            else:
                description = self.translation(30008).encode('UTF-8')
                
            banner = common.parseDOM(teaser,name='img',ret='src')
            banner = common.replaceHTMLCodes(banner[1]).encode("utf-8")
            
            banner = common.parseDOM(teaser,name='img',ret='src')
            banner = common.replaceHTMLCodes(banner[1]).encode("utf-8")
            
            parameters = {"link" : link,"title" : title,"banner" : banner,"backdrop" : self.defaultbackdrop, "mode" : "openSeries"}
            url = sys.argv[0] + '?' + urllib.urlencode(parameters)
            liz = self.html2ListItem(title,banner,"",description,"","","",url,None,True,'false');
        
    
    # Parses the Frontpage Carousel
    def getRecentlyAdded(self,url):
        html = common.fetchPage({'link': url})
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
            
            parameters = {"link" : link,"title" : title,"banner" : image,"backdrop" : "", "mode" : "openSeries"}
            url = sys.argv[0] + '?' + urllib.urlencode(parameters)
            liz = self.html2ListItem(title,image,"",desc,"","","",url,None,True,'false');
    
    # Parses the Frontpage Show Overview Carousel
    def getCategories(self):
        html = common.fetchPage({'link': self.base_url})
        html_content = html.get("content")
        
        content = common.parseDOM(html_content,name='div',attrs={'class':'mod_carousel'})
        items = common.parseDOM(content,name='a',attrs={'class':'carousel_item_link'})
        items_href = common.parseDOM(content,name='a',attrs={'class':'carousel_item_link'},ret="href")
        
        i = 0
        for item in items:
            link = common.replaceHTMLCodes(items_href[i]).encode('UTF-8')
            i = i + 1
            title = self.programUrlTitle(link).encode('UTF-8')
            if title.lower().strip() == "bundesland heute":
                image = common.parseDOM(item,name='img',ret="src")
                image = common.replaceHTMLCodes(image[0]).replace("height=56","height=280").replace("width=100","width=500").encode('UTF-8')
                self.getBundeslandHeute(link,image)
            if title.lower().strip() == "zib":
                image = common.parseDOM(item,name='img',ret="src")
                image = common.replaceHTMLCodes(image[0]).replace("height=56","height=280").replace("width=100","width=500").encode('UTF-8')
                self.getZIB(image)
            else:
                image = common.parseDOM(item,name='img',ret="src")
                image = common.replaceHTMLCodes(image[0]).replace("height=56","height=280").replace("width=100","width=500").encode('UTF-8')

                desc = self.translation(30008).encode('UTF-8')
                if title.lower().strip() != "bundesland heute":
                    parameters = {"link" : link,"title" : title,"banner" : image,"backdrop" : "", "mode" : "getSendungenDetail"}
                    url = sys.argv[0] + '?' + urllib.urlencode(parameters)
                    liz = self.html2ListItem(title,image,"",desc,"","","",url,None,True,'false');
    
    # Parses Details for the selected Show
    def getCategoriesDetail(self,category,banner):
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
            if len(current_date) > 0:
                current_date = current_date[0].encode("utf-8")
            else:
                current_date = ""
                
            current_time = common.parseDOM(bcast_info,name='span',attrs={'class': 'meta meta_time'})
            current_link = url
            if len(showname) > 0:
                current_title = "%s - %s" % (showname,current_date)       
                try:
                    current_desc = (self.translation(30009)).encode("utf-8")+' %s - %s\n'+(self.translation(30011)).encode("utf-8")+': %s' % (current_date,current_time,current_duration)
                except:
                    current_desc = self.translation(30008).encode('UTF-8');
                parameters = {"link" :  current_link,"title" :current_title,"banner" : banner,"backdrop" : "", "mode" : "openSeries"}
                url = sys.argv[0] + '?' + urllib.urlencode(parameters)
                liz = self.html2ListItem(current_title,banner,"",current_desc,"","","",url,None,True,'false');
            else:
                liz = self.html2ListItem((self.translation(30014)).encode('UTF-8'),self.defaultbanner,"","","","","","",None,True,'false');
        except:
            liz = self.html2ListItem((self.translation(30014)).encode('UTF-8'),self.defaultbanner,"","","","","","",None,True,'false');
        
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
                title = common.replaceHTMLCodes(common.parseDOM(item, name='a',ret="title")[0]).encode("utf-8").replace('Sendung ', '')
                title = "%s - %s" % (title,date)
                link = common.parseDOM(item,name='a',ret="href");
                try:
                    desc = (self.translation(30009)).encode("utf-8")+" %s - %s\n"+(self.translation(30011)).encode("utf-8")+": %s" % (date,time,duration)
                except:
                    desc = self.translation(30008).encode('UTF-8');
                parameters = {"link" :  link[0],"title" :title,"banner" : banner,"backdrop" : "", "mode" : "openSeries"}
                url = sys.argv[0] + '?' + urllib.urlencode(parameters)
                liz = self.html2ListItem(title,banner,"",desc,"","","",url,None,True,'false');
        
    # Parses "Sendung verpasst?" Date Listing
    def getArchiv(self,url):
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
            
            parameters = {"link" : link,"title" : title,"banner" : "","backdrop" : "", "mode" : "getArchivDetail"}
            url = sys.argv[0] + '?' + urllib.urlencode(parameters)
            liz = self.html2ListItem(title,"","","","",date,"",url,None,True,'false');
    
    
    # Creates a XBMC List Item
    def html2ListItem(self,title,banner,backdrop,description,duration,date,channel,videourl,subtitles=None,folder=True,playable='false'):
        if banner == '':
            banner = self.defaultbanner
        if backdrop == '':
            backdrop = self.defaultbackdrop
        if description == '':
            description = (self.translation(30008)).encode("utf-8")
        if not self.useSubtitles:
            subtitles = None;
        params = parameters_string_to_dict(videourl)
        mode = params.get('mode')
        blacklist = False
        if self.enableBlacklist:
            if mode == 'openSeries' or mode == 'getSendungenDetail':
                blacklist = True
        
        liz = createListItem(title,banner,description,duration,date,channel,videourl,playable,folder,self.translation,backdrop,self.pluginhandle,subtitles,blacklist)    
        return liz
    
    # Parses all "ZIB" Shows
    def getZIB(self,baseimage):
        url = 'http://tvthek.orf.at/programs/genre/ZIB/1';
        html = common.fetchPage({'link': url})
        html_content = html.get("content")
        
        content = common.parseDOM(html_content,name='div',attrs={'class':'base_list_wrapper mod_results_list'})
        items = common.parseDOM( content ,name='li',attrs={'class':'base_list_item jsb_ jsb_ToggleButton results_item'})
        
        for item in items:
            title = common.parseDOM(item,name='h4')
            if len(title) > 0:
                title = title[0].encode('UTF-8')
                item_href = common.parseDOM(item,name='a',attrs={'class':'base_list_item_inner.*?'},ret="href")
                image_container = common.parseDOM(item,name='figure',attrs={'class':'episode_image'},ret="href")
                desc = self.translation(30008).encode('UTF-8')
                image = common.parseDOM(item,name='img',attrs={},ret="src")
                if len(image) > 0:
                    image = common.replaceHTMLCodes(image[0]).encode('UTF-8').replace("height=180","height=265").replace("width=320","width=500")
                else:
                    image = baseimage
                    
                if len(item_href) > 0:
                    link = common.replaceHTMLCodes(item_href[0]).encode('UTF-8')
                    parameters = {"link" : link,"title" : title,"banner" : image,"backdrop" : "", "mode" : "getSendungenDetail"}
                    url = sys.argv[0] + '?' + urllib.urlencode(parameters)
                    liz = self.html2ListItem(title,image,"",desc,"","","",url,None,True,'false');
            
    # Parses all "Bundesland Heute" Shows 
    def getBundeslandHeute(self,url,image):
        html = common.fetchPage({'link': url})
        html_content = html.get("content")
        
        content = common.parseDOM(html_content,name='div',attrs={'class':'base_list_wrapper mod_link_list'})
        items = common.parseDOM(content,name='li',attrs={'class':'base_list_item'})
        items_href = common.parseDOM(items,name='a',attrs={},ret="href")
        items_title = common.parseDOM(items,name='h4')
        
        i = 0
        for item in items:
            link = common.replaceHTMLCodes(items_href[i]).encode('UTF-8')        
            title = items_title[i].encode('UTF-8')
            desc = self.translation(30008).encode('UTF-8')
            parameters = {"link" : link,"title" : title,"banner" : image,"backdrop" : "", "mode" : "getSendungenDetail"}
            url = sys.argv[0] + '?' + urllib.urlencode(parameters)
            liz = self.html2ListItem(title,image,"",desc,"","","",url,None,True,'false');
            i = i + 1
        
    # Parses a Video Page and extracts the Playlist/Description/...
    def getLinks(self,url,banner,playlist):
        playlist.clear()
        url = str(urllib.unquote(url))
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
            if self.useSubtitles:
                if "subtitles" in data.get("selected_video"):
                    current_subtitles = []
                    for sub in data.get("selected_video")["subtitles"]:
                        current_subtitles.append(sub.get(u'src'))
                else:
                    current_subtitles = None
            else:
                current_subtitles = None
            current_id = data.get("selected_video")["id"]
            current_videourl = self.getVideoUrl(data.get("selected_video")["sources"]);
        except Exception, e:
            current_subtitles = None

        if len(video_items) > 1:
            parameters = {"mode" : "playlist"}
            u = sys.argv[0] + '?' + urllib.urlencode(parameters)
            liz = self.html2ListItem("[ "+(self.translation(30015)).encode("utf-8")+" ]",banner,"",(self.translation(30015)).encode("utf-8"),'','','',u, None,True,'true');
            for video_item in video_items:
                try:
                    title_prefix = video_item["title_prefix"]
                    title = video_item["title"].encode('UTF-8')
                    desc = video_item["description"].encode('UTF-8')
                    duration = video_item["duration"]
                    preview_img = video_item["preview_image_url"]
                    id = video_item["id"]
                    sources = video_item["sources"]
                    if self.useSubtitles:
                        if "subtitles" in video_item:
                            subtitles = []
                            for sub in video_item["subtitles"]:
                                subtitles.append(sub.get(u'src'))
                        else:
                            subtitles = None
                    else:
                        subtitles = None
                    videourl = self.getVideoUrl(sources);

                    liz = self.html2ListItem(title,preview_img,"",desc,duration,'','',videourl, subtitles,False,'true')
                    playlist.add(videourl,liz)
                except Exception, e:
                    continue
            return playlist
        else:           
            liz = self.html2ListItem(current_title,current_preview_img,"",current_desc,current_duration,'','',current_videourl, current_subtitles,False,'true')
            playlist.add(current_videourl,liz)
            return playlist
    

    # Returns Live Stream Listing
    def getLiveStreams(self):
        liveurls = {}
        
        
        if self.disableGeoblock == True:
            liveurls['ORF1'] = "http://apasfiisl.apa.at/ipad/orf1_"+self.videoQuality.lower()+"/orf.sdp?wowzasessionid=1"
            liveurls['ORF2'] = "http://apasfiisl.apa.at/ipad/orf2_"+self.videoQuality.lower()+"/orf.sdp?wowzasessionid=1"
            liveurls['ORF3'] = "http://apasfiisl.apa.at/ipad/orf3_"+self.videoQuality.lower()+"/orf.sdp?wowzasessionid=1"
            liveurls['ORFS'] = "http://apasfiisl.apa.at/ipad/orfs_"+self.videoQuality.lower()+"/orf.sdp?wowzasessionid=1"
        else:
            liveurls['ORF1'] = "http://apasfiisl.apa.at/ipad/orf1_"+self.videoQuality.lower()+"/orf.sdp/playlist.m3u8"
            liveurls['ORF2'] = "http://apasfiisl.apa.at/ipad/orf2_"+self.videoQuality.lower()+"/orf.sdp/playlist.m3u8"
            liveurls['ORF3'] = "http://apasfiisl.apa.at/ipad/orf3_"+self.videoQuality.lower()+"/orf.sdp/playlist.m3u8"
            liveurls['ORFS'] = "http://apasfiisl.apa.at/ipad/orfs_"+self.videoQuality.lower()+"/orf.sdp/playlist.m3u8"
            
        html = common.fetchPage({'link': self.live_url})
        wrapper = common.parseDOM(html.get("content"),name='div',attrs={'class': 'base_list_wrapper.*mod_epg'})
        items = common.parseDOM(wrapper[0],name='li',attrs={'class': 'base_list_item.program.*?'})
        items_class = common.parseDOM(wrapper[0],name='li',attrs={'class': 'base_list_item.program.*?'},ret="class")
        i = 0
        for item in items:
            program = items_class[i].split(" ")[2].encode('UTF-8').upper()
            i += 1
                
            banner = common.parseDOM(item,name='img',ret="src")
            banner = common.replaceHTMLCodes(banner[0]).encode('UTF-8')
              
            title = common.parseDOM(item,name='h4')
            title = common.replaceHTMLCodes(title[0]).encode('UTF-8')
               
            time = common.parseDOM(item,name='span',attrs={'class': 'meta.meta_time'})
            time = common.replaceHTMLCodes(time[0]).encode('UTF-8').replace("Uhr","").replace(".",":").strip()

            if self.getBroadcastState(time):
                state = (self.translation(30019)).encode("utf-8")
                state_short = "Online"
            else:
                state = (self.translation(30020)).encode("utf-8")
                state_short = "Offline"

            link = liveurls[program]
                
            title = "[%s] - %s (%s)" % (program,title,time)
            liz = self.html2ListItem(title,banner,"",state,time,program,program,link,None,False,'true')
    
    # Helper for Livestream Listing - Returns if Stream is currently running
    def getBroadcastState(self,time):
        time_probe = time.split(":")
            
        current_hour = datetime.datetime.now().strftime('%H')
        current_min = datetime.datetime.now().strftime('%M')
        if time_probe[0] == current_hour and time_probe[1] >= current_min:
            return False
        elif time_probe[0] > current_hour:
            return False
        else:
            return True
    
    # Parses the Topic Overview Page
    def getThemen(self):
        html = common.fetchPage({'link': self.topic_url})
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
            if description == "":
                description = self.translation(30008).encode('UTF-8')

            parameters = {"link" : link,"title" : title,"banner" : image,"backdrop" : "", "mode" : "getThemenDetail"}
            url = sys.argv[0] + '?' + urllib.urlencode(parameters)
            liz = self.html2ListItem(title,image,"",description,"","","",url,None,True,'false');

    
    # Parses the Topic Detail Page
    def getThemenDetail(self,url):
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
                image = self.defaultbanner
                
            desc = common.parseDOM(topic,name='div',attrs={'class':'item_description'})
            if len(desc) > 0:
                desc = common.replaceHTMLCodes(desc[0]).encode('UTF-8')
            else:
                desc = self.translation(30008).encode('UTF-8')

            date = common.parseDOM(topic,name='time')
            date = common.replaceHTMLCodes(date[0]).encode('UTF-8')

            time = common.parseDOM(topic,name='span',attrs={'class':'meta.meta_duration'})
            time = common.replaceHTMLCodes(time[0]).encode('UTF-8')

            desc = "%s - (%s) \n%s" % (str(date),str(time).strip(),str(desc))
            
            parameters = {"link" : link,"title" : title,"banner" : image,"backdrop" : "", "mode" : "openSeries"}
            url = sys.argv[0] + '?' + urllib.urlencode(parameters)
            liz = self.html2ListItem(title,image,"",desc,"","","",url,None,True,'false');
    
    def getSearchHistory(self,cache):
        parameters = {'mode' : 'getSearchResults'}
        u = sys.argv[0] + '?' + urllib.urlencode(parameters)
        createListItem((self.translation(30007)).encode("utf-8")+" ...", self.defaultbanner, "", "", "", '', u, 'false', True,self.translation,self.defaultbackdrop,self.pluginhandle,None)

        cache.table_name = "searchhistory"
        some_dict = cache.get("searches").split("|")
        for str in reversed(some_dict):
            if str.strip() != '':
                parameters = {'mode' : 'getSearchResults','link' : str.replace(" ","+")}
                u = sys.argv[0] + '?' + urllib.urlencode(parameters)
                createListItem(str.encode('UTF-8'), self.defaultbanner, "", "", "", '', u, 'false', True,self.translation,self.defaultbackdrop,self.pluginhandle,None)

    def removeUmlauts(self,str):
        return str.replace("Ö","O").replace("ö","o").replace("Ü","U").replace("ü","u").replace("Ä","A").replace("ä","a")
                
    def getSearchResults(self,link,cache):
        keyboard = self.xbmc.Keyboard(link)
        keyboard.doModal()
        if (keyboard.isConfirmed()):
            cache.table_name = "searchhistory"
            keyboard_in = self.removeUmlauts(keyboard.getText())
            if keyboard_in != link:
                some_dict = cache.get("searches") + "|"+keyboard_in
                cache.set("searches",some_dict);
            searchurl = "%s?q=%s"%(self.search_base_url,keyboard_in.replace(" ","+"))
            self.getTableResults(searchurl)
        else:
            parameters = {'mode' : 'getSearchHistory'}
            u = sys.argv[0] + '?' + urllib.urlencode(parameters)
            createListItem((self.translation(30014)).encode("utf-8")+" ...", self.defaultbanner, "", "", "", '', u, 'false', True,self.translation,self.defaultbackdrop,self.pluginhandle,None)
