import urlparse
import requests
from BeautifulSoup import BeautifulSoup as BS
import getflashvideo



BASE_URL = 'http://www.classiccinemaonline.com'

def _url(path):
    return urlparse.urljoin(BASE_URL, path)

def get_categories():
    '''Returns a list of the main categories for the website.'''
    html = BS(requests.get(BASE_URL).content)
    ul = html.find('ul', {'class': 'gf-menu l1 '})
    lis = ul.findAll('li', recursive=False)
    return [li.a.text for li in lis[1:-1]]

def get_genres_flat(category):
    '''Returns the available genres as a flat list. Each item in the list
    is a tuple, (genre, url).
    '''
    html = BS(requests.get(BASE_URL).content, convertEntities=BS.HTML_ENTITIES)
    links = html.findAll('a', {'class': 'item'})

    # Will throw StopIteration if not found
    link = (link for link in links if link.text == category).next()
    menu = link.findNextSibling('div')

    return [(a.text, _url(a['href'])) for a in menu.findAll('a')]

def get_films(genre_url):
    '''Returns a list of (film_title, url) for the given genre url'''
    html = BS(requests.post(genre_url, {'limit': 0}).content)
    tds = html.findAll('td', {'class': 'list-title'})
    return [(td.text, _url(td.a['href'])) for td in tds]

def get_film(film_url):
    '''Returns a dict of info for a given film url'''
    src = requests.get(film_url).content
    url = getflashvideo.get_flashvideo_url(src)
    html = BS(src, convertEntities=BS.HTML_ENTITIES)
    img = html.find('img', src=lambda src: src.startswith('/images/posters/'))
    return {
        'title': html.find('h2').text,
        'url': url,
        'thumbnail': _url(img['src']),
    }

