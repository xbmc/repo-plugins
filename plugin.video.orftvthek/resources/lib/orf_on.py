import json
import re
from datetime import date, datetime, timedelta

from urllib.request import Request as urllib_Request
from urllib.request import urlopen as urllib_urlopen
from urllib.error import HTTPError as urllib_HTTPError
from urllib.error import URLError as urllib_URLError
from urllib.parse import quote_plus

from directory import Directory


class OrfOn:
    useragent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36'
    api_auth = 'Basic b3JmX29uX3Y0MzpqRlJzYk5QRmlQU3h1d25MYllEZkNMVU41WU5aMjhtdA=='
    api_version = '4.3'
    api_pager_limit = 50
    geo_lock_url = 'https://apasfiis.sf.apa.at/admin/proxycheck/'
    api_base = 'https://api-tvthek.orf.at/api/v%s' % api_version

    api_endpoint_settings = '/settings'
    api_endpoint_home = '/page/start'
    api_endpoint_recently_added = '/page/startpage/newest'
    api_endpoint_schedule = '/schedule/%s'
    api_endpoint_shows = '/profiles?limit=%d'
    api_endpoint_shows_letter = '/profiles/lettergroup/%s'
    api_endpoint_history = '/history'
    api_endpoint_search = '/search/%s'
    api_endpoint_search_partial = '/search-partial/%s/%s?limit=%d'
    api_endpoint_livestreams = '/livestreams'
    api_endpoint_livestream = '/livestream/%s'
    api_endpoint_timeshift = '/timeshift/channel/%d/sources'
    api_endpoint_channels = '/channels?limit=200'
    api_endpoint_channel_livestream = '/livestreams/channel/%s'

    channel_map = False
    settings = False

    use_segments = True

    supported_delivery = 'dash'
    quality_definitions = {
        'UHD': {
            'name': 'UHD',
            'width': 3840,
            'height': 2160,
        },
        'QXB': {
            'name': 'Adaptive',
            'width': 1280,
            'height': 720,
        },
        'QXA': {
            'name': 'Adaptive',
            'width': 1280,
            'height': 720,
        }
    }
    drm_widewine_brand = '13f2e056-53fe-4469-ba6d-999970dbe549'
    drm_widewine_brand_ts = '319f2ca9-0d0c-4e5b-bb70-72efae61dad7'

    def __init__(self, channel_map=None, settings=None, useragent=False, kodi_worker=None):
        self.kodi_worker = kodi_worker
        if useragent:
            self.useragent = useragent

        self.log("Loading ORF On API")
        if not channel_map:
            self.channel_map = self.get_channel_map()
        else:
            self.channel_map = channel_map

        if not settings:
            self.settings = self.get_settings()
        else:
            self.settings = settings

        self.type_map = {
            'highlights': self.translate_string(30115, 'Highlights'),
            'genres': self.translate_string(30116, 'Categories'),
            'orflive': self.translate_string(30113, 'Livestream')
        }

    def is_geo_locked(self):
        headers = self.get_headers()
        url = self.geo_lock_url
        try:
            self.log("Loading %s" % url)
            request = urllib_urlopen(urllib_Request(url, headers=headers))
        except urllib_HTTPError as error:
            self.log('%s (%s)' % (error, url), 'error')
            return False
        except urllib_URLError as error:
            self.log('%s (%s)' % (error, url), 'error')
            return False

        try:
            xml_data = request.read()
            pattern = r'isallowed="(\w+)"'
            match = re.search(pattern, xml_data.decode('utf-8'))
            if match:
                is_allowed = match.group(1)
                return is_allowed.lower() != 'true'
        except re.error as error:
            self.log('%s (%s)' % (error, url), 'error')
            return False

    def translate_string(self, translation_id, fallback, replace=None):
        if self.kodi_worker:
            return self.kodi_worker.get_translation(translation_id, fallback, replace)

        return fallback

    def set_pager_limit(self, limit):
        self.api_pager_limit = limit

    def set_segments_behaviour(self, use_segments):
        self.use_segments = use_segments

    def get_auth_headers(self) -> dict:
        headers = self.get_headers()
        headers.update({'Authorization': self.api_auth})
        return headers

    def get_headers(self) -> dict:
        headers = {}
        headers.update({'User-Agent': self.useragent})
        return headers

    def get_widevine_url(self) -> str:
        return self.settings.get('drm_endpoints').get('widevine')

    def get_widevine_brand(self, timeshift=False) -> str:
        if timeshift:
            return self.drm_widewine_brand_ts
        return self.drm_widewine_brand

    def get_replay_days(self) -> int:
        return int(self.settings.get('max_viewing_time'))

    def auth_request(self, url):
        headers = self.get_auth_headers()
        try:
            url = self.api_base + url
            self.log("Loading %s" % url)
            request = urllib_urlopen(urllib_Request(url, headers=headers))
        except urllib_HTTPError as error:
            self.log('%s (%s)' % (error, url), 'error')
            return {}
        data = request.read()
        return json.loads(data)

    def get_main_menu(self) -> list:
        items = [Directory(self.translate_string(30144, 'Recently added'), '', '/recent', '', 'new', translator=self.kodi_worker),
                 Directory(self.translate_string(30110, 'Frontpage'), '', self.api_endpoint_home, '', 'home', translator=self.kodi_worker),
                 Directory(self.translate_string(30111, 'Schedule'), '', '/schedule', '', 'schedule', translator=self.kodi_worker),
                 Directory(self.translate_string(30112, 'Shows'), '', self.api_endpoint_shows % self.api_pager_limit, '', 'shows', translator=self.kodi_worker),
                 Directory(self.translate_string(30113, 'Livestream'), '', self.api_endpoint_livestreams, '', 'live', translator=self.kodi_worker),
                 Directory(self.translate_string(30114, 'Search'), '', '/search', '', 'search', translator=self.kodi_worker)]
        items += self.get_frontpage(lanes=False)
        return items

    def get_sign_language_menu(self):
        return Directory(self.translate_string(30145, 'Broadcasts using sign language'), '', '/episodes/sign-language', '', 'oegscontent', translator=self.kodi_worker)

    def get_audio_description_menu(self):
        return Directory(self.translate_string(30146, 'Broadcasts with audio description'), '', '/episodes/visually-impaired', '', 'adcontent', translator=self.kodi_worker)

    def get_subtitles_menu(self):
        return Directory(self.translate_string(30148, 'Broadcasts with subtitles'), '', '/episodes/subtitles', '', 'adcontent', translator=self.kodi_worker)

    def get_settings(self) -> dict:
        # Return cached settings
        if self.settings:
            self.log("Found cached settings")
            return self.settings

        self.log("Fetching fresh settings")
        url = self.api_endpoint_settings
        data = self.auth_request(url)
        return data

    def get_channel_map(self) -> dict:
        # Return cached channel map
        if self.channel_map:
            self.log("Found cached channel map")
            return self.channel_map

        self.log("Fetching new channel map")
        url = self.api_endpoint_channels
        data = self.auth_request(url)
        channel_map = {}
        for channel in data['_embedded']['items']:
            name = channel['name']
            channel_id = channel['id']
            reel = channel['reel']
            if 'color_logo' in channel['_links']:
                media_url = self.clean_url(channel['_links']['color_logo']['href'])
                logo_data = self.auth_request(media_url)
                color_logo = logo_data['public_urls']['tiny']['url']
            else:
                color_logo = ""
            if 'black_and_white_logo' in channel['_links']:
                media_url = self.clean_url(channel['_links']['black_and_white_logo']['href'])
                logo_data = self.auth_request(media_url)
                logo = logo_data['public_urls']['tiny']['url']
            else:
                logo = ""
            channel_map[channel_id] = {
                'name': name,
                'color_logo': color_logo,
                'logo': logo,
                'reel': reel
            }
        return channel_map

    def get_last_uploads(self, last_upload_range=12):
        current_date = datetime.now()
        current_delta = current_date - timedelta(hours=last_upload_range)

        today_filter = current_date.strftime("%Y-%m-%d")
        yesterday_filter = current_delta.strftime("%Y-%m-%d")

        recently_added = []
        if current_delta.strftime("%d.%m.%Y") != current_date.strftime("%d.%m.%Y"):
            self.log("Also fetching videos from yesterday")
            request_url = self.api_endpoint_schedule % yesterday_filter
            more_uploads = self.get_url(request_url)
            for item in more_uploads:
                released = item.date()
                released_datetime = datetime.fromisoformat(released).replace(tzinfo=None)
                if released_datetime > current_delta:
                    recently_added.append(item)
        request_url = self.api_endpoint_schedule % today_filter
        uploads = self.get_url(request_url)
        for item in uploads:
            released = item.date()
            released_datetime = datetime.fromisoformat(released).replace(tzinfo=None)
            if released_datetime > current_delta:
                recently_added.append(item)
        return reversed(recently_added)

    def get_schedule_dates(self) -> tuple:
        replay_days = self.get_replay_days()
        current_date = date.today()
        day_items = []
        filter_items = []
        for day in range(replay_days):
            days_before = current_date - timedelta(days=day)
            isodate = days_before.isoformat()
            prettydate = days_before.strftime("%A, %d.%m.%Y")
            day_items.append(prettydate)
            filter_items.append(isodate)
        return day_items, filter_items

    def get_frontpage(self, lanes=True) -> list:
        url = self.api_endpoint_home
        data = self.auth_request(url)
        items = self.render(data)
        if not lanes:
            for item in items[:]:
                if item.type() == 'lane':
                    items.remove(item)
        else:
            for item in items[:]:
                if item.type() != 'lane':
                    items.remove(item)
        return items

    def get_live_schedule(self) -> list:
        url = self.api_endpoint_livestreams
        data = self.auth_request(url)
        streams = []
        for channel in data:
            channel_streams = data[channel]
            for stream_item in channel_streams['items']:
                stream_dir = self.build(stream_item)
                stream_dir.set_channel(channel)
                if stream_dir and stream_dir.livestream_active():
                    streams.append(stream_dir)
        return streams

    def get_pvr(self, channel_reel) -> Directory:
        channel_infos = self.get_channel_map()
        for channel_id in channel_infos:
            if channel_infos[channel_id].get('reel') == channel_reel:
                request_url = self.api_endpoint_channel_livestream % channel_id
                data = self.auth_request(request_url)
                if data and '_embedded' in data and 'items' in data['_embedded']:
                    for livestream_item in data['_embedded']['items']:
                        stream_dir = self.build(livestream_item)
                        stream_dir.set_channel(channel_reel)
                        if stream_dir:
                            stream_detail_url = stream_dir.url()
                            stream_detail_data = self.load_stream_data(stream_detail_url)
                            if stream_detail_data and len(stream_detail_data):
                                pvr_stream = stream_detail_data[0]
                                pvr_stream.set_pvr_mode()
                                return pvr_stream

    def get_search(self, query) -> list:
        request_url = self.api_endpoint_search % quote_plus(query)
        data = self.auth_request(request_url)
        results = []
        if 'search' in data:
            if 'episodes' in data['search']:
                if data['search']['episodes']['total'] > 0:
                    title = ' - ' + self.translate_string(30124, 'All episode results') + ' (%d) -' % data['search']['episodes']['total']
                    desc = ""
                    link = self.api_endpoint_search_partial % ('episodes', query, self.api_pager_limit)
                    results.append(Directory(title, desc, link))

            if 'segments' in data['search']:
                if data['search']['segments']['total'] > 0:
                    title = ' - ' + self.translate_string(30125, 'All chapter results') + ' (%d) -' % data['search']['segments']['total']
                    desc = ""
                    link = self.api_endpoint_search_partial % ('segments', query, self.api_pager_limit)
                    results.append(Directory(title, desc, link))

            if 'history' in data['search']:
                if data['search']['history']['total'] > 0:
                    title = ' - ' + self.translate_string(30126, 'All history results') + ' (%d) -' % data['search']['history']['total']
                    desc = ""
                    link = self.api_endpoint_search_partial % ('history', query, self.api_pager_limit)
                    results.append(Directory(title, desc, link))

        if 'suggestions' in data:
            if 'episodes' in data['suggestions']:
                for episode in data['suggestions']['episodes']:
                    results.append(self.build(episode))
            if 'segments' in data['suggestions']:
                for segment in data['suggestions']['segments']:
                    results.append(self.build(segment))
            if 'history' in data['suggestions']:
                for history in data['suggestions']['history']:
                    results.append(self.build(history))
        return results

    def get_search_partial(self, section, query, args):
        request_url = self.api_endpoint_search_partial % (section, quote_plus(query), self.api_pager_limit)
        if args.get('page'):
            request_url += "&page=%d" % int(args.get('page')[0])
        data = self.auth_request(request_url)
        results = []
        if data and 'items' in data:
            for item in data['items']:
                results.append(self.build(item))
        if 'next' in data and data['next'] and data['next'] != "":
            next_page_url = self.clean_url(data['next'])
            results.append(Directory(self.translate_string(30127, 'Next page', '[COLOR blue][B]%s[/B][/COLOR]'), '', next_page_url, '', 'pager'))
        return results

    def get_url(self, url) -> list:
        data = self.auth_request(url)
        return self.render(data)

    def get_listing(self, item) -> list:
        url = item.url()
        data = self.auth_request(url)
        return self.render(data)

    def get_livestream(self, livestream_id) -> Directory:
        url = self.api_endpoint_livestream % livestream_id
        data = self.auth_request(url)
        return self.build(data)

    def get_related(self, episodeid) -> list:
        episode_details = self.get_url('/episode/%s' % episodeid)
        for episode_detail in episode_details:
            episode_source = episode_detail.get_source()
            if 'profile' in episode_source.get('_links'):
                profile_url = self.clean_url(episode_source.get('_links').get('profile').get('href'))
                profile_details = self.get_url(profile_url)
                return profile_details

    def get_timeshift_stream_url(self, item) -> str:
        if '_embedded' in item.source and 'channel' in item.source['_embedded']:
            channel_id = item.source['_embedded']['channel']['id']
            timeshift_url = self.api_endpoint_timeshift % channel_id
            timeshift_data = self.auth_request(timeshift_url)
            if timeshift_data and 'sources' in timeshift_data and self.supported_delivery in timeshift_data['sources']:
                source = timeshift_data['sources'][self.supported_delivery]
                source['drm_token'] = timeshift_data['drm_token']
                return source

    def get_restart_stream_url(self, item) -> str:
        timeshift_sources = self.get_timeshift_stream_url(item)
        if item.has_timeshift() and timeshift_sources:
            start_time = item.get_start_time_iso()
            return "%s?begin=%s" % (timeshift_sources['src'], start_time)

    def get_restart_stream(self, item) -> Directory:
        source = self.get_timeshift_stream_url(item)
        start_time = item.get_start_time_iso()
        item.set_stream({
            'url': "%s&begin=%s" % (source['src'], start_time),
            'drm': source['is_drm_protected'],
            'drm_token': source['drm_token'],
            'drm_widewine_url': self.get_widevine_url(),
            'drm_widewine_brand': self.get_widevine_brand(True)
        })
        return item

    def get_subtitle_url(self, playitem, subtitle_type='srt'):
        if '_links' in playitem and 'subtitle' in playitem['_links']:
            subtitle_url = self.clean_url(playitem['_links']['subtitle']['href'])
            data = self.auth_request(subtitle_url)
            if data and '%s_url' % subtitle_type in data:
                return data['%s_url' % subtitle_type]

    def load_stream_data(self, url) -> list:
        self.log("Loading Stream Details from %s" % url)
        data = self.auth_request(url)

        playlist = []
        if '_embedded' in data and 'items' in data['_embedded']:
            for playitem in data['_embedded']['items']:
                source = self.get_preferred_source(playitem)
                if source:
                    video = self.build_video(playitem, source['src'])
                    video.set_stream({
                        'url': source['src'],
                        'drm': source['is_drm_protected'],
                        'drm_token': playitem['drm_token'],
                        'drm_widewine_url': self.get_widevine_url(),
                        'drm_widewine_brand': self.get_widevine_brand(),
                        'subtitle': self.get_subtitle_url(playitem, 'srt')
                    })
                    playlist.append(video)
                elif 'segments' in playitem.get('_embedded'):
                    for segment in playitem.get('_embedded').get('segments'):
                        source = self.get_preferred_source(segment)
                        if source:
                            video = self.build_video(segment, source['src'])
                            video.set_stream({
                                'url': source['src'],
                                'drm': source['is_drm_protected'],
                                'drm_token': segment['drm_token'],
                                'drm_widewine_url': self.get_widevine_url(),
                                'drm_widewine_brand': self.get_widevine_brand(),
                                'subtitle': self.get_subtitle_url(segment, 'srt')
                            })
                            playlist.append(video)
        elif '_embedded' in data and 'item' in data['_embedded']:
            item = data['_embedded']['item']
            source = self.get_preferred_source(item)
            if not source:
                self.log("No video available yet.")
                return []
            video = self.build_video(item, source['src'])
            video.set_stream({
                'url': source['src'],
                'drm': source['is_drm_protected'],
                'drm_token': item['drm_token'],
                'drm_widewine_url': self.get_widevine_url(),
                'drm_widewine_brand': self.get_widevine_brand(),
                'subtitle': self.get_subtitle_url(item, 'srt')
            })
            playlist.append(video)
        elif 'sources' in data:
            source = self.get_preferred_source(data)
            if not source:
                self.log("No video available yet.")
                return []
            video = self.build_video(data, source['src'])
            if self.kodi_worker.use_timeshift and '_embedded' in data and 'channel' in data['_embedded'] and data['timeshift_available_livestream']:
                source = self.get_timeshift_stream_url(video)
                start_time = video.get_start_time_iso()
                ts_url = "%s&begin=%s" % (source['src'], start_time)
                video.set_url(ts_url)
                video.set_stream({
                    'url': ts_url,
                    'drm': source['is_drm_protected'],
                    'drm_token': source['drm_token'],
                    'drm_widewine_url': self.get_widevine_url(),
                    'drm_widewine_brand': self.get_widevine_brand(True),
                    'subtitle': self.get_subtitle_url(data, 'srt')
                })
            else:
                video.set_stream({
                    'url': source['src'],
                    'drm': source['is_drm_protected'],
                    'drm_token': data['drm_token'],
                    'drm_widewine_url': self.get_widevine_url(),
                    'drm_widewine_brand': self.get_widevine_brand(),
                    'subtitle': self.get_subtitle_url(data, 'srt')
                })
            playlist.append(video)
        return playlist

    def get_preferred_source(self, item):
        if self.supported_delivery in item['sources']:
            for source in item['sources'][self.supported_delivery]:
                for (quality, values) in self.quality_definitions.items():
                    if quality in source['quality_key']:
                        self.log("Found Stream %s" % values['name'])
                        return source

    def render(self, data) -> list:
        content = []
        if isinstance(data, list):
            for item in data:
                result = self.build(item)
                if result:
                    content.append(result)

        elif 'page' in data and '_items' in data:
            item = {}
            for item in data['_items']:
                result = self.build(item)
                if result:
                    content.append(result)
            if 'next' in item['_links']:
                next_page_url = self.clean_url(item['_links']['next']['href'])
                content.append(Directory(self.translate_string(30127, 'Next page', '[COLOR blue][B]%s[/B][/COLOR]'), '', next_page_url, '', 'pager'))

        elif 'page' in data and '_embedded' in data and 'items' in data['_embedded']:
            for item in data['_embedded']['items']:
                result = self.build(item)
                if result:
                    content.append(result)

            if 'next' in data['_links']:
                next_page_url = self.clean_url(data['_links']['next']['href'])
                content.append(Directory(self.translate_string(30127, 'Next page', '[COLOR blue][B]%s[/B][/COLOR]'), '', next_page_url, '', 'pager'))

        elif 'history_highlights' in data:
            for item in data['history_highlights']:
                result = self.build(item)
                if result:
                    content.append(result)
            for item in data['history_items']:
                result = self.build(item)
                if result:
                    content.append(result)

        elif 'timeShift' in data:
            for item in data['timeShift']:
                result = self.build(data['timeShift'][item])
                if result:
                    content.append(result)

        elif 'children_count' in data:
            if data['children_count'] > 0:
                for item in data['children']:
                    result = self.build(item)
                    if result:
                        content.append(result)
            else:
                for item in data['video_items']['_items']:
                    result = self.build(item)
                    if result:
                        content.append(result)
        elif '_links' in data and 'episodes' in data['_links']:
            episode_url = self.clean_url(data['_links']['episodes']['href'])
            return self.get_url(episode_url)
        elif isinstance(data, dict) and 'video_type' in data:
            result = self.build(data)
            if result:
                content.append(result)
        else:
            self.log("Unknown Render Type", 'error')
            self.print_obj(data)

        return content

    def build(self, item) -> Directory:
        if '_embedded' in item and 'video_item' in item['_embedded']:
            video_item = item['_embedded']['video_item']['_embedded']['item']
            link = item['_embedded']['video_item']['_links']['self']['href']
            return self.build_video(video_item, link)
        if 'sources' in item and 'segments' in item['_links']:
            link = item['_links']['segments']['href']
            return self.build_video(item, link)
        if 'sources' in item and 'playlist' in item['_links']:
            link = item['_links']['playlist']['href']
            return self.build_video(item, link)
        if 'id' in item and 'type' in item:
            return self.build_directory(item)
        if 'id' in item and 'videos' in item:
            return self.build_directory(item)
        if 'video_type' in item:
            video_item = item
            link = item['_links']['self']['href']
            return self.build_video(video_item, link)

        self.log("Unknown Type", 'error')
        self.print_obj(item)

    def build_directory(self, item) -> Directory:
        self.log("Building Directory %s (%s)" % (item['title'], item['id']))
        banner, backdrop, poster = self.get_images(item)
        item['channel_meta'] = self.channel_map
        item_id = item['id']
        if 'type' in item:
            item_type = item['type']
        else:
            item_type = 'generic'

        if 'description' in item and item['description'] is not None and item['description'] != "":
            description = item['description']
        elif 'share_subject' in item:
            description = item['share_subject']
        elif 'episode_title' in item:
            description = item['episode_title']
        else:
            description = ""

        if 'self' in item['_links'] and 'href' in item['_links']['self']:
            link = self.clean_url(item['_links']['self']['href'])
        elif '_self' in item['_links'] and isinstance(item['_links']['_self'], str):
            link = self.clean_url(item['_links']['_self'])
        else:
            link = self.clean_url(item['_links']['self'])

        if item_type == 'genre':
            link = "%s/profiles?limit=%d" % (link, self.api_pager_limit)
            return Directory(item['title'], description, link, item['id'], item['type'], banner, backdrop, poster, item, translator=self.kodi_worker)
        if item_id == 'lane':
            return Directory(item['title'], description, link, item['id'], item['type'], banner, backdrop, poster, item, translator=self.kodi_worker)
        if item_id == 'highlights':
            return Directory(self.type_map['highlights'], description, link, item['id'], item['type'], banner, backdrop, poster, item, translator=self.kodi_worker)
        if item_id == 'genres':
            return Directory(self.type_map['genres'], description, link, item['id'], item['type'], banner, backdrop, poster, item, translator=self.kodi_worker)
        if item_id == 'orflive':
            return Directory(self.type_map['orflive'], description, link, item['id'], item['type'], banner, backdrop, poster, item, translator=self.kodi_worker)
        if 'title' in item and item['title'] and 'type' in item:
            return Directory(item['title'], description, link, item['id'], item['type'], banner, backdrop, poster, item, translator=self.kodi_worker)
        if 'title' in item and item['title'] and 'children_count' in item:
            return Directory(item['title'], description, link, item['id'], 'directory', banner, backdrop, poster, item, translator=self.kodi_worker)

    def build_video(self, item, link) -> Directory:
        self.log("Building Video %s (%s)" % (item['title'], item['id']))
        title = item['title']
        link = self.clean_url(link)

        # Try to get the segements if available and activated for the api.
        if self.use_segments:
            if 'segments_complete' in item and 'video_type' in item and item['video_type'] == 'episode' and '/segments' not in link and 'episode' in link:
                self.log("Found video with segments.")
                link = self.clean_url(link + "/segments")
        else:
            if 'episode' in link and link.endswith('/segments'):
                link = link.replace('/segments', '')

        if 'description' in item and item['description'] is not None and item['description'] != "":
            description = item['description']
        elif 'share_subject' in item:
            description = item['share_subject']
        elif 'episode_title' in item:
            description = item['episode_title']
        else:
            description = ""
        video_type = item['video_type']
        video_id = item['id']
        banner, backdrop, poster = self.get_images(item)
        item['channel_meta'] = self.channel_map
        self.log("Video Link %s" % link)
        return Directory(title, description, link, video_id, video_type, banner, backdrop, poster, item, translator=self.kodi_worker)

    def clean_url(self, url):
        return url.replace(self.api_base, "")

    def get_images(self, item) -> tuple:
        try:
            if '_embedded' in item:
                banner = item['_embedded']['image']['public_urls']['highlight_teaser']['url']
                backdrop = item['_embedded']['image']['public_urls']['reference']['url']
                if 'image2x3_with_logo' in item['_embedded'] and '_default_' not in item['_embedded']['image2x3_with_logo']['public_urls']['highlight_teaser']['url']:
                    poster = item['_embedded']['image2x3_with_logo']['public_urls']['highlight_teaser']['url']
                elif '_default_' not in item['_embedded']['image2x3']['public_urls']['highlight_teaser']['url']:
                    poster = item['_embedded']['image2x3']['public_urls']['highlight_teaser']['url']
                else:
                    poster = banner
                return banner, backdrop, poster
        except IndexError:
            self.log("No images found for %s (%s)" % (item['title'], item['id']), 'warning')
        except KeyError:
            self.log("No images found for %s (%s)" % (item['title'], item['id']), 'warning')
        return "", "", ""

    def log(self, msg, msg_type='info'):
        self.kodi_worker.log("[%s][ORFON][API] %s" % (msg_type.upper(), msg))

    def print_obj(self, obj):
        self.log(json.dumps(obj, indent=4))
