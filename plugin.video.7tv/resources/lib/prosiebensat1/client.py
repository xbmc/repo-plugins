from resources.lib.kodion import simple_requests as requests, KodionException


class Client(object):
    API_V1 = 1
    API_V2 = 2

    def __init__(self):
        self._device = 'tablet'  # 'phone'
        self._header = {'User-Agent': 'stagefright/1.2 (Linux;Android 4.4.2)',
                        'Accept-Encoding': 'gzip, deflate'}
        self._video_method = 6
        pass

    def set_video_method(self, method):
        """
        :param method: default is '6', '4' should also work. But only since Helix
        :return:
        """
        self._video_method = method
        pass

    def get_homepage(self, version, channel_id):
        result = {}

        try:
            # http://contentapi.sim-technik.de/mega-app/v2/pro7/phone/homepage
            url = "http://contentapi.sim-technik.de/mega-app/v2/%s/%s/homepage" % (channel_id, self._device)
            data = requests.get(url, headers=self._header).json()
            return data
        except:
            # do nothing
            pass

        return result

    def get_video_url(self, video_id):
        result = {}

        try:
            url = 'http://vas.sim-technik.de/video/video.json'
            params = {'clipid': video_id,
                      'app': 'megapp',
                      'method': str(self._video_method)}
            data = requests.get(url, headers=self._header, params=params).json()
            return data
        except:
            # do nothing
            pass

        return result

    def get_new_videos(self, version, format_ids=None):
        if not format_ids:
            format_ids = []
            pass

        result = {}

        format_id_string = ','.join(format_ids)
        format_id_string = '[' + format_id_string + ']'
        url = 'http://contentapi.sim-technik.de/mega-app/v2/tablet/videos/favourites'
        params = {'ids': format_id_string}
        data = requests.get(url, headers=self._header, params=params).json()
        return data

    def get_formats(self, version, channel_id):
        result = {}

        try:
            # http://contentapi.sim-technik.de/mega-app/v2/pro7/phone/format
            url = 'http://contentapi.sim-technik.de/mega-app/v2/%s/%s/format' % (channel_id, self._device)
            data = requests.get(url, headers=self._header).json()
            return data
        except:
            # do nothing
            pass

        return result

    def get_format_content(self, version, channel_id, format_id):
        result = {}

        try:
            # http://contentapi.sim-technik.de/mega-app/v2/pro7/phone/format/show/pro7:789
            url = 'http://contentapi.sim-technik.de/mega-app/v2/%s/%s/format/show/%s:%s' % (
                channel_id,
                self._device,
                channel_id,
                format_id)

            data = requests.get(url, headers=self._header).json()
            return data
        except:
            # do nothing
            pass

        return result

    def get_format_videos(self, version, channel_id, format_id, clip_type='full', page=1, per_page=50):
        result = {}

        try:
            # http://contentapi.sim-technik.de/mega-app/v2/tablet/videos/format/pro7:505?clip_type=full&page=1&per_page=50
            url = 'http://contentapi.sim-technik.de/mega-app/v2/%s/videos/format/%s:%s' % (
                self._device, channel_id, format_id)
            params = {'clip_type': clip_type,
                      'page': str(page),
                      'per_page': str(per_page)}
            data = requests.get(url, headers=self._header, params=params).json()
            return data
        except:
            # do nothing
            pass

        return result

    def search(self, version, query):
        result = {}

        try:
            # http://contentapi.sim-technik.de/mega-app/v2/phone/search?query=halligalli
            url = 'http://contentapi.sim-technik.de/mega-app/v2/tablet/search'
            params = {'query': query}
            data = requests.get(url, headers=self._header, params=params).json()
            return data
        except:
            # do nothing
            pass

        return result