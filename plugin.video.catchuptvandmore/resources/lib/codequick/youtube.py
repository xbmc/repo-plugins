# -*- coding: utf-8 -*-
from __future__ import absolute_import

# Standard Library Imports
import logging
import sqlite3
import json
import os

# Package imports
from resources.lib.codequick.route import Route
from resources.lib.codequick.utils import bold
from resources.lib.codequick.listing import Listitem
from resources.lib.codequick.resolver import Resolver
from resources.lib.codequick.support import logger_id
from resources.lib import urlquick

# Logger specific to this module
logger = logging.getLogger("%s.youtube" % logger_id)

# Localized string Constants
ALLVIDEOS = 32003
PLAYLISTS = 136
PLAYLISTS_PLOT = 32007

# Constants
CACHEFILE = os.path.join(Route.get_info("profile"), u"_youtube-cache.sqlite")  # Youtube cache directory
EXCEPTED_STATUS = [u"public", u"unlisted"]


class Database(object):
    def __init__(self):
        # Unfortunately with python 3, sqlite3.connect might fail if system local is 'c_type'(ascii)
        self.db = db = sqlite3.connect(CACHEFILE, timeout=1)

        db.isolation_level = None
        db.row_factory = sqlite3.Row
        self.cur = cur = db.cursor()

        # Performance tweaks
        cur.execute('PRAGMA locking_mode=EXCLUSIVE')
        cur.execute('PRAGMA journal_mode=MEMORY')
        cur.execute('PRAGMA temp_store=MEMORY')

        # Create missing channel table
        cur.execute("""CREATE TABLE IF NOT EXISTS channels
                    (channel_id TEXT PRIMARY KEY, uploads_id TEXT, fanart TEXT, channel_title TEXT)""")

        # Create missing category table
        cur.execute("""CREATE TABLE IF NOT EXISTS categories
                    (id INT PRIMARY KEY, genre TEXT)""")

        # Create missing video table
        cur.execute("""CREATE TABLE IF NOT EXISTS videos
                    (video_id TEXT PRIMARY KEY, title TEXT, thumb TEXT, description TEXT, genre_id INT,
                    count INT, date TEXT, hd INT, duration INT, channel_id TEXT,
                    FOREIGN KEY(channel_id) REFERENCES channels(channel_id),
                    FOREIGN KEY(genre_id) REFERENCES categories(id))""")

    def execute(self, execute_obj, sqlquery, args=""):
        self.cur.execute("BEGIN")
        try:
            execute_obj(sqlquery, args)
        except Exception as e:  # pragma: no cover
            self.db.rollback()
            raise e
        else:
            self.db.commit()

    def update_channels(self, channels):
        sqlquery = "INSERT INTO channels VALUES(:channel_id, :uploads_id, :fanart, :channel_title)"
        self.execute(self.cur.executemany, sqlquery, channels)

    def update_categories(self, categories):
        sqlquery = "INSERT INTO categories VALUES(?, ?)"
        self.execute(self.cur.executemany, sqlquery, categories)

    def update_videos(self, videos):
        sqlquery = """INSERT INTO videos VALUES(:video_id, :title, :thumb, :description,
                      :genre_id, :count, :date, :hd, :duration, :channel_id)"""
        self.execute(self.cur.executemany, sqlquery, videos)

    def extract_videos(self, data):
        results = self.cur.execute("""
        SELECT video_id, title, thumb, description, genre, count, date, hd, duration, videos.channel_id,
        fanart, channel_title FROM videos INNER JOIN channels ON channels.channel_id = videos.channel_id
        INNER JOIN categories ON categories.id = videos.genre_id
        WHERE video_id IN (%s)""" % ",".join("?" * len(data)), data)
        return {row[0]: row for row in results}

    @property
    def channels(self):
        """Return all channel ids."""
        return {data[0]: data[1] for data in self.cur.execute("SELECT channel_id, uploads_id FROM channels")}

    @property
    def categories(self):
        """Return all channel ids."""
        return frozenset(data[0] for data in self.cur.execute("SELECT id FROM categories"))

    def close(self):
        self.cur.close()
        self.db.close()

    def cleanup(self):
        """Trim down the cache if cache gets too big."""
        # Registor cleanup if the database has more than 10,000 videos stored
        if self.cur.execute("SELECT COUNT(*) FROM videos").fetchone()[0] > 10000:
            logger.debug("Running Youtube Cache Cleanup")

            # Remove all but 2,500 of the most recent videos
            sqlquery = """DELETE FROM videos WHERE video_id IN (select video_id from videos
                          ORDER BY date DESC LIMIT -1 OFFSET 2500)"""
            self.execute(self.cur.execute, sqlquery)

            # Remove any leftover channels
            sqlquery = """DELETE FROM channels WHERE channel_id in (SELECT channel_id from channels
                          WHERE channel_id not in (SELECT channel_id from videos))"""
            self.execute(self.cur.execute, sqlquery)

            # Compact the database using vacuum
            self.cur.execute("VACUUM")

        self.close()


class API(object):
    """
    API class to handle requests to the youtube v3 api.

    :param int max_results: [opt] The maximum number of items per page that should be returned. (default => 50)
    :param bool pretty_print: [opt] If True then the json response will be nicely indented. (default => False)
    """

    def __init__(self, max_results=50, pretty_print=False):
        self.req_session = urlquick.Session()
        self.req_session.headers["referer"] = "http://www.codequick.com/"
        self.req_session.params = {"maxResults": str(max_results),
                                   "prettyPrint": str(pretty_print).lower(),
                                   "key": "AIzaSyD_guosGuZjoQLWIZdJzYzYEn3Oy8VOUgs"}

    def _request(self, url, query):
        """
        Make online resource request.

        :param str url: The url resource to request.
        :param dict query: Dictionary of parameters that will be send to the api as a query.
        :return: The youtube api response
        :rtype: dict

        :raises RuntimeError: If youtube returns a error response.
        """
        source = self.req_session.get(url, params=query)
        response = json.loads(source.content, encoding=source.encoding)
        if u"error" not in response:  # pragma: no branch
            return response
        else:  # pragma: no cover
            try:
                message = response[u"error"][u"errors"][0][u"message"]
            except (KeyError, ValueError):
                raise RuntimeError("Youtube V3 API return an error response")
            else:
                raise RuntimeError("Youtube V3 API return an error response: %s" % message)

    def _connect_v3(self, api_type, query, loop=False):
        """
        Send API request and return response as a json object.

        :param str api_type: The type of api request to make.
        :param dict query: Dictionary of parameters that will be send to the api as a query.
        :param bool loop: [opt] Return all the playlists for channel. (Default => False)
        :returns: The youtube api response as a dictionary.
        :rtype: dict
        """
        # Convert id query from a list, to a comma separated list of id's, if required
        if "id" in query and hasattr(query["id"], '__iter__'):
            query["id"] = u",".join(query["id"])

        # Download the resource from the youtube v3 api
        url = "https://www.googleapis.com/youtube/v3/%s" % api_type
        if "id" in query:
            ids = query["id"].split(",")
            counter = 0

            # Fetch the first set of 50 item and use a base
            query["id"] = ",".join(ids[counter:counter + 50])
            feed = self._request(url, query)
            results = feed
            counter += 50

            # Fetch all content, 50 item at a time
            while counter < len(ids):
                query["id"] = ",".join(ids[counter:counter + 50])
                feed = self._request(url, query)
                results[u"items"].extend(feed[u"items"])
                counter += 50

            # Return the full feed
            return results

        elif loop:
            # Fetch the first page and use as base
            feed = self._request(url, query)
            results = feed

            # Loop until there is no more page tokens available
            while u"nextPageToken" in feed:
                query["pageToken"] = feed.pop(u"nextPageToken")
                feed = self._request(url, query)
                results[u"items"].extend(feed[u"items"])

            # Return the full feed
            return results
        else:
            return self._request(url, query)

    def channels(self, channel_id):
        """
        Return all available information for giving channel

        Note:
        If both parameters are given, then channel_id will take priority.

        Refer to 'https://developers.google.com/youtube/v3/docs/channels/list'

        :param channel_id: ID(s) of the channel for requesting data for.

        :returns: Dictionary of channel information.
        :rtype: dict

        :raises ValueError: If neither channel_id or for_username is given.
        """
        # Set parameters
        query = {"hl": "en", "part": "contentDetails,brandingSettings,snippet", "id": channel_id,
                 "fields": "items(id,brandingSettings/image/bannerTvMediumImageUrl,"
                           "contentDetails/relatedPlaylists/uploads,snippet/localized/title)"}

        # Connect to server and return json response
        return self._connect_v3("channels", query)

    def video_categories(self, region_code="us"):
        """
        Return the categorie names for giving id(s)

        Refer to 'https://developers.google.com/youtube/v3/docs/videoCategories/list'

        Note:
        If no id(s) are given then all category ids are fetched for given region.

        :param str region_code: [opt] The region code for the categories id(s).

        :returns: Dictionary of video categories.
        :rtype: dict
        """
        # Set parameters
        query = {"fields": "items(id,snippet/title)", "part": "snippet", "hl": "en", "regionCode": region_code}

        # Fetch video Information
        return self._connect_v3("videoCategories", query)

    def playlist_items(self, playlist_id, pagetoken=None, loop=False):
        """
        Return all videos ids for giving playlist ID.

        Refer to 'https://developers.google.com/youtube/v3/docs/playlistItems/list'

        :param str playlist_id: ID of youtube playlist
        :param str pagetoken: The token for the next page of results
        :param bool loop: [opt] Return all the videos within playlist. (Default => False)

        :returns: Dictionary of playlist items.
        :rtype: dict
        """
        # Set parameters
        query = {"fields": "nextPageToken,items(snippet(channelId,resourceId/videoId),status/privacyStatus)",
                 "playlistId": playlist_id, "part": "snippet,status"}

        # Add pageToken if exists
        if pagetoken:  # pragma: no cover
            query["pageToken"] = pagetoken

        # Connect to server to optain json response
        return self._connect_v3("playlistItems", query, loop)

    def videos(self, video_id):
        """
        Return all available information for giving video/vidoes.

        Refer to 'https://developers.google.com/youtube/v3/docs/videos/list'

        :param video_id: Video id(s) to fetch data for.
        :type video_id: str or list or frozenset

        :returns: Dictionary of video items.
        :rtype: dict
        """
        # Set parameters
        query = {"part": "contentDetails,statistics,snippet", "hl": "en", "id": video_id,
                 "fields": "items(id,snippet(publishedAt,channelId,thumbnails/medium/url,"
                           "categoryId,localized),contentDetails(duration,definition),statistics/viewCount)"}

        # Connect to server and return json response
        return self._connect_v3("videos", query)

    def playlists(self, channel_id, pagetoken=None, loop=False):
        """
        Return all playlist for a giving channel_id.

        Refer to 'https://developers.google.com/youtube/v3/docs/playlists/list'

        :param str channel_id: Id of the channel to fetch playlists for.
        :param str pagetoken: The token for the next page of results
        :param bool loop: [opt] Return all the playlists for channel. (Default => False)

        :returns: Dictionary of playlists.
        :rtype: dict
        """
        # Set Default parameters
        query = {"part": "snippet,contentDetails", "channelId": channel_id,
                 "fields": "nextPageToken,items(id,contentDetails/itemCount,snippet"
                           "(publishedAt,localized,thumbnails/medium/url))"}

        # Add pageToken if exists
        if pagetoken:  # pragma: no cover
            query["pageToken"] = pagetoken

        # Connect to server to optain json response
        return self._connect_v3("playlists", query, loop)

    def search(self, **search_params):
        """
        Return any search results.

        Refer to 'https://developers.google.com/youtube/v3/docs/search/list' for search Parameters

        :param search_params: Keyword arguments of Youtube API search Parameters

        :returns: Dictionary of search results.
        :rtype: dict
        """
        # Set Default parameters
        query = {"relevanceLanguage": "en", "safeSearch": "none", "part": "snippet", "type": "video",
                 "fields": "nextPageToken,items(id/videoId,snippet/channelId)"}

        # Add the search params to query
        query.update(search_params)

        # Connect to server and return json response
        return self._connect_v3("search", query)


class APIControl(Route):
    """Class to control the access to the youtube API."""

    def __init__(self):
        super(APIControl, self).__init__()
        self.db = Database()
        self.register_delayed(self.db.cleanup)
        self.api = API()

    def valid_playlistid(self, contentid):
        """
        Return a valid playlist uuid.

        Contentid can be a channel uuid, playlist uuid or channel uploads uuid.
        If channel uuid is given, then the required uploads uuid will be fetched
        from youtube and stored in the cache.

        :param str contentid: ID of youtube content to validate, Channel uuid,
                              Channel Uploads uuid or Playlist uuid.

        :raises ValueError: If contentid is not one of the required types.
        """
        # Check if content is a channel id
        if contentid.startswith("UC"):
            # Extract channel upload id from cache
            channel_cache = self.db.channels
            if contentid in channel_cache:
                return channel_cache[contentid]
            else:
                # Channel data is missing from cache
                # Update cache and return uploads uuid
                self.update_channel_cache([contentid])
                if contentid in self.db.channels:
                    return self.db.channels[contentid]
                else:
                    raise KeyError("Unable to find Youtube channel: {}".format(contentid))

        # PL = Playlist / UU = Channel Uploads / FL = Favorites List
        elif contentid[:2] in ("PL", "FL", "UU"):
            return contentid
        else:
            raise ValueError("contentid is not of valid type (PL,UU,UC): %s" % contentid)

    def update_category_cache(self):
        """Update on cache of category information."""
        feed = self.api.video_categories()
        category_cache = self.db.categories
        self.db.update_categories((int(item[u"id"]), item[u"snippet"][u"title"])
                                  for item in feed[u"items"] if int(item[u"id"]) not in category_cache)

    def update_channel_cache(self, ids):
        """
        Update the database of cached channel information.

        :param ids: ID(s) of the channel to request information for.
        :type ids: list
        """
        # Make channels api request
        feed = self.api.channels(ids)
        processed_channels = []

        for item in feed[u"items"]:
            # Fetch common info
            data = {"channel_id": item[u"id"],
                    "channel_title": item[u"snippet"][u"localized"][u"title"],
                    "uploads_id": item[u"contentDetails"][u"relatedPlaylists"][u"uploads"]}

            # Fetch the channel banner if available
            try:
                data["fanart"] = item[u"brandingSettings"][u"image"][u"bannerTvMediumImageUrl"]
            except KeyError:  # pragma: no cover
                data["fanart"] = None

            # Add the dict of channel data to list of channels that will be added to database
            processed_channels.append(data)

        self.db.update_channels(processed_channels)

    def request_videos(self, ids):
        """
        Return all requested videos from cache.

        If requested video(s) are not cached, the video data will be
        downloaded and added to cache.

        :param ids: ID(s) of the videos to request information for.
        :type ids: list
        """
        cached_videos = self.db.extract_videos(ids)
        uncached_ids = list(frozenset(key for key in ids if key not in cached_videos))  # pragma: no branch
        if uncached_ids:
            # Fetch video information
            feed = self.api.videos(uncached_ids)
            duration_search = __import__("re").compile("(\d+)(\w)")
            category_cache = self.db.categories
            channel_cache = self.db.channels
            update_categories = False
            required_channels = []
            processed_videos = []

            for video in feed[u"items"]:
                snippet = video[u"snippet"]
                content_details = video[u"contentDetails"]
                data = {
                    "title": snippet[u"localized"][u"title"],
                    "thumb": snippet[u"thumbnails"][u"medium"][u"url"],
                    "description": snippet[u"localized"][u"description"],
                    "date": snippet[u"publishedAt"],
                    "count": int(video["statistics"]["viewCount"]) if "statistics" in video else 0,
                    "channel_id": snippet[u"channelId"],
                    "video_id": video[u"id"],
                    "hd": int(content_details[u"definition"] == u"hd"),
                    "duration": "",
                    "genre_id": int(snippet[u"categoryId"])
                }

                # Convert duration to what kodi is expecting (duration in seconds)
                duration_str = content_details[u"duration"]
                duration_match = duration_search.findall(duration_str)
                if duration_match:  # pragma: no branch
                    data["duration"] = self._convert_duration(duration_match)

                # Add the dict of video data to list of video that will be added to database
                processed_videos.append(data)

                if data["channel_id"] not in required_channels and data["channel_id"] not in channel_cache:
                    required_channels.append(data["channel_id"])

                if update_categories is False and data["genre_id"] not in category_cache:
                    update_categories = True

            if required_channels:
                self.update_channel_cache(required_channels)
            if update_categories:
                self.update_category_cache()

            # Now we can safelly update the video cache
            self.db.update_videos(processed_videos)
            cached = self.db.extract_videos(uncached_ids)
            cached_videos.update(cached)

        # Return each video in the order givin by the playlist
        return (cached_videos[video_id] for video_id in ids if video_id in cached_videos)

    def videos(self, video_ids, multi_channel=False):
        """
        Process VideoIDs and return listitems in a generator

        :param video_ids: List of all the videos to show.
        :param bool multi_channel: [opt] Set to True to enable linking to channel playlists. (default => False)

        :returns: A generator of listitems.
        :rtype: :class:`types.GeneratorType`
        """
        # Check that the quality setting is set to HD or greater
        try:
            ishd = self.setting.get_int("video_quality", addon_id="script.module.youtube.dl")
        except RuntimeError:  # pragma: no cover
            ishd = True

        # Process videos
        for video_data in self.request_videos(video_ids):
            # Create listitem object
            item = Listitem()

            # Fetch Title
            item.label = video_data["title"]

            # Add channel Fanart
            item.art["fanart"] = video_data["fanart"]

            # Fetch video Image url
            item.art["thumb"] = video_data["thumb"]

            # Fetch Description
            item.info["plot"] = u"[B]%s[/B]\n\n%s" % (video_data["channel_title"], video_data["description"])

            # Fetch Studio
            item.info["studio"] = video_data["channel_title"]

            # Fetch Viewcount
            if video_data["count"]:
                item.info["count"] = video_data["count"]

            # Fetch Possible Date
            date = video_data["date"]
            item.info.date(date[:date.find(u"T")], "%Y-%m-%d")

            # Fetch Category
            item.info["genre"] = video_data["genre"]

            # Set Quality and Audio Overlays
            item.stream.hd(bool(ishd and video_data["hd"]))

            # Set duration
            item.info["duration"] = video_data["duration"]

            # Add Context item to link to related videos
            item.context.related(Related, video_id=video_data["video_id"])

            # Add Context item for youtube channel if videos from more than one channel are ben listed
            if multi_channel:
                item.context.container(Playlist, u"Go to: %s" % video_data["channel_title"],
                                       contentid=video_data["channel_id"])

            # Return the listitem
            item.set_callback(play_video, video_id=video_data["video_id"])
            yield item

    @staticmethod
    def _convert_duration(duration_match):
        """Convert youtube duration format to a format suitable for kodi."""
        duration = 0
        for time_segment, timeType in duration_match:
            if timeType == u"H":
                duration += (int(time_segment) * 3600)
            elif timeType == u"M":
                duration += (int(time_segment) * 60)
            elif timeType == u"S":  # pragma: no branch
                duration += (int(time_segment))

        return duration


@Route.register
class Playlists(APIControl):
    def run(self, channel_id, show_all=True, pagetoken=None, loop=False):
        """
        List all playlist for giving channel

        :param str channel_id: Channel id to list playlists for.
        :param bool show_all: [opt] Add link to all of the channels videos if True. (default => True)
        :param str pagetoken: [opt] The token for the next page of results.
        :param bool loop: [opt] Return all the playlist for channel. (Default => False)

        :returns: A generator of listitems.
        :rtype: :class:`types.GeneratorType`
        """
        # Make sure that we have a valid channel id
        if not channel_id.startswith("UC"):
            raise ValueError("channel_id is not valid: %s" % channel_id)

        # Fetch fanart image for channel
        fanart = self.db.cur.execute("SELECT fanart FROM channels WHERE channel_id = ?", (channel_id,)).fetchone()
        if fanart:  # pragma: no branch
            fanart = fanart[0]

        # Fetch channel playlists feed
        feed = self.api.playlists(channel_id, pagetoken, loop)

        # Add next Page entry if pagetoken is found
        if u"nextPageToken" in feed:  # pragma: no branch
            yield Listitem.next_page(channel_id=channel_id, show_all=False, pagetoken=feed[u"nextPageToken"])

        # Display a link for listing all channel videos
        # This is usefull when the root of a addon is the playlist directory
        if show_all:
            title = bold(self.localize(ALLVIDEOS))
            yield Listitem.youtube(channel_id, title, enable_playlists=False)

        # Loop Entries
        for playlist_item in feed[u"items"]:
            # Create listitem object
            item = Listitem()

            # Check if there is actualy items in the playlist before listing
            item_count = playlist_item[u"contentDetails"][u"itemCount"]
            if item_count == 0:  # pragma: no cover
                continue

            # Fetch video snippet
            snippet = playlist_item[u"snippet"]

            # Set label
            item.label = u"%s (%s)" % (snippet[u"localized"][u"title"], item_count)

            # Fetch Image Url
            item.art["thumb"] = snippet[u"thumbnails"][u"medium"][u"url"]

            # Set Fanart
            item.art["fanart"] = fanart

            # Fetch Possible Plot and Check if Available
            item.info["plot"] = snippet[u"localized"][u"description"]

            # Add InfoLabels and Data to Processed List
            item.set_callback(Playlist, contentid=playlist_item[u"id"], enable_playlists=False)
            yield item


@Route.register
class Playlist(APIControl):
    def run(self, contentid, pagetoken=None, enable_playlists=True, loop=False):
        """
        List all video within youtube playlist

        :param str contentid: Channel id or playlist id to list videos for.
        :param str pagetoken: [opt] The page token representing the next page of content.
        :param bool enable_playlists: [opt] Set to True to enable linking to channel playlists. (default => False)
        :param bool loop: [opt] Return all the videos within playlist. (Default => False)

        :returns: A generator of listitems.
        :rtype: :class:`types.GeneratorType`
        """
        # Fetch channel uploads uuid
        playlist_id = self.valid_playlistid(contentid)

        # Request data feed
        feed = self.api.playlist_items(playlist_id, pagetoken, loop)
        channel_list = set()
        video_list = []

        # Fetch video ids for all public videos
        for item in feed[u"items"]:
            if u"status" in item and item[u"status"][u"privacyStatus"] in EXCEPTED_STATUS:  # pragma: no branch
                channel_list.add(item[u"snippet"][u"channelId"])
                video_list.append(item[u"snippet"][u"resourceId"][u"videoId"])
            else:  # pragma: no cover
                logger.debug("Skipping non plublic video: '%s'", item[u"snippet"][u"resourceId"][u"videoId"])

        # Return the list of video listitems
        results = list(self.videos(video_list, multi_channel=len(channel_list) > 1))
        if u"nextPageToken" in feed:
            next_item = Listitem.next_page(contentid=contentid, pagetoken=feed[u"nextPageToken"])
            results.append(next_item)

        # Add playlists item to results
        if enable_playlists and contentid.startswith("UC") and pagetoken is None:
            item = Listitem()
            item.label = u"[B]%s[/B]" % self.localize(PLAYLISTS)
            item.info["plot"] = self.localize(PLAYLISTS_PLOT)
            item.art["icon"] = "DefaultVideoPlaylists.png"
            item.art.global_thumb("playlist.png")
            item.set_callback(Playlists, channel_id=contentid, show_all=False)
            results.append(item)

        return results


@Route.register
class Related(APIControl):
    def run(self, video_id, pagetoken=None):
        """
        Search for all videos related to a giving video id.

        :param str video_id: Id of the video the fetch related video for.
        :param str pagetoken: [opt] The page token representing the next page of content.

        :returns: A generator of listitems.
        :rtype: :class:`types.GeneratorType`
        """
        self.category = "Related"
        self.update_listing = bool(pagetoken)
        feed = self.api.search(pageToken=pagetoken, relatedToVideoId=video_id)
        video_list = [item[u"id"][u"videoId"] for item in feed[u"items"]]  # pragma: no branch

        # List all the related videos
        results = list(self.videos(video_list, multi_channel=True))
        if u"nextPageToken" in feed:  # pragma: no branch
            next_item = Listitem.next_page(video_id=video_id, pagetoken=feed[u"nextPageToken"])
            results.append(next_item)
        return results


@Resolver.register
def play_video(plugin, video_id):
    """
    :type  plugin: :class:`codequick.PlayMedia`
    :type video_id: str
    """
    url = u"https://www.youtube.com/watch?v={}".format(video_id)
    return plugin.extract_source(url)
