'''
    academicearth.scraper
    ~~~~~~~~~~~~~~~~~~~~~

    This module contains some functions which do the website scraping for the
    API module. You shouldn't have to use this module directly.
'''
import re
from urllib2 import urlopen
from urlparse import urljoin
from BeautifulSoup import BeautifulSoup as BS


BASE_URL = 'http://www.academicearth.org'
def _url(path):
    '''Returns a full url for the given path'''            
    return urljoin(BASE_URL, path)


def get(url):
    '''Performs a GET request for the given url and returns the response'''
    conn = urlopen(url)
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
    return url + 'page:1/show:500'


def get_subjects():
    '''Returns a list of subjects for the website. Each subject is a dict with
    keys of 'name' and 'url'.
    '''
    url = _url('subjects')
    html = _html(url)
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


def get_subject_metadata(subject_url):
    '''Returns metadata for a subject parsed from the given url'''
    html = _html(make_showall_url(subject_url))
    name = get_subject_name(html)
    courses = get_courses(html)
    lectures = get_lectures(html)
    desc = get_subject_description(html)

    return {
        'name': name,
        'courses': courses,
        'lectures': lectures,
        'description': desc,
    }


def get_subject_name(html):
    return html.find('article').h1.text


def get_course_name(html):
    return html.find('section', {'class': 'pagenav'}).span.text


def get_lecture_name(html):
    return html.find('section', {'class': 'pagenav'}).span.text


def get_subject_description(html):
    desc_nodes = html.find('article').findAll('span')
    return '\n'.join(node.text.strip() for node in desc_nodes)
    

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


def get_lectures(html):
    return _get_courses_or_lectures('lecture', html)


def get_courses(html):
    return _get_courses_or_lectures('course', html)


def get_course_metadata(course_url):
    html = _html(make_showall_url(course_url))
    lectures = get_lectures(html)
    name = get_course_name(html)
    return {
        'lectures': lectures,
        'name': name,
    }


def get_lecture_metadata(lecture_url):
    html = _html(lecture_url)
    name = get_lecture_name(html)
    youtube_id = parse_youtube_id(html)
    return {
        'name': name,
        'youtube_id': youtube_id        
    }
    


def parse_youtube_id(html):
    embed = html.find('embed')
    yt_ptn = re.compile(r'http://www.youtube.com/v/(.+?)\?')
    match = yt_ptn.search(embed['src'])
    if match:
        return match.group(1)
    return None
