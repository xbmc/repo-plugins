import simplejson
import urllib2
from datetime import datetime

API_URL = 'http://www.hardwareclips.com/api/xbmc/'

USER_AGENT = 'XBMC Addon: plugin.video.hwclips'

DEBUG = False

API_RESPONSE_TYPE_FOLDERS = u'folders'
API_RESPONSE_TYPE_VIDEOS = u'videos'
API_RESPONSE_TYPE_VIDEO = u'videoDetail'
API_RESPONSE_TYPE_ERROR = u'error'


class Api(object):

    def __init__(self, pref_lang='en', per_page=50):
        log('Api initialized with pref_lang: %s' % pref_lang)
        lang_suffix = {'de': '',
                       'en': '_en'}
        self.description_tag = 'description' + lang_suffix[pref_lang]
        self.name_tag = 'name' + lang_suffix[pref_lang]
        self.per_page = per_page

    def get_list(self, path=None, page=1):
        log('get_list started with path: %s page: %s' % (path, page))
        if int(page) > 1 and path:
            path = '%s/%s/%s' % (path, self.per_page,
                                 (page - 1) * self.per_page)
        if not path:
            path = 'root'
        log('get_list started with path: %s' % path)
        type, data, num_entries = self.__api_request(path)
        if type == API_RESPONSE_TYPE_FOLDERS:
            entries = self.__format_folders(data)
        elif type == API_RESPONSE_TYPE_VIDEOS:
            entries = self.__format_videos(data)
        else:
            raise Exception('Unexpected return type from api')
        log('get_list finished with %d entries' % len(entries))
        num_pages = num_entries / self.per_page + 1
        return type, entries, num_pages

    def get_video(self, video_id):
        log('get_list started with video_id: %s' % video_id)
        path = 'video/%d' % int(video_id)
        type, data, num_entries = self.__api_request(path)
        if type == API_RESPONSE_TYPE_VIDEO:
            entry = self.__format_video(data)
        elif type == API_RESPONSE_TYPE_ERROR:
            raise Exception('api returned error type')
        else:
            raise Exception('Unexpected return type from api')
        log('get_list finished')
        return entry

    def __api_request(self, path):
        log('__api_request started with path: %s' % path)
        url = API_URL + path
        log('__api_request using url: %s' % url)
        req = urllib2.Request(url)
        req.add_header('User-Agent', USER_AGENT)
        response = urllib2.urlopen(req).read()
        log('__api_request got response with %d bytes' % len(response))
        json = simplejson.loads(response)
        num_entries = 0
        if API_RESPONSE_TYPE_VIDEOS in json.keys():
            type = API_RESPONSE_TYPE_VIDEOS
            num_entries = int(json['num'])
        elif API_RESPONSE_TYPE_FOLDERS in json.keys():
            type = API_RESPONSE_TYPE_FOLDERS
        elif API_RESPONSE_TYPE_VIDEO in json.keys():
            type = API_RESPONSE_TYPE_VIDEO
        else:
            raise Exception('Unexpected return type from api')
        data = json[type]
        if DEBUG:
            log('DEBUG: type: %s' % type)
            if isinstance(data, list):
                log('DEBUG: list: %s' % simplejson.dumps(data[0], indent=1))
            else:
                log('DEBUG: item: %s' % simplejson.dumps(data, indent=1))
        log('__api_request finished with type: %s' % type)
        return type, data, num_entries

    def __format_folders(self, items):
        return [{'name': i.get(self.name_tag, i['name']),
                 'id': i.get('ID', ''),
                 'description': i.get(self.description_tag,
                                      i.get('description', '')),
                 'image': i.get('logo', ''),
                 'website': i.get('www', ''),
                 'gurl': i.get('gurl', ''),
                 'path': i['apiPath'],
                 'count': i.get('videoCount', '0'),
                } for i in items]

    def __format_videos(self, items):
        return [{'name': i['title'],
                 'id': i['ID'],
                 'image': i.get('previewImage', ''),
                 'keywords': i['keyword'].split(),
                 'username': i['username'],
                 'date': self.__format_date(i['addtime']),
                 'year': self.__format_year(i['addtime']),
                 'description': i.get('description', ''),
                 'gurl': i.get('gurl', ''),
                 'views': i.get('views', '0'),
                 'votes': i.get('ratingCount', '0'),
                 'rating': i.get('averageRating', '0.0'),
                 'is_hd': i.get('isHD', False),
                 'duration': self.__format_duration(i.get('duration', '0.0')),
                 'language': i.get('language', ''),
                } for i in items]

    def __format_video(self, item):
        return {'full_path': item['filePath']}

    def __format_date(self, timestamp):
        return datetime.fromtimestamp(int(timestamp)).strftime('%d.%m.%Y')

    def __format_year(self, timestamp):
        return int(datetime.fromtimestamp(int(timestamp)).strftime('%Y'))

    def __format_duration(self, duration):
        seconds = int(float(duration))
        minutes = seconds // 60
        seconds %= 60
        return '%02i:%02i' % (minutes, seconds)


def log(msg):
    print 'HWCLIPS.com scraper: %s' % msg
