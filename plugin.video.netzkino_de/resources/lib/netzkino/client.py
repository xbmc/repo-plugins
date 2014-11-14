import json
import urllib
import urllib2

__author__ = 'bromix'


class Client(object):
    def __init__(self):
        self._opener = urllib2.build_opener()
        self._opener.addheaders = [('User-Agent', 'Dalvik/1.6.0 (Linux; U; Android 4.4.4; GT-I9100 Build/KTU84Q)'),
                                   ('Host', 'api.netzkino.de.simplecache.net'),
                                   ('Connection', 'Keep-Alive')]
        pass

    def _execute(self, path, params=None):
        """
        [HOME]
        http://api.netzkino.de.simplecache.net/capi-2.0a/index.json?d=android-phone&l=de-DE&g=DE

        [CATEGORY]
        http://api.netzkino.de.simplecache.net/capi-2.0a/categories/5?d=android-phone&l=de-DE&g=DE
        :param params:
        :return:
        """

        # prepare the params
        if not params:
            params = {}
            pass
        params['d'] = 'android-tablet'
        params['l'] = 'de-DE'
        params['g'] = 'DE'

        base_url = 'http://api.netzkino.de.simplecache.net/capi-2.0a/'
        url = base_url + path.strip('/')
        url = url + '?' + urllib.urlencode(params)

        content = self._opener.open(url)
        return json.load(content, encoding='utf-8')

    def get_home(self):
        """
        Main entry point to get data of netzkino.de
        :return:
        """
        return self._execute('index.json')

    def get_categories(self):
        """
        Returns directly the 'categories'
        :return:
        """
        json_data = self.get_home()
        return json_data.get('categories', {})

    def get_category_content(self, category_id):
        """
        Returns the content of the given category
        :param category_id:
        :return:
        """
        return self._execute('categories/%s' % str(category_id))
        pass

    def search(self, text):
        """
        Search the given text
        :param text:
        :return:
        """
        return self._execute('search', params={'q': text})

    def get_video_url(self, stream_id):
        """
        Returns the url for the given id
        :param stream_id:
        :return:
        """
        content = urllib2.urlopen('http://www.netzkino.de/adconf/android-new.php')
        json_data = json.load(content)
        streamer_url = json_data.get('streamer', 'http://netzkino_and-vh.akamaihd.net/i/')
        return streamer_url+stream_id+'.mp4/master.m3u8'

    pass
