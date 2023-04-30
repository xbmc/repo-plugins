#
# Copyright 2012 Henning Saul, Joern Schumacher
# Copyright 2021 Christian Prasch
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
import logging, datetime, re, urllib.request, xbmc, xbmcaddon
#import web_pdb

# -- Constants ----------------------------------------------
ADDON_ID = 'plugin.video.tagesschau'

logger = logging.getLogger("plugin.video.tagesschau.api")
base_url = "https://www.tagesschau.de/api2u/"

addon = xbmcaddon.Addon(id=ADDON_ID)
showage = addon.getSettingBool('ShowAge')

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
    def __init__(self, tsid, title, timestamp, videourls=None, imageurls=None, duration=None, description=""):
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

        videourl = None
        
        if quality == 'X':
            videourl = self._videourls.get("h264xl")
        if quality == 'L' or not videourl:
            videourl = self._videourls.get("h264m")
        if quality == 'M' or not videourl:
            videourl = self._videourls.get("h264s")
        if quality == 'S' or not videourl:
            videourl = self._videourls.get("h264s")

        #nothing found if it is a livestream
        if videourl == None:
            videourl = self._videourls.get("adaptivestreaming")
            
        return videourl

    def image_url(self):
        """Returns the URL String of the image for this video."""
        imageurl = self._imageurls.get("16x9-640")
        return imageurl

    def __str__(self):
        """Returns a String representation for development/testing."""
        if(self.timestamp):
            tsformatted = self.timestamp.isoformat()
        else:
            tsformatted = str(None)
        s = "VideoContent(tsid=" + self.tsid + ", title='" + self.title + "', timestamp=" + tsformatted + ", "\
            "duration=" + str(self.duration) + ", videourl=" + str(self.video_url('L')) + ", "\
            "imageurl=" + str(self.image_url()) + ", description='" + str(self.description) + "')"
        return s.encode('utf-8', 'ignore')


class VideoContentParser(object):
    """Parses JSON/Python structure into VideoContent."""

    def parse_video(self, jsonvideo):
        """Parses the video JSON into a VideoContent object."""
        tsid = jsonvideo["sophoraId"]
        timestamp = self._parse_date(jsonvideo["date"])
        imageurls = {}
        imageurls = self._parse_image_urls(jsonvideo["teaserImage"]["imageVariants"])
        videourls = self.parse_video_urls(jsonvideo["streams"])
        duration = int(jsonvideo["tracking"][1]["length"])
        
        age = datetime.datetime.now() - timestamp
        if age.seconds > 3600:
            agestr = str(age.seconds//3600) + "h " + str(age.seconds // 60 % 60) +"min"
        else:
            agestr = str(age.seconds // 60 % 60) +"min"
        
        agostr = addon.getLocalizedString(30103)
        if agostr == "ago":
            agostr = agestr + " " + agostr
        else:
            agostr = agostr + " " + agestr

        if showage:
            title = agostr + ": " + jsonvideo["title"]    
        else:
            title = jsonvideo["title"]    
        
        description = agostr + "\n" + jsonvideo["title"]    
            
        return VideoContent(tsid, title, timestamp, videourls, imageurls, duration, description)

    def parse_broadcast(self, jsonbroadcast ):
        """Parses the broadcast JSON into a LazyVideoContent object."""
        tsid = jsonbroadcast["sophoraId"]
        title = jsonbroadcast["title"]
        timestamp = self._parse_date(jsonbroadcast["date"])
        if(timestamp):
            title = title + timestamp.strftime(' vom %d.%m.%Y  %H:%M')
        imageurls = {}
        imageurls = self._parse_image_urls(jsonbroadcast["teaserImage"]["imageVariants"])
        videourls = self.parse_video_urls(jsonbroadcast["streams"])
        duration = int(jsonbroadcast["tracking"][1]["length"])
        description = title
        return VideoContent(tsid, title, timestamp, videourls, imageurls, duration, description)

    def parse_livestream(self, jsonlivestream):
        """Parses the livestream JSON into a VideoContent object."""
        tsid = "livestream"
        title = "Livestream"
        timestamp = None
        imageurls = {}
        imageurls = self._parse_image_urls(jsonlivestream["teaserImage"]["imageVariants"])
        videourls = self.parse_video_urls(jsonlivestream["streams"])
        return VideoContent(tsid, title, timestamp, videourls, imageurls)

    def parse_video_urls(self, jsonvariants):
        """Parses the video mediadata JSON into a dict mapping variant name to URL."""
        variants = {}
        for name, url in list(jsonvariants.items()):
            variants[name] = url
        return variants

    def _parse_date(self, isodate):
        """Parses the given date in iso format into a datetime."""
        if(not isodate):
            return None
        # ignore time zone part
        isodate = isodate[:-6]
        return datetime.datetime(*list(map(int, re.split('[^\d]', isodate))))

    def _parse_image_urls(self, jsonvariants):
        """Parses the image variants JSON into a dict mapping variant name to URL."""
        variants = {}
        for name, url in list(jsonvariants.items()):
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
        for jsonstream in data["channels"]:
            if( not "date" in jsonstream ): # livestream has no date
                video = self._parser.parse_livestream(jsonstream)
                videos.append(video)

        return videos

    def latest_videos(self):
        """Retrieves the latest videos.

            Returns:
                A list of VideoContent items.
        """
        self._logger.info("retrieving videos")
        videos = []
        data = self._jsonsource.latest_videos()
        for jsonvideo in data["news"]:
            if( (jsonvideo["type"] == "video") and (jsonvideo["tracking"][0]["src"] == "ard-aktuell") ):
                video = self._parser.parse_video(jsonvideo)
                videos.append(video)

        self._logger.info("found " + str(len(videos)) + " videos")
        return videos

    def latest_broadcasts(self):
        """Retrieves the latest broadcast videos.

            Returns:
                A list of VideoContent items.
        """
        self._logger.info("retrieving broadcasts")
        videos = []
        data = self._jsonsource.latest_broadcasts()
        for jsonbroadcast in data["channels"]:
            if( "date" in jsonbroadcast ):  # Filter out livestream which has no date
                video = self._parser.parse_broadcast(jsonbroadcast)
                videos.append(video)

        self._logger.info("found " + str(len(videos)) + " videos")
        return videos


class JsonSource(object):
    """Provides access to the raw objects parsed from the TS JSON API.
        Can be replaced for unittesting purposes."""

    def livestreams(self):
        """Returns the parsed JSON structure for livestreams."""
        handle = urllib.request.urlopen(base_url + "channels")
        return json.loads(handle.read())

    def latest_videos(self):
        """Returns the parsed JSON structure for the latest videos."""
        handle = urllib.request.urlopen(base_url + "news")
        return json.loads(handle.read())

    def latest_broadcasts(self):
        """Returns the parsed JSON structure for the latest broadcasts."""
        handle = urllib.request.urlopen(base_url + "channels")
        return json.loads(handle.read())
