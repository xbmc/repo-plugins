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
import json
import requests
import HTMLParser
import StorageServer
import CommonFunctions
from itertools import repeat

html_decode = HTMLParser.HTMLParser().unescape
parseDOM = CommonFunctions.parseDOM
cache = StorageServer.StorageServer('nrk.no', 336)

session = requests.session()
session.headers['User-Agent'] = 'xbmc.org'

xhrsession = requests.session()
xhrsession.headers['User-Agent'] = 'xbmc.org'
xhrsession.headers['X-Requested-With'] = 'XMLHttpRequest'


def get_by_letter(arg):
  """ returns: </serie/newton> or </program/koif45000708> """
  url = "http://tv.nrk.no/programmer/%s?filter=rettigheter&ajax=true" % arg
  html = xhrsession.get(url).text
  return _parse_list(html)

def get_by_category(arg):
  url = "http://tv.nrk.no/kategori/%s" % arg
  html = xhrsession.get(url).text
  html = parseDOM(html, 'div', {'class':'alpha-list clear'})
  return _parse_list(html)

def get_categories():
  url = "http://tv.nrk.no/kategori/"
  html = xhrsession.get(url).text
  html = parseDOM(html, 'ul', {'id':'categoryList'})
  return _parse_list(html)

def _parse_list(html):
  titles = parseDOM(html, 'a')
  titles = [ re.sub('<[^>]*>', '', t) for t in titles ]
  titles = map(html_decode, titles)
  urls = parseDOM(html, 'a', ret='href')
  thumbs = [ _thumb_url(url) for url in urls ]
  fanart = [ _fanart_url(url) for url in urls ]
  return titles, urls, thumbs, fanart


def get_recommended():
  url = "http://tv.nrk.no/"
  html = xhrsession.get(url).text
  html = parseDOM(html, 'ul', {'id':'introSlider'})[0]
  
  h1s = parseDOM(html, 'h2')
  titles2 = parseDOM(h1s, 'a')
  titles1 = parseDOM(html, 'strong')
  titles = [ "%s - %s" % (t1, t2) for t1, t2 in zip(titles1, titles2) ]
  
  urls = parseDOM(h1s, 'a', ret='href')
  thumbs = [ _thumb_url(url) for url in urls ]
  fanart = [ _fanart_url(url) for url in urls ]
  return titles, urls, thumbs, fanart


def get_most_recent():
  url = "http://tv.nrk.no/listobjects/recentlysent.json/page/0"
  elems = xhrsession.get(url).json()['ListObjectViewModels']
  titles = [ e['Title'] for e in elems ]
  titles = map(html_decode, titles)
  urls = [ e['Url'] for e in elems ]
  thumbs = [ e['ImageUrl'] for e in elems ]
  fanart = [ _fanart_url(url) for url in urls ]
  return titles, urls, thumbs, fanart


def get_search_results(query, page=1):
  url = "http://tv.nrk.no/sok?q=%s&side=%s&filter=rettigheter" % (query, page)
  html = session.get(url).text # use normal request. xhr page wont list all the results
  anc = parseDOM(html, 'a', {'class':'searchresult listobject-link'})
  titles = [ parseDOM(a, 'strong')[0] for a in anc ]
  titles = map(html_decode, titles)
  
  urls = parseDOM(html, 'a', {'class':'searchresult listobject-link'}, ret='href')
  urls = [ r.split('http://tv.nrk.no')[1] for r in urls ]
  thumbs = [ _thumb_url(url) for url in urls ]
  fanart = [ _fanart_url(url) for url in urls ]
  return titles, urls, thumbs, fanart


def get_seasons(arg):
  """ returns: </program/Episodes/aktuelt-tv/11998> """
  url = "http://tv.nrk.no/serie/%s" % arg
  html = xhrsession.get(url).text
  html = parseDOM(html, 'div', {'id':'seasons'})
  html = parseDOM(html, 'noscript')
  titles = parseDOM(html, 'a', {'class':'seasonLink'})
  titles = [ "Sesong %s" % html_decode(t) for t in titles ]
  ids = parseDOM(html, 'a', {'class':'seasonLink'}, ret='href')
  thumbs = repeat(_thumb_url(arg))
  fanart = repeat(_fanart_url(arg))
  return titles, ids, thumbs, fanart


def get_episodes(series_id, season_id):
  """ returns: </serie/aktuelt-tv/nnfa50051612/16-05-2012..> """
  url = "http://tv.nrk.no/program/Episodes/%s/%s" % (series_id, season_id)
  html = xhrsession.get(url).text
  trs = parseDOM(html, 'tr', {'class':'has-programtooltip episode-row js-click *'})
  titles = [ parseDOM(tr, 'a', {'class':'p-link'})[0] for tr in trs ]
  titles = map(html_decode, titles)
  ids = [ parseDOM(tr, 'a', {'class':'p-link'}, ret='href')[0] for tr in trs ]
  ids = [ e.split('http://tv.nrk.no')[1] for e in ids ]
  descr = [lambda x=x: _get_descr(x) for x in ids ]
  thumbs = repeat(_thumb_url(series_id))
  fanart = repeat(_fanart_url(series_id))
  return titles, ids, thumbs, fanart, descr


def get_media_url(video_id, bitrate):
  bitrate = 4 if bitrate > 4 else bitrate
  url = "http://nrk.no/serum/api/video/%s" % video_id
  url = _get_cached_json(url, 'mediaURL')
  url = url.replace('/z/', '/i/', 1)
  url = url.rsplit('/', 1)[0]
  url = url + '/index_%s_av.m3u8' % bitrate
  return url


def _get_cached_json(url, node):
  return _get_cached(url, lambda x: json.loads(x)[node])

def _get_cached(url, transform):
  data = cache.get(url)
  if data:
    try:
      ret = transform(data)
      return ret
    except: # assume data is broken
      pass
  data = xhrsession.get(url).text
  cache.delete(url)
  cache.set(url, data)
  return transform(data)

def _thumb_url(id):
  return "http://nrk.eu01.aws.af.cm/t/%s" % id.strip('/')

def _fanart_url(id):
  return "http://nrk.eu01.aws.af.cm/f/%s" % id.strip('/')

def _get_descr(url):
  url = "http://nrk.no/serum/api/video/%s" % url.split('/')[3]
  descr = _get_cached_json(url, 'description')
  return descr
