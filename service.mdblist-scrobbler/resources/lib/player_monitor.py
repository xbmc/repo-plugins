import time
import urllib.parse

import requests
import xbmc
import xbmcaddon
import xbmcgui

from resources.lib import oauth, ratings_sync, sync_orchestrator
from resources.lib.mdblist_api import MDBListApiError
from resources.lib.timer import Timer
from resources.lib.utils import jsonrpc_request, fix_unique_ids


REQUEST_TIMEOUT_SECONDS = 5
REQUEST_RETRY_ATTEMPTS = 2
REQUEST_RETRY_BACKOFF_SECONDS = 1
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}
DEFAULT_BASE_URL = "https://api.mdblist.com"


class PlayerMonitor(xbmc.Player):
    def __init__(self):
        super().__init__()

        self.settings = None
        self.interval_timer = None

        self.total_time = None
        self.current_time = None

        self.video_info = {}
        self.rating_prompt_shown = False

        self.load_settings()

    def show_message(self, message: str):
        jsonrpc_request("GUI.ShowNotification", {"title": "MDBList Scrobbler", "message": message})

    def load_settings(self):
        self.settings = xbmcaddon.Addon().getSettings()

    def get_string_setting(self, setting_id: str, default: str = ""):
        try:
            return self.settings.getString(setting_id) or default
        except Exception as exception:
            xbmc.log(
                "MDBList Scrobbler: String setting '{}' unavailable, using default - {}".format(
                    setting_id, exception
                ),
                level=xbmc.LOGDEBUG,
            )
            return default

    def get_bool_setting(self, setting_id: str, default: bool = False):
        try:
            return self.settings.getBool(setting_id)
        except Exception as exception:
            xbmc.log(
                "MDBList Scrobbler: Boolean setting '{}' unavailable, using default={} - {}".format(
                    setting_id, default, exception
                ),
                level=xbmc.LOGDEBUG,
            )
            return default

    def get_int_setting(self, setting_id: str, default: int = 0):
        try:
            return self.settings.getInt(setting_id)
        except Exception as exception:
            xbmc.log(
                "MDBList Scrobbler: Integer setting '{}' unavailable, using default={} - {}".format(
                    setting_id, default, exception
                ),
                level=xbmc.LOGDEBUG,
            )
            return default

    def build_payload(self, event: str, use_cached_time: bool = False):
        if not self.video_info:
            return None

        media_type = self.video_info.get("type")

        if media_type not in ("movie", "episode"):
            xbmc.log(
                "MDBList Scrobbler: Skipping item with unsupported media type '{}' title='{}' uniqueid={}".format(
                    media_type, self.display_title(), self.video_info.get("uniqueid", {})
                ),
                level=xbmc.LOGDEBUG,
            )
            return None

        if not self.get_bool_setting("mediatype.{}".format(media_type), True):
            xbmc.log("MDBList Scrobbler: Scrobbling disabled for media type '{}'".format(media_type), level=xbmc.LOGDEBUG)
            return None

        if use_cached_time:
            total_time = self.total_time
            current_time = self.current_time
        else:
            total_time = self.getTotalTime() if self.isPlaying() else self.total_time
            current_time = self.getTime() if self.isPlaying() else self.current_time

        if total_time is not None:
            if total_time < 0:
                total_time = 0
            else:
                total_time = int(total_time)

        if current_time is not None:
            if current_time < 0:
                current_time = 0
            else:
                current_time = int(current_time)

        if total_time and current_time is not None:
            progress_percent = round((current_time / total_time) * 100, 2)
        else:
            xbmc.log(
                "MDBList Scrobbler: Skipping {} event due to missing/invalid playback time (total={}, current={})".format(
                    event, total_time, current_time
                ),
                level=xbmc.LOGDEBUG,
            )
            return None

        if media_type == "episode":
            show_ids = fix_unique_ids(self.video_info.get("tvshow", {}).get("uniqueid", {}), media_type)
            if not show_ids:
                show_ids = fix_unique_ids(self.video_info.get("uniqueid", {}), media_type)
            if not show_ids:
                xbmc.log("MDBList Scrobbler: Skipping episode scrobble, no supported show IDs found", level=xbmc.LOGWARNING)
                return None

            return {
                "show": {
                    "ids": show_ids,
                    "season": {
                        "number": self.video_info.get("season"),
                        "episode": {
                            "number": self.video_info.get("episode")
                        }
                    }
                },
                "progress": progress_percent,
                "app_version": xbmcaddon.Addon().getAddonInfo("version")
            }

        if media_type == "movie":
            movie_ids = fix_unique_ids(self.video_info.get("uniqueid", {}), media_type)
            if not movie_ids:
                xbmc.log("MDBList Scrobbler: Skipping movie scrobble, no supported movie IDs found", level=xbmc.LOGWARNING)
                return None

            return {
                "movie": {
                    "ids": movie_ids
                },
                "progress": progress_percent,
                "app_version": xbmcaddon.Addon().getAddonInfo("version")
            }

        return None

    def send_request(self, event: str, use_cached_time: bool = False):
        if not self.get_bool_setting("event.{}".format(event), True):
            xbmc.log("MDBList Scrobbler: Event '{}' disabled in settings, skipping".format(event), level=xbmc.LOGDEBUG)
            return

        json_data = self.build_payload(event, use_cached_time=use_cached_time)
        if not json_data:
            return

        access_token = oauth.ensure_valid_token()
        apikey = "" if access_token else self.get_string_setting("apikey")

        if not access_token and not apikey:
            xbmc.log("MDBList Scrobbler: Not authenticated (no OAuth token or API key configured)", level=xbmc.LOGERROR)
            self.show_message("Not authenticated. Open addon settings to connect.")
            return

        endpoint = self.event_to_endpoint(event)
        if not endpoint:
            return

        if access_token:
            url = "{}{}".format(DEFAULT_BASE_URL, endpoint)
            headers = {"Authorization": "Bearer {}".format(access_token)}
        else:
            url = "{}{}?apikey={}".format(DEFAULT_BASE_URL, endpoint, apikey)
            headers = None

        response = self.post_scrobble_request(event, endpoint, url, json_data, headers)
        if response is None:
            return

        if response.status_code >= 400:
            response_snippet = response.text[:200]
            xbmc.log(
                "MDBList Scrobbler: API error {} on {} payload={} response={}".format(
                    response.status_code, endpoint, json_data, response_snippet
                ),
                level=xbmc.LOGERROR,
            )
            return

        xbmc.log("MDBList Scrobbler: Scrobbled '{}' to {} ({})".format(event, endpoint, response.status_code), level=xbmc.LOGDEBUG)

    def post_scrobble_request(self, event: str, endpoint: str, url: str, json_data: dict, headers):
        for attempt in range(1, REQUEST_RETRY_ATTEMPTS + 1):
            try:
                response = requests.post(url, json=json_data, headers=headers, timeout=REQUEST_TIMEOUT_SECONDS)
            except requests.exceptions.RequestException as exception:
                if attempt < REQUEST_RETRY_ATTEMPTS:
                    xbmc.log(
                        "MDBList Scrobbler: Request failed on attempt {}/{} for '{}' - {}".format(
                            attempt, REQUEST_RETRY_ATTEMPTS, event, str(exception)
                        ),
                        level=xbmc.LOGWARNING,
                    )
                    time.sleep(REQUEST_RETRY_BACKOFF_SECONDS * attempt)
                    continue

                xbmc.log(
                    "MDBList Scrobbler: Request failed after {} attempts for '{}' - {}".format(
                        REQUEST_RETRY_ATTEMPTS, event, str(exception)
                    ),
                    level=xbmc.LOGWARNING,
                )
                return None
            except Exception as exception:
                xbmc.log(
                    "MDBList Scrobbler: Unexpected failure for '{}' - {}".format(event, str(exception)),
                    level=xbmc.LOGERROR,
                )
                return None

            if response.status_code in RETRYABLE_STATUS_CODES and attempt < REQUEST_RETRY_ATTEMPTS:
                xbmc.log(
                    "MDBList Scrobbler: Retryable API error {} on {} attempt {}/{}".format(
                        response.status_code, endpoint, attempt, REQUEST_RETRY_ATTEMPTS
                    ),
                    level=xbmc.LOGWARNING,
                )
                time.sleep(REQUEST_RETRY_BACKOFF_SECONDS * attempt)
                continue

            return response

        return None

    def event_to_endpoint(self, event: str):
        if event in ["start", "resume", "seek", "interval"]:
            return "/scrobble/start"
        if event == "pause":
            return "/scrobble/pause"
        if event in ["stop", "end"]:
            return "/scrobble/stop"
        return None

    def infer_media_type(self, item: dict):
        media_type = item.get("type")
        if media_type in ("movie", "episode"):
            return media_type

        season = item.get("season")
        episode = item.get("episode")
        if season not in (None, -1, "") or episode not in (None, -1, ""):
            return "episode"

        if item.get("showtitle") or item.get("firstaired") or item.get("tvshowid") not in (None, -1, ""):
            return "episode"

        if item.get("title") and (item.get("premiered") or item.get("year") or item.get("uniqueid")):
            return "movie"

        return media_type

    def apply_tmdb_helper_fallback(self):
        if not self.video_info:
            return

        file_path = self.video_info.get("file") or ""
        if not file_path.startswith("plugin://plugin.video.themoviedb.helper/"):
            return

        query = urllib.parse.urlsplit(file_path).query
        params = {key: values[-1] for key, values in urllib.parse.parse_qs(query).items() if values}

        tmdb_type = params.get("tmdb_type")
        tmdb_id = params.get("tmdb_id")
        if not tmdb_id:
            return

        if tmdb_type == "movie":
            self.video_info["type"] = "movie"
            self.video_info["uniqueid"] = {"tmdb": tmdb_id}
            return

        if tmdb_type != "tv":
            return

        season = params.get("season")
        episode = params.get("episode")
        if not season or not episode:
            return

        self.video_info["type"] = "episode"
        self.video_info["season"] = int(season) if season.isdigit() else season
        self.video_info["episode"] = int(episode) if episode.isdigit() else episode
        self.video_info["tvshow"] = {"uniqueid": {"tmdb": tmdb_id}}

    def display_title(self):
        if not self.video_info:
            return ""

        return (
            self.video_info.get("title")
            or self.video_info.get("showtitle")
            or self.video_info.get("label")
            or ""
        )

    def fetch_video_info(self):
        try:
            self.video_info = jsonrpc_request(
                "Player.GetItem",
                {
                    "playerid": 1,
                    "properties": [
                        "title",
                        "tvshowid",
                        "showtitle",
                        "season",
                        "episode",
                        "firstaired",
                        "premiered",
                        "year",
                        "uniqueid",
                        "file",
                    ],
                },
            ).get("item")
        except Exception as e:
            xbmc.log("MDBList Scrobbler: fetch_video_info failed - {}".format(e), level=xbmc.LOGERROR)
            self.video_info = None

        if not self.video_info:
            xbmc.log("MDBList Scrobbler: No video info available, scrobbling disabled for this item", level=xbmc.LOGDEBUG)
            return

        self.apply_tmdb_helper_fallback()

        media_type = self.video_info.get("type")
        inferred_media_type = self.infer_media_type(self.video_info)
        if inferred_media_type != media_type:
            xbmc.log(
                "MDBList Scrobbler: Inferred item type '{}' from Kodi type '{}'".format(
                    inferred_media_type, media_type
                ),
                level=xbmc.LOGDEBUG,
            )
            self.video_info["type"] = inferred_media_type
            media_type = inferred_media_type

        item_id = self.video_info.get("id")
        uniqueid = self.video_info.get("uniqueid", {})
        xbmc.log(
            "MDBList Scrobbler: Detected item type={} id={} uniqueid={} title={}".format(
                media_type, item_id, uniqueid, self.display_title()
            ),
            level=xbmc.LOGDEBUG,
        )

        if media_type == "episode":
            tvshowid = self.video_info.get("tvshowid")
            if tvshowid and tvshowid != -1:
                try:
                    tvshow = jsonrpc_request("VideoLibrary.GetTVShowDetails", {"tvshowid": tvshowid, "properties": ["uniqueid"]}).get("tvshowdetails")
                    self.video_info["tvshow"] = tvshow or {}
                    xbmc.log("MDBList Scrobbler: tvshow uniqueid={}".format(self.video_info["tvshow"].get("uniqueid", {})), level=xbmc.LOGDEBUG)
                except Exception as e:
                    xbmc.log("MDBList Scrobbler: Failed to fetch tvshow details - {}".format(e), level=xbmc.LOGWARNING)
                    self.video_info["tvshow"] = {}
            else:
                xbmc.log("MDBList Scrobbler: tvshowid={}, skipping library lookup, will use existing IDs".format(tvshowid), level=xbmc.LOGDEBUG)
                if not self.video_info.get("tvshow"):
                    self.video_info["tvshow"] = {}

    def start_interval_timer(self):
        self.interval_timer = Timer(self.get_int_setting("interval", 10), self.onInterval)
        self.interval_timer.start()

    def stop_interval_timer(self):
        if not self.interval_timer or not self.interval_timer.is_alive():
            return

        self.interval_timer.stop()

    def update_time(self):
        if self.isPlaying():
            self.total_time = self.getTotalTime()
            self.current_time = self.getTime()

    def reset_playback_state(self):
        self.total_time = None
        self.current_time = None
        self.video_info = {}
        self.rating_prompt_shown = False

    def get_progress_percent(self):
        if not self.total_time or self.current_time is None:
            return None

        if self.total_time <= 0:
            return None

        current_time = min(max(int(self.current_time), 0), int(self.total_time))

        return round((current_time / int(self.total_time)) * 100, 2)

    def finalize_previous_playback_on_transition(self):
        if not self.video_info:
            return

        self.stop_interval_timer()
        progress_percent = self.get_progress_percent()
        if progress_percent is None or progress_percent <= 0:
            xbmc.log(
                "MDBList Scrobbler: Previous playback state found before new playback, but cached progress is unavailable or zero",
                level=xbmc.LOGDEBUG,
            )
            return

        xbmc.log(
            "MDBList Scrobbler: Finalizing previous playback before new playback starts (progress={})".format(
                progress_percent
            ),
            level=xbmc.LOGDEBUG,
        )
        self.send_request("stop", use_cached_time=True)
        self.prompt_for_rating("stop")
        self.video_info = {}

    def should_prompt_for_rating(self, playback_event: str):
        if self.rating_prompt_shown or not self.video_info:
            return False

        if not self.get_bool_setting("rating.prompt.enabled", False):
            return False

        if playback_event == "end":
            if not self.get_bool_setting("rating.prompt.on_end", True):
                return False
        elif playback_event == "stop":
            if not self.get_bool_setting("rating.prompt.on_stop", True):
                return False
        else:
            return False

        media_type = self.video_info.get("type")
        if media_type == "movie":
            if not self.get_bool_setting("rating.prompt.movie", True):
                return False
            library_id = self.video_info.get("id")
        elif media_type == "episode":
            if not self.get_bool_setting("rating.prompt.episode", True):
                return False
            library_id = self.video_info.get("id")
        else:
            return False

        if library_id in (None, -1):
            if not self.get_bool_setting("sync.ratings.enabled", False):
                xbmc.log("MDBList Scrobbler: Skipping rating prompt, item is not in Kodi library and ratings sync is disabled", level=xbmc.LOGDEBUG)
                return False
            xbmc.log("MDBList Scrobbler: Item not in Kodi library, Kodi rating will be skipped but MDBList rating can proceed", level=xbmc.LOGDEBUG)

        if library_id not in (None, -1) and self.get_bool_setting("rating.prompt.unrated_only", True):
            media_type = self.video_info.get("type")
            try:
                if media_type == "movie":
                    details = jsonrpc_request("VideoLibrary.GetMovieDetails", {"movieid": library_id, "properties": ["userrating"]}).get("moviedetails", {})
                elif media_type == "episode":
                    details = jsonrpc_request("VideoLibrary.GetEpisodeDetails", {"episodeid": library_id, "properties": ["userrating"]}).get("episodedetails", {})
                else:
                    details = {}
                if int(details.get("userrating", 0) or 0) > 0:
                    return False
            except Exception as e:
                xbmc.log("MDBList Scrobbler: Failed to fetch userrating - {}".format(e), level=xbmc.LOGWARNING)

        progress_percent = self.get_progress_percent()
        if progress_percent is None:
            progress_percent = 100.0

        return progress_percent >= float(self.get_int_setting("rating.prompt.progress", 90))

    def save_kodi_rating(self, rating: int):
        if not self.get_bool_setting("rating.save.kodi", True):
            return False

        media_type = self.video_info.get("type")
        library_id = self.video_info.get("id")

        if library_id in (None, -1):
            xbmc.log("MDBList Scrobbler: Skipping Kodi rating save, item is not in Kodi library", level=xbmc.LOGDEBUG)
            return False

        if media_type == "movie":
            method = "VideoLibrary.SetMovieDetails"
            params = {"movieid": library_id, "userrating": rating}
        elif media_type == "episode":
            method = "VideoLibrary.SetEpisodeDetails"
            params = {"episodeid": library_id, "userrating": rating}
        else:
            return False

        try:
            jsonrpc_request(method, params)
            self.video_info["userrating"] = rating
            return True
        except Exception as exception:
            xbmc.log("MDBList Scrobbler: Failed to save Kodi rating - {}".format(str(exception)), level=xbmc.LOGERROR)
            return False

    def save_mdblist_rating(self, rating: int):
        if not self.get_bool_setting("sync.ratings.enabled", False):
            return False

        media_type = self.video_info.get("type")

        if media_type == "movie":
            movie_ids = fix_unique_ids(self.video_info.get("uniqueid", {}), "movie")
            if not movie_ids:
                xbmc.log("MDBList Scrobbler: Cannot rate movie on MDBList, no supported IDs", level=xbmc.LOGWARNING)
                return False
            record = {"dbtype": "movie", "ids": movie_ids, "userrating": rating}
        elif media_type == "episode":
            show_ids = fix_unique_ids(self.video_info.get("tvshow", {}).get("uniqueid", {}), "episode")
            if not show_ids:
                show_ids = fix_unique_ids(self.video_info.get("uniqueid", {}), "episode")
            if not show_ids:
                xbmc.log("MDBList Scrobbler: Cannot rate episode on MDBList, no supported show IDs", level=xbmc.LOGWARNING)
                return False
            record = {
                "dbtype": "episode", "show_ids": show_ids,
                "season": self.video_info.get("season"), "episode": self.video_info.get("episode"),
                "userrating": rating,
            }
        else:
            return False

        with sync_orchestrator.try_lock() as acquired:
            if not acquired:
                # A sync is in progress -- skip rather than race it. The
                # rating still reaches MDBList via the next periodic push()
                # backfill diff, so this isn't lost, just deferred.
                return False
            try:
                result = ratings_sync.push_single(record)
                return result is not False
            except MDBListApiError as exception:
                xbmc.log("MDBList Scrobbler: MDBList rating request failed - {}".format(str(exception)), level=xbmc.LOGERROR)
                return False

    def prompt_for_rating(self, playback_event: str):
        if not self.should_prompt_for_rating(playback_event):
            return

        heading = "Rate {}".format(self.video_info.get("title") or self.video_info.get("showtitle") or "item")
        choices = ["Skip"] + ["{}".format(value) for value in range(1, 11)]
        selection = xbmcgui.Dialog().select(heading, choices)

        self.rating_prompt_shown = True

        if selection <= 0:
            return

        rating = selection
        saved = []
        if self.save_kodi_rating(rating):
            saved.append("Kodi")
        if self.save_mdblist_rating(rating):
            saved.append("MDBList")
        if saved:
            self.show_message("Saved {}/10 to {}".format(rating, " & ".join(saved)))

    def onAVStarted(self):
        xbmc.log("MDBList Scrobbler: onAVStarted", level=xbmc.LOGDEBUG)
        self.load_settings()
        self.finalize_previous_playback_on_transition()
        self.reset_playback_state()
        self.fetch_video_info()
        self.update_time()

        self.send_request("start")
        self.start_interval_timer()

    def onPlayBackPaused(self):
        if not self.video_info:
            return

        self.update_time()
        self.send_request("pause")
        self.stop_interval_timer()

    def onPlayBackResumed(self):
        if not self.video_info:
            return

        self.send_request("resume")
        self.start_interval_timer()

    def onPlayBackStopped(self):
        xbmc.log("MDBList Scrobbler: onPlayBackStopped (video_info present={})".format(bool(self.video_info)), level=xbmc.LOGDEBUG)
        if not self.video_info:
            return

        self.update_time()
        self.send_request("stop")
        self.stop_interval_timer()
        self.prompt_for_rating("stop")
        self.video_info = {}

    def onPlayBackEnded(self):
        xbmc.log("MDBList Scrobbler: onPlayBackEnded (video_info present={})".format(bool(self.video_info)), level=xbmc.LOGDEBUG)
        if not self.video_info:
            return

        self.update_time()
        self.send_request("end")
        self.stop_interval_timer()
        self.prompt_for_rating("end")
        self.video_info = {}

    def onPlayBackSeek(self, time: int, seekOffset: int):
        if not self.video_info:
            return

        self.update_time()
        self.send_request("seek")

    def onPlayBackSeekChapter(self, chapter: int):
        if not self.video_info:
            return

        self.update_time()
        self.send_request("seek")

    def onInterval(self):
        if not self.video_info:
            return

        self.update_time()
        self.send_request("interval")
