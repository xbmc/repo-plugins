#!/usr/bin/env python
import bs4, html, time, json, re, sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta

from urllib.request import Request, urlopen
from urllib.parse import parse_qs, urlencode
from urllib.error import URLError

DATE_FORMAT = '%Y-%m-%d'

URL_BASE = 'https://www.rrr.org.au'

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36'

ignore_on_air = False


def get(resource_path):
    return urlopen_ua(Scraper.url_for(resource_path))

def urlopen_ua(url):
    return urlopen(Request(url, headers={'User-Agent': USER_AGENT}), timeout=5)

def get_json(url):
    return urlopen_ua(url).read().decode()

def get_json_obj(url):
    return json.loads(get_json(url))

def strptime(s, fmt):
    return datetime.fromtimestamp(time.mktime(time.strptime(s, fmt)))


class Resource:
    def __init__(self, itemobj):
        self._itemobj = itemobj

    def id(self):
        return self.path.split('/')[-1]

    @property
    def path(self):
        return Scraper.resource_path_for(self._itemobj.find('a').attrs['href'])

    RE_CAMEL = re.compile(r'(?<!^)(?=[A-Z])')
    @property
    def type(self):
        return self.RE_CAMEL.sub('_', self.__class__.__name__).lower()

    @property
    def img(self):
        return self._itemobj.find('img')

    @property
    def thumbnail(self):
        if self.img:
            return self.img.attrs.get('data-src')

    @property
    def links(self):
        return {
            'self': self.path
        }

    def attributes(self):
        return {}

    def links(self):
        return {
            'self': self.path
        }

    def relationships(self):
        return None

    def included(self):
        return None

    def to_dict(self):
        d = {
            'type':       self.type,
            'id':         self.id(),
            'attributes': {
                'title': self.title,
                **self.attributes(),
            },
            'links'     : self.links(),
        }

        r = self.relationships()
        if r:
            d = {
                **d,
                'relationships': r,
            }

        i = self.included()
        if i:
            d = {
                **d,
                'included': i,
            }
        return d



### Scrapers ##############################################

class UnmatchedResourcePath(BaseException):
    '''
    '''

def strip_value(v):
    if  isinstance(v, dict):
        return strip_values(v)
    elif isinstance(v, list):
        return [strip_values(x) for x in v]
    elif isinstance(v, str):
        return v.strip()
    else:
        return v

def strip_values(d):
    if isinstance(d, dict):
        return { k: remove_nulls(strip_value(v)) for k, v in d.items() }
    else:
        return d

def remove_nulls(obj):
    if  isinstance(obj, dict):
        return { k: remove_nulls(v) for k, v in obj.items() if v }
    elif isinstance(obj, list):
        return [remove_nulls(x) for x in obj if x]
    else:
        return obj


class Scraper:
    @classmethod
    def call(cls, resource_path):
        scraper = cls.find_by_resource_path(resource_path)
        return strip_values(scraper.generate())

    @classmethod
    def url_for(cls, resource_path):
        return (cls.find_by_resource_path(resource_path)).url()

    @classmethod
    def resource_path_for(cls, website_path):
        scraper = cls.find_by_website_path(website_path)
        m = scraper.match_website_path(website_path)
        if m:
            return scraper.RESOURCE_PATH_PATTERN.format_map(m.groupdict())


    @classmethod
    def find_by_resource_path(cls, resource_path):
        try:
            return next(scraper for scraper in cls.__subclasses__() if scraper.matching_resource_path(resource_path))(resource_path)
        except StopIteration:
            raise UnmatchedResourcePath(f"No match for '{resource_path}'")

    @classmethod
    def find_by_website_path(cls, website_path):
        return next(scraper for scraper in cls.__subclasses__() if scraper.match_website_path(website_path))

    @classmethod
    def regex_from(cls, pattern):
        return re.compile(
          '^' +
          re.sub('{([A-z]+)}', '(?P<\\1>[^/]+?)', pattern) +
          '(?:[?](?P<query_params>.+))?' +
          '$'
        )

    @classmethod
    def resource_path_regex(cls):
        return cls.regex_from(cls.RESOURCE_PATH_PATTERN)

    @classmethod
    def match_resource_path(cls, path):
        return cls.regex_from(cls.RESOURCE_PATH_PATTERN).match(path)

    @classmethod
    def match_website_path(cls, path):
        return cls.regex_from(cls.WEBSITE_PATH_PATTERN).match(path)

    @classmethod
    def matching_resource_path(cls, resource_path):
        if cls.match_resource_path(resource_path):
            return cls(resource_path)


    def __init__(self, resource_path):
        self.resource_path = resource_path
        m = self.__class__.resource_path_regex().match(self.resource_path)
        if m:
            self.groupdict = m.groupdict()

    def soup(self):
        return bs4.BeautifulSoup(get(self.resource_path), 'html.parser')

    def url(self):
        return f'{URL_BASE}{self.website_path()}'

    def website_path(self):
        template = self.__class__.WEBSITE_PATH_PATTERN

        if self.groupdict.get('query_params'):
            template += '?{query_params}'

        return template.format_map(self.groupdict)

    def pagination(self, pagekey='page', selfval=1, nextval=None, lastval=None):
        resource_path = self.resource_path.split('?')
        if len(resource_path) > 1:
            resource_params = parse_qs(resource_path[-1])
            if not resource_params.get(pagekey):
                resource_params[pagekey] = selfval
            else:
                resource_params[pagekey] = resource_params[pagekey][0]
        else:
            resource_params = {pagekey: selfval}

        template = resource_path[0] + '?{}'
        links = {}

        links['self'] = template.format(urlencode(resource_params))

        if nextval:
            resource_params[pagekey] = nextval
        else:
            resource_params[pagekey] = int(resource_params[pagekey]) + 1
        links['next'] = template.format(urlencode(resource_params))

        links_last = None
        if lastval:
            resource_params[pagekey] = lastval
            links['last'] = template.format(urlencode(resource_params))

        return links



class ProgramsScraper(Scraper):
    RESOURCE_PATH_PATTERN = '/programs'
    WEBSITE_PATH_PATTERN = '/explore/programs'

    def generate(self):
        return {
            'data': [
                Program(item).to_dict()
                for item in self.soup().findAll('div', class_='card clearfix')
            ],
            'links': {
                'self': self.__class__.RESOURCE_PATH_PATTERN
            },
        }


class ProgramScraper(Scraper):
    RESOURCE_PATH_PATTERN = '/programs/{program_id}'
    WEBSITE_PATH_PATTERN = '/explore/programs/{program_id}'

    def generate(self):
        soup = self.soup()
        programtitle = soup.find(class_='page-banner__heading')
        if programtitle:
            title = programtitle.text

        thumbnail, background = None, None
        programimage = soup.find(class_='card__background-image')
        if programimage:
            programimagesrc = re.search(r"https://[^']+", programimage.attrs.get('style'))
            if programimagesrc:
                thumbnail = programimagesrc[0]

        programbg = soup.find(class_='banner__image')
        if programbg:
            background = programbg.attrs.get('src')

        textbody = '\n'.join((
            soup.find(class_='page-banner__summary').text,
            soup.find(class_='page-banner__time').text
        ))

        # Aarrgh the website dragons strike again!
        def map_path(path):
            m = re.match('^/explore/(?P<collection>[^/]+?)/(?P<program>[^/]+?)#episode-selector', path)
            if m:
                d = m.groupdict()
                if   d['collection'] == 'programs':
                    return f"/explore/{d['collection']}/{d['program']}/episodes/page"
                elif d['collection'] == 'podcasts':
                    return f"/explore/{d['collection']}/{d['program']}/episodes"

        collections = [
            {
                'type': 'collection',
                'id': Scraper.resource_path_for(map_path(anchor.attrs['href'])),
                'attributes': {
                    'title': ' - '.join((title, anchor.text)),
                    'thumbnail':  thumbnail,
                    'background': background,
                    'textbody':   textbody,
                },
                'links': {
                    'self': Scraper.resource_path_for(map_path(anchor.attrs['href'])),
                }
            }
            for anchor in soup.find_all('a', class_='program-nav__anchor')
        ]
        highlights = soup.find('a', string=re.compile('highlights'))
        if highlights:
            collections.append(
                {
                    'type': 'collection',
                    'id': Scraper.resource_path_for(highlights.attrs['href']),
                    'attributes': {
                        'title': ' - '.join((title, 'Segments')),
                        'thumbnail': thumbnail,
                        'background': background,
                        'textbody':  textbody,
                    },
                    'links': {
                        'self': Scraper.resource_path_for(highlights.attrs['href']),
                    }
                }
            )
        return {
            'data': collections,
        }


class AudioItemGenerator:
    def generate(self):
        return {
            'data': [
                item for item in [
                    AudioItem.factory(div)
                    for div in self.soup().findAll(class_='card__text')
                ]
            ],
            'links': self.pagination()
        }

class ProgramBroadcastsScraper(Scraper):
    RESOURCE_PATH_PATTERN = '/programs/{program_id}/broadcasts'
    WEBSITE_PATH_PATTERN = '/explore/programs/{program_id}/episodes/page'

    def generate(self):
        soup = self.soup()
        programtitle = soup.find(class_='page-banner__heading')
        if programtitle:
            title = programtitle.text

        thumbnail, background = None, None
        programimage = soup.find(class_='card__background-image')
        if programimage:
            programimagesrc = re.search(r"https://[^']+", programimage.attrs.get('style'))
            if programimagesrc:
                thumbnail = programimagesrc[0]

        programbg = soup.find(class_='banner__image')
        if programbg:
            background = programbg.attrs.get('src')

        textbody = '\n'.join((
            soup.find(class_='page-banner__summary').text,
            soup.find(class_='page-banner__time').text
        ))

        # Aarrgh the website dragons strike again!
        def map_path(path):
            m = re.match('^/explore/(?P<collection>[^/]+?)/(?P<program>[^/]+?)#episode-selector', path)
            if m:
                d = m.groupdict()
                if   d['collection'] == 'programs':
                    return f"/explore/{d['collection']}/{d['program']}/episodes/page"
                elif d['collection'] == 'podcasts':
                    return f"/explore/{d['collection']}/{d['program']}/episodes"

        collections = [
            {
                'type': 'collection',
                'id': Scraper.resource_path_for(map_path(anchor.attrs['href'])),
                'attributes': {
                    'title': ' - '.join((title, anchor.text)),
                    'thumbnail':  thumbnail,
                    'background': background,
                    'textbody':   textbody,
                },
                'links': {
                    'self': Scraper.resource_path_for(map_path(anchor.attrs['href'])),
                }
            }
            for anchor in soup.find_all('a', class_='program-nav__anchor')
        ]

        # hackety - hack - hack - hack ... just blindly turn "Broadcasts" into "Segments" while nobody is looking
        collections[0]['id'] = collections[0]['id'].replace('broadcasts', 'segments')
        collections[0]['links']['self'] = collections[0]['id']
        collections[0]['attributes']['title'] = collections[0]['attributes']['title'].replace('Broadcasts', 'Segments')

        broadcasts = [
            item for item in [
                BroadcastCollection(div).to_dict()
                for div in self.soup().findAll(class_='card')
            ]
        ]

        images = {
            'background': background,
        }
        [b['attributes'].update(images) for b in broadcasts]

        collections = [item for item in (collections[::-1] + broadcasts) if item]

        return {
            'data': collections,
            'links': self.pagination(),
        }



class ProgramPodcastsScraper(Scraper, AudioItemGenerator):
    RESOURCE_PATH_PATTERN = '/programs/{program_id}/podcasts'
    WEBSITE_PATH_PATTERN = '/explore/podcasts/{program_id}/episodes'


class ProgramSegmentsScraper(Scraper, AudioItemGenerator):
    RESOURCE_PATH_PATTERN = '/programs/{program_id}/segments'
    WEBSITE_PATH_PATTERN = '/explore/programs/{program_id}/highlights'


class OnDemandSegmentsScraper(Scraper, AudioItemGenerator):
    RESOURCE_PATH_PATTERN = '/segments'
    WEBSITE_PATH_PATTERN = '/on-demand/segments'


class OnDemandBroadcastsScraper(Scraper, AudioItemGenerator):
    RESOURCE_PATH_PATTERN = '/broadcasts'
    WEBSITE_PATH_PATTERN = '/on-demand/episodes'


class ArchivesScraper(Scraper, AudioItemGenerator):
    RESOURCE_PATH_PATTERN = '/archives'
    WEBSITE_PATH_PATTERN = '/on-demand/archives'


class ArchiveScraper(Scraper):
    RESOURCE_PATH_PATTERN = '/archives/{item}'
    WEBSITE_PATH_PATTERN = '/on-demand/archives/{item}'

    def generate(self):
        item = self.soup().find(class_='adaptive-banner__audio-component')
        return {
            'data': AudioItem.factory(item)
        }


class ExternalMedia:
    RE_BANDCAMP_ALBUM_ID             = re.compile(r'https://bandcamp.com/EmbeddedPlayer/.*album=(?P<media_id>[^/]+)')
    RE_BANDCAMP_ALBUM_ART            = re.compile(r'"art_id":(\w+)')
    BANDCAMP_ALBUM_ART_URL           = 'https://bandcamp.com/api/mobile/24/tralbum_details?band_id=1&tralbum_type=a&tralbum_id={}'

    RE_BANDCAMP_ALBUM_LINK_ID        = re.compile(r'(?P<media_id>https?://[^/\.]+\.bandcamp.com/album/[\w\-]+)')
    RE_BANDCAMP_BAND_LINK_ID         = re.compile(r'(?P<media_id>https?://[^/\.]+\.bandcamp.com/)$')

    RE_BANDCAMP_TRACK_ID             = re.compile(r'(?P<media_id>https?://[^/\.]+\.bandcamp.com/track/[\w\-]+)')
    RE_BANDCAMP_TRACK_ART            = re.compile(r'art_id&quot;:(?P<art_id>\d+),')
    RE_BANDCAMP_TRACK_TITLE          = re.compile(r'\<h2 class\="trackTitle"\>\s+(?P<title>[^\n]*)\s+\<\/h2\>')
    RE_BANDCAMP_TRACK_ARTIST         = re.compile(r'data-band="[^"]*;name&quot;:&quot;(?P<artist>[^&]+)&quot;')
    RE_BANDCAMP_TRACK_DURATION       = re.compile(r'duration&quot;:(?P<duration>[\d\.]+),')
    RE_BANDCAMP_TRACK_BAND_ART       = re.compile(r'data-band="[^"]*image_id&quot;:(?P<band_art_id>\d+)}"')

    RE_SOUNDCLOUD_PLAYLIST_ID        = re.compile(r'.+soundcloud\.com/playlists/(?P<media_id>[^&]+)')

    RE_YOUTUBE_VIDEO_ID              = re.compile(r'^(?:(?:https?:)?\/\/)?(?:(?:www|m)\.)?(?:youtube(?:-nocookie)?\.com|youtu.be)(?:\/(?:[\w\-]+\?v=|embed\/|v\/)?)(?P<media_id>[\w\-]+)(?!.*list)\S*$')
    RE_YOUTUBE_VIDEO_ART_ID          = re.compile(r'^https:\/\/i\.ytimg\.com\/vi\/(?P<media_id>[\w\-]+)\/hqdefault\.jpg$')
    RE_YOUTUBE_VIDEO_TITLE           = re.compile(r'"videoDetails":{[^}]*,"title":"(?P<title>[^"]+)"')
    RE_YOUTUBE_VIDEO_ARTIST          = re.compile(r'<link itemprop="name" content="(?P<artist>[^"]+)"')
    RE_YOUTUBE_VIDEO_DESC            = re.compile(r'"attributedDescription":{"content":"(?P<textbody>[^{]*)","')
    RE_YOUTUBE_VIDEO_DURATION        = re.compile(r'itemprop="duration" content="PT(?P<hours>[\d]+H)?(?P<minutes>[\d]+M)?(?P<seconds>[\d]+S)?"')
    YOUTUBE_VIDEO_DURATION_URL       = 'https://www.youtube.com/watch?v={}'
    YOUTUBE_VIDEO_ART_URL_FORMAT     = 'https://i.ytimg.com/vi/{}/hqdefault.jpg'

    RE_YOUTUBE_PLAYLIST_ID           = re.compile(r'^(?:(?:https?:)?\/\/)?(?:(?:www|m)\.)?(?:youtube(?:-nocookie)?\.com|youtu.be)\/.+\?.*list=(?P<media_id>[\w\-]+)')
    YOUTUBE_PLAYLIST_ART_URL         = 'https://www.youtube.com/playlist?list={}'
    RE_YOUTUBE_PLAYLIST_ART          = re.compile(r'og:image" content="(?P<art_url>[^"]+)"><meta property="og:image:width" content="640"')
    RE_YOUTUBE_PLAYLIST_ART_LQ       = re.compile(r'og:image" content="(?P<art_url>[^?]+)[^"]+"')
    RE_YOUTUBE_PLAYLIST_TITLE        = re.compile(r'<meta property="og:title" content="(?P<title>[^"]+)"')
    RE_YOUTUBE_PLAYLIST_ARTIST       = re.compile(r'"shortBylineText":{"runs":\[{"text":"(?P<artist>[^"]+)"')
    RE_YOUTUBE_PLAYLIST_DURATION     = re.compile(r'"lengthText":[^}]+}},"simpleText":"(?P<duration>[^"]+)"}')

    RE_INDIGITUBE_ALBUM_ID           = re.compile(r'https://www.indigitube.com.au/embed/album/(?P<media_id>[^"]+)')
    INDIGITUBE_ACCESS_KEY            = 'access_token=%242a%2410%24x2Zy%2FTgIAOC0UUMi3NPKc.KY49e%2FZLUJFOpBCNYAs8D72UUnlI526'
    INDIGITUBE_ALBUM_URL             = 'https://api.appbooks.com/content/album/{}?' + INDIGITUBE_ACCESS_KEY
    INDIGITUBE_ALBUM_ART_URL         = 'https://api.appbooks.com/get/{}/file/file.jpg?w=512&quality=90&' + INDIGITUBE_ACCESS_KEY + '&ext=.jpg'

    RE_SPOTIFY_ALBUM_ID              = re.compile(r'.+spotify\.com(\/embed)?\/album\/(?P<media_id>[^&?\/]+)')
    RE_SPOTIFY_PLAYLIST_ID           = re.compile(r'.+spotify\.com(\/embed)?\/playlist\/(?P<media_id>[^&]+)')
    RE_SPOTIFY_ALBUM_ART             = re.compile(r'\-\-image\-src:url\((\&\#x27\;|\')(?P<art_url>[^\&\']+)(\&\#x27\;|\')')
    RE_SPOTIFY_DURATION              = re.compile(r'<\/h4><div class="[^"]+">(?P<duration>[^<]+)</div></li>')

    RE_APPLE_ALBUM_ID                = re.compile(r'.+music\.apple\.com\/au\/album\/(?P<media_id>.+)')
    APPLE_ALBUM_URL                  = 'https://music.apple.com/au/album/{}'
    RE_APPLE_ALBUM_ART               = re.compile(r'meta name="twitter:image" content="(?P<art_url>[^"]+)">')
    RE_APPLE_DURATION                = re.compile(r'meta property="music:song:duration" content="PT(?P<hours>[\d]+H)?(?P<minutes>[\d]+M)?(?P<seconds>[\d]+S)?">')

    RE_MEDIA_URLS = {
        'bandcamp': {
            're':     RE_BANDCAMP_ALBUM_ID,
        },
        'bandcamp_link': {
            're':     RE_BANDCAMP_ALBUM_LINK_ID,
        },
        'bandcamp_band_link': {
            're':     RE_BANDCAMP_BAND_LINK_ID,
        },
        'bandcamp_track': {
            're':     RE_BANDCAMP_TRACK_ID,
        },
        'soundcloud': {
            're':     RE_SOUNDCLOUD_PLAYLIST_ID,
        },
        'youtube': {
            're':     RE_YOUTUBE_VIDEO_ID,
        },
        'youtube_art': {
            're':     RE_YOUTUBE_VIDEO_ART_ID,
        },
        'youtube_playlist': {
            're':     RE_YOUTUBE_PLAYLIST_ID,
        },
        'indigitube': {
            're':     RE_INDIGITUBE_ALBUM_ID,
        },
        'spotify': {
            're':     RE_SPOTIFY_ALBUM_ID,
        },
        'spotify_playlist': {
            're':     RE_SPOTIFY_PLAYLIST_ID,
        },
        'apple': {
            're':     RE_APPLE_ALBUM_ID,
        },
    }

    fetch_yt_video = False

    def media_items(self, iframes, fetch_album_art=False, fetch_yt_video=False):
        matches = []
        self.fetch_yt_video = fetch_yt_video

        for iframe in iframes:
            if not iframe.get('src'):
                continue
            media_id = None
            for plugin, info in self.RE_MEDIA_URLS.items():
                plugin_match = re.match(info.get('re'), iframe.get('src'))
                if plugin_match:
                    media_id = plugin_match.groupdict().get('media_id')
                    if media_id:
                        break

            matches.append({
                'media_id':   media_id,
                'src':        iframe.get('src'),
                'attrs':      iframe.get('attrs') if iframe.get('attrs') else {},
                'plugin':     plugin if plugin_match else None,
            })

        if fetch_album_art:
            executor = ThreadPoolExecutor(max_workers=3)
            art_exec = [executor.submit(self.get_album_art, match=match) for match in matches]
            matches = [match.result() for match in art_exec]

        return matches

    def get_album_art(self, match={}):
        result = match
        media_id, plugin = match['media_id'], match['plugin']
        album_art = {}
        if plugin == 'bandcamp':
            album_art = self.bandcamp_album_art(media_id)
        elif plugin == 'bandcamp_link':
            album_art = self.bandcamp_track_art(media_id)
        elif plugin == 'bandcamp_band_link':
            album_art = self.bandcamp_band_art(media_id)
        elif plugin == 'bandcamp_track':
            album_art = self.bandcamp_track_art(media_id)
        elif plugin == 'indigitube':
            album_art = self.indigitube_album_art(media_id)
        elif plugin == 'spotify' or plugin == 'spotify_playlist':
            album_art = self.spotify_album_art(match['src'])
        elif plugin == 'apple':
            album_art = self.apple_album_art(media_id)
        elif plugin == 'youtube_playlist':
            album_art = self.youtube_playlist_art(media_id)
        elif plugin == 'youtube' or plugin == 'youtube_art':
            result['plugin'] = 'youtube'
            if self.fetch_yt_video:
                album_art = self.youtube_video_duration(media_id)
            album_art['art'] = self.YOUTUBE_VIDEO_ART_URL_FORMAT.format(media_id)

        result['thumbnail']  = album_art.get('art')
        result['background'] = album_art.get('band')
        result['duration']   = album_art.get('duration')
        if 'attrs' not in result.keys():
            result['attrs'] = {}
        if 'title' not in result['attrs'].keys() and album_art.get('title'):
            result['attrs']['title']    = album_art.get('title')
        if 'artist' not in result['attrs'].keys() and album_art.get('artist'):
            result['attrs']['artist']   = album_art.get('artist')
        if 'textbody' not in result['attrs'].keys() and album_art.get('textbody'):
            result['attrs']['textbody'] = album_art.get('textbody')
        return result

    def get_sum_duration(self, duration_matches):
        durations = [int(x.split(':')[0]) * 60 + int(x.split(':')[1]) for x in duration_matches]
        return sum(durations)

    def get_pt_duration(self, duration):
        result = 0
        if duration['hours']:
            result += int(duration['hours'][:-1]) * 3600
        if duration['minutes']:
            result += int(duration['minutes'][:-1]) * 60
        if duration['seconds']:
            result += int(duration['seconds'][:-1])
        return result

    def bandcamp_album_art(self, album_id):
        api_url  = self.BANDCAMP_ALBUM_ART_URL.format(album_id)
        try:
            json_obj = get_json_obj(api_url)
        except URLError as e:
            return {}

        art_id   = json_obj.get('art_id')
        band_id  = json_obj.get('band', {}).get('image_id')

        duration = 0.0
        for track in json_obj.get('tracks', []):
            duration += float(track.get('duration', '0'))

        result = {}
        if art_id:
            result['art']  = f'https://f4.bcbits.com/img/a{art_id}_5.jpg'
        if band_id:
            result['band'] = f'https://f4.bcbits.com/img/{band_id}_20.jpg'
        if duration:
            result['duration'] = int(duration)
        return result

    def bandcamp_track_art(self, track_url):
        try:
            track_page = get_json(track_url)
        except URLError as e:
            return {}

        art_match        = re.search(self.RE_BANDCAMP_TRACK_ART, track_page)
        band_match       = re.search(self.RE_BANDCAMP_TRACK_BAND_ART, track_page)
        title_match      = re.search(self.RE_BANDCAMP_TRACK_TITLE, track_page)
        artist_match     = re.search(self.RE_BANDCAMP_TRACK_ARTIST, track_page)
        duration_matches = re.finditer(self.RE_BANDCAMP_TRACK_DURATION, track_page)
        result = {}
        if art_match:
            art_id  = art_match.groupdict().get('art_id')
            result['art']  = f'https://f4.bcbits.com/img/a{art_id}_5.jpg'
        if band_match:
            band_id = band_match.groupdict().get('band_art_id')
            result['band'] = f'https://f4.bcbits.com/img/{band_id}_20.jpg'
        if title_match:
            result['title'] = title_match.groupdict().get('title', '').strip()
        if artist_match:
            result['artist'] = artist_match.groupdict().get('artist')

        duration = 0.0
        for match in duration_matches:
            duration += float(match.groupdict().get('duration', '0'))
        result['duration'] = int(duration)

        return result

    def bandcamp_band_art(self, track_url):
        try:
            track_page = get_json(track_url)
        except URLError as e:
            return {}

        band_match       = re.search(self.RE_BANDCAMP_TRACK_BAND_ART, track_page)
        artist_match     = re.search(self.RE_BANDCAMP_TRACK_ARTIST, track_page)
        result = {}
        if band_match:
            band_id = band_match.groupdict().get('band_art_id')
            result['band'] = f'https://f4.bcbits.com/img/{band_id}_20.jpg'
            result['art']  = result['band']
        if artist_match:
            result['artist'] = artist_match.groupdict().get('artist')
            result['title'] = result['artist']

        return result

    def indigitube_album_art(self, album_id):
        api_url  = self.INDIGITUBE_ALBUM_URL.format(album_id)
        result = {}

        try:
            json_obj = get_json_obj(api_url)
        except URLError as e:
            return result

        data = json_obj.get('data', {})

        art_id = data.get('coverImage', {}).get('_id')
        if art_id:
            result['art'] = self.INDIGITUBE_ALBUM_ART_URL.format(art_id)
        description = json_obj.get('data', {}).get('description', '')
        if description:
            result['textbody'] = re.compile(r'<[^>]+>').sub('', description)
        result['title']    = json_obj.get('title')
        result['artist']   = json_obj.get('realms', [{}])[0].get('title')

        return result

    def youtube_video_duration(self, video_id):
        video_url = self.YOUTUBE_VIDEO_DURATION_URL.format(video_id)
        try:
            video_page  = get_json(video_url)
        except URLError as e:
            return {}

        duration_match  = re.search(self.RE_YOUTUBE_VIDEO_DURATION, video_page)
        title_match     = re.search(self.RE_YOUTUBE_VIDEO_TITLE, video_page)
        artist_match    = re.search(self.RE_YOUTUBE_VIDEO_ARTIST, video_page)
        desc_match      = re.search(self.RE_YOUTUBE_VIDEO_DESC, video_page)
        result = {'duration': 0}
        if duration_match:
            gd = duration_match.groupdict()
            result['duration'] = self.get_pt_duration(gd)
        if title_match:
            result['title'] = title_match.groupdict().get('title', '').strip()
        if artist_match:
            result['artist'] = artist_match.groupdict().get('artist', '').strip()
        if desc_match:
            result['textbody'] = html.unescape(desc_match.groupdict().get('textbody', '').strip())

        return result

    def youtube_playlist_art(self, playlist_id):
        api_url = self.YOUTUBE_PLAYLIST_ART_URL.format(playlist_id)
        try:
            playlist_page = get_json(api_url)
        except URLError as e:
            return {}

        art_match        = re.search(self.RE_YOUTUBE_PLAYLIST_ART, playlist_page)
        duration_matches = re.findall(self.RE_YOUTUBE_PLAYLIST_DURATION, playlist_page)
        title_match     = re.search(self.RE_YOUTUBE_PLAYLIST_TITLE, playlist_page)
        artist_match    = re.search(self.RE_YOUTUBE_PLAYLIST_ARTIST, playlist_page)

        result = {}
        if art_match:
            result['art'] = art_match.groupdict().get('art_url').replace('&amp;', '&') + '&ext=.jpg'
        else:
            art_match = re.search(self.RE_YOUTUBE_PLAYLIST_ART_LQ, playlist_page)
            result['art'] = art_match.groupdict().get('art_url')
        if duration_matches:
            result['duration'] = self.get_sum_duration(duration_matches)
        if title_match:
            result['title'] = html.unescape(title_match.groupdict().get('title', '').strip())
        if artist_match:
            result['artist'] = html.unescape(artist_match.groupdict().get('artist', '').strip())
        return result

    def spotify_album_art(self, src):
        api_url = src
        try:
            spotify_page = get_json(api_url)
        except URLError as e:
            return {}

        art_match        = re.search(self.RE_SPOTIFY_ALBUM_ART, spotify_page)
        duration_matches = re.findall(self.RE_SPOTIFY_DURATION, spotify_page)

        result = {}
        if art_match:
            result['art'] = art_match.groupdict().get('art_url')
        if duration_matches:
            result['duration'] = self.get_sum_duration(duration_matches)
        return result

    def apple_album_art(self, album_id):
        api_url = self.APPLE_ALBUM_URL.format(album_id)
        try:
            album_page  = get_json(api_url)
        except URLError as e:
            return {}

        art_match       = re.search(self.RE_APPLE_ALBUM_ART, album_page)
        duration_match  = re.finditer(self.RE_APPLE_DURATION, album_page)
        result = {'duration': 0}

        if art_match:
            result['art'] = art_match.groupdict().get('art_url')
        for duration in duration_match:
            gd = duration.groupdict()
            result['duration'] += self.get_pt_duration(duration)

        return result

class FeaturedAlbumScraper(Scraper, ExternalMedia):
    RESOURCE_PATH_PATTERN = '/featured_albums/{album_id}'
    WEBSITE_PATH_PATTERN = '/explore/album-of-the-week/{album_id}'

    @property
    def path(self):
        return self.resource_path

    def generate(self):
        pagesoup = self.soup()

        iframes = [
            {
                'src': iframe.attrs.get('src'),
                'attrs': None
            }
            for iframe in pagesoup.findAll('iframe')
            if iframe.attrs.get('src')
        ]
        album_urls   = self.media_items(iframes, fetch_album_art=True, fetch_yt_video=True)

        album_copy   = '\n'.join([p.text for p in pagesoup.find(class_='feature-album__copy').findAll("p", recursive=False)])
        album_image  = pagesoup.find(class_='audio-summary__album-artwork')
        album_info   = pagesoup.find(class_='album-banner__copy')
        album_title  = album_info.find(class_='album-banner__heading', recursive=False).text
        album_artist = album_info.find(class_='album-banner__artist',  recursive=False).text

        album_type = 'featured_album'
        album_id   = self.resource_path.split('/')[-1]
        background = None
        duration   = None

        for album in [album for album in album_urls if album.get('plugin')]:
            album_type = album.get('plugin')
            album_id   = album.get('media_id')
            background = album.get('background')
            duration   = album.get('duration')

        data = [
            {
                'type': album_type,
                'id': album_id,
                'attributes': {
                    'title':     album_title,
                    'artist':    album_artist,
                    'textbody':  album_copy,
                    'duration':  duration,
                },
                'links': {
                    'self': self.path,
                }
            }
        ]

        if album_image:
            data[0]['attributes']['thumbnail']  = album_image.attrs.get('src')

        if background:
            data[0]['attributes']['background'] = background

        return {
            'data': data,
        }



class FeaturedAlbumsScraper(Scraper):
    RESOURCE_PATH_PATTERN = '/featured_albums'
    WEBSITE_PATH_PATTERN = '/explore/album-of-the-week'

    def generate(self):
        return {
            'data': [
                FeaturedAlbum(item).to_dict()
                for item in self.soup().findAll('div', class_='card clearfix')
            ],
            'links': self.pagination()
        }


class NewsItemsScraper(Scraper):
    RESOURCE_PATH_PATTERN = '/news_items'
    WEBSITE_PATH_PATTERN = '/explore/news-articles'

    def generate(self):
        return {
            'data': [
                News(item).to_dict()
                for item in self.soup().findAll(class_='list-view__item')
            ],
            'links': self.pagination(),
        }


class NewsItemScraper(Scraper):
    RESOURCE_PATH_PATTERN = '/news_items/{item}'
    WEBSITE_PATH_PATTERN = '/explore/news-articles/{item}'


class ProgramBroadcastScraper(Scraper):
    RESOURCE_PATH_PATTERN = '/programs/{program_id}/broadcasts/{item}'
    WEBSITE_PATH_PATTERN = '/explore/programs/{program_id}/episodes/{item}'

    def generate(self):
        soup = self.soup()
        programbg = soup.find(class_='banner__image')
        programbg = programbg.attrs.get('src') if programbg else None

        broadcast = ProgramBroadcast(
            soup.find(class_='audio-summary')
        ).to_dict()
        broadcast['attributes']['textbody'] = soup.find(class_='page-banner__summary').text

        segments = [
            ProgramBroadcastSegment(item).to_dict()
            for item in soup.findAll(class_='episode-detail__highlights-item')
        ]

        tracks = [
            ProgramBroadcastTrack(item).to_dict()
            for item in soup.findAll(class_='audio-summary__track clearfix')
        ]

        items = []
        for item in ([broadcast] + segments + tracks):
            if not item:
                continue
            if programbg and not item.get('attributes', {}).get('background'):
                item['attributes']['background'] = programbg
            items.append(item)

        return {
            'data': items
        }


class ProgramPodcastScraper(Scraper):
    RESOURCE_PATH_PATTERN = '/programs/{program_id}/podcasts/{item}'
    WEBSITE_PATH_PATTERN = '/explore/podcasts/{program_id}/episodes/{item}'

    def generate(self):
        return {'data': []}


class ProgramSegmentScraper(Scraper):
    RESOURCE_PATH_PATTERN = '/segments/{item}'
    WEBSITE_PATH_PATTERN = '/on-demand/segments/{item}'

    def generate(self):
        return {'data': []}


class ScheduleScraper(Scraper):
    RESOURCE_PATH_PATTERN = '/schedule'
    WEBSITE_PATH_PATTERN = '/explore/schedule'

    def generate(self):
        soup = self.soup()
        date = soup.find(class_='calendar__hidden-input').attrs.get('value')
        prevdate, nextdate = [x.find('a').attrs.get('href').split('=')[-1] for x in soup.findAll(class_='page-nav__item')]
        return {
            'data': [
                ScheduleItem(item).to_dict()
                for item in self.soup().findAll(class_='list-view__item')
            ],
            'links': self.pagination(pagekey='date', selfval=date, nextval=prevdate),
        }


class SearchScraper(Scraper):
    RESOURCE_PATH_PATTERN = '/search'
    WEBSITE_PATH_PATTERN = '/search'

    def generate(self):
        return {
            'data': [
                SearchItem(item).to_dict()
                for item in self.soup().findAll(class_='search-result')
            ],
            'links': self.pagination(),
        }


class SoundscapesScraper(Scraper):
    RESOURCE_PATH_PATTERN = '/soundscapes'
    WEBSITE_PATH_PATTERN = '/explore/soundscape'

    def generate(self):
        return {
            'data': [
                Soundscape(item).to_dict()
                for item in self.soup().findAll(class_='list-view__item')
            ],
            'links': self.pagination()
        }


class SoundscapeScraper(Scraper, ExternalMedia):
    RESOURCE_PATH_PATTERN = '/soundscapes/{item}'
    WEBSITE_PATH_PATTERN = '/explore/soundscape/{item}'

    def generate(self):
        pagesoup = self.soup()

        iframes = []
        section = pagesoup.find('section', class_='copy')
        for heading in section.findAll(['h1', 'h2', 'h3', 'h4', 'p'], recursive=False):
            iframe = heading.find_next_sibling()
            while iframe != None and iframe.find('iframe') == None:
                iframe = iframe.find_next_sibling()
            if iframe == None or len(heading.text) < 2:
                continue

            aotw = len(heading.text.split('**')) > 1

            attrs = {
                'id':             ' '.join(heading.text.split('**')[0].split(' - ')),
                'title':          heading.text.split('**')[0].split(' - ')[-1].split(' – ')[-1],
                'artist':         heading.text.split(' - ')[0].split(' – ')[0],
                'featured_album': heading.text.split('**')[1] if aotw else '',
            }
            media = {
                'src': iframe.find('iframe').attrs.get('src'),
                'attrs': attrs,
            }
            if aotw:
                iframes.insert(0, media)
            else:
                iframes.append(media)

        media_items = self.media_items(iframes, fetch_album_art=True, fetch_yt_video=True)
        soundscape_date = pagesoup.find(class_='news-item__title').text.split(' - ')[-1]

        data = []
        for media in media_items:
            dataitem = {}
            attributes = {
                'subtitle':   soundscape_date,
                'artist':     media.get('attrs').get('artist'),
                'thumbnail':  media.get('thumbnail'),
            }

            if media.get('background'):
                attributes['background'] = media.get('background')

            if media.get('duration'):
                attributes['duration'] = media.get('duration')

            if media.get('plugin'):
                # dataitem['id']   = media.get('attrs').get('id', '').replace(' ', '-').lower()
                dataitem['id'] = media.get('media_id')
                dataitem['type'] = media.get('plugin')
                attributes['title'] = media.get('attrs').get('title')
                # attributes['url']   = media.get('url')
            else:
                dataitem['id']    = ''
                attributes['title'] = media.get('attrs').get('title')

            if media.get('attrs').get('textbody'):
                attributes['textbody'] = media.get('attrs').get('textbody', '').strip()
            else:
                attributes['textbody'] = '{}\n{}\n'.format(
                    media.get('attrs').get('title'),
                    media.get('attrs').get('featured_album')
                ).strip()

            dataitem['attributes'] = attributes

            data.append(dataitem)

        return {
            'data': data,
        }


class Program(Resource):
    @property
    def path(self):
        return f"{Scraper.resource_path_for(self._itemobj.find('a').attrs['href'])}/broadcasts?page=1"

    def id(self):
        return self.path.split("/")[2]

    @property
    def title(self):
        return self._itemobj.find('h1', class_='card__title' ).find('a').text

    @property
    def textbody(self):
        return self._itemobj.find('p').text

    def attributes(self):
        return {
            'title':     self.title,
            'thumbnail': self.thumbnail,
            'textbody':  self.textbody,
        }


class Topic(Resource):
    @property
    def title(self):
        return self._itemobj.find('a').text

    def attributes(self):
        return {
            'title': self.title
        }


class TopicsScraper(Scraper):
    RESOURCE_PATH_PATTERN = '/topics'
    WEBSITE_PATH_PATTERN = '/'

    def generate(self):
        return {
            'data': [
                Topic(item).to_dict()
                for item in self.soup().findAll(class_='topic-list__item')
            ],
            'links': {
                'self': self.__class__.RESOURCE_PATH_PATTERN
            },
        }


class TopicScraper(Scraper):
    RESOURCE_PATH_PATTERN = '/topics/{topic}'
    WEBSITE_PATH_PATTERN = '/topics/{topic}'

    def generate(self):
        return {
            'data': [
                SearchItem(item).to_dict()
                for item in self.soup().findAll(class_='search-result')
            ],
            'links': self.pagination(),
        }


class TracksSearchScraper(Scraper):
    RESOURCE_PATH_PATTERN = '/tracks/search'
    WEBSITE_PATH_PATTERN = '/tracks/search'

    def generate(self):
        return {
            'data': [
                BroadcastTrack(item).to_dict()
                for item in self.soup().findAll(class_='search-result')
            ],
        }


class TrackScraper(Scraper):
    RESOURCE_PATH_PATTERN = '/tracks/{track_id}'
    WEBSITE_PATH_PATTERN = '/tracks/{track_id}'

    def generate(self):
        return {'data': []}


class Track(Resource):
    def __init__(self, path, artist, title):
        self._path = path
        self.artist = artist
        self.title = title

    @property
    def path(self):
        return self._path

    def id(self):
        return self.path.split('/')[-1]

    def attributes(self):
        return {
            'title':  self.title,
            'artist': self.artist,
        }


class EventsScraper(Scraper):
    RESOURCE_PATH_PATTERN = '/events'
    WEBSITE_PATH_PATTERN = '/events'

    def generate(self):
        return {
            'data': [
                Event(item).to_dict()
                for item in self.soup().findAll('div', class_='card')
            ],
            'links': self.pagination()
        }


class EventScraper(Scraper, ExternalMedia):
    RESOURCE_PATH_PATTERN = '/events/{item}'
    WEBSITE_PATH_PATTERN = '/events/{item}'

    @property
    def path(self):
        return self.resource_path

    def generate(self):
        item = self.soup().find(class_='event')
        venue = item.find(class_='event__venue-address-details')
        eventdetails = item.find(class_='event__details-copy').get_text(' ').strip()
        copy = item.find(class_='copy')
        textbody = copy.get_text('\n')

        flag_label = item.find(class_='flag-label')
        if flag_label:
            event_type = flag_label.text.replace(' ', '-').lower()
        else:
            # event_type = None
            event_type = 'event'

        result = {
            'data': [
                {
                    'type':       event_type,
                    'id':         Resource.id(self),
                    'attributes': {
                        'title':    item.find(class_='event__title').text,
                        'venue':    venue.get_text(' ') if venue else '',
                        'textbody': '\n'.join((eventdetails, textbody)),
                    },
                    'links': {
                        'self': self.resource_path,
                    }
                }
            ],
        }

        for link in copy.find_all(['a', 'iframe']):
            link_href = {
                'src': link.attrs.get('href', link.attrs.get('src')),
            }
            media = self.media_items([link_href], fetch_album_art=True, fetch_yt_video=True)[0]
            if media.get('plugin'):
                dataitem = {}
                if media.get('plugin'):
                    dataitem['id'] = media.get('media_id')
                    dataitem['type'] = media.get('plugin')
                else:
                    dataitem['id'] = ''

                dataitem['attributes'] = {
                    'thumbnail':  media.get('thumbnail'),
                    'background': media.get('background'),
                    'duration':   media.get('duration'),
                    'title':      media.get('attrs').get('title'),
                    'textbody':   media.get('attrs').get('textbody', media.get('attrs').get('title')),
                    'artist':     media.get('attrs').get('artist'),
                }

                result['data'].append(dataitem)

        return result


class GiveawaysScraper(Scraper):
    RESOURCE_PATH_PATTERN = '/giveaways'
    WEBSITE_PATH_PATTERN = '/subscriber-giveaways'

    def generate(self):
        return {
            'data': [
                Giveaway(item).to_dict()
                for item in self.soup().findAll(class_='list-view__item')
            ],
        }


class GiveawayScraper(Scraper):
    RESOURCE_PATH_PATTERN = '/giveaways/{giveaway}'
    WEBSITE_PATH_PATTERN = '/subscriber-giveaways/{giveaway}'

    @property
    def path(self):
        return self.resource_path

    def generate(self):
        item = self.soup().find(class_='subscriber_giveaway')
        banner = self.soup().find(class_='compact-banner')
        closes = banner.find(class_='compact-banner__date').text
        textbody = item.find(class_='subscriber-giveaway__copy').get_text(' ')

        return {
            'data': [
                {
                    'type': 'giveaway',
                    'id':   Resource.id(self),
                    'attributes': {
                        'title':     banner.find(class_='compact-banner__heading').text,
                        'textbody':  f'{closes}\n\n{textbody}',
                        'thumbnail': item.find(class_='summary-inset__artwork').attrs.get('src'),
                    },
                    'links': {
                        'self':  '/'.join((self.resource_path, 'entries')),
                    }
                }
            ],
        }


class VideoScraper(Scraper):
    RESOURCE_PATH_PATTERN = '/videos/{item}'
    WEBSITE_PATH_PATTERN = '/explore/videos/{item}'

    def generate(self):
        return {'data': []}


class VideosScraper(Scraper, ExternalMedia):
    RESOURCE_PATH_PATTERN = '/videos'
    WEBSITE_PATH_PATTERN = '/explore/videos'

    def generate(self):
        pagesoup = self.soup()

        images = []
        for card in pagesoup.findAll(class_='card'):
            img = card.find('img', class_='scalable-image__image')
            carddate = card.find('span', class_='card__meta')
            cardurl = card.find('a', class_='card__anchor')
            #time.strptime(carddate.text, '%d %B %Y')

            attrs = {
                'id':             cardurl.attrs.get('href', '/').split('/')[-1],
                'title':          img.attrs.get('alt'),
                'date':           carddate.text,
            }
            media = {
                'src': img.attrs.get('data-src'),
                'attrs': attrs,
            }
            images.append(media)

        media_items = self.media_items(images, fetch_album_art=True)

        data = []
        for media in media_items:
            dataitem = {}
            attributes = {
                'subtitle':   media.get('attrs').get('date'),
                'artist':     media.get('attrs').get('artist'),
                'thumbnail':  media.get('thumbnail'),
            }

            if media.get('background'):
                attributes['background'] = media.get('background')

            if media.get('duration'):
                attributes['duration'] = media.get('duration')

            if media.get('plugin'):
                dataitem['id'] = media.get('media_id')
                dataitem['type'] = media.get('plugin')
                attributes['title'] = media.get('attrs').get('title')
            else:
                dataitem['id']    = ''
                attributes['title'] = media.get('attrs').get('title')

            attributes['textbody'] = media.get('attrs').get('title').strip()

            dataitem['attributes'] = attributes

            data.append(dataitem)

        return {
            'data': data,
            'links': self.pagination(),
        }



### Scrapers ##############################################

class FeaturedAlbum(Resource):
    @property
    def title(self):
        return self._itemobj.find('h1', class_='card__title' ).find('a').text

    @property
    def subtitle(self):
        return self._itemobj.find(class_='card__meta').text

    @property
    def textbody(self):
        return self._itemobj.find('p').text

    def attributes(self):
        return {
            'title':     self.title,
            'subtitle':  self.subtitle,
            'thumbnail': self.thumbnail,
            'textbody':  self.textbody,
        }


class Giveaway(Resource):
    @property
    def title(self):
        return self._itemobj.find('span').text

    @property
    def textbody(self):
        return self._itemobj.find('p').text

    def attributes(self):
        return {
            'title':     self.title,
            'textbody':  self.textbody,
            'thumbnail': self.thumbnail,
        }


class News(Resource):
    @property
    def title(self):
        return self._itemobj.find(class_='list-view__title').text

    @property
    def type(self):
        return 'news_item'

    @property
    def textbody(self):
        return self._itemobj.find(class_='list-view__summary').text

    def attributes(self):
        return {
            'title':    self.title,
            'textbody': self.textbody,
        }


class Soundscape(Resource):
    @property
    def title(self):
        return self._itemobj.find('span').text.replace(':', '').replace('Triple R ', '')

    @property
    def subtitle(self):
        return self._itemobj.find('span').text.split(' - ')[-1]

    @property
    def textbody(self):
        return self._itemobj.find('p').text

    def attributes(self):
        return {
            'title':     self.title,
            'subtitle':  self.subtitle,
            'textbody':  self.textbody,
            'thumbnail': self.thumbnail,
        }


class Event(Resource):
    @property
    def _itemtitle(self):
        return self._itemobj.find(class_='card__title').find('a').text

    @property
    def title(self):
        if self.label:
            return ' - '.join((self._itemtitle, self._itemdate, self.label))
        else:
            return ' - '.join((self._itemtitle, self._itemdate))

    @property
    def label(self):
        label = self._itemobj.find(class_='card__label')
        return label.text if label else ''

    @property
    def _itemtype(self):
        return self._itemobj.find(class_='card__meta').find('div').text

    @property
    def type(self):
        return self._itemtype.replace(' ', '-').lower()

    @property
    def img(self):
        return self._itemobj.find('a', class_='card__anchor').find('img')

    @property
    def _itemdate(self):
        meta = self._itemobj.find('span', class_='card__meta')
        metadiv = meta.findAll('div')
        if len(metadiv) > 0:
            return metadiv[0].text
        else:
            return meta.text if meta else ''

    @property
    def venue(self):
        meta = self._itemobj.find('span', class_='card__meta')
        metadiv = meta.findAll('div')
        if len(metadiv) > 1:
            return metadiv[1].text

    @property
    def textbody(self):
        venue = self.venue
        return '\n'.join((self._itemtitle, 'Date: ' + self._itemdate, ('Venue:\n' + venue) if venue else '', '', self._itemtype))

    def attributes(self):
        return {
            'title':         self.title,
            'thumbnail':     self.thumbnail,
            'venue':         self.venue,
            'textbody':      self.textbody,
        }


class ScheduleItem:
    def __init__(self, itemobj):
        self._itemobj = itemobj
        self._audio_item = AudioItem.factory(itemobj)

    @property
    def path(self):
        path = Scraper.resource_path_for(self._itemobj.find('a').attrs['href'])
        segments = path.split('?')[0].split('/')
        if 'programs' in segments and 'broadcasts' not in segments:
            path += '/broadcasts?page=1'

        return path

    @property
    def start(self):
        return self._itemobj.attrs.get('data-timeslot-start')

    @property
    def end(self):
        return self._itemobj.attrs.get('data-timeslot-end')

    @property
    def _on_air_status(self):
        if self.start and self.end and '+' in self.start:
            start = self.start.split('+')
            end   = self.end.split('+')
            td    = timedelta(hours=int(start[1][:2]))
            try:
                start = strptime(start[0], '%Y-%m-%dT%H:%M:%S') - td
                end   = strptime(end[0],   '%Y-%m-%dT%H:%M:%S') - td
                return start, end
            except (ValueError, TypeError) as e:
                pass
        return None, None

    @property
    def textbody(self):
        return self._itemobj.find('p').text

    @property
    def duration(self):
        if self.audio_item:
            return self.audio_item.get('attributes').get('duration')

    @property
    def content(self):
        content = json.loads(self._itemobj.find(class_='hide-from-all').attrs['data-content'])
        content['title'] = content.pop('name')

        if self.audio_item:
            content['type'] = 'broadcast_index'
            content['title'] = self.audio_item.get('attributes').get('title')
        else:
            if '/broadcasts?page=1' not in self.path:
                content['type'] = 'broadcast_index'
            elif content['type'] == 'programs':
                content['type'] = 'program'
            else:
                content['type'] = 'scheduled'

        start, end = self._on_air_status
        if (not ignore_on_air) and start and end:
            localtime = datetime.utcnow()
            if start < localtime and end > localtime:
                flag_label = self._itemobj.find(class_='flag-label__on-air').next_sibling
                if flag_label:
                    content['on_air'] = flag_label.string
        img = self._itemobj.find(class_='list-view__image')
        if img:
            content['thumbnail'] = img.attrs.get('data-src')

        return content

    @property
    def audio_item(self):
        return self._audio_item or {}

    def to_dict(self):
        attrs = {
            **self.content,
            'start': self.start,
            'end': self.end,
            'textbody': self.textbody,
            'duration': self.duration,
        }
        itemid = attrs.pop('id')
        itemtype = attrs.pop('type')

        return {
            'type': itemtype,
            'id': itemid,
            'attributes': attrs,
            'links': {
                'self': self.path
            }
        }


class ItemType:
    def from_label(val):
        default = "_".join(val.lower().split())
        return {
            'album_of_the_week': 'featured_album',
            'audio_archive':     'archive',
            'broadcast_episode': 'broadcast',
            'news':              'news_item',
            'podcast_episode':   'podcast',
        }.get(default, default)


class SearchItem(Resource):
    @property
    def type(self):
        return ItemType.from_label(self._itemobj.find(class_='flag-label').text)

    @property
    def title(self):
        return self._itemobj.find(class_='search-result__title').text

    @property
    def textbody(self):
        body = self._itemobj.find(class_='search-result__body')
        if body:
            return "\n\n".join([item.text for item in body.children])

    def attributes(self):
        return {
            **Resource.attributes(self),
            'textbody': self.textbody,
        }


class BroadcastTrack(Resource):
    def id(self):
        return f'{SearchItem.id(self)}.{self.track.id()}'

    @property
    def title(self):
        return f'{self.track.artist} - {self.track.title} (Broadcast on {self.broadcast_date} by {self.program_title})'

    RE = re.compile(r'Played (?P<played_date>[^/]+) by (?P<played_by>.+)View all plays$')
    @property
    def played(self):
        return self.RE.match(self._itemobj.find(class_='search-result__meta-info').text)

    @property
    def broadcast_date(self):
        return time.strftime(DATE_FORMAT, time.strptime(self.played['played_date'], '%A %d %b %Y'))

    @property
    def program_title(self):
        return self.played['played_by']

    @property
    def track(self):
        return Track(
            Scraper.resource_path_for(self._itemobj.find(class_='search-result__meta-links').find('a').attrs['href']),
            self._itemobj.find(class_='search-result__track-artist').text,
            self._itemobj.find(class_='search-result__track-title').text,
        )

    def attributes(self):
        return {
            'broadcast_date': self.broadcast_date,
            'program_title':   self.program_title,
        }

    def relationships(self):
        return {
            'broadcast': {
                'links': {
                    # TODO - FIXME:
                    # Nb. this shouldn't be `self.path` as this class is a BroadcastTrack not a Broadcast
                    # which _also_ means that BroadcastTrack shouldn't have a `links.self`
                    'related': self.path
                },
                'data': {
                    'type': 'broadcast',
                    'id':  Resource.id(self),
                },
            },
            'track': {
                'links': {
                    'related': self.track.path,
                },
                'data': {
                    'type': self.track.type,
                    'id':   self.track.id(),
                },
            },
        }

    def included(self):
        return [
            self.track.to_dict(),
        ]


class PlayableResource(Resource):
    @property
    def _playable(self):
        view_playable_div = self._itemobj.find(lambda tag:tag.name == 'div' and 'data-view-playable' in tag.attrs)
        if view_playable_div:
            return json.loads(view_playable_div.attrs['data-view-playable'])['items'][0]
        else:
            return {}

    @property
    def _data(self):
        return self._playable.get('data', {})

    @property
    def _audio_data(self):
        return self._data.get('audio_file', {})

    @property
    def _on_air_toggle(self):
        dataview = self._itemobj.attrs.get('data-view-on-air-toggle')
        if dataview:
            return json.loads(dataview)

    @property
    def _on_air_status(self):
        toggle = self._on_air_toggle
        if toggle:
            start = toggle.get('startTime').split('+')
            end   = toggle.get('endTime').split('+')
            td    = timedelta(hours=int(start[1][:2]))
            try:
                start = strptime(start[0], '%Y-%m-%dT%H:%M:%S') - td
                end   = strptime(end[0],   '%Y-%m-%dT%H:%M:%S') - td
                return start, end
            except (ValueError, TypeError) as e:
                pass
        return None, None

    @property
    def type(self):
        t = self._playable.get('type')
        if t == 'clip':
            return 'segment'
        if t == 'broadcast_episode':
            return 'broadcast'
        else:
            return t

    def id(self):
        if self._playable:
            return str(self._playable.get('source_id'))

    @property
    def path(self):
        return

    @property
    def title(self):
        if self._data:
            return self._data.get('title')
        else:
            start, end = self._on_air_status
            localtime = datetime.utcnow()
            title = None

            if start and end and self._on_air_toggle:
                if start > localtime:
                    title = self._itemobj.find(class_=self._on_air_toggle.get('upcomingEl')[1:])
                if start < localtime and end > localtime:
                    title = self._itemobj.find(class_=self._on_air_toggle.get('onAirEl')[1:])
                if end < localtime:
                    title = self._itemobj.find(class_=self._on_air_toggle.get('offAirEl')[1:])
            elif self._on_air_toggle:
                title = self._itemobj.find(class_=self._on_air_toggle.get('offAirEl')[1:])

            return title.find('span').text if title else None

    @property
    def subtitle(self):
        return self._data.get('subtitle')

    @property
    def textbody(self):
        return None

    @property
    def _itemtime(self):
        if self.subtitle:
            try:
                return time.strptime(self.subtitle, '%d %B %Y')
            except ValueError:
                return

    @property
    def date(self):
        if self._itemtime:
            return time.strftime(DATE_FORMAT, self._itemtime)

    @property
    def year(self):
        if self._itemtime:
            return self._itemtime[0]

    @property
    def aired(self):
        return self.date

    @property
    def duration(self):
        if self._audio_data:
            return round(self._audio_data.get('duration', 0))
        elif self._data:
            return round(self._data.get('duration', 0))

    @property
    def url(self):
        if self._data and self._data.get('timestamp'):
            return f"https://ondemand.rrr.org.au/getclip?bw=h&l={self.duration}&m=r&p=1&s={self._data.get('timestamp')}"
        elif self._audio_data and self._audio_data.get('path'):
            return self._audio_data.get('path')
        else:
            start, end = self._on_air_status
            localtime = datetime.utcnow()

            if start and end:
                if start < localtime and end > localtime:
                    return 'https://ondemand.rrr.org.au/stream/ws-hq.m3u'

    @property
    def thumbnail(self):
        if self._data:
            return self._data.get('image', {}).get('path')
        else:
            img = self._itemobj.find(class_='audio-summary__image')
            if img:
                return img.attrs.get('data-src')

    def attributes(self):
        return {
            'title':     self.title,
            'subtitle':  self.subtitle,
            'textbody':  self.textbody,
            'date':      self.date,
            'year':      self.year,
            'aired':     self.aired,
            'duration':  self.duration,
            'url':       self.url,
            'thumbnail': self.thumbnail,
        }


class ProgramBroadcast(PlayableResource):
    '''
      <div data-view-playable='
        {
          "component":"episode_player",
          "formattedDuration":"02:00:00",
          "shareURL":"https://www.rrr.org.au/explore/programs/the-international-pop-underground/episodes/22347-the-international-pop-underground-19-october-2022",
          "sharedMomentBaseURL":"https://www.rrr.org.au/shared/broadcast-episode/22347",
          "items":[
            {
              "type":"broadcast_episode",
              "source_id":22347,
              "player_item_id":269091,
              "data":{
                "title":"The International Pop Underground – 19 October 2022",
                "subtitle":"19 October 2022",
                "timestamp":"20221019200000",
                "duration":7200,
                "platform_id":1,
                "image":{
                  "title":"International Pop Underground program image"
                  "path":"https://cdn-images-w3.rrr.org.au/81wyES6vU8Hyr8MdSUu_kY6cBGA=/300x300/https://s3.ap-southeast-2.amazonaws.com/assets-w3.rrr.org.au/assets/041/aa8/63b/041aa863b5c3655493e6771ea91c13bb55e94d24/International%20Pop%20Underground.jpg"
                }
              }
            }
          ]
        }"
    '''



class ProgramBroadcastSegment(PlayableResource):
    '''
      <div data-view-playable='
        {
          "component": "player_buttons",
          "size": "normal",
          "items": [
            {
              "type": "clip",
              "source_id": 3021,
              "player_item_id": 270803,
              "data": {
                "title": "International Pop Underground: Guatemalan Cellist/Songwriter Mabe Fratti Seeks Transcendence",
                "subtitle": "19 October 2022",
                "platform_id": 1,
                "timestamp": "20221019211747",
                "duration": 1097,
                "image": {
                  "title": "Mabe Fratti",
                  "path": "https://cdn-images-w3.rrr.org.au/1v6kamv_8_4xheocBJCa6FKZY_8=/300x300/https://s3.ap-southeast-2.amazonaws.com/assets-w3.rrr.org.au/assets/3a7/61f/143/3a761f1436b97a186be0cf578962436d9c5404a8/Mabe-Fratti.jpg"
                }
              }
            }
          ]
        }
      '><div class="d-flex">
    '''



class ProgramBroadcastTrack(Resource, ExternalMedia):
    _media = {}

    def id(self):
        if self.media:
            return self.media
        else:
            return re.sub(r'[\[\]\{\}\(\)\.\/\\,\:\;]', '', f'{self.artist}-{self.title}'.lower().replace(' ', '-'))

    @property
    def type(self):
        if self.media:
            return self._media.get('plugin')
        else:
            return super().type

    @property
    def artist(self):
        return self._itemobj.find(class_='audio-summary__track-artist').text.strip()

    @property
    def broadcast_artist(self):
        params = { 'q': self.artist }
        return '/tracks/search?' + urlencode(params)

    @property
    def broadcast_track(self):
        params = { 'q': f'{self.title} - {self.artist}' }
        return '/tracks/search?' + urlencode(params)

    @property
    def title(self):
        return self._itemobj.find(class_='audio-summary__track-title').text.strip()

    def _get_media(self):
        if not self._media:
            href = self._itemobj.find(class_='audio-summary__track-title').attrs.get('href')
            if href:
                self._media = self.media_items([{'src': href}], fetch_album_art=True)[0]
        return self._media if self._media else {}

    @property
    def media(self):
        return self._get_media().get('media_id')

    @property
    def thumbnail(self):
        return self._get_media().get('thumbnail')

    @property
    def background(self):
        return self._get_media().get('background')

    @property
    def duration(self):
        return self._get_media().get('duration')

    def attributes(self):
        attr = {
            'artist':    self.artist,
            'title':     self.title,
        }
        if self.thumbnail:
            attr['thumbnail'] = self.thumbnail
        if self.background:
            attr['background'] = self.background
        if self.duration:
            attr['duration'] = self.duration
        return attr

    def links(self):
        return {
            'broadcast_artist': self.broadcast_artist,
            'broadcast_track': self.broadcast_track,
        }


class BroadcastCollection(Resource):
    @property
    def type(self):
        return 'broadcast_index'

    def id(self):
        return self.path

    @property
    def _playable(self):
        view_playable_div = self._itemobj.find(lambda tag:tag.name == 'div' and 'data-view-playable' in tag.attrs)
        if view_playable_div:
            return json.loads(view_playable_div.attrs['data-view-playable'])['items'][0]
        else:
            return {}

    @property
    def _data(self):
        return self._playable.get('data', {})

    @property
    def duration(self):
        if self._data:
            return round(self._data.get('duration'))

    @property
    def title(self):
        return self._itemobj.find(class_='card__title').text

    @property
    def thumbnail(self):
        programimage = self._itemobj.find(class_='card__background-image')
        if programimage:
            programimagesrc = re.search(r"https://[^']+", programimage.attrs.get('style'))
            if programimagesrc:
                return programimagesrc[0]

        programimage = self._itemobj.find(class_='scalable-image__image')
        if programimage:
            return programimage.attrs.get('data-src')

    @property
    def textbody(self):
        cardbody = self._itemobj.find(class_='card__meta')
        if cardbody:
            return cardbody.text

    def attributes(self):
        return {
            'title':     self.title,
            'textbody':  self.textbody,
            'thumbnail': self.thumbnail,
            'duration':  self.duration,
        }



class AudioItem:

    @classmethod
    def factory(cls, item):
        cardbody = item.find(class_='card__body')
        if cardbody:
            textbody = cardbody.text
        else:
            cardbody = item.find(class_='card__meta')
            if cardbody:
                textbody = cardbody.text
            else:
                textbody = ''

        view_playable_div = item.find(lambda tag:tag.name == 'div' and 'data-view-playable' in tag.attrs)
        if view_playable_div:
            view_playable = view_playable_div.attrs['data-view-playable']
            itemobj = json.loads(view_playable)['items'][0]

            if 'data-view-account-toggle' in view_playable_div.parent.parent.attrs:
                itemobj['subscription_required'] = True
            else:
                itemobj['subscription_required'] = False

            if   itemobj['type'] == 'clip':
                obj = Segment(item, itemobj, textbody)
            elif itemobj['type'] == 'broadcast_episode':
                obj = Broadcast(item, itemobj, textbody)
            elif itemobj['type'] == 'audio_archive_item':
                obj = Archive(item, itemobj, textbody)
            elif itemobj['type'] == 'podcast_episode':
                obj = Podcast(item, itemobj, textbody)
            else:
                obj = AudioItem(item, itemobj, textbody)
            return obj.to_dict()
        else:
            # Should we _also_ have a NonPlayable AudioItem ?
            return None


    def __init__(self, item, itemobj, textbody):
        self._item = item
        self._itemobj = itemobj
        self._itemdata = itemobj['data']
        self.textbody = textbody

    @property
    def resource_path(self):
        card_anchor = self._item.find(class_='card__anchor')
        if card_anchor:
            return Scraper.resource_path_for(card_anchor.attrs['href'])

    @property
    def type(self):
        return self.__class__.__name__.lower()

    @property
    def subscription_required(self):
        return self._itemobj.get('subscription_required')

    @property
    def id(self):
        return str(self._itemobj['source_id'])

    @property
    def title(self):
        return self._itemdata['title']

    @property
    def subtitle(self):
        return self._itemdata['subtitle']

    @property
    def _itemtime(self):
        return time.strptime(self._itemdata['subtitle'], '%d %B %Y')

    @property
    def date(self):
        return time.strftime(DATE_FORMAT, self._itemtime)

    @property
    def year(self):
        return self._itemtime[0]

    @property
    def aired(self):
        return self.date

    @property
    def duration(self):
        duration = self._itemobj.get('data', {}).get('duration', {})
        if not duration:
            audio_file = self._itemdata.get('audio_file')
            if audio_file:
                duration = audio_file['duration']
            else:
                duration = 0
        return round(duration)

    @property
    def thumbnail(self):
        return self._itemdata['image']['path'] if 'image' in self._itemdata.keys() else ''

    @property
    def url(self):
        audio_file = self._itemdata.get('audio_file')
        if audio_file:
            return audio_file['path']
        else:
            ts = self._itemdata['timestamp']
            l = self.duration
            return 'https://ondemand.rrr.org.au/getclip?bw=h&l={}&m=r&p=1&s={}'.format(l, ts)

    def to_dict(self):
        item = {
            'type':          self.type,
            'id':            self.id,
            'attributes': {
                'title':         self.title,
                'subtitle':      self.subtitle,
                'textbody':      self.textbody,
                'date':          self.date,
                'year':          self.year,
                'aired':         self.aired,
                'duration':      self.duration,
                'url':           self.url,
                'thumbnail':     self.thumbnail,
            },
            'links': {
                'self': self.resource_path,
            }
        }
        if self.subscription_required:
            item['links']['subscribe'] = '/subscribe'
        return item


class Archive(AudioItem):
    ''

class Broadcast(AudioItem):
    ''

class Segment(AudioItem):
    ''

class Podcast(AudioItem):
    ''


if __name__ == "__main__":
    print(json.dumps(Scraper.call(sys.argv[1])))
