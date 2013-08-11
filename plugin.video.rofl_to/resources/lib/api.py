from urllib2 import urlopen, Request, HTTPError, URLError
import re

from BeautifulSoup import BeautifulSoup

USER_AGENT = 'XBMC Add-on Rofl.to'


class NetworkError(Exception):
    pass


class RoflApi():

    URLS = {
        'en': 'http://clips.rofl.to',
        'de': 'http://videos.rofl.to',
    }

    def __init__(self, language=None):
        if not language or language not in self.URLS:
            language = 'de'
        self.main_url = self.URLS[language]

    def get_sort_methods(self):
        url = self.__build_url()
        tree = self.__get_tree(url)
        parent = tree.find('div', {'id': 'top-bar'})
        sort_methods = []
        for li in parent.ul.findAll('li'):
            sort_method = {
                'title': li.a.contents[-1].strip(),
                'path': self.__pathify(li.a['href']) or 'new-clips',
            }
            sort_methods.append(sort_method)
        return sort_methods

    def get_categories(self):
        url = self.__build_url()
        tree = self.__get_tree(url)
        parent = tree.find('ul', {'class': 'categories'})
        categories = []
        for a in parent.findAll('a'):
            category = {
                'title': a.string.strip(),
                'path': self.__pathify(a['href']),
            }
            categories.append(category)
        return categories

    def get_videos(self, sort_method=None, category=None, page='1'):
        re_length = re.compile(('(?:(?P<mins>\d+) (?:Minute?n?|minutes?), )?'
                                '(?P<secs>\d+) (?:Sekunden?|seconds?)'))
        if category == 'all':
            category = None
        url = self.__build_url(
            sort_method=sort_method,
            category=category,
            page=page,
        )
        tree = self.__get_tree(url)
        videos = []
        for div in tree.findAll('div', {'class': 'container-inner'}):
            m = re.search(re_length, div.a['title'])
            if m:
                d = m.groupdict()
                duration = (
                    int(d.get('mins') or 0) * 60
                    + int(d.get('secs') or 0)
                )
            else:
                duration = 0
            video = {
                'title': div.h2.a.string.strip(),
                'video_id': self.__pathify(div.a['href']),
                'thumb': div.a.img['src'],
                'duration': duration,
            }
            videos.append(video)
        has_next_page = tree.find('a', {'class': 'next'}) is not None

        return videos, has_next_page

    def get_video_url(self, video_id):
        url = '%s/clip/%s' % (self.main_url, video_id)
        tree = self.__get_tree(url)
        return tree.find('div', {'id': 'video-player'})['href']

    def __build_url(self, **kwargs):
        SCHEME = '%(main_url)s/%(sort_method)s/%(unit)s/%(page)d/%(category)s'
        properties = {
            'main_url': self.main_url,
            'sort_method': kwargs.get('sort_method') or 'new-clips',
            'unit': kwargs.get('unit') or 'week',
            'page': int(kwargs.get('page', '1')),
            'category': kwargs.get('category') or '',
        }
        return SCHEME % properties

    def __get_tree(self, url):
        self.log('opening url: %s' % url)
        request = Request(url)
        request.add_header('User-Agent', USER_AGENT)
        try:
            html = urlopen(request).read()
        except HTTPError, error:
            self.log('HTTPError: %s' % error)
            raise NetworkError('HTTPError: %s' % error)
        except URLError, error:
            self.log('URLError: %s' % error)
            raise NetworkError('URLError: %s' % error)
        self.log('got %d bytes' % len(html))
        tree = BeautifulSoup(html, convertEntities=BeautifulSoup.HTML_ENTITIES)
        return tree

    @staticmethod
    def __pathify(link):
        return link.split('/')[-1]

    @staticmethod
    def log(text):
        print 'RoflApi: %s' % repr(text)

if __name__ == '__main__':
    rofl_api = RoflApi()
    sort_methods = rofl_api.get_sort_methods()
    assert sort_methods
    categories = rofl_api.get_categories()
    assert categories
    videos = rofl_api.get_videos()
    assert videos
    video_url = rofl_api.get_video('nice-nice-nice-nice')
    assert video_url
