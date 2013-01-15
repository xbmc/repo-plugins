'''
    academicearth.scraper
    ~~~~~~~~~~~~~~~~~~~~~

    This module contains some functions which do the website scraping for the
    API module. You shouldn't have to use this module directly.

    This module is meant to emulate responses from a "virtual" API server. All
    website scraping is handled in this module, and clean dict responses are
    returned. The `api` module, acts as a python client library for this
    module's API.
'''
import re
import urllib
import urlparse
from BeautifulSoup import BeautifulSoup as BS


BASE_URL = 'http://www.academicearth.org'
def _url(path):
    '''Returns a full url for the given path'''
    return urlparse.urljoin(BASE_URL, path)


def get(url):
    '''Performs a GET request for the given url and returns the response'''
    conn = urllib.urlopen(url)
    resp = conn.read()
    conn.close()
    return resp


def _html(url):
    '''Downloads the resource at the given url and parses via BeautifulSoup'''
    return BS(get(url), convertEntities=BS.HTML_ENTITIES)


def make_showall_url(url):
    '''Takes an api url and appends info to the path to force the page to
    return all entries instead of paginating.
    '''
    if not url.endswith('/'):
        url += '/'
    return url + 'page:1/show:1000'


class University(object):

    listing_url = make_showall_url(_url('universities'))

    @classmethod
    def get_universities_partial(cls):
        '''Returns a list of universities available on the website.'''
        html = _html(cls.listing_url)

        parent = html.find('div', {'class': 'lectureVideosIndex'}).div
        unis = parent.findAll('div')

        return [{
            'name': uni.findAll('a')[-1].string.strip(),
            'url': _url(uni.a['href']),
            'icon': uni.img['src'],
        } for uni in unis]

    @classmethod
    def from_url(cls, url):
        '''Returns metadata for a university parsed from the given url'''
        html = _html(make_showall_url(url))
        name = cls.get_name(html)
        desc = cls.get_description(html)
        courses = cls.get_courses(html)
        lectures = cls.get_lectures(html)

        return {
            'name': name,
            'courses': courses,
            'lectures': lectures,
            'description': desc,
        }

    @staticmethod
    def get_name(html):
        return html.find('div', {'class': 'title'}).h1.text

    @staticmethod
    def get_description(html):
        desc_nodes = html.find('div', {'class': 'courseDetails'}).findAll('span')
        return '\n'.join(node.text.strip() for node in desc_nodes)

    @staticmethod
    def get_courses(html):
        return _get_courses_or_lectures('course', html)

    @staticmethod
    def get_lectures(html):
        return _get_courses_or_lectures('lecture', html)


class Subject(object):

    listing_url = _url('subjects')

    @classmethod
    def get_subjects_partial(cls):
        '''Returns a list of subjects for the website. Each subject is a dict with
        keys of 'name' and 'url'.
        '''
        html = _html(cls.listing_url)
        subjs = html.findAll('a',
            {'href': lambda attr_value: attr_value.startswith('/subjects/')
                                        and len(attr_value) > len('/subjects/')})

        # subjs will contain some duplicates so we will key on url
        items = []
        urls = set()
        for subj in subjs:
            url = _url(subj['href'])
            if url not in urls:
                urls.add(url)
                items.append({
                    'name': subj.string,
                    'url': url,
                })

        # filter out any items that didn't parse correctly
        return [item for item in items if item['name'] and item['url']]

    @classmethod
    def from_url(cls, url):
        '''Returns metadata for a subject parsed from the given url'''
        html = _html(make_showall_url(url))
        name = cls.get_name(html)
        desc = cls.get_description(html)
        courses = cls.get_courses(html)
        lectures = cls.get_lectures(html)

        return {
            'name': name,
            'courses': courses,
            'lectures': lectures,
            'description': desc,
        }

    @staticmethod
    def get_name(html):
        return html.find('article').h1.text

    @staticmethod
    def get_description(html):
        return html.find('article').p.text

    @staticmethod
    def get_courses(html):
        return _get_courses_or_lectures('course', html)

    @staticmethod
    def get_lectures(html):
        return _get_courses_or_lectures('lecture', html)


class Speaker(object):

    listing_url = make_showall_url(_url('speakers'))

    @classmethod
    def get_speakers_partial(cls):
        '''Returns a list of speakers available on the website.'''
        html = _html(cls.listing_url)
        speakers = html.findAll('div', {'class': 'blue-hover'})
        return [{
            'name': spkr.div.string.strip(),
            'url': _url(spkr.a['href']),
        } for spkr in speakers]

    @classmethod
    def from_url(cls, url):
        '''Returns metadata for a speaker parsed from the given url'''
        html = _html(make_showall_url(url))
        name = cls.get_name(html)
        courses = cls.get_courses(html)
        lectures = cls.get_lectures(html)

        return {
            'name': name,
            'courses': courses,
            'lectures': lectures,
        }

    @staticmethod
    def get_name(html):
        return html.find('div', {'class': 'title'}).h1.text

    @staticmethod
    def get_courses(html):
        return _get_courses_or_lectures('course', html)

    @staticmethod
    def get_lectures(html):
        return _get_courses_or_lectures('lecture', html)


class Course(object):

    @classmethod
    def from_url(cls, url):
        html = _html(make_showall_url(url))
        lectures = cls.get_lectures(html)
        name = cls.get_name(html)
        return {
            'lectures': lectures,
            'name': name,
        }

    @staticmethod
    def get_name(html):
        return html.find('section', {'class': 'pagenav'}).span.text

    @staticmethod
    def get_lectures(html):
        return _get_courses_or_lectures('lecture', html)


class Lecture(object):

    @classmethod
    def from_url(cls, url):
        html = _html(url)
        name = cls.get_name(html)
        youtube_id = cls.parse_youtube_id(html)
        return {
            'name': name,
            'youtube_id': youtube_id
        }

    @staticmethod
    def get_name(html):
        return html.find('section', {'class': 'pagenav'}).span.text

    @staticmethod
    def parse_youtube_id(html):
        url = html.find('a',
                        href=lambda h: h.startswith('http://www.youtube.com'))
        return url['href'].split('=')[1]


def _get_courses_or_lectures(class_type, html):
    '''class_type can be 'course' or 'lecture'.'''
    nodes = html.findAll('div', {'class': class_type})

    items = [{
        'name': node.h3.text,
        'url': _url(node.a['href']),
        'icon': node.img['src'],
        #'university':  '',
        #'speaker': '',
    } for node in nodes]

    return items
