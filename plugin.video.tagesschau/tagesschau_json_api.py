#
# Copyright 2012 Henning Saul, Joern Schumacher 
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

try: import json
except ImportError: import simplejson as json
import urllib2, logging, datetime, re

logger = logging.getLogger("plugin.video.tagesschau.api")

class VideoContent(object):
    """Represents a single video or broadcast.

    Attributes:
        tsid: A String with the video's id
        title: A String with the video's title
        timestamp: A datetime when this video was broadcast
        imageurls: A dict mapping image variants Strings to their URL Strings
        videourls: A dict mapping video variant Strings to their URL Strings
        duration: An integer representing the length of the video in seconds
        description: A String describing the video content
    """       
    def __init__(self, tsid, title, timestamp, videourls=None, imageurls=None, duration=None, description=None):
        """Inits VideoContent with the given values."""
        self.tsid = tsid
        self.title = title
        # datetime
        self.timestamp = timestamp
        # video/mediadata names mapped to urls
        self._videourls = videourls
        # image variant names mapped to urls
        self._imageurls = imageurls
        # duration in seconds
        self.duration = duration
        # description of content
        self.description = description
    
    def video_id(self):
        return self.tsid
        
    def video_url(self, quality):
        """Returns the video URL String for the given quality.
        
        Falls back to lower qualities if no corresponding video is found.
        
        Args:
            quality: One of 'S', 'M', 'L' or 'X'

        Returns:
            A URL String for the given quality or None if no URL could be found.

        Raises:
            ValueError: If the given quality is invalid
        """
        if (not quality in ['S', 'M', 'L', 'X']):
            raise ValueError("quality must be one of 'S', 'M', 'L', 'X'")

        if quality == 'X':
            videourl = self._videourls.get("h264xl")
            if not videourl:
                videourl = self._videourls.get("http_tab_high")
        if quality == 'L':
            videourl = self._videourls.get("h264l")
            if not videourl:
                videourl = self._videourls.get("http_tab_high")
        if quality == 'M' or not videourl:    
            videourl = self._videourls.get("h264m")
            if not videourl:
                videourl = self._videourls.get("http_tab_normal")
        if quality == 'S' or not videourl:    
            videourl = self._videourls.get("h264s")
            if not videourl:
                videourl = self._videourls.get("http_tab_normal")
        return videourl

    def image_url(self):
        """Returns the URL String of the image for this video."""
        imageurl = self._imageurls.get("gross16x9")
        if(not imageurl):
            # fallback for Wetter
            imageurl = self._imageurls.get("grossgalerie16x9")
        return imageurl
         
    def __str__(self):
        """Returns a String representation for development/testing."""
        if(self.timestamp):
            tsformatted = self.timestamp.isoformat()
        else:
            tsformatted = str(None)      
        s = "VideoContent(tsid=" + self.tsid + ", title='" + self.title + "', timestamp=" + tsformatted + ", "\
            "duration=" + str(self.duration) + ", videourl=" + str(self.video_url('L')) + ", "\
            "imageurl=" + str(self.image_url()) + ", description='" + unicode(self.description) + "')"
        return s.encode('utf-8', 'ignore')


class LazyVideoContent(VideoContent):
    """Represents a single video or broadcast that fetches its video urls attributes lazily.

    Attributes:
        tsid: A String with the video's id
        title: A String with the video's title
        timestamp: A datetime when this video was broadcast
        imageurls: A dict mapping image variants Strings to their URL Strings
        detailsurl: A String pointing to the detail JSON for this video
        duration: An integer representing the length of the video in seconds
        description: A String describing the video content
    """  
    def __init__(self, tsid, title, timestamp, detailsurl, imageurls=None, duration=None, description=None):
        VideoContent.__init__(self, tsid, title, timestamp, None, imageurls, duration, description)
        self.detailsurl = detailsurl
        self.detailsfetched = False
        self._videoid = ""
        self._parser = VideoContentParser()
        self._logger = logging.getLogger("plugin.video.tagesschau.api.LazyVideoContent")

    def video_id(self):
        """Overwritten to fetch details lazily."""
        if(not self.detailsfetched):
            self._fetch_details()
        return self._videoid
          
    def video_url(self, quality):
        """Overwritten to fetch videourls lazily."""
        if(not self.detailsfetched):
            self._fetch_details()
        return VideoContent.video_url(self, quality)    
    
    def _fetch_details(self):
        """Fetches videourls from detailsurl."""
        self._logger.info("fetching details from " + self.detailsurl)
        handle = urllib2.urlopen(self.detailsurl)
        jsondetails = json.load(handle)
        self._videourls = self._parser.parse_video_urls(jsondetails["fullvideo"][0]["mediadata"])       
        self._videoid = jsondetails["fullvideo"][0]["sophoraId"]
        self.detailsfetched = True
        self._logger.info("fetched details")


class VideoContentParser(object):
    """Parses JSON/Python structure into VideoContent.""" 
    
    def parse_video(self, jsonvideo):
        """Parses the video JSON into a VideoContent object."""
        tsid = jsonvideo["sophoraId"]
        title = jsonvideo["headline"]
        timestamp = self._parse_date(jsonvideo["broadcastDate"])
        imageurls = {}
        if(len(jsonvideo["images"]) > 0):
            imageurls = self._parse_image_urls(jsonvideo["images"][0]["variants"])
        videourls = self.parse_video_urls(jsonvideo["mediadata"])
        # calculate duration using outMilli and inMilli, duration is not set in JSON
        if("inMilli" in jsonvideo and "outMilli" in jsonvideo):
            duration = (jsonvideo["outMilli"] - jsonvideo["inMilli"]) / 1000
        else:
            duration = None    
        return VideoContent(tsid, title, timestamp, videourls, imageurls, duration)    

    def parse_ts_100_sek(self, jsonvideo):
        """Parses the video JSON into a VideoContent object."""
        tsid = "none"
        title = jsonvideo["headline"]
        timestamp = self._parse_date(jsonvideo["broadcastDate"])
        if(timestamp):
#            print '-'*20
#            print timestamp
            title = title + timestamp.strftime(' vom %d.%m.%Y %H:%M')
        imageurls = {}
        if(len(jsonvideo["images"]) > 0):
            imageurls = self._parse_image_urls(jsonvideo["images"][0]["variants"])
        videourls = self.parse_video_urls(jsonvideo["mediadata"])
        print videourls
        # calculate duration using outMilli and inMilli, duration is not set in JSON
        if("inMilli" in jsonvideo and "outMilli" in jsonvideo):
            duration = (jsonvideo["outMilli"] - jsonvideo["inMilli"]) / 1000
        else:
            duration = None
        #print title
        return VideoContent(tsid, title, timestamp, videourls, imageurls, duration)    


    def parse_broadcast(self, jsonbroadcast, timestring = '%d.%m.%Y'):
        """Parses the broadcast JSON into a LazyVideoContent object."""
        tsid = jsonbroadcast["sophoraId"]
        title = jsonbroadcast["title"]
        timestamp = self._parse_date(jsonbroadcast["broadcastDate"])
        if(timestamp):
            title = title + timestamp.strftime(' vom ' + timestring)
        imageurls = self._parse_image_urls(jsonbroadcast["images"][0]["variants"])
        details = jsonbroadcast["details"]
        description = None
        if("topics" in jsonbroadcast):
            description = ", ".join(jsonbroadcast["topics"])
        # return LazyVideoContent that retrieves details JSON lazily
        return LazyVideoContent(tsid, title, timestamp, details, imageurls, None, description)

    def _parse_livestream(self, jsonlivestream):
        """Parses the livestream JSON into a VideoContent object."""
        tsid = "livestream"
        title = "Livestream: " + jsonlivestream["title"]
        timestamp = None
        imageurls = self._parse_image_urls(jsonlivestream["images"][0]["variants"])
        videourls = self.parse_video_urls(jsonlivestream["mediadata"]) 
        return VideoContent(tsid, title, timestamp, videourls, imageurls)

    def parse_livestreams(self, jsonlivestreams):
        """Parses the multimedia JSON into a list of VideoContent objects."""
        videos = []
        for jsonvideo in jsonlivestreams:
            # only add livestream if on the air now...
            if(jsonvideo["live"] == "true"):               
                video = self._parse_livestream(jsonvideo)
                videos.append(video)            
        return videos

    def parse_video_urls(self, jsonvariants):
        """Parses the video mediadata JSON into a dict mapping variant name to URL."""
        variants = {}
        for jsonvariant in jsonvariants:
            for name, url in jsonvariant.iteritems():
                variants[name] = url
        return variants

    def _parse_date(self, isodate):
        """Parses the given date in iso format into a datetime."""
        if(not isodate):
            return None
        # ignore time zone part
        isodate = isodate[:-6]
        return datetime.datetime(*map(int, re.split('[^\d]', isodate)))

    def _parse_image_urls(self, jsonvariants):
        """Parses the image variants JSON into a dict mapping variant name to URL.""" 
        variants = {}
        for jsonvariant in jsonvariants:
            for name, url in jsonvariant.iteritems():
                variants[name] = url
        return variants


class VideoContentProvider(object):
    """Provides access to the VideoContent offered by the tagesschau JSON API.""" 
    
    def __init__(self, jsonsource):
        self._jsonsource = jsonsource
        self._parser = VideoContentParser()
        self._logger = logging.getLogger("plugin.video.tagesschau.api.VideoContentProvider")

    def livestreams(self):
        """Retrieves the livestream(s) currently on the air.
        
            Returns:
                A list of VideoContent object for livestream(s) on the air.
        """
        self._logger.info("retrieving livestream(s)")
        videos = []
        data = self._jsonsource.livestreams()
        if("multimedia" in data):
            multimedia = data["multimedia"]
            if("livestreams" in multimedia[0]):  
                videos = self._parser.parse_livestreams(multimedia[0]["livestreams"])         
        return videos    

    def latest_videos(self):
        """Retrieves the latest videos.
            
            Returns: 
                A list of VideoContent items.
        """
        self._logger.info("retrieving videos")
        videos = []
        data = self._jsonsource.latest_videos()
        for jsonvideo in data["videos"]:
            video = self._parser.parse_video(jsonvideo)
            videos.append(video) 
    
        videos.append(self.tagesschau_in_100_sek())

        self._logger.info("found " + str(len(videos)) + " videos")
        return videos

    def tagesschau_in_100_sek(self):
        self._logger.info("retrieving videos")
        data = self._jsonsource.latest_videos()
        if("multimedia" in data):
            multimedia = data["multimedia"]
            if("tsInHundredSeconds" in multimedia[1]):  
                #print multimedia[1]
                video = self._parser.parse_ts_100_sek(multimedia[1]["tsInHundredSeconds"])
        return video

    def dossiers(self):
        """Retrieves the latest dossier videos.
            
            Returns: 
                A list of VideoContent items.
        """    
        self._logger.info("retrieving videos")
        videos = []
        data = self._jsonsource.dossiers()
        for jsonvideo in data["videos"]:
            video = self._parser.parse_video(jsonvideo)
            videos.append(video)  
        self._logger.info("found " + str(len(videos)) + " videos")            
        return videos

    def latest_broadcasts(self):
        """Retrieves the latest broadcast videos.
            
            Returns: 
                A list of VideoContent items.
        """        
        self._logger.info("retrieving videos")
        videos = []
        data = self._jsonsource.latest_broadcasts()
        for jsonbroadcast in data["latestBroadcastsPerType"]:
            video = self._parser.parse_broadcast(jsonbroadcast)
            videos.append(video)

        videos.append(self.tagesschau_in_100_sek())
	videos.append(self._parser.parse_broadcast(data["latestBroadcast"], '%d.%m.%Y %H:%M'))

        self._logger.info("found " + str(len(videos)) + " videos")              
        return videos

    def archived_broadcasts(self):
        """Retrieves the archive broadcast videos.
            
            Returns: 
                A list of VideoContent items.
        """        
        self._logger.info("retrieving videos") 
        videos = []
        data = self._jsonsource.archived_broadcasts()
        for jsonbroadcast in data["latestBroadcastsPerType"]:
            video = self._parser.parse_broadcast(jsonbroadcast)
            videos.append(video)
        self._logger.info("found " + str(len(videos)) + " videos")              
        return videos


class JsonSource(object):
    """Provides access to the raw objects parsed from the TS JSON API.
        Can be replaced for unittesting purposes."""
    
    def livestreams(self):
        """Returns the parsed JSON structure for livestreams."""
        handle = urllib2.urlopen("http://www.tagesschau.de/api/multimedia/video/ondemand100~_type-video.json")
        return json.loads(handle.read())

    def latest_videos(self):
        """Returns the parsed JSON structure for the latest videos."""        
        handle = urllib2.urlopen("http://www.tagesschau.de/api/multimedia/video/ondemand100~_type-video.json")
        return json.loads(handle.read())

    def dossiers(self):
        """Returns the parsed JSON structure for the dossiers."""        
        handle = urllib2.urlopen("http://www.tagesschau.de/api/multimedia/video/ondemanddossier100.json")
        return json.loads(handle.read())

    def latest_broadcasts(self):
        """Returns the parsed JSON structure for the latest broadcasts."""        
        handle = urllib2.urlopen("http://www.tagesschau.de/api/multimedia/sendung/letztesendungen100.json")
        return json.loads(handle.read())

    def archived_broadcasts(self):
        """Returns the parsed JSON structure for the archived broadcasts."""        
        handle = urllib2.urlopen("http://www.tagesschau.de/api/multimedia/sendung/letztesendungen100~_week-true.json")
        return json.loads(handle.read())
        
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s %(funcName)s %(message)s')
    provider = VideoContentProvider(JsonSource())
    videos = provider.livestreams()
    print "Livestreams:"     
    for video in videos:
        print video
    video = provider.tagesschau_in_100_sek()
    print "100 Sek Videos"     
    print video
    #if True:
    #    sys.exit(0)
    videos = provider.latest_videos()
    print "Aktuelle Videos"     
    for video in videos:
        print video
    videos = provider.dossiers()
    print "Dossier"
    for video in videos:
        print video
    videos = provider.latest_broadcasts()
    print "Aktuelle Sendungen"
    for video in videos:
        print video
    videos = provider.archived_broadcasts()
    print "Sendungsarchiv"
    for video in videos:
        print video   
    
