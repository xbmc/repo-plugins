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

from bs4 import BeautifulSoup
import lib.webget
import requests
import re

class Filmarkivet(object):
	MOVIES_PER_PAGE = 50

	MAIN_MENU = [{'mode': 'categories', 'title': 30010},
				 {'mode': 'letters', 'title': 30011},
				 {'mode': 'themes', 'title': 30012},
				 {'mode': 'search', 'title': 30023}]

	class ListItem(object):
		def __init__(self, title, url, description, icon):
			self.title = title
			self.url = url
			self.description = description
			self.icon = icon
			self.playable = False
			self.year = None
			self.duration = None


	def __init__(self, info):
		self.info = info
		self.webget = lib.webget.WebGet(info.cache_file)
		self.movies_regex = re.compile('.*Visar.*av (.*) filmer')
		self.meta_regex = re.compile('(\d+) / (\d+) min')

	def __url_for(self, url):
		return 'plugin://{}{}'.format(self.info.id, url)

	def get_mainmenu(self):
		return [self.ListItem(self.info.trans(item['title']), self.__url_for('?mode={}'.format(item['mode'])), '', '') for item in self.MAIN_MENU]

	def mode_url(self, mode):
		return 'plugin://{}?mode={}'.format(self.info.id, mode)

	def get_categories(self):
		html = self.webget.getURL('/')
		soup = BeautifulSoup(html, 'html.parser')
		soup = soup.find('ul', {'class': 'site-nav-menu'})
		lists = soup.find_all('ul')
		items = lists[0].find_all('li')
		mode_url = self.mode_url('category')
		return [self.ListItem(item.a.string, '{}&url={}'.format(mode_url, item.a['href']), '', '') for item in items[1:]]

	def __get_range(self, soup):
		try:
			soup = soup.find('span', {'id': 'pageSpan'})
			m_range = soup.string.split('-')
			t = soup.parent.get_text().strip()
			match = self.movies_regex.match(t)
			return [int(m_range[0]), int(m_range[1])], int(match.group(1))
		except:
			return None, None

	def get_url_movies(self, url, mode, page=1, limit=False):
		get_url = url
		if limit:
			get_url += '{}limit={}&pg={}'.format('?' if url.rfind('?') < 0 else '&', self.MOVIES_PER_PAGE, page)
		html = self.webget.getURL(get_url)
		soup = BeautifulSoup(html, 'html.parser')
		_range, range_max = self.__get_range(soup)
		soup = soup.find('div', {'id': 'list'})
		movies = soup.find_all('a', {'class': 'item'})
		result = []
		mode_url = self.mode_url('watch')
		for movie in movies:
			title = movie.h3.contents[0].strip()
			movie_url = '{}&url={}'.format(mode_url, requests.utils.quote(movie['href'].replace('#038;', '')))
			meta = movie.h3.span.string.strip()
			desc = u'{} ({})'.format(movie.p.string.strip(), meta)
			img = movie.figure.img['src']
			li = self.ListItem(title, movie_url, desc, img)
			li.playable = True
			try:
				match = self.meta_regex.match(meta)
				if match:
					li.year = int(match.group(1)),
					li.duration = int(match.group(2)) * 60
			except:
				pass
			result.append(li)
		if _range[1] < range_max:
			next_url = '{}&url={}&page={}'.format(self.mode_url(mode), requests.utils.quote(url), page + 1)
			result.append(self.ListItem(self.info.trans(30001), next_url, None, None))
		return result

	def get_letters(self):
		mode_url = self.mode_url('letter')
		return [self.ListItem(l, u'{}&l={}'.format(mode_url, l), '', '') for l in u'ABCDEFGHIJKLMNOPQRSTUVWXYZÅÄÖ']

	def get_letter_movies(self, letter):
		html = self.webget.getURL('/filmer-a-o/')
		soup = BeautifulSoup(html, 'html.parser')
		soup = soup.find('section', {'class': 'block', 'id': letter.lower()})
		soup = soup.find('ul', {'class': 'alphabetical'})
		movies = soup.find_all('a')
		mode_url = self.mode_url('watch')
		result = []
		for movie in movies:
			title = movie.contents[0].strip()
			url = '{}&url={}'.format(mode_url, requests.utils.quote(movie['href']))
			li = self.ListItem(title, url, None, None)
			li.playable = True
			result.append(li)
		return result

	def get_themes(self):
		html = self.webget.getURL('/')
		soup = BeautifulSoup(html, 'html.parser')
		soup = soup.find('ul', {'class': 'site-nav-menu'})
		lists = soup.find_all('ul')
		items = lists[1].find_all('li')
		mode_url = self.mode_url('theme')
		return [self.ListItem(item.a.string, '{}&url={}'.format(mode_url, requests.utils.quote(item.a['href'])), '', '') for item in items[1:]]

	def get_media_url(self, url):
		html = self.webget.getURL(url)
		soup = BeautifulSoup(html, 'html.parser')
		video = soup.find('div', {'class': 'video-container'}).get_text()
		start = video.find('sources:')
		if start >= 0:
			end = video.find('}]', start)
			video = video[start:end]
			for line in video.split('\n'):
				if line.strip().startswith('file:'):
					l = line.split('"')
					if l[1].startswith('https:'):
						return l[1]
		return None
