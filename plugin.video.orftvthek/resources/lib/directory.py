import re
from datetime import datetime, timedelta


class Directory:
    def __init__(self, title, description, link, content_id="", content_type="", thumbnail="", backdrop="", poster="", source={}, translator=None):
        self.translator = translator
        self.title = title
        if description:
            self.description = description.strip()
        else:
            self.description = " "
        self.link = link
        self.content_id = content_id
        self.content_type = content_type
        self.thumbnail = thumbnail
        self.backdrop = backdrop
        self.poster = poster
        self.meta = self.build_meta(source)
        self.source = source
        self.videos = {}
        self.context_menu = self.build_content_menu()
        self.pvr_mode = False

    def has_segments(self):
        seg_matcher = r"\/episode\/[1-10].*\/segments"
        if re.search(seg_matcher, self.link):
            return True
        return False

    def build_content_menu(self) -> list:
        context_menu_items = []

        if self.is_livestream():
            restart_url = self.get_restart()
            if restart_url:
                context_menu_items.append({
                    'title': self.translate_string(30139, 'Restart'),
                    'url': "restart/%s" % self.source.get('id'),
                    'type': 'run'
                })

        if self.type() == 'episode':
            context_menu_items.append({
                'title': self.translate_string(30140, 'All episodes'),
                'url': "episode/%s/more" % self.source.get('id'),
                'type': 'update'
            })

        if self.type() == 'segment' and self.source.get('episode_id'):
            context_menu_items.append({
                'title': self.translate_string(30140, 'All episodes'),
                'url': "episode/%s/more" % self.source.get('episode_id'),
                'type': 'update'
            })

        if 'genre_id' in self.source and 'id' in self.source:
            related_link = "/lane/related_content/%s/%s" % (self.source.get('genre_id'), self.source.get('id'))
            context_menu_items.append({
                'title': self.translate_string(30150, 'Related content'),
                'url': related_link,
                'type': 'update'
            })

        return context_menu_items

    def get_context_menu(self) -> list:
        return self.context_menu

    def translate_string(self, translation_id, fallback, replace=None):
        if self.translator:
            return self.translator.get_translation(translation_id, fallback, replace)

        return fallback

    @staticmethod
    def build_meta(item) -> dict:
        meta = {}
        if 'online_episode_count' in item:
            meta['episodes'] = item['online_episode_count']

        # Show Meta
        if 'genre_title' in item and item['genre_title'] is not None:
            if item['genre_title'] == 'Film & Serie' and 'sub_headline' in item and item['sub_headline'] is not None:
                meta['genre'] = item['sub_headline']
            else:
                meta['genre'] = item['genre_title']

        if 'genre_id' in item and item['genre_id'] is not None:
            meta['genre_id'] = item['genre_id']
        if 'production_year' in item and item['production_year'] is not None:
            meta['year'] = item['production_year']
        if 'production_country' in item and item['production_country'] is not None:
            meta['country'] = item['production_country']

        # Build Release Infos
        if 'date' in item and item['date'] is not None:
            meta['release_date'] = item['date']
        elif 'episode_date' in item and item['episode_date'] is not None:
            meta['release_date'] = item['episode_date']
        elif 'updated_at' in item and item['updated_at'] is not None:
            meta['release_date'] = item['updated_at']

        # Build additional Title Infos
        if 'headline' in item and item['headline'] is not None:
            meta['headline'] = item['headline']
        if 'sub_headline' in item and item['sub_headline'] is not None:
            meta['sub_headline'] = item['sub_headline']
        if 'episode_title' in item and item['episode_title'] is not None:
            meta['episode'] = item['episode_title']

        # Build Channel Info
        if 'main_channel_id' in item and item['main_channel_id'] is not None:
            if str(item['main_channel_id']) in item['channel_meta']:
                meta['channel'] = item['channel_meta'][str(item['main_channel_id'])]
                meta['channel_id'] = item['main_channel_id']
        elif 'channel_id' in item and item['channel_id'] is not None:
            if str(item['channel_id']) in item['channel_meta']:
                meta['channel'] = item['channel_meta'][str(item['channel_id'])]
                meta['channel_id'] = item['channel_id']
        elif 'SSA' in item and 'channel' in item['SSA']:
            for channel in item['channel_meta']:
                if item['channel_meta'][channel]['reel'] == item['SSA']['channel']:
                    meta['channel'] = item['channel_meta'][channel]
                    break

        # Build Accessibility infos
        if 'audio_description_service_available' in item and item['audio_description_service_available'] is not None:
            meta['audio_description_available'] = item['audio_description_service_available']
        if 'has_subtitle' in item and item['has_subtitle'] is not None:
            meta['subtitles'] = item['has_subtitle']
        else:
            meta['subtitles'] = False

        # Stream Meta
        if 'two_channel_audio' in item and item['two_channel_audio'] is not None:
            meta['multiaudio'] = item['two_channel_audio']
        if 'restart' in item and item['restart'] is not None:
            meta['restart'] = item['restart']
        if 'uhd' in item and item['uhd'] is not None:
            meta['uhd'] = item['uhd']
        if 'duration_seconds' in item and item['duration_seconds'] is not None:
            meta['duration'] = int(item['duration_seconds'])
        if 'audio_description' in item and item['audio_description'] is not None:
            meta['audio_description'] = item['audio_description']
        elif 'audio_description_service_available' in item and item.get('title').startswith("AD | "):
            meta['audio_description'] = True
        else:
            meta['audio_description'] = False
        if 'oegs' in item and item['oegs'] is not None:
            meta['oegs'] = item['oegs']
        elif 'is_oegs' in item and item['is_oegs'] is not None:
            meta['oegs'] = item['is_oegs']
        else:
            meta['oegs'] = False

        if 'right' in item and item['right'] is not None and item['right'] == 'austria':
            meta['geo_lock'] = True
        else:
            meta['geo_lock'] = False
        return meta

    def label(self) -> str:
        if self.meta.get('headline') and self.meta.get('headline') != self.title and self.meta.get('headline') not in self.title:
            label = "%s | %s" % (self.title, self.meta.get('headline'))
        else:
            label = self.title

        if self.is_livestream() and self.get_channel() and not self.is_pvr_mode():
            channel = self.get_channel()
            if self.meta.get('restart'):
                label = "[LIVE] [R] [%s] %s" % (channel, label)
            else:
                label = "[LIVE] [%s] %s" % (channel, label)
        elif self.is_pvr_mode():
            channel = self.get_channel()
            label = "%s | %s" % (channel, label)
        return label

    def label2(self) -> str:
        if self.meta.get('sub_headline') and self.meta.get('sub_headline') != self.title and self.meta.get('sub_headline') not in self.title:
            return self.meta.get('sub_headline')

    def is_livestream(self) -> bool:
        return self.type() == 'timeshift' or self.type() == 'livestream'

    def livestream_active(self) -> bool:
        current_time = datetime.now()
        start_time = self.get_start_time()
        end_time = self.get_end_time()
        if start_time < current_time < end_time:
            return True

    def is_geo_locked(self):
        return self.meta.get('geo_lock')

    def has_audio_description(self):
        return self.meta.get('audio_description')

    def has_sign_language(self):
        return self.meta.get('oegs')

    def get_start_time(self):
        return datetime.fromisoformat(self.get_source().get('start')).replace(tzinfo=None)

    def get_start_time_iso(self):
        ref_date = datetime.fromisoformat(self.get_source().get('start')) - timedelta(hours=2)
        d_date = ref_date.strftime("%Y%m%d")
        d_time = ref_date.strftime("%H%M%S")
        return "%sT%s" % (d_date, d_time)

    def get_end_time(self):
        return datetime.fromisoformat(self.get_source().get('end')).replace(tzinfo=None)

    def set_channel(self, channel_reel):
        for channel in self.source['channel_meta']:
            if self.source['channel_meta'][channel]['reel'] == channel_reel:
                self.meta['channel'] = self.source['channel_meta'][channel]
                break

    def has_timeshift(self):
        if 'timeshift_available_livestream' in self.source and 'video_type' in self.source:
            if self.source['timeshift_available_livestream'] and self.source['video_type'] == 'timeshift':
                return True
        return False

    def get_restart(self):
        if 'restart' in self.source:
            if self.source['restart'] and '_embedded' in self.source and 'channel' in self.source['_embedded']:
                restart_url = self.source['_embedded']['channel']['channel_restart_url_hbbtv']
                return restart_url
        return False

    def get_channel(self):
        special_regex = r"^web\d*"
        if self.meta.get('channel'):
            if re.search(special_regex, self.meta.get('channel').get('name')):
                return "Special"
            return self.meta.get('channel').get('name')

    def get_channel_logo(self):
        if self.meta.get('channel'):
            return self.meta.get('channel').get('logo')

    def get_resolution(self):
        if self.meta.get('uhd'):
            return 3840, 2160

        return 1280, 720

    def set_stream(self, sources):
        self.videos = sources

    def get_stream(self):
        return self.videos

    def date(self):
        return self.meta.get('release_date')

    def time(self):
        try:
            return datetime.fromisoformat(self.date()).strftime("%H:%M")
        except TypeError:
            self.log('No time set for %s' % self.label())

    def get_description(self) -> str:
        if self.description is not None:
            return self.description

        return ""

    def get_meta_description(self):
        meta_description = {}
        if not self.is_pvr_mode():
            if self.get_episodes() > 1:
                meta_description[self.translate_string(30141, 'Episodes')] = self.get_episodes()
            if self.get_channel():
                meta_description[self.translate_string(30142, 'Channel')] = self.get_channel()
            if self.is_livestream() and self.get_stream_runtime():
                meta_description[self.translate_string(30113, 'Livestream')] = self.get_stream_runtime()
                if not self.livestream_active():
                    meta_description[self.translate_string(30114, 'Starts in')] = "%d min" % self.get_stream_start_delta()
            if 'episode_title' in self.get_source() and 'sub_headline' in self.get_source():
                meta_description[self.meta.get('sub_headline')] = ""

        return meta_description

    def get_stream_start_delta(self):
        current_time = datetime.now()
        start_time = self.get_start_time()
        return int((start_time - current_time).total_seconds() / 60)

    def get_stream_runtime(self):
        start_time = self.get_start_time().strftime("%H:%M")
        end_time = self.get_start_time().strftime("%H:%M")
        if start_time != end_time:
            return "%s - %s" % (start_time, end_time)

    def annotate_time(self):
        self.title = "%s | %s" % (self.time(), self.title)

    def annotate_channel(self):
        self.title = "[%s] %s" % (self.get_channel(), self.title)

    def country(self):
        return self.meta.get('country')

    def year(self):
        return self.meta.get('year')

    def genre(self) -> str:
        if 'genre' in self.meta:
            return self.meta.get('genre')

    def has_art(self) -> bool:
        if self.poster or self.thumbnail or self.backdrop:
            return True
        return False

    def is_playable(self) -> bool:
        if self.type() == 'episode':
            return True
        if self.type() == 'segment':
            return True
        if self.is_livestream():
            return True
        if self.get_episodes() == 1 and self.type() == 'temporary':
            return True
        return False

    def get_episodes(self):
        if self.meta.get('episodes') is not None:
            return int(self.meta.get('episodes'))
        return 1

    def get_cast(self):
        cast = []
        part = None
        cast_extract_pattern = r'(?P<name>.*?)(\s\((?P<role>.*?)\)|,|u.v.m| u.a.|u. a.)'
        if 'Besetzung:' in self.description:
            part = self.description.split('Besetzung:')
        elif 'Hauptdarsteller:' in self.description:
            part = self.description.split('Hauptdarsteller:')
        elif 'Besetzung\r\n' in self.description:
            part = self.description.split('Besetzung\r\n')
        elif 'Hauptdarsteller\r\n' in self.description:
            part = self.description.split('Hauptdarsteller\r\n')
        elif 'Mit:' in self.description:
            part = self.description.split('Mit:')
        elif '\r\nMit ' in self.description:
            part = self.description.split('\r\nMit ')

        try:
            if part is not None and len(part) > 1:
                matches = re.findall(cast_extract_pattern, part[1], re.DOTALL)
                for name, _, role in matches:
                    if name.strip() != "":
                        if '\r\n' in name.strip() or 'Regie:' in name.strip():
                            break
                        if role.strip() != "":
                            cast.append((name.strip(), role.strip()))
                        else:
                            cast.append(name.strip())
            return cast
        except re.error:
            return cast

    def url(self) -> str:
        return self.link

    def set_url(self, url):
        self.link = url

    def type(self) -> str:
        return self.content_type

    def get_duration(self):
        if self.meta.get('duration') is not None:
            return int(self.meta.get('duration'))

    def is_pvr_mode(self):
        return self.pvr_mode

    def set_pvr_mode(self):
        self.pvr_mode = True

    def media_type(self) -> str:
        contenttype = self.type()
        if self.label2() == 'Fernsehfilm':
            return 'movie'
        if self.get_duration() is not None and self.get_duration() > 60 * 60:
            return 'movie'
        if contenttype == 'lane':
            return 'video'
        if contenttype == 'episode':
            return 'episode'
        if contenttype == 'segment':
            return 'episode'
        if contenttype == 'temporary':
            return 'tvshow'
        return 'movie'

    def get_source(self):
        return self.source

    def debug(self):
        self.log('Title: %s' % self.title)
        self.log('Playable: %s' % self.is_playable())
        self.log('Description: %s' % self.description)
        self.log('Link: %s' % self.link)
        self.log('ID: %s' % self.content_id)
        self.log('Type: %s' % self.content_type)
        self.log('Playable: %s' % self.is_playable())
        self.log('Thumbnail: %s' % self.thumbnail)
        self.log('Backdrop: %s' % self.backdrop)
        self.log('Poster: %s' % self.poster)
        for (key, value) in self.meta.items():
            self.log("%s: %s" % (key.capitalize().replace("_", " "), value))

        for context_menu_item in self.context_menu:
            self.log('Context Menu Item: %s' % context_menu_item.get('title'))

        if len(self.get_stream()):
            self.log('Stream Data available %d' % len(self.get_stream()))

    def log(self, msg, msg_type='info'):
        if self.translator:
            self.translator.log("[%s][ORFON][DIRECTORY] %s" % (msg_type.upper(), msg))
