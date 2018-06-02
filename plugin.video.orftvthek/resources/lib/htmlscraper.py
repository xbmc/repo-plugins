#!/usr/bin/python
# -*- coding: utf-8 -*-

import datetime
import json
import sys
import time
import urllib
import urllib2

import CommonFunctions as common

from resources.lib.helpers import *
from .base import *
from .Scraper import *

class htmlScraper(Scraper):

    __urlBase       = 'http://tvthek.orf.at'
    __urlLive       = __urlBase + '/live'
    __urlMostViewed = __urlBase + '/most_viewed'
    __urlNewest     = __urlBase + '/newest'
    __urlSchedule   = __urlBase + '/schedule'
    __urlSearch     = __urlBase + '/search'
    __urlShows      = __urlBase + '/profiles/a-z'
    __urlTips       = __urlBase + '/tips'
    __urlTopics     = __urlBase + '/topics'
    __urlArchive    = __urlBase + '/archive'


    def __init__(self, xbmc, settings, pluginhandle, quality, protocol, delivery, defaultbanner, defaultbackdrop):
        self.translation = settings.getLocalizedString
        self.xbmc = xbmc
        self.videoQuality = quality
        self.videoDelivery = delivery
        self.videoProtocol = protocol
        self.pluginhandle = pluginhandle
        self.defaultbanner = defaultbanner
        self.defaultbackdrop = defaultbackdrop
        self.enableBlacklist = settings.getSetting("enableBlacklist") == "true"
        debugLog('HTML Scraper - Init done','Info')


    def getMostViewed(self):
        self.getTableResults(self.__urlMostViewed)


    def getNewest(self):
        self.getTableResults(self.__urlNewest)


    def getTips(self):
        self.getTableResults(self.__urlTips)

    # Extracts VideoURL from JSON String
    def getVideoUrl(self,sources):
        for source in sources:
            if source["protocol"].lower() == self.videoProtocol.lower():
                if source["delivery"].lower() == self.videoDelivery.lower():
                    if source["quality"].lower() == self.videoQuality.lower():
                        return generateAddonVideoUrl(source["src"])
        return False

    # Converts Page URL to Title
    def programUrlTitle(self,url):
        title = url.replace(self.__urlBase,"").split("/")
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

            image = common.parseDOM(item,name='img',attrs={},ret='src')
            image = common.replaceHTMLCodes(image[0]).encode('UTF-8')
            link = common.parseDOM(item,name='a',attrs={},ret='href')
            link = link[0].encode('UTF-8')
            if date != "":
                title = "%s - %s" % (title,date)

            parameters = {"link" : link, "banner" : image, "mode" : "openSeries"}

            url = sys.argv[0] + '?' + urllib.urlencode(parameters)
            self.html2ListItem(title,image,"",desc,"","","",url,None,True, False);


    def openArchiv(self,url):
        url = self.__urlBase + urllib.unquote(url)
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

            banner = common.parseDOM(teaser.replace('>"', '"'), name='img', ret='src')
            banner = common.replaceHTMLCodes(banner[1]).encode("utf-8")

            parameters = {"link" : link, "banner" : banner, "mode" : "openSeries"}
            url = sys.argv[0] + '?' + urllib.urlencode(parameters)
            self.html2ListItem(title,banner,"",description,"","","",url,None,True, False);


    # Parses the Frontpage Carousel
    def getHighlights(self):
        html = common.fetchPage({'link': self.__urlBase})
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

            parameters = {"link" : link, "banner" : image, "mode" : "openSeries"}
            url = sys.argv[0] + '?' + urllib.urlencode(parameters)
            self.html2ListItem(title,image,"",desc,"","","",url,None,True, False);

    # Parses the Frontpage Show Overview Carousel
    def getCategories(self):
        html = common.fetchPage({'link': self.__urlShows})
        html_content = html.get("content")

        content = common.parseDOM(html_content,name='div',attrs={'class':'region_main'})
        items = common.parseDOM(content,name='article',attrs={'class':'item'})

        for item in items:
            link = common.parseDOM(item,name='a',attrs={'class':'item_inner clearfix'},ret="href")
            link = common.replaceHTMLCodes(link[0]).encode('UTF-8')
            title = common.parseDOM(item,name='h4',attrs={'class':'item_title'})
            title = common.replaceHTMLCodes(title[0]).encode('UTF-8').replace("[","").replace("]","")

            image = common.parseDOM(item,name='img',ret="src")
            image = common.replaceHTMLCodes(image[0]).encode('UTF-8')

            parameters = {"link" : link, "banner" : image, "mode" : "getSendungenDetail"}
            url = sys.argv[0] + '?' + urllib.urlencode(parameters)
            self.html2ListItem(title,image,"", None,"","","",url,None,True, False);

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
                    current_desc = '%s %s - %s\n%s: %s' % (self.translation(30009), current_date, current_time[0], self.translation(30011), current_duration[0])
                except:
                    current_desc = None
                parameters = {"link" :  current_link, "banner" : banner,"mode" : "openSeries"}
                url = sys.argv[0] + '?' + urllib.urlencode(parameters)
                self.html2ListItem(current_title,banner,"",current_desc,"","","",url,None,True, False);
            else:
                self.html2ListItem((self.translation(30014)).encode('UTF-8'),self.defaultbanner,"","","","","","",None,True, False);
        except:
            self.html2ListItem((self.translation(30014)).encode('UTF-8'),self.defaultbanner,"","","","","","",None,True, False);

        itemwrapper = common.parseDOM(html.get("content"),name='div',attrs={'class': 'base_list_wrapper.mod_latest_episodes'})
        if len(itemwrapper) > 0:
            items = common.parseDOM(itemwrapper,name='li',attrs={'class': 'base_list_item'})
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
                    desc = '%s %s - %s\n%s: %s' % (self.translation(30009), date, time[0], self.translation(30011), duration[0])
                except:
                    desc = None
                parameters = {"link" :  link[0], "banner" : banner, "mode" : "openSeries"}
                url = sys.argv[0] + '?' + urllib.urlencode(parameters)
                self.html2ListItem(title,banner,"",desc,"","","",url,None,True, False);

    # Parses "Sendung verpasst?" Date Listing
    def getSchedule(self):
        html = common.fetchPage({'link': self.__urlSchedule})
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

            parameters = {"link" : link, "mode" : "getScheduleDetail"}
            url = sys.argv[0] + '?' + urllib.urlencode(parameters)
            self.html2ListItem(title,"","","","",date,"",url,None,True, False);

    def getArchiv(self):
        html = common.fetchPage({'link': self.__urlArchive})
        html_content = html.get("content")

        content = common.parseDOM(html_content,name='section',attrs={'class':'mod_archive_items.*?'})
        archives = common.parseDOM(content,name='article',attrs={'class':'item'})

        for archive in archives:
            title = common.parseDOM(archive,name='h4',attrs={'class':'item_title'})
            if title[0]:
                title = common.replaceHTMLCodes(title[0]).encode('UTF-8')

                link = common.parseDOM(archive,name='a',attrs={},ret="href")
                link = common.replaceHTMLCodes(link[0]).encode('UTF-8')

                image = common.parseDOM(archive,name='img',ret="src")
                image = common.replaceHTMLCodes(image[0]).replace("width=395","width=500").replace("height=209.07070707071","height=265").encode('UTF-8')

                description = common.parseDOM(archive,name='div',attrs={'class':'item_description'})
                description = common.replaceHTMLCodes(description[0]).encode('UTF-8')

                parameters = {"link" : link, "mode" : "getArchiveDetail"}
                url = sys.argv[0] + '?' + urllib.urlencode(parameters)
                self.html2ListItem(title,image,"",description,"","","",url,None,True, False);

    # Creates a XBMC List Item
    def html2ListItem(self,title,banner,backdrop,description,duration,date,channel,videourl,subtitles=None,folder=True,playable = False,contextMenuItems = None):
        if banner == '':
            banner = self.defaultbanner
        if backdrop == '':
            backdrop = self.defaultbackdrop
        params = parameters_string_to_dict(videourl)
        mode = params.get('mode')
        if not mode:
            mode = "player"

        blacklist = False
        if self.enableBlacklist:
            if mode == 'openSeries' or mode == 'getSendungenDetail':
                blacklist = True
        debugLog("Adding List Item","Info")
        debugLog("Mode: %s" % mode,"Info")
        debugLog("Videourl: %s" % videourl,"Info")
        debugLog("Duration: %s" % duration,"Info")

        return createListItem(title,banner,description,duration,date,channel,videourl,playable,folder, backdrop,self.pluginhandle,subtitles,blacklist,contextMenuItems)

    # Parses a Video Page and extracts the Playlist/Description/...
    def getLinks(self,url,banner,playlist):
        playlist.clear()
        url = str(urllib.unquote(url))
        debugLog("Loading Videos from %s" % url,'Info')
        if banner != None:
            banner = urllib.unquote(banner)

        html = common.fetchPage({'link': url})
        data = common.parseDOM(html.get("content"),name='div',attrs={'class': "jsb_ jsb_VideoPlaylist"},ret='data-jsb')
        if len(data):
            try:
                data = data[0]
                data = common.replaceHTMLCodes(data)
                data = json.loads(data)

                video_items = data.get("playlist")["videos"]
                current_title = data.get("selected_video")["title"]
                if data.get("selected_video")["description"]:
                    current_desc = data.get("selected_video")["description"].encode('UTF-8')
                else:
                    current_desc = ""

                if data.get("selected_video")["duration"]:
                    current_duration = float(data.get("selected_video")["duration"])
                    current_duration = int(current_duration / 1000)
                else:
                    current_duration = 0

                current_preview_img = data.get("selected_video")["preview_image_url"]
                if "subtitles" in data.get("selected_video"):
                    current_subtitles = []
                    for sub in data.get("selected_video")["subtitles"]:
                        current_subtitles.append(sub.get(u'src'))
                else:
                    current_subtitles = None
                current_videourl = self.getVideoUrl(data.get("selected_video")["sources"]);
            except Exception as e:
                debugLog("Error Loading Episode from %s" % url,'Exception')
                notifyUser((self.translation(30052)).encode("utf-8"))
                current_subtitles = None

            if len(video_items) > 1:
                debugLog("Found Video Playlist with %d Items" % len(video_items),'Info')
                parameters = {"mode" : "playlist"}
                u = sys.argv[0] + '?' + urllib.urlencode(parameters)
                liz = self.html2ListItem("[ "+(self.translation(30015)).encode("utf-8")+" ]",banner,"",(self.translation(30015)).encode("utf-8"),'','','',u,None,False,False);
                for video_item in video_items:
                    try:
                        title = video_item["title"].encode('UTF-8')
                        if video_item["description"]:
                            desc = video_item["description"].encode('UTF-8')
                        else:
                            debugLog("No Video Description for %s" % title,'Info')
                            desc = ""

                        if video_item["duration"]:
                            duration = float(video_item["duration"])
                            duration = int(duration / 1000)
                        else:
                            duration = 0

                        preview_img = video_item["preview_image_url"]
                        sources = video_item["sources"]
                        if "subtitles" in video_item:
                            debugLog("Found Subtitles for %s" % title,'Info')
                            subtitles = []
                            for sub in video_item["subtitles"]:
                                subtitles.append(sub.get(u'src'))
                        else:
                            subtitles = None
                        videourl = self.getVideoUrl(sources);

                        liz = self.html2ListItem(title,preview_img,"",desc,duration,'','',videourl, subtitles,False, True)
                        playlist.add(videourl,liz)
                    except Exception as e:
                        debugLog(e,'Error')
                        continue
                return playlist
            else:
                debugLog("No Playlist Items found for %s. Setting up single video view." % current_title.encode('UTF-8'),'Info')
                liz = self.html2ListItem(current_title,current_preview_img,"",current_desc,current_duration,'','',current_videourl, current_subtitles,False, True)
                playlist.add(current_videourl,liz)
                return playlist
        else:
            notifyUser((self.translation(30052)).encode("utf-8"))
            sys.exit()


    # Returns Live Stream Listing
    def getLiveStreams(self):
        liveurls = {}

        try:
            xbmcaddon.Addon('inputstream.adaptive')
            inputstreamAdaptive = True
        except RuntimeError:
            inputstreamAdaptive = False

        liveurls['ORF1'] = "http://apasfiisl.apa.at/ipad/orf1_"+self.videoQuality.lower()+"/orf.sdp/playlist.m3u8"
        liveurls['ORF2'] = "http://apasfiisl.apa.at/ipad/orf2_"+self.videoQuality.lower()+"/orf.sdp/playlist.m3u8"
        liveurls['ORF3'] = "http://apasfiisl.apa.at/ipad/orf3_"+self.videoQuality.lower()+"/orf.sdp/playlist.m3u8"
        liveurls['ORFS'] = "http://apasfiisl.apa.at/ipad/orfs_"+self.videoQuality.lower()+"/orf.sdp/playlist.m3u8"

        channelnames = {}
        channelnames['ORF1'] = "ORF 1"
        channelnames['ORF2'] = "ORF 2"
        channelnames['ORF3'] = "ORF III"
        channelnames['ORFS'] = "ORF Sport+"

        html = common.fetchPage({'link': self.__urlLive})
        wrapper = common.parseDOM(html.get("content"),name='div',attrs={'class': 'base_list_wrapper mod_epg'})
        items = common.parseDOM(wrapper[0],name='li',attrs={'class': 'base_list_item.program.*?'})
        items_class = common.parseDOM(wrapper[0],name='li',attrs={'class': 'base_list_item.program.*?'},ret="class")
        i = 0
        for item in items:
            program = items_class[i].split(" ")[2].encode('UTF-8').upper()
            i += 1
            if channelnames[program]:
                banner = common.parseDOM(item,name='img',ret="src")
                banner = common.replaceHTMLCodes(banner[0]).encode('UTF-8')

                title = common.parseDOM(item,name='h4')
                title = common.replaceHTMLCodes(title[0]).encode('UTF-8')

                time_str = common.parseDOM(item,name='span',attrs={'class': 'meta.meta_time'})
                time_str = common.replaceHTMLCodes(time_str[0]).encode('UTF-8').replace("Uhr","").replace(".",":").strip()

                if self.getBroadcastState(time_str):
                    state = (self.translation(30019)).encode("utf-8")
                else:
                    state = (self.translation(30020)).encode("utf-8")

                initial = True
                link = liveurls[program]
                final_title = "[%s] - %s (%s)" % (channelnames[program],title,time_str)

                child_list = common.parseDOM(item,name='li',attrs={'class': 'base_list_item'})
                for child_list_item in child_list:
                    contextMenuItems = []
                    child_restart = common.parseDOM(child_list_item , name='span',attrs={'class': 'is_restartable.*?'},ret="class")

                    child_list_title = common.parseDOM(child_list_item,name='h4')
                    child_list_title = common.replaceHTMLCodes(child_list_title[0]).encode('UTF-8')
                    child_list_link = common.parseDOM(child_list_item,name='a',attrs={'class': 'base_list_item_inner'},ret="href")
                    child_list_link = common.replaceHTMLCodes(child_list_link[0])
                    child_list_time = common.parseDOM(child_list_item,name='span',attrs={'class': 'meta.meta_time'})
                    child_list_time = common.replaceHTMLCodes(child_list_time[0]).encode('UTF-8').replace("Uhr","").replace(".",":").strip()

                    if initial:
                        if inputstreamAdaptive and child_restart:
                            final_title = "[Restart][%s] - %s (%s)" % (channelnames[program],title,time_str)
                            contextMenuItems.append(('Restart', 'RunPlugin(plugin://%s/?mode=liveStreamRestart&link=%s)' % (xbmcaddon.Addon().getAddonInfo('id'), child_list_link)))

                        self.html2ListItem(final_title,banner,"",state,time_str,program,program, generateAddonVideoUrl(link),None,False, True,contextMenuItems)
                        initial = False

                    if child_list_time == time_str and child_list_title != title:
                        if inputstreamAdaptive and child_restart:
                            contextMenuItems.append(('Restart', 'RunPlugin(plugin://%s/?mode=liveStreamRestart&link=%s)' % (xbmcaddon.Addon().getAddonInfo('id'), child_list_link)))
                        child_list_streaming_url = self.getLivestreamUrl(child_list_link,self.videoQuality)
                        child_list_final_title = "[%s] - %s (%s)" % (channelnames[program],child_list_title,child_list_time)

                        self.html2ListItem(child_list_final_title,banner,"",state,time,program,program, generateAddonVideoUrl(child_list_streaming_url),None,False, True,contextMenuItems)

    def liveStreamRestart(self, link):
        try:
            xbmcaddon.Addon('inputstream.adaptive')
        except RuntimeError:
            return

        livestream_id = link.rpartition('/')[-1]
        html = common.fetchPage({'link': link})
        bitmovinStreamId = self.getLivestreamBitmovinID(html)
        stream_info = self.getLivestreamInformation(html)

        if bitmovinStreamId:

            title       = stream_info['title']
            image       = stream_info['image']
            description = stream_info['description']
            duration    = stream_info['duration']
            date        = stream_info['date']
            channel     = stream_info['channel']

            ApiKey = '2e9f11608ede41f1826488f1e23c4a8d'
            response = urllib2.urlopen('http://restarttv-delivery.bitmovin.com/livestreams/%s/sections/?state=active&X-Api-Key=%s' % (bitmovinStreamId, ApiKey)) # nosec
            section = json.loads(response.read())[0]

            streamingURL = 'http://restarttv-delivery.bitmovin.com/livestreams/%s/sections/%s/manifests/hls/?startTime=%s&X-Api-Key=%s' % (bitmovinStreamId, section.get('id'), section.get('metaData').get('timestamp'), ApiKey)

            listItem = createListItem(title, image, description, duration, date, channel , streamingURL, True, False, self.defaultbackdrop, self.pluginhandle)
            listItem.setProperty('inputstreamaddon', 'inputstream.adaptive')
            listItem.setProperty('inputstream.adaptive.manifest_type', 'hls')
            self.xbmc.Player().play(streamingURL, listItem)

    @staticmethod
    def getLivestreamUrl(url,quality):
        html = common.fetchPage({'link': url})
        container = common.parseDOM(html.get("content"),name='div',attrs={'class': "player_viewport.*?"})
        data_sets = common.parseDOM(container[0],name='div',attrs={},ret="data-jsb")
        for data in data_sets:
            try:
                data = common.replaceHTMLCodes(data)
                data = json.loads(data)
                if 'playlist' in data:
                    if 'videos' in data['playlist']:
                        for video_items in data['playlist']['videos']:
                            for video_sources in video_items['sources']:
                                if video_sources['quality'].lower() == quality.lower() and video_sources['protocol'].lower() == "http" and video_sources['delivery'].lower() == 'hls':
                                    return video_sources['src']
            except:
                debugLog("Error getting Livestream","Info")

    @staticmethod
    def getLivestreamBitmovinID(html):
        container = common.parseDOM(html.get("content"),name='div',attrs={'class': "player_viewport.*?"})
        data_sets = common.parseDOM(container[0],name='div',attrs={},ret="data-jsb")
        for data in data_sets:
            try:
                data = common.replaceHTMLCodes(data)
                data = json.loads(data)
                if 'bitmovin_stream_id' in data:
                    return data['bitmovin_stream_id']
            except:
                debugLog("Error getting Livestream Bitmovin ID","Info")


    @staticmethod
    def getLivestreamInformation(html):
        container = common.parseDOM(html.get("content"),name='div',attrs={'class': "player_viewport.*?"})
        data_sets = common.parseDOM(container[0],name='div',attrs={},ret="data-jsb")
        title       = "Titel"
        image       = ""
        description = "Beschreibung"
        duration    = ""
        date        = ""
        channel     = ""
        time_str    = ""


        for data in data_sets:
            try:
                data = common.replaceHTMLCodes(data)
                data = json.loads(data)

                if 'playlist' in data:
                    if 'title' in data['playlist']:
                        title = data['playlist']['title'].encode('UTF-8')
                    if 'preview_image_url' in data['playlist']:
                        image = data['playlist']['preview_image_url']
                    if 'livestream_start' in data['playlist']:
                        date = data['playlist']['livestream_start']
                        time_str = datetime.datetime.fromtimestamp(int(date)).strftime('%H:%M')
                    if 'livestream_end' in data['playlist']:
                        date = data['playlist']['livestream_end']
                        time_str_end = datetime.datetime.fromtimestamp(int(date)).strftime('%H:%M')
                    if 'videos' in data['playlist']:
                        if 'description' in data['playlist']['videos']:
                            description = data['playlist']['videos']['description']

                    return {"title" : "%s (%s - %s)" % (title,time_str,time_str_end),"image" : image,"description" : description, "date" : date, "duration" : duration, "channel" : channel}
            except:
                debugLog("Error getting Livestream Infos","Info")

    # Helper for Livestream Listing - Returns if Stream is currently running
    @staticmethod
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

    # Parses the Topic Overview Page
    def getThemen(self):
        html = common.fetchPage({'link': self.__urlTopics})
        html_content = html.get("content")

        content = common.parseDOM(html_content,name='section',attrs={})
        #topics = common.parseDOM(content,name='section',attrs={'class':'item_wrapper'})

        for topic in content:
            title = common.parseDOM(topic,name='h3',attrs={'class':'item_wrapper_headline.subheadline'})
            if title:
                title = common.replaceHTMLCodes(title[0]).encode('UTF-8')

                link = common.parseDOM(topic,name='a',attrs={'class':'more.service_link.service_link_more'},ret="href")
                link = common.replaceHTMLCodes(link[0]).encode('UTF-8')

                image = common.parseDOM(topic,name='img',ret="src")
                image = common.replaceHTMLCodes(image[0]).replace("width=395","width=500").replace("height=209.07070707071","height=265").encode('UTF-8')

                descs = common.parseDOM(topic,name='h4',attrs={'class':'item_title'})
                description = ""
                for desc in descs:
                    description += "* "+common.replaceHTMLCodes(desc).encode('UTF-8') + "\n"

                parameters = {"link" : link, "mode" : "getThemenDetail"}
                url = sys.argv[0] + '?' + urllib.urlencode(parameters)
                self.html2ListItem(title,image,"",description,"","","",url,None,True, False);

    # Parses the Archive Detail Page
    def getArchiveDetail(self,url):
        url = urllib.unquote(url)
        html = common.fetchPage({'link': url})
        html_content = html.get("content")

        content = common.parseDOM(html_content,name='section',attrs={'class':'mod_container_list.*?'})

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
                desc = ''

            date = common.parseDOM(topic,name='time')
            date = common.replaceHTMLCodes(date[0]).encode('UTF-8')

            time = common.parseDOM(topic,name='span',attrs={'class':'meta.meta_duration'})
            time = common.replaceHTMLCodes(time[0]).encode('UTF-8')

            desc = "%s - (%s) \n%s" % (str(date),str(time).strip(),str(desc))

            parameters = {"link" : link, "banner" : image, "mode" : "openSeries"}
            url = sys.argv[0] + '?' + urllib.urlencode(parameters)
            self.html2ListItem(title,image,"",desc,"","","",url,None,True, False);

    def getSearchHistory(self,cache):
        parameters = {'mode' : 'getSearchResults'}
        u = sys.argv[0] + '?' + urllib.urlencode(parameters)
        createListItem((self.translation(30007)).encode("utf-8")+" ...", self.defaultbanner, "", "", "", '', u, False, True, self.defaultbackdrop,self.pluginhandle,None)

        cache.table_name = "searchhistory"
        some_dict = cache.get("searches").split("|")
        for str_val in reversed(some_dict):
            if str_val.strip() != '':
                parameters = {'mode' : 'getSearchResults','link' : str_val.replace(" ","+")}
                u = sys.argv[0] + '?' + urllib.urlencode(parameters)
                createListItem(str_val.encode('UTF-8'), self.defaultbanner, "", "", "", '', u, False, True, self.defaultbackdrop,self.pluginhandle,None)

    @staticmethod
    def removeUmlauts(str_val):
        return str_val.replace("Ö","O").replace("ö","o").replace("Ü","U").replace("ü","u").replace("Ä","A").replace("ä","a")

    def getSearchResults(self,link,cache):
        keyboard = self.xbmc.Keyboard(link)
        keyboard.doModal()
        if (keyboard.isConfirmed()):
            cache.table_name = "searchhistory"
            keyboard_in = self.removeUmlauts(keyboard.getText())
            if keyboard_in != link:
                some_dict = cache.get("searches") + "|"+keyboard_in
                cache.set("searches",some_dict);
            searchurl = "%s?q=%s"%(self.__urlSearch,keyboard_in.replace(" ","+"))
            self.getTableResults(searchurl)
        else:
            parameters = {'mode' : 'getSearchHistory'}
            u = sys.argv[0] + '?' + urllib.urlencode(parameters)
            createListItem((self.translation(30014)).encode("utf-8")+" ...", self.defaultbanner, "", "", "", '', u, False, True, self.defaultbackdrop,self.pluginhandle,None)

