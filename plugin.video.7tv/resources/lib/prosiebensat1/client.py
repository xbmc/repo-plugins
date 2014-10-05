import urllib
import urllib2
import json


class Client(object):
    def __init__(self):
        self._device = 'tablet'  # 'phone'
        self._opener = urllib2.build_opener()
        self._opener.addheaders = [('User-Agent', 'stagefright/1.2 (Linux;Android 4.4.2)')]
        pass

    def get_homepage(self, channel_id):
        result = {}

        try:
            url = "http://contentapi.sim-technik.de/mega-app/v1/%s/%s/homepage" % (channel_id, self._device)
            content = self._opener.open(url)
            data = json.load(content)
            return data
        except:
            # do nothing
            pass

        return result

    def get_video_url(self, video_id):
        result = {}

        try:
            url = "http://vas.sim-technik.de/video/video.json?clipid=%s&app=megapp&method=6" % video_id
            content = self._opener.open(url)
            data = json.load(content)
            return data
        except:
            # do nothing
            pass

        return result

    def get_new_videos(self, format_ids=None):
        if not format_ids:
            format_ids = []
            pass

        result = {}

        format_id_string = ','.join(format_ids)
        format_id_string = '[' + format_id_string + ']'
        url = "http://contentapi.sim-technik.de/mega-app/v1/tablet/videos/favourites?ids=%s" % format_id_string
        content = self._opener.open(url)
        data = json.load(content)

        return data

    def get_format(self, channel_id):
        result = {}

        try:
            """
            http://contentapi.sim-technik.de/mega-app/v1/pro7/tablet/format
            """
            url = "http://contentapi.sim-technik.de/mega-app/v1/%s/%s/format" % (channel_id, self._device)
            content = self._opener.open(url)
            data = json.load(content)
            return data
        except:
            # do nothing
            pass

        return result

    def get_format_background(self, channel_id, format_id):
        try:
            url = "http://contentapi.sim-technik.de/mega-app/v1/%s/%s/format/show/%s:%s" % (channel_id,
                                                                                            self._device,
                                                                                            channel_id,
                                                                                            format_id)

            content = self._opener.open(url)
            data = json.load(content)
            screen = data.get('screen', {})
            screen_objects = screen.get('screen_objects', [])
            for screen_object in screen_objects:
                if screen_object.get('type', '') == 'format_teaser_header_item':
                    return screen_object.get('image_url', u'')
                    pass
                pass
            return data
        except:
            # do nothing
            pass

        return u''

    def get_format_videos(self, channel_id, format_id, clip_type='full', page=1, per_page=50):
        result = {}

        try:
            """
            http://contentapi.sim-technik.de/mega-app/v1/phone/videos/format/pro7:203702?clip_type=
            full&page=2&per_page=50
            """
            url = "http://contentapi.sim-technik.de/mega-app/v1/%s/videos/format/%s:%s?clip_type=%s&page=%d&per_page=%d" % (
                self._device,
                channel_id,
                format_id,
                clip_type,
                page,
                per_page)

            content = self._opener.open(url)
            data = json.load(content)
            return data
        except:
            # do nothing
            pass

        return result

    def has_more_videos(self, channel_id, format_id, clip_type='full', current_page=1, per_page=50):
        next_page = current_page + 1
        json_data = self.get_format_videos(channel_id, format_id, clip_type, next_page, per_page)
        objects = json_data.get('objects', [])
        return len(objects) > 0

    def search(self, query):
        result = {}

        try:
            url = "http://contentapi.sim-technik.de/mega-app/v1/tablet/search?query=%s" % (urllib.quote(query))
            content = self._opener.open(url)
            data = json.load(content)
            return data
        except:
            # do nothing
            pass

        return result