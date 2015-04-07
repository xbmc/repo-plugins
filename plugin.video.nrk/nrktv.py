# -*- coding: utf-8 -*-
#
# Copyright (C) 2014 Thomas Amland
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import requests
import HTMLParser
import CommonFunctions as common
from itertools import repeat
from nrktv_mobile import Program

html_decode = HTMLParser.HTMLParser().unescape
parseDOM = common.parseDOM

session = requests.Session()
session.headers['User-Agent'] = 'xbmc.org'
session.headers['X-Requested-With'] = 'XMLHttpRequest'
session.headers['Cookie'] = "NRK_PLAYER_SETTINGS_TV=devicetype=desktop&preferred-player-odm=hlslink&preferred-player-live=hlslink"


def _programs_from_lists(titles, urls, thumbs, fanart, descr=repeat(None)):
    programs = []
    for t, u, th, f, d in zip(titles, urls, thumbs, fanart, descr):
        p = Program(title=t, url=u, thumb=th, fanart=f, description=d)
        programs.append(p)
    return programs


def get_live_stream(ch):
    url = "http://tv.nrk.no/direkte/nrk%s" % ch
    html = session.get(url).text
    url = parseDOM(html, 'div', {'id': 'playerelement'}, ret='data-media')[0]
    img = parseDOM(html, 'img', {'class': 'poster'}, ret='src')[0]
    return url, img


def get_categories():
    titles = ["Barn", "Dokumentar", "Drama og serier", "Film", "Humor", "Kultur", "Livsstil",
              "Natur", "Nyheter", "Samisk", "Sport", "Sysnstolk", "Tegnspråk", "Underholdning", "Vitenskap"]
    ids = ["barn", "dokumentar", "drama-serier", "film", "humor", "kultur", "livsstil",
           "natur", "nyheter", "samisk", "sport", "synstolk", "tegnspraak", "underholdning", "vitenskap"]
    return titles, ids


def get_by_letter(l):
    url = "http://tv.nrk.no/programmer/%s" % l
    return _program_list(url)


def get_by_category(category, l):
    url = "http://tv.nrk.no/programmer/%s/%s" % (category, l)
    return _program_list(url)


def _program_list(url):
    items = session.get(url).json()
    items = [i for i in items if i['hasOndemandRights']]
    titles = [i['Title'] for i in items]
    urls = [i['Url'] for i in items]

    image_url = "http://m.nrk.no/m/img?kaleidoId=%s&width=%d"
    img_ids = [i['ImageUrl'].split('/')[-1] for i in items]
    thumbs = [image_url % (id, 300) for id in img_ids]
    fanart = [image_url % (id, 1920) for id in img_ids]
    return _programs_from_lists(titles, urls, thumbs, fanart)


def get_recommended():
    url = "http://tv.nrk.no/programmer"
    html = session.get(url).text
    html = parseDOM(html, 'div', {'class': 'recommended-list'})[0]
    titles = map(html_decode, parseDOM(html, 'img', ret='alt'))
    urls = parseDOM(html, 'a', ret='href')
    thumbs = parseDOM(html, 'img', ret='src')
    fanart = [_fanart_url(url) for url in urls]
    return _programs_from_lists(titles, urls, thumbs, fanart)


def get_most_recent():
    url = "http://tv.nrk.no/listobjects/recentlysent.json/page/0/100"
    return _json_list(url)


def get_most_popular_week():
    url = "http://tv.nrk.no/listobjects/mostpopular/Week.json/page/0/100"
    return _json_list(url)


def get_most_popular_month():
    url = "http://tv.nrk.no/listobjects/mostpopular/Month.json/page/0/100"
    return _json_list(url)


def _json_list(url):
    elems = session.get(url).json()['Data']
    titles = [e['Title'] for e in elems]
    titles = map(html_decode, titles)
    urls = [e['Url'] for e in elems]
    thumbs = [e['Images'][0]['ImageUrl'] for e in elems]
    fanart = [_fanart_url(url) for url in urls]
    return _programs_from_lists(titles, urls, thumbs, fanart)


def get_search_results(query, page=0):
    url = "http://tv.nrk.no/sokmaxresults?q=%s&page=%s" % (query, page)
    html = session.get(url).text
    lis = parseDOM(html, 'div', attrs= {'class': 'air'})

    titles = [parseDOM(li, 'h3')[0] for li in lis]
    titles = [html_decode(common.stripTags(_).replace('\n', ' ')) for _ in titles]

    urls = [parseDOM(li, 'a', ret='href')[0] for li in lis]
    urls = [url.replace('http://tv.nrk.no', '') for url in urls]

    descr = [parseDOM(li, 'p')[0] for li in lis]
    descr = [html_decode(common.stripTags(_).replace('&hellip;', '')) for _ in descr]

    thumbs = [parseDOM(li, 'img', ret='src')[0] for li in lis]
    fanart = [_fanart_url(url) for url in urls]
    return _programs_from_lists(titles, urls, thumbs, fanart, descr)


def get_seasons(arg):
    url = "http://tv.nrk.no/serie/%s" % arg
    html = session.get(url).text
    items = parseDOM(html, 'li', {'class': 'season-menu-item'})
    titles = [html_decode(parseDOM(li, 'a')[0]) for li in items]
    ids = [parseDOM(li, 'a', ret='data-season')[0] for li in items]
    urls = ["/program/Episodes/%s/%s/0" % (arg, i) for i in ids]
    thumbs = repeat(_thumb_url(arg))
    fanart = repeat(_fanart_url(arg))
    return _programs_from_lists(titles, urls, thumbs, fanart)


def get_episodes(series_id, season_id):
    url = "http://tv.nrk.no/program/Episodes/%s/%s" % (series_id, season_id)
    html = session.get(url).text
    ul = parseDOM(html, 'ul', {'class': 'episode-list'})
    assert len(ul) == 1
    cls = parseDOM(ul, 'li', ret='class')
    items = parseDOM(ul, 'li')
    items = [items[i] for i in range(len(items)) if "no-rights" not in cls[i]]
    titles = [parseDOM(i, 'h3')[0] for i in items]
    titles = [html_decode(common.stripTags(_)) for _ in titles]
    urls = [parseDOM(i, 'a', ret='href')[0] for i in items]
    descr = [parseDOM(i, 'p')[0] for i in items]
    descr = [html_decode(common.stripTags(_)) for _ in descr]
    thumbs = repeat(_thumb_url(series_id))
    fanart = repeat(_fanart_url(series_id))
    return _programs_from_lists(titles, urls, thumbs, fanart, descr)


def get_media_url(video_id):
    url = "http://v8.psapi.nrk.no/mediaelement/%s" % video_id
    return session.get(url).json()['mediaUrl']


def _thumb_url(id):
    return "http://nrk.eu01.aws.af.cm/t/%s" % id.strip('/')


def _fanart_url(id):
    return "http://nrk.eu01.aws.af.cm/f/%s" % id.strip('/')
