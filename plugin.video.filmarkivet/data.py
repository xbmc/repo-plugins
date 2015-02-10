# -*- coding: utf-8 -*-

'''
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''


import re, string, traceback, itertools

import BeautifulSoup
html_decode = lambda string: BeautifulSoup.BeautifulSoup(string, convertEntities=BeautifulSoup.BeautifulSoup.HTML_ENTITIES).contents[0]

import CommonFunctions
parseDOM = CommonFunctions.parseDOM
getParameters = CommonFunctions.getParameters

import requests

session = requests.session()
session.headers['User-Agent'] = 'xbmc.org'


FILMARKIVET_BASE = "http://www.filmarkivet.se/sv/"
MOVIES_PER_PAGE = 20


def make_category_url(url):
	try:
		spos = url.find('filter')
		if spos != -1:
			epos = url.find('&', spos)
			return '/category/%s/%d' % (url[spos:epos], 1)
	except:
		return '/categories'
	return '/categories'


SUB_CATEGORIES = {'categories':0, 'years':1, 'provinces':2, 'cities':3}


def parse_categories(subcat):
	if subcat not in SUB_CATEGORIES.keys():
		return None

	try:
		url = FILMARKIVET_BASE + "Sok/?quicksearch=sorted"
		html = session.get(url).text
		html = parseDOM(html, 'div', {'class':'result-body'})
		html = parseDOM(html, 'div', {'class':'unit size1of5 filter-col'})

		# Parse results to a list where each element is the sub category (catories, years, provinces, cities).
		categories = parseDOM(html, 'ul')
		category = categories[SUB_CATEGORIES[subcat]]
		elements = parseDOM(category, 'li')
		elements = elements[1:]		# Drop first element that contains the category title

		titles = parseDOM(elements, 'a')
		titles = map(html_decode, titles)
		urls = parseDOM(elements, 'a', ret='href')
		urls = [make_category_url(u) for u in urls]

		result = zip(titles, urls, itertools.repeat(''), itertools.repeat(''))

		return result
	except:
		return None


def parse_category(arg, page=1):
	try:
		url = FILMARKIVET_BASE + 'Sok/?quicksearch=sorted&%s&page=%d' % (arg, page)
		html = session.get(url).text

		hits = parseHits(html)
		films = parseFilms(html)

		next_url = None
		if page * MOVIES_PER_PAGE < hits:
			next_url = '/category/%s/%d' % (arg, page+1)

		return films, next_url
	except:
		return None, None


def make_theme_url(url):
	try:
		pos = url.find('themeid=')
		if pos != -1:
			return '/theme/%s' % (url[pos+8:])
	except:
		return '/themes'
	return '/themes'


def parse_themes():
	try:
		url = FILMARKIVET_BASE
		html = session.get(url).text
		html = parseDOM(html, 'ul', {'class':'themes'})
		html = parseDOM(html, 'li')

		titles = parseDOM(html, 'a')
		titles = map(html_decode, titles)
		urls = parseDOM(html, 'a', ret='href')
		urls = [make_theme_url(u) for u in urls]
		return zip(titles, urls, itertools.repeat(''), itertools.repeat(''))
	except:
		return None

  
def parse_theme(theme_id, page=1):
	try:
		url = FILMARKIVET_BASE + 'Sok/?themeid=%s&page=%d' % (theme_id, page)
		html = session.get(url).text

		hits = parseHits(html)
		films = parseFilms(html)

		next_url = None
		if page * MOVIES_PER_PAGE < hits:
			next_url = '/theme/%s/%d' % (theme_id, page+1)

		return films, next_url
	except:
		return None, None


def parse_popular(page=1):
	try:
		url = FILMARKIVET_BASE + 'Sok/?quicksearch=popular&page=%d' % page
		html = session.get(url).text

		hits = parseHits(html)
		films = parseFilms(html)

		next_url = None
		if page * MOVIES_PER_PAGE < hits:
			next_url = '/popular/%d' % (page+1)

		return films, next_url
	except:
		return None, None


def parse_recent(page=1):
	try:
		url = FILMARKIVET_BASE + 'Sok/?quicksearch=latest&page=%d' % page
		html = session.get(url).text

		hits = parseHits(html)
		films = parseFilms(html)

		next_url = None
		if page * MOVIES_PER_PAGE < hits:
			next_url = '/recent/%d' % (page+1)

		return films, next_url
	except:
		return None, None

 
def parse_search(search_string, page=1):
	try:
		url = FILMARKIVET_BASE + 'Sok/?q=%s&page=%d' % (search_string, page)
		html = session.get(url).text

		hits = parseHits(html)
		films = parseFilms(html)

		next_url = None
		if page * MOVIES_PER_PAGE < hits:
			next_url = '/search/%s/%d' % (search_string, page+1)

		return films, next_url
	except:
		return None, None


def parseHits(html):
	try:
		h = parseDOM(html, 'div', {'class':'number-of-hits'})
		return int(h[0].split('</span>')[1])
	except:
		print 'failed to get hits.'
	return 0


def make_film_url(url):
	try:
		params = getParameters(url)
		return '/film/' + params['movieid']
	except:
		return '/categories'
	return '/categories'


def parseFilms(html):
	html = parseDOM(html, 'ul', {'class':'search-result current'})
	html = parseDOM(html, 'li')
  
	titles = parseDOM(html, 'a')
	titles = parseDOM(titles, 'h3')
	titles = map(html_decode, titles)

	descs = None
	try:
		descs = parseDOM(html, 'a')
		descs = parseDOM(descs, 'p')
		descs = map(html_decode, descs)
		a = iter(descs)
		descs = [i+' | '+j for i, j in itertools.izip(a, a)]
	except:
	  descs = None

	if descs == None:
		descs = itertools.repeat()
	else:
		a = iter(titles)
		b = iter(descs)
		titles = [i + '  (' + j + ')' for i, j in itertools.izip(a, b)]
 
	urls = parseDOM(html, 'a', ret='href')
	urls = [make_film_url(u) for u in urls]
 
	thumbs = parseDOM(html, 'a')
	thumbs = parseDOM(thumbs, 'img', ret='src')
	thumbs = ['http://www.filmarkivet.se%s' % t for t in thumbs]

	return zip(titles, urls, descs, thumbs)
  
  
def parse_media_url(video_id):
	url = FILMARKIVET_BASE + 'Film/?movieid=%s' % video_id
	html = session.get(url).text
	html = parseDOM(html, 'div', {'class':'moviecontainer'})
	html = parseDOM(html, 'div', {'id':'player'})
	html = parseDOM(html, 'video')
	html = parseDOM(html, 'source', ret='src')
	return html[0]
  
  

