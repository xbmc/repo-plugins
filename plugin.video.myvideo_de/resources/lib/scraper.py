#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#     Copyright (C) 2012 Tristan Fischer (sphere@dersphere.de)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#

import hashlib
import re
from base64 import b64decode
from BeautifulSoup import BeautifulSoup
from binascii import unhexlify
from urllib import unquote, urlencode
from urllib2 import urlopen, Request, HTTPError, URLError

MAIN_URL = 'http://www.myvideo.de/'

UA = (
    'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.11 '
    '(KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11'
)
GK = (
    'WXpnME1EZGhNRGhpTTJNM01XVmhOREU0WldNNVpHTTJOakpt'
    'TW1FMU5tVTBNR05pWkRaa05XRXhNVFJoWVRVd1ptSXhaVEV3'
    'TnpsbA0KTVRkbU1tSTRNdz09'
)

CATEGORIES = (
    {'title': 'Top 100', 'path': 'Top_100'},
    {'title': 'Videos', 'path': 'Videos_A-Z'},
    {'title': 'Serien', 'path': 'Serien'},
    {'title': 'Filme', 'path': 'Filme'},
    {'title': 'Musik', 'path': 'Musik'}
)

BLOCKED_SUBCATS = (
    '/Videos_A-Z/Video_Flight',
    '/Videos_A-Z/Videos_in_Playlisten',
    '/musik-tv',
    '/channel/Clipgenerator',
    '/echo',
    '/Themen/Sexy',
    '/Top_100/Top_100_Playlisten',
    '/Serien/WWE',
    '/Serien/Serien_Suche',
    '/channel/unforgettable',
    '/webstarts'
)

R_ID = re.compile('watch/([0-9]+)/?')


class NetworkError(Exception):
    pass


def get_categories():
    return CATEGORIES


def get_sub_categories(path):
    __log('get_sub_categories started with path: %s' % path)
    tree = __get_tree(MAIN_URL)
    section = tree.find('div', {'class': 'body topNavFW'})
    sub_cats = []
    link = section.find('a', {'href': '/%s' % path})
    if link:
        for l in link.parent.findAll('a', {'class': 'topsub nArrow'}):
            if l['href'] in BLOCKED_SUBCATS:
                __log('skipping entry with link: %s' % l['href'])
                continue
            elif '/watch/' in l['href']:
                __log('skipping playable entry with link: %s' % l['href'])
                continue
            sub_cats.append({
                'title': l.span.string.strip(),
                'path': l['href'][1:]}
            )
    __log('get_sub_categories finished with %d elements' % len(sub_cats))
    return sub_cats


def get_search_result(query):
    __log('get_search_result started with path: %s' % query)
    path = '/Videos_A-Z?%s' % urlencode({'searchWord': query})
    items = get_path(path)
    return items


def get_path(path):
    __log('get_path started with path: %s' % path)
    parser = None
    if 'Top_100' in path:
        parser = __parse_video_charts
    elif 'filme_video_list' in path:
        parser = __parse_movies
    elif 'video_list' in path:
        parser = __parse_channels
    elif 'mv_charts' in path:
        parser = __parse_channels
    elif 'Charts' in path:  # fixme: still needed?
        parser = __parse_video_charts
    elif 'channel' in path:
        parser = __parse_channels
    elif 'playlist' in path:  # fixme: needs to be rewritten
        parser = __parse_playlists
    elif 'Musik_K' in path:
        if not 'lpage' in path:
            parser = __parse_letter
        else:
            parser = __parse_music_artists
    elif 'Musik_Videos' in path:
        parser = __parse_video_default
    elif 'Musik' in path:
        parser = __parse_music
    elif 'Filme' in path:
        parser = __parse_movies
    elif 'Kategorien' in path:
        parser = __parse_categories
    elif 'Alle_Serien_A-Z' in path:
        parser = __parse_shows_overview
    elif 'Serien' in path:
        parser = __parse_shows
    elif '/archiv' in path:
        parser = __parse_webstars
    elif 'webstars' in path:
        parser = __parse_webstars_overview
    else:
        parser = __parse_video_default
    tree = __get_tree(MAIN_URL + path)
    __log('Using Parser: %s' % parser.__name__)
    return parser(tree)


def get_video(video_id):
    __log('get_video started with video_id: %s' % video_id)
    r_adv = re.compile('var flashvars={(.+?)}')
    r_adv_p = re.compile('(.+?):\'(.+?)\',?')
    r_swf = re.compile('swfobject.embedSWF\(\'(.+?)\'')
    r_rtmpurl = re.compile('connectionurl=\'(.*?)\'')
    r_playpath = re.compile('source=\'(.*?)\'')
    r_path = re.compile('path=\'(.*?)\'')
    r_title = re.compile("<h1(?: class='globalHd')?>(.*?)</h1>")
    video = {}
    params = {}
    encxml = ''
    videopage_url = MAIN_URL + 'watch/%s/' % video_id
    html = __get_url(videopage_url, MAIN_URL)
    video['title'] = re.search(r_title, html).group(1)
    sec = re.search(r_adv, html).group(1)
    for (a, b) in re.findall(r_adv_p, sec):
        if not a == '_encxml':
            params[a] = b
        else:
            encxml = unquote(b)
    if not params.get('domain'):
        params['domain'] = 'www.myvideo.de'
    xmldata_url = '%s?%s' % (encxml, urlencode(params))
    if 'flash_playertype=MTV' in xmldata_url:
        __log('get_video avoiding MTV player')
        xmldata_url = (
            'http://www.myvideo.de/dynamic/get_player_video_xml.php'
            '?flash_playertype=D&ID=%s&_countlimit=4&autorun=yes'
        ) % video_id
    enc_data = __get_url(xmldata_url, videopage_url).split('=')[1]
    enc_data_b = unhexlify(enc_data)
    sk = __md5(b64decode(b64decode(GK)) + __md5(str(video_id)))
    dec_data = __rc4crypt(enc_data_b, sk)
    rtmpurl = re.search(r_rtmpurl, dec_data).group(1)
    video['rtmpurl'] = unquote(rtmpurl)
    if 'myvideo2flash' in video['rtmpurl']:
        __log('get_video forcing RTMPT')
        video['rtmpurl'] = video['rtmpurl'].replace('rtmpe://', 'rtmpt://')
    playpath = re.search(r_playpath, dec_data).group(1)
    video['file'] = unquote(playpath)
    if not video['file'].endswith('f4m'):
        ppath, prefix = unquote(playpath).split('.')
        video['playpath'] = '%s:%s' % (prefix, ppath)
    else:
        raise NotImplementedError
        video['playpath'] = video['file']
    swfobj = re.search(r_swf, html).group(1)
    video['swfobj'] = unquote(swfobj)
    video['pageurl'] = videopage_url
    m_filepath = re.search(r_path, dec_data)
    video['filepath'] = m_filepath.group(1)
    return video


def __parse_video_charts(tree):
    r_div = re.compile('vThumb')
    subtree = tree.find('div', {'class': 'lContent'})
    sections = subtree.findAll('div', {'class': r_div})
    items = []
    for sec in sections:
        path = sec.a['href']
        is_folder, video_id = __detect_folder(path)
        title = sec.a['title']
        thumb = __get_thumb(sec.img)
        try:
            length_str = sec.span.string
            length = __format_length(length_str)
        except AttributeError:
            length = '0:00'
        items.append({
            'title': title,
            'thumb': thumb,
            'length': length,
            'path': path,
            'is_folder': is_folder,
            'video_id': video_id
        })
    __log('__parse_video_charts finished with %d elements' % len(items))
    return items


def __parse_video_default(tree):
    subtree = tree.find('div', {'class': 'lContent'})
    r_td = re.compile('hslice.*?video_list')
    items = []
    pagination = subtree.find('div', {'class': 'pView'})
    if pagination:
        prev_link = pagination.find('a', {'class': 'pView pnBack'})
        if prev_link:
            items.append({
                'title': prev_link['title'],
                'pagenination': 'PREV',
                'path': prev_link['href']
            })
        next_link = pagination.find('a', {'class': 'pView pnNext'})
        if next_link:
            items.append({
                'title': next_link['title'],
                'pagenination': 'NEXT',
                'path': next_link['href']
            })
    sections = subtree.findAll('div', {'class': r_td})
    for sec in sections:
        link = sec.find('a', {'class': 'vLink'})
        if not link:
            continue
        path = link['href']
        is_folder, video_id = __detect_folder(path)
        title = link['title']
        thumb = __get_thumb(link.img)
        length_str = sec.find('span', {'class': 'vViews'}).string
        length = __format_length(length_str)
        username = sec.find('span', {'class': 'nick'}).a['title']
        span = sec.find('span', {'id': 'vc%s' % video_id})
        if span:
            views = span.string.replace('.', '')
        else:
            views = 0
        date = sec.find('div', {'class': 'sCenter vAdded'}).string
        items.append({
            'title': title,
            'thumb': thumb,
            'length': length,
            'path': path,
            'is_folder': is_folder,
            'username': username,
            'views': views,
            'date': date,
            'video_id': video_id
        })
    __log('__parse_video_default finished with %d elements' % len(items))
    return items


def __parse_music(tree):
    r_td = re.compile('floatLeft fRand')
    subtree = tree.find('div', {'class': 'lContent'})
    sections = subtree.findAll('div', {'class': r_td})
    items = []
    for sec in sections:
        div = sec.find('div', {'class': 'vThumb chThumb'})
        if div:
            path = div.a['href']
            is_folder, video_id = __detect_folder(path)
            title = div.a['title']
            thumb = __get_thumb(div.img)
            length_str = div.find('span', {'class': 'vViews'}).string
            length = __format_length(length_str)
            items.append({
                'title': title,
                'thumb': thumb,
                'length': length,
                'path': path,
                'is_folder': is_folder,
                'video_id': video_id
            })
    __log('__parse_music finished with %d elements' % len(items))
    return items


def __parse_categories(tree):
    r_td = re.compile('body floatLeft')
    sections = tree.findAll('div', {'class': r_td})
    items = []
    for sec in sections:
        d = sec.find('div', {'class': 'sCenter kTitle'})
        if not d:
            continue
        path = d.a['href']
        is_folder = True
        title = d.a.string
        thumb = __get_thumb(sec.find('div', {'class': 'vThumb kThumb'}).a.img)
        items.append({
            'title': title,
            'thumb': thumb,
            'path': path,
            'is_folder': is_folder
        })
    __log('__parse_categories finished with %d elements' % len(items))
    return items


def __parse_shows_overview(tree):
    subtree = tree.find('div', {'class': 'lContent'})
    sections = subtree.findAll('div', {'class': 'lBox seriesDetail'})
    items = []
    for sec in sections:
        prevs = sec.previousSibling
        path = prevs.a['href']
        is_folder = True
        title = prevs.a.string
        thumb = __get_thumb(sec.find(
            'div', {'class': 'vThumb pChThumb'}).div.img
        )
        items.append({
            'title': title,
            'thumb': thumb,
            'path': path,
            'is_folder': is_folder
        })
    __log('__parse_shows_overview finished with %d elements' % len(items))
    return items


def __parse_webstars_overview(tree):
    subtree = tree.find('div', {'class': 'content grid_12'})
    sections = subtree.findAll('div')
    items = []
    r_archiv = re.compile('/archiv')
    for sec in sections:
        if sec.a:
            path = sec.find('a', {'href': r_archiv})['href']
            is_folder = True
            title = sec.a.img['alt']
            thumb = __get_thumb(sec.find('img'))
            items.append({
                'title': title,
                'thumb': thumb,
                'path': path,
                'is_folder': is_folder
            })
    __log('__parse_webstars_overview finished with %d elements' % len(items))
    return items


def __parse_webstars(tree):
    subtree = tree.find('div', {'class': 'video-list videos'})
    a_elements = subtree.findAll('a', recursive=False)
    items = []
    for a_element in a_elements:
        path = a_element['href']
        is_folder, video_id = __detect_folder(path)
        title = a_element.find('span', {'class': 'headline-sub-sub'}).string
        thumb = __get_thumb(a_element.find('img'))
        items.append({
            'title': title,
            'thumb': thumb,
            'path': path,
            'is_folder': is_folder,
            'video_id': video_id
        })
    pagination = tree.find('div', {'class': re.compile('video_pager')})
    if pagination:
        prev_link = pagination.find('a', text=u'\u25c4')
        if prev_link and prev_link.parent.get('href'):
            items.append({
                'title': '',
                'pagenination': 'PREV',
                'path': prev_link.parent['href']
            })
        next_link = pagination.find('a', text=u'\u25ba')
        if next_link and next_link.parent.get('href'):
            items.append({
                'title': '',
                'pagenination': 'NEXT',
                'path': next_link.parent['href']
            })
    __log('__parse_webstars finished with %d elements' % len(items))
    return items


def __parse_playlists(tree):
    subtree = tree.find('div', {'class': 'globalBxBorder globalBx'})
    sections = subtree.findAll('div', {'class': 'vds_video_sidebar_item'})
    items = []
    for sec in sections:
        d = sec.find('div', {'class': 'nTitle'})
        title = d.a['title']
        path = d.a['href']
        is_folder = True
        thumb = __get_thumb(sec.find('img', {'class': 'vThumb nThumb pThumb'}))
        items.append({
            'title': title,
            'thumb': thumb,
            'path': path,
            'is_folder': is_folder
        })
    __log('__parse_playlists finished with %d elements' % len(items))
    return items


def __parse_channels(tree):
    r_div = re.compile('lBox floatLeft qLeftBox charts_box')
    r_td = re.compile('body floatLeft')
    subtree = tree.find('div', {'class': r_div})
    subtree2 = tree.find('div', {'class': 'uBList'})
    items = []
    if subtree:  # video channel
        __log('__parse_channels assuming video channel')
        r_pagination = re.compile('pViewBottom')
        r_pagelink = re.compile('src=\'(.+?)\'')
        pagination = tree.find('div', {'class': r_pagination})
        if pagination:
            prev_link = pagination.find(
                'a', {'class': 'pView pSmaller pnBack'}
            )
            if prev_link:
                link = re.search(r_pagelink, prev_link['onclick']).group(1)
                items.append({
                    'title': prev_link['title'],
                    'pagenination': 'PREV',
                    'path': link
                })
            next_link = pagination.find(
                'a', {'class': 'pView pSmaller pnNext'}
            )
            if next_link:
                link = re.search(r_pagelink, next_link['onclick']).group(1)
                items.append({
                    'title': next_link['title'],
                    'pagenination': 'NEXT',
                    'path': link
                })
        sections = subtree.findAll('div', {'class': r_td})
        for sec in sections:
            d = sec.find('div', {'class': 'pChHead'})
            if d:
                title = d.a['title']
                path = d.a['href']
                is_folder, video_id = __detect_folder(path)
                length_str = sec.find('span', {'class': 'vViews'}).string
                length = __format_length(length_str)
                thumb = __get_thumb(sec.find('img', {'class': 'vThumb'}))
                items.append({
                    'title': title,
                    'thumb': thumb,
                    'path': path,
                    'length': length,
                    'video_id': video_id,
                    'is_folder': is_folder
                })
    elif subtree2:  # music channel
        __log('__parse_channels assuming music channel')
        r_pagination = re.compile('pView')
        r_pagelink = re.compile('src=\'(.+?)\'')
        pagination = tree.find('table', {'class': r_pagination})
        if pagination:
            prev_link = pagination.find('a', {'class': 'pView pnBack'})
            if prev_link:
                link = re.search(r_pagelink, prev_link['onclick']).group(1)
                items.append({
                    'title': prev_link['title'],
                    'pagenination': 'PREV',
                    'path': link
                })
            next_link = pagination.find('a', {'class': 'pView pnNext'})
            if next_link:
                link = re.search(r_pagelink, next_link['onclick']).group(1)
                items.append({
                    'title': next_link['title'],
                    'pagenination': 'NEXT',
                    'path': link
                })
        sections = subtree2.findAll('div', {'class': 'uBItem'})
        for sec in sections:
            d = sec.find('div', {'class': 'sCenter uBTitle'})
            title = d.a.string
            path = d.a['href']
            is_folder, video_id = __detect_folder(path)
            length_str = sec.find('span', {'class': 'vViews uBvViews'}).string
            length = __format_length(length_str)
            thumb = __get_thumb(sec.find('img', {'class': 'uBThumb uBvThumb'}))
            items.append({
                'title': title,
                'thumb': thumb,
                'path': path,
                'length': length,
                'video_id': video_id,
                'is_folder': is_folder
            })
    __log('__parse_channels finished with %d elements' % len(items))
    return items


def __parse_shows(tree):
    r_td = re.compile('body .*? series_member')
    subtree = tree.find('div', {'class': 'lContent'})
    items = []
    if subtree:
        sections = subtree.findAll('div', {'class': r_td})
        for sec in sections:
            d = sec.find('div', {'class': 'pChHead'})
            title = d.a.string
            path = d.a['href']
            is_folder = True
            thumb = __get_thumb(sec.find('img', {'class': 'vThumb'}))
            items.append({
                'title': title,
                'thumb': thumb,
                'path': path,
                'is_folder': is_folder
            })
    __log('__parse_shows finished with %d elements' % len(items))
    return items


def __parse_movies(tree):
    r_pagination = re.compile('pView')
    r_pagelink = re.compile('src=\'(.+?)\'')
    items = []
    pagination = tree.find('div', {'class': r_pagination})
    if pagination:
        prev_link = pagination.find('a', {'class': 'pView pnBack'})
        if prev_link:
            link = re.search(r_pagelink, prev_link['onclick']).group(1)
            items.append({
                'title': prev_link['title'],
                'pagenination': 'PREV',
                'path': link
            })
        next_link = pagination.find('a', {'class': 'pView pnNext'})
        if next_link:
            link = re.search(r_pagelink, next_link['onclick']).group(1)
            items.append({
                'title': next_link['title'],
                'pagenination': 'NEXT',
                'path': link
            })
    sections = tree.findAll('div', {'class': 'filme_entry'})
    for sec in sections:
        d = sec.find('div', {'class': 'vTitle'})
        title = d.a['title']
        path = d.a['href']
        is_folder, video_id = __detect_folder(path)
        length_str = sec.find('span', {'class': 'vViews'}).string
        length = __format_length(length_str)
        thumb = __get_thumb(sec.find('img', {'class': 'vThumb'}))
        items.append({
            'title': title,
            'thumb': thumb,
            'path': path,
            'length': length,
            'video_id': video_id,
            'is_folder': is_folder
        })
    __log('__parse_movies finished with %d elements' % len(items))
    return items


def __parse_letter(tree):
    sections = tree.findAll('td', {'class': 'mView'})
    items = []
    for sec in sections:
        title = sec.a.string.strip()
        path = sec.a['href']
        is_folder = True
        items.append({
            'title': title,
            'path': path,
            'is_folder': is_folder
        })
    __log('__parse_letter finished with %d elements' % len(items))
    return items


def __parse_music_artists(tree):
    subtree = tree.find('div', {'class': 'lBox mLeftBox music_channels'})
    items = []
    if subtree:
        sections = subtree.findAll('div', {'class': 'body floatLeft sTLeft'})
        for sec in sections:
            d = sec.find('div', {'class': 'pChThumb pPrThumb'})
            title = d.a['title']
            path = d.a['href']
            is_folder, video_id = __detect_folder(path)
            thumb = __get_thumb(d.img)
            items.append({
                'title': title,
                'thumb': thumb,
                'path': path,
                'video_id': video_id,
                'is_folder': is_folder
            })
    __log('__parse_music_artists finished with %d elements' % len(items))
    return items


def __format_length(length_str):
    h = m = s = '0'
    if ' min' in length_str:
        m, s = length_str.replace(' min', '').split(':')
    elif ' Std.' in length_str:
        h, m, s = length_str.replace(' Std.', '').split(':')
    seconds = int(h) * 3600 + int(m) * 60 + int(s)
    return seconds


def __detect_folder(path):
    video_id = None
    is_folder = True
    m_id = re.search(R_ID, path)
    if m_id:
        video_id = m_id.group(1)
        is_folder = False
    return is_folder, video_id


def __get_thumb(img):
    return img.get('longdesc') or img.get('src')


def __get_tree(url, referer=None):
    html = __get_url(url, referer)
    tree = BeautifulSoup(html, convertEntities=BeautifulSoup.HTML_ENTITIES)
    return tree


def __get_url(url, referer=None):
    __log('__get_url opening url: %s' % url)
    req = Request(url)
    if referer:
        req.add_header('Referer', referer)
    req.add_header(
        'Accept', (
            'text/html,application/xhtml+xml,'
            'application/xml;q=0.9,*/*;q=0.8'
        )
    )
    req.add_header('User-Agent', UA)
    try:
        html = urlopen(req).read()
    except HTTPError, error:
        raise NetworkError('HTTPError: %s' % error)
    except URLError, error:
        raise NetworkError('URLError: %s' % error)
    __log('__get_url got %d bytes' % len(html))
    return html


def __rc4crypt(data, key):
    x = 0
    box = range(256)
    for i in range(256):
        x = (x + box[i] + ord(key[i % len(key)])) % 256
        box[i], box[x] = box[x], box[i]
    x = 0
    y = 0
    out = []
    for char in data:
        x = (x + 1) % 256
        y = (y + box[x]) % 256
        box[x], box[y] = box[y], box[x]
        out.append(chr(ord(char) ^ box[(box[x] + box[y]) % 256]))
    return ''.join(out)


def __md5(s):
    return hashlib.md5(s).hexdigest()


def __log(msg):
    print('MyVideo.de scraper: %s' % msg)
