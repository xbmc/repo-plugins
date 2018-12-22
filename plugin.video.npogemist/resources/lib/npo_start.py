# -*- coding: utf-8 -*-
"""A Kodi plugin for watching NPO, using the new npo-start API."""
import datetime
import re
import time
import calendar
import urllib

from . import start_api_retriever

from resources.lib.errors import NPOContentError

DEBUG = False
SUPPORTED_CHANNELS = ["NED1", "NED2", "NED3"]


class NPO:
    def __init__(self):
        pass

    def get_duration(self, fr, to):
        """Get all broadcasts with a duration between fr and to seconds."""
        for broadcast in self._get_broadcasts_days_ago(7):
            if not self._is_rerun(broadcast):
                duration = int(broadcast["program"]["duration"]) if broadcast["program"]["duration"] is not None else 0
                if self._is_started(broadcast["startsAt"]):
                    if fr < duration and (to is None or duration <= to):
                        yield self._broadcast2item(broadcast)

    def _get_broadcasts_days_ago(self, days_ago):
        """Get all broadcasts from last days. Used to find things."""
        # "When in doubt, use brute force." -- Dennis Ritchie
        for days_ago in range(0, days_ago):
            date = datetime.datetime.today() - datetime.timedelta(days=days_ago)
            npo_date = self._npo_date(date)
            epg = start_api_retriever.retrieve_epg_by_date(npo_date)
            for channel_schedule in epg["epg"]:
                if channel_schedule["channel"]["channel"] in SUPPORTED_CHANNELS:
                    for broadcast in channel_schedule["schedule"]:
                        # rule out 24-hour channels
                        if broadcast["startsAt"] is not None and broadcast["program"] is not None:
                            yield broadcast

    def get_recents(self):
        """Get recent broadcasts."""
        for broadcast in self._get_broadcasts_days_ago(2):
            if self._is_recent(broadcast["startsAt"]) and self._is_started(broadcast["startsAt"]):
                yield self._broadcast2item(broadcast)

    def _broadcast2item(self, broadcast):
        """Convert a single broadcast into an item."""
        item = {
            "label": self._broadcast_label(broadcast),
            "thumb": self._broadcast_thumb(broadcast),
            "fanart": self._broadcast_fanart(broadcast),
            "mid": broadcast["program"]["id"],
            "genre": self._genre_string(broadcast["program"]["genres"]),
            "plot": broadcast["program"]["descriptionLong"],
            "tagline": broadcast["program"]["description"],
            "aired": time.mktime(self._json2datetime(broadcast["startsAt"]).timetuple()),
            "duration": int(broadcast["program"]["duration"]) if broadcast["program"]["duration"] is not None else 0,
            "rerun": self._is_rerun(broadcast),
            "is_video": True,
        }
        item["future"] = (item.get("aired", 0) + item.get("duration", 0) > time.time())
        return item

    def _is_rerun(self, broadcast):
        """Return True if this is a re-run. Useful in searches and such."""
        starts_at = self._json2datetime(broadcast["startsAt"])
        broadcast_date = starts_at  # Ssume no re-run
        if broadcast["program"]["broadcastDate"] is not None:
            broadcast_date = self._json2datetime(broadcast["program"]["broadcastDate"])
        return (starts_at != broadcast_date)

    def _is_started(self, starts_at):
        """Return True if we can try to play this item now.

        We ignore availability for epg items, as NPO Start is known to lie.
        """
        now = datetime.datetime.now()
        return (now > self._json2datetime(starts_at))

    def _is_recent(self, starts_at):
        """Return True if an item is less than a day old ."""
        now = datetime.datetime.now()
        diff = now - self._json2datetime(starts_at)
        return diff.days == 0

    def _is_not_expired(self, availability):
        """Return True if this program hasn't expired, i.e. it is or will be available."""
        # If you get it from EPG it is not always correct, so don't use it then.
        now = datetime.datetime.now()
        fr, to = self._availability(availability, now)
        return (now <= to)  # not expired

    def _availability(self, availability, now):
        """Helper method to determine the availability period when parts are missing."""
        fr = now
        froms = availability["from"]
        if froms is not None:
            fr = self._json2datetime(froms)
        to = now
        tos = availability["to"]
        if tos is not None:
            to = self._json2datetime(tos)
        return fr, to

    def _genre_string(self, genres):
        """Convert a genre list to a comma separated string."""
        # Keep sort order.
        genrelist = []
        for genre_obj in genres:
            for genre in genre_obj["terms"]:
                if genre not in genrelist:
                    genrelist.append(genre)
        return ", ".join(genrelist)

    def _broadcast_thumb(self, broadcast):
        """Get a picture for the broadcast."""
        for format in ["original", "tv"]:
            try:
                image = broadcast["program"]["images"]["original"]["formats"][format]["source"]
                if image is not None and image != "":
                    return image
            except (KeyError, TypeError):
                pass
            return None

    def _broadcast_fanart(self, broadcast):
        """Get a picture for the series of this broadcast.

        This is not cheap, so we use the same picture as the thumb."""
        return self._broadcast_thumb(broadcast)

    def _json2datetime(self, jsondate):
        """Convert a JSON date to a datetime object, keeping UTC in mind."""
        # Crazy workaround see https://bugs.python.org/issue27400
        try:
            utc_dt = datetime.datetime.strptime(jsondate, '%Y-%m-%dT%H:%M:%SZ')
        except TypeError:
            utc_dt = datetime.datetime.fromtimestamp(time.mktime(time.strptime(jsondate, '%Y-%m-%dT%H:%M:%SZ')))
        timestamp = calendar.timegm(utc_dt.timetuple())
        local_dt = datetime.datetime.fromtimestamp(timestamp)
        return local_dt

    def _broadcast_label(self, broadcast):
        """Make a nice name for the broadcast."""
        program = None
        try:
            program = broadcast["program"]["franchiseTitle"]
        except (KeyError, TypeError):
            pass
        episode = None
        try:
            episode = broadcast["program"]["title"]
        except (KeyError, TypeError):
            pass
        return self._make_fullname(program, episode)

    def _make_fullname(self, program, episode):
        """Combine series and episode name in a nice way."""
        # if either is empty, return the other.
        if program is None or program == "":
            return episode
        if episode is None or episode == "":
            return program
        # If episode starts with program, drop program.
        if re.search(program, episode, re.IGNORECASE):
            return episode
        # Combine program and episode. Put : in between
        if program[-1].isalnum():
            divider = ": "
        else:
            # If program ends in funny char, just use a space.
            divider = " "
        return program + divider + episode

    def get_guide_channels(self, date):
        """Get a list of channels."""
        npo_date = self._npo_date(date)
        epg = start_api_retriever.retrieve_epg_by_date(npo_date)
        return self._guide2channels(epg)

    def _guide2channels(self, epg):
        """Create channel items from the epg."""
        npo_channels = []
        for channel_schedule in epg["epg"]:
            channel_info = channel_schedule["channel"]
            if channel_info["channel"] in SUPPORTED_CHANNELS:
                npo_channels.append({
                    'label': channel_info["name"],
                    'plot': channel_info["name"],
                    'thumb': channel_info["images"]["original"]["formats"]["tv"]["source"],
                    'channel': channel_info["channel"]
                })
        return sorted(npo_channels, key=lambda c: (len(c["label"]), c["label"]))

    def _npo_date(self, date):
        """Convert a date to the NPO supported format."""
        return date.strftime('%Y-%m-%d')

    def get_channel_guide(self, channel, datestamp):
        """Get the program guide for a date and a channel."""
        date = datetime.datetime.fromtimestamp(float(datestamp))
        npo_date = self._npo_date(date)
        epg = start_api_retriever.retrieve_epg_by_date(npo_date)
        for channel_schedule in epg["epg"]:
            if channel_schedule["channel"]["channel"] in SUPPORTED_CHANNELS and \
                    (channel_schedule["channel"]["channel"] == channel or channel == "all"):
                for broadcast in channel_schedule["schedule"]:
                    # rule out 24-hour channels and other non-playable items.
                    if broadcast["startsAt"] is not None and broadcast["program"] is not None:
                        yield self._broadcast2item(broadcast)

    def get_letters(self):
        """Get filter values for programs by alphabet."""
        catalogue = start_api_retriever.retrieve_filters()
        for component in catalogue["components"]:
            if component["type"] == "filter":
                return self._filters2letters(component["filters"])

    def _filters2letters(self, filters):
        """Convert filter options to letter tuples."""
        letters = []
        for filter in filters:
            if filter["filterArgument"] == "az":
                for option in filter["options"]:
                    if option["value"] is not None:  # suppress all, it's too much anyway
                        letters.append((option["display"], option["value"]))
        return letters

    def get_series(self, letter):
        """Get series starting with letter."""
        catalogue = start_api_retriever.retrieve_series(letter)
        series = self._get_catalogue_series(catalogue)
        if series is not None:
            for serie in series:
                if self._is_series(serie):
                    yield self._serie2item(serie)

    def _get_catalogue_series(self, catalogue):
        """Get the series from the catalogue."""
        for component in catalogue["components"]:
            if component["type"] == "grid":
                return component["data"]["items"]
        return None

    def _is_series(self, serie):
        """Return True if an item is a series."""
        return serie["type"] == "series"

    def get_series_by_ids(self, ids):
        """Get all series with id in ids. Skip if they ceased to exist."""
        for id in ids:
            try:
                franchise = start_api_retriever.retrieve_series_by_id(id)
            except NPOContentError:
                pass
            else:
                series_header = self._get_franchise_header(franchise)
                if series_header is not None:
                    yield self._serie2item(series_header["series"])

    def _get_franchise_header(self, franchise):
        """Get the component called 'franchiseheader' from the franchise."""
        for component in franchise["components"]:
            if component["type"] == "franchiseheader":
                return component
        return None

    def get_serie_id_by_episode(self, episode_code):
        """Get the series id for this episode."""
        episode = start_api_retriever.retrieve_episode_by_id(episode_code)
        episode_header = self._get_episode_header(episode)
        if episode_header is not None:
            series = episode_header["series"]
            if series is not None:
                return series["id"]
        return None

    def _get_episode_header(self, episode):
        """Get the component called 'episodeheader' from the episode."""
        for component in episode["components"]:
            if component["type"] == "episodeheader":
                return component
        return None

    def _serie2item(self, serie):
        """Convert a series to an item."""
        item = {
            "mid": serie["id"],
            "label": serie["title"],
            "thumb": self._series_thumb(serie),
            "fanart": self._series_fanart(serie),
            "tagline": serie["title"],
            "is_video": False,
        }
        if "genres" in serie:
            item["genre"] = self._genre_string(serie["genres"])
        if "description" in serie:
            item["plot"] = serie["description"]
        if DEBUG:
            item["label"] += " [" + serie["type"] + "]"
        return item

    def _series_thumb(self, serie):
        """Get a picture for the series."""
        return self._series_image(None, serie)

    def _series_fanart(self, serie):
        """Get a background picture for the series."""
        return self._series_thumb(serie)

    def get_episodes(self, series_code):
        """Get all episodes for this series."""
        franchise = start_api_retriever.retrieve_series_by_id(series_code)
        series_header = self._get_franchise_header(franchise)
        series = None
        if series_header is not None:
            series = series_header["series"]
        episodes = self._get_franchise_episodes(franchise)
        if episodes is not None:
            for episode in episodes:
                if self._is_not_expired(episode["availability"]):
                    yield self._episode2item(episode, series)

    def _get_franchise_episodes(self, franchise):
        """Get the episodes from the franchise."""
        for component in franchise["components"]:
            if component["id"] == "grid-episodes":
                return component["data"]["items"]
        return None

    def get_episode_by_id(self, episode_code):
        """Get an episode by id."""
        episode = start_api_retriever.retrieve_episode_by_id(episode_code)
        return self._episode2item(episode, episode["series"])

    def _episode2item(self, episode, serie=None):
        """Convert an episode to an item.

        We can do some things nicer because we may have a series, too. Otherwise it is
        similar to a broadcast.
        """
        label = episode["episodeTitle"]
        if serie is not None:
            label = self._make_fullname(serie["title"], episode["episodeTitle"])
        item = {
            "label": label,
            "mid": episode["id"],
            "thumb": self._episode_thumb(episode, serie),
            "fanart": self._episode_fanart(episode, serie),
            "genre": self._genre_string(episode["genres"]),
            "plot": episode["descriptionLong"],
            "tagline": episode["description"],
            "aired": time.mktime(self._json2datetime(episode["broadcastDate"]).timetuple()),
            "duration": int(episode["duration"]) if episode["duration"] is not None else 0,
            "rerun": False,
            "is_video": True,
        }
        item["future"] = (item.get("aired", 0) + item.get("duration", 0) > time.time())
        if serie is not None:
            item["seriesid"] = serie["id"]
        if DEBUG:
            label += " [" + episode["type"] + "]"
        return item

    def _episode_thumb(self, episode, serie):
        """Get an image for this episode, or from the series if not available."""
        return self._get_image(episode, serie, self._episode_image, self._series_image)

    def _episode_fanart(self, episode, serie):
        """Get a series image for this episode, or from the episode itself if not available."""
        return self._get_image(episode, serie, self._series_image, self._episode_image)

    def _get_image(self, episode, serie, *image_functions):
        """Try to get an image using imagefunctions, in the order given."""
        for image_function in image_functions:
            thumb = image_function(episode, serie)
            if thumb is not None:
                return thumb
        return ""

    def _episode_image(self, episode, serie):
        """Get the episode image."""
        for format in ["original", "tv"]:
            try:
                image = episode["images"]["original"]["formats"][format]["source"]
                if image is not None and image != "":
                    return image
            except (KeyError, TypeError):
                pass
        return None

    def _series_image(self, episode, serie):
        """Get the series' image."""
        for format in ["original", "tv"]:
            try:
                image = serie["images"]["original"]["formats"][format]["source"]
                if image is not None and image != "":
                    return image
            except (KeyError, TypeError):
                pass
        return None

    def get_genres(self):
        """Get a list of genres by detecting them from a lot of series."""
        genres = []
        catalogue = start_api_retriever.retrieve_series_random()
        series = self._get_catalogue_series(catalogue)
        if series is not None:
            for serie in series:
                if "genres" in serie:
                    for genre in serie["genres"]:
                        genres.extend(genre["terms"])
        return sorted(set(genres))

    def get_series_by_genre(self, genre):
        """Get series by genre."""
        catalogue = start_api_retriever.retrieve_series_genre(genre)
        for component in catalogue["components"]:
            if component["type"] == "grid":
                for serie in component["data"]["items"]:
                    if self._is_series(serie):
                        yield self._serie2item(serie)

    def get_search(self, search):
        """get series and broadcasts by searching."""
        # NPO doesn't like "/", even when encoded.
        search_name = urllib.quote(search.replace("/", " "))
        result = start_api_retriever.retrieve_items_by_search(search_name)
        for item in result["items"]:
            if self._is_series(item):
                yield self._serie2item(item)
            elif self._is_episode(item):
                if self._is_not_expired(item["availability"]):
                    yield self._episode2item(item)

    def _is_episode(self, item):
        """Return True if item is an episode."""
        return item["type"] == "broadcast"

    def get_subtitles_url(self, mid):
        """Return a url for subtitles for this id."""
        return "https://rs.poms.omroep.nl/v1/api/subtitles/{0}/nl_NL/CAPTION.vtt".format(mid)

    def get_play_url(self, mid):
        """Return a video url for this id."""
        videodata = start_api_retriever.retrieve_video_data(mid)
        return videodata['url']

