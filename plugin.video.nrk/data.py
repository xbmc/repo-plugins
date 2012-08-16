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

import re

import BeautifulSoup
html_decode = lambda string: BeautifulSoup.BeautifulSoup(string,
    convertEntities=BeautifulSoup.BeautifulSoup.HTML_ENTITIES).contents[0]

import CommonFunctions
parseDOM = CommonFunctions.parseDOM

import requests
requests = requests.session(headers={'User-Agent':'xbmc.org'})


def parse_by_letter(arg):
  """ returns: </serie/newton> or </program/koif45000708> """
  url = "http://tv.nrk.no/programmer/%s?filter=rettigheter" % arg
  html = requests.get(url).text
  html = parseDOM(html, 'div', {'id':'programList'})
  return _parse_list(html)

def parse_by_category(arg):
  url = "http://tv.nrk.no/kategori/%s" % arg
  html = requests.get(url).text
  html = parseDOM(html, 'div', {'class':'alpha-list clear'})
  return _parse_list(html)

def parse_categories():
  url = "http://tv.nrk.no/kategori/"
  html = requests.get(url).text
  html = parseDOM(html, 'ul', {'id':'categoryList'})
  return _parse_list(html)

def _parse_list(html):
  titles = parseDOM(html, 'a')
  titles = map(html_decode, titles)
  urls = parseDOM(html, 'a', ret='href')
  return titles, urls


def parse_recommended():
  url = "http://tv.nrk.no/"
  html = requests.get(url).text
  html = parseDOM(html, 'ul', {'id':'introSlider'})[0]
  
  h1s = parseDOM(html, 'h1')
  titles2 = parseDOM(h1s, 'a')
  titles1 = parseDOM(html, 'strong')
  titles = [ "%s - %s" % (t1, t2) for t1, t2 in zip(titles1, titles2) ]
  
  urls = parseDOM(h1s, 'a', ret='href')
  imgs = re.findall(r'1900":"([^"]+)', html)
  return titles, urls, imgs


def parse_most_recent():
  url = "http://tv.nrk.no/listobjects/recentlysent"
  html = requests.get(url).text
  urls = parseDOM(html, 'a', {'class':'listobject-link'}, ret='href')
  thumbs = parseDOM(html, 'img', ret='src')[::2] #extract even elements
  html = ''.join(parseDOM(html, 'span', {'class':'listobject-title'}))
  titles = parseDOM(html, 'strong')
  titles = map(html_decode, titles)
  return titles, urls, thumbs


def parse_seasons(arg):
  """ returns: </program/Episodes/aktuelt-tv/11998> """
  url = "http://tv.nrk.no/serie/%s" % arg
  html = requests.get(url).text
  html = parseDOM(html, 'div', {'id':'seasons'})
  html = parseDOM(html, 'noscript')
  titles = parseDOM(html, 'a', {'class':'seasonLink'})
  titles = [ "Sesong %s" % html_decode(t) for t in titles ]
  ids = parseDOM(html, 'a', {'class':'seasonLink'}, ret='href')
  return titles, ids


def parse_episodes(series_id, season_id):
  """ returns: </serie/aktuelt-tv/nnfa50051612/16-05-2012..> """
  url = "http://tv.nrk.no/program/Episodes/%s/%s" % (series_id, season_id)
  html = requests.get(url).text
  html = parseDOM(html, 'table', {'class':'episodeTable'})
  trs = parseDOM(html, 'tr', {'class':'has-programtooltip episode-row js-click *'})
  titles = [ parseDOM(tr, 'a', {'class':'p-link'})[0] for tr in trs ]
  titles = map(html_decode, titles)
  ids = [ parseDOM(tr, 'a', {'class':'p-link'}, ret='href')[0] for tr in trs ]
  ids = [ e.split('http://tv.nrk.no')[1] for e in ids ]
  descr = [lambda x=x: _get_descr(x) for x in ids ]
  return titles, ids, descr


def parse_media_url(video_id, bitrate):
  bitrate = 4 if bitrate > 4 else bitrate
  url = "http://nrk.no/serum/api/video/%s" % video_id
  url = requests.get(url).json['mediaURL']
  url = url.replace('/z/', '/i/', 1)
  url = url.rsplit('/', 1)[0]
  url = url + '/index_%s_av.m3u8' % bitrate
  return url

def _get_descr(url):
  url = "http://nrk.no/serum/api/video/%s" % url.split('/')[3]
  descr = requests.get(url).json['description']
  return descr

