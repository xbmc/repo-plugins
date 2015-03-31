#!/usr/bin/python
# -*- coding: utf-8 -*-
import urllib,urllib2,re,xbmcplugin,xbmcgui,sys,xbmcaddon,base64,socket,datetime,time,os,os.path,urlparse,json
import CommonFunctions as common

from base import *
    
class serviceAPI:
    # serviceAPI Settings
    serviceAPItoken         = 'ef97318c84d4e8'

    serviceAPIEpisode       = 'http://tvthek.orf.at/service_api/token/%s/episode/%s/'
    serviceAPIDate          = 'http://tvthek.orf.at/service_api/token/%s/episodes/by_date/%s?page=0&entries_per_page=1000'
    serviceAPIDateFrom      = 'http://tvthek.orf.at/service_api/token/%s/episodes/from/%s0000/till/%s0000?page=0&entries_per_page=1000'
    serviceAPIProgram       = 'http://tvthek.orf.at/service_api/token/%s/episodes/by_program/%s'
    serviceAPISearch        = 'http://tvthek.orf.at/service_api/token/%s/search/%s?page=0&entries_per_page=1000'
    servieAPITopic          = 'http://tvthek.orf.at/service_api/token/%s/topic/%s/'

    serviceAPIPrograms      = 'http://tvthek.orf.at/service_api/token/%s/programs?page=0&entries_per_page=1000'
    serviceAPITopics        = 'http://tvthek.orf.at/service_api/token/%s/topics?page=0&entries_per_page=1000'
    serviceAPITrailers      = 'http://tvthek.orf.at/service_api/token/%s/episodes/trailers?page=0&entries_per_page=1000'

    serviceAPILive          = 'http://tvthek.orf.at/service_api/token/%s/livestreams/from/%s/till/%s/detail?page=0&entries_per_page=%i'
    serviceAPITip           = 'http://tvthek.orf.at/service_api/token/%s/teaser_content/recommendations'
    serviceAPIHighlights    = 'http://tvthek.orf.at/service_api/token/%s/teaser_content/highlights'
    serviceAPIRecent        = 'http://tvthek.orf.at/service_api/token/%s/teaser_content/newest'
    serviceAPIViewed        = 'http://tvthek.orf.at/service_api/token/%s/teaser_content/most_viewed'

    
    def __init__(self,xbmc,settings,pluginhandle,quality,protocol,delivery,defaultbanner,defaultbackdrop,useSubtitles,defaultViewMode):
        self.translation = settings.getLocalizedString
        self.xbmc = xbmc
        self.defaultViewMode = defaultViewMode
        self.videoQuality = quality
        self.videoDelivery = delivery
        self.videoProtocol = protocol
        self.pluginhandle = pluginhandle
        self.defaultbanner = defaultbanner
        self.defaultbackdrop = defaultbackdrop
        self.useSubtitles = useSubtitles
        self.xbmc.log(msg='ServiceAPI  - Init done', level=xbmc.LOGDEBUG);
        
    def getTableResults(self, urlAPI):
        urlAPI = urlAPI % self.serviceAPItoken
        print urlAPI
        try:
            response = urllib2.urlopen(urlAPI)
            responseCode = response.getcode()
        except urllib2.HTTPError, error:
            responseCode = error.getcode()
            pass

        if responseCode == 200:
            global time
            print responseCode
            jsonData = json.loads(response.read())
            if 'teaserItems' in jsonData:
                results = jsonData['teaserItems']
            else:
                results = jsonData['episodeShorts']

            for result in results:
                title       = result.get('title').encode('UTF-8')
                image       = self.JSONImage(result.get('images'))
                if image == '':
                    image = self.JSONImage(result.get('images'), 'logo')
                description = self.JSONDescription(result.get('descriptions'))
                duration    = result.get('duration')
                date        = time.strptime(result.get('date'), '%d.%m.%Y %H:%M:%S')

                description = '%s %s\n\n%s' % ((self.translation(30009)).encode("utf-8"), time.strftime('%A, %d.%m.%Y - %H:%M Uhr', date), description)

                parameters = {'mode' : 'openEpisode', 'link': result.get('episodeId')}
                u = sys.argv[0] + '?' + urllib.urlencode(parameters)
                # Direcotory should be set to False, that the Duration is shown.
                # But then there is an error with the Pluginhandle
                createListItem(title, image, description, duration, time.strftime('%Y-%m-%d', date), '', u, 'false', True,self.translation,self.defaultbackdrop,self.pluginhandle,None)
        else:
            self.xbmc.log(msg='ServiceAPI no available ... switch back to HTML Parsing in the Addon Settings', level=xbmc.LOGDEBUG);
            
            
    # Useful  Methods for JSON Parsing
    def JSONEpisode2ListItem(self,JSONEpisode, ignoreEpisodeType = None):
        title        = JSONEpisode.get('title').encode('UTF-8')
        image        = self.JSONImage(JSONEpisode.get('images'))
        description  = self.JSONDescription(JSONEpisode.get('descriptions'))
        duration     = JSONEpisode.get('duration')
        date         = time.strptime(JSONEpisode.get('date'), '%d.%m.%Y %H:%M:%S')
        link         = JSONEpisode.get('episodeId')

        if JSONEpisode.get('episodeType') == ignoreEpisodeType:
            return None

        parameters = {'mode' : 'openEpisode', 'link': link}
        u = sys.argv[0] + '?' + urllib.urlencode(parameters)
        # Direcotory should be set to False, that the Duration is shown.
        # But then there is an error with the Pluginhandle
        createListItem(title, image, description, duration, time.strftime('%Y-%m-%d', date), '', u, 'false', True,self.translation,self.defaultbackdrop,self.pluginhandle,None)


    def JSONSegment2ListItem(self,JSONSegment, date):
        title        = JSONSegment.get('title').encode('UTF-8')
        image        = self.JSONImage(JSONSegment.get('images'))
        description  = self.JSONDescription(JSONSegment.get('descriptions'))
        duration     = JSONSegment.get('duration')
        streamingURL = self.JSONStreamingURL(JSONSegment.get('videos'))
        if JSONSegment.get('subtitlesSrtFileUrl') and self.useSubtitles:
            subtitles = [JSONSegment.get('subtitlesSrtFileUrl')]
        else:
            subtitles = None
        return [streamingURL, createListItem(title, image, description, duration, time.strftime('%Y-%m-%d', date), '', streamingURL, 'true', False,self.translation,self.defaultbackdrop,self.pluginhandle,subtitles)]

    def JSONDescription(self,jsonDescription):
        desc = ''
        for description in jsonDescription:
            if description.get('text') != None:
                if len(description.get('text')) > len(desc):
                    desc = description.get('text')
                if description.get('fieldName') == 'description':
                    return description.get('text').encode('UTF-8')
        return desc.encode('UTF-8')

    def JSONImage(self,jsonImages, name = 'image_full'):
        logo = ''
        for image in jsonImages:
            if image.get('name') == name:
                return image.get('url')
            elif image.get('name') == 'logo':
                logo = image.get('url')
        return logo

    def JSONStreamingURL(self,jsonVideos):
        for streamingURL in jsonVideos:
            streamingURL = streamingURL.get('streamingUrl')
            if 'http' in streamingURL and 'mp4/playlist.m3u8' in streamingURL:
                return streamingURL.replace('Q4A', self.videoQuality)
        return ''
    
    # list all Categories
    def getCategories(self):
        list = []
        try:
            response = urllib2.urlopen(self.serviceAPIPrograms % self.serviceAPItoken)
            responseCode = response.getcode()
        except urllib2.HTTPError, error:
            responseCode = error.getcode()
            pass

        if responseCode == 200:
            for result in json.loads(response.read())['programShorts']:
                title       = result.get('name').encode('UTF-8')
                image       = self.JSONImage(result.get('images'), 'logo')
                description = ''
                link        = result.get('programId')

                if result.get('episodesCount') == 0:
                    continue

                dict = {}
                dict['title'] = title
                dict['image'] = image
                dict['desc'] = description
                dict['link'] = link
                dict['mode'] = 'openProgram'
                
                parameters = {'mode' : 'openProgram', 'link': link}
                u = sys.argv[0] + '?' + urllib.urlencode(parameters)
                createListItem(title, image, description, "", "", '', u, 'false', True,self.translation,self.defaultbackdrop,self.pluginhandle,None)
        
    
    # list all Episodes for the given Date
    def getDate(self, date, dateFrom = None):
        if dateFrom == None:
            url = self.serviceAPIDate % (self.serviceAPItoken, date)
        else:
            url = self.serviceAPIDateFrom % (self.serviceAPItoken, dateFrom, date)
        response = urllib2.urlopen(url)

        if dateFrom == None:
            episodes = json.loads(response.read())['episodeShorts']
        else:
            episodes = reversed(json.loads(response.read())['episodeShorts'])

        for episode in episodes:
            self.JSONEpisode2ListItem(episode)


    # list all Entries for the given Topic
    def getTopic(self,topicID):
        url = self.servieAPITopic % (self.serviceAPItoken, topicID)
        response = urllib2.urlopen(url)

        for entrie in json.loads(response.read())['topicDetail'].get('entries'):
            title       = entrie.get('title').encode('UTF-8')
            image       = self.JSONImage(entrie.get('images'))
            description = self.JSONDescription(entrie.get('descriptions'))
            duration    = entrie.get('duration')
            date        = time.strptime(entrie.get('date'), '%d.%m.%Y %H:%M:%S')

            if entrie.get('teaserItemType') == 'episode':
                parameters = {'mode' : 'openEpisode', 'link': entrie.get('episodeId')}
            elif entrie.get('teaserItemType') == 'segment':
                parameters = {'mode' : 'openSegment', 'link': entrie.get('episodeId'), 'segmentID': entrie.get('segmentId')}
            else:
                continue

            u = sys.argv[0] + '?' + urllib.urlencode(parameters)
            # Direcotory should be set to False, that the Duration is shown.
            # But then there is an error with the Pluginhandle
            createListItem(title, image, description, duration, time.strftime('%Y-%m-%d', date), '', u, 'false', True,self.translation,self.defaultbackdrop,self.pluginhandle,None)

        


    # list all Episodes for the given Broadcast
    def getProgram(self,programID,playlist):
        url = self.serviceAPIProgram % (self.serviceAPItoken, programID)
        response = urllib2.urlopen(url)
        responseCode = response.getcode()

        if responseCode == 200:
            episodes = json.loads(response.read())['episodeShorts']
            if len(episodes) == 1:
                for episode in episodes:
                    self.getEpisode(episode.get('episodeId'),playlist)
                    return

            for episode in episodes:
                self.JSONEpisode2ListItem(episode, 'teaser')

            


    # listst all Segments for the Episode with the given episodeID
    # If the Episode only contains one Segment, that get played instantly.
    def getEpisode(self,episodeID,playlist):
        playlist.clear()

        url = self.serviceAPIEpisode % (self.serviceAPItoken, episodeID)
        response = urllib2.urlopen(url)
        result = json.loads(response.read())['episodeDetail']

        title       = result.get('title').encode('UTF-8')
        image       = self.JSONImage(result.get('images'))
        description = self.JSONDescription(result.get('descriptions'))
        duration    = result.get('duration')
        date        = time.strptime(result.get('date'), '%d.%m.%Y %H:%M:%S')

        referenceOtherEpisode = False
        for link in result.get('links'):
            if link.get('identifier') == 'program':
                referenceOtherEpisode = True
                addDirectory(link.get('name').encode('UTF-8'), '',  self.defaultbackdrop,self.translation,'', link.get('id'), 'openProgram',self.pluginhandle)

        if referenceOtherEpisode:
            return

        if len(result.get('segments')) == 1:
            for segment in result.get('segments'):
                image        = self.JSONImage(segment.get('images'))
                streamingURL = self.JSONStreamingURL(segment.get('videos'))
                if segment.get('subtitlesSrtFileUrl') and self.useSubtitles:
                    subtitles = [segment.get('subtitlesSrtFileUrl')]
                else:
                    subtitles = None

            listItem = createListItem(title, image, description, duration, time.strftime('%Y-%m-%d', date), '', streamingURL, 'true', False,self.translation,self.defaultbackdrop,self.pluginhandle,subtitles)
            playlist.add(streamingURL, listItem)
            self.xbmc.Player().play(playlist)

        else:
            parameters = {'mode' : 'playlist'}
            u = sys.argv[0] + '?' + urllib.urlencode(parameters)
            createListItem('[ '+(self.translation(30015)).encode('UTF-8')+' ]', image, '%s\n%s' % ((self.translation(30015)).encode('UTF-8'), description), duration, time.strftime('%Y-%m-%d', date), '', u, 'false', False,self.translation,self.defaultbackdrop,self.pluginhandle,None)

            for segment in result.get('segments'):
                listItem = self.JSONSegment2ListItem(segment, date)
                playlist.add(listItem[0], listItem[1])
            
    # Parses the Topic Overview Page
    def getThemen(self):
        try: 
            response = urllib2.urlopen(self.serviceAPITopics % self.serviceAPItoken)
            responseCode = response.getcode()
        except ValueError, error:
            responseCode = 404
            pass
        except urllib2.HTTPError, error:
            responseCode = error.getcode()
            pass

        if responseCode == 200:
            for topic in json.loads(response.read())['topicShorts']:
                if topic.get('parentId') != None or topic.get('isArchiveTopic'):
                    continue
                title       = topic.get('name').encode('UTF-8')
                image       = self.JSONImage(topic.get('images'))
                description = topic.get('description')
                link        = topic.get('topicId')

                addDirectory(title, image, self.defaultbackdrop,self.translation, description, link, 'openTopic',self.pluginhandle)

            
    # Plays the given Segment, if it is included in the given Episode
    def getSegment(self,episodeID, segmentID,playlist):
        playlist.clear()

        url = self.serviceAPIEpisode % (self.serviceAPItoken, episodeID)
        response = urllib2.urlopen(url)
        responseCode = response.getcode()

        if responseCode == 200:
            result = json.loads(response.read())['episodeDetail']
            date = time.strptime(result.get('date'), '%d.%m.%Y %H:%M:%S')
            for segment in result.get('segments'):
                if segment.get('segmentId') == int(segmentID):
                    listItem = self.JSONSegment2ListItem(segment, date)
                    playlist.add(listItem[0], listItem[1])
                    self.xbmc.Player().play(playlist)
                    return                  
                    
    # list all Trailers for further airings
    def getTrailers(self):
        url = self.serviceAPITrailers % self.serviceAPItoken
        response = urllib2.urlopen(url)

        for episode in json.loads(response.read())['episodeShorts']:
            self.JSONEpisode2ListItem(episode)

    
    # lists archiv overview (date listing)
    def getArchiv(self):
        for x in xrange(9):
            date  = datetime.datetime.now() - datetime.timedelta(days=x)
            title = '%s' % (date.strftime('%A, %d.%m.%Y'))
            parameters = {'mode' : 'openDate', 'link': date.strftime('%Y%m%d')}
            if x == 8:
                title = 'älter als %s' % title
                parameters = {'mode' : 'openDate', 'link': date.strftime('%Y%m%d'), 'from': (date - datetime.timedelta(days=150)).strftime('%Y%m%d')}
            u = sys.argv[0] + '?' + urllib.urlencode(parameters)
            createListItem(title, '', title, '', date.strftime('%Y-%m-%d'), '', u, 'False', True,self.translation,self.defaultbackdrop,self.pluginhandle,None)
    
    # Returns Live Stream Listing
    def getLiveStreams(self):
        url = self.serviceAPILive % (self.serviceAPItoken, datetime.datetime.now().strftime('%Y%m%d%H%M'), (datetime.datetime.now() + datetime.timedelta(days=1)).strftime('%Y%m%d%H%M'), 25)
        try: 
            response = urllib2.urlopen(url)
            responseCode = response.getcode()
        except urllib2.HTTPError, error:
            responseCode = error.getcode()
            pass

        if responseCode == 200:
            global time

            bannerurls = {}
            bannerurls['ORF1'] = 'http://tvthek.orf.at/assets/1326810345/orf_channels/logo_color/6779277.png'
            bannerurls['ORF2'] = 'http://tvthek.orf.at/assets/1326810345/orf_channels/logo_color/6779281.png'
            bannerurls['ORF3'] = 'http://tvthek.orf.at/assets/1326810345/orf_channels/logo_color/6779305.png'
            bannerurls['ORFS'] = 'http://tvthek.orf.at/assets/1326810345/orf_channels/logo_color/6779307.png'

            results = json.loads(response.read())['episodeDetails']
            for result in results:

                description     = self.JSONDescription(result.get('descriptions'))
                program         = result.get('channel').get('reel').upper()
                programName     = result.get('channel').get('name')
                programName     = programName.strip()
                livestreamStart = time.strptime(result.get('livestreamStart'), '%d.%m.%Y %H:%M:%S')
                livestreamEnd   = time.strptime(result.get('livestreamEnd'),   '%d.%m.%Y %H:%M:%S')

                # already playing
                if livestreamStart < time.localtime():
                    duration = time.mktime(livestreamEnd) - time.mktime(time.localtime())
                    state = (self.translation(30019)).encode("utf-8")
                    state_short = 'Online'

                else:
                    duration = time.mktime(livestreamEnd) - time.mktime(livestreamStart)
                    state = (self.translation(30020)).encode("utf-8")
                    state_short = 'Offline'
                    link = sys.argv[0] + '?' + urllib.urlencode({'mode': 'liveStreamNotOnline', 'link': result.get('episodeId')})

                # find the livestreamStreamingURLs
                livestreamStreamingURLs = []
                for streamingURL in result.get('livestreamStreamingUrls'):
                    if '.m3u' in streamingURL.get('streamingUrl'):
                        livestreamStreamingURLs.append(streamingURL.get('streamingUrl'))

                livestreamStreamingURLs.sort()
                link = livestreamStreamingURLs[len(livestreamStreamingURLs) - 1].replace('q4a', 'q6a')

                title = "[%s] %s (%s)" % (programName, result.get('title'), time.strftime('%H:%M', livestreamStart))

                if program in bannerurls:
                    banner = bannerurls[program]
                else:
                    banner = ''

                createListItem(title, banner, description, duration, time.strftime('%Y-%m-%d', livestreamStart), program, link, 'True', False,self.translation,self.defaultbackdrop,self.pluginhandle,None)
    
    def getLiveNotOnline(self,link):
        url = self.serviceAPIEpisode % (self.serviceAPItoken, link)
        response = urllib2.urlopen(url)
        result = json.loads(response.read())['episodeDetail']

        title       = result.get('title').encode('UTF-8')
        image       = self.JSONImage(result.get('images'))
        description = self.JSONDescription(result.get('descriptions'))
        duration    = result.get('duration')
        date        = time.strptime(result.get('date'), '%d.%m.%Y %H:%M:%S')
        subtitles   = None # result.get('subtitlesSrtFileUrl')

        dialog = xbmcgui.Dialog()
        if dialog.yesno((self.translation(30030)).encode("utf-8"), (self.translation(30031)).encode("utf-8")+" %s.\n "+(self.translation(30032)).encode("utf-8") % time.strftime('%H:%M', date)):
            sleepTime = int(time.mktime(date) - time.mktime(time.localtime()))
            dialog.notification((self.translation(30033)).encode("utf-8"), '%s %s' % ((self.translation(30034)).encode("utf-8"),sleepTime))
            self.xbmc.sleep(sleepTime * 1000)
            if dialog.yesno('', (self.translation(30035)).encode("utf-8")):
                self.xbmc.Player().play(urllib.unquote(link))

                # find the livestreamStreamingURL
                livestreamStreamingURLs = []
                for streamingURL in result.get('livestreamStreamingUrls'):
                    if '.m3u' in streamingURL.get('streamingUrl'):
                        livestreamStreamingURLs.append(streamingURL.get('streamingUrl'))

                livestreamStreamingURLs.sort()
                streamingURL = livestreamStreamingURLs[len(livestreamStreamingURLs) - 1].replace('q4a', self.videoQuality)
                listItem = createListItem(title, image, description, duration, time.strftime('%Y-%m-%d', date), '', streamingURL, 'true', False,self.translation,self.defaultbackdrop,self.pluginhandle,subtitles)
                self.xbmc.Player().play(streamingURL, listItem)